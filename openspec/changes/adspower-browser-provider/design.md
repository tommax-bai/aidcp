## Context

edge 今天**自己 spawn 真实 Chrome** 并经 CDP 接入：`launchChrome`（`chrome-launcher.ts:585`）发现路径 / spawn / 探测 `/json/version` / 默认诚实拒绝复用 / 清单例锁 / `killAndConfirmDead`，返回 `ChromeInstance`（`pid` / `reused` / `kill` / `killAndConfirmDead`，`chrome-launcher.ts:85`）；`main.ts:88` 拿到它后 `attachToPage`（`session.ts:65`）连上 `debug_port`，其下的 targets / 定位 / 拟人 / `readSelfIdentity` 全部工作在这个 CDP 会话上。反检测是**自研 CDP 注入式 stealth**（`stealth-injector.ts`，默认开、只抹自动化痕迹、刻意不伪造 canvas/webgl/ua/时区——一机一号真实指纹），且**无代理、无 WebRTC 防泄露**（源码 grep 零命中）。

`multi-account-node-support`（35/36，未归档）把同机多账号的**进程 / 端口 / 目录 / 路由 / 账号**隔离做完了，但其 `chrome-instance-isolation` 明确 **MUST NOT 引入第三方指纹浏览器**、Non-Goal 写「同机不同账号防关联非本次范围（edge 仍一机真实指纹）」。规模化多账号要防关联，就要补上**每账号独立指纹 + 独立 IP**——这正是 AdsPower 这类反关联浏览器的本职。

约束（项目铁律）：边轻云重、状态单写、**绝不静默假成功 / 绝不静默回落**、协议 v2 不漂移、DOM-first 定位三闸与 CdpClient 重连不可破。AdsPower 本地 API：`http://local.adspower.net:50325`，`browser/start|stop|active`，限速 **1 req/s**，开安全校验时 `Authorization: Bearer <key>`，`start` 返回标准 `debug_port` + `ws.puppeteer`。

## Goals / Non-Goals

**Goals:**
- 让 edge 能**可选**地把浏览器启动 / 生命周期托管给 AdsPower 指纹浏览器，实现同机多账号**防关联**（每 profile 独立指纹 + 独立代理 + 独立账号）。
- **接缝最小**：只换「启动 / 生命周期」一层，CDP attach 及以下（定位 / 拟人 / 读身份）**零改动**。
- **默认零变化**：`self` 仍是默认 provider，自起真实指纹 Chrome，行为同今天；AdsPower 为显式 opt-in。
- 修订 `multi-account-node-support` 把指纹浏览器列为绝对禁止的 Non-Goal，画清「默认 self / opt-in AdsPower」边界。

**Non-Goals:**
- 替换或弱化默认 `self` 路径；为 self 模式补任何指纹伪造。
- 自建指纹引擎 / 自管代理池（指纹与代理由 AdsPower profile 承载、由运营配置）。
- 任何 cloud / console / 边-云协议改动——accountId 仍由 `readSelfIdentity` 从登录态读出，账号归并 / 风控 / 多租户仍按 `multi-account-node-support`。
- 把多 profile 的编排拉起塞进 edge 核心（保持边缘薄；编排留在 `scripts/` 之外，沿用 `multi-account-node-support` 边缘薄原则）。

## Decisions

### D1. provider 抽象边界 =「换启动层、留连接层」
**选择**：新增 `src/cdp/browser-provider.ts`，定义 `BrowserProvider { launch(opts): Promise<ChromeInstance> }`，**复用现有 `ChromeInstance` 形状**（`pid` / `reused` / `kill` / `killAndConfirmDead`）。两实现：`SelfChromeProvider`（直接调现有 `launchChrome`）、`AdsPowerProvider`（调本地 API 拿 `debug_port`）。`main.ts` 只把「`launchChrome(...)` → provider.launch(...)」这一行换掉，`attachToPage({host,port})` 及以下**完全不动**。
**理由**：AdsPower 的 `start` 返回标准 DevTools `debug_port`（`/json` / `/json/version` / ws 都在），与 edge 接入层天然兼容——PoC 已真机验证现成 `attachToPage` 零改动连上（C1 ✅）。把抽象边界精确切在「启动 / 生命周期」与「CDP 接入」之间，改动面最小、风险最低。
**取舍 / 备选**：① 直接在 `main.ts` 里 if/else 两条启动路径——否决，启动逻辑会和身份 / 反检测装配缠在一起、难测；② 走 AdsPower 的 Selenium/Puppeteer SDK——否决，会绕开 edge 自研裸 CDP 接入层、等于重写定位 / 拟人。

