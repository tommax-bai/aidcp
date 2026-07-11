## Context

加群两次边缘调用（`src/facebook/join-executor.ts`）：观测腿 `GROUP_JOIN_OBSERVE_JS`（采集候选、挑 `mainCta`/`joinButton`、上报云端）→ 云端裁判 → 点击腿 `GROUP_JOIN_CLICK_JS`（新页重采、取文档序第一个 `join` 类节点、`element.click()`）。两腿的节点采集**逐字同源**：`document.querySelectorAll('button,a,[role="button"]')` 过 `visible` + 排 `banner/navigation/complementary`（`join-executor.ts:403-405`）。

真机取证（pending 群 `groups/311384382278852`，37 候选）：`i=2` 目标群自身「取消请求」`div[role=button]`；`i=9` **推荐群家常菜**的「加入小组」`div[role=button]`；`i=5`「发现更多小组」`a[role=link]`；`i=4`「查看推荐小组」；`i=10..28`「移除对X的推荐」逐项。推荐栏候选不带 banner/navigation/complementary 角色，**穿过现有排除**；点击腿「文档序第一个 join」会选中 `i=9` 推荐群按钮 → 加错群。

## Goals / Non-Goals

**Goals:**
- 点击腿**绝不**点到指向异群的候选（推荐栏），语言无关。
- 目标群自身控件非 join 类（pending/member/晚渲染）时，点击腿 fail-closed 诚实回报、绝不越域找 join。
- 观测腿据作用域挑群主 CTA，仍如实全量上报候选（不 fail-closed 丢原文）。
- 纯 edge、纯本地确定性 DOM 判定，零协议 / 零云端改动。

**Non-Goals:**
- 不改 pending/member/join 词表（sibling change B）。
- 不给按钮上视觉、不建 N 语字典。
- 不动 L3 后置校验（composer 跃迁）结构、不动 `pendingRequest`/`composerPresent`/`joinCtaPresent` 语义。
- 不做 clickTarget 协议（那是 L2；本 change 是 L2 的作用域前置）。

## Decisions

**D1（2026-07-12 评审订正，承重）：作用域 = 目标群自身「头部/动作区」正向包含，fail-closed 默认出域。** 一轮对抗评审坐实：原稿 D1「异群链接排除」是**排除式黑名单**（候选默认在域内、只排能证明链向异群的），与本 change 自称的「白名单式作用域」（旧 D3/Risks）**内部矛盾**；且真机 dump 里推荐位「加入小组」钮（`i=9` `div[role=button]`）是群名链接（`i=8` `a`）的**兄弟节点**、非后代 → `closest('a[href]')` 取不到异群链接 → 黑名单**漏排** → 默认在域内 → 目标群自身是 pending 时它成唯一在域内 join → 被点 → 加错群（红线仍在）。**订正为正向包含**：候选 `inTargetScope=true` **当且仅当**它是目标群自身「头部/动作区」块的后代——该块 = 含群名主标题（`<h1>` / `[role="heading"][aria-level="1"]`，承载群名）的**头部/hero 容器**（承载群名 + 群主 CTA）。该块解析不出 → **无候选在域内**（fail-closed），点击腿按 D3 诚实 `no_target_in_scope`、绝不页面级扫。正向包含的失败态是**安全侧**（块取窄 → 漏认目标自身 Join → 诚实不点 + 重试），与黑名单的失败态（漏排 → 误点异群）方向相反。头部块祖先的确切判据（从群名标题上溯几层 / 哪个祖先）需真机校准（Open Question / 确认探针），校准前不 land。

**D2（承重降级为 corroborating 排除，进一步收窄）：异群链接排除 + 推荐轮播容器排除。** 在 D1 正向包含之上再叠两条**排除**（只会让作用域更窄、绝不放宽）：**E1 异群链接**——候选被 `a[href]` 祖先（`closest('a[href]')`）或自身 `href` 解析到 `/groups/<id>` 且 `<id>` 异于当前页目标群 id（`location.pathname` 解析，numeric-id / vanity-slug 两式规范化）则排除；**E2 推荐轮播容器**——候选落在「发现更多小组 / 查看推荐小组」横向轮播容器（carousel role + 每项「移除推荐」按钮群识别）内则排除。**最终判据 = D1 正向包含 AND NOT E1 AND NOT E2。** E1/E2 是补强（catch 万一混进头部块的带链推荐项），**非承重**——承重是 D1 正向包含的 fail-closed 默认出域；E2 容器选择器真机校准前不启用，不因其未定档而放宽 D1。

**D3：点击腿 fail-closed，绝不回落页面级。** `GROUP_JOIN_CLICK_JS`：① 若目标群 id 从 URL 解析失败、或目标群头部块解析不出 → 诚实 `clicked:false, reason:'scope_unresolved'`，**绝不**页面级扫 join；② 作用域内（过 D1 正向包含 + E1/E2 排除）无 `join` 类候选 → `clicked:false, reason:'no_target_in_scope'`；③ 只在作用域内候选里取 `join`。删除「页面级文档序第一个 join」这条危险回落。备选（页面级扫 + 只加异群黑名单）被否——推荐栏动态重排、且 dump 证实推荐位 join 是兄弟裸 `div` 无异群链接，黑名单漏得掉；正解是 fail-closed 正向包含。

