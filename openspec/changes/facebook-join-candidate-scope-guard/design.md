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

**D7（2026-07-12 二轮实装对抗评审订正，5 确认发现，含 1 红线）。** 一轮把 D1 从黑名单翻成正向包含后，二轮评审在 jsdom 里真跑注入 IIFE 复现出一个**残余红线**并补三个测试缺口，据此订正如下（实装已按此落）：

- **D7-1（红线闭合，承重；经两轮评审收敛到「扫全部元素属性」）：头部块的「异群引用」检测扫 `[role=main]` 子树内全部元素的 `href` 与所有属性值里的 `/groups/<id>`。** 评审坐实：D1 正向包含的 fail-closed **并非无条件成立**——它靠「检测到异群 `/groups/` 引用」来框定头部块上界。若推荐位用**非锚点导航**（group id 编码在 `data-*` 等属性而非 `href`；FB 常见，其自身 join 控件亦是 `div[role=button]` + 合成事件），旧实现（`__hasForeignGroupLink` 只 `querySelectorAll('a[href]')`）**找不到异群引用** → 头部块一路上溯吞进 `[role="main"]` → 推荐位 join 落「在域」→ 被点（异群 join 红线）/ 推荐位「已加入」污染成员判定（D4 红线尾巴）。**一轮订正**先把检测拓到 `a[href],[role="link"]` + `__groupIdFromEl` 扫属性，但**二轮再评审 jsdom 复现**证仍漏：`__groupIdFromEl` 虽扫全属性、`__hasForeignGroupRef` 却只对 `a[href],[role="link"]` 元素调用它 → group id 编码在 `div[role=button]`/裸 div 的 `data-*` 上仍漏检（`ok=true clicked=true` 复现）。**二轮订正**：`__hasForeignGroupRef` 改 `querySelectorAll('*')` 对**每个元素**调 `__groupIdFromEl`（href + 全属性）。**三轮再评审**又证仍漏：`querySelectorAll('*')` 只覆盖**后代**，漏了「异群 id 编码在**头部块根元素自身**属性上」（`div#B data-nav=/groups/999` 包住目标 header + 推荐位）——walk 把 #B 当干净块返回、块内推荐位仍被点。**最终订正（完备性）**：① `__hasForeignGroupRef` 加**节点自身**属性检查（`__foreignId(node)` OR 后代）；② `__resolveHeaderBlock` 返回前对未在 walk 中验过子树的起点 heading 补一次完整核；③ `__candForeignRef`（E1）改**走候选到 `__HEADER_BLOCK` 为止**（不设 12 层上限、不走到根——走到根会被块上方共享祖先的异群引用误伤目标自身控件）。**完备性论证**：返回的头部块**保证不含任何可检测的异群 `/groups/<id>` 引用**（块根自身 + 全部后代）。**四轮再评审**又证「块无异群引用」这个**负向**判据不足以推出「块属于目标群」：FB「你可能想加入」**双列卡片**把异群 `/groups/999` 链接放缩略图列、群名 h1+加入钮放**兄弟内容列**（内容列自身无异群链接）——该干净内容列会冒充目标头部、其加入钮被误点（jsdom 复现 `ok=true` 加错群 / 或其成员 CTA 伪造 already_member）。根因 = `__groupHeading` 盲取首个 h1、只负向校验、从不**正向**确认 heading 属目标群。**四轮根因修（正向甄别 heading，无需目标自引用）**：`__resolveHeaderBlock` 改**逐个候选 heading 甄别**，只接受「上溯 walk **抵达/停在 ceiling（`[role=main]`）**」的 heading——推荐卡片内的 heading 上溯会先停在「引用异群的**中层**卡片容器（低于 ceiling）」故被跳过；目标群顶层 heading 只在 ceiling 处才撞见（别处的）推荐位异群引用故被接受。无任一合格 → null（fail-closed / not_ready）。**故完备性推论成立**：接受的块既无异群引用、又正向确认为「停在 ceiling 的顶层 heading」= 目标群头部，非推荐卡片片段。**五轮再评审**又证「停在 ceiling」隐含「推荐卡片带自身异群引用」这个假设：若异群链接**游离在卡片外**（`[role=main]` 下的裸兄弟、卡片自身无引用），卡片 h1 也停在 ceiling → 目标区与推荐卡片区成**对称的干净 h1 区域**、无法确信哪个是目标（评审自评 LOW realism：非今日 FB，真卡片带自身内链）。**五轮加固（歧义即 fail-closed，原则性安全网）**：`__resolveHeaderBlock` 收集**所有**合格 heading，**恰一个**才返回其块、`0 或 >1` → null（fail-closed / not_ready）。正常页恰一个（目标头部；推荐卡片带自身引用故其 h1 停在中层被跳过）；出现 ≥2 对称区域即判歧义、宁可不点。这把 v5 红线从「点错群」降为「fail-closed 可重试」。**至此停止客户端启发式加固**——剩余角落不靠真机 DOM 无法消解、均 0.1-gated（见 Open Questions）。**残留**（见 Risks / Open Question）：foreign id **在轻 DOM 里任何属性都不以 `/groups/<id>` 子串出现**（只活 JS 闭包 / 裸数字 id 无 `/groups/` 前缀 / shadow root / iframe）的纯不透明推荐位——无信号可辨，靠 D7-2 堵污染方向 + 真机校准（0.1）坐实 FB 是否存在此形态。

