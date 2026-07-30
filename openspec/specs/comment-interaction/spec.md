# comment-interaction Specification

## Purpose
TBD - created by archiving change comment-interaction. Update Purpose after archive.
## Requirements
### Requirement: 评论支线接在互动完成与进主页评估之间

系统 SHALL 把评论支线挂在 `interaction.completed`（即**仅在该笔记真发生过 like / collect 时**才进入评论评估），
并把"是否进个人主页"的判断（`AuthorEvaluator`）的触发**从 `interaction.completed` 改挂到评论支线的终结事件**（`comment.done` / `comment.skipped`）。
评论支线 MUST 在笔记详情页仍打开时整条跑完；评论成功 / 跳过 / 失败 MUST 都汇到"是否进主页评估"这唯一出口、且每篇 MUST 只触发一次该评估。
评论支线 MUST NOT 在评论结束后直接进入个人主页（MUST 经"是否进主页评估"，该评估可决定不进 / 已关注跳过）。
系统 MUST 使用独立 `comment.*` 事件族，MUST NOT 复用或扩宽 `InteractionCompletedPayload.actions`（其同时被命令翻译与 `AuthorEvaluator` 消费）。

#### Scenario: 互动后进入评论评估，再评估是否进主页
- **WHEN** 某笔记 `InteractionAppraiser` 选择 like / collect 并 emit `interaction.completed`
- **THEN** 评论支线（`CommentAppraiser`）启动；其终结（`comment.done` 或 `comment.skipped`）后才触发 `AuthorEvaluator` 的"是否进主页"判断；like/collect 命令仍在 `interaction.completed` 同步下发、评论命令在评论支线内下发，二者在评论完成（真回执）之前 MUST 先于任何 `profile_open` / 返回导航

#### Scenario: pass 的笔记不评论也不进主页
- **WHEN** `InteractionAppraiser` 判 pass 并 emit `interaction.skipped`
- **THEN** 评论支线 MUST NOT 触发（评论只在已互动的笔记上发生），照旧由 `BackToFeed` 回流刷下一篇

#### Scenario: 评论失败仍走进主页评估、不死锁
- **WHEN** 评论命令回报 `ok:false`（找不到框 / 未生效 / 验证码）
- **THEN** 评论支线 MUST emit 终结事件触发"是否进主页评估"，MUST NOT 卡死在详情页、MUST NOT 重复触发该评估

#### Scenario: 红线反例——评论完直接进主页或挂错事件（禁止）
- **WHEN** 有实现让评论完成后直接 emit `profile.entered` / 直接下发 `profile_open`，或仍让 `AuthorEvaluator` 直接消费 `interaction.completed` 而绕过评论支线，或扩宽 `InteractionCompletedPayload.actions` 容纳 `comment`
- **THEN** MUST 视为违规、不予合入；进主页 MUST 经"是否进主页评估"，且该评估 MUST 由评论支线终结事件触发

### Requirement: 评估→撰写→去AI味→审批四段单职责角色

系统 SHALL 以四个独立角色实现评论支线，**评估与撰写 MUST NOT 合并**：`CommentAppraiser`（只判定要不要评、产判定不产文本）→
`CommentComposer`（产评论文本）→ `CommentDeAiFlavor`（去 AI 味 + 合规声明判定：**检测步**确定性无 LLM；**改写步**在命中 AI 味信号或与参考语料撞车时按**该账号人设口吻**做至多一次 LLM 改写，改写失败 / 超时 MUST 回退原文、不抛异常）→
`CommentApprovalGate`（循环内飞书人审）。任一段失败 / 不通过 MUST emit `comment.skipped` 并带如实原因，MUST NOT 伪造文本或伪造通过。
`CommentComposer` 作为浏览闭环首个自由文本角色，MUST 自己保证：空 / 超长文本如实跳过、做跨笔记近似去重、撰写时避开裸 `@`（编辑器带 `data-tribute` 提及）；并 SHALL 提供**语义弃权出口**——对着笔记确实写不出有真实内容的话时，MUST 返回弃权（`nothing_genuine`）走 `comment.skipped` 分支，MUST NOT 硬凑客套话（客套敷衍正是评论体裁的 AI 味主形态）。

