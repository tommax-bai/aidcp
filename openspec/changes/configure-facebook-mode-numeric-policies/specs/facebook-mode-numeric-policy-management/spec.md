## ADDED Requirements

### Requirement: Facebook 模式策略只开放封闭的数字字段

系统 SHALL 提供严格类型的 Facebook 规则模式与慢启动数字策略。规则模式策略 MUST 且只能包含 `1..100` 的整数 `viewThreshold` 和 `joinEveryNRounds`；慢启动策略 MUST 固定为第 1 至第 7 天，并在每天完整包含 `view`、`like`、`comment`、`follow`、`publish`、`search`、`join_group` 的 `0..QUOTA_MAX` 整数 `dailyCap`。`QUOTA_MAX` SHALL 复用 Cloud 风控 quota 的版本化校验权威，本 schema 的值为 `100000`；Cloud SHALL 返回这些固定范围并在服务端重新校验。

策略 schema MUST NOT 接受动作列表、动作次数、动作顺序、脚本、Prompt、模板、审批模式、force、七日时长、时区、分钟/小时公式、风控状态或安全闸字段。Facebook 慢启动中的 `collect`、`comment_like`、`dm_reply` SHALL 继续由代码固定为 0，MUST NOT 出现在可编辑 schema 中。为保持“逐日放开”语义，每个可编辑动作的 `dailyCap` 从第 1 天至第 7 天 MUST 单调不降。任一缺失、重复、越界、非整数、逐日下降或未知字段 MUST 使整个请求失败且不产生部分写入。

#### Scenario: 两个规则数字通过严格校验

- **WHEN** 内部管理员提交处于 Cloud 返回范围内的整数 `viewThreshold` 与 `joinEveryNRounds`
- **THEN** Cloud 接受这两个数字进入草稿校验
- **AND** 不从请求推导或接受任何动作与 Prompt 配置

#### Scenario: 零周期不能暗中关闭固定动作

- **WHEN** 请求把 `viewThreshold` 或 `joinEveryNRounds` 设为 0、负数、非整数或超出 Cloud 返回上限
- **THEN** Cloud 整块拒绝请求且草稿版本不推进
- **AND** 操作者只能通过既有 `enabled` 开关关闭模式，不能用数字删除固定动作

#### Scenario: 七日矩阵必须完整且封闭

- **WHEN** 慢启动请求缺少任一天或任一受支持动作、重复 day/action、增加第 8 天、携带 `collect` 或加入任意未知键
- **THEN** Cloud 返回逐字段校验错误并拒绝整个请求
- **AND** 已保存草稿与已发布版本逐位不变

#### Scenario: 每个动作不得随天数收紧

- **WHEN** 某动作第 4 天的 `dailyCap` 小于其第 3 天
- **THEN** Cloud 拒绝整个慢启动草稿并定位该递减单元格
- **AND** MUST NOT 通过保存较小后日值把“逐日放开”改成任意波动曲线

#### Scenario: 可编辑每日值不改变派生公式

- **WHEN** 管理员修改某一天某动作的 `dailyCap`
- **THEN** Cloud 只保存该每日天花板
- **AND** 分钟与小时天花板继续按既有 Cloud 公式派生，客户端不得提交覆盖值

### Requirement: 数字策略使用 CAS 草稿与不可变发布版本

每个策略族 SHALL 提供一个可编辑草稿、一个全局当前指针和单调递增、不可变的已发布 revision。草稿写入 MUST 携带 `expectedDraftVersion` 并返回规范化服务端真态；版本冲突 MUST 拒绝整次写入。发布 MUST 携带 `expectedDraftVersion` 与 `expectedPublishedRevision`，并在同一事务中重新执行完整 schema 校验、冻结类型值、推进该策略族的全局当前指针、记录 actor、requestId、说明和时间，再返回服务端生成的 revision identity。Console MUST NOT 生成 revision、schema version 或 definition id。

已发布 revision 及其数值 MUST NOT 原地更新或物理删除。规则与慢启动的草稿、revision 和全局当前指针 SHALL 相互独立；发布其中一个策略族 MUST NOT 为另一个策略族创建版本或改变其当前指针。恢复历史数值 SHALL 从历史 revision 建立新草稿并发布为新的单调 revision，MUST NOT 倒退指针或改写旧 revision。

#### Scenario: 并发草稿写入以 CAS 拒绝

