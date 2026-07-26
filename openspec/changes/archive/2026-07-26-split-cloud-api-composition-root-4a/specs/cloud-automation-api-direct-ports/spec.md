## ADDED Requirements

### Requirement: automation SHALL 只经窄端口调用 API authority

独立 automation 进程 SHALL 只通过版本化窄端口调用 API-owned accounts、publish log、interaction
config/audit、reply config、persona、environment、onboarding、notification 与 Feishu/card 能力，
MUST NOT 构造 API owner store、打开 API owner 数据库连接、接收调用方 PG client，或把 API 模块复制为
本地实现。每个端口的方法面 MUST 与 3b 后仍存在的真实 automation consumer census 对应；无消费者对象
SHALL 从组合根删除而不是开放 route。

#### Scenario: automation 的 4a scoped wiring
- **WHEN** source guard 检查 `AIDCP_SERVICE=automation` 的 4a admitted authority wiring
- **THEN** 该 scoped wiring 只构造 automation owner pools/stores 和 API HTTP clients，不构造或连接 API
  owner pool/store；该结果本身不证明 full root 可 typecheck 或 boot

#### Scenario: 旧单体 root 含无消费者 API 对象
- **WHEN** census 发现某 API 对象的所有消费者均属于 API/面板/飞书入站而非 automation
- **THEN** 实现删除该对象在 automation root 的组装，不为它新增跨进程端口

### Requirement: scoped 方法账与 independent-root blocker ledger SHALL 分别门禁

4a SHALL 从 source consumer 与 owner map 导出 design D1 列出的 20 个方法簇、55 个 method slots：
automation→API 16/50、API→automation 3/4、API→content 1/1，并逐方法测试
route/client/owner adapter；MUST NOT 重建 3b
已经交付的 publish approval authority 七方法、decision writer、dispatch trigger 或 panel event channel。
同步 persona/account/config/environment/edge-state consumer SHALL 保留为 4b 镜像 blocker，MUST NOT
改成同步 HTTP、`T | Promise<T>`、默认值或直接跨 owner 读取；但会删除 `pausedEdges` 的
`resumeEdgesForAccount`、Facebook scope writes 与 Publish UI update SHALL 作为 4a paired commands，
MUST NOT 继续归为镜像或未鉴权的 3a 扩展。

系统还 SHALL 对完整 api/automation/content hand-written roots 生成独立 blocker ledger。该 ledger MUST
至少保留所有未解决 4b mirrors，以及 PersonaGenerator 之外的 Facebook publish media、其它 role factories、
通用 LLM、TokenUsage 和 curated content write。scoped 20/55 census 通过只证明 4a API authority surface
闭合；blocker ledger 未清零时 MUST NOT 声称 full root closure、独立 typecheck/boot 或三进程可运行。

#### Scenario: approval authority 在 4a 实施时已存在
- **WHEN** automation 需要读取或推进 publish approval revision
- **THEN** 它继续使用 3b 的现有 authority port/token，4a 不新增别名 route、重复 store adapter或第二份状态机

#### Scenario: 同步配置 getter 阻塞独立启动
- **WHEN** 4a 端口完成后 automation root 仍缺少同步 persona/config/account 镜像
- **THEN** 验收将其记为 4b blocker，不以 HTTP 包装、假默认或 API pool 回落令启动表面通过

#### Scenario: 非 Persona content authority 仍被 root 消费
- **WHEN** scoped 20/55 census 已闭合，但 hand-written root 仍依赖 Facebook media、其它 role factory、
  通用 LLM、TokenUsage 或 curated content write
- **THEN** independent-root ledger 保留具名 content-owner blocker；验收不得因它不属于 4a slots 而声称
  full root 已闭合

#### Scenario: scoped census 与 blocker ledger 结果不同
- **WHEN** 20/55 route/client/adapter 全绿，而 independent-root blocker ledger 非空
- **THEN** 交付仅声明 API authority scoped closure，并把独立 boot 保持为未交付

### Requirement: 内部调用 SHALL 同时验证版本、target 与 Bearer

每个 4a 请求 SHALL 携带 contract version、`executionTarget` 与方法输入，并使用所属方向的 internal
Bearer 凭据。API、automation 或 content server SHALL 在业务处理前验证凭据、版本及本地 target；
独立 api/automation/content 缺少
合法 target、URL 或 token 时 SHALL fail fast/fail closed。target 不匹配请求 MUST NOT 读取或修改任何
owner 数据，日志 MUST NOT 记录 token。