评论撰写前的外部语料召回属于可选 prompt 增强，MUST 设独立短超时；异常、超时或空结果 MUST 按“无参考语料”继续撰写，不得让该 Promise 无界占住评论支线，也不得把可选增强失败伪装成评论成功。

#### Scenario: 评估为是才进入撰写

- **WHEN** `CommentAppraiser` 判定该笔记值得评论且配额/门槛通过
- **THEN** emit `comment.appraised` 触发 `CommentComposer` 产文本 → `CommentDeAiFlavor` 去 AI 味 / 合规 → `CommentApprovalGate`；评估为否则 emit `comment.skipped`，不进入撰写（不付 LLM 撰写成本）

#### Scenario: 可选语料召回悬空时按空参考继续

- **WHEN** `CommentComposer` 的参考语料召回在短超时内未 resolve / reject
- **THEN** 系统 MUST 记录稳定超时原因并按空参考继续调用评论撰写模型；MUST NOT 永久停在 `comment.appraised`，MUST NOT 因可选语料缺失伪造模板评论

#### Scenario: 去AI味检测步确定性、改写步失败回退

- **WHEN** `CommentComposer` 产出草稿文本
- **THEN** `CommentDeAiFlavor` 的 AI 味检测 MUST 为确定性规则（无 LLM、可独立单测）；命中信号触发的人设口吻改写走 LLM，改写失败 / 超时 MUST 回退检测前原文并继续流程，MUST NOT 抛异常中断评论支线

#### Scenario: 撰写诚实弃权不硬凑

- **WHEN** `CommentComposer` 面对已判值得评的笔记仍写不出有真实内容的评论（LLM 返回弃权）
- **THEN** MUST emit `comment.skipped{reason:'nothing_genuine'}`，不进入去 AI 味与审批；评论支线照常收敛（下游进主页评估不受影响）

#### Scenario: 红线反例——撰写失败伪造文本（禁止）

- **WHEN** `CommentComposer` LLM 失败 / 产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST emit `comment.skipped{reason}`，绝不发出无法落地的伪造评论

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让普通评论的 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。**通用默认地板** SHALL 为：`likeCount > 300` **且**（`collectCount > 100` **或** `likeCount > 10000` 超高热豁免），边界均为严格大于。**无「收藏」概念的平台**（如 Facebook）SHALL **只放宽收藏合取项**、保留主门槛 `likeCount > 300`。普通评论任一不满足门槛 MUST 直接 `comment.skipped`，硬门槛之上继续叠加 LLM 精品判定与飞书人审；实际生效每日上限仍为运营配置与风控安全配额取小。

详情全文确认命中的结构化 `mandatory_interactions` 规则若含 `comment`，则是上述**普通评论策略的唯一显式例外**：`CommentAppraiser` MUST 跳过会话 comments 软预算、普通每日策略闸、热度门槛、评论冷却与“要不要评”LLM，但在撰写前 MUST 经过可解释的 `RiskController.explain('comment')` 硬风控预检。预检拒绝时不得撰写、不得发免审通知；预检放行才 emit `comment.appraised` 并携规则上下文。预检不是配额预占，评论下发前仍 MUST 再经过同一硬风控，真实成功才计数。

**该例外中「跳过评论冷却」一项的理由 MUST 与 `interaction-cooldown` 同源**：冷却是**兜底**（防意外爆发），其抑制语义是**丢弃而非排队**；mandatory 是运营对指定内容类别的显式授权、且为每帖一次性机会 ⇒ 兜底 MUST NOT destroy 一次已授权的机会。该理由 MUST NOT 表述为「授权动作不该被数量约束挡」——冷却不表达数量策略，数量由 `RiskController` 主闸单独负责，而本例外**不跳过主闸**（预检 ＋ 下发前二次判均保留）。

#### Scenario: 达到每日上限即停止普通评论
- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)，且本篇未命中结构化强制规则
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再发起普通评论

#### Scenario: 运营配置不可越过风控安全线
- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达硬门槛的普通帖子不评
- **WHEN** 普通帖子未达该品类 / 账号硬门槛且无 mandatory context
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过

#### Scenario: 无收藏平台按放宽收藏合取项入普通候选
- **WHEN** 一篇普通 Facebook 帖 `likeCount = 500`、`collectCount = 0`
- **THEN** 收藏合取项恒真、主门槛满足，该帖进入普通 LLM 精品判定

