# 视频号互动管理 v1 冻结合同

本目录是 OpenSpec change `wechat-channels-interaction-management` 的机器可验证合同，供 Session 01–04 并行实现。Session 00 不包含 Edge、Cloud、Console 或 Electron 业务代码，也不表示任何真实账号读写已经验证。

## 权威性与变更规则

1. 行为与不变量以 `openspec/changes/wechat-channels-interaction-management/` 为准。
2. 字段、枚举和 envelope 以 `schemas/*.schema.json` 为准。
3. 正常/降级样例以 `fixtures/` 为准。
4. 边云协议总览同步写入 `docs/protocol.md`；基础 inbox 的 7 个类型和本次新增的 6 个恢复/offboard 类型必须在 Edge、Cloud 同步上线，不能只按 schema 数量声称链路可用。
5. Session 01–04 不得在各自仓库发明字段别名、放宽枚举或改变状态语义。确需改合同，应先回到控制仓新开或更新 OpenSpec change，并重新生成 fixtures 与校验结果。

所有示例均为合成数据；时间统一为 epoch milliseconds；所有 ID 均为 opaque string；合同不得加入 Cookie、二维码、真实私信、真实账号身份或第三方原始错误体。

## 冻结文件

| 文件 | 冻结内容 |
| --- | --- |
| `schemas/common.schema.json` | 平台、渠道、状态、风险、错误 envelope、公共原子类型 |
| `schemas/domain.schema.json` | auth、thread、message、reply job、send attempt 与同步对象 |
| `schemas/ws-v2.schema.json` | 14 个 Interaction WS 消息及四段 capability 协商 payload |
| `schemas/customer-auth-api.schema.json` | 客户 InteractionWorkspace API 的请求/响应 |
| `schemas/internal-api.schema.json` | Console 配置、预览、发布、runtime controls 与审计 API |
| `schemas/ai-roles.schema.json` | classifier、polisher、risk reviewer 的严格输入/输出 |
| `schemas/walkthrough.schema.json` | comment 与 DM 合同走读结构 |

## 平台和能力

- 平台 ID：`wechat_channels`。
- 账号归属键：`envKey + accountId`；Cloud 的 `accounts.platform` 为平台校验事实源。
- 稳定能力名：`identity`、`overlay`、`auth.browser_sidecar`、`interaction.comment.read`、`interaction.comment.reply`、`interaction.dm.read`、`interaction.dm.send_text`、`interaction.dm.send_image`。
- v1 不支持 browse/like/collect/follow/publish/patrol；`interaction.dm.send_image` 始终 false。
- browser driver 只负责登录/挑战现场、身份和 sidecar 生命周期；interaction connector 负责增量读取、发送和回查。
- 浏览器 `closed` 可以与 auth `active` 同时成立，不得误报下线。
- 本地加密会话通过身份与已启用读取探针时必须保持 API-only，不得仅为启动环境而打开浏览器；只有会话失效或人工要求时才打开 sidecar。
- 重新授权启动 AdsPower profile 遇到确切占用签名时，Edge 报 `reauth_required + unavailable + INTERACTION_BROWSER_PROFILE_IN_USE`；合同和客户 API 不得携带原始占用者标识。释放占用后由用户显式重试，accepted 不等于已恢复。
- capability 必须同时满足 build support、feature flag、auth active、identity match 和 endpoint probe，任一不确定即 false。

## WS v2 冻结

现有 `{v,type,id,ts,payload}` envelope 不变；payload 不重复 `type`。基础 Interaction 合同的 7 个消息加上恢复/offboard 的 6 个消息、账号 runtime controls 1 个消息和浏览器前后台控制 1 个消息，使目标 MessageType 从 83 增至 91：

