## Context

3a 已提供 api→automation 的五组单向 owner routes，并刻意把 Facebook
`importTargets` / `replaceTargetScopes` 留到账号花名册反向端口完成后；3b 又交付了
`PublishApprovalAuthorityPort` 七方法、approval decision writer、dispatch trigger、restricted
recovery 与 panel event push。DEV 仍是 monolith，独立 `aidcp-api` / `aidcp-automation` 组合根尚未
通过全量 typecheck/boot。

§10 的“automation 要 api 侧 11 条”是 3b 前的簇级估数。对 `aidcp-cloud@67941e4`、
`module-ownership.json`、3a/3b artifacts 与 hand-written automation root 重新逐调用点复核后：

- 3b 的 approval authority/read/write/trigger 已交付，必须从 4a 删除；
- `getAccountCommentMode`、通知联系台账、首作进度、账号归属/运行期命令与 interaction purge
  等传递依赖不能继续漏算；
- `resumeEdgesForAccount` 虽曾列在“边缘在场同步镜像”，实际会删除 automation
  `WsServer.pausedEdges`，是 API→automation 写命令而不是 read projection；
- `reconcileCleanupAdmissions` 同时读写 API admission ledger、读取并物化 automation offboard，
  不能整体变成一个 API route；编排必须移到 automation，网络两侧只保留 owner-local primitives；
- `AccountPersonaService.generate` 属 API authority，但依赖 content-owned `PersonaGenerator`；
  API 必须调用 content port，不能复制角色/LLM；
- `PublishDispatcher`、`ScheduledPublishReconciler` 与 scheduler 是 publish log 的 automation-owned
  传递消费者；只盘点 server 直接调用会漏掉 9 个方法。`pendingPublishPreviewForRecord` 则只应由 API
  owner 本地读取，再经 API→automation UI command 推送；
- 同步 persona/config/account/edge-state 读取属于 4b 镜像，不能为了消 typecheck 临时包 HTTP；
- 飞书入站、面板层的归属已经裁决，不应把没有 automation 消费者的 API 对象复制进该进程；
- PersonaGenerator 以外的 Facebook media、其它 role factories、通用 LLM、TokenUsage 与 curated
  content write 虽不进入 4a 方法面，仍会阻塞 full root；必须进 blocker ledger，不能写成已排除即已闭合。

## Goals / Non-Goals

**Goals:**

- 给所有确认仍由 automation 真消费者发起的 API-owned 异步 authority/command 建立窄端口。
- D1 准入的 automation 消费者只装窄 HTTP client，不直接构造/接收 API owner store 或 pool；
  root 其余未迁移构造必须留在 D7 blocker ledger，4a 不据此声称独立 automation 已可启动。
- 保留 owner 事务、target、鉴权、版本/CAS、三态结果、at-least-once 与 unknown-result 语义。
- 完成 AccountRoster 反向取源，并配对开放 Facebook scope import/replace 的完整 3a 面板操作。
- 以最窄 target-bound command 让 API 请求 automation 恢复账号名下暂停 Edge，返回真实恢复数，
  并保持账号状态恢复与 Edge 恢复的部分成功真相。
- 让 Facebook 两条 scope 写同样成为受鉴权、target-bound、可判 result-unknown 的 automation commands。
- 让 API owner 本地生成 publish preview/state 更新，再经受鉴权、target-bound、可去重的
  `applyPublishUiUpdate` command 投递 automation UI projection；automation 不跨 owner 回读单条 record。
- 把 offboard reconcile 改为 automation 编排 API admission ledger 与本地 offboard owner primitives，
  保持 at-least-once、CAS receipt 与无跨网事务。
- 让 API 通过受鉴权的 content `PersonaGeneratorPort` 完成生成人设，persist 继续由 API owner 提交。
- 形成可机械核对的逐方法 scoped inventory、独立 root blocker ledger、共享包同步、聚焦测试和分层运行证据。

**Non-Goals:**

- 不重做 3b 已交付的 approval authority 七方法、decision writer、dispatch trigger 或 panel push。
- 不处理 `getSoul`/persona binding、账号显示身份/暂停态、environment gate、四张业务配置同步读、
  config freshness ambient 状态等 4b 镜像。