#### Scenario: 低热度强制帖子绕过普通门槛与判定
- **WHEN** 一篇 Facebook 帖 `likeCount = 0` 但全文确认命中 actions 含 comment 的结构化规则
- **THEN** `CommentAppraiser` 不检查软预算/普通每日策略闸/冷却/热度、不调用评论判定 LLM，但必须先过硬风控预检，放行后才进入撰写

#### Scenario: 例外的理由不得与兜底定位冲突
- **WHEN** 有人以「冷却是数量约束、已授权动作不该被数量约束挡」为由解释本例外
- **THEN** MUST 拒绝该表述——冷却不表达数量策略；本例外的唯一正当理由是「兜底丢弃不排队，MUST NOT destroy 已授权的一次性机会」

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论默认因必须在详情页打开时发出而**循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经人审授权。等待期间系统 MUST 进入可识别的审批暂停态，并设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获有效授权 MUST NOT 下发评论命令。

免逐条审批路径有两类：① 本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`；② 当前账号显式配置全局评论 `auto_approve_all`，后者 MUST 覆盖普通浏览、排期、联系、mandatory、飞书 `/comment` 和结构化委托来源的局部模式。任一免审路径下，`CommentApprovalGate` MUST 直接 emit `comment.approved`，并把账号、目标和清洗后的终稿旁路发送到免审通知口。提交链 MUST NOT 等待通知；通知口未接线或发送失败只记日志，MUST NOT emit `comment.skipped`、MUST NOT 阻止下发、MUST NOT 回退为按钮审批。账号为 `source_rules` 时，未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** `source_rules` 账号的普通评论人审在超时窗口内写入授权信号
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 强制规则免审直接授权并旁路通知
- **WHEN** `source_rules` 账号的 mandatory comment 规则显式 `auto_approve`
- **THEN** gate 不等待逐条点击，直接 emit approved；旁路通知内容必须是即将提交的终稿

#### Scenario: 账号全局免审覆盖普通评论
- **WHEN** 普通浏览评论所属账号显式配置 `auto_approve_all`
- **THEN** gate 不发送按钮审批卡、不等待点击，直接 emit approved 并继续既有目标复核与提交链

#### Scenario: 免审通知失败不影响全局免审
- **WHEN** 任一免审路径的通知口未接线或发送失败
- **THEN** MUST 只记录日志并继续既有提交链，MUST NOT 回退按钮审批或产生 `auto_approve_notice_failed`

#### Scenario: 来源规则账号的 XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 账号为 `source_rules` 且评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审，MUST NOT 被隐式全局自动直发

### Requirement: 执行端发评论动作——拟人输入 + 发布后校验、绝不假成功

边缘 SHALL 实装 `executeComment`：① 点折叠态评论入口（`.engage-bar .input-box .content-edit .not-active.inner-when-not-active`，"说点什么"）激活编辑器；
② 点编辑器本体（`p#content-textarea.content-input[contenteditable]`）落 caret；③ `dispatchKeystrokes` 拟人逐字输入；
④ 提交前 `captchaPresentFresh` 自检；⑤ 点提交键（`.engage-bar.active … button.btn.submit`，"发送"；空/无效内容时带 `.gray` 禁用、有效内容后 `.gray` 消失）；
⑥ **后置校验：编辑器清空 且 自己的评论作为顶部新 `div#comment-<id>` 行出现**。MUST 经既有 `reportActionCompleted{action,ok,reason}` 如实回报；
找不到框 / 按钮回 `no_target`、提交后未生效回 `state_unchanged`、验证码回 `blocked_by_captcha`。MUST NOT 静默假成功。MUST 复用 `LocatingEngine` 三道闸、不破坏其接口。

#### Scenario: 发布成功的判定
- **WHEN** 输入文本、点"发送"后，编辑器清空且评论列表顶部出现包含本次文本的新 `div#comment-<id>` 行
- **THEN** `executeComment` MUST 回 `reportActionCompleted{action:'comment', ok:true}`；评论数文本不可靠，MUST NOT 仅凭计数判定

