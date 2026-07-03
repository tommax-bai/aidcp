# Tasks — adspower-browser-provider

> 接缝已由 `aidcp-edge/scripts/adspower-poc.ts` 真机验证（C1 attach ✅ / C3 cdp_mask+stealth-off ✅，2026-06-27）；本 change 把 PoC 固化为正式 provider。代码改动落 aidcp-edge，进度回写本仓。
> 实现主体见 edge `9f1fad8`（`src/cdp/browser-provider.ts` + `main.ts` 接线 + 单测）。

## 1. aidcp-edge — BrowserProvider 抽象 + Self 包装

- [x] 1.1 新增 `src/cdp/browser-provider.ts`：定义 `BrowserProvider { launch(opts): Promise<LaunchedBrowser> }`，`LaunchedBrowser` 含现有 `ChromeInstance` 形状 + `endpoint`（adspower 端口动态）<!-- aidcp-edge 9f1fad8 -->
- [x] 1.2 实现 `SelfChromeProvider`：直接委托现有 `launchChrome`，入参 / 返回 / 行为逐字不变（self 默认路径零变化）<!-- aidcp-edge 9f1fad8 -->
- [x] 1.3 从 `src/cdp/index.ts` 导出 `BrowserProvider` 接口与两实现 <!-- aidcp-edge 9f1fad8 -->
- [x] 1.4 单测：`SelfChromeProvider` 透传 `launchChrome` 的入参与返回（注入桩，不起真浏览器）<!-- aidcp-edge 9f1fad8 -->

## 2. aidcp-edge — AdsPowerProvider

- [x] 2.1 实现 `AdsPowerProvider.launch()`：`GET /api/v1/browser/start?...` → 解析 `data.debug_port` → 轮询 `/json/version` 就绪 → 返回 `LaunchedBrowser` <!-- aidcp-edge 9f1fad8 -->
- [x] 2.2 `kill` / `killAndConfirmDead`：调 `browser/stop?user_id=` + 轮询 `browser/active` 确认已关（status≠Active）；无法确认返回 false <!-- aidcp-edge 9f1fad8 -->
- [x] 2.3 本地 API 客户端：base / api-key / user_id 经 env（`AIDCP_ADS_API_BASE` 默认 `http://local.adspower.net:50325` / `AIDCP_ADS_API_KEY` 作 Bearer、不落库 / `AIDCP_ADS_USER_ID`），≥1.1s 串行节流避开 1req/s 限速 <!-- aidcp-edge 9f1fad8 -->
- [x] 2.4 `launch_args` 固定桌面视口 `--window-size=1440,980` + 起始页（避免小红书窄屏布局变体）<!-- aidcp-edge 9f1fad8 -->
- [x] 2.5 诚实失败红线：API 不可达 / `code≠0` / 无 `debug_port` → 报错停手，**绝不回落 self、绝不假成功** <!-- aidcp-edge 9f1fad8 -->
- [x] 2.6 单测：start 成功→就绪→交付句柄 / start 失败（code≠0 / 无 port / 不可达）→诚实报错 / stop→active 确认（注入 fetch 桩）<!-- aidcp-edge 9f1fad8 -->

## 3. aidcp-edge — main.ts 装配 + stealth env 开关

- [x] 3.1 `main.ts` 按 `AIDCP_BROWSER_PROVIDER`（默认 `self`）选 provider，`provider.launch(...)` 取代 `launchChrome(...)` 直调；用返回的 `endpoint` 接 `attachToPage`，attach 及以下零改动 <!-- aidcp-edge 9f1fad8 -->
- [x] 3.2 `attachOpts.stealth` 由 `AIDCP_STEALTH` 注入，缺省随 provider（`self`=on / `adspower`=off）；接到 `session.ts` 既有 `stealth` 开关 <!-- aidcp-edge 9f1fad8 -->
- [x] 3.3 未登录 / 读身份失败仍走现有诚实 halt，`adspower` 模式失败不回落 self（注释同步更新）<!-- aidcp-edge 9f1fad8 -->
- [x] 3.4 反检测恰一层生效：`adspower`+stealth-off → `navigator.webdriver` 不暴露——已由 PoC C3 真机验证（2026-06-27）<!-- aidcp-edge scripts/adspower-poc.ts -->

## 4. aidcp-edge — 回归与真机

- [x] 4.1 `npm run typecheck`(0 错) + `npm test`(376/376) + `npm run test:acceptance`(11/11) 全绿；self 默认路径行为逐字不变 <!-- aidcp-edge 9f1fad8 -->
- [x] 4.2 安全红线回归：provider 失败 MUST NOT 静默回落 / 假成功（test 含 code≠0 / 无 port / 不可达三例断言 rejects）<!-- aidcp-edge 9f1fad8 -->
- [x] 4.3 真机灰度：用正式 `AdsPowerProvider` 启动 profile `k1e0awu5`（aidcp-graytest），`scripts/adspower-poc.ts` **C1-C5 全绿**——attach / 导航 explore / webdriver 未暴露 / `readSelfIdentity` 读出 accountId=66cd1d4f000000001d0314ee（source=in-place）/ 拟人滚动 winY 0→1400 + 懒加载卡片 120→252。<!-- 2026-06-27 真机全绿。注：profile 直连无代理→IP 非独立（属 B 阶段防关联）；完整 cloud 自动浏览闭环（npm start adspower 连生产云）未跑，可选、待 go -->