- 除 Edge resume/Facebook scope/Publish UI update 写命令外，不处理 API→automation 的排期/边缘在场读等反向端口；
  不恢复 `listAccountAutomationCatalog` mega-route，目录继续按 3a 决议在 API 本地由窄 automation
  facts 组装。
- API→content 只在本 change 实现 `PersonaGeneratorPort.generate`；Facebook media、其它角色工厂、
  通用 LLM、TokenUsage 与 curated write 仍是显式 independent-root blocker，不得因不进入 4a 方法面而
  从 ledger 消失。
- 不改变 protocol v2、Edge/Console 外部 DTO，不制作 installer，不部署 OL。
- 本 change 的源码完成不等于三进程已部署；4b mirror 或 content-owner blocker 任一未清零时，
  独立启动验收继续保持未交付。

## Decisions

### D1. 以 3b 后逐方法账为准，不保留“11 条”历史计数

4a 的 scoped 实现清单为 **20 个方法簇、55 个 method slots**：automation→API 主体 16 簇/50 slots、
API→automation 配对命令 3 簇/4 slots、API→content 生成依赖 1 簇/1 slot。该数字只证明 API authority
scoped closure，不代表 full composition root 闭合。表中每一项都必须由 source-derived consumer
census 与 owner map 同时导出；若调用点已随并行变更移回 owner 本地，则删除该端口而不是保留无消费者
route。独立 root 还必须通过 D7 blocker ledger 门禁，两道门不得互相替代。

| 方法组 | 4a 方法面 | owner → admitted consumer |
| --- | --- | --- |
| Account roster source | `listAccountIdentities` | API accounts → automation account projection / FB scope guard |
| Account ownership | `getExecutionTarget`, `resolveExecutionTarget`, `setExecutionTarget` | API accounts → automation handshake/risk ownership；无 automation 消费者的兼容 `claimExecutionTarget` 不开放 |
| Account runtime authority | `ensureAccount`, `getPlatformOrNull`, `getContactInfo`, `recordNickname` | API accounts → connection runtime, reply/comment workflow；`recordNickname` 在 owner 内比较并幂等写，避免跨网同步 get-then-set |
| Publish log for automation | `loadForDispatch`, `updateStatus`, `updatePostId`, `markScheduled`, `markImagesAttached`, `listDueScheduled`, `deferScheduledReconcile`, `confirmScheduledPublished`, `getMostRecentPublishTime`, `recentPublishedContents`, `editDraft`, `rejectPendingApproval`, `pendingApprovalForAccount`, `pendingPublishPreviewForAccount`, `lastPublishedForAccount`, `countPendingForAccount`, `countPendingAutonomousForAccount`, `countPublishedTodayForAccount`, `countPublishedSinceForAccount` | API publish log → automation dispatcher/scheduled reconciler/scheduler/UI account snapshot/delegated executor；传递消费者 9 方法必须计入 |
| Edge publish commands | `removeDraftImage`, `decidePublishApproval` | automation-owned Edge WS → API-owned handler；wire payload/result 复用 API-local contract，不导入 automation protocol |
| Interaction auth gate | `authorizeAuthStateWrite`, `checkAccountScope` | API transaction/row locks → automation interaction writes |
| Interaction API writes | `insertAuditEvent`, `purgeReplyConfigForAccount`, `purgeExpiredAuditEvents` | API tables → automation outbox/retention/offboard；HTTP 方法不得接收调用方 PG client |
| Reply config resolver | `resolve`, `getPublished`, `getSnapshotForJob` | API reply config → automation reply workflow |
| Account persona | `generate`, `persist` | API persona authority → automation Edge command handler；generate 内部再调 content generator |
| Environment handshake | `registerHandshakeEnvironment` | API client environment registry；owner 成功登记后在 API 内触发 persona auto-fill，不暴露第二个半完成通知 |
| Comment approval policy | `getAccountCommentMode` | API approval policy → automation comment approval gate |
| Notification contacts | `appendEvents` | API notification contact ledger → automation notification observer |
| First-post progress | `getFirstPostProgress` | API onboarding ledger → automation daily-usage snapshot |
| Automation config commands | `countContactAttemptsToday`, `recordContactCommentAttempt`, `resolveFacebookContainerName` | API content/Facebook config → automation browse/comment workflows；同步 schedule/config views 留 4b |
| Offboard admission ledger | `reconcileActiveOffboardSnapshot`, `claimPendingMaterializations`, `recordMaterializationReceipt` | API ledger primitives → automation-owned reconcile loop；无跨网 owner transaction |
| API notification exit | typed `deliver` command union | API Feishu/card builders/chat routing → automation notices；chat resolve/bind 均留 API 本地 |
| Edge resume command | `resumeEdgesForAccount` | API command face → automation `WsServer.pausedEdges`；写命令返回首次应用的真实 resumed count |
| Facebook scope commands | `importTargets`, `replaceTargetScopes` | API panel → automation owner writes；AccountRoster refresh 是其嵌套反向读 |
| Publish UI update command | `applyPublishUiUpdate` | API owner local preview/state producer → automation UI projection；stable commandId、owner receipt，禁止 automation 回读 record preview |
| Persona generator | `generate` | API AccountPersonaService → content-owned PersonaGenerator/LLM |

