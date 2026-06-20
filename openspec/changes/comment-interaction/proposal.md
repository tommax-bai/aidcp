# 浏览闭环新增「发评论」互动（精品逻辑 + 循环内人审）

## Why

- 浏览闭环现有的写互动只有 like / collect / follow，**没有"在笔记下留言"的能力**（`comment_reviewer` 只读评论、不发评论；
  协议里 `comment` 只作为风控动作枚举与保留通道存在，从未接线为下发动作）。
- 评论是**价值最高、也是封号信号最强**的公开文本写互动——它在他人笔记下、以人格身份留下不可逆的公开文本。
  因此目标是**精品策略**：只在**高热度 / 高价值**笔记上评、**每天少量**、**按账号在后台可配上限**、且**每条循环内过飞书人审**。
- 「发评论」执行端三处关键未知（评论框选择器、提交控件、发布后校验信号）**已用真机 CDP 探针坐实**
  （探针 `aidcp-edge/scripts/comment-probe.ts`，已提交 `aidcp-edge@d377691`；结论见 `design.md`）。执行端不再有拦路未知。

## What Changes

> 触及协议的部分为 **BREAKING**（新增一条消息、计数 54→55）。其余为浏览闭环内的新增角色与接线。

- **【cloud】评论支线接线（接在互动完成 → 进主页评估之间）**：评论支线挂在 `interaction.completed`（即**只在真点过 like/collect 的笔记上**触发）。
  把"是否进个人主页"的判断（`AuthorEvaluator`）的触发**从 `interaction.completed` 改挂到评论支线的终结事件**（`comment.done` / `comment.skipped`），
  形成串行：`interaction.completed → 评论评估 →（评论支线）→ 是否进主页评估`。评论支线无论成功 / 跳过 / 失败，**最终都汇到"是否进主页评估"出口、只走一次**；
  **评论完是触发"是否进主页评估"，不是直接进主页**。新增独立 `comment.*` 事件族，**不复用 / 不污染** `InteractionCompletedPayload.actions`。
- **【cloud】四段单职责角色（评估→撰写→去AI味→审批，不合并）**：
  `CommentAppraiser`（只判定要不要评、不产文本）→ `CommentComposer`（产评论文本，浏览闭环首个自由文本角色）→
  `CommentDeAiFlavor`（复用发帖侧 `PostProcessor` 去 AI 味 + 合规声明判定，确定性、无 LLM）→ `CommentApprovalGate`（循环内飞书人审）。
  每段失败 / 不通过 MUST 如实 `comment.skipped`，绝不伪造。
- **【cloud】精品门槛 + 每账号每日评论上限（后台可配）**：`CommentAppraiser` 仅在笔记过**高热度 / 高价值门槛**时才可能评；
  新增**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api`）；**实际生效 = min(运营配置上限, 风控安全配额)**。
  "今日已评数"复用风控按账号按天计数。数量 / 门槛在**最便宜的评估阶段**就拦截，过不了直接走"不评论 → 进主页评估"。
- **【cloud】循环内真人审批（带暂停态 + 短超时）**：评论必须在**笔记详情页仍开着**时整条跑完，故审批**循环内等**；
  复用验证码那套"按 edge 暂停下发"的闸，使浏览会话进入**被系统认得的「等评论审批」暂停态**（看门狗按"有意暂停"处理、不判 idle 重启）。
  设**短超时**（可信停留上限）；**超时 / 拒绝 → 本篇不评、记审计 → 进主页评估**。复用发帖 AC-PUB 的 `/tmp` 先到先得审批信号，
  用**评论专属 requestId**；**未授权绝不下发评论命令**。
- **【cloud】风控接线（单写不破）**：`canInteract` / 会话预算 / `consumeBudget` / `interaction.occurred` 四处动作集合**加入 `comment`**；
  `RiskController.canDo('comment')` 既已支持（配额已定义），`restricted` / `warned` / `frozen` 自动拦截；**计数只在执行端真回执成功时 `record('comment')`**（按账号持久化）。
- **【BREAKING · 协议】新增 `interaction.comment`（cloud→edge）**：两份 `protocol.ts` 逐字一致 + `CommentPayload{noteId,text,thinkMs}` +
  `command-bridge` 映射 + `EdgeCommand.action` 并集 + `docs/protocol.md` + 两份 `protocol-contract.test.ts` 计数 **54→55**。
- **【edge】实装 `executeComment`（探针已坐实）**：点折叠态"说点什么"入口激活 → 点编辑器本体 `p#content-textarea` 落 caret →
  `dispatchKeystrokes` 拟人输入（避开裸 `@`，`data-tribute` 提及）→ 提交前 `captchaPresentFresh` 自检 → 点 `.engage-bar.active … button.btn.submit`（"发送"）→
  **后置校验：编辑器清空 且 自己的评论作为顶部新 `div#comment-<id>` 行出现** → 经既有 `reportActionCompleted{action,ok,reason}` 如实回报。
  找不到框 / 按钮 `no_target`、未生效 `state_unchanged`、验证码 `blocked_by_captcha`，**绝不静默假成功**。
- **【console】每账号每日评论上限配置 UI**：在管理后台按账号读写该上限（新增一个写操作 + 面板只读回显）。

## Capabilities

### New Capabilities