#### Scenario: 找不到框 / 提交无效如实回报
- **WHEN** 评论框 / 提交键定位失败，或点击"发送"后编辑器未清空且无自己的评论行出现
- **THEN** MUST 回 `ok:false` 且 `reason` 为 `no_target` / `state_unchanged`；MUST NOT 回 `ok:true`

#### Scenario: 提交前命中验证码
- **WHEN** 提交前 `captchaPresentFresh` 检出验证 / 安全浮层
- **THEN** MUST 回 `ok:false, reason:'blocked_by_captcha'`，MUST NOT 提交、MUST NOT 假成功

#### Scenario: 红线反例——点了发送就当成功（禁止）
- **WHEN** 有实现点击"发送"后不做后置校验即回 `ok:true`
- **THEN** MUST 视为违规、不予合入；`ok:true` MUST 以"编辑器清空 且 自己的评论行出现"为前提

### Requirement: 协议 v2 新增 interaction.comment 并三处同步

系统 SHALL 新增 cloud→edge 消息 `interaction.comment`（payload `CommentPayload{noteId, text, thinkMs?}`）。
两份 `src/comm/protocol.ts`（edge / cloud）MUST 逐字一致新增该 `MessageType` 与 payload；`command-bridge.ts` MUST 加 `comment → interaction.comment` 映射；
`EdgeCommand.action` 并集 MUST 加 `comment`；`docs/protocol.md` 头部计数与 §2 表 MUST 同步；两份 `protocol-contract.test.ts` 的 `ALL_MESSAGE_TYPES` 与计数断言 MUST 由 54 改为 55。

#### Scenario: 两份 protocol.ts 不漂移
- **WHEN** 新增 `interaction.comment` 后运行 `npm run typecheck` 与 `npm run test:acceptance`
- **THEN** `Record<MessageType,true>` 穷举与 `AC-PROTO-*`（计数 55）MUST 全过；任一处（两份 protocol.ts / command-bridge / docs / 两份 contract test）漏改 MUST 使构建失败

#### Scenario: 红线反例——单边新增消息（禁止）
- **WHEN** 仅在 cloud 侧 protocol.ts 新增 `interaction.comment` 而未同步 edge 侧 / contract test 计数
- **THEN** MUST 视为违规、不予合入；协议三处 + 两份 contract test MUST 原子同步

### Requirement: 评论纳入风控闸与按账号配额、计数挂真实回执、终态单写

系统 SHALL 把 `comment` 纳入下发前风控闸与会话预算：`role-dispatcher` 的 `canInteract`、`freshBudget()`、`consumeBudget` 并集 MUST 加 `comment`，
下发前 MUST 过 `riskController.canDo('comment')`、被拒 MUST 诚实跳过（不下发、不扣预算、不伪造）。`comment` 计数 / 持久化 MUST 只在执行端真回执 `ok:true` 时经 `interaction.occurred → RiskController.record('comment')` 发生（`handler.ts` 过滤与事件类型加 `comment`）。
账号风控终态 MUST 仅由云端 `RiskController` 单写；边缘与各评论角色 MUST 只读 `canDo`、MUST NOT 写终态。

#### Scenario: 被风控拒则诚实跳过
- **WHEN** 下发评论前 `riskController.canDo('comment')` 返回 false（配额尽 / `restricted` / `warned` / `frozen`）
- **THEN** MUST 不下发评论命令、不扣预算、emit `comment.skipped{reason}`，MUST NOT 伪造已评

#### Scenario: 仅真回执成功才计数
- **WHEN** 评论命令回执 `ok:true`
- **THEN** MUST emit `interaction.occurred` 使 `RiskController.record('comment')` 按账号计数并持久化；回执 `ok:false` MUST NOT 计数、MUST NOT 扣预算

#### Scenario: 红线反例——下发即记账或边缘改写终态（禁止）
- **WHEN** 有实现在下发评论时就 `record('comment')` / 扣预算，或在边缘改写账号风控终态
- **THEN** MUST 视为违规、不予合入；计数 MUST 挂真回执、终态 MUST 仅云端 `RiskController` 单写

### Requirement: Facebook automatic comment path must not weaken xhs human approval

Facebook scheduled comments SHALL use a separate platform-specific automatic path gated by deterministic validators and kill switches. Existing xhs comment interaction and manual approval requirements MUST remain intact; changes to shared composer helpers MUST preserve xhs `CommentApprovalGate` behavior and MUST NOT make xhs comments auto-post without approval.