**D4：观测腿标注 `inTargetScope`，据此挑群主 CTA + 收窄成员信号，仍全量上报。** `GROUP_JOIN_OBSERVE_JS`：每候选加 `inTargetScope` 布尔（同 D1 正向包含 + E1/E2 判据）；`mainCta`/`joinButton` 的挑选**只在 `inTargetScope` 候选里**进行（推荐栏 join 绝不冒充群主 CTA）；**`membershipSignals` 亦只在目标群头部块内读取**——现状 `signals.slice(0, 8)` 是页面级扫描（`join-executor.ts:361`），推荐位某个「已加入」的建议群信号会污染它、致点后 `hasMemberSignal` 对**错群**假成功（红线1 尾巴，同「推荐位污染」根因）；收进作用域即绝不把推荐群的「已加入」当目标群成功。候选清单**仍如实全量上报**（含 `inTargetScope:false` 项），供云端裁判掌握全貌、不静默丢弃（守 L4 边缘不 fail-closed 丢原文）。

**D5：自身区控件不可分类 → 诚实。** 作用域内存在候选但 `ctaKind` 判不出 join/member/pending 时，观测腿据实上报（附原文 + `inTargetScope`），点击腿按 D3-② 诚实不点。绝不越域找 join 冒充（守「找不到目标报 no_target 而非 ok」）。

**D6：与 sibling / L2 的关系。** A 单独即让 pending 场景 fail-safe（目标群头部块内控件是「取消请求」非 join、且推荐位 join 不在头部块内 → 作用域内无 join → D3-② 诚实不点，即使 B 未落、词表仍漏认 pending）；此 fail-safe **建立在 D1 正向包含之上**（非旧黑名单——旧黑名单对兄弟裸 `div` 推荐位 join 漏排即失守）。B（词表补「取消请求」）修正**状态上报**准确性、不改本 change 安全性。L2 的 clickTarget 字面相等匹配**必须**在本 change 的 `inTargetScope` 候选内进行——L2 文档据此声明对 A 的前置依赖。

## Risks / Trade-offs

- [目标群头部块解析不出 / 取太窄 → 漏认目标自身 Join、可加入群点不了] → **安全侧退化**（fail-closed：无候选在域内 → 诚实 `no_target_in_scope` + 重试，绝不误点异群）；头部块祖先判据真机校准（确认探针 + Open Question），校准前不 land。这是 D1 正向包含相较旧黑名单主动接受的取舍：宁可偶尔漏认可加入群（安全侧、可重试），绝不漏排推荐位 join（红线侧）。
- [推荐位 join 是兄弟裸 `div`、无异群链接包裹] → **正是旧黑名单 D1 漏排、本次订正的核心 case**：D1 正向包含默认出域即挡住（推荐位不在目标群头部块内），E1/E2 再补强；不再依赖「候选带异群 `href`」这一 dump 未坐实的假设。
- [目标群自身 Join 钮恰被指向本群的链接包裹 → E1 误排] → E1 只排 **id 异于当前页** 的链接；本群 id 相同故保留。numeric-id ↔ vanity-slug 规范化须两式都比（Open Question 定档）。
- [目标群 id 解析失败 → fail-closed] → 安全侧退化（宁可诚实不点 + 重试）；URL 解析对 `/groups/<id>/` 稳定，失败罕见。
- [E2 容器选择器随 FB 改版漂] → E2 非承重、漂了退回 D1 正向包含 + E1；承重是 D1 fail-closed 正向包含。
- [观测腿全量上报 35~61 候选的体量] → 真机实测云端裁判可容忍全量噪声列表（探针 21/21）；`inTargetScope` 标注让云端不必自行去噪。

## Migration Plan

- 纯 edge，改 `join-executor.ts` 两段 in-page JS + 作用域 helper；无 schema / 无协议 / 无云端。
- 实装序：① 先一次真机确认探针（**硬前置**：捕获目标群头部块结构——群名 `<h1>` 祖先链、目标自身 Join 相对该块的位置、推荐位 join 相对该块的位置——坐实 D1 正向包含能框住目标自身 Join、且推荐位 join 落在块外；同时捕获推荐栏 join `href`/祖先群链接为 E1/E2 定档）→ ② 落 D1 正向包含 + D3 fail-closed（点击腿，承重）→ ③ D4 观测腿标注 + 成员信号收窄 → ④ E1/E2 排除补强（选择器真机校准后）。**头部块祖先判据 + E2 容器选择器均真机校准后方 land**（fail-closed 的「在域」判据不可凭猜）。
- 部署：edge master land → dev（electron:dev / 安装包重建后运营机生效）；无 ECS。
- 回滚：作用域是**收窄叠加**，回退即恢复页面级选取老行为；但因这是安全修复，回滚需谨慎（回滚即重开误点异群风险）。保留 D1 正向包含 + E1 为最小安全集。

## Open Questions

- **D1 头部块祖先判据（承重、决定能否安全 land）**：从群名主标题（`<h1>` / `[role="heading"][aria-level="1"]`）上溯到「含群名 + 群主 CTA 的头部/hero 块」的稳定判据（上溯几层 / 哪个祖先容器 / 是否有稳定 `[role="main"]` 或 data-attr 边界）——真机探针取证。取窄=安全侧（漏认可重试），取宽=靠 E1/E2 兜底；**校准前不 land**（fail-closed 判据不可凭猜）。
- **E1 群 id 规范化**：`/groups/<numeric-id>` 与 `/groups/<vanity-slug>` 两式如何统一比对（同一群可能两式并存）——实装前定档，偏保守（比不上即判异群、排除，安全侧）。真机探针取证。
- **E2 推荐轮播容器选择器**：「发现更多小组 / 查看推荐小组」carousel 的稳定结构标志（role / 每项「移除推荐」按钮群 / 容器 aria）——真机校准，取得前只靠 D1 正向包含 + E1。落 backlog。
- **观测腿 `mainCta` 挑选在作用域内多 join 候选时的优先级**（罕见：目标群头部多个 join 类控件）——先取作用域内文档序首个，真机若现异常再补结构判据。
