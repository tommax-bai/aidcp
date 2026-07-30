## Context

当前 Facebook 规则模式由 Cloud 编译期常量决定 `viewThreshold=5`、`joinEveryNRounds=2`，定义标识同时编码数字并参与进度、去重事实和批次主键。Facebook 慢启动由 Cloud 固定七日 `[min,max]` 表决定，但运行时只消费每格上界；Edge 又复制了一份七日表用于展示。数值变更因此需要 Cloud/Edge 发版，并存在展示与执行漂移风险。

本变更必须在 `environment-level-rule-mode-and-approval` 完成后实施：模式开关以 `envKey` 为配置权威，数字策略是全局内部配置，账号仍是规则进度、去重和动作结果的权威键。`facebook-rule-mode-without-persona` 正在修改同一规则运行规格，`split-cloud-automation-production-runtime` 正在修改同一 sync-read/组合根，`wechat-review-residuals` 正在修改同一慢启动投影/clamp requirement；实施前须先串行集成这四个活跃 change 并在最新基线重核 delta。Cloud API、automation、Console、Edge 会同时受影响；DEV/OL 长期共享业务 PostgreSQL，因此不能以“某个进程已升级”推断所有消费者都理解新版本。

## Goals / Non-Goals

**Goals:**

- 让内部管理后台可配置规则模式的 `viewThreshold`、`joinEveryNRounds`，以及 Facebook 固定七日慢启动的受支持动作 `dailyCap`。
- 使用严格、不可自由扩展的类型，而不是脚本或通用 JSON DSL。
- 通过草稿、服务端校验、不可变发布版本、全局当前指针、影响预览和审计，使每次变更可定位、可用新版本恢复历史数值。
- 为规则收集周期、批次和慢启动生命周期定义确定的版本采用边界，重启、并发和服务拆分后结果不漂移。
- 只读客户端与运行态投影显示 Cloud 实际采用的版本和数字，未知或陈旧时不伪造默认值。
- 初始迁移逐位保留当前运行行为和既有开关、起点、进度及结果。

**Non-Goals:**

- 不开放动作集合、每轮动作次数、动作顺序、join-contact 编排参数、Prompt、模板、审批模式、强制执行或安全闸。
- 不开放七日时长、运营日时区、分钟/小时派生公式、RiskController 配额/状态、会话预算或全局停用闸。
- 不配置 `collect`、`comment_like`、`dm_reply`；它们在 Facebook 慢启动中继续固定为 0。
- 不新增客户级覆盖或任意继承规则；客户仅用于 Console 筛选和影响预览。
- 不提供环境级数字或版本选择；环境页只读展示实际/待采用版本。
- 不让 Edge 解释策略或触发规则动作，不改变 Native/Protocol v2 动作协议。
- 本变更不提供在途慢启动环境的强制换版；若以后确有需要，须另立带影响确认与审计的迁移契约。
- 不把提案、源码合并或 DEV 部署描述成已发布客户端或真实 Facebook 动作验证。

## Decisions

### 1. 使用两个严格类型的策略族，不建立通用规则 DSL

Cloud SHALL 定义两个封闭 schema：

- `facebook_rule_numeric`: `viewThreshold`、`joinEveryNRounds`，均为 `1..100` 的整数；对应 collecting progress 的数据库范围固定为 `0..99`。
- `facebook_slow_start_numeric`: 固定 `day=1..7`；每一天必须且只能包含 `view`、`like`、`comment`、`follow`、`publish`、`search`、`join_group` 的 `0..QUOTA_MAX` 整数 `dailyCap`，且同一动作从第 1 天到第 7 天单调不降。`QUOTA_MAX` 复用 Cloud 风控配额的固定校验权威，当前 schema 值为 `100000`；其后若要变化须升级 schema version。缺天、缺动作、额外动作、重复键、逐日下降和未知字段均整块拒绝。