#### Scenario: xhs approval still required
- **WHEN** xhs comment interaction produces a draft after this change
- **THEN** it still waits for the existing human approval gate before edge submit, unless an existing explicit manual path already defines otherwise

#### Scenario: Facebook validator path does not enter xhs manual skip set
- **WHEN** Facebook scheduled comment code runs
- **THEN** it uses its own automatic account tracking and does not add Facebook accounts to xhs manual-comment skip-quota collections

### Requirement: Shared compose extraction preserves approval semantics

If composition and cleanup logic is refactored into shared helpers, the helper SHALL be wrapped by separate xhs `withApproval` and Facebook `withValidators` callers. The helper itself MUST NOT decide that a comment can be posted.

#### Scenario: Helper returns draft only
- **WHEN** shared composition logic succeeds
- **THEN** it returns candidate text to the caller; xhs approval or Facebook validators still determine whether submit is allowed

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the Feishu human-review gate before edge submit by default. The exceptions are explicit structured product policy: a detail-confirmed mandatory rule whose actions include comment and whose `comment_approval` is `auto_approve`, or an account/source approval policy that explicitly authorizes automatic approval. An automatic path MUST send the required readable notice before submit according to that policy and MUST fail closed when a mandatory notice is unavailable. A process environment variable MUST NOT disable review or create an automatic-approval exception. An unwired approval port, review timeout, rejection, or failed mandatory notice MUST produce an honest non-submitting outcome with no success mark.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a Facebook comment has no valid structured automatic-approval policy
- **THEN** it MUST request Feishu approval and MUST NOT submit until approved

#### Scenario: Structured standing approval notifies then submits
- **WHEN** full-detail matching confirms an account rule with comment plus `comment_approval:auto_approve`
- **THEN** the system MUST send the required final-comment notification first and MAY submit only after that send succeeds

#### Scenario: Review or auto-approval notification failure is honest no-submit
- **WHEN** review is unwired/timed out/rejected, or a mandatory auto-approval notice fails
- **THEN** the run MUST audit a non-success reason, MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Environment cannot disable review
- **WHEN** an inherited or deployed `AIDCP_FB_COMMENT_REVIEW_ALL=false` is present but no structured account/source policy authorizes automatic approval
- **THEN** the comment still requires review and the environment value has no effect

#### Scenario: Red-line reversal — implicit auto-post is forbidden
- **WHEN** an implementation auto-posts because of free-form persona wording, account id, nickname, a global heuristic, or an environment variable rather than a validated structured policy
- **THEN** it MUST be treated as a violation and not merged

### Requirement: 评论链人设注入对齐互动评估样板

评论支线的判定与产文角色（`CommentAppraiser` / `CommentComposer` / `CommentDeAiFlavor` 的两条改写路径）SHALL 注入账号人设的**性格字段**（`background` / `tone`，判定角色另注入 `like_principle` 类互动原则；对齐互动评估角色的注入水平），使不同人设账号在「是否开口」「怎么说话」上产生可区分差异；判定角色 SHALL 注入 `behavior_guidelines.style`（浏览风格）作为行为倾向背景。撞车改写路径（与参考语料雷同触发的重写）MUST 与主改写路径同源使用人设口吻行，MUST NOT 以无人设的通用口吻改写。

本要求只约束**生成式**正文链路。模板正文链路 MUST NOT 读取人设、MUST NOT 经过人设口吻改写，也 MUST NOT 因账号无人设而被拒绝——Facebook 规则批次的模板评论即走这条链路。无人设账号在生成式链路上仍按 `mandatory-account-persona` 既有闸诚实拒绝，本要求不改变该行为。

#### Scenario: 判定与撰写 prompt 含性格字段

- **WHEN** 构造 `CommentAppraiser` / `CommentComposer` 的 prompt
- **THEN** prompt 含该账号 `background` / `tone`（判定另含互动原则与浏览风格），MUST NOT 仅注入「名字 + 职业 + 兴趣清单」

#### Scenario: 撞车改写带人设口吻

- **WHEN** 评论草稿与参考语料近似撞车、触发重写
- **THEN** 重写 prompt 含该账号人设口吻行（与主改写路径同源），产出保留该账号个人腔，MUST NOT 收敛为通用中庸腔