- **WHEN** 两个管理员基于相同 `expectedDraftVersion` 编辑同一草稿且第一个写入已成功
- **THEN** 第二个写入以版本冲突失败并返回当前服务端草稿
- **AND** Cloud 不合并字段、不覆盖第一个管理员的值

#### Scenario: 发布前服务端再次校验

- **WHEN** 草稿在保存后因 schema 能力变化而不再满足当前完整校验
- **THEN** 发布失败且不产生 published revision、不推进全局当前指针

#### Scenario: 发布原子推进该类全局当前版本

- **WHEN** 一个合法草稿发布为新 revision
- **THEN** Cloud 在同一事务冻结新 revision 并把该策略族的全局当前指针推进到它
- **AND** 历史 revision、另一个策略族、在途规则进度与慢启动 active pin 均保持不变

#### Scenario: 历史数值通过新 revision 恢复

- **WHEN** 管理员从一个仍兼容的历史 published revision 建立草稿并发布
- **THEN** Cloud 生成高于当前版本号的新 revision 并推进当前指针
- **AND** MUST NOT 修改、删除或把当前指针直接倒退到历史 revision

### Requirement: 全局当前规则版本只在账号安全边界采用

规则模式数字 SHALL 只有一个 API owner 全局当前 revision，MUST NOT 提供客户级或环境级数字/版本覆盖。每个 automation execution target SHALL 只在完整原子应用 owner snapshot 后推进自己的 `appliedCurrentRevision` 与 `appliedCursor`。账号无活动批次且 collecting progress 为 0 时 SHALL 在下一次 admission 采用该 target 已应用、仍新鲜的 current revision；已有部分 collecting progress 或活动批次时 MUST 继续使用其持久快照直至该轮终态并清除 active-round pointer，下一轮才可采用更新的 applied current。publish commit MUST NOT 被表述为所有 target 已经应用。

规则 progress SHALL 保存 adopted revision、`viewThreshold` 与 `joinEveryNRounds` 快照；batch SHALL 保存同一 revision、两项数字、cycle position 与 `includesJoinContact`。这些持久快照连同独立的 definition schema identity SHALL 足以恢复和结算旧 revision 的在途工作，automation 镜像无需继续保留已经退出 current 的旧规则数值定义。重启、环境换绑、全局发布或历史投影 MUST NOT 依据当前全局数字重新解释这些事实；任一快照/identity 缺失或非法时 MUST 失败关闭。换绑后的新账号从 0 开始并采用该 target 当时已应用的 current revision，旧账号在途事实仍按自己的快照诚实收敛。

#### Scenario: 部分收集继续旧阈值

- **WHEN** 账号按 revision 7 已收集 3 个唯一确认 view，此时其 execution target 已应用 revision 8
- **THEN** 当前 collecting progress 继续按 revision 7 的阈值创建并结算这一轮
- **AND** 下一轮从 0 开始时才采用 revision 8

#### Scenario: 在途批次的周期位置不被重算

- **WHEN** 一个 batch 已按旧 revision 持久化 `includesJoinContact=false` 后全局周期数字发生变化
- **THEN** 重启与投影均继续把该 batch 的 join/comment 腿解释为不适用
- **AND** MUST NOT 用新的 `joinEveryNRounds` 重算历史或在途 batch

#### Scenario: 新账号不继承旧账号进度

- **WHEN** 规则模式环境从账号 A 换绑到账号 B
- **THEN** 账号 B 从 0 开始并采用换绑时其 execution target 已应用的 current revision
- **AND** 账号 A 的 progress、去重和在途 batch 不迁移到账号 B

### Requirement: 慢启动在开启时固定全局当前版本

慢启动数字 SHALL 只有一个全局当前 revision，MUST NOT 提供客户级或环境级数字/版本覆盖。Cloud 开启环境慢启动时 MUST 在同一事务写入对齐运营自然日的 `slow_start_since` 与当时全局当前 revision 的 active pin；当前版本缺失、陈旧或不兼容时整次开启 MUST 失败。重复开启 MUST 保持既有起点与 active pin，不得借幂等请求换版或重置 day。

第 1 至第 7 天 SHALL 始终使用 active pin 的完整策略。发布新全局 revision MUST NOT 改写正在慢启动环境的 active pin、day、since 或当日额度；关闭时 SHALL 原子清空 since 与 active pin，再次开启采用届时全局当前 revision。环境换绑账号 MUST 保留环境的 since 与 active pin。

#### Scenario: 发布不改变正在慢启动的环境

- **WHEN** 环境 E 正按 revision 4 处于第 3 天且全局当前发布为 revision 5
- **THEN** E 继续按 revision 4 完成七日生命周期
- **AND** 之后新开启的环境采用 revision 5

