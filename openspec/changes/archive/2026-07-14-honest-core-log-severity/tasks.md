# Tasks — honest-core-log-severity

> **设计偏离（实装时改的，如实记录）**：proposal 原本设计一个三档分类器
> `classifyCoreLogLine(message) → 'fatal' | 'warn' | 'info'`，靠「这句话看着像不像错误」的内容正则来判。
> **实装时放弃了这个方向**，原因是把核心里 59 条写 stderr 的日志逐条摊开看之后，语料**推翻了它**：
>
> - `console.warn` 里既有良性排队（`外壳暂时给不出浏览器槽位…`），**也有真终态**（`CDP 重连不可恢复（终态）→ 诚实下线 + 回收退出`）；
> - `console.error` 里既有真崩（`浏览会话异常`），**也有无害的遥测发送失败**（`risk.captcha_cleared 上报失败`）。
>
> 也就是说**方法名（warn/error）和通道一样没有信息量**。而按散文猜「像不像错误」会变成军备竞赛——
> 例如 `执行云端命令 X 失败: Error: …` 同时带着 `失败` 和 `Error:` 两个"错误特征"，但引擎照跑。
>
> **改用的判据是结构性的**（对齐 memory `failure-must-be-structural`：失败判据只能是结构上做不到）：
> 核心里**每条致命路径都必然退出进程**（`启动失败` → `process.exit(1)`；`身份确立失败` → `terminateNow()`；
> `CDP 终态` / `云端重连耗尽` → `requestShutdown()`），而外壳 `child.on('close')` 的异常退出分支**才是权威判据**
> ——核心自己的注释就是这么写的：「致命启动失败立即非零退出，让桌面外壳的 `edgeProcess.on('exit')` 立刻看见」。
> 所以日志行**不需要**去猜谁是错误，只需要认核心**自己声明**的终态。落成两个纯函数：
>
> - `declaresCoreHalt(line)` —— 核心自述终态的**白名单**（不是散文启发式）。保留 `CDP 输入控制不可用`，
>   因为那是**唯一不退出**的终态（核心活着但驱不动浏览器、要求人工介入）；少了它，「边缘在线但浏览器
>   驱不动」这个哑状态就没人报了。
> - `isFailureShapedLine(line)` —— 失败**归因**候选，内容判定 + 良性排除表。
>
> 净效果与 proposal 的意图一致（徽标按内容判、不按通道判），但判据更窄、更可辩护、无军备竞赛。
> spec delta 写的是行为契约（不点函数名），因此无需改动。

## 1. aidcp-edge — 纯函数判据（落在既有纯模块 `src/electron/fleet.cjs`）

- [x] 1.1 新增 `declaresCoreHalt(message)`：核心自述终态白名单（`CDP 输入控制不可用` / `CDP 重连不可恢复` / `诚实下线` / `回收退出` / `身份确立失败` / `^[aidcp-edge] 启动失败:`）。**MUST NOT 看该行走 stdout 还是 stderr。** <!-- aidcp-edge 2473b7e -->
- [x] 1.2 新增 `isFailureShapedLine(message)`：失败归因候选，内容判定 + 良性排除表（`[publish-submit-diag]` 观测日志 / `上报失败`·`回传失败` 遥测发送失败 / `给不出浏览器槽位` 排队 / `租约抑制`）。 <!-- aidcp-edge 2473b7e -->
- [x] 1.3 两函数导出；语料**逐字取自核心真实日志**的单测落在新文件 `test/electron/core-log-severity.test.ts`（22 例）。 <!-- aidcp-edge 2473b7e：未塞进 fleet.test.ts，本 change 的契约自成一组、单独一个文件更好找 -->

## 2. aidcp-edge — 状态投影改用内容判据

- [x] 2.1 `main.cjs` `handleEdgeLogLine`：`edge: fleet.declaresCoreHalt(message) ? 'warning' : 'running'`，取代 `isError ? 'warning' : 'running'`。 <!-- aidcp-edge 2473b7e -->
- [x] 2.2 `main.cjs` `rememberEdgeFailureCandidate`：去掉 `isError` 短路与该形参，改用 `fleet.isFailureShapedLine`。 <!-- aidcp-edge 2473b7e -->
- [x] 2.3 `appendEdgeLog(handle.envId, message, isError)` 保持按真实通道记 `ERR` 前缀（**未改**；传输事实要留痕，只是不再被误读成语义）。 <!-- aidcp-edge 2473b7e：契约测试锁死 -->
- [x] 2.4 退出处 `abnormalExitFailurePatch`（权威判据）**未改**；契约测试锁死其仍在、仍按退出码/信号给出权威失败呈现。 <!-- aidcp-edge 2473b7e -->

## 3. 验证

- [x] 3.1 **回归断言在修复前的代码上确实失败**（这条是本 change 的成立前提，实测过、不是声称）：把 `main.cjs` 临时还原成 `origin/master` 版本、`fleet.cjs` 保持新版再跑 → `pass 20 / fail 2`，失败的正是那两条契约断言（edge 徽标不得由 `isError` 派生；失败归因不得被 `isError` 短路）。修复后 22/22 全绿。 <!-- aidcp-edge 2473b7e -->
- [x] 3.2 良性语料（槽位排队 / `[publish-submit-diag]` / 租约抑制 / 冷待机重连重试 / 遥测上报失败 / 单次浏览会话异常）→ 一律不判终态、不污染失败归因。真终态语料（6 条）→ 仍判死。 <!-- aidcp-edge 2473b7e -->
- [x] 3.3 `npm run typecheck` 干净；`npm run test:acceptance` 19/19；全量 `npm test` **1296/1296**。rebase 到并发方新推的 master（`214fb58`）之后**重跑一遍**仍全绿。 <!-- aidcp-edge 2473b7e -->
- [x] 3.4 `openspec validate honest-core-log-severity --strict` 通过。 <!-- control repo -->

## 4. 收口

- [x] 4.1 合回 `aidcp-edge` master：`214fb58..2473b7e`。首次 push 撞 non-ff（并发流刚推了两个 UI 提交），按铁律 rebase 后重跑全量再推，**未 force**。canonical 已 ff 同步、worktree 与分支已清。 <!-- aidcp-edge 2473b7e -->
- [x] 4.2 真机验收项登记到 `docs/real-machine-acceptance-backlog.md` 簇 79。 <!-- control repo -->
- [x] 4.3 归档。 <!-- control repo -->

## 边界（已守住）

- **未碰 `aidcp-edge/src/main.ts`**（提交前显式核过 diff 文件清单）。那 6 处良性 `console.warn` 的措辞**不需要**改——改措辞只是掩盖症状，真正的 bug 是呈现层在误读；且该文件正由并行流改动（FB 租约闸的节奏豁免 + 冷待机闸）。
- 只改「什么时候翻红」。核心真崩 / 真启动失败的红**一分未动**（由退出处权威判据兜底，契约测试锁死）。