#### Scenario: 模板正文不进入人设注入链路

- **WHEN** 有效正文方案为模板，正文取自账号模板或区域通用模板
- **THEN** 该正文直接进入既有校验与提交链，不构造撰写 prompt、不做人设口吻改写，也不因账号无人设被拒绝

### Requirement: 撰写语境穿透与言语行为多样化

系统 SHALL 让评论撰写基于「刚发生的真实体验」而非孤立正文：`CommentAppraiser` 判定「值得评」的理由 SHALL 经 `comment.appraised` payload（可选字段）穿透到撰写 prompt；撰写 prompt SHALL 注入本次互动类型（like / collect）与作者名；会话内已采集到该笔记当页评论时 SHALL 注入头部摘要（限幅 3-5 条）以贴合现场话题、避免重复他人已说，未采集到时 MUST 诚实不注入、MUST NOT 为此改动事件时序或新增边缘采集。撰写的**切入角** SHALL 为可选面板（共鸣 / 真问题 / 自己的相关经历 / 纯情绪短评等）由人设与内容选择，MUST NOT 钉死单一「共鸣或提问」两模式；长度约束 SHALL 表述为「一般一两句，可以更短、更随口」（保留平台上限硬闸），MUST NOT 诱导恒定长度。

#### Scenario: 判定理由穿透进撰写

- **WHEN** `CommentAppraiser` 产出「值得评」判定且 payload 携带 reason
- **THEN** 撰写 prompt 含「你刚才觉得这篇值得评，因为…」语境；payload 无 reason 时省略该片段（可选字段向后兼容）

#### Scenario: 当页评论缺失不编造

- **WHEN** 会话内未采集到该笔记的当页评论
- **THEN** 撰写 prompt 省略现场评论片段，MUST NOT 编造「大家在聊…」占位语境

#### Scenario: 切入角与长度不钉死

- **WHEN** 同一账号在多篇不同笔记下撰写评论
- **THEN** 切入角随人设与内容在面板内变化、长度自然波动，MUST NOT 每条都呈「一句共鸣 / 一个提问 + 近似等长」的模板签名

### Requirement: 去 AI 味信号集覆盖评论体裁

`CommentDeAiFlavor` 的 AI 味检测 SHALL 使用**评论体裁专用信号集**（客套模板句如「感谢分享」「学到了」单句成评、空洞附和、和稀泥句式等，人工校准维护），命中 **1 条**即触发人设口吻改写；MUST NOT 仅复用发帖侧长文议论文连接词词表与其阈值（该词表对评论体裁近零召回、致改写路径长期空转）。改写指令 SHALL 允许「可以更短、更随口」，MUST NOT 强制等长。发帖侧既有词表与阈值不受本要求影响。

#### Scenario: 客套模板评论被检出并改写

- **WHEN** 评论草稿为「感谢分享，学到了！」类客套模板句（不含议论文连接词）
- **THEN** 评论体裁信号集命中、触发按账号人设口吻的改写；改写后保持贴题、允许比原文更短

#### Scenario: 发帖侧不受影响

- **WHEN** 发布正文走发帖侧去 AI 味
- **THEN** 发帖侧词表、阈值与行为与本 change 之前一致

### Requirement: 强制评论必须生成贴题终稿并有界失败，禁止模板伪造“一定”

mandatory comment SHALL 继续经过 `CommentComposer`、`CommentDeAiFlavor` 与反照搬护栏。撰写 prompt MUST 注入规则的 `comment_guidance` 并明确本篇必须产出具体评论；模型返回弃权、空或超长时 MAY 有界重试一次。重试仍失败、清洗为空或仍与参考语料近似照搬 MUST 诚实 `comment.skipped`，MUST NOT 回退固定模板或占位话术来伪造“已满足必评”。mandatory context MUST 沿所有 `comment.*` payload 透传到审批终点。

#### Scenario: 强制评论按规则指引生成
- **WHEN** 越南招工规则命中且评论指引要求用越南语询问岗位细节
- **THEN** composer prompt 含该指引和必产要求，产出的终稿继续经过去 AI 味与反照搬检查

