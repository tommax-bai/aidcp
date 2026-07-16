## Context

`aidcp` 当前的浏览闭环、`comment-interaction` 与 `interaction_feed` 都描述 aidcp 主动执行的页面动作；它们没有“外部用户发来一条消息”的唯一键、处理队列、审批、发送 attempt、ambiguous 回查或客户数据保留语义。视频号候选能力又来自创作者助手私有接口，不能把浏览器、Cloud 或第三方 SDK 当作稳定凭证/接口事实源。

本设计服务五个后续仓库工作面：Edge 平台与 connector、Cloud 入站互动域和 API、Console 配置、Electron 互动 workspace、最终集成验收。Session 00 只在控制仓冻结契约；运行时代码、migration、部署与真实写测试由 Session 01–05 完成。

当前实现约束：

- Edge/Cloud `PlatformId` 只有 `xiaohongshu | facebook`；Edge `PlatformDriver` 偏浏览器能力，Cloud registry 偏逐帖编排能力。
- WS v2 当前为 `{v,type,id,ts,payload}`，两端各 76 个 `MessageType`；Edge 主动命令存在 typecheck 抓不到的 active-command 白名单。
- customer-auth 使用独立 JWT/端口并在每次请求回库复核 enabled user；internal panel API 使用另一 JWT 域，现有响应没有统一 envelope。
- Cloud `RiskController` 是账号最终风险态单写者；成功计数必须挂平台确认后的真实回执。
- 客户端基线是全局标题栏 + 左侧环境栏 + 当前环境右侧 workspace，`820×720` 为基准窗口。

## Goals / Non-Goals

**Goals:**

- 给 Session 01–04 一份相同的、机器可验证的 v1 contract，精确到消息类型、字段、枚举、API 路径、状态转换、唯一键、错误码和权限。
- 保证同步批次、消息、回复 job 和发送 attempt 跨重启幂等；`sent` 只来自平台 ack 或回查确认。
- 让浏览器在会话有效后正常关闭，凭证永不离开所属 Edge；身份错配、挑战、schema 漂移一律 fail closed。
- 把模板确定语义、AI 受限润色、风险复核和人工/自动门禁分层，AI 失败不产空文本、不改变事实、不伪造发送。
- 用 capability negotiation 和默认关闭的写开关支持新旧版本偏斜与逐级开放。

**Non-Goals:**

- 不实现或复制第三方私有接口代码，不把端点描述成微信官方稳定 API。
- 不在 Session 00 创建 Cloud migration、Edge/Cloud TypeScript、Console/renderer 业务代码或部署配置。
- 不开放视频发布、直播、电商订单、外部工单或图片私信发送。
- 不在 renderer、Cloud、fixture、日志或文档保存真实 Cookie、二维码、私信原文或真实客户身份。
- 不改变现有 XHS/Facebook 主动评论、发布、浏览、风险状态机语义。

## Decisions

### 1. 平台与运行时分成 browser driver 和 interaction connector

精确平台 ID 为 `wechat_channels`。每个视频号账号仍对应一个 `envKey + accountId` 环境，`accounts.platform` 与 Edge 环境平台标注必须一致。Edge 新增与 browser-oriented `PlatformDriver` 并列的 `InteractionConnector`；browser driver 只负责打开登录/挑战现场、读取身份和管理 sidecar 生命周期，connector 负责接口探针、增量读取、发送和回查。

能力使用稳定标识：`identity`、`overlay`、`auth.browser_sidecar`、`interaction.comment.read`、`interaction.comment.reply`、`interaction.dm.read`、`interaction.dm.send_text`、`interaction.dm.send_image`。browse/like/collect/follow/publish/patrol 在本版本显式 unsupported。`interaction.auth.status.capabilities` 中的布尔值表达“此账号此刻有效可用”，不是“代码里可能实现”；必须同时满足 build support、feature flag、active auth、identity match 与端点 probe。

所有私有接口能力初始 fail closed；写总开关、账号写开关、评论写和私信写均默认 false。`dmSendImage` 在 v1 恒 false。读取可在受控 dev 账号完成 schema probe 后按账号开启。

备选方案是把所有方法继续塞入 `PlatformDriver`。它会迫使视频号伪装 browse/publish 能力，也会让“浏览器关闭但 connector 正常”难以表达，因此拒绝。