| type | 方向 | 关联语义 |
| --- | --- | --- |
| `wechat_channels.inbox.auth.status` | Edge → Cloud | 主动状态推送 |
| `wechat_channels.inbox.sync.batch` | Edge → Cloud | Cloud 用同 envelope `id` 回 ack |
| `wechat_channels.inbox.sync.ack` | Cloud → Edge | 整批 accepted/duplicate/rejected |
| `wechat_channels.inbox.reply.result` | Edge → Cloud | 回填 send 的 envelope `id` |
| `wechat_channels.inbox.reply.result.ack` | Cloud → Edge | 使用 result envelope `id`；仅 exact accepted/duplicate 可清 durable outbox |
| `wechat_channels.inbox.reply.reconcile` | Cloud → Edge | 启动/重连后仅核验既有 attempt，不得触发平台写 |
| `wechat_channels.inbox.reply.reconcile.result` | Edge → Cloud | 回填 reconcile envelope `id`，逐 attempt 报 result_replayed/not_found/binding_conflict |
| `wechat_channels.inbox.sync.request` | Cloud → Edge | 后续 batch 用 payload `requestId` 关联 |
| `wechat_channels.inbox.reply.send` | Cloud → Edge | Edge 回 reply.result |
| `wechat_channels.inbox.auth.reopen` | Cloud → Edge | Edge 后续以 auth.status 报阶段 |
| `wechat_channels.inbox.browser.control` | Cloud → Edge | active 会话的浏览器显隐控制；受理不等于已打开/关闭，Edge 后续以 auth.status.browserState 报真态 |
| `wechat_channels.inbox.runtime.controls` | Cloud → Edge | 仅向 scope 匹配且已协商能力的 Edge 下发版本化账号开关；enqueue 不等于应用 |
| `wechat_channels.inbox.offboard.command` | Cloud → Edge | scope-bound 撤权清理命令；先停同步/写并 drain，再删密文、关 sidecar |
| `wechat_channels.inbox.offboard.result` | Edge → Cloud | 可跨重启重放的 cleared/already_cleared/failed 结果 |
| `wechat_channels.inbox.offboard.ack` | Cloud → Edge | 使用 result envelope `id`；仅 exact accepted/duplicate 可清 durable outbox |

基础协商标识固定为 `interaction_inbox_v1`；结果恢复另用 `interaction_reply_recovery_v1`，offboard 另用 `interaction_offboarding_v1`，账号开关另用 `interaction_runtime_controls_v1`，浏览器前后台控制另用 `interaction_browser_control_v1`。Edge 在 optional `hello.capabilities` 声明，Cloud 只在双方支持时于 optional `welcome.capabilities` 回显。Cloud 回显 offboard capability 时必须同时给 account-bound `welcome.interactionRecovery.offboardPending`；Edge 仅在它明确为 false 时恢复 connector，缺失或 true 均 fail closed。回显 runtime-controls capability 时必须同时给 scope-bound `welcome.interactionRuntime`；缺失、畸形或错误 scope 时 Edge 的互动能力全关。恢复/offboard/runtime-controls/browser-control capability 依赖基础 inbox，未回显时不得发送对应扩展 type。旧 Cloud 仍可接收基础 `wechat_channels.inbox.reply.result`，但 Edge 不得把 fire-and-forget 当确认并清 outbox；旧 Edge 不支持 offboard 时 Cloud 必须先撤权停写并保留 pending cleanup，等待可用的新 Edge，不能提前 tombstone 或谎报清理完成。

同步是整批事务。只有 Cloud 持久化 batch/thread/message/cursor 成功后才能 ack `accepted`；已持久化批次回 `duplicate`；拒绝或部分失败回 `rejected`。Edge 只有在 `accepted|duplicate` 且 ack `cursorAfter` 与本批一致时推进本地 checkpoint。

回复结果先在 Edge durable outbox 落盘，再发送 `wechat_channels.inbox.reply.result`。Cloud 在同一事务完成 attempt/job CAS 后返回 scope、attempt、idempotency identity 全匹配的 ack；Edge 只在 `accepted|duplicate` 且全部绑定字段一致时清除。超时、断线、Cloud 崩溃、rejected 或错绑 ack 均保留并在重连后补发。Cloud 启动和 Edge 重连时对 `created|dispatched|ambiguous` 发 reconcile；Edge 只能检查 durable execution/result 和平台历史，绝不能因本地缺失而重新调用平台写。`created + not_found` 可明确 failed；`dispatched|ambiguous + not_found` 保持 ambiguous；`result_replayed` 由正常 durable result 再推进终态。

