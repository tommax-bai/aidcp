## 1. aidcp-edge — 预编译让包能跑（D1，最高优先 blocker）

- [ ] 1.1 新增 `tsconfig.build.json`（`rootDir:"src"`、`include:["src/**/*.ts"]`、`declaration:false`、`outDir:"dist"`），产出 `dist/main.js` 等（仅 src、不含 test）
- [ ] 1.2 技术验证（apply 第一步）：`ELECTRON_RUN_AS_NODE=1 <electron-execPath> dist/main.js` 起一次，确认 ESM import 链路 + `ws` 初始化无 import/扩展名报错（验证 `type:module` 下编译产物可被 Electron 内置 Node 运行）
- [ ] 1.3 改 `src/electron/main.cjs` 的 `startEdge`（:79-89）：`spawn(process.execPath, [path.join(app.getAppPath(),'dist','main.js')], { env:{...process.env, ELECTRON_RUN_AS_NODE:'1'}, stdio:['pipe','pipe','pipe'] })` 取代 `npx tsx`；保留 `handleEdgeOutput` 日志解析（:93-94）
- [ ] 1.4 改 `package.json`：`build.files` = `dist/**/*` + `src/electron/**/*.cjs` + `src/electron/renderer/**` + `package.json`；`extraMetadata.main` 保持 `src/electron/main.cjs`；`scripts.electron:build` 串入「clean + `tsc -p tsconfig.build.json`」，**编译失败即整体构建失败**（不带旧/缺失 dist 出包）
- [ ] 1.5 回归：确认开发态 `npm start`（tsx 路径，:18）不受影响

## 2. aidcp-edge — macOS 打包目标（D2）

- [ ] 2.1 `package.json` build 段新增 `mac`：`target:[{target:'dmg',arch:['x64','arm64']},{target:'zip',arch:['x64','arm64']}]`、`category:'public.app-category.utilities'`、`hardenedRuntime:true` + entitlements/entitlementsInherit **占位**（本 change 不做实际签名/公证）
- [ ] 2.2 `scripts.electron:build` 拆 `electron:build:win`（`--win`）/ `electron:build:mac`（`--mac`），去掉写死的 `--win`（:14）
- [ ] 2.3 补应用图标资源（`.icns`/`.ico`，dmg/nsis 引用）——若图未定则放占位图并在 OPERATOR/开放问题登记
- [ ] 2.4 在本机（darwin）实跑 `electron:build:mac`，产出覆盖 `x64`+`arm64` 的 dmg/zip，确认可装可开（首次手动放行 Gatekeeper）

## 3. aidcp-edge — 运行时路径跨平台（D3，portability，非生产 blocker）

- [ ] 3.1 `src/publish/approval-gate.ts:33` `DEFAULT_SIGNAL_DIR` `'/tmp'`→`os.tmpdir()`，支持 `process.env.AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖（`signalDir` 参数已存在、`main.ts` 接线随默认生效不改）
- [ ] 3.2 更新/补 approval-gate 测试到新默认：含 `os.tmpdir()` 路径用例 + env 覆盖用例 + 两端同机对齐用例；保证 `AC-PUB-*` 全过
- [ ] 3.3 注记：同机 mock/e2e 需两端对齐时共用 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR`（cloud 不改，ECS Linux `/tmp` 正常）

## 4. aidcp-edge — 失败可见（D4，红线：不静默假成功）

- [ ] 4.1 `src/main.ts` 启动序列（含 `await client.connect()` :125）包 try/catch → 打印一行清晰错误 + `process.exit(1)`（把未捕获 rejection 转成诚实退出，**不重试**）
- [ ] 4.2 `src/electron/main.cjs` `edgeProcess.on('exit')`（:95）在 `code!==0` 时 `mainWindow.show()` + `new Notification({title,body}).show()`
- [ ] 4.3 `src/electron/main.cjs` `launchChromeAndGateEdge`（:134-138）Chrome 缺失（`launched.ok===false`）时 `show()` + `Notification`
- [ ] 4.4 自检/评审：确认**未**加连接退避重试（守「快速失败 + 可见」，不制造「看着在重连其实没跑」的假象）
- [ ] 4.5 回归：连云失败 → edge 非零退出 + 外壳弹窗/通知（最小测试或手动验证清单）

## 5. 文档 — OPERATOR.md（落 aidcp-edge）

- [ ] 5.1 写 `aidcp-edge/OPERATOR.md`：下载安装、**前置须装 Google Chrome**、首次扫码登录小红书、一台机器多开怎么开、双 Chromium 内存需求（Electron ~200MB + 每个 Chrome ~500-800MB）、`disconnected`/崩溃排查、首次手动放行签名警告（macOS 右键打开 / Windows「仍要运行」）
- [ ] 5.2 OPERATOR.md 注明：多开隔离当前**未做**（归 `account-identity-from-login`），避免运维误以为可安全多开同账号/多账号

## 6. 验证与回归（CLAUDE.md §4 纪律）

- [ ] 6.1 edge `npm run typecheck`
- [ ] 6.2 edge `npm run test:acceptance`（`AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 全过）
- [ ] 6.3 edge `npm test` 全量
- [ ] 6.4 实机：打包 app 起一次走通 Chrome→扫码登录→连云→状态面板更新→故意断云验证「崩溃可见」；（Windows）跑一次本地 mock/e2e 验证路径可移植
- [ ] 6.5 自检：无新协议消息、无 DB 迁移、未碰两份 `protocol.ts`/`command-bridge`/edge 白名单/`docs/protocol.md`（边轻云重 + 协议不漂移）

## 7. 跨 change 协调（非本 change 实装，仅转达/登记）

- [ ] 7.1 把「多开隔离 + Electron `.cjs` 启动器静默接管缝」正式转达 `account-identity-from-login` 负责人：`src/electron/chrome-launcher.cjs` 端口写死 9222（:6）/ 共用 profile（:31-32）/「端口有 Chrome 就盲目复用」（:58-60）→ 第二个 app 静默接管第一账号浏览器（撞红线）
- [ ] 7.2 确认该 `.cjs` 启动器被纳入 `account-identity-from-login` 的多开隔离范围（落地由该 change 做，非本 change）