### 2. WS 保持 v2 envelope，冻结 13 个 Interaction 消息类型

基础 inbox 的 7 个消息已使目标 `MessageType` 从 76 增至 83；result recovery 与 offboarding 再增加 6 个，使当前目标总数为 89。payload 不重复携带 `type`，时间字段统一为 epoch milliseconds `number`，不在消息体再建协议版本。精确类型：

| type | 方向 | 关联 |
| --- | --- | --- |
| `interaction.auth.status` | Edge → Cloud | 状态推送 |
| `interaction.sync.batch` | Edge → Cloud | Cloud 以同 envelope `id` 回 `interaction.sync.ack` |
| `interaction.sync.ack` | Cloud → Edge | 确认整批持久化/重复/拒绝 |
| `interaction.reply.result` | Edge → Cloud | recovery 协商后 Cloud 以同 envelope `id` 回 ack |
| `interaction.reply.result.ack` | Cloud → Edge | exact accepted/duplicate 后清 Edge result outbox |
| `interaction.reply.reconcile` | Cloud → Edge | 仅核验既有 attempt，不得写平台 |
| `interaction.reply.reconcile.result` | Edge → Cloud | 回填 reconcile envelope `id` |
| `interaction.sync.request` | Cloud → Edge | 后续 batch 用 payload `requestId` 关联 |
| `interaction.reply.send` | Cloud → Edge | Edge 回 `interaction.reply.result` |
| `interaction.auth.reopen` | Cloud → Edge | Edge 后续用 auth.status 报阶段 |
| `interaction.offboard.command` | Cloud → Edge | 撤权后 scope-bound 清理凭证 |
| `interaction.offboard.result` | Edge → Cloud | durable 清理结果，可重连补发 |
| `interaction.offboard.ack` | Cloud → Edge | exact accepted/duplicate 后清 Edge offboard outbox |

工作包的“五类”与候选六个 type 不一致，且没有 ack 就无法诚实推进 checkpoint；因此新增 `interaction.sync.ack` 并冻结七个 type。拒绝复用 `action.completed`，因为它是页面动作回执，没有批次事务和 cursor 语义。

兼容性通过现有握手的 optional 字段完成：基础能力为 `interaction_inbox_v1`，结果恢复和 offboarding 分别为 `interaction_reply_recovery_v1`、`interaction_offboarding_v1`，且两者依赖基础能力。新 Cloud 只回显双方都声明的 capability；回显 offboarding 时必须事务性/权威读取 account pending 状态并附 `welcome.interactionRecovery.offboardPending`，Edge 只有明确 false 才恢复 connector，缺失或查询失败均 fail closed。旧 Cloud 可继续消费基础 result，但没有 exact ack 时新 Edge 保留 durable outbox；旧 Edge 无 offboard capability 时新 Cloud 先撤权停写并保留 pending cleanup，不提前 tombstone。未知 type 仍按现有策略忽略或返回 `unsupported_type`，连接不得崩溃或重试风暴。

### 3. 同步采用整批事务 + 显式 ack + Cloud 权威 cursor

评论 thread 以顶级评论为 `externalThreadId`，`sourceExternalId` 为视频 ID；私信 thread 以平台会话 ID 为 `externalThreadId`。一个 batch 只含一个 account/env/channel/scope，thread/message 均带稳定平台 ID。未知消息类型保存为 `unknown`；删除/隐藏以 tombstone 表达，不硬删。

Cloud 在单事务中校验 scope、幂等写 batch/thread/message、更新 cursor 候选并写审计；全部成功才返回 `accepted`，已处理 batch 返回同口径 `duplicate`。Edge 只在 ack 为 `accepted|duplicate`、且 ack 的 `cursorAfter` 与本批一致时提交本地 checkpoint。`rejected`、连接中断或部分失败均不推进。

### 4. Cloud 新建独立入站数据域

权威表/唯一键冻结如下；实现可增加 surrogate key、时间戳和必要索引，但不得削弱键或把内容塞进 outbound `interaction_feed`：