- `comment-interaction`：浏览闭环的「发评论」互动——接在"互动完成"与"是否进主页评估"之间的评估→撰写→去AI味→循环内人审→下发链路；
  精品门槛 + 每账号每日上限（后台可配、与风控安全配额取小）；循环内审批暂停态 + 短超时 + AC-PUB 未授权不发；
  执行端拟人输入 + 发布后校验如实回报、绝不假成功；风控按账号配额单写、计数挂真实回执；协议新增 `interaction.comment` 三处同步。

### Modified Capabilities

<!-- 不修改任何已合并 capability 的 requirement。复用 command-pacing 的 thinkMs（评论命令可携带，机制不变）、复用 DOM-first 定位三道闸（engine 不改）、
复用既有审批信号文件机制（路径契约不漂移、仅换评论 requestId 命名空间）、复用 RiskController 状态机（只读 canDo / 单写 record）。
browse-loop-resilience 看门狗与「等评论审批」暂停兼容（同验证码暂停：发给已暂停 edge 的 nudge 在传输层丢弃、session.end 仍可达），无 requirement 变更。 -->

## Impact

- **aidcp-cloud（主体）**：
  - 新增角色 `src/agents/comment-appraiser.ts` / `comment-composer.ts` / `comment-de-ai-flavor.ts` / `comment-approval-gate.ts`（均 extends `BaseRole`）。
  - `src/orchestrator/role-dispatcher.ts`：注册上述角色；新增 `comment` 命令翻译分支（`canInteract('comment')` 闸 → `sendCommand` → 真回执后 `consumeBudget`）；
    `freshBudget()` 加 `comments` 计数、`consumeBudget` 加 `comment` 分支；`canInteract` 并集加 `comment`；**`AuthorEvaluator` 改挂评论终结事件**；
    新增「等评论审批」按-edge 暂停的进入 / 退出（复用 captcha pause 通道）。
  - `src/event-bus/types.ts`：新增 `comment.appraised` / `comment.composed` / `comment.cleared` / `comment.approved` / `comment.held` / `comment.done` / `comment.skipped`。
  - `src/comm/handler.ts`：`interaction.occurred` 过滤与事件类型加 `comment`（真回执 `ok:true` 才计数）。
  - 复用（不改）：`src/publish-agent/post-processor.ts`（去 AI 味）、`src/publish-agent/roles/compliance-decider.ts` 的判定逻辑（合规声明）、
    `feishu` 审批卡 + `server.ts` 的 `isPublishApproved` / `writeApprovalSignal`（换评论 requestId 命名空间）、`RiskController.canDo/record` + `quotas`（comment 配额已定义）。
  - 新增**每账号每日评论上限配置**存储（PG，按 accountId）+ 面板 API 读写端点；`CommentAppraiser` 读取配置与今日已评数（风控计数）做 `min(配置, 风控配额)` 闸。
- **aidcp-edge**：
  - `src/browse/browse-session.ts`：新增 `interaction.comment` 命令分支 + `executeComment()`（探针坐实的定位 / 拟人输入 / 提交 / 后置校验 / 如实回报；复用 `LocatingEngine` 三道闸、`dispatchKeystrokes`、`captchaPresentFresh`、`reportActionCompleted`）。
  - `src/comm/protocol.ts`：镜像新增 `interaction.comment` + `CommentPayload`。
  - 探针 `scripts/comment-probe.ts` 已在仓（`d377691`），实装时作为选择器 / 后置校验的事实来源。
- **协议**：`interaction.comment`（+1，计数 54→55）；`command-bridge.ts` 加 `comment` 映射；`docs/protocol.md` 头部计数 + §2 表同步；
  `Record<MessageType,true>` 穷举 + `AC-PROTO-*` 守护两份 `protocol.ts` 不漂移。
- **DB（ECS PostgreSQL 库 `aidcp`）**：新增"每账号每日评论上限"配置（按 accountId，幂等 DDL）；复用既有 `risk_counters`（comment 按账号按天计数，schema 已支持）。不记敏感值。
- **aidcp-console**：管理后台新增"每账号每日评论上限"读写 UI（一个写操作 + 只读回显）。
- **安全红线（必须全过）**：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布——评论作为公开文本同受其约束）、
  `AC-RISK-*`（绝不自残、被禁 `record` 返 false、终态单写）、`MUST NOT 静默假成功`（评论后置校验如实回报）。
- **依赖与排期**：
  - 执行端未知项已由探针清零（先决条件已满足）。
  - 评论支线触碰的调度区域（`role-dispatcher` 的 `action.completed` 回执记账、`InteractionAppraiser`）与两个在途 change 重叠——
    **本 change 的 cloud 部分应排在 `follow-already-followed-truthful-report` 与 `interaction-appraiser-like-rebalance` 归档之后**，按它们落地后的形态对齐（按真回执记账）。
  - 与 `skip-profile-visit-if-followed` 无结构冲突（评论支线在其之前），但需补一条验收：已关注作者、主页被跳过时评论仍正常、且仍走"是否进主页评估"出口。
  - 复用发帖侧 `PostProcessor` / 合规判定 / `/tmp` 审批信号为独立件，**不需要** publish-* 改动先归档；但部署到 ECS 前按既有纪律做 dry-run scope 核对（rsync 会带上累积的 master）。