offboard 顺序固定为：Cloud 事务撤销 customer scope 与读写能力 → 创建 durable offboard → Edge durable claim → connector stop 并 drain 在途同步/写 → 删除 scope-bound encrypted session → 关闭 sidecar → durable result/outbox → Cloud exact ack → Cloud tombstone → 最迟 requestedAt 后 30 天内 purge。`failed` 结果回到 pending 并重试；Edge 离线不改变顺序。普通 pause/close/standby/logout 不得映射成 offboard 或删除密文。审计只允许 offboardId、envKey、accountId、userId、event、status、timestamp，不得记录消息正文、回复/模板最终文本或凭证。

## 数据与幂等不变量

| 数据 | 不变量 |
| --- | --- |
| thread | `UNIQUE(platform, account_id, channel, external_thread_id)`，并保存/校验 env 归属 |
| message | 非空外部 ID 上 `UNIQUE(platform, account_id, channel, direction, external_message_id)`；正文不参与去重 |
| sync batch | `UNIQUE(platform, account_id, batch_id)` |
| sync cursor | `UNIQUE(platform, account_id, channel, scope_external_id)`；只随 accepted batch 事务推进 |
| reply job | `UNIQUE(inbound_message_id)`；CAS version 单调增加 |
| send attempt | `UNIQUE(idempotency_key)` 与 `UNIQUE(reply_job_id, attempt_no)`；同 job 最多一个 active/ambiguous attempt |
| result outbox | Edge durable；exact accepted/duplicate ack 前不可删除；reconnect/startup 必须重放 |
| offboard | 每个 `(platform,envKey)` 最多一个非 purged 任务；结果/ack exact scope，Cloud ack 后才 tombstone |
| runtime controls | `UNIQUE(platform, account_id)`；与不可变 reply config 分离 |
| config version | `UNIQUE(platform, account_id, config_version)`；published 后不可变 |

精确幂等键：

```text
sha256(platform | accountId | inboundMessageId | replyJobId | finalTextSha256)
```

字段按 UTF-8 原值与字面量 `|` 拼接；两个 SHA-256 都输出小写 hex。Cloud 与 Edge 必须持久保存和复用同一个键。

## 状态机红线

Reply job 主路径：

```text
new -> classifying -> draft_ready | approval_required | queued | failed
approval_required -> approved -> queued -> sending -> sent | failed | ambiguous
```

- `approve` 只做 `approval_required -> approved`；`send` 只做 `approved -> queued`。
- `draft_ready` 是不可发送草稿；`ignored`、`escalated`、`sent` 为当前 message 终态。
- `failed` 仅表示明确未发送；必须经显式 CAS 操作才可重新 queued。
- `ambiguous` 只能由回查转 `sent|failed`，不得超时清除或自动重投。

Send attempt：

```text
created -> dispatched -> confirmed | failed | ambiguous
ambiguous -> confirmed | failed
```

job 只有在 attempt `confirmed` 后才能变为 `sent` 并由 Cloud `RiskController.record` 计成功。网络超时、断连或响应无法解析必须是 `ambiguous`。

## HTTP、权限与配置

本能力的新端点统一成功体 `{data,meta:{requestId,asOf}}` 和安全错误体 `{error:{code,message,requestId,retryable,details?}}`。列表 cursor 是 server-signed opaque base64url；排序固定 `lastMessageAt DESC, id DESC`，默认 limit 30、最大 100。跨 env 资源与不存在资源返回相同 404。

Customer API：

```text
GET  /environments/:envKey/interactions
GET  /environments/:envKey/interactions/:threadId
PUT  /environments/:envKey/replies/:jobId/draft
POST /environments/:envKey/replies/:jobId/approve
POST /environments/:envKey/replies/:jobId/send
POST /environments/:envKey/replies/:jobId/regenerate
POST /environments/:envKey/interactions/:messageId/ignore
POST /environments/:envKey/interactions/:messageId/escalate
POST /environments/:envKey/interactions/sync
POST /environments/:envKey/interactions/auth/reopen
POST /environments/:envKey/interactions/browser
DELETE /environments/:envKey
GET  /offboarding/:offboardId
```