| 表 | 关键唯一性 / 不变量 |
| --- | --- |
| `interaction_threads` | `UNIQUE(platform, account_id, channel, external_thread_id)`；每行同时保存 `env_key` 并校验归属 |
| `interaction_messages` | 非空外部 ID 上 `UNIQUE(platform, account_id, channel, direction, external_message_id)`；正文不得参与去重 |
| `interaction_sync_batches` | `UNIQUE(platform, account_id, batch_id)`；保存 scope/cursor/ack 真态 |
| `interaction_sync_cursors` | `UNIQUE(platform, account_id, channel, scope_external_id)`；只随 accepted batch 事务推进 |
| `interaction_reply_jobs` | `UNIQUE(inbound_message_id)`；一个 inbound message 最多一个 job；含单调 `version` CAS |
| `interaction_send_attempts` | `UNIQUE(idempotency_key)`、`UNIQUE(reply_job_id, attempt_no)`；每 job 最多一个 `created|dispatched|ambiguous` attempt |
| `interaction_audit_events` | append-only；不保存 Cookie、二维码、完整私信或普通日志禁止的文本 |
| `interaction_runtime_controls` | `UNIQUE(platform, account_id)`；读/写/kill switch 与版本化回复配置分离 |
| `interaction_reply_configs` | `UNIQUE(platform, account_id)`；保存 draft/published 指针与 CAS version |
| `interaction_reply_config_versions` | `UNIQUE(platform, account_id, config_version)`；published 后不可变 |
| `reply_templates` | 模板逻辑 ID + template version 在账号/channel/config version 内唯一；历史引用不可覆盖 |
| `reply_rules` | rule ID 在 config version 内唯一；同优先级同条件不同模板禁止发布 |
| `account_reply_profiles` | `UNIQUE(platform, account_id, channel, config_version)` |
| `interaction_offboards` | 每个 `(platform,env_key)` 最多一个非 purged 任务；Cloud exact ack 后才 tombstone |
| `interaction_offboard_audit` | body-free append-only 事件，不含消息、回复、模板文本或凭证 |

幂等键精确为 `sha256(platform | accountId | inboundMessageId | replyJobId | finalTextSha256)`；字段以 UTF-8 原值和字面量 `|` 拼接，`finalTextSha256` 为最终文本 UTF-8 的小写 hex SHA-256。Cloud 和 Edge 都必须持久保存并复用该键。

### 5. 回复 job 与 send attempt 使用两个状态机

Job 状态：`new → classifying → draft_ready | approval_required | queued | failed`；`approval_required → approved`；`approved → queued`；`queued → sending`；`sending → sent | failed | ambiguous`。`draft_ready` 是 `draft_only` 模式的不可发送草稿；`ignored`、`escalated`、`sent` 为该 message 的终态。`failed` 仅在错误明确未发送且可重试时，经显式 CAS 动作回 `queued`。`ambiguous` 只能经平台回查转 `sent` 或 `failed`；不能直接重发。

编辑或重新生成从 `approval_required` 回到 `approval_required` 并增加 version、重新执行确定性门禁与 risk reviewer。`approve` 只做 `approval_required → approved`，`send` 只做 `approved → queued`，避免“已批准”和“已进入发送队列”混为一个事实。后续新 inbound message 建新 job；忽略只终止当前 message，不永久关闭 thread。

Attempt 状态：`created → dispatched → confirmed | failed | ambiguous`，`ambiguous → confirmed | failed` 只允许验证器推进。Job 只有 attempt `confirmed` 才写 `sent`。网络超时、连接中断、响应无法解析一律 ambiguous，不能按失败自动重投。

Edge 在平台执行结果返回后先把 result 写入 durable outbox，再发 Cloud；Cloud 事务推进 attempt/job 后回 exact `accepted|duplicate|rejected` ack。Edge 仅在 job/attempt/idempotency/env/account/platform 全匹配且 ack 为 accepted/duplicate 时清 outbox，断线、超时、Cloud 崩溃和 rejected 均跨重启补发。Cloud 启动和 Edge 重连时只发 reconcile：Edge 对已有 durable execution/result 做验证或结果重放，绝不得因本地缺失而新调用平台写。`created+not_found` 可明确失败；`dispatched|ambiguous+not_found` 保持 ambiguous；账号级串行可释放，但同 job ambiguous 仍阻断新 attempt。

### 6. API 使用新端点统一 envelope、opaque cursor 与 CAS