Cloud 是 schema、字段范围和动作闭集合的唯一裁决者；Console 可用同一元数据做即时反馈，但服务端必须重新校验。`viewThreshold=0` 或 `joinEveryNRounds=0` 不作为“关闭动作”的隐式写法，模式关闭仍只走既有 `enabled`。

慢启动不再保存无运行语义的 `[min,max]`；迁移只取现有 Facebook 曲线每格上界作为 `dailyCap`。固定为 0 的三项动作由运行时补齐，后台不显示也不接受它们。

**Alternatives considered:** 复用通用 quota 页面会混淆安全基准与生命周期 clamp；自由 JSON/动作列表虽然扩展快，却会间接开放动作和编排，均不采用。

### 2. 发布版本不可变，草稿使用 CAS，标识不再编码数字

API owner 数据库使用一张公共元数据表和按策略族归一化的类型表：

- `facebook_mode_policy_revisions`: 全局稳定且不依赖数据库本地 sequence 的 `id`、`kind`、单调 `revision`、`schema_version`、`status=draft|published`、`lock_version`、创建/更新/发布 actor 与时间、发布说明。
- `facebook_rule_numeric_policy_values`: 每个 revision 一行，保存两个整数。
- `facebook_slow_start_policy_day_caps`: 每个 revision 固定 7×7 行，以 `(revision_id, day, action)` 唯一。
- `facebook_mode_policy_current`: 每个 kind 指向一个已发布版本，发布时以 CAS 原子推进。
- `client_environments.slow_start_policy_revision_id`: 慢启动开启时保存全局当前 revision 的生命周期 pin；关闭时与 `slow_start_since` 一起清空。

automation owner 数据库另建 `facebook_rule_policy_writer_rollout`，按 `execution_target` 保存单向 `legacy_fill → reject_missing` phase、epoch、切换 changeRef、权威 expected-automation-instance-set digest 与时间，并保存每个 automation writer 实例的 build SHA、writer contract version、server `observedAt`/`freshUntil` 心跳。API writer coverage 由 API owner 独立记录和裁决，不复制进 automation 表。automation 的 rule progress/view fact/batch 只保存稳定的跨库 policy identity 与完整数字快照，不建立指向 API 数据库的外键，也不让 trigger 读取 API owner current。

草稿保存与发布统一携带 `expectedDraftVersion`；校验只返回规范化预览与错误；发布另外携带 `expectedPublishedRevision`，在单事务内严格校验、冻结新 revision、推进全局当前指针并写审计。已发布行及其类型值不得更新或删除。恢复历史数值须读取历史不可变 revision 的完整详情，再把其数字写为新草稿并发布成新的单调 revision，不把当前指针倒退或原地修改旧版本。Console 不创建 definition id、revision 或 schema version。

规则动作拓扑使用独立的编译期 `definitionSchemaId`/`definitionSchemaVersion`；数字使用 `policyRevisionId`。两者共同构成运行身份，避免继续用 `facebook_browse_5_...` 这类把参数编码进定义名的标识。

**Alternatives considered:** 原地更新单例配置无法解释在途进度，也不能可靠审计/回退；只保存 JSONB 会把闭集合与逐格完整性完全推给应用校验，故采用带数据库约束的类型表。

### 3. 全局版本由运行态在安全边界自动采用

规则模式开关仍归属环境，数字策略不提供环境覆盖。API owner 的事务指针称为 `ownerCurrentPolicyRevision`；每个 automation target 完整应用镜像后持有 `appliedCurrentPolicyRevision` 与 `appliedCursor`。发布提交不等于全部 consumer 已应用；传播窗口内 target 可以继续使用其仍新鲜、完整的旧 applied current，Panel 必须显示 owner current、各 target applied current/cursor/lag，不能把它描述成已经全体采用。配置读回同时返回对应 target 的 applied current 和当前账号的 `adoptedPolicyRevision`；没有唯一账号绑定时只返回“下次执行将采用”的 applied 版本，不编造运行态。