`DELETE /environments/:envKey` 仅对 enabled user 的权威 scope 生效，事务内同时验证 interaction account binding；返回 offboard 状态而非“已删除”。客户不得通过 `POST /environments` 自声明归属。`GET /offboarding/:offboardId` 只允许创建该任务的客户查看，响应继续包含 `envKey/accountId/meta.asOf`。

所有 job/message 写入带 `expectedVersion`；send/sync/reopen/browser-control 还要求 `Idempotency-Key`。浏览器控制 body 仅接受 `{action:"open"|"close"}`；只允许 active 且 scope 匹配的会话执行。HTTP 2xx 只表示动作受理，UI 必须展示读回的 job state 或 `auth.browserState`，不得把 accepted 当成浏览器已显隐。

Internal API：

```text
GET|PUT    /api/accounts/:accountId/interaction-runtime-controls
GET|PUT    /api/accounts/:accountId/interaction-reply-policy
GET|POST   /api/accounts/:accountId/reply-templates
PUT|DELETE /api/accounts/:accountId/reply-templates/:templateId
GET|POST   /api/accounts/:accountId/reply-rules
PUT|DELETE /api/accounts/:accountId/reply-rules/:ruleId
GET|PUT    /api/accounts/:accountId/reply-profile
GET        /api/accounts/:accountId/reply-preview-contexts?channel=<comment|dm>&limit=<1..50>
POST       /api/accounts/:accountId/reply-preview
POST       /api/accounts/:accountId/reply-config/publish
GET        /api/accounts/:accountId/reply-config/audit
```

权限固定为 `interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full`、`interaction.audit.view`，缺 grant fail closed。

模板变量只允许 `{{user_name}}`、`{{video_title}}`、`{{account_name}}`、`{{support_channel}}`；只做字面替换。规则排序 `priority ASC, ruleId ASC`。运行 controls 与 draft/published config 分离，published snapshot 不可变。comment/dm profile 可带 nullable `knowledgeDocument`（Markdown/纯文本、≤20,000 字符），随 group/default scope 版本发布；旧 profile 缺字段按 null。`reply-preview-contexts` 仅返回账号当前权威环境内最近的入站预览字段，不触发同步、建 job 或发送；DM 正文额外要求 `interaction.dm.view_full`。

## AI 与发送门禁

LLM role 只有 `reply_intent_classifier`、`reply_polisher`、`reply_risk_reviewer`；template renderer 是确定性程序。classifier/reviewer 失败都降级 unknown + 人工；polisher 失败回落原模板并强制人工。polisher 仅在实际启用时接收命中渠道的 `knowledgeDocument`，并只能用文档明确支持的业务事实回答；文档被视为不可信数据，内部命令不得覆盖系统规则，缺答案必须诚实说明无法确认。模型自报的 `meaningChanged`、`introducedClaims`、`riskLevel` 与 `allowAutoSend` 都不是安全事实源：候选文本必须再过确定性 profile/claim gate，至少硬拦价格、折扣、促销、退款、订单、售后承诺和补偿承诺。

规则级 `actions.allowAutoSend` 对模板原文和 AI 回复使用相同的“人工审核 / 自动回复”语义。AI 风格润色只有在全部角色调用成功、候选通过确定性检查、reviewer 为 low 且建议自动、没有改义或新增事实时才能自动；普通知识问答允许记录 `meaning_changed`/`introduced_claim` 审计标签，但必须同时具备当前渠道知识文档、普通问题、完整 introducedClaims 和仅流程标签的低风险结果。无文档新增事实、无审计事实的改义、unknown、模型 fallback、候选拒绝、规则实际命中的 `forceHumanTags` 或任何实质 hard-risk 都强制人工。生成准入和真实派发前分别复核；派发仍要求账号 allowlist、runtime controls、active identity/capability、登录冷却、RiskController、专用限速、CAS、幂等和结果核验。DM AI 默认 false。

任何发送都必须通过 scope、auth、identity、capability、全局/账号/channel 开关、published config、CAS、无 active/ambiguous attempt、文本/变量、消息类型、账号单飞、限速与 `RiskController.canDo`。评论沿用 `comment` action；私信新增 `dm_reply`，三窗口 fallback quota 均为 0。所有写开关默认 false；`auto_safe` 默认 false。

## Schema 校验