新 customer-auth/internal 端点统一成功体 `{data,meta:{requestId,asOf}}`；`asOf` 为 epoch ms。错误体为 `{error:{code,message,requestId,retryable,details?}}`，message 是安全用户文案，绝不回传第三方原始响应。HTTP 映射：401 token、403 permission、404 不存在或跨 env 不可枚举、409 state/version/ambiguous、422 validation/config、429 rate、503 feature/schema/upstream unavailable。

列表 cursor 为 server-signed/opaque base64url，固定快照 `asOf`，排序 `lastMessageAt DESC, id DESC`；默认 limit 30、最大 100。跨 env 的 thread/job 即使存在也返回与不存在相同的 404。

Customer API 路径：

- `GET /environments/:envKey/interactions`
- `GET /environments/:envKey/interactions/:threadId`
- `PUT /environments/:envKey/replies/:jobId/draft`
- `POST /environments/:envKey/replies/:jobId/approve`
- `POST /environments/:envKey/replies/:jobId/send`
- `POST /environments/:envKey/replies/:jobId/regenerate`
- `POST /environments/:envKey/interactions/:messageId/ignore`
- `POST /environments/:envKey/interactions/:messageId/escalate`
- `POST /environments/:envKey/interactions/sync`
- `POST /environments/:envKey/interactions/auth/reopen`
- `DELETE /environments/:envKey`
- `GET /offboarding/:offboardId`

所有写 body 带 `expectedVersion`（sync/reopen 无 job version），send/sync/reopen 还必须带 `Idempotency-Key` header。send API 的成功只表示进入 `queued|sending|sent` 真态，UI 必须读回 job state，不能把 HTTP 2xx 当平台已发送。

客户不得通过 `POST /environments` 或任何 customer-auth 输入自声明 `envKey` 归属。归属来自内部权威环境注册/管理员授予，并对 active env 全局唯一（明确共享授权模型上线前不共享）。每个 customer interaction endpoint 必须在同一事务锁定 enabled user、权威 env ownership 与 interaction account binding；跨 scope 与不存在统一不可枚举。DELETE 只创建/返回 offboard 真态，不表示凭证或 Cloud 数据已清完；GET 只允许原客户查看自己的任务并回 `envKey/accountId/meta.asOf`。

Internal API 路径冻结为工作包候选路径，另加运行时控制与审计：

- `GET|PUT /api/accounts/:accountId/interaction-runtime-controls`
- `GET|PUT /api/accounts/:accountId/interaction-reply-policy`
- `GET|POST /api/accounts/:accountId/reply-templates`
- `PUT|DELETE /api/accounts/:accountId/reply-templates/:templateId`
- `GET|POST /api/accounts/:accountId/reply-rules`
- `PUT|DELETE /api/accounts/:accountId/reply-rules/:ruleId`
- `GET|PUT /api/accounts/:accountId/reply-profile`
- `POST /api/accounts/:accountId/reply-preview`
- `POST /api/accounts/:accountId/reply-config/publish`
- `GET /api/accounts/:accountId/reply-config/audit`

权限名：`interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full`、`interaction.audit.view`。现有 panel 用户必须映射显式 grants；缺 grant fail closed。customer-auth 继续以 enabled user + env ownership 为边界，读写还分别受 runtime controls、published policy、state/risk gate 限制。

### 7. 配置是账号级不可变发布快照

运行时 controls（能力/kill switch）与版本化 reply config 分离，避免坏 draft 停止入站同步。config 包含 policy、templates、rules、comment/dm profiles；编辑写唯一 draft，使用 aggregate `expectedVersion`。publish 在单事务内验证全部 schema、变量 fallback、规则冲突、硬门禁和 role 引用，生成新的不可变 published config version；历史 job 永远引用创建时的 template/config version。

模板变量仅允许 `{{user_name}}`、`{{video_title}}`、`{{account_name}}`、`{{support_channel}}`。模板只能做字面替换，不支持表达式、脚本或 HTML。published profile 必须为模板使用到的每个可能缺失变量配置非空安全 fallback；否则禁止发布。运行时不得发 `null`、raw ID 或空占位。

规则排序固定为 `priority ASC, ruleId ASC`；相同 priority + 规范化条件命中不同模板是发布错误。没有规则/模板、配置不可读或引用过期时继续同步，但 job 进入可解释的 config failure，绝不自动发送。

### 8. AI 只有三个模型 role，renderer 是确定性程序

