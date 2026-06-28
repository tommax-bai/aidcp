## Why

当前一篇笔记的发布是**一坨同步流程**：触发后第一步就「让位」——干净结束该账号的浏览会话并标记不可续场，然后云端串行跑完「生成正文/配图/标题/元数据 + 质检 + 审批决策」，再在发布执行端**内联等待人审最长 15 分钟**（生产 `AIDCP_PUBLISH_APPROVAL_WAIT_MS=900000`，期满落 `needs_review`），人审通过后才把整条指令序列下发给边缘真发，最后才解除让位、起新浏览会话。让位与等待都包在 `PublishOrchestrator.trigger()` 这一次调用里（`publish-orchestrator.ts:55-58,90-94` 经 `server.ts:449-458` 的 `onPublishStart/onPublishEnd` → `endSessionForAccount/resumeSessionForAccount`）。

由此带来三个真实代价：

1. **独占窗口被严重放大**：真正需要独占边缘的只有最后的指令序列（导航→传图→填写→提交，约数十秒）；而前面的云端生成（约 1–3 分钟）与人审等待（最长 15 分钟）**根本不碰边缘**，却同样把该账号的浏览掐死。
2. **发布管线全局单飞，人审期堵死全部发布**：`PublishOrchestrator` 同一时刻只跑一条管线（`publish-orchestrator.ts:39-49`），A 在等人审的 15 分钟里，B 的发布触发被直接忽略。
3. **被迫设审批超时**：因为「等人审」塞在角色执行内部、占着管线与让位，不设上限浏览就被无限期掐死——于是只能给人审一个 15 分钟窗口，运营来不及处理就落 `needs_review`，逼运营仓促决定。

根因是：**让位与人审等待发生得太早、且与生成绑死在同一次同步调用里**。生成是 100% 云端、不碰边缘；草稿已经持久化（`publish_log` 带稳定 `recordId` + 标题/正文/图/元数据）；人审是独立的文件/面板信号（`/tmp/aidcp-publish-approve-<requestId>.json`，首写者胜）。即异步化所需的耐久状态与审批原语**都已就绪**，只差把流程在「审批边界」切开。

## What Changes

> 本 change 的改动为 **BREAKING**——它改变发布的**控制时序**（让位时机）与**审批生命周期**（去内联超时、改事件驱动下发）。但**不动协议、不动边缘、不动 AC-PUB 红线**（未授权绝不发布），是一个 **cloud-only** 重构。

把单坨发布拆成两段，在「人审通过」处切开：

- **【BREAKING】生成候审段不再让位浏览**：触发后 `PublishOrchestrator.trigger()` 只做「生成终稿 + 落库草稿 + 发飞书审批卡」，随即返回；**MUST NOT** 在此段调用 `onPublishStart`/结束浏览会话。该账号的浏览在生成与候审全程**照常进行**。
- **【BREAKING】审批通过即下发（通过即切）**：人审授权信号到达即触发下发段——此时才「让位」（结束该账号浏览、标记不可续场）、从落库草稿重建发布输入、驱动指令序列下发边缘真发、完成后解除让位经续场各闸起新浏览会话。让位窗口从「生成 + 15 分钟审批 + 发布」缩到「仅发布」（约数十秒）。
- **【BREAKING】下发**所发即审批卡上所审的那份草稿，**绝不在下发时重新生成**。接受陈旧性：草稿在生成时刻定稿，几小时后被批准也照发该草稿（所见即所发）；生成与下发之间人设/配置变化不回灌已定稿草稿。
- **【BREAKING】取消发布审批超时**：删除发布执行端内联的 `approvalWaitMs` 轮询等待与「期满落 `needs_review`」逻辑。草稿落库后停在「待审（`pending_approval`）」**无限期**，直到人审授权（→ 下发）或运营显式否决/撤稿（→ 终态）。**绝不**因超时自毁、**绝不**因超时改判、**更绝不**因超时自动发布（AC-PUB 不变）。
- **【BREAKING】并发语义收敛**：生成段单飞保持（避免 LLM 成本尖峰）；下发段**按账号单飞**且**每账号至多一份待下发草稿**（一份草稿未被处理前不再为该账号生成新草稿），杜绝草稿堆积与下发撞会话。
- **范围仅笔记发布**：评论生成快、走另一条路径、不触发发布让位，本 change **不改评论**。

## Capabilities

### Modified `publish-pipeline`

