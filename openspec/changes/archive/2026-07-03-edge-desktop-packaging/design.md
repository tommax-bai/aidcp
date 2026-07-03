## Context

`aidcp-edge` 已有 Electron 外壳（`src/electron/`：托盘 + 状态面板 + 暂停/恢复/重登）与 `electron-builder` 配置，但只配了 Windows 目标，且打包产物**无法运行**：当前 Electron 主进程用 `spawn('npx',['tsx','src/main.ts'])`（`src/electron/main.cjs:83`）在运行时靠 `tsx` 解释 TypeScript 源码，而 `tsx`/`typescript` 是 devDependency（`package.json:55-56`）、会被 `electron-builder` 排除出包；`build.files` 装的是 `src/**/*` 原始 TS、无编译步骤（`package.json:28-32`）。

约束（来自 CLAUDE.md）：边轻云重、不静默假成功、edge 不做兜底/策略（诚实硬失败）、协议四处同步不可漂移、并发会话纪律（精确 git add、避开迁移号竞争）。分发对象为**内部少数运维机器**（已定），故签名/公证可降级为首次手动放行。

关键既有事实（已核实）：
- 运行时依赖仅 `ws`（纯 JS、无原生模块）→ 跨平台无 node-gyp 坑。
- Chrome 路径发现/profile/临时目录在 Electron 启动器里已按 `process.platform` 分支（`src/electron/chrome-launcher.cjs:12-29`），跨平台 OK。
- `tsconfig.json`：`outDir:"dist"`、`rootDir:"."`、`module:ES2022`、`include` 含 `src` 与 `test`；源码相对 import 已带 `.js` 扩展（如 `src/main.ts:39`、`approval-gate.ts:3`）→ 编译出的 ESM 可被 Node 直接运行。
- 发布审批信号文件：生产走**命令驱动路径**（云端按步下发、人审在云端 ECS 侧 feishu→`writeApprovalSignal` 写读自己的 `/tmp`，`cloud/src/feishu/ws-receiver.ts:64,89`+`server.ts:542`）；edge 的 `/tmp` 文件闸（`approval-gate.ts:33`）只服务旧整页 `publish.request` 路径 + 本地 mock/e2e、同机轮询 → **生产桌面应用不经此路径，cloud 不需改**。

## Goals / Non-Goals

**Goals:**
- 打出 macOS（dmg+zip，x64+arm64）与 Windows（nsis x64）双平台包，**装上去能真跑**（不依赖目标机有 Node/npx/tsx）。
- 启动/运行失败对运维**可见**（不静默装跑）。
- edge 运行时路径跨平台（本地 mock/e2e 可在 Windows 跑）。
- 一份 `OPERATOR.md`。

**Non-Goals:**
- 代码签名 + 公证（内部机器首次手动放行；仅留 `hardenedRuntime`/entitlements 占位）。
- 配置入口 UI / 账号绑定（归 `account-identity-from-login`）。
- 多开隔离（每实例独立账号/端口/profile + 去静默接管）——整条归 `account-identity-from-login`，含 `src/electron/chrome-launcher.cjs` 端口写死 9222 + 共用 profile + 盲目复用的那条缝（须转达其负责人，见 proposal）。
- 自动更新、app 内多账号管理 UI、改 pkg/nexe 轻量路线。
- 改 cloud 默认审批路径、改边-云协议、DB 迁移。

## Decisions

### D1：打包产物用「预编译 dist + Electron 内置 Node 运行」，不靠 tsx/系统 Node
- **怎么做**：新增 `tsconfig.build.json`（`rootDir:"src"`、`include:["src/**/*.ts"]`、`declaration:false`、`outDir:"dist"`→ 输出 `dist/main.js` 等）；`electron:build` 先跑该编译再 `electron-builder`。`build.files` 改为 `dist/**/*` + `src/electron/**/*.cjs` + `src/electron/renderer/**` + `package.json`（Electron 外壳是手写 `.cjs`/HTML、非 TS，不经编译、原样随包）。`main` 仍是 `src/electron/main.cjs`。
- **edge 子进程怎么起**：`startEdge` 改为 `spawn(process.execPath, [path.join(app.getAppPath(),'dist','main.js')], { env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, stdio: ['pipe','pipe','pipe'] })`——用 **Electron 自带的 Node 运行**编译后的 JS。保留 stdio 管道，使现有 `handleEdgeOutput` 日志解析照旧工作。
- **为什么**：内部运维机器**不保证装了 Node/npx**；Electron 包内已自带 Node 运行时，`ELECTRON_RUN_AS_NODE=1` 让 `process.execPath` 退化为纯 Node，零额外依赖。预编译彻底去掉运行时 `tsx`，包更小、冷启动省去每次 TS 解析。
- **备选与否决**：① 把 `tsx`+`typescript` 挪进 dependencies 进包——臃肿、运行时仍解释 TS、冷启动慢，**否决**。② 要求运维装 Node——违背「双击即用」，**否决**。③ 用 esbuild 打成单文件——更快但引入新依赖，`tsc` 已配好，YAGNI，**否决（留作后续优化）**。④ 把 edge 逻辑塞进 Electron 主进程内联跑——丢掉进程隔离与现成的 on('exit') 崩溃可见钩子，**否决**。⑤ `utilityProcess.fork`——可行但改动 stdout/IPC 比需要的大，**否决（保持最小改动）**。