规则版本采用规则如下：

1. 无活动批次且当前 collecting progress 为 0 时，可在下一次 admission 采用本 execution target 已原子应用且仍新鲜的 current revision；不得直接跨 owner 数据库读取刚发布但尚未应用的指针。
2. 已有 collecting progress 时，继续使用该 progress 已快照的旧阈值，创建并结算这一轮；已有批次也继续使用批次快照。
3. 该轮终态并清除 active-round pointer 后，下一轮才采用该 target 届时已应用的 current revision。
4. 换绑账号不迁移 progress、去重或批次；新账号从 0 开始采用其 execution target 当时已应用的 current revision，旧账号的在途批次按原快照诚实收敛。

进度/视图事实键包含 account、server-injected execution target、独立的 `definitionSchemaId`/`definitionSchemaVersion` 和 adopted policy revision。进度保存 `viewThresholdSnapshot` 与 `joinEveryNRoundsSnapshot`；批次保存同一 revision、两项数字、`cyclePosition`、`includesJoinContact`。这些持久快照是旧规则 revision 在途结算的完整数字权威：恢复非零 progress/active batch 时验证其 definition identity、revision identity 与数字快照即可，不要求 automation 镜像继续携带已退出 current 的旧规则定义；任一快照缺失/非法则失败关闭。运行时不得回查一个可变化的全局当前指针来重写既有进度或批次语义。

慢启动开启时，Cloud 通过 customer PUT、admin PUT 和程序化环境创建 intent 共用的服务，在同一事务写 `slow_start_since` 和当时 owner current 的 `slow_start_policy_revision_id`；生命周期七日内始终使用该 pin。发布新 revision 只影响之后开启的环境，不改变当前 day、起点或额度。关闭时原子清空起点和 active pin；再次开启按当时 owner current revision 重新 pin。环境换绑账号保留起点与 active pin。

**Alternatives considered:** 发布后热改全部在途环境最直观，但会让同一天额度和部分收集进度中途改变；复制策略到账号则破坏环境配置权威。安全边界采用同时保留两者。

### 4. 两类策略独立发布并在提交前展示影响

内部 Panel API 提供：

- 策略列表、游标分页的历史 revision 列表、单个不可变 revision 完整详情、草稿读取/保存、校验、发布和游标审计；历史恢复通过“读取旧详情 → 写入新草稿”完成；
- 发布前的影响预览，返回会在安全边界采用的规则账号数、仍会固定旧版本的在途规则轮次数、之后开启会采用新版本的环境数、正在固定旧慢启动版本的环境数和不兼容消费者；易变计数携带 `asOf`，只用于影响说明；
- 发布请求携带草稿版本、预期当前 published revision、基于规范化草稿/当前指针/schema capability/客户端能力 cohort 的稳定 preview digest 与说明；提交时复核这些承重事实并返回最新易变计数，账号进度自然变化本身不制造无穷 CAS 冲突。相同幂等键与完全相同 payload 的重放是超时后的权威结果查询；不得换新幂等键猜测发布结果。

规则与慢启动草稿、revision 和当前指针彼此独立，修改其中一类不生成另一类的新版本。发布成功只推进该类全局当前指针；它不写环境级数字，不重置进度或起点，也不改写慢启动 active pin。任一预期版本或预览 digest 漂移时发布整块拒绝。所有写回包均返回完整服务端真态、actor、时间与 request id，Console 非乐观刷新。

Customer-auth/Edge 路由继续只接受 `{enabled}`。客户与 Edge 无法读取草稿、历史审计、其它环境或内部影响统计，也不能提交 revision。