使用支持 JSON Schema draft 2020-12 和相对 `$ref` 的校验器。在 `schemas/` 目录运行：

```bash
check-jsonschema --check-metaschema *.schema.json
check-jsonschema --schemafile ws-v2.schema.json ../fixtures/ws/*.json
check-jsonschema --schemafile customer-auth-api.schema.json ../fixtures/customer-api/*.json
check-jsonschema --schemafile internal-api.schema.json ../fixtures/internal-api/*.json
check-jsonschema --schemafile ai-roles.schema.json ../fixtures/ai/*.json
check-jsonschema --schemafile walkthrough.schema.json ../fixtures/walkthroughs/*.json
```

## Session 01–04 统一 handoff

| Session | 必须消费 | 不得改变 | 独立阻断 |
| --- | --- | --- | --- |
| 01 Edge | platform/capability、WS schemas、auth/sync/send fixtures、幂等键与 ambiguous 语义 | 不把私有接口当官方稳定 API；不在 ack 前推进 cursor；不假成功 | OQ-02 阻断对应真实 capability；OQ-05 阻断真实写验收 |
| 02 Cloud | 全部数据键、两状态机、customer/internal API、risk action、retention | 不复用 outbound `interaction_feed`；不让非 RiskController 写最终风险态；不自动重投 ambiguous | migration 编号在实现时从最新主线分配；OQ-03 阻断 ol 正文 |
| 03 Console | internal API schema/fixtures、权限、配置快照、preview/publish | 不绕过 permissions；不让 preview 建 job/send attempt；不把 draft 当 published | OQ-04 阻断普通角色看 DM 原文与 DM AI |
| 04 Electron | customer API schema/fixtures、auth/browserState、CAS、可读状态 | 不直接 fetch 任意 URL；不把 accepted/queued 当 sent；环境切换不串响应 | OQ-05 只阻断真实发送；可按 fixtures 完成 UI |

Session 01/02 接协议时必须原子同步 Edge/Cloud `PlatformId`、`MessageType`、payload types、Cloud command mapping、Edge active-command routing 和 `docs/protocol.md`。仅 typecheck 不足以证明路由完整。Session 03/04 只按 schema 和 fixtures 开发，不应复制各自版本的 DTO。

## 合同走读

- `fixtures/walkthroughs/comment-confirmed-flow.json`：从 capability 协商、整批同步、AI、人工审批到 `confirmed`，证明只有确认后才 `sent`。
- `fixtures/walkthroughs/dm-ambiguous-flow.json`：发送派发后无法确认，证明结果停在 `ambiguous`、UI 显示待核验、系统不自动重试。

走读只验证合同闭环，不代表对真实账号执行过写操作。

## 未解决问题与阻断范围

| ID | Owner | 保守默认 | 阻断范围 |
| --- | --- | --- | --- |
| OQ-01 私有接口/平台条款授权 | 产品 + 法务/平台合规 | 全能力账号 flag 和写总开关 off | ol、真实客户数据、任何自动写 |
| OQ-02 真实分页/删除/ID/回查字段 | Session 01 + 测试账号 owner | schema mismatch 即熔断能力 | 对应真实读/写 capability |
| OQ-03 180/90/365 天保留与 30 天 purge | 数据 owner + 合规 | 按保守默认实现 | ol 保存真实正文 |
| OQ-04 DM 原文角色与 AI 供应商 | 安全/合规 + Console owner | 专门权限；DM AI=false | DM AI、普通排障原文 |
| OQ-05 真机账号和可删除写目标 | 业务 owner | 只读/gated，不声明成功 | Session 05 真实写验收 |
| OQ-06 production auto_safe 名单 | 产品/风控 | 全局和账号 off | 自动发送 |
| OQ-07 图片 DM 限制 | Session 01 + 业务 owner | `dmSendImage=false` | 图片发送 |
| OQ-08 外部工单/通知 | 产品 | 仅状态、审计、队列 | 外部工单集成 |

Cloud migration 的数字 ID 不在本合同冻结，因为它会随 Session 02 开工时默认分支上的并行 migration 变化；Session 02 必须在最新 `master` 上分配下一个可用 ID。这不阻断 schema、mock、API 或状态机实现。