#### Scenario: 重复开启不换版

- **WHEN** 已开启环境再次收到 `{enabled:true}` 且全局当前 revision 已变化
- **THEN** Cloud 幂等返回原 since 与 active revision
- **AND** 不重置 day、不采用新 revision

#### Scenario: 关闭后重开采用届时当前版本

- **WHEN** 环境完成关闭后在全局当前 revision 变化后再次开启
- **THEN** Cloud 写入新的运营日起点并 pin 届时当前 revision
- **AND** 旧生命周期事实不得冒充新生命周期的 active pin

### Requirement: 发布必须复核影响预览与消费者兼容性

管理后台 SHALL 在发布前请求服务端影响预览。规则预览至少返回会在下一安全边界采用的账号数与仍按旧 revision 收敛的 collecting/batch 数；慢启动预览至少返回之后开启会采用新 revision 的环境范围与仍 pin 旧 revision 的在途环境数。这些易变计数 SHALL 携带 `asOf` 且只用于影响说明。预览 SHALL 另返回 API owner current、每个 DEV/OL execution target 的 applied current/cursor/lag、writer rollout phase/epoch、expected-instance-set coverage/freshness、基于规范化草稿/当前 published revision/runtime schema capability 的稳定 digest，以及受影响环境的 `facebook_mode_policy_projection_v1` 客户端能力 cohort。

发布请求 MUST 携带稳定 preview digest、`expectedDraftVersion` 与 `expectedPublishedRevision` 并在事务内复核。任一期望值/承重 digest 漂移、预览过期，DEV 或 OL 任一可能消费 runtime 未报告 schema 兼容、未通过 fresh authenticated health 证明永久 `reject_missing` 与完整 expected API/automation writer coverage，或规则模式受影响 cohort 中任一环境的客户端能力 missing/unsupported/stale 时，发布 MUST 整块拒绝，不推进共享全局当前指针。仅“旧 writer heartbeat 为零”不得替代完整实例集合证明；API 不得跨库查询 automation phase。慢启动的既有 active pin 不换版；其后每次 non-legacy enable 必须在 customer/admin/create-intent 入口检查该环境 30 天内的 fresh positive capability。账号 progress、batch 或环境 lifecycle 在 preview `asOf` 后自然变化 SHALL 在发布回包中刷新，但其计数变化本身 MUST NOT 制造无穷 CAS 冲突；安全边界/pin 语义继续承重。客户筛选 MAY 用于影响展示，但 MUST NOT 创建客户或环境配置层。

DEV 与 OL 共享业务 PostgreSQL，因此非默认发布 SHALL 被视为同时影响两端的全局行为变更；MUST NOT 以 DEV-only 发布作为验收手段。两端兼容 runtime 与客户端 cohort 未满足、或缺少明确全局发布授权时，系统 MAY 保存草稿并生成预览，但 publish writer MUST 保持关闭。发布成功后，target 在下一份完整 snapshot 应用前 MAY 继续使用其仍新鲜的旧 applied current；该传播窗口 SHALL 投影为 pending/lag，MUST NOT 冒充全体已采用。

publish writer SHALL 由 API 服务端强制执行且默认关闭。只有 request-serving process 满足 `AIDCP_DEPLOY_ENV=ol`、`AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_ENABLED=true` 和非空 `AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_CHANGE_REF` 时，发布请求才可继续经过全部既有校验；任何缺省、非法、DEV 或未标明 OL 的进程 MUST 返回 `policy_publish_disabled` 且 current 不变。gate 状态、target、build SHA、instance、changeRef 与 server observedAt SHALL 形成 append-only observation并出现在 Panel read/preview/health；发布审计 MUST 关联所用 observation。Console MUST NOT 提供 gate 开关或隐藏 override。恢复 revision 也只能经另行授权短时开启该 gate并走相同 preview/CAS/capability/idempotency/audit，不存在 bypass。

#### Scenario: 影响未漂移时发布

- **WHEN** 管理员确认一份当前且所有消费者兼容的影响预览
- **THEN** Cloud 原子创建 published revision、推进该类全局当前指针并写审计
- **AND** 回包返回完整写后服务端真态

#### Scenario: 预览后当前版本发生变化

- **WHEN** 另一个管理员先发布导致 `expectedPublishedRevision` 或预览 digest 失效
- **THEN** Cloud 返回冲突并拒绝整个发布
- **AND** 不创建孤立 published revision、不推进指针