`InteractionApiWrites` 的两个 purge 现有接口携带 `Queryable`，这在物理拆库后会把 automation
连接传给 API SQL。4a 把 kernel port 改为纯 DTO；API adapter 自己开 owner 事务并返回真实 row count。
`insertAuditEvent` 保留载荷 `eventId` 主键和 `ON CONFLICT DO NOTHING`，重放返回 inserted/duplicate
而不是一律 `void`。

不进入本表的方法：

- 3b：`getApproval`、`listPendingDispatch`、`voidApproval`、`markDispatching`、`markConsumed`、
  `releaseToPending`、`setBlockedReason`、`writeDecision`、`triggerApproved`；
- 4b：任何同步 `getSoul`/persona/config/account/edge-state getter；`resumeEdgesForAccount` 是写副作用，
  不在此列；
- 3a/API 本地：`listAccountAutomationCatalog`；
- API 本地：`resolveCardChatId`、`resolveAccountChatId`、`bindBotChat` 与兼容
  `claimExecutionTarget`，automation 没有消费者，不开 HTTP；
- publish owner 本地：`listPendingApprovalIds` 由 3b authenticated pending-dispatch scan 取代，
  `pendingPublishPreviewForRecord` 只用于 API 本地生成 preview/update；两者不进入 automation→API port。

PersonaGenerator 之外的 content-owner 依赖不是本表的 4a slots，但必须出现在 D7 blocker ledger；“未进
scoped 方法账”不等于“full root 已消除”。

### D2. 端口按 owner transaction/失败语义拆组，不造 API mega-client

共享 kernel 只放纯 DTO/port；transport 每组拥有独立版本常量、route 表、server registration 和
client。API 组合根构造本地 owner adapter；automation 组合根只构造 client。不同失败方向不得塞入同一
`call()` 包装器：

- roster/reply/persona/policy/first-post 等读失败原样变为具名 unavailable/bad-response，不能返回
  `[]`、`null`、default 或 `false`；
- publish log、interaction、account/environment 等写由 owner 保留事务/CAS/幂等；
- 通知投递在 owner 明确拒绝、已送达、未送达与结果未知之间保持可区分；没有群是业务拒绝，
  发送后响应丢失是 `delivery_result_unknown`，不得自动重试制造重复卡；
- 既有调用点若明确“吵闹放过”，只能在业务调用层记录 warn 后继续，transport 不吞错。

不采用一个 `ApiClient` mega-interface：它会让每个 consumer 获得超出需要的写权，且无法对不同
CAS/unknown/fail-closed 语义做结构性审查。

### D3. 所有 4a route 都版本化、target-bound、Bearer authenticated

每个请求 envelope 至少包含：

```ts
{
  version: 1;
  executionTarget: 'dev' | 'ol';
  input: T;
}
```

带副作用且没有天然业务幂等键的方法另带稳定 `commandId`；读可带 correlation id 但不得借它缓存结果。
API server 在解析业务参数前验证：

1. Bearer 凭据；
2. contract version；
3. 本地 `AIDCP_DEPLOY_ENV` 合法且与 envelope target 一致；
4. 方法级输入。