- **MODIFIED**「发布须与浏览会话互斥（让位），不计时也不被并发浏览撞页」：让位的边界从「整次 `trigger()`（含生成 + 候审）」收窄为「仅下发段（人审通过后的指令序列）」。生成与候审期间 **MUST NOT** 让位、浏览照常；下发期间仍 MUST 独占边缘、MUST NOT 有并发浏览撞页、所耗时间 MUST NOT 计入浏览会话；被忽略的触发仍 MUST NOT 动会话；最坏故障仍为诚实暂停而非撞页。
- **ADDED**「发布拆分为生成候审段与下发段，生成候审期间不让位浏览」。
- **ADDED**「审批通过即下发，下发从落库草稿重建、绝不重生成（通过即切 + 陈旧草稿如实照发）」。
- **ADDED**「取消发布审批超时：草稿待审无限期、绝不超时自毁或改判（AC-PUB 不变）」。
- **ADDED**「下发段按账号单飞且每账号至多一份待下发草稿」。

### 不修改的既有 capability

- `publish-submit-integrity`（AC-PUB / 成功判定 / 失败诚实）：红线不变，本 change 只让「下发」更晚发生、不放宽任何成功判定或授权判定。
- `session-auto-resume`（休息续场各闸）：机制不变，下发段结束后仍经同一各闸起新浏览会话；本 change 只改「何时触发让位/续场」，不改续场闸本身。
- 协议 v2 与边缘：**零改动**（边缘仍在人审通过后收到整条 `publish.command` 序列，与现状一致）。

## Impact

- **aidcp-cloud（唯一改动仓）**
  - 改 `src/publish-agent/publish-orchestrator.ts`：`trigger()` 的终止边界收于「草稿落库 + 审批卡已发」，不再内联等待人审；移除 `onPublishStart`/`onPublishEnd` 包裹（让位下放到下发段）；生成段超时回落到只覆盖生成（去掉为容纳 15 分钟审批而抬高的 `pipelineTimeoutMs`）。
  - 改 `src/publish-agent/roles/publish-executor.ts`：拆掉「内联 `waitForApproval` 轮询 + 期满 `needs_review` + 内联 `executePublishSequence`」；改为落库草稿（`status='pending_approval'`）+ 发审批卡后即返回；下发交由新的下发路径。
  - 新增「审批→下发」路径（如 `src/publish-agent/publish-dispatcher.ts`）：订阅人审授权信号到达，按账号单飞地：让位（`endSessionForAccount`）→ 从 `publish-log-store` 读回草稿重建 `PublishSequenceInput` → `CommandSequencer.executePublishSequence(approvedByUser:true)` → 回写 `published`/`failed` → 解除让位（`resumeSessionForAccount`）。下发时边缘离线则诚实 `failed`（复用现有 `resolveEdgeIdForAccount` 无节点判败红线）。
  - 改 `src/publish-agent/publish-log-store.ts`：补「读回待审/已批草稿 → 重建发布输入」（标题/正文/标签/图 URL/`publish_metadata`）；新增/复用 `pending_approval` 状态语义；提供「按账号查是否已有待下发草稿」。
  - 改 `src/feishu/ws-receiver.ts` 与 `src/panel/panel-server.ts` 的审批写入点：写授权信号后**触发**对应 `recordId` 的下发（事件驱动），取代发布执行端的内联轮询。
  - 改 `src/server.ts`：移除发布让位包裹 `trigger()` 的接线，改为接到下发段；装配下发路径与审批信号触发；移除 `AIDCP_PUBLISH_APPROVAL_WAIT_MS` / `roleTimeoutMs` 中为内联审批预留的部分（生成段超时回落）。
  - 单飞/堆积保护：下发段按账号串行；生成段在该账号已有待下发草稿时不再生成新草稿。

- **aidcp-edge**：无改动。
- **协议**：无改动（消息集与计数不变）。
- **DB（ECS PostgreSQL 库 `aidcp`）**：不新增表/列；复用 `publish_log` 既有列与 `status`。`status` 新增取值 `pending_approval`，需一处**幂等 CHECK 约束更新**（`DROP CONSTRAINT IF EXISTS` + 以新取值集合重建，随 `PUBLISH_SCHEMA_SQL` 在 `init()` 幂等执行，无需手工迁移）。
- **依赖与红线**：`AC-PUB-*`（未授权绝不静默发布）MUST 仍全过——下发只在 `approved === true` 时发生；`AC-PROTO-*` 不受影响（协议不动）；`AC-RISK-*` 不受影响。审批信号文件路径契约 `/tmp/aidcp-publish-approve-<requestId>.json` 两端不漂移。

- **与在途 publish 系列 change 的关系**
  - `publish-trigger-and-apply`（三扳机触发 + AC-PUB 双闸）是本 change 的上游底座：本 change 不改其触发与授权判定，只把「触发后到下发之间」的让位时机与审批等待方式重构。
  - 归档时本 change 的 `publish-pipeline` delta 与在途各 change 的 delta 依序并入同一 spec；本 change 的 requirement 名与既有/在途 requirement 名互不重叠（一条 MODIFIED 复用既有名以替换之）。
