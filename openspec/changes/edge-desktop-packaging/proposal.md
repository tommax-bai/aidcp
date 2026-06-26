## Why

`aidcp-edge` 要交付给内部运维去跑，但现在只能由开发者在终端 `npm start`（靠 `tsx` 解释 TS 源码）启动。仓里虽已接好 Electron 外壳 + `electron-builder`，却有两道硬伤：① build 目标只配了 Windows，没有 macOS；② **即便打出 Windows 包，装上去也跑不起来**——打包产物在运行时仍想用 `tsx` 解释 `src/main.ts`，而 `tsx` 是 devDependency、会被排除出包（`src/electron/main.cjs:83`、`package.json:55-56` / `28-32`）。此外还有一处 POSIX-only 的运行时路径（发布审批信号文件默认 `/tmp`，影响本地 mock/e2e 在 Windows 的可移植性，**非生产发帖 blocker**——详见下）和一条「崩了却看不见」的红线缺口。本 change 把 edge 收口成 **macOS + Windows 都能双击运行的桌面应用**，只做「让包真能跑 + 跨平台 + 不撞红线」的最小集合，面向内部少数运维机器分发。

## What Changes

- **打包产物可运行（最高优先）**：构建期把 `src/` 预编译成 `dist/` 的 JS，`build.files` 改装 `dist/**/*`，`main.cjs` 改用 `node dist/main.js` 起 edge 子进程，`electron:build` 串入编译步骤。彻底脱离 `tsx`/`npm` 的运行时依赖。
- **补 macOS 打包目标**：`package.json` build 段新增 `mac` 节（`dmg`+`zip`，arch 同出 `x64`+`arm64`），`electron:build` 去掉写死的 `--win`；`hardenedRuntime`+entitlements 仅留占位（为后续公证留缝，本 change 不做实际签名）。
- **跨平台安全的运行时路径（portability，非生产 blocker）**：edge 发布审批信号文件默认路径写死 `/tmp`（`src/publish/approval-gate.ts:33`），POSIX-only。经核实：生产发布走**命令驱动路径**（云端按步下发、人审在云端 ECS 侧把关——feishu→cloud 写读它自己的 `/tmp`，见 cloud `feishu/ws-receiver.ts:64,89` + `server.ts:542`），edge 这个文件闸只属于**旧整页 `publish.request` 路径 + 本地 mock/e2e 自驱**、且为同机轮询，生产桌面应用不经此路径。故此项为可移植性修复（让本地 mock/e2e 能在 Windows 跑），**不是生产发帖 blocker**。改 edge 默认为 `os.tmpdir()`（`signalDir` 参数已存在、仍可经 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖）。
- **失败可见（红线：不静默假成功）**：edge 子进程异常退出 / Chrome 缺失 / 连云失败时，Electron 外壳 MUST 主动 `BrowserWindow.show()` + 发系统通知把失败暴露出来，而非停在「starting」静默装跑。MUST NOT 加连接退避重试（会引入「看着在重连其实没跑」的新静默风险）——要的是「快速失败 + 可见」。
- **运维文档 `OPERATOR.md`**：安装、前置须装 Google Chrome、首次扫码登录、一台机器多开、双 Chromium 内存需求、disconnected/崩溃排查。

## Capabilities

### New Capabilities
- `edge-desktop-packaging`: 把 edge 交付为 macOS + Windows 桌面可执行应用的契约——打包产物 MUST 自带可运行的编译产物（不依赖 dev 工具链）、MUST 同时产出两平台目标、运行时路径 MUST 跨平台、启动/运行失败 MUST 对运维可见而非静默。

### Modified Capabilities
<!-- 无。发布审批信号路径在现有 spec 中仅为实现细节、非 requirement 级契约（publish-pipeline 只规定审批门结论/标题，不规定信号文件路径），故路径跨平台化作为新 capability 的可移植性要求承载，不改 publish-pipeline / publish-submit-integrity 的行为契约。 -->

## Impact

- **aidcp-edge（主体）**：
  - 构建：`tsconfig.json`/新增构建脚本产出 `dist/`；`package.json` 的 `build.files`、`extraMetadata.main`、`scripts.electron:build`、`build.mac`。
  - 启动：`src/electron/main.cjs`（`startEdge` 改 `node dist/main.js`；进程退出/Chrome 缺失时 `show()`+`Notification`）。
  - 路径：`src/publish/approval-gate.ts:33`（`DEFAULT_SIGNAL_DIR` `/tmp`→`os.tmpdir()`，可经 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖；`signalDir` 参数已存在，`main.ts` 接线无需改动即随默认生效）。
  - 文档：新增 `OPERATOR.md`。
- **aidcp-cloud（无需改）**：云端只跑 ECS Linux，`getApprovalSignalPath` 的 `/tmp`（`feishu/ws-receiver.ts:64,89`）正常工作，且审批信号在云端本机写读（feishu→`writeApprovalSignal`→`server.ts:542` 读），与 edge 不同机、不共享文件系统。仅当要让**同机** mock/e2e 两端路径对齐时，靠共同的 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` env 覆盖即可，不动 cloud 默认。本 change 不强制改 cloud。
- **不动**：边-云协议（无新 `MessageType`、不碰两份 `protocol.ts` / `command-bridge` / edge 白名单 / `docs/protocol.md`）；无 DB 迁移；不下放任何规划/风控/编排到边缘（边轻云重）。
- **校验**：edge `npm run typecheck` + `npm test` + `npm run test:acceptance`（因动了发布审批路径默认值，`AC-PUB-*` 未授权绝不静默发布 MUST 全过、`AC-PUB-*` 关于审批 gate 的回归须更新到新默认）；cloud 不改、无需重跑（除非选择性同机对齐）。
- **多开静默接管缝（用户拍板拆两半）**：① **安全半（红线，本 change 已做）**——Electron 外壳加单实例锁：同机第二个实例**诚实拒绝**（弹「已在运行」+退出），不再静默接管第一个账号的浏览器；锁随退出释放，不影响同应用重启重连自身浏览器。② **真·多开半（仍归 `account-identity-from-login`）**——每实例独立端口/profile 让多账号真能同机并行，与其节点槽位模型（每节点独立端口 + 用户数据目录 `node-<n>`、身份从登录态读出）强耦合，故不在本 change。**经核实** master 上 `src/electron/chrome-launcher.cjs` 仍端口写死 `9222`（:6）/ 共用 `userData/chrome-profile`（:31-32）/ 盲目复用（:58-60），身份 change 只动 CLI/核心路径未碰此 `.cjs`——真·多开落地时需把它纳入；当前红线已被安全半兜住，非紧急。
- **非目标**：代码签名/公证（内部机器首次手动放行）、配置入口 UI（归身份 change）、自动更新（electron-updater）、app 内多账号管理 UI（形态已定为「一 app 一账号、一机多 app」）、改 pkg/nexe 轻量路线（Electron 外壳已可用，YAGNI）。
