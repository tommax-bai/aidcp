# Design — comment-interaction

## 背景与现状（坐实，带文件:行）

- 浏览闭环是事件驱动单总线，`RoleDispatcher.setup()`（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:242-306`）注册各角色，单注的一篇笔记走
  `feed.entered → content.valuable → note.detail.arrived → quality.pass → reading.* → interaction.completed → profile.* → back`。
- 写互动只有 like / collect / follow（`src/comm/protocol.ts` 仅 `interaction.like/collect/follow`；`command-bridge.ts` 无 comment 分支）。
  `comment` 只作为风控动作枚举与保留通道存在（`src/risk/types.ts`、`quotas.ts` 已定义 comment 配额），从未接线为下发动作。
- "是否进个人主页"的判断由 `AuthorEvaluator` 直接消费 `interaction.completed`（`src/agents/author-evaluator.ts:31-108`）；
  `interaction.skipped`（pass）直接进 `BackToFeed`（`src/agents/back-to-feed.ts:27-37`），不进主页。
- `comment_reviewer` 只读评论、明示不发评论（`src/agents/comment-reviewer.ts`）。

## 关键决策

### 1. 位置：串接在"互动完成 → 是否进主页评估"之间（不是并行、不是直接进主页）

- 评论要发，必须在**笔记详情页还开着**时发（一旦下发 `profile_open`，页面切走、评论框消失）。所以评论支线 MUST 串行、且进主页要等评论结束。
- 评论支线挂在 `interaction.completed`（**只在真 like/collect 过的笔记上评**——评论是最高封号信号写互动，必须有互动信号背书；pass 的笔记不评）。
- 把 `AuthorEvaluator` 的触发**从 `interaction.completed` 改挂到评论支线终结事件**（`comment.done` / `comment.skipped`），由此形成真正的串行边：
  `互动完成 → 评论评估 →（评论支线）→ 是否进主页评估 → 进/不进`。**评论完触发的是"是否进主页评估"，不是直接进主页**（已关注跳主页等逻辑照常生效）。
- 用独立 `comment.*` 事件族，不污染 `InteractionCompletedPayload.actions`（它同时被命令翻译与 `AuthorEvaluator` 消费，扩宽会把评论文本泄进进主页决策）。

> 演进说明：评审曾权衡"挂 `reading.done`（覆盖未点赞笔记）vs 挂 `interaction.completed`（只覆盖已互动）"。本设计取后者——风险正确（每条评论都有互动背书），并与用户"先互动才评论"的意图一致。

### 2. 角色：评估→撰写→去AI味→审批，四段不合并

- 评估与撰写**不合并**：评估只产"要不要评"的判定（便宜、决定支线分叉），撰写才付 LLM 产文本——这样数量/门槛/配额能在最便宜的评估阶段拦掉，过不了不付撰写成本。
- 去AI味为**独立确定性步骤**：复用发帖侧 `PostProcessor`（`src/publish-agent/post-processor.ts`）与合规声明判定（`roles/compliance-decider.ts` 的规则），无 LLM、可独立回归。
- `CommentComposer` 是浏览闭环**首个自由文本角色**（其余角色都产结构化判定）：要自管空/超长/跨笔记近似去重/避开裸 `@`（编辑器 `data-tribute` 提及）。
- 复用 `BaseRole.decide()/log()` 的逐决策日志；`CommentAppraiser` 结构对标 `InteractionAppraiserRole`。

### 3. 精品 + 每账号每日上限（后台可配、与风控取小）

- 精品 = 两道闸：① 高热度/高价值门槛（用详情页已有的真实点赞/收藏量等）；② 每日少量名额。
- **每账号每日上限**做成后台可配（console 读写、面板 `/api`、PG 按 accountId 持久化）；**生效 = min(运营配置, 风控安全配额)**。
- "今日已评数"复用风控按账号按天计数（`risk_counters`，schema 已支持 comment），不另起表。
- 门槛/数量在评估阶段判定，超了直接"不评 → 进主页评估"。

### 4. 循环内真人审批：暂停态 + 短超时（用户明确选择"循环内等"）

- 物理约束：要在详情页开着时发，故审批只能循环内等——这意味着**整场浏览在这篇笔记上暂停，直到人点批或超时**。
- 复用验证码那套"按-edge 暂停下发"的闸（`captcha-restrict-and-interaction-gating` 已落），进入**被看门狗认得的「等评论审批」暂停态**（不判 idle 重启、`session.end` 仍可达）。
- **硬短超时**（可信停留上限——人盯一篇笔记几分钟本身是异常信号）；超时/拒绝 → 本篇不评、记审计 → 进主页评估。
- 复用发帖 AC-PUB 的 `/tmp` 先到先得审批信号（`server.ts` `isPublishApproved` / `feishu/ws-receiver.ts` `writeApprovalSignal`），换**评论专属 requestId** 命名空间；**未授权绝不下发**。
- 备选（未采用，留作 v2）：离线预审 + 按 id 重开笔记补发——与用户"进主页前同步发完"相悖，故 v1 取循环内等。

### 5. 执行端动作：探针已坐实（aidcp-edge@d377691）

真机 CDP 探针（`aidcp-edge/scripts/comment-probe.ts`，只读默认 + 受闸真发）实测结论：
- 折叠态入口：`.engage-bar .input-box .content-edit .not-active.inner-when-not-active`（"说点什么"）→ 激活后 engage-bar 加 `.active`。
- 真编辑器：`p#content-textarea.content-input[contenteditable=true][data-tribute=true]`；**必须点编辑器本体落 caret**（不能靠 activeElement）。
- 拟人输入：`dispatchKeystrokes` 逐字 ✅ 落进编辑器并读回成功。
- 提交键：`.engage-bar.active … button.btn.submit`（"发送"）；**空/无效时 `btn submit gray`（禁用），有效内容后 `.gray` 消失** = 可提交信号。
- **发布后校验**：发送后**编辑器清空 且 自己的评论作为顶部新 `div#comment-<id>` 行出现**（评论数文本不可靠，不依赖）。
- 套进既有 like/collect 的"定位→动作→后置校验→如实回报"契约（`browse-session.ts` `executeLikeOrCollect` / `reportActionCompleted`），复用 `LocatingEngine` 三道闸、`captchaPresentFresh`。

### 6. 风控接线：单写不破、计数挂真回执

- `canInteract` / `freshBudget` / `consumeBudget` / `interaction.occurred` 四处并集加 `comment`；下发前过 `canDo('comment')`、被拒诚实跳过。
- 计数只在真回执 `ok:true` 时 `record('comment')`（对齐 follow 的"按真实结果记账"），终态仅云端 `RiskController` 单写。

## 不做（边界）

- 不做离线预审/补发（v2）；不做评论的多图/表情/回复他人评论（后续）；不把高热度门槛做成可配（先内置阈值，留干净缝）。
- 不复用 `publish-pipeline` capability 名（"publish" 属发帖、且四个 publish-* 仍在途）；只复用其独立件（PostProcessor / 合规判定 / `/tmp` 审批信号）。

## 排期与依赖

- 先决：执行端探针已清零未知（done）。
- cloud 部分排在 `follow-already-followed-truthful-report` 与 `interaction-appraiser-like-rebalance` 归档之后（同改 `role-dispatcher` 回执记账 / `InteractionAppraiser`），按其落地形态对齐。
- `skip-profile-visit-if-followed` 无结构冲突（评论在其前），补一条已关注作者验收。
- 部署前按 ECS dry-run 纪律核对 scope。