### D2. provider 选择经 env，默认 `self`，非 BREAKING
**选择**：`AIDCP_BROWSER_PROVIDER ∈ {self, adspower}`，缺省 `self`。未设 = 今天的行为，逐字等价。
**理由**：opt-in 才动新路径，存量单机 / 多节点部署零影响；回滚 = 不设该 env。

### D3. AdsPower 生命周期映射 + 诚实失败不回落
**选择**：`AdsPowerProvider.launch()` = `GET /api/v1/browser/start?user_id=<id>&ip_tab=0&headless=<0|1>&launch_args=[...]`（带 Bearer 如配置）→ 解析 `data.debug_port` → 轮询 `/json/version` 就绪 → 返回 `ChromeInstance`，其中 `kill`/`killAndConfirmDead` 调 `browser/stop?user_id=` 并轮询 `browser/active` 确认已关。本地 API 调用串行节流（≥1s 间隔，避开限速）。**任一步失败（API 不可达 / `code≠0` / 无 `debug_port` / profile 未登录致 `readSelfIdentity` 读不出）→ 诚实报错停手**，MUST NOT 静默回落 `self`、MUST NOT 假成功。
**理由**：延续全仓「绝不静默假成功」红线；静默回落 self 会让「本该用独立指纹 / IP 的账号」偷偷以本机真实指纹 + 本机 IP 起跑——正是防关联要避免的最坏情况，必须诚实失败让运营介入。
**取舍**：`killAndConfirmDead` 从「自己 SIGTERM/SIGKILL 确认端口释放」变成「调 AdsPower stop + active 确认」——失去对进程的直接控制，换取不自管指纹浏览器多进程外壳。`reused` 字段对 AdsPower 语义=「外部托管」（`pid=null`）。

### D4. 反检测层归属：AdsPower 模式关 edge stealth、由 cdp_mask 独占
**选择**：新增 `AIDCP_STEALTH ∈ {on, off}`，`main.ts` 据此设 `attachOpts.stealth`。**默认值随 provider**：`self → on`（保持现状）、`adspower → off`。
**理由**：AdsPower 内核自带指纹伪造 + `cdp_mask`（默认开）。若再叠 edge 自研 stealth，两层会对 `navigator.webdriver` / plugins / `toString` 重复打补丁、甚至 UA 说一套字体说另一套——**指纹的命门是自洽，不是改得多**，双层反而制造新的可识破点。PoC C3 已验证「cdp_mask 开 + edge stealth 关」自洽（`navigator.webdriver=false`、`window.chrome=true`、UA 一致）。
**备选**：保留 edge stealth、关 AdsPower cdp_mask——否决，等于放弃 AdsPower 真 canvas/webgl/ua 指纹这一买它的根本理由。

### D5. AdsPower 模式经 launch_args 固定桌面视口
**选择**：`launch_args` 传 `["--window-size=1440,980"]`。
**理由**：小红书 web 是响应式双布局，视口不固定会落进窄屏变体致定位 / 滚动 / 本人锚点选择器全套失效（见 `docs/xhs-layout-states.md`，2026-06-27 真机校准元凶）。self 模式的 `buildChromeArgs` 已固定视口；AdsPower 模式经 `launch_args` 补回同一约束。

### D6. 防关联绑定契约：1 profile = 1 指纹 = 1 IP = 1 账号
**选择**：作为**运维 / 配置契约**（spec 写明，edge 不强制枚举）：每个 AdsPower profile 绑定唯一指纹 + 唯一独立 IP（住宅代理优先）+ 唯一小红书账号，长期稳定。**指纹绑账号、不绑任务 / 进程**：同一账号 MUST NOT 配多套指纹 / 多个 IP（= 平台「换设备登录」告警）。
**理由**：这正是 `anti-detection.md` Phase 3「profile × 指纹 × IP 三元绑定」。代理质量是命门——同一出口 IP 跑多账号，指纹再不同也会被 IP 维度关联，故独立 IP 与独立指纹同等必要。edge 侧无法、也不该校验「IP 是否真独立」，这是运营配 AdsPower profile 的责任，spec 以约束形式固化、不在 edge 代码强制。