publish route 另受一个服务端发布闸约束：只有 OL API owner 同时满足 `AIDCP_DEPLOY_ENV=ol`、`AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_ENABLED=true`，并提供非空部署变更引用 `AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_CHANGE_REF` 时才可进入既有 preview/CAS/capability/idempotency 复核；缺省、非法、DEV 或 monolith 未标明 OL 时一律返回具名 `policy_publish_disabled`。该状态必须出现在 Panel read/preview 与 health 中，不能成为隐藏 veto；Console 不提供打开闸门的按钮。Cloud 每次启动/状态变化 SHALL 追加记录 target、build SHA、instance、enabled、changeRef 与 server observedAt，每次发布审计关联所用 gate observation。恢复 revision 也走同一普通发布路由和全部校验：若 writer 已关闭，必须另行授权短时开启、发布、确认 target applied 后再次关闭，不存在未审计 bypass。

**Alternatives considered:** “保存即全局热生效”缺少 blast-radius 边界；让客户自己选 revision 会把内部节奏控制暴露到客户端，均不采用。

### 5. API owner 持久化，automation 使用本地 gate 镜像

策略元数据和 owner current 由既有 Cloud API/配置所有者写入。automation 不在动作热路径同步查 API 或共享 ambient singleton，而是把 Facebook mode numeric policy 作为 gate 扩展到既有 `client_environment_automation` 完整快照：同一 cursor 原子携带环境 enablement/slow-start anchor+active pin、两个 owner current 的严格定义、所有仍被 active slow-start pin 引用的旧不可变定义，以及每个环境的 `facebook_mode_policy_projection_v1` positive/negative observation、server `observedAt` 与 `freshUntil`；并按 `executionTarget` 原子保存 contract version、`appliedCurrentPolicyRevision`、`appliedCursor`、as-of、fresh-until 和 applied digest。旧规则 progress/batch 使用自身完整数字快照结算，不扩大镜像去保留所有历史规则定义。该能力不能继续借用当前 content-schedule 刷新信号，也不新增未登记的第十二条同步热读。

数据迁移必须按物理 owner 拆成独立、带 ownership metadata 的 API migration 与 automation migration。API migration 可在同库为旧 `slow_start_since` writer 安装读取 API owner current 的 legacy bridge；该 trigger 与 publish CAS 必须锁同一个 kind current row，使并发旧 enable 要么在发布前原子 pin legacy，要么在发布后因缺 non-legacy pin 失败，disable 则始终原子清空 anchor+pin。automation migration 的 rule trigger 不得尝试跨库读取该 current，而是按行上的 server-injected `execution_target` 对本库 rollout phase 做与切换事务冲突的锁定读：`legacy_fill` 时只补迁移定义的稳定 legacy policy identity、既有 definition identity 与 `5/2` 快照，`reject_missing` 时拒绝任一缺字段写入。phase 缺失、target 非法或 identity 不匹配同样失败关闭；phase 只能前进且永久不得回开。

每个 target 切换到 `reject_missing` 前，automation owner 必须用权威部署清单枚举该 target 所有 desired/restartable automation writer 实例，并要求集合中每个实例都在既有 service-heartbeat TTL 内报告 policy-aware writer contract、允许的 build SHA 与 server freshness；仅“旧 heartbeat 数量为零”不构成完整证明。切换事务只在 automation owner 内锁定 target phase，等待旧 rule 写事务退出，执行幂等 catch-up 与零缺口 census，再原子推进 phase。automation health snapshot 将 phase/epoch、expected-automation-instance-set digest、coverage、build 与 freshness 作为 target-attested readiness 投影给 API；API 不跨库查询。API owner 以自己的 deployment inventory 与心跳独立证明 API writer coverage。non-legacy publish 必须复核两份独立证据：DEV/OL automation 均为 fresh `reject_missing` 且 coverage 完整，以及 DEV/OL API writer coverage 完整。