#### Scenario: 两次都无法生成则诚实不发
- **WHEN** mandatory composer 首次与一次重试均失败、弃权、为空或超长
- **THEN** 系统 emit 真实 skip 原因，不使用“还招吗/支持一下”等固定模板替代，不报告评论成功

### Requirement: mandatory 免审评论必须区分预授权与真实终态

mandatory comment 在撰写前 MUST 使用带稳定 reason 的硬风控预检。预检被 `state:*` 或 `quota:minute|hour|day` 拒绝时 MUST 在同帖 mandatory like 已有机会入队后诚实跳过，MUST NOT 调 composer、MUST NOT 发免审通知、MUST NOT声称该评论已授权或已发布。预检通过不构成配额预占，下发前最终硬风控 MUST 保留。

免审通知成功时 SHALL 只表述“终稿已预授权、等待平台执行”，使用非绿色中性状态，并携 requestId、账号、目标与终稿。通知之后系统 MUST 以同一 requestId 最多回报一个可见终态：`confirmed`、`pending`、`failed` 或 `unknown`。只有 edge 真实回 `action.completed{action:'comment',ok:true}` 才能回 `confirmed` 并记成功；`pending_group_approval` MUST 回 `pending` 且不计成功；明确风控/页面/下发/edge 失败 MUST 回 `failed`；命令或迁移在途时断线、会话结束或有界超时 MUST 回 `unknown`，明确要求人工核对且不得猜测上墙状态。

#### Scenario: 硬风控预检拒绝不白跑也不发卡
- **WHEN** mandatory comment 命中，但 `explain('comment')` 返回 `quota:minute`、`quota:hour`、`quota:day`、`state:restricted` 或 `state:frozen`
- **THEN** 系统不调用 composer、不发送预授权卡，并留下带原始稳定 reason 的审计日志；同帖 mandatory like 的派发顺序不受影响

#### Scenario: 预授权卡不是成功卡
- **WHEN** mandatory auto-approve 终稿通知成功
- **THEN** 卡片 MUST 使用中性/黄色语义说明“已预授权、等待平台执行”，MUST NOT 使用绿色“已成功”语义

#### Scenario: 平台确认成功才回成功终态
- **WHEN** 已预授权评论收到 edge `action.completed{action:'comment',ok:true}`
- **THEN** 系统以同一 requestId 回一次绿色 `confirmed` 终态；该回执是唯一允许称评论已发布并计成功的依据

#### Scenario: 群审批与明确失败如实分档
- **WHEN** edge 返回 `pending_group_approval`，或最终风控/迁移/下发/edge 返回明确失败
- **THEN** 前者回黄色 `pending` 并说明尚未上墙，后者回人话 `failed`；两者均不得计成功或显示机器码

#### Scenario: 断线或超时保持未知
- **WHEN** 评论命令已下发或评论迁移仍在途，但连接断开、会话结束或超过有界回执时间仍无终态
- **THEN** 系统以同一 requestId 回黄色 `unknown`，说明是否上墙未知、需人工核对；MUST NOT猜成功、MUST NOT补记配额

### Requirement: Facebook 评论撰写与重写保持账号写作语言
Facebook `CommentComposer`、定向评论撰写器、强制互动评论以及 `CommentDeAiFlavor` 的去 AI 味/撞车重写 SHALL 使用账号 soul 的 `writing_language`。目标帖正文和评论区语言只作语境，MUST NOT 覆盖账号配置；重写结果语言不匹配时 SHALL 回退已验证原文或诚实停止。

#### Scenario: 通用 Facebook composer 使用账号语言
- **WHEN** Facebook CommentComposer 为 `writing_language=en` 的账号撰写评论
- **THEN** prompt 明确要求只输出英文，现有“跟随帖子语言”规则不得覆盖它

#### Scenario: 定向 Facebook composer 使用同一规则
- **WHEN** CommentScheduler 的 Facebook 定向路径为 `writing_language=vi` 的账号撰写评论
- **THEN** 定向 prompt 同样要求越南语并通过同一语言守卫，MUST NOT 与通用 composer 漂移

#### Scenario: 去 AI 味不切换语言
- **WHEN** 已验证为中文/英文/越南语的 Facebook 评论触发去 AI 味或撞车重写
- **THEN** 重写提示要求保持输入语言；若结果不匹配则回退原评论或停止，MUST NOT 把另一语言文本送审/提交

