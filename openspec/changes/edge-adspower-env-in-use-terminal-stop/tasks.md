# Tasks — edge-adspower-env-in-use-terminal-stop

> edge-only（`../aidcp-edge`），不动协议 / 云端 / 风控 / ECS。热点：`src/electron/main.cjs`（并发 session 多）——land 前 rebase 到最新 master、只改本变更相关段。改动后按回归纪律 `test:acceptance` → `test` → `typecheck`。真机生效需运营机 pull edge master + 安装包重建。

## 1. aidcp-edge — 识别拒启（纯逻辑，`src/electron/fleet.cjs`）

- [x] 1.1 新增纯函数 `classifyAdsInUse(line)`：命中「browser/start 失败上下文 + 同账号并发占用拒启签名（`not allowed to open` / `being used` / 中文 `正在使用`·`已打开`）」时返回 `{ inUse: true, account }`；`account` 从 `is being used by [<account>]` 解析（解析不到则空）；不命中返回 `{ inUse: false }`。纯函数、无 electron 依赖，随 `module.exports` 导出。 <!-- edge 7d7d758 -->
- [x] 1.2 `test/electron/fleet.test.ts` 补用例：真实拒启 msg 判 `inUse:true` 且抽出账号；普通崩溃行 / 缺内核行（`SunBrowser 148 is not ready`）/ 无关「失败」行 / 空 判 `inUse:false`（防误判）。 <!-- edge 7d7d758 -->

## 2. aidcp-edge — 置终局标志（`src/electron/main.cjs` `handleEdgeLogLine`）

- [x] 2.1 在 `rememberEdgeFailureCandidate` 后调用 `classifyAdsInUse`：命中且护栏开启时置 `handle.envInUseThisRun = true` + `handle.envInUseHolder = account`。与 `kernelMissThisRun` 同 `stopping` 语义。 <!-- edge 7d7d758 -->
- [x] 2.2 护栏 env `AIDCP_EDGE_ENV_IN_USE_TERMINAL`（默认开；`'0'/'false'/'off'/'no'` 关，关则不置标志、退回旧重起行为）。 <!-- edge 7d7d758 -->
- [x] 2.3 `startEdge`（spawn 新核心处）清零 `handle.envInUseThisRun` / `handle.envInUseHolder`，避免跨运行误带。 <!-- edge 7d7d758 -->

## 3. aidcp-edge — 终局停止 + 友好呈现（`src/electron/main.cjs` `child.on('close')`）

- [x] 3.1 算出 `decision` 后：`envInUse`（异常退出 + 标志）为真则强制 `decision = { action:'stop', streak:0 }`（不进重起、不消耗连续失败预算）。与 `kernelMissExit` 分支并列。 <!-- edge 7d7d758 -->
- [x] 3.2 该终局时把 `edgeFailure.summary` + `lastMessage` 设为友好中文（复用 `updateEnvProxy`/`deleteEnv` 模板口径，含 `envInUseHolder` 若非空）；不出现「稍后自动重启」倒计时（`willRespawn=false` 本就不会）。 <!-- edge 7d7d758 -->
- [x] 3.3 一次性系统通知：`envInUse` 走专门「环境被占用」通知（不带误导性「重新登录」提示）；原 `streak===1 || gaveUp` 分支保留。 <!-- edge 7d7d758 -->
- [x] 3.4 复位标志由 `startEdge`（下次 spawn）统一清零，与 `kernelMissThisRun` 同处、同模式（close 内不额外复位，避免与既有模式漂移）。 <!-- edge 7d7d758 -->
- [x] 3.5 红线核查：本变更**不新增**任何 `browser/stop` / OS 杀 / attach 指向该分身（只停本机重起 + 换文案 + 通知）；决策分支加红线注释坐实。 <!-- edge 7d7d758 -->

## 4. aidcp-edge — 回归

- [x] 4.1 `npm run test:acceptance`（16 绿，AC-* 安全红线不破）→ `npm test`（993 绿）→ `npm run typecheck`（0 error）全过。 <!-- edge 7d7d758 land+rebase 后复跑仍 993 绿 -->

## 5. 真机验收（登记 backlog，解耦不阻塞归档）

- [ ] 5.1 运营机制造「分身已在别处打开」再启动，确认：不再空转 6 次、直接停；失败详情显示「环境被其它端占用（账号 …）…请先关闭后重试」；别处浏览器不被关。登记 `docs/real-machine-acceptance-backlog.md` 新簇。 <!-- 真机项，运营机 pull edge master + 安装包重建后核 -->
- [ ] 5.2 真机确认 AdsPower 同账号并发到底返 `code=-1` 拒启还是 `code=0` 复用端口（后者会 attach 别人浏览器，属另一条待评估路径，不在本变更）。 <!-- 真机项 -->
