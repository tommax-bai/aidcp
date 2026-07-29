## ADDED Requirements

### Requirement: 入站互动域必须与 outbound interaction feed 分离

Cloud SHALL 建立独立的 thread、message、sync batch/cursor、reply job、send attempt 和 audit 持久化域。外部用户发来的评论/私信、处理状态和回复 attempt MUST NOT 写入只记录 aidcp 主动动作的 `interaction_feed`，也 MUST NOT 从 Edge 日志字符串推导业务状态。

#### Scenario: 入站评论不污染主动互动记录
- **WHEN** Cloud 接收一条视频号用户评论
- **THEN** 该评论进入 inbound tables 并创建相应 job，现有 outbound `interaction_feed` 不新增一条伪主动评论

#### Scenario: 业务状态只来自结构化事实
- **WHEN** Edge 普通日志出现“发送成功”字样但没有结构化 confirmed result
- **THEN** Cloud job MUST NOT 进入 sent，UI MUST NOT 展示成功

### Requirement: 数据唯一键和 account/env scope 不得削弱

Cloud MUST 实施以下唯一性：thread `(platform,account_id,channel,external_thread_id)`；非空 external message `(platform,account_id,channel,direction,external_message_id)`；batch `(platform,account_id,batch_id)`；cursor `(platform,account_id,channel,scope_external_id)`；job `inbound_message_id`；attempt `idempotency_key` 与 `(reply_job_id,attempt_no)`。所有读写 MUST 同时带 `account_id` 与 `env_key` 并验证归属，正文 MUST NOT 参与去重。

#### Scenario: 同文案的两条消息保持独立
- **WHEN** 同一用户先后发送两条文本相同但 external message ID 不同的私信
- **THEN** Cloud 保存两条消息并各自按规则创建 job，MUST NOT 因文本相同去重

#### Scenario: 跨环境 ID 不可读取
- **WHEN** 客户 A 用其 env 查询实际属于客户 B/env B 的 thread ID
- **THEN** 服务端返回与不存在一致的 404，MUST NOT 泄漏资源存在或内容

### Requirement: 同步批次必须事务幂等并保存 unknown/tombstone

Cloud SHALL 在单事务内验证 scope、幂等写 batch/thread/message、创建唯一 job、更新 cursor 候选和审计；全部成功后才 ack。未知消息类型 SHALL 保存为 `unknown` 占位且禁止自动发送；平台删除/隐藏 SHALL 保存 tombstone，不硬删除历史审计。

#### Scenario: 未知 DM 不丢整个会话
- **WHEN** 一个 DM batch 含 image 与未识别 message type
- **THEN** 已知项正常入库，未知项作为 `unknown` 保存并进入人工可见状态，MUST NOT 丢弃整条 thread

#### Scenario: 删除评论保留历史事实
- **WHEN** 后续 sync 发现先前评论被删除或隐藏
- **THEN** message 更新 lifecycle tombstone，相关 job/attempt/audit 保留且 UI 如实显示不可再发送

### Requirement: Reply job 状态转换必须以 CAS 守卫

Job 状态 SHALL 为 `new|classifying|draft_ready|approval_required|approved|queued|sending|sent|failed|ambiguous|ignored|escalated` 并维护单调 `version`。`approve` 只允许 `approval_required→approved`，`send` 只允许 `approved→queued`；`draft_ready` 属 draft-only 不可发送。任何写动作 MUST 提交 `expectedVersion`，冲突 MUST 返回当前版本/状态且不部分写。

#### Scenario: 两个客户端不能重复批准
- **WHEN** 两个客户端以同一 expectedVersion 同时批准一个 job
- **THEN** 只有一个 CAS 成功，另一个返回 `INTERACTION_VERSION_CONFLICT` 和当前真态

#### Scenario: draft-only 草稿不能直接发送
- **WHEN** policy mode 为 `draft_only` 且 job 为 `draft_ready`
- **THEN** send 返回 `INTERACTION_APPROVAL_REQUIRED|INTERACTION_STATE_CONFLICT`，MUST NOT 创建 attempt