## 5. aidcp（中控）— 跨 change 协调 + 文档 + 校验

- [x] 5.1 软化 `multi-account-node-support` 指纹浏览器 Non-Goal：`proposal.md` 末条 + `specs/chrome-instance-isolation/spec.md:25`，从「MUST NOT 引入第三方指纹浏览器」改为范围说明 <!-- aidcp c7fd533 同步软化 proposal + spec + design(Non-Goals/D5) 四处 -->
- [ ] 5.1a apply 阶段须复核：`multi-account-node-support` 归档时，软化后的 `chrome-instance-isolation` 措辞正确并入 baseline，且与本能力 `pluggable-browser-provider` 不冲突
- [x] 5.2 回写 `aidcp/docs/anti-detection.md`（注：在**umbrella** 仓非 edge）Phase 3 + §8：指纹浏览器接入由路线图转实现指针（本 change + `browser-provider.ts` + `scripts/adspower-poc.ts`）<!-- aidcp 本提交 -->
- [x] 5.3 `openspec validate adspower-browser-provider --strict` 通过
- [x] 5.4 tasks 进度按 sub-repo 分节回写本仓，完成项标 `[x]` 并附 `<!-- <repo> <commit-sha> 备注 -->` <!-- aidcp 本提交 -->

## 6. aidcp-edge — 默认 provider 翻转为 adspower（BREAKING，用户 2026-06-27 拍板）

- [x] 6.1 `selectBrowserProvider` 缺省 self→adspower；模块 header / 函数 doc / `main.ts` header env 文档同步 <!-- aidcp-edge 3653a0a -->
- [x] 6.2 self 专属路径钉回 self：`scripts/launch-multinode.ts` 冻结 env 设 `AIDCP_BROWSER_PROVIDER='self'`（槽位=端口+目录 self 专属）；`src/electron/main.cjs` spawn env 钉 self（`'self'` 在前、`...process.env` 可覆盖）<!-- aidcp-edge 3653a0a -->
- [x] 6.3 更新单测（默认 adspower 缺 user_id 报错 / 默认 adspower 全配 / 显式 self）；typecheck 0 / 全量 380 / acceptance 11 全绿 <!-- aidcp-edge 3653a0a -->
- [x] 6.4 spec / proposal / design 同步「默认 adspower + BREAKING + self 专属路径钉回」措辞 <!-- aidcp 本提交 -->

## 7. aidcp-edge — adspower 多开编排（resolve design OQ#1）

- [x] 7.1 `scripts/launch-multinode.ts` 加 adspower 分支：`AIDCP_ADS_USER_IDS="prof1,prof2"` → 每 profile 一个 adspower 节点；端口/用户数据目录/指纹/IP 由 AdsPower 自管、无需分配；edgeId 默认 `ads-<profileId>`；`AIDCP_ADS_API_KEY/BASE` 随父环境继承 <!-- aidcp-edge da5ba98 -->
- [x] 7.2 未设 `AIDCP_ADS_USER_IDS` 仍走原 self 多节点（行为不变）；看护/重起/信号两模式共用；新增 `AIDCP_MULTINODE_PRINT=1` 干跑 <!-- aidcp-edge da5ba98；干跑实测 adspower 2 profile / self 2 槽位计划正确，scoped typecheck 0 错 -->
- [x] 7.3 前提确认：云端多租户 `multi-account-node-support` 已部署 ECS（2026-06-25，cloud 497d1bc+a38fb96）→ 两 edge 两账号不串号；非 default 账号须先后台配人设否则诚实人设闸拒启 <!-- 据 multi-account-node-support tasks §7.3/§2 -->
- [x] 7.4 真机灰度：起 2 个 adspower 节点（profile k1e0awu5=账号66cd / k1e0ero8=账号63e2）跑通**双号并行连云闭环**——各起各浏览器、各读各账号、sess-1/sess-2 隔离、各刷各 feed、**不串号**（生产云多租户生效）<!-- 2026-06-27 真机实测 -->
  - 附带修复 launcher Windows 既有 bug：原 `spawn(.bin/tsx)` Windows ENOENT → 改 `spawn(node --import tsx)` 跨平台 <!-- aidcp-edge 559a18c -->
  - 待用户核：账号63e2 据称未绑人设却直接浏览——确认后台人设闸是否对其生效