该镜像按 gate 处理：首次未装载、transport/policy snapshot 陈旧、结构无效、未知 schema/revision、当前指针引用缺失版本或 target 不匹配时，不开始/推进任何新的规则或慢启动平台动作，并投影具名 blocker；不得用编译期旧数字补成“可执行”。镜像自身的 transport/policy `freshUntil` 与其中 capability observation 的 `freshUntil` 是两个独立时钟：一份新鲜、结构合法的 snapshot 可以诚实携带 missing/negative/expired capability，后者只阻止后续 non-legacy enable/adoption，不会把整份镜像变陈旧，也不会单独中断已有 active pin 或已 adopted revision。active pin 与 day 可以作为持久生命周期事实继续推进，但每次新平台动作仍须通过 transport/policy gate；只有已经 dispatch 的不可逆动作可在该 gate 失效后按既有自然收敛路径结算。相同 cursor 重放幂等，旧 cursor 不得覆盖当前值。

共享 PostgreSQL 中的业务策略不按 DEV/OL 复制；因此不存在“只发布到 DEV”的非默认 current。真实发布前必须检查 DEV 与 OL 的 policy-aware API/automation consumer 均已报告支持对应 `schema_version`，并取得一次明确的全局行为变更授权；任一目标不兼容、未部署或状态未知时可以保存草稿和预览，但不能发布并推进共享 owner current。publish commit 与 target snapshot apply 分开观测，传播 lag 不是伪装成已全体采用的理由。

**Alternatives considered:** automation 每次查库/API 增加热路径故障面；按 target 复制业务配置会产生同一环境两份真相，均不采用。

### 6. Console 集中管理全局数字，环境页与运行页只读展示

Console 新增 `/mode-policies`，置于 System：

- 规则模式页仅显示两个数字、允许范围、当前草稿/发布版本、影响预览和发布确认；
- 慢启动页以 7 天×7 个固定动作矩阵编辑 `dailyCap`，分钟/小时按 Cloud 元数据和既有公式只读预览；
- 版本/审计页可比较、回看历史已发布版本，并可从历史数值建立新草稿。

环境页显示规则模式的 owner current/target applied current/账号 adopted revision、慢启动的全局当前/环境 active pin、开关、binding 状态和“传播中/下一轮/下次开启采用”提示，不提供数字或版本选择。账号排期页继续只显示账号进度与动作真实结果，可跳转环境配置，不承担策略编辑。

Edge 通过 additive customer-auth DTO 获取完整 policy envelope：`envKey`、`kind`、`revision`、`schemaVersion`、`complete=true`、`asOf`、`freshUntil`、可选 digest 和同 revision 的规则摘要或慢启动 `days`（恰好七行，每行含 `day` 与固定七动作 `dailyCaps`）。顶层 `dayQuotas` 只表示有唯一绑定账号时同一次 controller 计算出的**当日最终额度**，绝不表示七日策略。Edge 删除本地硬编码表，不本地推算天数、阈值或分钟/小时值；缺失、陈旧或不兼容时显示未知并保留模式开关的 Cloud 真态，不展示伪造默认。

新 Edge 在已认证的环境读取、写入和创建完成请求中以 `X-AIDCP-Client-Capabilities` 上报固定 token `facebook_mode_policy_projection_v1`；Cloud 只按已授权 owned envKey 或有效 create-intent completion 记录服务端 observation。含 token 记为 positive，相关已认证请求不含 token 或值非法时必须以新的 `observedAt` 记录 negative，立即撤销旧 positive；positive 仅在 30 天内为 fresh。规则策略发布的受影响客户端 cohort 是所有已启用规则模式、可能在下一安全边界采用新 current 的 Facebook 环境；任何环境为 negative、missing 或 stale 均阻止 non-legacy 发布。non-legacy current 下的新规则 enable 与每次新 revision adoption、以及新的慢启动 enable（含 customer/admin/create-intent）也必须有 fresh positive；automation 只从同 cursor 的本地 gate snapshot 读取该事实。规则 disable 仍允许执行，因为它只减少平台动作。慢启动一旦在 fresh capability 下 pin 成功，之后 capability 过期不会换版或单独中断既有生命周期，运行时仍由 policy gate freshness 约束。Panel 预览逐 envKey 显示 compatible/incompatible/unknown，不接受口头覆盖。