#### Scenario: 旧消费者阻止新数字上线

- **WHEN** 任一可能消费目标尚未报告支持待发布 revision 的 schema version
- **THEN** 草稿保存与预览仍可用，但发布失败并列出不兼容目标
- **AND** 旧 runtime 不会继续按编译期数字执行却被管理面冒充为新策略

#### Scenario: DEV 不能单独推进共享 current

- **WHEN** DEV 已兼容但 OL 尚未部署 policy-aware runtime，或本次仅获得 DEV 验收授权
- **THEN** 草稿、校验、影响预览与隔离 fixture 可以执行，但 publish writer 保持关闭
- **AND** MUST NOT 推进共享 owner current 后再把 OL 另行决定

#### Scenario: 发布成功但 target 尚未应用

- **WHEN** owner current 已由 revision 7 推进到 8，而 OL automation 的 fresh snapshot 仍原子应用 revision 7
- **THEN** Panel 显示 owner current 8、OL applied current 7、对应 cursor 与 propagation lag
- **AND** OL 的零进度 admission 仍采用 revision 7，直至完整新 snapshot 原子应用

#### Scenario: 旧客户端能力阻止受影响规则策略发布

- **WHEN** 一个已开启规则模式、可能在下一安全边界采用新 revision 的环境没有 30 天内的 positive `facebook_mode_policy_projection_v1` 观察
- **THEN** preview 将该 envKey 列为 incompatible/unknown 且 publish 失败
- **AND** 管理员不得用口头确认或隐藏 override 绕过门禁

#### Scenario: DEV 或默认配置不能调用共享发布 writer

- **WHEN** publish route 运行于 DEV，或 OL API 未显式启用 gate/未提供 changeRef
- **THEN** 服务端返回 `policy_publish_disabled` 并保留 draft、published revision 与 owner current
- **AND** Panel 显示 gate 的具名关闭原因，MUST NOT 仅靠前端隐藏按钮

### Requirement: 管理后台以非乐观真态管理数字策略

Console SHALL 提供 `/mode-policies` 内部管理页面，分别呈现规则数字、固定七日每日额度、版本/审计与影响预览。慢启动编辑器 SHALL 固定为 7 天×7 个受支持动作，分钟/小时值只读展示 Cloud 规范化预览；规则编辑器 SHALL 只渲染两个数字字段。任何保存或发布操作在 Cloud 完整回包前 MUST 显示提交中且不得冒充成功，完成后 SHALL 以服务端真态刷新。

页面 SHALL 显示 draft/published/current/active/adopted 的不同含义、revision、actor、时间、freshness、兼容性和服务端 publish gate 的 enabled/target/changeRef presence/observedAt 与具名关闭原因；changeRef 的具体内部值 MAY 最小化展示。策略、镜像或 gate 未就绪时 MUST 显示具名不可用状态并禁用相应写操作，MUST NOT 用前端常量合成默认值。页面 MUST NOT 提供 publish gate、动作、Prompt、模板、安全闸、客户/环境覆盖或在途慢启动强制换版入口。

#### Scenario: 管理员只能看到批准的数字控件

- **WHEN** 管理员打开规则与慢启动策略编辑器
- **THEN** 页面只提供两个规则整数与固定七日七动作的 dailyCap 输入
- **AND** 不渲染动作编辑、Prompt、分钟/小时覆盖、风控或 force 控件

#### Scenario: 发布在途不冒充当前默认

- **WHEN** 发布请求尚未完成
- **THEN** Console 保留最近一次已确认版本并显示发布中
- **AND** 不把草稿标成已发布或全局当前

#### Scenario: 权威策略不可读

- **WHEN** Panel API 返回策略未知、镜像陈旧或 schema 不兼容
- **THEN** Console 显示具名不可用状态并阻止发布
- **AND** MUST NOT 回填代码内的 `5/2` 或本地七日表

### Requirement: 策略写入必须经过内部鉴权并保留完整审计

草稿、校验、发布、影响预览与审计读取 SHALL 只存在于内部 Panel JWT 域；customer JWT、Edge IPC 和未认证请求 MUST NOT 访问或代理这些接口。每个成功写入和拒绝的发布尝试 SHALL 关联可追踪 requestId；成功审计至少记录 actor、操作、kind、前后 revision、影响摘要、发布时间说明与时间。