automation→API 的 4a authority 使用 `AIDCP_API_INTERNAL_TOKEN`；API→automation 的 Edge resume、
Facebook scope 与 Publish UI update commands 使用同方向的 `AIDCP_AUTOMATION_INTERNAL_TOKEN`，但按 capability
分别注册窄 route；API→content persona generation 使用 `AIDCP_CONTENT_INTERNAL_TOKEN`。三者都不扩大
3b `AIDCP_PUBLISH_APPROVAL_INTERNAL_TOKEN` 的权力边界。独立 api/automation/content 模式缺
URL、target 或 token
即不装配可用 client/server；敏感不可逆入口 fail fast，后台读/中继进入具名 unavailable 并保持
pending/cursor。token 比较复用 `InternalHttpServer.registerBearer` 的定长摘要比较，日志不得打印 token。

不采用“只靠 loopback 绑定”或 target 参数当鉴权：部署配置错误或端口暴露时两者都不能识别调用者。

### D4. mutation 的 ACK 丢失一律保持 result unknown

HTTP client 把 owner 的稳定业务拒绝、CAS conflict/not-found、transport unavailable 与
post-side-effect response loss 分开。只有以下情况可重放：

- owner 已有天然幂等键，例如 audit `eventId`；
- 请求带稳定 `commandId` 且 API owner 有去重结果；
- `editDraft` 等以 expected content version 做 CAS，重试能返回相同结果或稳定 conflict。

否则 client 返回/抛 `*_result_unknown`，调用方保持待核验状态并停止不可逆后继动作。不得因 timeout
自动重试 nickname、environment、notification、Publish UI update 或 publish mutation，也不得把 unknown 映射为
`ok:false` 后触发补偿性删除/作废。

3b approval revision CAS 保持原端口与 token；4a 的 publish log/Edge command 复用 content version，
不在 transport 层伪造新的 approval revision。

### D5. AccountRoster 与 Facebook scope 写必须成对闭环

API owner route 返回 `AccountIdentityProjectionRow[]` 全量真态。automation projection refresher：

- source throw、malformed 或空 roster 都不推进 `fresh_until`；
- 成功非空读取才幂等 upsert，并保留未返回账号的既有过期语义；
- API 不可达时绝不直接读 API pool，也不返回空数组。

在该 client 完成后，扩展 3a `FacebookGroupOpsPort` 的 `importTargets` /
`replaceTargetScopes`。两条 API→automation 调用在 scope label 首次判否时，先让 automation 经
AccountRoster route 刷新本地投影，再重新验证：

- 刷新后 label 存在，才在 automation owner 事务内写 target/scope 并回读真态；
- 刷新失败、空 roster、仍不存在或投影陈旧，返回具名拒绝且不产生部分 target/scope 写；
- `replaceTargetScopes` 与 `importTargets` 使用同一 refresh-before-reject helper，不能只修一条；
- HTTP 嵌套调用不得持有 automation scope 写事务等待 API，避免锁跨网络。

两条方法不是“给 3a 未鉴权 route 加字段”，而是正式 command：

- 请求携带 version、target、稳定 commandId，并以 `AIDCP_AUTOMATION_INTERNAL_TOKEN` Bearer 鉴权；
- automation owner 按 `target + capability + commandId` 去重并保存原始业务 receipt；同 id 不同
  payload 拒绝；
- API 在 timeout/ack loss 后报告 `facebook_scope_result_unknown`，MUST NOT 自动重试或把未知写成
  `invalid_account_group`/零更新；
- wrong bearer/target 在 roster refresh、owner transaction 或任何写之前拒绝。

不采用“删掉 refresh 后直接判 invalid_account_group”：这会改变现有账号刚登记后的自愈行为。

### D6. notification 只传结构化命令，卡片与落点仍由 API owner 构造

automation 不导入飞书 SDK、card builders、`BotChatStore` 或 API messenger。跨进程端口**只有**
`deliver`，使用 kernel
判别联合覆盖现有真实调用种类（评论候审、mandatory outcome、收件箱提醒、巡视/排期/委托结果、
运维告警/文本）；API 根据 kind 构卡、解析账号显示名与 chat route，再发送。

