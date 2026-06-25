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
`CommentComposer`（产评论文本）→ `CommentDeAiFlavor`（复用发帖侧 `PostProcessor` 去 AI 味 + 合规声明判定，确定性、无 LLM、不抛异常）→
`CommentApprovalGate`（循环内飞书人审）。任一段失败 / 不通过 MUST emit `comment.skipped` 并带如实原因，MUST NOT 伪造文本或伪造通过。
`CommentComposer` 作为浏览闭环首个自由文本角色，MUST 自己保证：空 / 超长文本如实跳过、做跨笔记近似去重、撰写时避开裸 `@`（编辑器带 `data-tribute` 提及）。

#### Scenario: 评估为是才进入撰写
- **WHEN** `CommentAppraiser` 判定该笔记值得评论且配额/门槛通过
- **THEN** emit `comment.appraised` 触发 `CommentComposer` 产文本 → `CommentDeAiFlavor` 去 AI 味 / 合规 → `CommentApprovalGate`；评估为否则 emit `comment.skipped`，不进入撰写（不付 LLM 撰写成本）

#### Scenario: 去AI味为确定性步骤、可独立回归
- **WHEN** `CommentComposer` 产出草稿文本
- **THEN** `CommentDeAiFlavor` MUST 复用 `PostProcessor.process` 做禁用词扫描 + 至多一次改写，并按合规判定决定是否需 AI 声明；该步 MUST 无 LLM、不抛异常、可脱离风控 / 审批单测

#### Scenario: 红线反例——撰写失败伪造文本（禁止）
- **WHEN** `CommentComposer` LLM 失败 / 产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST emit `comment.skipped{reason}`，绝不发出无法落地的伪造评论

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬数值阈值**：仅当详情页 `likeCount > 1000` **且** `collectCount > 300`（均严格大于）时该笔记才达门槛；任一不满足 MUST 直接 `comment.skipped`、不进入撰写 / 去 AI 味 / 审批。硬数值阈值之上，现有 LLM 精品判定（高热度 + 高价值）与飞书人审继续叠加（阈值为必要非充分条件）。此外系统保留**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api` 下发）；**实际生效每日上限 = min(运营配置上限, 风控安全配额)**，"今日已评数" MUST 复用风控按账号按天计数。数量、阈值与门槛 MUST 在评估阶段就判定：超上限 / 不达数值阈值 / LLM 判不值得 MUST 直接走"不评论 → 进主页评估"分支，MUST NOT 进入撰写 / 去 AI 味 / 审批。

#### Scenario: 达到每日上限即停止评论
- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再评论，直接进"是否进主页评估"

#### Scenario: 运营配置不可越过风控安全线
- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达硬数值阈值不评
- **WHEN** 笔记 `likeCount ≤ 1000` 或 `collectCount ≤ 300`（按详情页真实点赞 / 收藏量）
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过，不进入撰写

#### Scenario: 阈值边界严格大于
- **WHEN** 笔记 `likeCount === 1000` 或 `collectCount === 300`（恰好等于）
- **THEN** MUST 视为未达门槛、不评（「超过」语义为严格大于，等于不算达标）

#### Scenario: 达数值阈值仍需过 LLM 与人审
- **WHEN** 笔记 `likeCount > 1000` 且 `collectCount > 300`
- **THEN** 该笔记仅**通过硬数值阈值**进入后续判定，是否真评论仍由 LLM 精品判定 + 飞书人审决定（阈值是必要非充分条件）

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

因评论 MUST 在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。
等待期间系统 MUST 进入**被看门狗认得的「等评论审批」暂停态**（复用按-edge 暂停通道：暂停期间不发其他浏览 / 互动命令、`session.end` 仍可达、看门狗按"有意暂停"而非 idle 处理）。
MUST 设**硬性短超时**（可信停留上限）；超时 / 拒绝 MUST 视为本篇不评、记审计、emit `comment.skipped` 进"是否进主页评估"。
审批 MUST 复用既有 `/tmp` 先到先得审批信号机制、用**评论专属 requestId 命名空间**（与发帖 `publish-<recordId>` 区分）；**未获授权 MUST NOT 下发评论命令**。

#### Scenario: 授权后下发、超时则跳过
- **WHEN** 飞书人审在超时窗口内写入评论 requestId 的授权信号
- **THEN** `CommentApprovalGate` MUST emit `comment.approved` 触发评论命令下发；若窗口内未授权 / 被拒，MUST emit `comment.skipped{reason:'approval_timeout'|'rejected'}`、退出暂停态、进"是否进主页评估"

#### Scenario: 等待审批期间不卡死会话、不误判 idle
- **WHEN** 浏览会话处于"等评论审批"暂停态
- **THEN** 看门狗 MUST 按"有意暂停"处理、MUST NOT 因 idle 重启会话；该 edge 的其他浏览 / 互动命令 MUST 在暂停期间不下发，`session.end` MUST 仍可达

#### Scenario: 红线反例——未授权或超时仍发评论（禁止）
- **WHEN** 有实现在无授权信号 / 超时后仍下发评论命令，或为绕开"页面久留"把评论改成无人审自动直发
- **THEN** MUST 视为违规、不予合入；评论 MUST 在授权信号存在时才下发（AC-PUB），未授权 / 超时一律 `comment.skipped` 不发

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

