## Context

浏览闭环在「离页巡视 / 深读后返回列表」时依赖 `navigateBack`（`aidcp-edge/src/browse/browse-session.ts:1364-1396`）。当前逻辑：先关浮层，再判断「是否在作者主页」——**只有在作者主页时跳过浏览器后退、改整页导航**；其余一律 `history.back()`。

问题：从**通知页**这类整页离页动作返回时，当前 URL 是 `/notification`，落不进「作者主页」白名单 → 照走 `history.back()`。而通知巡视是把 `/notification` 压在**上一条仍在历史里的笔记详情**之上（`note.open` 是真实点击开的 modal，SPA pushState 出 `/explore/<id>?xsec_token=...`）。`history.back()` 只撤销 `/notification` 一格 → 落回那条**笔记详情**；小红书的 `xsec_token` 是临时票据、易过期（尤其搜索来源），过期后该详情页 = 反爬错误页 `error_code=300031「当前笔记暂时无法浏览」`。

这堵瞬时坏页被旁路遮罩监测（`aidcp-edge/src/browse/overlay-monitor.ts`，1s 轮询、`none→unknown` 第一轮差异即触发、无去抖）按形状/尺寸/iframe 启发式（无任何语义文案）判成 `unknown`，边缘经 `main.ts` 的 `watcherSupervisor` overlay 分支上报 `risk.captcha_detected{kind:'unknown'}`。云端据既有映射 `unknown→light→warned`（能力 `captcha-incident-handling`）把账号打成 `warned` 并在传输层暂停该 edge（`sent=0`）。`warned` 持久化且不自动回滚。净效果：一次自愈得掉的瞬时坏页闪现，换来整会话停摆 + 账号被无谓标黄。

现状已有一层**被动兜底**（`browse-loop-resilience` 的「返回后须对 404/坏页健壮」）：`history.back()` 落坏页后会 `Page.navigate` 回良好列表并健康校验再上报。但它发生在**坏页已经渲染并被监测抓到之后**——救得回页面，救不回那次误报。

事故实证：account `66cd1d4f000000001d0314ee` / edge `ads-k1e0awu5`，2026-07-01 19:39:00，`captcha detected kind=unknown status=warned url=/explore`。

## Goals / Non-Goals

**Goals:**
- 从源头消除「离页返回回踩失效 token 笔记详情 → 300031 闪现」这条路径（预防，非事后自愈）。
- 让最低置信的 `unknown` 瞬时遮罩不再一闪就惊动云端 / 迁移账号状态（纵深防御）。
- 全程不弱化真验证码 / 登录墙的即时 fail-CLOSED 秒报秒停。
- 零协议 / 零云端改动，代码只落 `aidcp-edge` 一仓。

**Non-Goals:**
- 不新增「识别 300031 文案 → 判笔记级墙」的语义分类器（YAGNI：根因删除后这堵墙不再产生；靠文案分辨账号级 vs 笔记级有漏报真封禁风险）。
- 不改造监测体基类的定时器 / 时钟注入 / 接口（根因删除后导航期抑制窗无事可抓）。
- 不改云端 `RiskController` 的 `kind→signal→state` 映射、暂停 / 恢复语义（修复在其上游）。
- 不动 `warned` 的持久化与「清除不自动回滚风控状态」这一有意设计（由既有恢复窗口 / 人工命令 / 活跃 change `restore-auto-resume-and-global-safety-config` 负责恢复）。

## Decisions

### 决策 1：返回手势判据从「按 URL 猜主页」升级为「是否盖着笔记浮层」

`navigateBack` 三分支替换现有 `onProfile` 单条判据（用现成 `this.deps.modalCtrl.isModalOpen()`，须在 `safeCloseModal()` 之前抓一次 `modalWasOpen`）：
- **已在目标列表**（feed `EXPLORE_FEED_RE` / search `/search_result/`）→ 不后退、不重载（关浮层列表即露出，滚动位由 SPA 保住）。
- **不在列表 + 有笔记浮层** → `history.back()`（唯一保留的后退路径）。卡片真实点击开的浮层，其上一条历史必是来源列表，后退安全且保滚动位。
- **不在列表 + 无浮层**（通知 / 主页 / 任意整页离页返回）→ 跳过后退，直接 `Page.navigate(this.exploreUrl)`（search 来源仍按既有 `targetPage` 语义回搜索结果）。前向进带新鲜 token 的列表，永不回踩失效详情。
- 既有健康校验兜底（`browse-session.ts:1386-1393`）原样保留当安全网，判据改用重算的 `onList`。`back ok:true` 回执契约不变。