#### Scenario: 合法内部调用
- **WHEN** 调用方携带受支持版本、匹配本地 target 与正确 Bearer
- **THEN** 接收方只调用对应窄 owner adapter 并返回 owner 的结构化结果

#### Scenario: target 不匹配
- **WHEN** dev automation 向 API 发送 `executionTarget=ol` 或 API 本地 target 缺失无效
- **THEN** API 在进入 owner handler 前拒绝请求，且没有数据库写、通知发送或后继命令

#### Scenario: 凭据缺失或错误
- **WHEN** 4a route 收到缺失或错误 Bearer
- **THEN** server 返回统一 `internal_http_unauthorized`，不泄露记录是否存在、revision、target 或业务拒绝

### Requirement: 读取失败 SHALL 与合法空值分离

Account roster、publish log、reply config、persona/policy/onboarding 与其它 4a read SHALL 只在 owner 确认无记录时
MAY 返回契约声明的 null/empty；owner unavailable、timeout、bad response 或 schema failure SHALL 返回
具名错误，MUST NOT 转为空数组、null、零、false、默认配置或未绑定。

#### Scenario: owner 确认真正无记录
- **WHEN** API owner 成功查询且领域结果确实为空
- **THEN** client 返回该方法契约规定的合法空结果，并保留“已成功查询”的语义

#### Scenario: roster source 不可达
- **WHEN** automation 无法完成 `listAccountIdentities`
- **THEN** 本轮投影刷新失败且 `fresh_until` 不推进，调用方不得观察到“账号总数为零”的伪成功

### Requirement: 写操作 SHALL 保留 CAS、幂等与结果未知

API owner SHALL 保留 publish content version、approval revision、audit event id、environment/account
幂等键及现有事务边界。owner 明确拒绝、not-found、CAS conflict、transport unavailable 与写后响应丢失
SHALL 可区分；没有天然幂等键或稳定 command 去重的 mutation 在响应丢失时 SHALL 报
`result_unknown`，MUST NOT 自动重试或映射为成功/失败终态。

#### Scenario: publish draft version 已变化
- **WHEN** automation 使用过期 content version 调用 publish log edit 或 Edge draft command
- **THEN** API 返回稳定 version conflict，当前稿件与 3b approval revision 均保持不变

#### Scenario: audit relay 重放
- **WHEN** 相同 audit `eventId` 因 at-least-once relay 重投
- **THEN** API 至多保留一行并返回 inserted/duplicate 真态，consumer 可安全推进游标

#### Scenario: 通知发送后响应丢失
- **WHEN** API 可能已把卡片交给飞书但 automation 未收到 HTTP ack
- **THEN** client 返回 `delivery_result_unknown`，不得自动重发或记录为确定已送达/未送达

#### Scenario: Edge resume 响应丢失
- **WHEN** automation 可能已经删除暂停 Edge，但 API 没有收到可验证 receipt
- **THEN** API 记录 `edge_resume_result_unknown` 且不自动重试，不得把真实未知的恢复数写成 0

### Requirement: PublishLog scoped surface SHALL 覆盖传递消费者并保留 owner-local preview

automation→API PublishLog port SHALL 恰好覆盖 19 方法：`loadForDispatch`、`updateStatus`、
`updatePostId`、`markScheduled`、`markImagesAttached`、`listDueScheduled`、
`deferScheduledReconcile`、`confirmScheduledPublished`、`getMostRecentPublishTime`、
`recentPublishedContents`、`editDraft`、`rejectPendingApproval`、`pendingApprovalForAccount`、
`pendingPublishPreviewForAccount`、`lastPublishedForAccount`、`countPendingForAccount`、
`countPendingAutonomousForAccount`、`countPublishedTodayForAccount` 与
`countPublishedSinceForAccount`。census MUST 追踪 `PublishDispatcher`、
`ScheduledPublishReconciler` 与 scheduler 等传递消费者，MUST NOT 只统计 server 直接调用。

`listPendingApprovalIds` SHALL 不进入该 port；pending scan 继续使用 3b authenticated
`listPendingDispatch`。`pendingPublishPreviewForRecord` SHALL 只由 API owner 本地读取，MUST NOT 暴露为
automation→API route。

#### Scenario: 传递 consumer 使用 schedule 方法
- **WHEN** automation scheduled reconciler 调用 due-list/defer/confirm，或 scheduler 调用
  schedule/status/image/recent-history 方法