### 7. 安全与可观测性边界不随数字配置放宽

规则数字只决定何时创建固定的一次 like 和固定的一次 join-contact 链；每个动作继续经过 RiskController、session、daily、approval、dedupe、target、Native input 和平台后置验证。慢启动每个窗口的最终值仍为风险缩放/显式 quota 与该日派生天花板逐动作取更小值。全局停用、未知绑定、平台不支持和风险状态保持现有优先级。

所有投影按语义携带 owner current、target applied current/cursor/lag、effective/adopted/active revision、schema version、freshness、blocker 和更新时间。监控至少覆盖发布失败、镜像陈旧、不兼容 schema、缺失 revision、客户端 capability 缺失/陈旧、target 传播延迟、延迟采用和旧版本在途数量。

## Risks / Trade-offs

- [跨活跃 OpenSpec 变更重叠] → 先完成 `environment-level-rule-mode-and-approval`，并在 `facebook-rule-mode-without-persona`、`split-cloud-automation-production-runtime`、`wechat-review-residuals` 的热点提交集成后 rebase、重新核对 delta；这些单写热点不并行实现。
- [共享数据库滚动部署时旧进程读到新 schema] → 先做向后兼容迁移和只读支持，再发布管理写面；发布前检查消费者 capability。
- [物理拆库使 rule trigger 无法读取 owner current] → API/automation 使用 owner-specific migrations；automation trigger 只读本库单向 rollout phase，API 通过 fresh target-attested readiness 机械门禁 non-legacy publish。
- [owner publish 后 target 尚未应用] → 分别投影 owner current 与 target applied current/cursor/lag；admission 只采用本 target 已原子应用的 fresh current，不声称 publish 回包即全体生效。
- [旧安装客户端看不到新数字] → 使用环境作用域、30 天 fresh 的能力观察门禁；缺失能力时阻止受影响 cohort 的非 legacy 发布或后续 enable/adoption。
- [规则换版丢失部分浏览进度或重跑动作] → 进度与批次快照数字和 revision，只在终态安全边界采用。
- [慢启动当天额度中途变化] → 启用时 pin 七日版本，新发布不迁移在途生命周期。
- [后台把大数字误解为放宽安全上限] → UI 明示“生命周期天花板”，Cloud 最终逐位取更严值并显示派生/最终值差异。
- [初始曲线注释与实际表不一致] → 初始版本以当前运行时真实上界为准，保证零行为回归；任何产品修正另发新 revision。
- [Edge/Cloud 展示漂移] → Edge 只渲染 Cloud 投影，移除复制表；未知不回落本地常量。
- [不可变版本累积] → 版本只追加并分页查询；历史数值通过新 revision 恢复，不物理删除审计证据。

## Migration Plan

