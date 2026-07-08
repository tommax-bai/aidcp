# Tasks — edge-bundled-adspower-cli-runtime

> 代码改动落 `aidcp-edge`；进度回写本仓，格式 `<!-- <repo> <commit-sha> 备注 -->`。真机 / 打包验证项登记到 `docs/real-machine-acceptance-backlog.md`，不在此勾。api-key 为敏感值，只记读取方式、不写值。
>
> 进度说明（2026-07-08）：运行时启动 + 内核预检 + 进度门控 + 渲染进度条 + 单测已实装并**已 ff 合入 edge master**（commit `ff7ae43`，a2fac2a..ff7ae43；typecheck + acceptance 13/13 + 全量 717 通过）。按新约定不打安装包、edge 不自动部署。**打包（第 1 组）与「运行时中途死亡有界重起」（2.3 后半）暂缓**：打包/签名与并发 change `edge-macos-developer-id-signing` 在同一 `edge-desktop-packaging` 面重叠，按单写者纪律待其落地后再做（届时新开 worktree、rebase 最新 master）。未内嵌 CLI 时启动流程 no-op（mode: none/external），对现有外部客户端用户零行为变化。

## 1. aidcp-edge — 打包内嵌运行时（edge-desktop-packaging）

> 暂缓：与 `edge-macos-developer-id-signing` 在 `package.json` build 配置 / 签名面重叠，待其落地后再合（单写者串行）。

- [ ] 1.1 把 `adspower-browser` 加入 edge 依赖并纳入分发；确认包内 native `.node`（sqlite）为 N-API、五架构预编译齐全 <!-- 事实已核实：包 58MB、sqlite 为 N-API（298 napi 符号）、mac/arm64/x64/linux/ia32 预编译齐全（本机验证 2026-07-08）；加依赖 + 分发配置待打包组一并做 -->
- [ ] 1.2 electron-builder 配置：运行时包置于 `extraResources` / `asarUnpack`（asar 外），native 模块随 hardened runtime 签名；确认主安装包 MUST NOT 含浏览器内核
- [ ] 1.3 用 Electron 自带 Node（`ELECTRON_RUN_AS_NODE`+`process.execPath`，复用现有模式）能直接跑随包的 `cli/index.js`——加一个最小 spawn 冒烟 <!-- resolveCliEntry 已就绪（extraResources/asar.unpacked/node_modules 三候选 + require.resolve 兜底），打包后冒烟随打包组 -->
- [ ] 1.4 确定运行时工作目录/缓存的可写位置策略（`~/.adspowerCli` + 必要时首运把包内 `cwd/` 复制到用户可写目录）

## 2. aidcp-edge — 运行时启动与看护（adspower-cli-embedded-runtime）

- [x] 2.1 主进程新增「拉起内嵌运行时」：spawn `cli/index.js start -k <key>`（key 从设置/env 读），等 Local API 就绪后再继续 <!-- aidcp-edge ff7ae43 ads-runtime.cjs ensureRuntime（status→start→轮询就绪，限流退避）+ main.cjs ensureAdsRuntimeAndKernel 接线 -->
- [x] 2.2 端口对接：读运行时实际监听端口（`ads status`），据此设 `AIDCP_ADS_API_BASE`，不硬编码 50325 <!-- aidcp-edge ff7ae43 parseRuntimePort + embeddedAdsApiBase → buildProviderEnv 优先用之 -->
- [ ] 2.3 运行时进程看护：起不来诚实呈现（已做）+ **中途死亡有界重起（未做）**；不静默把核心带进注定失败的启动（已守红线） <!-- aidcp-edge ff7ae43 起不来/内核失败诚实 surfaceFailure + 不 startEdge 已做；daemon 化后中途死亡的健康轮询 + 有界重起待补 -->
- [x] 2.4 接线到启动链：`startAdsPowerFlow` 在起核心前先确保运行时就绪 <!-- aidcp-edge ff7ae43 startAdsPowerFlow 改 async，startEdge 前 await ensureAdsRuntimeAndKernel、失败即 return -->

## 3. aidcp-edge — 内核预检 + 进度门控（adspower-cli-embedded-runtime）