### D7. Non-Goal 修订用跨 change 协调，不做 baseline MODIFIED delta
**选择**：`chrome-instance-isolation` 尚未并入 baseline `openspec/specs/`（仍在未归档的 `multi-account-node-support` delta 中），故本 change **不**建 `specs/chrome-instance-isolation/` 的 MODIFIED delta（否则 `validate --strict` 找不到 baseline 需求而失败）。改为**直接软化 `multi-account-node-support` 自身**的两处措辞：`proposal.md` Non-Goal 与 `specs/chrome-instance-isolation/spec.md:25`，从「MUST NOT 引入第三方指纹浏览器」改为范围说明「该 change 本次不引入；同机防关联经 change `adspower-browser-provider` 以显式 opt-in provider 接入」。本 change 只 ADD 新能力 `pluggable-browser-provider`。
**理由**：两 change 并行活跃，软化措辞使其不矛盾、且都过 strict 校验；待 `multi-account-node-support` 归档后，软化后的措辞并入 baseline，与本能力一致。
**取舍**：若先于 `multi-account-node-support` 归档本 change，则那条软化措辞要在对方归档时随其 delta 合入——错峰协调，二者归档顺序不强制，但软化动作须在两 change 都活跃时一次做掉。

## Risks / Trade-offs

- **[新增付费常驻依赖]** AdsPower 客户端 + 本地 API 服务（50325）须常驻、按 profile 计费 → 仅 `adspower` 模式需要；`self` 默认路径零依赖，回滚即切回 self。
- **[本地 API 限速 1 req/s]** 多 profile 并发 start/stop 可能触限 → provider 内串行节流（≥1s 间隔）；CDP 流量直连 `debug_port`、不过 50325，不受限。
- **[双层反检测误配更危险]** 若误把 edge stealth 与 cdp_mask 都开 / 都关 → 自洽被破或裸奔 → 默认值随 provider 锁死（self=on / adspower=off），并在 spec 写明二者**恰一层生效**。
- **[失去自管生命周期]** `killAndConfirmDead` 改信任 AdsPower stop+active → 回收确认精度下降 → 轮询 `browser/active` 确认 + 超时诚实报告，不假装已关。
- **[代理质量 = 防关联命门]** AdsPower profile 若挂同一 / 失效 IP，指纹再独立也会被 IP 关联（PoC 里 demo profile 的 US 代理就连不上小红书）→ D6 契约强制独立 IP；上线前逐 profile 验证「能到小红书 + IP 独立 + 已登录」。
- **[与 multi-account-node-support 协调]** 软化其 Non-Goal 措辞须在两 change 都活跃时一次做掉，避免归档顺序导致措辞漂移 → 列入 tasks 显式协调项。

## Migration Plan

1. **edge 实现（默认不启用）**：落 `browser-provider.ts` + `SelfChromeProvider`（包 `launchChrome`）+ `AdsPowerProvider` + `main.ts` 按 env 选 provider + `AIDCP_STEALTH` 接线。`self` 默认路径行为逐字不变，先全量回归（`npm test` / `test:acceptance` / `typecheck` 绿）。
2. **跨 change 协调**：软化 `multi-account-node-support` 的指纹浏览器 Non-Goal 措辞（proposal + chrome-instance-isolation spec）。
3. **运维准备**：逐账号建 AdsPower profile（独立指纹 + 独立住宅 IP + 登录目标小红书号），记 `user_id`；验证每个 profile 「能到小红书 + 已登录」（可复用 `scripts/adspower-poc.ts`）。
4. **灰度启用**：先单账号 `AIDCP_BROWSER_PROVIDER=adspower AIDCP_ADS_USER_ID=<id>` 跑通真机闭环，再扩多账号。
5. **回滚**：不设 `AIDCP_BROWSER_PROVIDER`（或设 `self`）即切回自起 Chrome，零依赖、向后兼容。

## Open Questions

1. 多 AdsPower profile 的同机并行编排是否纳入现有 `launch-multinode.ts`（加 `adspower` 分支：用 `user_id` 列表替代端口 / 目录分配），还是本 change 只做单 provider、编排留后续？（倾向：本 change 只做 provider 抽象 + 单实例 opt-in，多 profile 编排另起。）
2. `AdsPowerProvider` 的 API base / api-key / user_id 经哪些 env 暴露（`AIDCP_ADS_API_BASE` / `AIDCP_ADS_API_KEY` / `AIDCP_ADS_USER_ID`），api-key 的读取与不落库纪律（沿用「不记敏感值」铁律：只记读取方式、不写值）。
3. 代理是否完全交给 AdsPower profile，还是 edge 侧也要暴露逃生阀——倾向完全交给 AdsPower（D6），edge 不碰代理。
