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