**为什么不用「按 URL 猜是不是笔记详情页」**：URL 判据脆（`/explore/<id>` 与 `/explore` 前缀近似、search 来源另有形态），且无法覆盖「历史栈里上一格是什么」。「头上有没有浮层」直接对应「后退会不会落回详情」，语义更准、一次覆盖主页 / 通知 / 未来任何 excursion。

**Alternatives considered:**
- **B — 让监测体语义识别 300031 文案、判成笔记级墙**：根因删除后无墙可识；且有漏报真封禁的欠反应风险；还要真机标定这堵墙的 DOM 命中面。弃。
- **C 完整体 — 导航期开 settle 抑制窗 + 覆写 watcher**：根因删除后抑制窗抓不到东西；在安全关键的旁路监测里加机关，性价比差。只取其内核（见决策 2）。

### 决策 2：低置信 `unknown` 云端上报加一轮持续性确认

`main.ts` 的 `watcherSupervisor` overlay 分支（`none/…→unknown` 翻转）当前第一轮探测差异就发 `risk.captcha_detected`。改为：`to==='unknown'` 时**不立即发**，延后约一个轮询周期（~2×pollMs）再读 `overlayMonitor.state` 公有态，仍为 `unknown` 才发；已自愈成非阻断则**既不发 `detected` 也不发孤儿 `cleared`**。`captcha` / `login` 指纹类分支**保持即时**，不经任何延后。本地停手闸（`waitWhileBlocked` 读 `.state`、`isBlockingKind` 含 `unknown`）**不动**——瞬时 `unknown` 期间边缘仍会本地短暂停手、自愈即恢复，只是不再惊动云端 / 打 `warned`。

**为什么必做**：这是一条独立于返回路径的脆弱点——任何蹭到 catch-all 形状启发式的 ~1s 瞬时物都能一次性把账号打成 `warned`+暂停。决策 1 删的是「返回路径」这一个源，决策 2 兜住「其它任何瞬时 unknown」这一整类。

### 决策 3：自愈自动上报 `cleared` 复用现状，仅补配对不变量

`main.ts` 已有「阻断态→非阻断态翻转发 `risk.captcha_cleared`」（现役 `main.ts:433-441`）。不新写；仅保证决策 2 的确认闸「只有真发过 `detected` 才发 `cleared`」，不产生无配对的孤儿 `cleared`，也不遗留已发未清的 `detected`。

## Risks / Trade-offs

- **[决策 1 误判浮层态]** `isModalOpen()` 偶发误报 false（本有浮层却判无）→ 最坏退化成「整页重载丢滚动位」（安全侧），绝不会变成闪现或落错页。→ Mitigation：判据用 note-open 同款探测（`modal-controller.ts`），真机验收覆盖。
- **[决策 1 嵌套历史栈残留]** 连开两笔记中途不回列表、关浮层没弹掉被压详情态时，历史栈 `[feed, 详情A, 详情B]`，后退仍可能落失效详情 A 一闪。→ Mitigation：决策 2 的持续性确认闸兜住这类瞬时闪现，不上报云端。
- **[决策 2 延迟真·新型 unknown 墙上报 ~一个轮询]** 真持续的未知阻断墙晚约 2s 才上报。→ Mitigation：只延后最低置信桶、fail-toward-reporting（仍在就照报）；`captcha`/`login` 不延后。可接受。
- **[决策 2 欠报风险]** 确认窗设太长会漏报真阻断。→ Mitigation：窗口取 ~2×pollMs（≈2s），远短于人工响应尺度；本地停手对 `unknown` 仍即时。
- **[总体]** 纯边缘内改动，零协议 / 零云端，AC-PROTO / AC-RISK 不受影响需回归验证仍绿。

## Migration Plan

1. `aidcp-edge` 落两处改动 + 单测（含事故回归）。
2. `npm run test:acceptance`（AC-PROTO/AC-RISK 全绿）→ `npm test` → `npm run typecheck`。
3. 打包边缘（本地跑、连 `ws://121.89.85.150:8787`），真机分身跑验收序列。
4. Rollback：改动局限 `navigateBack` 与 `main.ts` overlay 分支两处，回退即恢复原判据 / 原即时上报，无状态迁移、无数据变更、无协议兼容问题。

## Open Questions

- 关浮层后 URL 是否弹回 feed（决定「有浮层」分支后退能否保住滚动位）——推荐的 `onList` 短路对两种情况都安全，具体保滚动位行为待真机确认。
- 决策 2 的确认窗精确取值（1×vs 2×pollMs）——真机对照「瞬时闪现被抑制」与「真墙及时上报」后定。