`resolveCardChatId`、`resolveAccountChatId` 与 `bindBotChat` 的消费者都在 API-owned panel/Feishu
入站/卡片构造链，留为 API 本地调用；不得为“看起来完整”把它们授予 automation。

需要人工审批的卡发送失败原样抛；运维通知可由调用层 warn-and-continue；watchdog 的“无群”仍是错误，
不能记成 delivered。发送响应丢失报告 unknown，验收只证明 API 接受/发送结果，不声称飞书最终展示。

已有 content `PublishCardExitPort` 保持独立，不因字段相似合并：其 write approval signal 已受 3b token
保护，消费方、权限与失败后果均不同。

### D7. scoped census 与 independent-root blocker ledger 是两道独立门禁

第一道门是 source-derived scoped census：从当前 source consumer、owner map 与 service-mode guard
机械导出 D1 的 20 组/55 slots，并证明每个 admitted route/client/adapter 都有真实 consumer。它只回答
“4a 承诺的 API authority surface 是否闭合”，不能回答“独立 root 是否可 boot”。

第二道门是 independent-root blocker ledger：对 api/automation/content hand-written roots 做完整
source scan，逐项保留未解决依赖及 owner/direction/consumer/失败证据。以下 blocker 任一存在，full root
均保持未闭合：

- **4b mirror blockers**：persona binding/soul；account display/platform-age/pause 与 environment
  automation gate；content schedule/hot lead/Facebook config/join config 同步 view；config mirror
  freshness ambient state；API 所需的 week mask、edge presence/in-flight/captcha 等反方向镜像；
- **content-owner blockers**：除本 change 明列的 PersonaGenerator 外，Facebook publish media、其它
  role factories、通用 LLM、TokenUsage 与 curated content write。

任何同步 consumer 不改成 `T | Promise<T>`，也不在热路径临时调用 HTTP。Edge resume、Facebook scope
writes 与 Publish UI update 是副作用命令，不能从镜像推导或由错误 owner 本地执行，故属于 4a paired
commands；这不代表其余 edge presence/Facebook read 或 content authority 进入 4a。

scoped census 全绿时可以验收 4a route/client；blocker ledger 未清零时只能记录 scoped closure，MUST NOT
写成 full root closure、独立 typecheck/boot 或三进程可运行。

### D8. Edge resume 是独立命令，不是 3b restricted recovery 的别名

新增 `EdgeResumeCommandPort.resumeEdgesForAccount` 请求包含稳定 `commandId`、`accountId` 与
`executionTarget`，由 automation internal server 校验 version/target/Bearer 后调用本地
`WsServer.resumeEdgesForAccount`。首次应用返回真实 `resumedEdges`；owner 在当前进程生命周期内按
`target + commandId` 缓存原始 receipt，等价重投返回原 count，同 id 不同 account 拒绝。

`pausedEdges` 本身是进程内状态，因此本 change 不伪造跨重启 durable exactly-once。HTTP timeout、
响应丢失或 automation 重启使 receipt 不可证明时，API 记录 `edge_resume_result_unknown` 且 MUST NOT
自动重试；操作员后续显式恢复是新 commandId。禁止把 timeout 映射为 resumed=0。

API command face 保持顺序：

1. 先提交 API-owned `accountState.resume(accountId)`；
2. 成功后才调用远端 Edge resume command；
3. 若第一步失败，不发 Edge 命令；
4. 若第一步成功而第二步明确失败/unknown，结果必须表达
   `accountState=active` 与 `edgeResume=failed|unknown` 的部分成功，不回滚账号状态，也不回“全部恢复”；
5. 两步都成功才返回 `accountState=active, edgeResume=applied, resumedEdges=<真实数>`。

它与 3b restricted recovery 是两条权威链：restricted recovery 只在 automation 风控命令已经落账为
`applied` 且写后 risk 真态为 `normal` 后，本地恢复 Edge，并用其 durable resume-claim/outcome 收口；
通用 `/resume`/panel resume command 不修改 risk、不绕过 restricted recovery，也不得复用其 command
kind 或把 `accountState=active` 当成 risk normal。

### D9. Offboard reconcile 由 automation 编排三项 API ledger primitives

