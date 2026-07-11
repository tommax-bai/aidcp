# Design — edge-adspower-env-in-use-terminal-stop

## 现状锚点（edge master `1e7e6d9`）
- 拒启抛错：`src/cdp/browser-provider.ts:303-306`（`browser/start` 收到 `code≠0` 时把 `msg` 原样插值抛错）。冒泡到顶层 `src/main.ts:966-970` → `console.error('[aidcp-edge] 启动失败:', err)`（写 stderr）→ `process.exit(1)`。
- 外壳看护：`src/electron/main.cjs` 的 `child.on('close')`（~1304）判 `exitedAbnormally`（code≠0 且非有意停止）→ `fleet.decideRespawn`（`src/electron/fleet.cjs:195-203`，只看退出码）→ 有界重起（`RESPAWN_OPTS` 默认 max=5、退避 1s→30s、healthy=60s，`main.cjs:522-527`）。
- 唯一原因特判先例：缺内核 `handleEdgeLogLine` 匹配 `/SunBrowser (\d+) is not ready/` → 置 `handle.kernelMissThisRun` → `close` 处 `kernelMissExit` 分支走可恢复路径（`main.cjs:1341-1359`）。**本变更完全复用这套骨架**，只是走的是终局停止而非可恢复重起。
- 失败详情呈现：`abnormalExitFailurePatch`（`main.cjs:804-808`）用 `handle.lastEdgeFailureLine` 作 `edgeFailure.summary`；`synthesizeHealth`（`ui-logic.js:25-26`）在 `edge==='warning'` 时直接取 `edgeFailure.summary` 作详情；失败区块 `#edge-failure-text`（`renderer.js:619-627`）也显示它。**所以只要改 `summary` 文案，用户即可见**，无需动渲染层。

## 关键决策

### D1. 识别放外壳侧（文本分类），不引入新退出码契约
- 选外壳侧：在 `handleEdgeLogLine` 对 stderr 行做文本分类，命中置 `handle.envInUseThisRun`。**与缺内核特判同构**（同样是对 AdsPower 输出做文本驱动的控制流），零核心改动、零新退出码契约、blast radius 最小。
- 否决核心侧专属退出码（类比 `EXIT_RECYCLE=75`）：更「locale-proof」但要动核心 + 立新退出码契约 + 跨文件，YAGNI 下不值。文本误判风险由「双语正则 + 限定在 browser/start 失败上下文 + 护栏开关」压住。
- 排序安全：`handle.envInUseThisRun` 由 `handleEdgeLogLine`（stderr `data`）置、由 `child.on('close')` 读。Node 保证 `close` 在 stdio 全 drain 之后触发（`main.cjs:1298-1303` 注释即据此把终局判定挂 `close`）——缺内核特判正是靠同一保证，本变更沿用。

### D2. 停重试用「本地覆盖决策」，不改 `decideRespawn` 孪生
- 在 `close` 算出 `decision` 后、`scheduleRespawnIfNeeded` 前，若 `envInUseThisRun` 为真则**强制 `decision = { action:'stop', streak:0 }`**。因为「是否重起」只由 `decision.action` 门控，这是唯一杠杆。
- 不改 `fleet.decideRespawn` / `src/supervise/respawn-policy.ts`（风控相邻热点、§7 单写文件）——与现有 `kernelMissExit` 同样在 `close` 处本地特判，不动纯策略孪生。
- `streak:0` 保证操作者随后手动点「启动」不被之前失败计数惩罚。

### D3. 红线：绝不关他处浏览器
- 拒启发生在拿到浏览器句柄之前（`browser-provider.ts:257-267` 的实例只在成功后构造），现状本就无 teardown 触达该分身。本变更**只**做「停本机重起 + 换文案 + 通知」，**不新增**任何 `browser/stop` / OS 杀 / attach。这条不变量写进 spec 与代码注释。

### D4. 提示（最小范围，用户 07-11 定）
- 只把 `edgeFailure.summary`（→ 失败区块详情 + 健康详情 + 系统通知）换成友好中文，复用既有模板口径（`main.cjs:2401-2402 / 2422-2423` 的「该环境正在使用中（可能已在其它设备或窗口打开）…请先关闭该环境后重试」）。
- 失败区块静态标题「本机引擎已停止」、在场感行「引擎已停止，请查看详情」保持不变（不动 `index.html` / `ui-logic.js` 渲染分支，零渲染风险）。因为 `decision.action==='stop'`，`willRespawn=false`，本就不会出现「稍后自动重启」倒计时——与 spec 一致。

### D5. 护栏
- `AIDCP_EDGE_ENV_IN_USE_TERMINAL` 默认开（`'0'/'false'/'off'/'no'` 关）。关掉则不置终局标志、退回旧的按崩溃重起，供识别误伤时应急。

## 风险与对冲
- 文本误判（把可恢复失败误当终局）：正则限定「browser/start 失败上下文 + 拒启签名（`not allowed to open` / `being used` / 中文 `正在使用·已打开`）」，且给护栏兜底。误判后果是「停而不重试」（保守、非自残），操作者点启动即重试。
- AdsPower 若在同账号并发时返回 `code=0` 复用既有端口（而非拒启）——那是另一条（会 attach 别人浏览器的）危险路径，**不在本变更范围**（本变更只处理 `code=-1` 明确拒启），登记真机确认项。