- **THEN** 它使用同一 authenticated、target-bound 19-method PublishLog client，automation root 不构造
  API PublishLogStore

#### Scenario: automation 请求逐 record preview
- **WHEN** automation UI projection 需要 owner record 的 preview/state 更新
- **THEN** automation 不调用 `pendingPublishPreviewForRecord`；API owner 本地读取后通过
  `applyPublishUiUpdate` command 单向投递

### Requirement: Publish UI update SHALL 是 owner-local preview 后的单向 command

API SHALL 在 owner-local publish mutation 后本地调用 `pendingPublishPreviewForRecord`，把结果整形成 typed
preview/state update，再通过 versioned、target-bound、`AIDCP_AUTOMATION_INTERNAL_TOKEN`
Bearer-authenticated `applyPublishUiUpdate(commandId, accountId, update)` 调用 automation。automation
SHALL 只更新本地 UI projection，并以 `target + commandId` 返回 applied/duplicate/collision receipt。
API preview 查询失败 SHALL 不发送 command；automation 可能已应用但响应不可证明时 SHALL 返回
`publish_ui_update_result_unknown`，MUST NOT 自动重试、声称未应用或回退为反向 preview read。

#### Scenario: API owner 本地生成 preview
- **WHEN** publish mutation 已提交且 API owner 成功读取 record preview
- **THEN** API 整形并发送 Publish UI update；automation 接收的 payload 不含 API store/SQL handle，且不
  回读该 record

#### Scenario: Publish UI update 重投或碰撞
- **WHEN** automation 当前进程收到相同 commandId
- **THEN** 相同 target/accountId/update 返回首次 receipt 的 duplicate，不同 payload 返回 collision，均不
  二次应用 UI projection

#### Scenario: preview owner read 失败
- **WHEN** API 无法证明 `pendingPublishPreviewForRecord` 的 owner 查询结果
- **THEN** API 不构造空 preview、不发送清除命令，并记录 owner-read failure

#### Scenario: UI update 响应丢失
- **WHEN** automation 可能已应用 update，但 API 未收到可验证 receipt
- **THEN** API 返回 `publish_ui_update_result_unknown` 且不自动重试；该未知状态不得改变 publish/approval
  终态

### Requirement: AccountRoster 与 Facebook scope 写 SHALL 成对完成

API SHALL 提供 `AccountRosterSourcePort.listAccountIdentities` 的全量真态；automation 只有在成功取得非空、
有效 roster 后才推进账号投影 freshness。3a 的 Facebook `importTargets` 与 `replaceTargetScopes` SHALL
在 scope label 首次不匹配时，于开启 automation 写事务前触发 roster refresh 并重新校验。刷新失败、
空 roster、陈旧投影或重校验仍不匹配时，两条操作 SHALL 具名拒绝且不产生部分 target/scope 写。
两条 command MUST 携带 version、匹配 target、稳定 commandId 与
`AIDCP_AUTOMATION_INTERNAL_TOKEN` Bearer；owner SHALL 返回原始 dedupe receipt 或
`facebook_scope_result_unknown`，MUST NOT timeout 自动重试。

#### Scenario: 新账号标签经刷新后可用
- **WHEN** scope label 在 automation 投影首次未命中、API roster 已含该标签且 refresh 成功
- **THEN** automation 重校验通过后在单个 owner 事务中完成 import/replace 并返回写后真态

#### Scenario: refresh 失败
- **WHEN** API roster route 不可达、返回 malformed/empty，或 freshness 无法推进
- **THEN** import/replace 返回可识别的 roster unavailable/stale 拒绝，已有 targets/scopes 保持不变

#### Scenario: replace 与 import 行为一致
- **WHEN** 同一未知 label 分别进入 `importTargets` 与 `replaceTargetScopes`
- **THEN** 两条路径都执行同一 refresh-before-reject 规则，MUST NOT 只有一条获得自愈能力

#### Scenario: Facebook command 的 bearer 或 target 错误
- **WHEN** `importTargets` / `replaceTargetScopes` 携带错误 Bearer 或不匹配 target
- **THEN** automation 在 roster refresh 和 owner transaction 前拒绝，targets/scopes 零写入

#### Scenario: Facebook command 响应丢失
- **WHEN** owner 可能已提交 scope 写但 API 未收到可验证 receipt
- **THEN** API 报 `facebook_scope_result_unknown` 且不自动重试；同 commandId 的显式对账只接受
  owner 原始 receipt，不能把 0 或业务拒绝当成结果

