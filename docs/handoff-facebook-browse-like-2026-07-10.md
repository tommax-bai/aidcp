# Handoff — Facebook 浏览 + 点赞（Change B）续做（2026-07-10）

> 面向接手的新 session。语言：正文中文，代码/命令/标识符英文（CLAUDE.md §6）。
> 这是把 Facebook "按人设筛选内容 → 点赞 / 评论" 真正跑起来的续做交接。**读完即可续做。**

## 0. 一句话现状

- **养号纪律脊柱（Change A）已实装 + 全绿 + 部署 ol + 真机冒烟通过**。
- **"按人设筛内容 → 点赞 / 评论" 的大脑已现成且平台无关**（`content_evaluator` 按人设兴趣筛卡、`interaction_appraiser` 按人设点赞标准判点赞），XHS 在用、FB 可原样复用。
- **唯一缺口 = FB 浏览 + 点赞能力（Change B，本文档续做）**：FB driver 无 `browse`/`interact` 能力 → 平台闸拒（真机实测 `platform_no_browse`）→ 没 feed 可刷 → 大脑空转。
- 全部在隔离分支 `feature/fb-full-integration`（三仓），与主版本隔离；隔离期真机在 **ol**，不碰 dev。

## 0.4 实装完成（2026-07-10 深夜，接手先读这条）

- **Change B（FB 浏览+点赞闭环）代码已全部实装 + land + 全绿**：edge `4c9ce61` / cloud `b302251`（隔离分支 `feature/fb-full-integration`，已 push）。edge 单测 913 + acceptance 16、cloud 单测 1770 + acceptance 47、两仓 typecheck 干净、`openspec validate --strict` 过、**零改 protocol.ts**。
- **做了什么**：edge `src/facebook/` 新增 feed-reader（role=feed>role=article 扫卡、跳虚拟化空壳、collect 恒 0）、post-reader（permalink→role=dialog 深读正文+评论+计数）、like-executor（帖级 `留下心情` toggle、in-page element.click、后置校验真翻转才 ok、shadow）、cta-labels（多语言反应词匹配 + 数字守卫）、consent（forward-port）、facebook-session（独占单槽 browseHandler、内含评论/加群委托、三态 AIDCP_FB_BROWSE_AUTO kill switch、每命令恰一诚实回执 + 有界超时放行链）。driver 声明 browse/interact、main.ts 按 `usesFacebookBrowseSession` 分支、FB 验证码/软限流上报云端。cloud registry facebook 加 browse/interact/join、session-start 闸放行。
- **对抗性评审已修**：critical bug（reactState 把「赞+数字」反应计数按钮误当已赞 toggle → 点赞在任何有反应的帖上变 no-op / 假 already_liked）已修 + jsdom 回归；FB 验证码/软限流上报云端已补（否则 Change A 的 FB 限流退避失效）。
- **仍待真机（backlog 簇 44）**：① shadow 在 ol 跑通（AIDCP_FB_BROWSE_AUTO=shadow）+ **标定「已赞」态确切 aria-label**（唯一待确认，收紧 VERIFY）；② shadow 过后放真点赞；③ 部署 cloud `b302251` 到 ol（gate 生效，edge flag 关时 dormant 安全）+ 运营机重建 edge；④ fast-follow：FB 身份自愈 IdentityWatcher（另案，防误报砸会话）。
- **下一步**：由用户明确后部署 ol → 用测试账号 `61591458584142`/env `k1ehveal` 连 `ws://123.56.253.183:8787` 跑 shadow。ol 部署按 CLAUDE.md §5 安全序列，默认关 kill switch。

## 0.5 本轮进度更新（2026-07-10 晚，接手先读）

- **测试环境已从 iPhone 指纹修成桌面 Mac**：§1/§2 假设「UA 天然桌面、移动布局纯窗太窄」**是错的**——环境 `k1ehveal` 建出来是**整套 iPhone 移动指纹**（iPhone UA + platform + touch5 + 360×780），FB 据 UA 发移动站，与窗宽无关。已用 AdsPower `user/update` 下发**显式桌面 `ua`** 修好（保留 cookie 登录）。**教训：FB 环境建完必须验 `navigator.userAgent`，别假定桌面**。详见 memory `fb-test-env-desktop-ua-fix`。
- **Change A 在 PC UA 上重跑 = 全绿**（握手 `sess-3`、平台闸 `platform_no_browse`、normal 档），桌面 feed 真出（`role=feed`+3×`role=article`、cookie 登录 Michelle Garcia）。
- **边缘补 `--start-maximized`**（edge `eaec298`，AdsPower 启动层强制宽窗，对齐 self 模式；次要加固、非 UA 根因）。
- **真机探针地基已落库**：`openspec/changes/facebook-browse-and-like-loop/facebook-browse-and-like-loop-probe-findings.md`（控制仓 `a9df78d`）——feed/detail/like 选择器全部实测钉死，**宽窄（1440/900/700）同选择器**已验（满足 spec 7.7）。**接手先读这份 findings，edge `src/facebook/` 直接照它写**（tasks 2/3/4）→ 再 cloud（task 5）→ 测试 → shadow。
- **仍缺**：点赞「已赞」态确切标识（toggle 真值）留给 shadow（task 8.2）；探针纪律：真机导航要拉开间隔，连续 resize+navigate 会触发软阻断/hydrate 失败假象。