### D2：macOS 目标 = dmg+zip、x64+arm64 双架构（非 universal）
- **怎么做**：`package.json` build 段加 `mac:{ target:[{target:'dmg',arch:['x64','arm64']},{target:'zip',arch:['x64','arm64']}], hardenedRuntime:true, entitlements/entitlementsInherit 占位 }`；`category` 填 `public.app-category.utilities`。`electron:build` 拆成 `electron:build:win`（`--win`）/`electron:build:mac`（`--mac`），去掉写死的 `--win`。
- **为什么**：内部分发不需要单一 universal 包的便利，分架构包体更小；zip 给后续自动更新留口。hardenedRuntime+entitlements 先占位，公证后续再开（本 change 不做）。
- **备选**：universal 单包——体积翻倍，内部场景无必要，**否决**。

### D3：edge 审批信号默认路径 `/tmp`→`os.tmpdir()`（portability，edge-only，cloud 不动）
- **怎么做**：`approval-gate.ts:33` `DEFAULT_SIGNAL_DIR` 由 `'/tmp'` 改为 `os.tmpdir()`，并允许 `process.env.AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖；`signalDir` 参数已存在，`main.ts` 接线随默认生效、无需改。
- **为什么**：仅修可移植性（让本地 mock/e2e 在 Windows 能跑）。**非生产 blocker**（生产是命令驱动 + 云端把关，不经此 edge 文件闸）。cloud 在 ECS Linux、`/tmp` 正常且与 edge 不同机，**不改**；同机 e2e 要对齐时两端共用上面那个 env。

### D4：失败可见 = 诚实硬失败 + 主动弹窗/通知；**不加重试退避**
- **怎么做**：① edge `main.ts` 把启动序列（含 `await client.connect()`，`main.ts:125`）包进 try/catch → 打印一行清晰错误 + `process.exit(1)`（把当前的未捕获 rejection 转成诚实退出码，**不重试**）。② Electron `main.cjs` 的 `edgeProcess.on('exit')`（`:95`）在 `code!==0` 时、以及 `launchChrome` 返回 `ok:false`（Chrome 缺失，`:136`）时，主动 `mainWindow.show()` + `new Notification({title,body}).show()`。
- **为什么**：守「不静默假成功」红线——托盘最小化时崩溃/连不上要让运维立刻看见。**MUST NOT 加连接退避重试**：那会制造「看着在重连其实没跑」的新静默假象，与红线及「edge 不做策略」哲学相悖；要的是「快速失败 + 可见」。
- **边界**：try/catch + exit(1) 是把失败**暴露**，不是兜底/掩盖，符合 edge 诚实硬失败哲学。

## Risks / Trade-offs

- **[目标机无系统 Node] → D1 用 Electron 内置 Node（execPath + `ELECTRON_RUN_AS_NODE=1`）**，不依赖 PATH 上的 node/npx。
- **[ESM 在 Electron Node 下能否跑] → apply 第 1 步先实测**：编译后 `dist/main.js` 是 ESM（`type:module`），源码相对 import 已带 `.js`；用 `ELECTRON_RUN_AS_NODE=1 process.execPath dist/main.js` 起一次确认能 import 链路跑通，再继续。
- **[出包前 dist 过期 / 漏编译，静默装了旧码] → `electron:build` 必须先 clean 再 `tsc -p tsconfig.build.json`**，并在脚本里让编译失败即整体失败（不许带着旧 dist 出包）。部署/分发后按 [[deploy-verify-content-after-rsync]] 思路 grep 包内 `dist/main.js` 关键行确认新码。
- **[在 mac 上构建 Windows 包需 wine] → 各平台目标在各自原生 OS 构建**（mac 包在本机 darwin 出；win 包在 Windows 机或现有 win 流程出）。列入开放问题。
- **[未签名 → Gatekeeper/SmartScreen 拦] → 内部接受首次手动放行**，`OPERATOR.md` 写清 macOS 右键打开 / Windows「仍要运行」。
- **[同机 mock/e2e 在 mac 上 `os.tmpdir()`≠`/tmp` 致两端路径不一致] → 同机 e2e 两端共用 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` env 覆盖**对齐。
- **[app/dmg/nsis 图标缺失] → 需补一份应用图标资源**（当前托盘是内联 SVG data URL，dmg/nsis 需真实 `.icns`/`.ico`）；缺失不阻断功能，列入 tasks。
- **[双 Chromium 内存] → 已知代价**（Electron ~200MB + 每个真实 Chrome ~500–800MB），写进 `OPERATOR.md`，不在本 change 优化。

## Migration Plan

- **加法式、不动生产运行链**：开发态 `npm start`（tsx）路径保留不变；打包是新增产物。cloud 零改动。回滚 = 不分发新包即可，无生产副作用。
- **构建**：本机（darwin）出 macOS dmg+zip（x64+arm64）；Windows 包沿用现有 win 流程（Windows 机或 wine）。
- **分发**：内部下载/共享盘取包；首次打开按 `OPERATOR.md` 手动放行 Gatekeeper/SmartScreen。
- **验证序列**：edge `npm run typecheck`+`npm test`+`npm run test:acceptance`（`AC-PUB-*` 全过、审批 gate 回归更新到新默认）→ 实机起一次打包 app：Chrome 拉起、扫码登录、连云、状态面板更新、故意断云验证「崩溃可见」、（Windows）跑一次本地 mock/e2e 验证路径可移植。

## Open Questions

1. Windows 目标在哪构建——Windows 机 vs mac+wine？（不阻断设计，落地时定）
2. macOS 是否要 universal 单包（默认按 D2 分架构，若运维要单包再加 `arch:['universal']`）。
3. 应用图标资源（`.icns`/`.ico`）由谁出、用什么图。
4. 是否顺带把 Electron 外壳 `.cjs` 也纳入一次性 lint/格式统一（非本 change 必须，避免范围蔓延）。