## 9. aidcp-edge — 桌面外壳应用内 provider 选择 + 全量中文化（2026-07-01，反转 §6.2 桌面钉回 self）

> 用户要桌面主用路径也走 AdsPower（防关联），同时保留一键切回本机 Chrome；面板全量中文化。反转 §6.2「Electron 桌面外壳 spawn env 钉 self」。改动仅在 Electron 外壳（`src/electron/`），核心 provider 层（§1–§3）零改动。

- [x] 9.1 设置持久化：`userData/settings.json` 存 `{ provider, adsProfileId, adsApiKey, adsApiBase }`；`loadSettings`/`saveSettings`（默认 provider=adspower）；`saveSettings` 返回 `{ok,error}`——**写盘失败诚实回报、不谎报成功**（红线）<!-- aidcp-edge ee04a42 -->
- [x] 9.2 provider env 派生：`buildProviderEnv()` 按选择产出 `AIDCP_BROWSER_PROVIDER` + adspower 的 `AIDCP_ADS_USER_ID`/`AIDCP_ADS_API_KEY`/`AIDCP_ADS_API_BASE`；provider env 在前、被 `...process.env` 覆盖（外部逃生阀保留）；`startEdge` 用之取代原钉死的 `'self'` <!-- aidcp-edge ee04a42 -->
- [x] 9.3 启动流程分派：`startFlow` 按 provider 分派——`self` 走原 `launchChromeAndGateEdge`（自起 9222 + cookie 登录门）；`adspower` 走 `startAdsPowerFlow`（不自起 Chrome、不轮询，委托核心经 AdsPower；缺分身 id → 面板「待配置」诚实提示，不派生核心）<!-- aidcp-edge ee04a42 -->
- [x] 9.4 有序重启统一出口 `stopAndRestart`（保存 / 恢复 / 重新登录复用）：核心在跑则 SIGTERM 后经 exit 回调按新 provider 起（避开 `startEdge` 的「已在跑则跳过」竞态）；**退出 / 暂停途中作废在途重启**（`quitApp`/`pauseEdge` 清 `restartPending`、exit 分支 `!isQuitting` 守卫）→ 杜绝关闭后孤儿核心、暂停被复活覆盖 <!-- aidcp-edge ee04a42 修 adversarial review 4 项 -->
- [x] 9.5 IPC + preload：`settings:get`/`settings:save`（save 后 restart，返回 `saveOk`/`saveError`）/`browser:openAdsDownload`（`shell.openExternal` 到 `https://www.adspower.net/download`）<!-- aidcp-edge ee04a42 -->
- [x] 9.6 面板 UI：provider 分段切换 + AdsPower 配置（分身 id 必填 / API key 可选 / API base 可选）+「下载 AdsPower」入口；全量中文化（HTML / renderer.js 徽标文案 / main.cjs 状态消息 / 托盘菜单）；徽标 className 仍用英文状态码保 CSS 上色，仅展示文案本地化 <!-- aidcp-edge ee04a42 -->
- [x] 9.7 异常退出提示 adspower 化：核心非零退出（最常见 = 分身未登录致身份确立失败 exit 1）弹窗提示去 AdsPower 窗口登录后「重新登录」+ 查 AdsPower 客户端 / 本地 API / 分身 id <!-- aidcp-edge ee04a42 -->
- [x] 9.8 验证：三 electron 文件 `node --check` 通过；jsdom 无头冒烟 21 项（中文化 / 徽标上色 / provider 切换 / 待配置提示 / 保存门 / api key 透传 / 下载外链 / 状态推送）+ 写盘失败诚实提示 1 项全绿；edge `npm run typecheck` 0 错；`selectBrowserProvider` 契约（默认 adspower / 缺 user_id 报错 / 显式 self）回归绿 <!-- aidcp-edge ee04a42 -->
- [x] 9.9 对抗性多 agent 评审（4 维 + 独立复核）：查出并修 4 项确认缺陷——退出途中孤儿核心重生 / 暂停被在途重启覆盖 / self 缺 Chrome 残留绿色「运行中」/ 设置写盘失败谎报已保存（红线）<!-- aidcp-edge ee04a42 -->
- [x] 9.10 文档：`aidcp-edge/OPERATOR.md` 改写为双 provider（AdsPower 默认 + 本机 Chrome 可切）安装 / 配置 / 登录 / 排查；spec delta 加「桌面外壳内可选浏览器 provider 且默认 adspower」需求 + 4 场景，narrow 原「self 专属编排路径」为仅命令行多节点；proposal/design 同步（D8）<!-- aidcp / aidcp-edge ee04a42 -->

## 8. 待办（延后/可选）

- [ ] 8.1 5.1a：`multi-account-node-support` 归档时复核软化措辞并入 baseline（见 5.1a）
- [ ] 8.2 单账号完整 cloud 闭环真机灰度（`AIDCP_BROWSER_PROVIDER=adspower npm start` 连生产云，可选）