## 1. 用户新定案（勿再反向，2026-07-10）

- **FB 自动化一律用 PC 版**：**PC / 桌面 UA**（本项目指纹模板 `DEVICE_TEMPLATES` 全是 win11/macos 桌面，无移动模板，UA 天然是桌面）+ **强制宽桌面窗（~1280px+）**。**绝不用移动版 UA / 移动布局。**
- **宽窄兼容仍是一等要求**（Change B/C spec 已固化）：选择器 DOM-first、解析不到即诚实 `no_target`。但对 FB 浏览的**首选策略 = 强制宽窗走 PC 布局**（见 §3 实测原因），窄布局只作兜底。

## 2. 真机探针关键发现（2026-07-10，Change B 选择器策略的地基）

用测试账号真机探了 FB feed 的真实 DOM（CDP 直连 AdsPower 浏览器），结论：

1. **可行性坐实**：cookie 免登录成功（账号真身 `Michelle Garcia` / id `61591458584142`），feed 真能加载出真实帖子（探到"張鈞甯 的帖 / 5339 赞 / 149 评论"），全程可经 CDP 驱动读取。
2. **移动 vs PC 布局是窗口宽度决定的，不是 UA**：AdsPower 默认把窗开在 **360px 宽 → FB 渲染移动版布局**——此时 **`role="feed"` / `role="article"` 都不存在**，取而代之是移动版私有图标字体（`󱡓` 之类）的结构，极难做。域名仍是 `www.facebook.com`、UA 仍是桌面 Mac。**纯粹是窗太窄触发响应式移动布局。**
3. **PC 布局才好做**：宽窗（≥ ~1000px）下 FB 走桌面 feed，用标准 `role="feed"` > `role="article"` + Like 按钮标准 `aria-label`。→ **Change B 第一件事就是强制宽窗。**
4. **`Emulation.setDeviceMetricsOverride` 不够**：只改 viewport override 时 `innerWidth` 仍是 360、布局不切。**必须 `Browser.setWindowBounds`（或 AdsPower 环境/启动层）真正把窗口 resize 宽**，才切 PC 布局。（探针 v5 用 `Browser.getWindowForTarget` + `Browser.setWindowBounds` 到 1360px 的路子，被用户在验证前打断，未跑完确认——**这是接手第一个要跑完的验证**。）
5. **feed 前有两道门**：① "允许 Facebook 使用 Cookie" 同意浮层（边缘已有 `src/facebook/consent.ts` 自动接受，见 memory `facebook-consent-overlay-landed`）；② 新号 getting-started 引导页（`/gettingstarted/notifications/` 开启通知 / 跳过）。Change B 的浏览进入路径要能过这两道门到 feed。探针里我用"点含 允许/跳过 文本的按钮"粗暴过门，误点到"使用 facebook 应用"promo——**正式实现要精确识别这两道门的按钮，别乱点**。

## 3. Change B 要做什么（净新增，云端大脑复用）

change 提案已在 `openspec/changes/facebook-browse-and-like-loop/`（proposal/design/tasks/spec 齐，strict 过，0 实装）。核心：

- **边缘 FB 侧（`aidcp-edge/src/facebook/`）**：
  1. 强制宽桌面窗 + PC UA + 过 consent/onboarding → 稳定进 PC feed。
  2. PC feed 选择器 → 结构化 `page.cards`（`role="article"` 抽 author / 正文 / 图文 / 反应数）。
  3. `note.detail` 抽取 + **点赞原子执行器**（后置校验按钮状态真翻转才回 `ok`，否则 `no_target`，绝不 `count||1` / 假成功）。
  4. **声明 `browse`/`interact` 能力**——**必须与 FB BrowseSession 实现原子同落**（否则装配闸把 xhs BrowseSession 误挂 FB 边端；`facebook/driver.ts` 现 `['identity','overlay','comment','join']`）。
  5. FB 浏览/点赞独立命令进 edge `onMessage` 主动命令白名单 + FB idle 看门狗（复用 browse-loop-resilience）。
- **云端（`aidcp-cloud`）**：`platform/registry.ts` facebook 加 `browse`/`interact` + 放开 `canStartSession` 平台闸；`role-dispatcher` 让 FB 走同一套双层翻译。
- **复用（几乎不改）**：`content_evaluator`（人设兴趣筛卡）、`interaction_appraiser`（人设点赞标准）——平台无关、吃结构化 `page.cards`/`note.detail`。评论支线（appraiser→composer→de-ai→approval-gate）同理复用。
- **目标零改 `protocol.ts`**（复用既有平台中立消息 + 可选载荷；避让 feed-refresh 的 `feed.refresh`）。

