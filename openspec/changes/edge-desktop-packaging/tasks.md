## 1. aidcp-edge — 预编译让包能跑（D1，最高优先 blocker）

- [x] 1.1 新增 `tsconfig.build.json`（`rootDir:"src"`、`include:["src/**/*.ts"]`、`declaration:false`、`outDir:"dist"`），产出 `dist/main.js` 等（仅 src、不含 test） <!-- aidcp-edge 0bcd47a tsconfig.build.json 新增 -->
- [x] 1.2 技术验证（apply 第一步）：`ELECTRON_RUN_AS_NODE=1 <electron-execPath> dist/main.js` 起一次，确认 ESM import 链路 + `ws` 初始化无 import/扩展名报错 <!-- aidcp-edge 0bcd47a 已用 electron bundled node import dist/{cdp,client,browse,flows,publish} 全通过(ESM-OK) -->
- [x] 1.3 改 `src/electron/main.cjs` 的 `startEdge`：`spawn(process.execPath, [appRoot/dist/main.js], { env:{...,ELECTRON_RUN_AS_NODE:'1'}, stdio pipes })` 取代 `npx tsx`；保留 `handleEdgeOutput` 日志解析 <!-- aidcp-edge 0bcd47a -->
- [x] 1.4 改 `package.json`：`build.files`=`dist/**/*`+`src/electron/**/*.cjs`+`src/electron/renderer/**`+`package.json`；`extraMetadata.main` 保持 `src/electron/main.cjs`；`electron:build` 串入 clean+`tsc -p tsconfig.build.json`（编译失败即整体失败） <!-- aidcp-edge 0bcd47a 含 clean:dist/build:dist 脚本 -->
- [x] 1.5 回归：确认开发态 `npm start`（tsx 路径）不受影响 <!-- aidcp-edge 0bcd47a start 脚本未改、仍 tsx src/main.ts，与 dist 路径独立 -->

## 2. aidcp-edge — macOS 打包目标（D2）

- [x] 2.1 `package.json` build 段新增 `mac`：`dmg`+`zip`、`x64`+`arm64`、`category`、`hardenedRuntime:true`、`identity:null`（未签名内部）；entitlements 占位（不做实际公证） <!-- aidcp-edge 0bcd47a -->
- [x] 2.2 `scripts` 拆 `electron:build:win`/`electron:build:mac`，`electron:build` 去掉写死的 `--win`（按当前平台） <!-- aidcp-edge 0bcd47a -->
- [ ] 2.3 补应用图标资源（`.icns`/`.ico`）——未做（用 electron-builder 默认图标，待定真实图标后补；非阻断）
- [ ] 2.4 在本机（darwin）实跑 `electron:build:mac` 产出 dmg/zip 并装开验证——GATED（重型真机构建，未自动跑；compile+ESM-load 已验证核心路径）

## 3. aidcp-edge — 运行时路径跨平台（D3，portability，非生产 blocker）

- [x] 3.1 `approval-gate.ts` 默认信号目录 `/tmp`→`os.tmpdir()`（call 时解析，`AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖）；并改用 `path.join`，与云端 `getApprovalSignalPath` 同 dir 下逐字一致（跨平台） <!-- aidcp-edge 0bcd47a -->
- [x] 3.2 更新 approval-gate 测试：跨平台 AC-PUB-01（join+basename+os.tmpdir+env 覆盖）+ 单测显式 signalDir；`AC-PUB-*` 全过 <!-- aidcp-edge 0bcd47a 单测10/10、acceptance 11/11 -->
- [x] 3.3 注记：同机 mock/e2e 两端共用 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 对齐；cloud 不改（ECS Linux） <!-- aidcp-edge 0bcd47a 记于 approval-gate.ts 注释 + OPERATOR/proposal -->

## 4. aidcp-edge — 失败可见（D4，红线：不静默假成功）

- [ ] 4.1 `main.ts` 顶层 `main().catch` 由 `exitCode=1` 改 `exit(1)`（致命启动失败立即非零退出，不重试）——DEFERRED：`main.ts` 正被并发会话（`account-identity-from-login` 的 shutdown/EXIT_RECYCLE 改造）实时编辑，避免撞车；现状已有 `main().catch`→清晰报错+非零 `exitCode`，需与该会话协调后再上 `exit(1)`
- [x] 4.2 `main.cjs` `edgeProcess.on('exit')` 异常退出（`signal!=null||code!==0` 且非主动退出）→ `mainWindow.show()`+`Notification` <!-- aidcp-edge 0bcd47a surfaceFailure() -->
- [x] 4.3 `main.cjs` Chrome 缺失（`launched.ok===false`）→ `show()`+`Notification` <!-- aidcp-edge 0bcd47a -->
- [x] 4.4 自检：未加任何连接退避重试（守快速失败+可见） <!-- aidcp-edge 0bcd47a 无重试代码 -->
- [ ] 4.5 回归：连云失败 → edge 非零退出 + 外壳弹窗/通知——PARTIAL：外壳侧 surfacing 已实装（4.2/4.3）；edge 即时非零退出依赖 4.1（DEFERRED），故端到端断言随 4.1 一并补

## 5. 文档 — OPERATOR.md（落 aidcp-edge）

- [x] 5.1 写 `aidcp-edge/OPERATOR.md`：前置装 Chrome、首次手动放行、扫码登录、多开、双 Chromium 内存、disconnected/崩溃排查 <!-- aidcp-edge 0bcd47a -->
- [x] 5.2 OPERATOR.md 注明多开隔离未做（归 `account-identity-from-login`）、暂不要同机多开 <!-- aidcp-edge 0bcd47a §3 -->

## 6. 验证与回归（CLAUDE.md §4 纪律）

- [x] 6.1 edge `npm run typecheck` <!-- aidcp-edge 0bcd47a exit 0 -->
- [x] 6.2 edge `npm run test:acceptance`（`AC-PUB-*` 全过） <!-- aidcp-edge 0bcd47a 11/11 -->
- [x] 6.3 edge `npm test` 全量 <!-- aidcp-edge 0bcd47a 345/345 -->
- [ ] 6.4 实机：打包 app 起一次走通 Chrome→登录→连云→状态更新→断云验证崩溃可见；（Windows）本地 mock/e2e 验证路径可移植——GATED（真机/真打包，未自动跑）
- [x] 6.5 自检：无新协议消息、无 DB 迁移、未碰两份 `protocol.ts`/`command-bridge`/edge 白名单/`docs/protocol.md` <!-- aidcp-edge 0bcd47a 改动仅 package.json/tsconfig.build.json/electron.cjs/approval-gate.ts/2 测试/OPERATOR.md -->

## 7. 跨 change 协调（非本 change 实装，仅转达/登记）

- [ ] 7.1 把「多开隔离 + Electron `.cjs` 启动器静默接管缝」转达 `account-identity-from-login` 负责人——已登记于 proposal/design/memory + OPERATOR §3 警告；待人对人转达确认
- [ ] 7.2 确认该 `.cjs` 启动器被纳入 `account-identity-from-login` 的多开隔离范围——待确认（该 change 仍 active）