- **D7-2（成员污染方向补强，矛盾守卫）：`already_member` 仅当作用域内无 join 按钮时成立。** 一个显示「加入」CTA 的群绝不可能是你已加入的群，故「有成员信号 + 同时有域内 join 按钮」必是异群信号污染 → 不判 `already_member`、照常去点目标自身 join。这条与 bounding 正交、语言无关，即便极端不透明推荐位漏进作用域，也堵死「推荐位『已加入』伪造目标 already_member」这一红线方向。

- **D7-3（Finding 2，可用性正确性）：作用域守卫 fail-closed 的回执映射为可重试 `not_ready`，不折叠成 `no_button`。** 评审追踪云端链坐实：`no_button` 被云端判**永久 `failed`**（不进 `claimNext` 重试池），会把「重导航/晚渲染时暂时框不住作用域」的**可加入群永久丢弃**——与原注释「云端按 gated、非硬失败」矛盾。**订正**：观测腿 `scopeResolved===false` 与点击腿 `scope_unresolved`/`no_target_in_scope` 均返回 `not_ready`（云端 `isNetworkTransient` 短退避重试、不计尝试上限）。安全侧不变（不点、可重试），且不永久丢弃可加入群。

- **D7-4（Finding 3/4/5，测试补齐）：补三条 jsdom 回归护栏**——① 推荐位异群 join 在文档序**先于**目标 join + click（删掉点击腿 `&& __inTargetScope` 即失败，护住承重 P0 代码）；② in-page URL 无 `/groups/<id>`（`__TARGET_GID=null`）→ fail-closed；③ 点后目标未成成员 + 推荐位异群「已加入」出域 → 诚实 `join_failed` 不伪造。另加「非锚点推荐位（role=link + `data-*` 编码）被识别出域」一条证 D7-1。**注**：`scopeResolved` 在 `publicObservation` 里区分「未评估（undefined，如预烘焙观测）」与「评估为 false」——绝不默认 false，否则 fail-closed 闸误触发所有未标注观测。

## Risks / Trade-offs