模型 role ID 固定为 `reply_intent_classifier`、`reply_polisher`、`reply_risk_reviewer`；`reply_template_renderer` 是确定性服务，不进入 LLM role catalog。结构化 schema 位于合同目录。

- classifier 失败：intent=`unknown`、risk tags 包含 `unknown`，强制人工。
- renderer 失败：不产草稿，返回 `INTERACTION_CONFIG_MISSING|INTERACTION_VALIDATION_FAILED`。
- polisher 超时/解析失败/越界：使用原 rendered template，绝不空回复。
- reviewer 失败：risk=`unknown`、自动发送 false，保留人工审核；确定性硬门禁仍不可绕过。
- `meaningChanged=true` 或 `introducedClaims` 非空：自动发送 false；模型自报这些字段不能作为安全事实源。
- 模型候选文本必须经过独立确定性 claim gate，至少识别并硬拦价格、折扣、促销、退款、订单、售后承诺和补偿承诺。
- 短期自动发送只允许未经过 AI、与确定性 template renderer 输出逐字相同且 claim gate 为空的文本；任何 AI 润色强制人工审批。
- 人工修改后必须重跑 reviewer；预览不建 job、不发 WS、不落真实 send attempt。

AI 输入只含当前任务必需的最小上下文。DM 的 AI 开关默认 false，直到业务/合规确认供应商与脱敏要求；关闭时仍可用确定性模板进入人工审核。

### 9. 风控与自动发送分成 all-send gates 和 auto-only gates

任何发送都必须同时满足：scope/ownership 匹配、auth active、identity match、有效 capability、全局/账号/channel 写开关、published policy、job CAS、无 active/ambiguous attempt、文本非空且长度合法、变量全部解析、非 unknown message、账号单飞、回复限速、Cloud `RiskController.canDo`。评论回复使用既有 `comment` action；私信回复新增 `dm_reply`，三窗口默认 quota 为 0，须显式配置后才可发送。只有 confirmed 才 `record`，失败/ambiguous 不记成功。

自动发送还必须满足 `mode=auto_safe`、账号白名单、rule 明确 allow、channel allow、risk=`low`、无硬风险 tag、未调用 AI、final text 与确定性模板渲染逐字相同、确定性 claim gate 为空、非人工编辑、登录冷却已过。任一不确定降级 `approval_required`。最终风险态仍只由 Cloud `RiskController` 写；reply rate limiter/kill switch 只能读风险态或做背压，不能改写它。

### 10. 凭证、隐私与保留采用保守默认

Cookie/session/二维码/浏览器调试地址只在所属 Edge 的 OS 安全存储或应用主密钥密文中存在，绑定 `envKey + accountId + finderIdentity + browserProfileId`。切换环境必须切换 cookie jar/timer/in-flight namespace。清除登录信息立即停写、删除本地密文并进入 login_required。

Cloud 默认保留评论正文 180 天、DM 正文 90 天、无正文审计元数据 365 天。解绑/删除/客户终止使用显式 offboard 状态机，顺序固定：Cloud 在单事务 revoke access + stop sync/write + durable command → Edge durable claim、drain、删除 scope 密文、关闭 sidecar并 durable 回执 → Cloud exact ack 后 tombstone → requestedAt 后 30 天内 purge。Edge 离线或失败时任务保持 pending 并在重连后重试；普通 pause/close/standby/logout 不得删除密文。允许保留到 365 天的审计只含必要 ID/event/status/time，不得含正文、最终回复/模板文本或凭证。该默认可支持 dev/mock；ol/真实客户数据仍需业务/合规确认。

### 11. Electron 只替换右侧 workspace

`wechat_channels` 环境选择后渲染 InteractionWorkspace；标题栏和左侧环境栏保持既有布局，不新增永久第二侧栏、不显示 browse/like/collect 等零 KPI。renderer 只经具名 preload IPC → Electron main → customer-auth API；无任意 URL fetch、JWT/Cookie 入口。环境切换取消请求并校验响应 `envKey`，旧响应不得覆盖新环境。浏览器 closed 是 active 的正常副状态；reauth/challenge 才禁写。ambiguous 显示“待核验”，HTTP accepted/queued 不显示绿色成功。