### Requirement: interaction 与 environment 跨 owner 写 SHALL 由 API 自持事务

Interaction auth gate 的行锁/判定、reply config/audit purge 与 environment registry SHALL 在 API
owner adapter 内使用 API pool/transaction。automation SHALL 只发送纯 DTO；
MUST NOT 把 automation `PoolClient` 编入 kernel/HTTP 请求。握手 welcome 已提交后的 environment 登记失败
SHALL 响亮记录但不撤销连接；只有 API 登记成功后，API MAY 触发本地 persona auto-fill。

#### Scenario: interaction purge
- **WHEN** automation 请求清理 API-owned reply config 或过期 audit
- **THEN** API 在自己的事务内执行并返回真实删除行数，automation 连接从未传入或用于 API SQL

#### Scenario: 握手登记失败
- **WHEN** Edge 已完成 welcome 而 environment registry route 不可达或结果未知
- **THEN** 连接保持在线，系统记录具名失败且不声称登记或 persona auto-fill 已完成

### Requirement: Offboard reconcile SHALL 由 automation 编排 owner-local primitives

系统 MUST NOT 把 `reconcileCleanupAdmissions` 整体暴露为 API route。automation SHALL 先在本地成功
读取完整 `activeWechatOffboards`，再调用 API-owned `reconcileActiveOffboardSnapshot`；
随后通过 `claimPendingMaterializations` 原子取得带 claim token/revision 的 admission candidates，
本地调用 `materializeEnvironmentOffboard`，最后以 `recordMaterializationReceipt` CAS/idempotently
回写真实 outcome。任何网络调用期间 MUST NOT 持有另一 owner 的 transaction。

#### Scenario: automation 活跃快照读取失败
- **WHEN** 本地 `activeWechatOffboards` 读取失败或不能证明是完整快照
- **THEN** automation 不调用 API snapshot reconcile，API 不把空输入当成“全部已清除”并释放 admissions

#### Scenario: claim 后物化成功
- **WHEN** API 原子认领一个 pending admission，automation 本地按 offboardId 幂等物化成功
- **THEN** automation 以 claim token/expected revision 回写 receipt，API CAS 匹配后记录真实
  offboardId/materializedAt 并返回 applied/duplicate

#### Scenario: binding 尚不存在
- **WHEN** local materialization 返回 `binding_missing`
- **THEN** receipt 保持 admission pending 并释放或续租 claim，MUST NOT 记录 materialized 或删除 admission

#### Scenario: receipt 回写结果未知
- **WHEN** automation 已本地物化但 API receipt ack 丢失
- **THEN** automation 不宣称整轮成功，admission/claim 由相同 offboardId 和 CAS 在后续轮次收敛，
  MUST NOT 生成第二条 offboard 或假成功释放 admission

### Requirement: Persona generation SHALL 留在 content owner

automation 调用的 `AccountPersonaPort.generate` SHALL 继续由 API 校验账号、平台、keywords、language 与
idempotency；API SHALL 通过 versioned、target-bound、`AIDCP_CONTENT_INTERNAL_TOKEN` Bearer-authenticated
`PersonaGeneratorPort.generate` 调用 content owner。API MUST NOT 构造 content `PersonaGenerator`
或通用 LLM；`AccountPersona.persist` SHALL 继续只写 API authority。生成响应不可证明时 SHALL 返回
`persona_generation_result_unknown`，MUST NOT 自动再次调用模型或复用 approval token。

#### Scenario: 合法 persona generation
- **WHEN** API 校验输入后以正确 content token/target 调用 generator
- **THEN** content 使用本地 PersonaGenerator/LLM 返回结构化 outcome，API 整形结果但不在 generate 阶段持久化 persona

#### Scenario: content 凭据错误
- **WHEN** persona generation route 收到缺失或错误 `AIDCP_CONTENT_INTERNAL_TOKEN`
- **THEN** content 在调用模型前返回统一 unauthorized，不泄露模型配置或账号事实

#### Scenario: generation 响应丢失
- **WHEN** content 可能已完成模型生成但 API 未收到可验证结果
- **THEN** API 返回 `persona_generation_result_unknown` 且不自动再生成；同 idempotency key 只能复用
  content 当前进程可证明的原 receipt

### Requirement: 通知出口 SHALL 只接受结构化命令并诚实回报投递