- [目标群头部块解析不出 / 取太窄 → 漏认目标自身 Join、可加入群点不了] → **安全侧退化**（fail-closed：无候选在域内 → 诚实 `no_target_in_scope` + 重试，绝不误点异群）；头部块祖先判据真机校准（确认探针 + Open Question），校准前不 land。这是 D1 正向包含相较旧黑名单主动接受的取舍：宁可偶尔漏认可加入群（安全侧、可重试），绝不漏排推荐位 join（红线侧）。
- [推荐位 join 是兄弟裸 `div`、无异群链接包裹] → **正是旧黑名单 D1 漏排、一轮订正的核心 case**：D1 正向包含默认出域即挡住（推荐位不在目标群头部块内，只要头部块被正确框住），E1 再补强。
- [**D1 正向包含的 fail-closed 并非无条件**：头部块上界靠「检测到异群 `/groups/` 引用」框定（二轮评审红线）] → 若推荐位用非锚点导航（id 编码在属性而非 `href`），旧「只认 `a[href]`」检测不到 → 头部块吞进推荐位 → **fail-open**（异群 join 被点 / 成员污染）。**D7-1 经两轮评审收敛为「扫 `[role=main]` 子树全部元素的 href + 所有属性值里的 `/groups/<id>`」**（`__hasForeignGroupRef` 用 `querySelectorAll('*')`、`__candForeignRef` 上溯 12 层），覆盖锚点与属性编码（含 `div[role=button]`/裸 div 的 `data-*`）两类推荐位；**残留**：foreign id 在轻 DOM 任何属性都不以 `/groups/<id>` 子串出现（JS 闭包 / 裸数字 id / shadow root）的纯不透明推荐位——无信号可辨。此残留靠 **D7-2 成员矛盾守卫**堵死污染方向、靠真机校准（0.1）坐实 FB 是否存在此形态；**land 前 0.1 必须真机验证一个非锚点推荐位、而非只重采锚点推荐位**（否则测试给假信心）。
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

- **D1 头部块祖先判据 + 非锚点推荐位形态（承重、决定能否安全 land；二轮评审强化）**：从群名主标题（`<h1>` / `[role="heading"][aria-level="1"]`）上溯到「含群名 + 群主 CTA 的头部/hero 块」的稳定判据（上溯几层 / 哪个祖先容器 / 是否有稳定 `[role="main"]` 或 data-attr 边界）——真机探针取证。取窄=安全侧（漏认可重试），取宽=靠 E1 兜底。**因头部块上界靠「检测异群 `/groups/` 引用」框定，0.1 探针 MUST 同时坐实真机「发现更多小组」推荐位卡片的导航形态**：是 `a[href="/groups/id"]`、`[role="link"]`+属性编码 id、还是纯 JS 闭包（无任何属性带 id）。前两类 D7-1 已覆盖；若为第三类纯不透明形态，需补真机可辨的结构信号（否则该形态下头部块会 fail-open，仅靠 D7-2 堵成员污染方向、join-click 方向仍需结构信号）。**校准前不 land**（fail-closed 判据不可凭猜；且 land 前须真机验证一个非锚点推荐位、不能只重采锚点形态）。
- **E1 群 id 规范化**：`/groups/<numeric-id>` 与 `/groups/<vanity-slug>` 两式如何统一比对（同一群可能两式并存）——实装前定档，偏保守（比不上即判异群、排除，安全侧）。真机探针取证。
- **E2 推荐轮播容器选择器**：「发现更多小组 / 查看推荐小组」carousel 的稳定结构标志（role / 每项「移除推荐」按钮群 / 容器 aria）——真机校准，取得前只靠 D1 正向包含 + E1。落 backlog。
- **观测腿 `mainCta` 挑选在作用域内多 join 候选时的优先级**（罕见：目标群头部多个 join 类控件）——先取作用域内文档序首个，真机若现异常再补结构判据。
- **（五轮评审总结，承重）纯客户端启发式识别目标头部有不可消解的双向角落——0.1 真机校准是唯一权威解。** 五轮对抗评审逐层收敛（锚点→全属性→块自身→heading 甄别→歧义守卫），每轮堵住一个逃逸、下一轮现更刁钻者、现实概率逐轮降低（v5 已 LOW realism）。当前代码把所有 high/medium-realism 攻击堵成安全态，但两类角落只能靠真机 DOM 定夺：**① fail-open 残留**——异群 id 在轻 DOM 任何属性都不以 `/groups/<id>` 子串出现（JS 闭包/shadow/iframe/裸数字），或异群链接游离在卡片外形成对称歧义（后者已被歧义守卫降为 fail-closed）；**② fail-closed 可用性损失**（安全但漏认真目标）——(a) 目标群头部自身引用了兄弟/关联群 `/groups/<异 id>` → 目标 heading 被甄别掉 → 永久 `not_ready`（云端无限重试不成功）；(b) 嵌套 `[role=main]` / 推荐位铺平为 `[role=main]` 裸兄弟 → 块退化成无 join 的裸 heading → `no_button`（云端永久失败）。**0.1 真机 MUST 取证 FB 真实结构**（推荐卡片是否带自身内链、群名 heading 层级、目标头部是否引用别群、是否嵌套 main），据实把「停在 ceiling / 歧义 / heading 层级」判据校准到真值——而非继续凭猜加启发式。校准前不 land。