审计响应 MUST NOT 返回 token、密钥、Prompt 内容或其它客户环境的非必要数据。客户与 Edge 只能获得自己环境运行所需的最小只读 owner-current、target-applied、adopted/active/next-enable envelope；不能读取草稿、历史版本列表/详情、其它环境、内部 current-pointer 管理元数据、影响统计、publish gate changeRef 或内部 actor。

#### Scenario: Customer JWT 尝试写策略

- **WHEN** 客户 token 调用任一内部数字策略草稿、预览、发布或审计接口
- **THEN** Cloud 拒绝请求且不泄露策略内容或是否存在

#### Scenario: 发布审计可定位变更

- **WHEN** 内部管理员成功发布一个 revision
- **THEN** 审计可关联 actor、requestId、规范化数字摘要、说明和时间
- **AND** 运行投影可独立区分仍使用旧 pin/快照与已采用该 revision 的对象

### Requirement: 初始版本与消费者兼容门禁保证零行为回归

迁移 SHALL 以当前实际运行真值创建 legacy published revisions：规则数字为 `viewThreshold=5`、`joinEveryNRounds=2`；Facebook 慢启动 dailyCap 逐格取迁移时 `FB_COLD_START_PLANS` 的运行上界，包括当前代码实际存在的第 3、4 天 `join_group=1`。注释与代码不一致 MUST 以运行代码为零回归依据，产品修正只能另发新 revision。

迁移 MUST 把两个全局当前指针设为对应 legacy revision，并保留环境开关、`slow_start_since`、规则收集进度、去重事实、批次、动作结果和 execution target；正在慢启动的 Facebook 环境 SHALL pin legacy slow-start revision，其它平台路径 MUST NOT 写入 Facebook pin；规则运行事实 SHALL 回填 migration-defined、跨 owner 稳定且不依赖数据库本地 sequence 的 legacy rule policy identity 与必要数字快照。数据库变更 SHALL 只追加新迁移；若允许范围超过现有 progress CHECK，必须显式扩展约束。旧消费者尚不能理解新 revision/schema 时，Cloud MAY 保存草稿和生成影响预览，但 MUST 拒绝发布。

expand SHALL 拆成带 ownership metadata 的 API-owner 与 automation-owner migrations，MUST NOT 用一份跨属主 migration 或跨库 trigger。API migration SHALL 创建 policy/current/pin 并安装 slow-start legacy bridge：trigger 与 publish CAS 锁定同一个 kind current row；API owner current 仍为 legacy 时，旧 writer 对 Facebook `slow_start_since` 的开启/关闭原子补齐/清除 legacy pin；current 成为 non-legacy 后，任何缺 pin 的旧开启写入 MUST 失败关闭，而 disable 始终原子清空 anchor+pin。automation migration SHALL 创建 rule snapshots、writer heartbeat 与按 `execution_target` 持久化的单向 rollout phase，初始为 `legacy_fill`；本库 rule trigger SHALL 对对应 phase row 做与切换事务冲突的锁定读，在该 phase 只补 migration-defined legacy identity、既有 definition identity 与 `5/2` 快照，在 `reject_missing` phase 拒绝任一缺字段写入。automation trigger MUST NOT 读取或推断 API owner current；phase/target 缺失、非法或 identity 不匹配均失败关闭，`reject_missing` 永久不得回到 `legacy_fill`。

每个 target 的 phase 切换 MUST 由 automation owner 以权威 deployment inventory 枚举该 target 所有 desired/restartable automation writer 实例，并要求集合中每个实例在既有 service-heartbeat TTL 内报告 policy-aware writer contract、允许的 build SHA、server `observedAt`/`freshUntil`，同时证明旧 artifact 已不再是可重启配置。仅“旧 writer heartbeat 为零”或只看到部分新实例 MUST NOT 作为覆盖证明。切换事务 SHALL 仅在 automation owner 内锁定 rollout phase、等待旧 rule 写事务退出、执行最终幂等 catch-up 与 target-scoped census，并仅在缺 rule policy/definition identity、numeric snapshot 与非法半行均为 0 时原子推进到 `reject_missing`。automation SHALL 通过既有 target health snapshot 向 API 投影 phase/epoch、expected-automation-instance-set digest、实例 coverage、build 与 freshness；API MUST NOT 跨库查询。API owner SHALL 用自己的权威 deployment inventory 与 heartbeat 独立证明 DEV/OL API writer coverage。strict consumer 与任何 non-legacy publish MUST 分别要求 DEV/OL 的 fresh `reject_missing` attestation 和完整 API writer coverage，任一 owner 不得代替另一 owner 出具证明。