1. 先完成并归档/合并 `environment-level-rule-mode-and-approval`，确认规则模式配置已是 env-scoped，Console 不再写 account-scoped 开关；等待 `facebook-rule-mode-without-persona`、`split-cloud-automation-production-runtime` 与 `wechat-review-residuals` 的规则运行/sync-read/慢启动投影热点稳定后 rebase 并重核本 change。
2. 追加两组 owner-specific、expand-only migration 与只读模型。API migration 创建策略/审计/current、slow-start pin 与 API legacy bridge；automation migration 创建 rule snapshots、按 target 的 `legacy_fill` rollout phase/实例心跳及本库 triggers，并在同一 owner migration 宽化 `view_count` CHECK。两边共享一个迁移定义的稳定 legacy rule policy identity；不得用各库本地 sequence 猜测对应关系，不得修改既有迁移。
3. API migration 创建两个 legacy published revision：规则数字取当前 `5/2`；慢启动逐格取当前 `FB_COLD_START_PLANS` 上界，包括实际 D3 `join_group=1`，并把两个 owner current 指向它们。正在慢启动的 Facebook 环境 pin legacy slow-start revision 且保留原 `slow_start_since`；automation migration 以同一稳定 rule identity 回填现有 progress/fact/batch 的 definition identity 与数字快照，不重置、不补动作。
4. 初始 API bridge 在 slow-start owner current 仍为 legacy 时为旧 `slow_start_since` writer 原子补/清 legacy pin，current 成为 non-legacy 后拒绝缺 pin 写入。automation trigger 不读 API current：各 target 为 `legacy_fill` 时为旧 rule writer 补稳定 legacy identity/`5/2` 快照，切为 `reject_missing` 后永久拒绝缺字段写入。
5. 先部署 policy-aware API 三个慢启动入口的 anchor+pin 双写、rule runtime snapshot 双写、writer contract heartbeat 和 capability observation producer，保持 reader 宽容且 publish gate 默认关闭。DEV/OL 任一 target 仍处于 `legacy_fill` 时 automation trigger 继续承接旧 rule 写；不得先启用该 target 的 strict automation consumer。
6. 对每个 target，automation owner 从权威 deployment inventory 固定 expected desired/restartable automation instance set；要求集合内每个 automation writer 均在既有 heartbeat TTL 内报告 policy-aware contract、允许 build SHA 与 freshness，且旧 artifact 已不再是可重启配置。仅观察“没有旧 heartbeat”不足。随后在锁定 phase 的同一 automation owner 事务中等待旧 rule 写退出、执行幂等 catch-up、证明该 target 缺 rule snapshot/definition identity/非法半行为 0，并单向切换 `legacy_fill → reject_missing`。API owner 独立固定自己的 DEV/OL expected writer sets、验证同样的 fresh build/contract coverage，并证明 `since!=NULL,pin=NULL` 为 0；任一侧不得跨库完成另一侧证明。
7. 只有 DEV/OL 的 fresh target health 都证明 `reject_missing`、expected-instance-set coverage 完整且 API writer coverage 完整后，才启用 strict automation mirror consumer/fail-closed gate；该 phase 永不回开。部署 Console 只读/草稿/预览面与 customer-auth additive DTO，随后通过另行授权的 Edge 安装包发布动态展示和 capability marker；旧 Edge 可忽略新增响应字段，但在 non-legacy current 下不得开启/采用新策略。
8. DEV 验证只使用草稿、预览、代码级测试或不会推进共享 `facebook_mode_policy_current` 的隔离 fixture；不得用共享库发布 non-legacy revision 来“先试 DEV”，因为它会同时改变 OL 可见的业务 current。
9. 只有在 OL 也经明确发布授权部署兼容 API/automation、DEV/OL runtime capability、fresh `reject_missing` rollout attestation、完整实例 coverage 与受影响 Edge cohort 均满足，并另行取得全局行为变更授权后，才在 OL API 短时开启具名 publish gate、发布一次 non-legacy revision、关闭 gate。随后分别验证 durable gate-off、owner current、各 target applied cursor/current、规则安全边界、慢启动 pin、镜像陈旧与审计；代码/config 验收不作为真实 Facebook 动作确认。

Rollback 不删除版本或回滚迁移：先关闭管理写入口；若需基于 legacy 数值发布新的恢复 revision，则按另行授权在 OL API 短时重新开启同一 publish gate，走正常 preview/CAS/capability/idempotency/audit 后立即关闭。已开始规则轮次和慢启动生命周期仍按各自快照/pin 收敛。policy-aware reader/schema 是永久不可回退地板：即使 owner/applied current 已恢复、所有 non-legacy 规则在途事实与 active pin 均排空/结算，也只能回退到仍理解 policy revision/pin/snapshot 的兼容实现，永远不得部署 pre-policy runtime；迁移永不回滚。

## Open Questions

- 无阻塞产品问题。实现前需在依赖变更合入后的最新基线重新确认 API/automation 的最终配置 owner 名称和迁移序号；这不改变上述权威、版本或失败关闭语义。