- [x] 3.1 预检逻辑：`get-kernel-list` 查所需内核 `is_downloaded`（固定 `DEFAULT_KERNEL`=148）；已就绪则秒过 <!-- aidcp-edge ff7ae43 kernelDownloaded + ensureKernel alreadyPresent 秒过 -->
- [x] 3.2 缺则 spawn `download-kernel`，解析其 `Kernel progress: N% [state]` 流；下完（completed）才 `startEdge()` <!-- aidcp-edge ff7ae43 ensureKernel 流式解析 + completed 判定；startAdsPowerFlow 门控 -->
- [x] 3.3 进度推送：`updateStatus`/`status:update` 新增 `kernelPrep` 字段 <!-- aidcp-edge ff7ae43 status.kernelPrep{state,percent,version}，onProgress→updateStatus -->
- [x] 3.4 渲染层：准备态 + 确定型进度条，文案标「约 750MB、仅首次」 <!-- aidcp-edge ff7ae43 index.html #kernel-prep + styles.css .kp-* + renderer.js renderKernelPrep -->
- [x] 3.5 失败处置：下载失败诚实停「准备失败」、不起核心；绝不让核心在 `browser/start` 里惰性下载 <!-- aidcp-edge ff7ae43 kres.ok=false → surfaceFailure + 不 startEdge；预检在起核心前完成 -->

## 4. 测试（落 aidcp-edge，桩层可测的）

- [x] 4.1 运行时启动/门控/失败单测（重起有界待 2.3 后半补） <!-- aidcp-edge ff7ae43 ads-runtime.test.ts：ensureRuntime 已跑/无key/起后就绪/无cliEntry；有界重起待 2.3 -->
- [x] 4.2 内核预检状态机单测：已就绪秒过 / 缺则进度门控 / 下载失败不起核心 / 未列出诚实报错 / 限流重试 <!-- aidcp-edge ff7ae43 ads-runtime.test.ts 覆盖 -->
- [x] 4.3 端口/解析单测：status 端口解析、非默认端口 base、限流检测 <!-- aidcp-edge ff7ae43 parseRuntimePort/getRuntime/isThrottled 单测；main.cjs buildProviderEnv 取值走集成、未单测 -->
- [x] 4.4 `typecheck` + `npm test` 全过 <!-- aidcp-edge ff7ae43 typecheck 干净；全量 717 pass -->

## 4b. aidcp-edge — 设置页重设计（embedded-CLI 形态收敛，用户令 07-08）

- [x] 4b.1 provider 选择改「本机 Chrome 开/关」开关（关=默认内置 AdsPower，开=self）；三卡分组（浏览器引擎/AdsPower 环境/窗口停放）消割裂 <!-- aidcp-edge 0d58ffb index.html+styles.css+renderer.js -->
- [x] 4b.2 删「AdsPower 状态/检测」徽标+按钮（探测改静默填充环境列表）、删「下载 AdsPower」链接（含 renderer 死码 adsDownloadUrl/setProbeBadge/handlers） <!-- aidcp-edge 0d58ffb -->
- [x] 4b.3 renderer-smoke 测试改开关+静默探测模型；全量 743 pass、typecheck 干净 <!-- aidcp-edge 0d58ffb -->
- [ ] 4b.4 **待补 spec delta（change 收口前写齐，§3）**：`pluggable-browser-provider`（删「下载 AdsPower 入口」requirement/scenario；「一键切换」措辞容纳开关形态）+ `adspower-desktop-env-picker`（删「检测」按钮/「已就绪」徽标可见要求 + 失败提示不再引下载入口；探测转静默填充；主区文案去「状态/下载入口」）。暂记待办：redesign 已在 edge master、与 merged spec 有暂时漂移，收口时随其他 spec delta 一并补齐
- [ ] 4b.5 backend 死码清理（可选，低优）：main.cjs `browser:openAdsDownload` handler + preload `openAdsDownload` + settings:get 的 adsDownloadUrl 字段（前端已不调、留着无害）

## 5. 打包 / 真机验证（登记 backlog，不在此勾）

- [ ] 5.1 干净机器（mac arm64 / mac x64 / win）打包后各起一次：N-API `.node` 加载、`ads start` 起服、端点直连、`browser/start`+CDP headful <!-- 本机（mac arm64，全局装 CLI + live runtime）已验：端点直连 + kernel 148 下载 + browser/start→CDP headful Chrome/148 全通；打包态待打包组后真机验 -->
- [ ] 5.2 mac 签名/公证后首启 Gatekeeper 对下载的内核/chromedriver 行为
- [ ] 5.3 首启内核下载全程 + 中断/重试（续传 vs 重来）实测
- [ ] 5.4 单账号完整 cloud 闭环灰度（真机 backlog `adspower-browser 8.2`，本 change 前置）

## 6. 文档与收尾

- [ ] 6.1 OPERATOR / README 新机装机路径（内嵌运行时 + 首启下内核），self 与外部 `AIDCP_ADS_API_BASE` 逃生阀说明保留
- [ ] 6.2 `docs/anti-detection.md` 补内嵌 CLI 运行时形态说明
- [ ] 6.3 `openspec validate edge-bundled-adspower-cli-runtime --strict` 通过 → 归档（注意与 `edge-installer-oss-distribution` 在 `edge-desktop-packaging` 上按序合并）