#### Scenario: 忽略只终止当前 message
- **WHEN** 用户忽略当前 inbound message 后同 thread 到达新 inbound message
- **THEN** 旧 job 保持 ignored，新 message 获得新的唯一 job 并重新进入队列

### Requirement: Send attempt 与 ambiguous 必须可恢复且不盲重试

Attempt 状态 SHALL 为 `created|dispatched|confirmed|failed|ambiguous`，ambiguous 只可经平台验证转 confirmed/failed。一个 job 同时最多一个 active/ambiguous attempt。Job 只有 confirmed 才进入 sent；failed 只有在明确未发送且错误可重试时，才能经显式 CAS 创建下一个 attempt。

#### Scenario: ambiguous 阻止第二次发送
- **WHEN** job 当前 attempt 为 ambiguous
- **THEN** 任何自动/人工 send 请求返回 `INTERACTION_SEND_AMBIGUOUS`，直到回查把 attempt 收敛

#### Scenario: 重启后继续回查同一 attempt
- **WHEN** Cloud 在 attempt ambiguous 后重启
- **THEN** 启动恢复读取原 attempt/idempotencyKey 并继续验证，MUST NOT 新建 attempt 或重发

#### Scenario: 账号队列不被旧 ambiguous 永久卡死
- **WHEN** 旧 job 保持 ambiguous 但同账号后续独立 message 已人工批准
- **THEN** 旧 job 仍禁止第二 attempt，账号级 active serialization 只覆盖 created/dispatched，后续 job MAY 排队发送且不得重投旧平台写

### Requirement: API 分页、envelope 与错误码必须稳定

本能力的新 HTTP API SHALL 使用成功 `{data,meta:{requestId,asOf}}` 与错误 `{error:{code,message,requestId,retryable,details?}}` envelope；`asOf` 为 epoch ms。列表 cursor MUST 为 opaque/signed base64url，固定 `asOf` 并按 `lastMessageAt DESC,id DESC` 排序；默认 limit=30、最大 100。第三方原始错误/响应 MUST NOT 出现在 error body。

#### Scenario: 翻页期间新消息不造成重复跳页
- **WHEN** 客户按 nextCursor 请求第二页且此时有新消息到达
- **THEN** 服务端使用 cursor 内固定 asOf 继续原快照，第二页不因新消息重复/漏掉原快照记录

#### Scenario: 平台拒绝只返回稳定错误
- **WHEN** 平台返回未文档化的拒绝正文
- **THEN** API 只返回映射后的稳定 code、安全 message 与 requestId，MUST NOT 回传第三方全文

### Requirement: 内容保留与删除必须按敏感度执行

默认保留评论正文 180 天、DM 正文 90 天、无正文审计元数据 365 天。账号解绑、用户删除或客户终止时 SHALL 立即撤权/停同步，Edge 立即清除会话密文，Cloud MUST 在 30 天内 purge 对应正文与业务记录；依法保留的审计不得含正文。普通日志 MUST 只记录 ID 摘要、长度、类型和状态。

#### Scenario: DM 到期不残留在普通表或日志
- **WHEN** 一条 DM 正文超过 90 天且没有合法 hold
- **THEN** Cloud 清除正文/附件敏感元数据，审计只保留允许的无正文事实，普通日志无可恢复原文

#### Scenario: 解绑立即阻断访问与发送
- **WHEN** 一个环境被客户解绑
- **THEN** 同一事务撤销 scope、停止同步/写并创建 durable offboard；下次 API 请求即不可访问，Cloud 仅在 exact Edge cleared/already_cleared ack 后 tombstone，并在 requestedAt 后 30 天内 purge

#### Scenario: 客户终止覆盖所有权威环境
- **WHEN** enabled 客户被内部管理员终止
- **THEN** Cloud 锁定该客户及其全部权威视频号 binding，为每个环境创建 customer_terminated offboard 后再禁用用户；任一缺失 account binding 时事务 fail closed，不得部分终止

#### Scenario: offboard 审计不含正文或凭证
- **WHEN** access revoke、Edge cleanup failed/cleared、Cloud tombstone 或 purge 被审计
- **THEN** 事件只包含必要 scope ID、actor/user、event、status、时间，MUST NOT 包含 message content、final/template text、Cookie/session 或第三方原始响应
