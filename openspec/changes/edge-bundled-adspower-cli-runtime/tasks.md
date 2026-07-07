# Tasks — edge-bundled-adspower-cli-runtime

> 代码改动落 `aidcp-edge`；进度回写本仓，格式 `<!-- <repo> <commit-sha> 备注 -->`。真机 / 打包验证项登记到 `docs/real-machine-acceptance-backlog.md`，不在此勾。api-key 为敏感值，只记读取方式、不写值。

## 1. aidcp-edge — 打包内嵌运行时（edge-desktop-packaging）

- [ ] 1.1 把 `adspower-browser` 加入 edge 依赖并纳入分发；确认包内 native `.node`（sqlite）为 N-API、五架构预编译齐全
- [ ] 1.2 electron-builder 配置：运行时包置于 `extraResources` / `asarUnpack`（asar 外），native 模块随 hardened runtime 签名；确认主安装包 MUST NOT 含浏览器内核
- [ ] 1.3 用 Electron 自带 Node（`ELECTRON_RUN_AS_NODE`+`process.execPath`，复用 `src/electron/main.cjs:644` 现有模式）能直接跑随包的 `cli/index.js`——加一个最小 spawn 冒烟
- [ ] 1.4 确定运行时工作目录/缓存的可写位置策略（`~/.adspowerCli` + 必要时首运把包内 `cwd/` 复制到用户可写目录）

## 2. aidcp-edge — 运行时启动与看护（adspower-cli-embedded-runtime）

- [ ] 2.1 主进程新增「拉起内嵌运行时」：spawn `cli/index.js start -k <key>`（key 从设置/env 读），等 Local API 就绪（`/status`）后再继续
- [ ] 2.2 端口对接：读运行时实际监听端口（`ads status`/等价），据此设 `AIDCP_ADS_API_BASE`，不硬编码 50325
- [ ] 2.3 运行时进程看护：起不来/中途死亡诚实呈现 + 有界重起；不静默把核心带进注定失败的启动（守红线）
- [ ] 2.4 接线到启动链：`startFlow`→`startAdsPowerFlow`（`src/electron/main.cjs:767`）在起核心前先确保运行时就绪

## 3. aidcp-edge — 内核预检 + 进度门控（adspower-cli-embedded-runtime）

- [ ] 3.1 预检逻辑：`get-kernel-list` 查所需内核 `is_downloaded`（先固定 148，见 Open Question）；已就绪则秒过
- [ ] 3.2 缺则 spawn `download-kernel`，解析其 `Kernel progress: N% [state]` 流；下完（completed）才 `startEdge()`（`main.cjs:622`）
- [ ] 3.3 进度推送：`updateStatus`/`status:update`（`main.cjs:478`）新增 kernel 准备/进度字段；preload 新 IPC 通道（如需）
- [ ] 3.4 渲染层：准备态 + 确定型进度条（`renderer/` STATUS_LABELS/render `renderer.js:110/1176`，状态区 `#ads-config` `renderer.js:88`），文案标「约 750MB、仅首次」
- [ ] 3.5 失败处置：下载失败诚实停「准备失败 + 重试」、不起核心；绝不让核心在 `browser/start` 里惰性下载

## 4. 测试（落 aidcp-edge，桩层可测的）

- [ ] 4.1 运行时启动/看护单测：就绪门控、失败诚实、重起有界（桩掉 spawn 与 Local API）
- [ ] 4.2 内核预检状态机单测：已就绪秒过 / 缺则进度门控 / 下载失败不起核心（桩掉 download-kernel 进度流）
- [ ] 4.3 端口对接单测：非默认端口时 `AIDCP_ADS_API_BASE` 取实际值
- [ ] 4.4 `npm run typecheck` + `npm test` 全过（伴侣端为主，勿触发无关红线回归）

## 5. 打包 / 真机验证（登记 backlog，不在此勾）

- [ ] 5.1 干净机器（mac arm64 / mac x64 / win）打包后各起一次：N-API `.node` 加载、`ads start` 起服、端点直连、`browser/start`+CDP headful
- [ ] 5.2 mac 签名/公证后首启 Gatekeeper 对下载的内核/chromedriver 行为
- [ ] 5.3 首启内核下载全程 + 中断/重试（续传 vs 重来）实测
- [ ] 5.4 单账号完整 cloud 闭环灰度（真机 backlog `adspower-browser 8.2`，本 change 前置）

## 6. 文档与收尾

- [ ] 6.1 OPERATOR / README 新机装机路径（内嵌运行时 + 首启下内核），self 与外部 `AIDCP_ADS_API_BASE` 逃生阀说明保留
- [ ] 6.2 `docs/anti-detection.md` 补内嵌 CLI 运行时形态说明
- [ ] 6.3 `openspec validate edge-bundled-adspower-cli-runtime --strict` 通过 → 归档（注意与 `edge-installer-oss-distribution` 在 `edge-desktop-packaging` 上按序合并）
