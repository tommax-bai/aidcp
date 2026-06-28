# Design — decouple-publish-generation-from-dispatch

## 1. 现状（坐实，带文件:行）

发布是一次同步调用 `PublishOrchestrator.trigger(triggerInput)`：

- **让位发生在最早**：`trigger()` 一进来（跳过「已在跑则忽略」后）即 `onPublishStart(accountId)`（`publish-orchestrator.ts:55-58`）→ `server.ts:449-458` 的 `endSessionForAccount(accountId,'publish_takeover')`（结束浏览、标记不可续场）。`finally` 里 `onPublishEnd`（`publish-orchestrator.ts:90-94`）→ `resumeSessionForAccount`（经续场各闸起新浏览）。让位包住整次调用。
- **生成是黑板事件级联、纯云端**：`trigger()` 写 `trigger` 键启动级联（`publish-orchestrator.ts:70`），ContentScout→ContentCreator→（清洗/配图/质检/元数据并行）→ContentAssembler→TitleCreator/ApprovalGatekeeper，全部 LLM/规则、**不碰边缘**。
- **人审等待塞在最后一个角色内联**：`PublishExecutor.handleAutoPublishViaSequencer`（`publish-executor.ts:273-340`）落库草稿（`status='draft'`）→ 读审批信号 `isApproved('publish-<recordId>')`→ 未授权则发飞书审批卡 + `waitForApproval` 在 `approvalWaitMs`（生产 900000ms=15min，`server.ts:973-977`）内每 `approvalPollMs`（3s）轮询；期满未授权 → `updateStatus('needs_review')` 返回（`publish-executor.ts:298-302,342-354`）。角色超时 `roleTimeoutMs`（生产 1080000ms=18min）须 ≥ 审批窗 + 序列耗时。
- **下发是唯一碰边缘的一段**：授权后 `CommandSequencer.executePublishSequence(approvedByUser:true)`（`publish-executor.ts:304-317` → `command-sequencer.ts:163-245`）逐条 `send→await→advance`：`navigate_entry→select_mode→[upload_image]→fill_field→…→submit_publish→capture_postId`。
- **审批信号是独立耐久原语**：飞书点按钮（`feishu/ws-receiver.ts`）/ 面板 `/approve`（`panel-server.ts:243-264`）都 `writeApprovalSignal`（首写者胜）写 `/tmp/aidcp-publish-approve-<requestId>.json`；`isPublishApproved` 读之，`approved===true` 才放行。
- **全局单飞**：`trigger()` 开头 `status==='running'` 即忽略（`publish-orchestrator.ts:39-49`）。故 A 等人审的 15 分钟里 B 发不了。

**痛点**：让位与人审等待都发生在「不需要边缘」的阶段，却独占边缘并占住全局单飞；审批超时是被这种同步占用逼出来的产物。

## 2. 业界设计模式映射

- **生产者/消费者 + 持久工作队列**：把「生成草稿」（生产）与「下发上线」（消费）解耦，草稿落耐久存储（已是 `publish_log`），消费由独立触发驱动。经典「outbox/审批队列」模式。
- **人审作为带外异步审批（Human-in-the-loop, out-of-band）**：审批不应阻塞生产线程；审批结论是一个**事件**，到达即推进状态机，而非被生产线程轮询等待。
- **资源独占最小化（critical section 收窄）**：边缘（一边缘一 Chrome）是稀缺独占资源；只在真正操作边缘的临界区持锁，临界区前的准备（生成、候审）不持锁。
- **WYSIWYG 审批（所见即所发）**：审批对象 = 冻结的草稿快照；批准即认可该快照，下游不重生成（已有「审批卡显示真实标题，人工通过即认可该标题+正文+配图」requirement 支撑）。

## 3. 选定设计

在「人审通过」处切成两段，**cloud-only**：

### 段一：生成候审（不持边缘锁、不让位）
`trigger()` 跑生成级联 → 落库草稿（`status='pending_approval'`，含标题/正文/标签/图 URL/`publish_metadata`/血缘）→ 发飞书审批卡 → **返回**。全程不调 `onPublishStart`、不结束浏览会话。生成段超时回落到只覆盖生成（约 2–3min 量级），不再为容纳审批抬高。

