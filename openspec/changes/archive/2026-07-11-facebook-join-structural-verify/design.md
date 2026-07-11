## Context

Facebook 加群成败当前靠 edge `src/facebook/join-executor.ts` 的多语词表判定：`classifyCtaLabel` 分类 join/member/pending，`hasMemberSignal()` 据 `MEMBER_CTA_LABELS` + `MEMBER_MEMBERSHIP_PHRASES` 判成员、`PENDING_CTA_LABELS` 判待审；observe 期 `hasMemberSignal()` 命中即返回 `already_member`（`clicked:false`）。云端裁判镜像同表（drift-guard 护）。词表覆盖不全 + 不对称 → 真机事故：加成功→按钮翻本地语「已加入」未被词表命中→报 `join_failed`→重复加群（[[fb-join-comment-resilience-change]]）。

加群回执的观测走**松类型通道**：`ActionCompletedPayload.observation?: unknown` / `postObservation?: unknown`（`src/comm/protocol.ts` ~1046-1048），非两份 `protocol.ts` 的 parity 类型字段。故给观测补结构信号**不触协议 parity、不涉 `AC-PROTO`、无需与协议类 change 串行**。这是本 change 能独立先上的关键。

分层方案定位：接在 C1（[[facebook-locale-pin-en-us]] 界面钉英文、新号治本）之后，L3 治「成败校验语言相关」这条存量号/登出态也犯的缝。点击动作定位解耦（clickToken）是另一条触协议热点的独立 change（[[facebook-join-actuation-decouple]]），与本 change 解耦。C3（同意浮层结构化）正交。

## Goals / Non-Goals

**Goals:**
- 加群成败校验补语言无关结构真值为主判，消灭「本地语已加入→误判失败→重复加群」false-negative。
- **不引入新的 false-positive**：绝不让「非成员组渲染的 composer」被当已加入（评审红线）。
- 词表保留为只正向补充（绝不否决、绝不无信号假成功）。
- 零协议 parity 改动，独立可上。

**Non-Goals:**
- 不删多语词表（留作正向补充 + 云端裁判稳定网）。
- 不改点击动作定位 / 不加 clickToken（那是 [[facebook-join-actuation-decouple]] 的事）。
- 不给按钮上视觉、不引 FB 私有前端 JSON 当真值。
- 不动租约瞬态/退避分级/待审问卷不销毁等既有 resilience 机制。

## Decisions

**D1：结构主判 = 点后单帧「有 composer 且无可见 Join CTA」+ 同调用跃迁；承重闸是点后单帧事实（复验收紧）。** 这是评审揪出的关键：公开组可能对非成员也渲染发帖框/「写点什么…」诱导框，裸 composer 当已加入真值会造成新的 false-positive（假成功、实际没进群、后续覆盖评论失败）。故：
- **承重闸（点后单帧事实）**：判 joined 要求点后观测**有可聚焦 composer 且群主体内无可见 Join CTA**。「点后无可见 Join CTA」是单帧事实（非跨导航「消失」），对两次调用架构稳——非成员公开组点后 Join CTA 仍在、故不满足。复验证明这是承重项。
- **跃迁（佐证）**：composer 跃迁用**同一次 `click=true` 导航内的 pre/post 观测对**（点前刚采的 pre + 点后 post，`join-executor.ts` 一次导航内 `observation`+`postObservation`），**不用**另一次独立 observe-only 调用的观测（跨两次页面加载、渲染时序独立、不可靠）。晚渲染的非成员 composer 即便造成假跃迁，也被「点后无可见 Join CTA」承重闸挡下。
- **顺序**：pending/问卷检测**先于** joined 判——Join→Pending 翻转即便渲了 composer 也判 pending、不判 joined。
- observe 期裸 composer 不得翻 `already_member`；observe 期 `already_member` 仍要正向成员信号（词表命中，或 composer + 无可见 Join CTA）。
备选（裸 composer presence 当真值）被否——评审指出的新 false-positive 源。备选（跨导航「Join CTA 消失」）被否——两次调用架构下不可靠，改用点后单帧事实。备选（继续堆词表到 N 语）被否——永远追不全。