## 真机校准结论（2026-07-12，task 0.1 已做完）

运营机 AdsPower 真机实测（账号已登录、中文 chrome，只读探针 `scripts/fb-group-scope-probe.ts` 注入发货 `SCOPE_HELPERS_JS` + 真实 executor 驱动 `scripts/fb-join-live-drive.ts`；三群加群/退群全流程、账号复原）把上面的 Open Questions 逐条落地：

- **推荐卡片导航形态**：真实「相关小组/发现更多小组」卡片的 join 是裸 `div[role=button]`，其异群 `/groups/<id>` 锚点在**卡片内**（`a[href]`，非纯 JS 闭包），距 join 钮仅 **2–4 跳后代**——承重的 `__hasForeignGroupRef` 后代扫描恒能检出。**「纯不透明第三类」fail-open 形态未出现**（① 的 join-click 方向残留在真机不成立）。E1 走不到（异群锚点是候选的兄弟子树、非祖先），故承重靠 D1 后代扫描、E1 仅 corroborating（与实装一致）。
- **群名 heading 层级 + 唯一性**：目标群名恒为 `[role=main]` 内**单一 `<h1>`**；真实推荐卡片**不用 `<h1>`**（用链接/纯文本）→ 页面群名 h1 唯一。**v4/v5 为「双列卡片竞争 h1」加的甄别在真机不被触发**（合成防御保留作纵深，无害）。
- **② fail-closed 可用性角落 (a) 真机命中并已修**：加群成功后 FB 弹「相关小组」takeover，其异群栏与目标 h1 **共享一个 `[role=main]` 之下的中层 `div`**（栏是目标头部的兄弟子树）。v4「没停 ceiling 就拒 heading」把唯一的目标 h1 也拒掉 → `scopeResolved=false` → 成员信号（收窄到未解析块）空 → **成功加群误报 `join_failed`、已加入群误读 `not_ready`**（真机 2/2 复现；fail-safe 但打断 happy path）。**修法**：`__resolveHeaderBlock` 改为——单一群名 h1（真实 FB 均如此）用其**最后一个干净祖先**作块（含目标自身 CTA、结构性排除兄弟栏）；多 heading 保留 v4/v5 甄别（唯一「停在 ceiling」者，≥2 对称→歧义 fail-closed）。**真机验证**：修后 fresh 加群 `ok=true`、post `scopeResolved=true`、`mainCtaText=已加入`、`membershipSignals=[已加入]`、`outOfScopeJoinCount=10`（10 个别群 join 仍全出域，安全不变）。
- **② 角落 (b) 嵌套 main**：`/groups/discover` 有 2 个（嵌套），但**群落地页为单 main**，不触发块退化。
- **修法 residual（真机未见、诚实记录）**：目标页**自身无 h1** 而某推荐卡片**有 h1** → 单 heading 分支会误接受该卡片块。真实 FB 目标群页恒有 h1、卡片从不用 h1，故不触发；交对抗评审（0b.3）复核。

结论：D1 正向包含（块无异群引用 → 兄弟栏结构性出域）在真机是承重且成立的安全判据；此前 v4 的「停 ceiling 强判据」在真机过严、打断成员/takeout 态，已用「单 h1 取最后干净祖先」修回、安全不减（栏 join 恒出域，真机 `outOfScopeJoinCount=10` 实证）。