### 段二：下发上线（持边缘锁、通过即切）
人审授权信号到达 → 触发对应 `recordId` 的下发：
1. 按账号取下发锁（同账号串行）；
2. 让位：`endSessionForAccount(accountId,'publish_takeover')`；
3. 从 `publish_log` 读回草稿，重建 `PublishSequenceInput`（`approvedByUser:true`）；
4. `CommandSequencer.executePublishSequence` 驱动边缘；下发时若该账号无在线边缘 → 诚实 `failed`（复用 `resolveEdgeIdForAccount` 无节点判败红线）；
5. 回写 `published`（+postId/postUrl）/ `failed`；
6. 解除让位：`resumeSessionForAccount` 经续场各闸起新浏览。

**触发方式（事件驱动优先）**：审批写入点（飞书 `handleCardAction` / 面板 `/approve`）在 `writeApprovalSignal` 成功后，投递一个「下发 `recordId`」的内部事件给下发路径。无可靠事件时以低频兜底扫描「`pending_approval` 且信号已 `approved`」的草稿作为补偿（at-least-once，靠下发段幂等去重）。

**取消超时**：删除 `waitForApproval` 内联轮询与「期满 `needs_review`」。草稿停在 `pending_approval` 无限期，终态只由两条边推进：人审授权 → 下发；运营显式否决/撤稿 → `rejected`/`discarded`（既有否决信号路径，非超时）。

**并发收敛**：生成段单飞保持；新增「该账号已有 `pending_approval` 草稿则不再生成新草稿」与「下发段按账号单飞」。

## 4. 关键决策（用户已拍板）

- **通过即切**：授权到达即下发，不等自然空档。换来实现最简、独占窗口已大幅缩短；自然空档调度作为可选后续优化（见 §6）。
- **陈旧草稿如实照发**：草稿在生成时刻定稿，批准时不重生成、不回灌期间的人设/配置变化。审批卡即将发的成稿，所见即所发。代价（人设中途改动则发旧调性）可接受且可被审批卡看见。
- **下发时边缘离线 → 诚实失败**：不引入「等边缘重连再发」的下发重试队列（YAGNI）；失败可见，运营可重触发。重试队列列为后续可选。

## 5. 不变量（必须守住）

- **AC-PUB**：下发只在 `approved===true` 时发生；取消超时**绝不**意味着「久未审批就自动发」——恰恰相反，无授权则永不下发。
- **诚实**：下发成功判定仍锚真实平台成功信号（`publish-submit-integrity` 不变）；抓不到 postId 不误判失败；离线诚实失败不伪造。
- **让位最坏故障是诚实暂停**：下发段解除让位的保证终止点缺失时，停在「无浏览会话」诚实暂停，**绝不**让浏览在下发途中把边缘拽回 feed 撞页。
- **续场闸不变**：下发后起新浏览仍须过调度开关/人设/活跃时段/每日上限/风控各闸。

## 6. 对抗性评审（过度设计 / 失败模式）

- **会不会过度工程化成完整任务队列？** 不。草稿存储已是 `publish_log`；「队列」= 一个状态列 + 按账号串行下发 + 可选兜底扫描。不引入外部 MQ。✅ 守 YAGNI。
- **审批事件丢失（飞书写了信号但下发事件没投递）怎么办？** 低频兜底扫描「`pending_approval` + 信号 `approved`」补偿；下发段幂等（已 `published`/下发中的 `recordId` 不重入）。✅
- **重复授权 / 重复点击？** 审批信号首写者胜（既有）；下发段按 `recordId` 幂等 + 按账号单飞。✅
- **草稿堆积？** 每账号至多一份 `pending_approval` 草稿，未处理前不生成新草稿。✅
- **下发途中边缘掉线？** 与今天同：诚实 `failed`，不伪造、不静默；浏览会话保持诚实暂停待重连/运营介入。✅
- **陈旧草稿发出过期内容？** 已知接受（用户决策）；审批卡是所见即所发的最后一道人控。若日后要时效护栏，可加「草稿超 X 龄则到下发时提示/需复批」——本 change 不做。
- **去掉超时后运营永不处理 → 草稿长挂？** 那是无授权态，本就不该发；长挂草稿是「待办」而非「故障」，后台可见、可否决。比今天「逼 15 分钟内决定、否则 needs_review」更符合人审本意。✅

## 7. 边界

- 仅笔记发布。评论不改。
- 协议/边缘零改动。
- 不改触发扳机（`PublishScheduler` 三扳机不动）、不改 AC-PUB 授权判定、不改续场闸本身——只改「触发后到下发之间」的让位时机与审批等待方式。