#### Scenario: 升级后未发布新数字时行为逐位不变

- **WHEN** 数据迁移完成且两个全局当前指针、在途 pin 与规则快照均为 legacy revision
- **THEN** 规则模式继续按 `5/2`，慢启动继续按迁移前真实七日上界执行
- **AND** 既有起点、day、收集计数、批次和结果不被重置或补写动作

#### Scenario: 注释与运行表冲突时种子取运行真值

- **WHEN** 迁移发现注释声称 join 不早于第 5 天但当前 Facebook 运行表第 3、4 天上界为 1
- **THEN** legacy revision 的第 3、4 天 `join_group` dailyCap 均为 1
- **AND** 若产品要改为 0，必须另发新 revision

#### Scenario: automation legacy bridge 不跨 owner 数据库

- **WHEN** automation target 的 rollout phase 为 `legacy_fill`，旧 rule writer 写入缺少 policy identity 或数字快照的 progress/view fact/batch
- **THEN** automation 本库 trigger 使用 migration-defined legacy identity 与 `5/2` 快照原子补齐
- **AND** MUST NOT 连接 API 数据库、读取 owner current 或使用 automation 本地 sequence 伪造对应 revision

#### Scenario: 实例集合不完整阻止 phase 切换

- **WHEN** 只观察到没有 legacy heartbeat，但 automation deployment inventory 中任一 desired/restartable rule writer 缺少 fresh policy-aware heartbeat、build 不受允许或旧 artifact 仍可重启
- **THEN** target rollout phase 保持 `legacy_fill`，strict consumer 与 non-legacy publish 继续被阻止
- **AND** MUST NOT 用已观察实例的子集推断全部 writer 已升级

#### Scenario: reject phase 永久拒绝旧 rule writer

- **WHEN** target 已在锁定事务、零缺口 census 与完整实例 coverage 后推进到 `reject_missing`
- **THEN** 后续任何缺 policy identity、definition identity 或数字快照的 rule 写入失败关闭
- **AND** phase 永久不得回开，API 只通过 fresh target-attested health 读取该状态

#### Scenario: phase 切换与旧 rule INSERT 并发

- **WHEN** 旧 rule writer 在 target phase 从 `legacy_fill` 切到 `reject_missing` 的同时提交缺新字段 INSERT
- **THEN** phase-row 冲突锁使两笔事务串行化，INSERT 要么在切换前完整补 legacy snapshot，要么在切换后整笔失败
- **AND** MUST NOT 提交一个 phase 已为 `reject_missing` 却缺 policy/definition identity 或数字快照的半行

#### Scenario: owner current CAS 与旧 slow-start enable 并发

- **WHEN** 旧 API writer 在 slow-start owner current 从 legacy CAS 到 non-legacy 的同时写入 enable anchor 而不写 pin
- **THEN** current-row 冲突锁使 enable 要么在 CAS 前原子 pin legacy revision，要么在 CAS 后整笔失败
- **AND** MUST NOT 留下 non-NULL anchor 与 NULL pin，也不得在 CAS 后静默补 legacy pin

#### Scenario: 旧消费者阻止激活新 schema

- **WHEN** 任一可能消费目标尚未报告支持待发布 revision 的 schema version
- **THEN** 发布失败并返回不兼容目标
- **AND** 旧 reader 不会把新引用误解为编译期 `5/2` 后继续执行

### Requirement: 非 legacy 引用建立不可回退的 policy-aware runtime 地板

迁移与不可变历史 MUST NOT 回滚。policy-aware reader/schema 是永久运行地板，API/automation 在任何时候都 MUST NOT 回退到不理解 policy revision、numeric snapshot 或 active pin 的 pre-policy 版本。回滚 SHALL 先关闭 writer；必要时经另行授权短时开启同一 OL publish gate，正常发布使用 legacy 数字的新恢复 revision后立即关闭，并持续投影 owner/applied current 与所有 non-legacy 引用数量。恢复 revision 已传播且这些引用全部排空或结算，只允许回退到仍满足 policy-aware schema 的兼容版本，不会重新允许 pre-policy runtime。

#### Scenario: 非 legacy active pin 阻止旧 runtime 回滚

- **WHEN** 任一环境仍持有非 legacy slow-start active pin，或任一规则 progress/batch 仍引用非 legacy snapshot
- **THEN** readiness 标记 rollback floor 未满足并阻止部署 pre-policy runtime
- **AND** MUST NOT 通过回滚迁移、删除 revision 或改写 pin 来制造可回退状态