## 4. Change B 实装顺序（建议）

1. **edge 稳定进 PC feed**：强制宽窗（`Browser.setWindowBounds` 或 AdsPower 环境/启动层设窗口尺寸）+ 精确过 consent + onboarding → 确认 `role="feed"`/`role="article"` 出现（先把探针 v5 跑完确认）。
2. edge：`role="article"` → `page.cards` 抽取器（宽版为主）。
3. edge：`note.detail` + 点赞执行器 + 后置校验。
4. edge：声明 browse/interact 能力（原子同落 BrowseSession）+ 白名单 + 看门狗。
5. cloud：registry 放开 + session-start 闸放行 + 双层翻译接 FB。
6. 复用 content_evaluator/interaction_appraiser（人设筛选）→ 端到端"按人设点赞"。
7. 评论：复用现成评论支线。
8. 全程默认关 `AIDCP_FB_BROWSE_AUTO` + shadow（只浏览不点赞 / 点赞只记日志）→ 过 shadow 再放真点赞。
9. 真机在 ol 迭代选择器（宽窄覆盖：B tasks 7.7 / C tasks 6.5）。

## 5. 测试 harness（可复用，详见 memory `fb-integration-test-flow`）

- **建 FB 环境（cookie 免登录）**：直接调本机 AdsPower API `user/create`（指纹用 `ads-fingerprint.cjs` 的 `buildFingerprintConfig(getTemplate('macos-m2'))`；group `9997175`=aidcp-创建；remark 带 `plat:facebook`；`no_proxy`；`cookie` 注入 FB 会话 cookie）。脚本在 scratchpad，cookie 只经 env 传、不落库。
- **启核心连 ol**：`AIDCP_PLATFORM=facebook AIDCP_ADS_USER_ID=<envid> AIDCP_CLOUD_URL=ws://123.56.253.183:8787 npm run start`（或 `npm run start:ol`，edge `8a0e51d` 已加便捷脚本）。在 `aidcp-edge.wt/fb-full-integration` worktree 里跑 = FB 分支代码。
- **CDP 探针**：`browser/start` 取 debug_port → 浏览器级 ws（`/json/version`）→ `Target.createTarget` + `Target.attachToTarget{flatten}` → `Browser.setWindowBounds` 拉宽 → `Runtime.evaluate` 探 DOM。收尾 `browser/stop` + `pkill -f "tsx src/main.ts"`。
- **测试流不受配额约束**：ol 已 `AIDCP_COLDSTART_RAMP=false`（冷启动 clamp 关，测试账号回落 normal 档，comment/publish 不被 Day-1 压 0）。冷启动正确性已由单测 + 真机冒烟证过。

## 6. 台账（隔离期）

- **分支**：`feature/fb-full-integration`（三仓）。tip：控制 `41065a7` / cloud `07b6c18` / edge `8a0e51d`（本文档提交后更新）。
- **ol（FB 测试环境）**：cloud 跑 `npx tsx src/server.ts`，`/opt/aidcp/cloud`；备份 `cloud.bak.20260710-194239.tar.gz`；**共用 dev 库** `121.89.85.150/aidcp`（用户定案，新 FB 账号按 account_id 隔离）；同机仅 aidcp-cloud+nginx（无 isales）；`AIDCP_COLDSTART_RAMP=false`。启动日志确认 Change A 生效。
- **测试账号**：`61591458584142`（Michelle Garcia），platform=facebook，created_at 2026-07-10；已绑测试人设（persona_config，从现有 persona 复制，仅供测机制）。
- **AdsPower 环境**：`k1ehveal`（group aidcp-创建，no_proxy，已注入 FB cookie 免登录）。
- **安全铁律**：FB 账号密码 / 2FA / cookie 属敏感值，**绝不写仓库 / 文档 / 记忆 / commit**，只临时经 API/env 用。

## 7. 红线 / 热点提醒

- **PC UA + 强制宽窗**（用户明确要求，别用移动版）。
- browse 能力翻转**必须与 BrowseSession 原子同落**。
- 目标**零改 `protocol.ts`**。
- **后置校验防假成功**（点赞按钮真翻转才算成；找不到即 `no_target`）。
- **宽窄兼容**（DOM-first；窄版兜底）。
- 默认关 kill switch + shadow 先行。

## 8. 相关 change / 文档 / memory

- change：`facebook-browse-and-like-loop`（B）、`facebook-publish`（C）、`account-nurture-discipline-spine`（A，已实装大部）。
- 前序交接：`docs/handoff-facebook-support-2026-07-08.md`（FB 评论 / 登录 / 平台抽象）。
- memory：`fb-integration-test-flow`、`fb-full-integration-design`、`facebook-consent-overlay-landed`、`fb-group-join-observe-i18n`（真机排查法：CDP 看真 DOM + 就绪轮询）、`real-machine-test-accounts`、`adspower-env-platform-label`。