右侧 workspace 必须继续提供当前环境的显式生命周期控制，避免替换旧 workspace 时连同唯一的单环境启动入口一起隐藏。按钮复用现有 Electron 生命周期 IPC：核心停止或异常时显示“启动”，会话暂停时显示“恢复”，其余启动中或运行态显示“暂停”；调用始终携当前 `envKey`，返回状态仍走既有 fleet/status 路由。它与“全部启动”、显示浏览器、重新登录是不同动作，不得互相替代。

## Risks / Trade-offs

- [私有接口字段、端点或平台条款变化] → 每能力独立 flag、schema probe、TLS 校验和 `WECHAT_SCHEMA_CHANGED` 熔断；默认关闭写能力。
- [13 个 Interaction MessageType 增加协议漂移面] → 单一 JSON Schema/fixtures、两端枚举/handler/mapping/active-command 原子接线、分段能力协商与协议计数验收。
- [统一新 API envelope 与现有 API 风格不同] → 只约束本能力端点；不批量改造旧 API，Session 03/04 只消费 v1 schema。
- [配置关系表较多] → 以不可变 config snapshot 换取历史审计和可恢复性；v1 不做跨账号模板复用。
- [默认 quota=0/写开关关闭导致开箱不能发] → 这是私有接口与真实账号的安全代价；dev 受控账号可显式开启并留下审计。
- [DM 内容进入 Cloud/AI 的隐私风险] → 90 天保留、专门 permission、最小上下文、DM AI 默认关闭；ol 由合规问题阻断。
- [ambiguous 长时间占住 job] → 保持阻断比盲重试安全；提供回查、审计和人工可见状态，不能靠超时自动清除。

## Migration Plan

1. Session 00 合入/共享本 contract commit；不部署。
2. Session 02 先建 additive tables、API、schema validators、WS receiver/sender 和 mock Edge；所有 runtime/write flags 默认 off。
3. Session 01 实现 `wechat_channels` driver/connector、握手 capability、同步/ack、发送幂等与只读 probes；真实写仍 gated。
4. Session 03/04 仅按 fixtures 开发 Console 与 Electron workspace，不修改合同字段。
5. 集成时先启只读 dev 账号，验证分页/重启/身份；再启人工评论、人工 DM；auto_safe 与图片发送保持 off。
6. 回滚时先关全局/账号 write flags，再关 read flags；additive 数据表保留以便审计，不通过删表回滚。任何 `ambiguous` attempt 在回滚后仍保留，不自动重投。

## Open Questions

| ID | Owner | 保守默认 | 阻断范围 |
| --- | --- | --- | --- |
| OQ-01 私有接口/平台条款与账号风险是否获业务授权 | 产品负责人 + 法务/平台合规 | 全能力账号 flag off，写总开关 off | 阻断 ol、真实客户数据和任何自动写；不阻断 mock/dev 代码 |
| OQ-02 真实评论/DM 分页字段、删除标识、外部 ID 与发送回查稳定性 | Session 01 + 测试账号提供方 | 关键字段不符即 `schema_changed`，对应 capability off | 阻断该真实读/写 capability；不阻断 schema/mocks |
| OQ-03 评论 180 天、DM 90 天、审计 365 天和 30 天 purge 是否获确认 | 业务数据 owner + 合规 | 按本文保守默认实现 | 阻断 ol 保存真实正文；不阻断 dev/mock |
| OQ-04 哪些 Console 角色可看 DM 原文、AI 供应商能否处理 DM | 安全/合规 + Console owner | 仅 `interaction.dm.view_full` 可看；DM AI=false | 阻断 DM AI/普通排障原文；不阻断同步和模板人工审核 |
| OQ-05 真机账号、可删除评论目标和 DM 对话由谁提供 | 业务 owner | 无批准目标只做 read-only/gated，不声称发送成功 | 阻断 Session 05 真实写验收 |
| OQ-06 第一批 production 账号何时允许 auto_safe | 产品/风控 owner | auto_safe 全局和账号开关 false | 仅阻断自动发送，不阻断人工发送 |
| OQ-07 图片 DM 上传/过期/类型限制 | Session 01 + 业务 owner | `dmSendImage=false`，schema 只允许 text send | 仅阻断图片发送 |
| OQ-08 “转人工”最终是否接外部工单/通知 | 产品 owner | v1 只做状态 + 审计 + 可筛选队列 | 仅阻断外部工单集成 |