不得把 `ClientUserStore.reconcileCleanupAdmissions()` 整体注册为 API route：该方法内部调用
automation `activeWechatOffboards` / `materializeEnvironmentOffboard`，若 API route 再反调
automation，会把一次循环伪装成跨网事务并放大断链窗口。

改为 automation owner 的 reconcile loop：

1. 本地调用 `activeWechatOffboards()` 取得**完整成功快照**；失败则整轮停止，绝不提交空快照；
2. 调 API `reconcileActiveOffboardSnapshot(commandId, rows)`；API 在自己的事务内按现有 SQL
   幂等认领缺失 admission、释放已物化且已不活跃的 admission，返回真实 adopted/released counts；
3. 调 API `claimPendingMaterializations(workerId, limit)`；API 以 revision/claim token 原子认领
   `materialized_at IS NULL` 候选，按 `requested_at, env_key` 返回纯 DTO；
4. automation 对每个 candidate 本地调用 `materializeEnvironmentOffboard`；
5. 调 API `recordMaterializationReceipt`，携带 revocationId、claim token/expected revision 与
   `materialized` 判别结果。API 只在 CAS 匹配时提交真实 receipt；相同 receipt 重放返回 duplicate，
   冲突返回 stale/collision。

`binding_missing` receipt 清除/续租 claim 后保持 admission pending；materialized receipt 写真实
offboardId/materializedAt。automation 调本地 owner 时不持 API transaction，调用 API 时不持
automation transaction。任何调用 unknown 都保留 claim/admission 并在 lease/下轮收敛，不得声称已
materialized、释放 admission 或返回假空列表。

### D10. PersonaGenerator 留 content，API 只持 client

`AccountPersonaPort.generate` 仍是 automation→API authority：API 负责账号/platform/keyword/language/
idempotency 校验与结果整形；其生成步骤通过 versioned、target-bound、Bearer-authenticated
`PersonaGeneratorPort.generate` 调 content internal server。`persist` 继续只写 API persona authority。

content 复用既有纯 kernel `PersonaGeneratorPort`，不暴露通用 LLM。`AIDCP_CONTENT_INTERNAL_TOKEN`
与 approval token 分离；missing/wrong token 在 LLM 调用前拒绝。请求保留 idempotency key/diversity
seed；生成后响应丢失为 `persona_generation_result_unknown`，API 不自动再调模型，也不把 unknown
改写为 `generation_failed`。content 可在当前进程生命周期复用同 idempotency receipt，但不声称跨重启
durable exactly-once。

### D11. Publish UI preview 由 API owner 本地生成并单向推送

`pendingPublishPreviewForRecord` 的 record owner 与查询实现都在 API；automation 不应为刷新 UI
projection 反向逐条读取。API 在 owner-local publish mutation 后读取该 preview，整形成
`PublishUiUpdate`，再以 versioned、target-bound、`AIDCP_AUTOMATION_INTERNAL_TOKEN`
Bearer-authenticated `applyPublishUiUpdate(commandId, accountId, update)` command 推送 automation。

automation receiver 只更新本地 UI projection，并按 `target + commandId` 保存当前进程原 receipt；同
commandId 同 payload 返回 duplicate，同 id 异 payload返回 collision。API 查询不到 owner record 是明确
业务结果；owner preview 查询失败时不发 command。automation 可能已应用但 ack 丢失时，API 报
`publish_ui_update_result_unknown`，不得改为“未应用”、自动重试或回退到 automation→API
`pendingPublishPreviewForRecord` route。该 UI command 不改变 publish log/approval authority，也不作为
发布成功的终态证据。

`listPendingApprovalIds` 同样不开放：automation dispatcher 的 pending scan 继续走 3b
authenticated `listPendingDispatch`，避免重建第二条 approval scan 权威链。

### D12. server-first、派生同步与验收分层

实施顺序：

1. 在 `aidcp-cloud` 事实源补 kernel contracts、API/automation/content owner adapters、三向
   transport 与 direct
   loopback tests；
2. API internal server 注册 automation→API routes；automation internal server 注册 Edge resume/
   Facebook/Publish UI update commands；content internal server 注册 persona generator；automation service-mode 中
   D1 准入的 API authority 消费者只装 client，source guard 证明这些消费者没有 API owner pool/store
   reachability；root 其余构造继续由 D7 blocker ledger 明示；