automation SHALL 只通过一个 kernel `deliver` 判别联合发送结构化通知命令；API SHALL 独占飞书 SDK、card builders、
账号显示名与 chat route 解析。需要人工审批的通知失败 SHALL 原样失败；允许业务层继续的运维通知也
必须先产生可观测 warn。无可用群、owner 拒绝、明确送达与结果未知 SHALL 保持不同结果。
`resolveCardChatId`、`resolveAccountChatId` 与 `bindBotChat` SHALL 留在 API 本地，MUST NOT 出现在
automation client 或内部 route。

#### Scenario: automation 发送候审通知
- **WHEN** automation 提交结构化评论候审命令
- **THEN** API 解析 owner 真态、构造并发送卡片；automation 不导入飞书 SDK 或 raw card builder

#### Scenario: 未知通知 kind
- **WHEN** API 收到版本支持但判别联合之外的通知 kind
- **THEN** route 稳定拒绝且不发送任何消息，MUST NOT 降级为自由文本或默认卡片

#### Scenario: chat resolve 与 bind
- **WHEN** API panel/Feishu 入站需要解析目标群或绑定默认群
- **THEN** API 直接调用本地 owner 能力，不经 automation、不开放额外 HTTP 方法

### Requirement: 交付证据 SHALL 分开证明契约、单体与独立拓扑

4a SHALL 以 source-derived scoped census 和 direct loopback tests 证明 20 组/55 slots 的
route/client/错误语义，以边界门禁证明 D1 准入的 automation 消费者只经 HTTP/client port 且没有
API owner pool/store reachability；另以 independent-root blocker ledger 证明尚未闭合的 4b mirrors、
root 构造与 content-owner dependencies 没有被隐藏。4a scoped acceptance MUST NOT 要求 blocker ledger
清零或用 full-root require-empty gate 冒充 scoped gate。DEV monolith 验收只证明现网零回归并保持独立
listener 未额外开放。只有 blocker ledger 清零、独立 api/automation/content units 实际启动后，才可声明
真实跨进程拓扑可达和 process-wide 无 foreign-owner pool。

#### Scenario: 只有 loopback 与 DEV monolith 通过
- **WHEN** 4a route/client tests 与 DEV 单体 health 均通过，但独立 units 未启动
- **THEN** 交付记录只声明 API authority scoped closure、源码/契约与单体零回归，不声明 full root、
  三进程互通、真实断链恢复或无跨 owner 运行连接

#### Scenario: 派生契约漂移
- **WHEN** kernel DTO、transport route、API adapter 或 automation client 任一侧未同步或 pin 过期
- **THEN** typecheck、package export probe、direct HTTP test 或 `sync-split-repos` 至少一道失败并指出漂移

### Requirement: Edge resume SHALL 是 target-bound 写命令

API SHALL 通过 versioned、`AIDCP_AUTOMATION_INTERNAL_TOKEN` Bearer-authenticated、target-bound
`resumeEdgesForAccount(commandId, accountId)` 调用 automation owner；automation SHALL 删除该账号名下
真实存在于 `pausedEdges` 的条目并返回首次应用的真实 resumed count。等价 commandId 重投 SHALL 返回
owner 当前进程保存的原 receipt；同 id 不同 payload SHALL 拒绝。receipt 不可证明时 SHALL 返回结果未知，
MUST NOT timeout 自动重试或把 0 当成未执行证明。

#### Scenario: 首次恢复暂停 Edge
- **WHEN** 匹配 target 的命令首次到达，账号有两个 paused Edge
- **THEN** automation 删除两项并返回 `resumedEdges=2`，API 不把该 count 推导自在线镜像

#### Scenario: 等价 commandId 重投
- **WHEN** 同一进程收到相同 target、commandId 与 accountId 的重复请求
- **THEN** automation 返回首次 receipt 的 resumed count，不再次执行后把结果改写为 0

#### Scenario: accountState 已恢复而 Edge 结果未知
- **WHEN** API 已成功提交 `accountState.resume`，随后 Edge resume transport 结果未知
- **THEN** 结果明确表示 `accountState=active` 且 `edgeResume=unknown`，不回滚账号状态、不声称全部恢复

#### Scenario: restricted recovery
- **WHEN** 3b `recoverRestricted` 尚未落账为 applied 或写后 risk 真态不是 normal
- **THEN** 本命令不得被用来绕过其闸门；restricted recovery 仍只由 automation 本地 durable
  resume-claim/outcome 链决定是否恢复 Edge