**D1b：结构字段必须透传到云端裁判（joined authority，复验揪出）。** 云端 `evaluatePostClick` 现只收 post 观测、其观测类型无 composer/CTA 字段，故结构主判若只在边缘做、云端仍按未知语种成员标签回 `failed`→AND 门下仍重复加群（change 目标落空）；而放松 AND 门去信边缘又丢了云端独立复核。故本 change MUST 把结构字段（composer/Join-CTA/Leave present）+ 同调用 pre 观测一并喂给云端裁判，让 joined 权威用结构主判。这是 L3 落地的接线要点，不是可选。

**D2：词表只正向补充，红线兜底不假成功。** 词表命中 = 正向加固；缺失绝不否决结构跃迁确认。结构跃迁（含可供性翻转）与词表**都无**正向命中时 MUST NOT 报成功——honest not-joined / retry。既有 `hasMemberSignal()` 的「必须正向命中才算成员」纪律延续到结构层。

**D3：零协议 parity——观测走松类型通道。** 结构信号（群主体内可聚焦 composer 存在、Join CTA 存在、Leave 可供性存在）写入 `observation`/`postObservation`（`unknown` 通道），云端解析。不动两份 `protocol.ts` parity 类型、不加 `MessageType`、不动 `GroupJoinPayload`。故不涉 `AC-PROTO`、不需与 `facebook-scheduled-comment` 等协议类 change 串行。备选（把结构信号提升为 parity 类型字段）被否——YAGNI，松通道已够，徒增串行成本。

**D4：慢渲染复用既有 readiness 层。** composer 跃迁在慢渲染下可能滞后：未就绪走既有 post-click readiness retry tier（`facebook-group-join-resilience` 已有 slow-render→retry），不当终局失败、不 fail-closed。M3 子树判别（区分群内发帖框 vs 无关输入框）落 backlog 真机取证选择器。

## Risks / Trade-offs

- [非成员组的 composer 被当已加入 → 假成功] → **跃迁 + 可供性翻转**双闸：点前已存在的 composer 不算跃迁、Join CTA 还在就不算翻转；observe 期裸 composer 不翻 `already_member`。spec 已编码对应场景。
- [composer 子树误判：群内无关输入框（搜索框/评论他人）当发帖框] → M3 子树判别限定「群主体内可聚焦发帖/评论 composer」，真机取证选择器；判不准时不构成跃迁信号、回落词表 + retry，不假成功。
- [结构与词表都无信号] → honest not-joined / retry（红线兜底），绝不 assume-joined。
- [慢渲染 composer 滞后] → 既有 readiness retry tier 兜底，不当终局。
- [与并发 sibling 撞加群文件] → 本 change 无协议改动，冲突面仅 `join-executor.ts` + 云端裁判；与 `facebook-scheduled-comment`（评论侧）文件面不同，rebase 后 land 即可，无强串行依赖。

## Migration Plan

- 无协议先行：直接改 edge 观测采集 + 后置校验 + 云端裁判解析。
- 部署：edge dev land + cloud dev（安全序列，先 `test:acceptance` 再全量 `test` 再 `typecheck`；`AC-PROTO` 不涉及但仍全绿把关）。
- 回滚：结构主判可 env 旗标包裹（如需灰度），秒回词表主判；词表路径保留就是天然回滚位。

## Open Questions

- 「群主体内可聚焦发帖/评论 composer」在各版式群页的最稳选择器 + M3 子树判别（区分发帖框 vs 无关输入框）——真机取证，与 [[fb-comment-editor-label-gap]] 编辑框识别共用经验。
- 「成员可供性翻转」的最稳结构判据（Join CTA 消失 vs Leave 可供性出现，哪个更早更稳）——真机校准，先两者取其一即可。
- 是否需 env 旗标灰度，取决于真机重复加群复现频率——落 backlog 真机项定。