3. 同步 kernel/transport 及真实消费仓，精确 pin，`aidcp-automation` 继续用本地 transport；
4. 运行 Cloud acceptance/full/typecheck/boundary，再运行各派生仓 focused/full-where-available/typecheck；
5. DEV monolith 只证明零回归、现有 listener/health/schema/Feishu/PostgreSQL；不额外打开任何独立
   internal listener；
6. source-derived scoped census 与 independent-root blocker ledger 分别验收；只有 4b mirror 与
   content-owner blockers 都清零、且独立 api/automation/content units 真启动后，才验收端口互通、
   断链/恢复与无跨 owner pool。

## Risks / Trade-offs

- [旧 root 复制了无消费者 API 对象，机械包端口继续放大面] → 每组实施前以最终 consumer 和 owner map
  双证据准入；无 consumer 直接删除组装，不开 route。
- [嵌套 Facebook import 形成分布式事务/死锁] → roster refresh 在 scope 写事务前完成；owner 写事务只碰
  automation 库。
- [远程读失败被业务 null/empty 吞掉] → wire response 用判别联合并做 malformed response tests；
  transport 从不提供默认值。
- [写后响应丢失导致重复副作用] → 天然键/CAS 才允许重放，其余稳定返回 result unknown、无自动 retry。
- [一个内部 token 权力过大] → 三个 owner 方向分别使用 API、automation、content token，3b approval
  token 不复用；route 仍按窄 capability 注册并做 source-level census。
- [账号状态恢复成功而 Edge 命令失败] → 返回 active + failed/unknown 的部分成功，绝不回滚已提交的 API
  事实或把 resumed count 猜成 0。
- [offboard 编排在任一边界中断] → admission/claim 保留，owner-local materialization 按 offboardId
  幂等，API receipt CAS；不持跨网事务，不释放未证实完成的 admission。
- [persona generation ack 丢失导致重复模型调用] → API 返回 generation_result_unknown 且不自动重试；
  content 只按同 idempotency key 返回当前进程可证明的 receipt。
- [notification union 漏掉一种卡，运行时静默不发] → 从当前调用点生成穷举 kind 清单，API switch 用
  `never` exhaustiveness，未识别 kind 返回稳定拒绝。
- [4a scoped tests 通过被误写为 full root/三进程完成] → tasks 与文档强制分开 source-derived census、
  blocker ledger、loopback、DEV monolith 与独立 units 五类证据；4b 或 content blocker 未闭合时不启动切换。

## Migration Plan

1. 建立 Cloud/kernel/transport/API/automation/content/control 隔离 worktree，重跑 preflight、
   source-derived 3b 后 scoped census 与 independent-root blocker ledger。
2. server-first 实现 4a contracts、owner adapters、HTTP 与 Facebook pair；先跑 direct/focused，再跑 Cloud
   acceptance/full/typecheck/boundary。
3. 同步共享包和派生仓，更新精确 pin；分别验证，不用 hand-written root 的既有 4b 错误冒充 4a 失败或成功。
4. 串行 rebase/fast-forward 默认分支并推送。若 runtime 行为改变且门禁全绿，仅部署 DEV monolith；
   备份、checksum sync、只重启 aidcp-cloud unit，验证现役服务。
5. 更新 §10 与 tasks，记录 20 组/55 slots、repo SHA、测试、DEV、未清零 blocker ledger 和尚未做的
   独立进程证据。

回滚按 consumer pin → transport/kernel → Cloud owner routes 的逆序执行。新增 routes/DTO 无破坏性 schema
删除；若确需 command dedupe inbox，只允许 additive migration，并保证旧 monolith 可忽略。任何 token
变更在部署前单独核对目标与回滚，不触碰 OL。

## Open Questions

无阻塞问题。实现期允许根据最终 source-derived consumer census 删除无消费者方法，但新增方法必须先回写
本 design 的 inventory 与 spec；不得用“让 root 先编过”为理由把 4b 同步镜像临时包 HTTP，也不得把
PersonaGenerator 之外的 content-owner blockers 从 independent-root ledger 隐去。
