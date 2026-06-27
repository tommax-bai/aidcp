# Tasks — adspower-browser-provider

> 接缝已由 `aidcp-edge/scripts/adspower-poc.ts` 真机验证（C1 attach ✅ / C3 cdp_mask+stealth-off ✅，2026-06-27）；本 change 把 PoC 固化为正式 provider。代码改动落 aidcp-edge，进度回写本仓。

## 1. aidcp-edge — BrowserProvider 抽象 + Self 包装

- [ ] 1.1 新增 `src/cdp/browser-provider.ts`：定义 `BrowserProvider { launch(opts): Promise<ChromeInstance> }`，复用现有 `ChromeInstance` 形状（`pid`/`reused`/`kill`/`killAndConfirmDead`，`chrome-launcher.ts:85`）
- [ ] 1.2 实现 `SelfChromeProvider`：直接委托现有 `launchChrome`，入参 / 返回 / 行为逐字不变（self 默认路径零变化）
- [ ] 1.3 从 `src/cdp/index.ts` 导出 `BrowserProvider` 接口与两实现
- [ ] 1.4 单测：`SelfChromeProvider` 透传 `launchChrome` 的入参与返回（注入桩，不起真浏览器）

## 2. aidcp-edge — AdsPowerProvider

- [ ] 2.1 实现 `AdsPowerProvider.launch()`：`GET /api/v1/browser/start?user_id=&ip_tab=0&headless=&launch_args=[...]` → 解析 `data.debug_port` → 轮询 `/json/version` 就绪 → 返回 `ChromeInstance`
- [ ] 2.2 `kill` / `killAndConfirmDead`：调 `browser/stop?user_id=` + 轮询 `browser/active` 确认已关；无法确认则如实报告
- [ ] 2.3 本地 API 客户端：base / api-key / user_id 经 env（`AIDCP_ADS_API_BASE` 默认 `http://local.adspower.net:50325` / `AIDCP_ADS_API_KEY` 作 Bearer、不落库 / `AIDCP_ADS_USER_ID`），调用 ≥1s 串行节流避开 1req/s 限速
- [ ] 2.4 `launch_args` 固定桌面视口 `--window-size=1440,980`（避免小红书窄屏布局变体）
- [ ] 2.5 诚实失败红线：API 不可达 / `code≠0` / 无 `debug_port` → 报错停手，**绝不回落 self、绝不假成功**
- [ ] 2.6 单测：start 成功→就绪→交付句柄 / start 失败→诚实报错 / stop→active 确认（注入 fetch 桩）

## 3. aidcp-edge — main.ts 装配 + stealth env 开关

- [ ] 3.1 `main.ts:88` 按 `AIDCP_BROWSER_PROVIDER`（默认 `self`）选 provider，`provider.launch(...)` 取代 `launchChrome(...)` 直调；attach 及以下调用点**零改动**
- [ ] 3.2 `attachOpts.stealth` 由 `AIDCP_STEALTH` 注入，缺省随 provider（`self`=on / `adspower`=off）；接到 `session.ts:32/53` 既有 `stealth` 开关
- [ ] 3.3 未登录 / 读身份失败仍走现有诚实 halt（`main.ts:112`），`adspower` 模式失败不回落 self
- [ ] 3.4 自检「反检测恰一层生效」：`adspower`+stealth-off → `navigator.webdriver` 不暴露（复用 PoC C3 口径）

## 4. aidcp-edge — 回归与真机

- [ ] 4.1 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿；self 默认路径行为逐字不变
- [ ] 4.2 安全红线回归：provider 失败 MUST NOT 静默回落 / 假成功（新增断言）
- [ ] 4.3 真机灰度：单账号 `AIDCP_BROWSER_PROVIDER=adspower` 跑通自动浏览闭环；上线前逐 profile 用 `scripts/adspower-poc.ts` 验「能到小红书 + 已登录 + IP 独立」

## 5. aidcp（中控）— 跨 change 协调 + 文档 + 校验

- [ ] 5.1 软化 `multi-account-node-support` 指纹浏览器 Non-Goal：`proposal.md` 末条 + `specs/chrome-instance-isolation/spec.md:25`，从「MUST NOT 引入第三方指纹浏览器」改为范围说明（「本 change 不引入；同机防关联经 change `adspower-browser-provider` 以显式 opt-in provider 接入」）；两 change 都活跃时一次做掉
- [ ] 5.2 回写 `aidcp-edge/docs/anti-detection.md` Phase 3：指纹浏览器接入由路线图转实现指针（本 change + `browser-provider.ts` + `scripts/adspower-poc.ts`）
- [ ] 5.3 `openspec validate adspower-browser-provider --strict` 通过
- [ ] 5.4 tasks 进度按 sub-repo 分节回写本仓，完成项标 `[x]` 并附 `<!-- <repo> <commit-sha> 备注 -->`
