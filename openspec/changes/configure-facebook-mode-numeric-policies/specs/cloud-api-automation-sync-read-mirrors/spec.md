## MODIFIED Requirements

### Requirement: 4b 必须封闭且仅封闭十一组同步读缺口

系统 SHALL 以 `aidcp-cloud@67941e4` 的组合根消费点为准，维护 api 六组与 automation 五组同步依赖的穷举清单。4b MUST NOT 重复 3a/3b 已交付的异步 owner route、受限恢复、审批触发或面板事件，也 MUST NOT 将 4a 的异步 authority 端口并入本 change。

api 六组 SHALL 是：全局 `weekActiveMask`、排期自动化静态目录、Edge presence 三读 `edgeCount` / `onlineEdgeCount` / `resolveEdgeIdForAccount`、publish in-flight ids、captcha availability、分域 config-mirror health。

automation 五组 SHALL 是：persona/binding/soul、client-environment automation gate（包含 slow-start anchor/active pin、Facebook 规则 enablement、两类 owner current 数字策略、所有仍被 active slow-start pin 引用的不可变定义，以及 env-scoped Edge policy capability positive/negative observation 与 freshness）、每进程 config freshness runtime、账号身份/状态、四张 api-owner 业务配置。数字策略与 capability observation 属于既有 client-environment automation gate 的扩展，MUST NOT 借用 content-schedule mirror/version，也 MUST NOT 新增一条未登记的第十二组同步热读。旧规则 revision 的在途结算 SHALL 依赖 progress/batch 自身持久的完整 numeric snapshots，而不是把全部历史规则 revision 加入该镜像。

`resumeEdgesForAccount` 会改变 automation 的 paused-edge 内存态，MUST NOT 进入 A3 snapshot 或本地镜像。它 SHALL 由 4a 提供独立 api → automation command，验证本地 target、内部 Bearer 与稳定 requestId，保持幂等，并将明确结果、拒绝、transport unavailable 与写后响应丢失的 `result_unknown` 分开。

#### Scenario: 边界 census 精确匹配十一组

- **WHEN** 对 api/automation 受管组合根运行同步跨属主读 census
- **THEN** 每条结果 MUST 映射到上述一个且仅一个 inventory 编号
- **AND** Facebook 数字策略只作为 client-environment automation gate 完整 payload 的闭合成员，不形成 ambient 第十二读

#### Scenario: 新增未登记同步跨属主读

- **WHEN** 组合根新增一个同步读取另一属主运行时或存储的调用点
- **THEN** 穷举边界检查 MUST 失败
- **AND** 实现 MUST 先为其明确 owner、投影形态、新鲜度档位与 unknown 语义

#### Scenario: API 请求恢复账号 Edge

- **WHEN** API 因面板或飞书账号恢复动作需要调用 `resumeEdgesForAccount`
- **THEN** 它 SHALL 使用 4a 的 authenticated target-bound automation command
- **AND** 4b presence mirror MUST NOT 删除 paused edge、推算恢复数或把未知结果当零

### Requirement: api-owner 事实必须落入 automation 本域投影

系统 SHALL 由 api owner internal route 为 persona、client environment gate/slow-start/Facebook mode numeric policies、账号身份/状态以及 content schedule、hot-lead、Facebook comment、Facebook join 配置提供全量 snapshot，由 automation 在自己的内存或属主数据库中原子应用。这些业务事实与 projection payload SHALL 在 DEV/OL 间共享，并复用现有 `config_mirror_version`/owner version；相关 mutation SHALL 在 owner 事务内推进对应现有 key，MUST NOT 新建 target-scoped 业务 revision 或复制两份 projection 内容。每个 execution target 只保存自己的 `appliedCursor`、`appliedCurrentRevision`、applied digest 与 freshness 作为消费状态，不把它们冒充另一份业务 current。automation MUST NOT 连接 api 数据库或在热读路径调用 HTTP。

client-environment automation snapshot SHALL 在同一个 repeatable-read/cursor 中完整携带环境 slow-start anchor 与 active pin、环境规则 enablement、两个 owner current revision 的严格类型定义、所有仍被 active slow-start pin 引用的旧不可变定义，以及每个环境最新 capability observation 的 `supported`、server `observedAt`、`freshUntil`。snapshot 原子应用成功时 SHALL 一起推进该 target 的 `appliedCursor`、两类 `appliedCurrentRevision`、capability facts、digest 与 freshness；publish owner current 或 API capability mutation 本身 MUST NOT 直接改写 target applied 状态。引用缺定义、定义非法、capability observation 非法、同 cursor payload 漂移或 policy schema 不兼容时 MUST 拒绝整份 snapshot且不推进 cursor/freshness。规则配置、数字策略与 capability MUST NOT 继续通过 content-schedule mirror key 刷新或作为其 ready 状态的附带值。

#### Scenario: api-owner 写入后投影刷新

- **WHEN** api owner 成功提交一项 persona、environment、account、Facebook 数字策略或业务配置变更
- **THEN** 对应共享 owner version SHALL 在同一 owner 事务内前进
- **AND** automation 下一次 snapshot 应用后 SHALL 以同步本地读看到新值

#### Scenario: owner current 与 target applied current 在传播窗口分开

- **WHEN** policy publish 已推进 owner current，但某 target 尚未原子应用携带该 revision 的下一份 snapshot
- **THEN** 该 target 保持原 applied current/cursor 并投影 propagation lag
- **AND** 其 admission 只能采用仍 fresh 的 applied current，MUST NOT 直接读取 owner current 或声称新 revision 已应用

#### Scenario: owner 写入回滚

- **WHEN** api owner 的业务 mutation 回滚
- **THEN** 对应 snapshot revision MUST NOT 前进
- **AND** automation MUST NOT 观察到只存在 revision 而不存在业务值的半提交

#### Scenario: policy 引用与定义原子应用

- **WHEN** snapshot 同时包含环境 active revision 和其不可变七日定义
- **THEN** automation 原子应用引用、定义、cursor 与 freshness
- **AND** MUST NOT 先应用引用再等待另一条流补定义

#### Scenario: capability 与 policy adoption gate 同 cursor 应用

- **WHEN** snapshot 为某环境携带 non-legacy applied current 与最新 positive/negative capability observation
- **THEN** automation 原子应用 policy、observation、cursor 与 freshness，并只用这份本地 gate fact 裁决安全边界 adoption
- **AND** MUST NOT 直连 API 数据库、在热路径调用 HTTP，或沿用被更新 negative observation 撤销的旧 positive

#### Scenario: 旧规则轮次不依赖历史定义镜像

- **WHEN** owner current 已推进，而某账号仍有引用旧 rule revision 的非零 progress 或 active batch
- **THEN** automation 使用该 progress/batch 持久的 revision、definition identity、两项 numeric snapshots 与 `includesJoinContact` 继续结算
- **AND** snapshot 不需要保留该旧 rule definition；任一持久快照非法时失败关闭而不改用 current

#### Scenario: automation 无法刷新 api-owner 投影

- **WHEN** api route 不可达或 projection apply 失败
- **THEN** automation MUST 保留最后好值但 MUST NOT 延长其 freshUntil 或推进 cursor
- **AND** 到达陈旧上限后所有 gate 读 SHALL fail-closed

### Requirement: gate 镜像陈旧必须停手，parameter 镜像只能沿用最后好值

系统 SHALL 复用 `CONFIG_MIRRORS` 的 gate/parameter 分类和既有陈旧上限。client-environment/Facebook mode numeric policy SHALL 登记为 gate，因为较低阈值或由 0 变正的额度可以更早准入真实平台动作。gate stream 在 uninitialized、stale 或 invalid 时 MUST 拒绝新的平台动作；parameter stream 只有在至少成功装载过一次后才可沿用最后好值，并 SHALL 告警与投影 stale。consumer 只有在当前 authenticated owner fetch 成功生成更晚 snapshot observation 时才能续镜像 transport/policy freshness，MUST NOT 由本地读或历史 envelope 自行延长。

镜像 transport/policy freshness 与 payload 内某环境的 Edge capability observation freshness SHALL 独立裁决。一份 transport/policy 仍新鲜且结构合法的 snapshot MAY 携带 missing、`supported=false` 或已过期 positive observation；这些状态 MUST 保持为有效的本地事实，只阻止该环境后续 non-legacy enable/adoption，不得把整份镜像标为 stale，也不得单独停止已固定 active pin 或已采用 revision 的运行。只有 capability payload 结构非法才拒绝整份 snapshot；capability 状态变化仍须随新的 owner cursor 原子应用。

#### Scenario: client environment automation transport 或 policy gate 陈旧

- **WHEN** `client_environment_automation_gate` 的 transport/policy snapshot、slow-start anchor/pin 或 Facebook mode policy 陈旧
- **THEN** automation MUST 拒绝开始或推进受影响的新规则/慢启动平台动作
- **AND** MUST NOT 把未知 gate 当 allowed、把未知 slow-start 当“不限”或回落编译期数字

#### Scenario: fresh snapshot 携带 negative 或过期 capability

- **WHEN** automation 原子应用了一份 transport/policy 仍新鲜的 snapshot，而某环境的 capability observation 为 missing、`supported=false` 或 positive 已过期
- **THEN** automation MUST 只阻止该环境后续 non-legacy revision adoption，并投影精确 capability blocker
- **AND** 已有 slow-start active pin 或规则 adopted revision 仍可在其它 transport/policy/risk/safety gate 通过时继续运行，MUST NOT 因 capability 状态单独中断

#### Scenario: 业务配置 gate 陈旧

- **WHEN** content schedule、Facebook comment 或 Facebook join enablement 的镜像陈旧
- **THEN** 对应 scheduler SHALL 停止领取/开始新的平台动作并记录具名 stale reason
- **AND** 已经执行中的动作按既有自然收敛路径结束

#### Scenario: 数字策略 last-good 不得无限承重

- **WHEN** automation 曾成功装载 Facebook 数字策略但 snapshot 已超过 freshUntil
- **THEN** health MAY 显示完整 last-good revision 供诊断，但新规则/慢启动平台动作 MUST 停止
- **AND** MUST NOT 把该 gate 降级成 parameter 后继续执行

#### Scenario: hot-lead 参数镜像刷新失败

- **WHEN** hot-lead parameter 曾成功装载但之后刷新失败
- **THEN** automation MAY 沿用最后好值
- **AND** health/告警 MUST 显示 stale，MUST NOT 宣称刷新成功或改用代码默认

### Requirement: 配置镜像健康必须按消费进程分域并保留传输新鲜度

api SHALL 直接投影 api 本地 refresher health；automation SHALL 生成只描述 automation 本地镜像的 health snapshot。面板聚合 SHALL 带 `sourceService`、source `asOf` 与 delivery state。automation health 的 delivery 已陈旧时，api MUST 将该整段标为 unavailable，而不是继续展示旧条目为 fresh。

automation health snapshot SHALL 另外按 execution target 携带本库 `facebook_rule_policy_writer_rollout` 的 phase/epoch、权威 expected desired/restartable instance-set digest、每个实例的 build SHA/writer contract version/observedAt/freshUntil、coverage 结论及最后零缺口 census 时间。API SHALL 只消费经既有 authenticated health transport 收到且自身 delivery 仍 fresh 的 target attestation，不得连接 automation 数据库或从缺失实例、旧 payload、单个进程或“legacy heartbeat 为零”推断全部 writer 已升级。任何 non-legacy publish SHALL 要求 DEV/OL attestation 均为不可回退的 `reject_missing`、集合 coverage 完整，并另行要求 API owner 的 expected writer instance set 在既有 service-heartbeat TTL 内全部报告 policy-aware contract。

#### Scenario: automation health 传输陈旧

- **WHEN** api 上一次收到的 automation health snapshot 已超过 freshUntil
- **THEN** 面板 SHALL 将 automation health 与 writer rollout attestation 标为 unavailable/stale
- **AND** 即使 payload 内旧条目写着 fresh 或 `reject_missing`，也 MUST NOT 对外宣称 automation 镜像健康或允许 non-legacy publish

#### Scenario: api 本地与 automation 远端状态不同

- **WHEN** api 本地镜像 fresh 而 automation 某 gate mirror stale
- **THEN** 面板 SHALL 分别展示两个 source service 的真态
- **AND** MUST NOT 聚合成一个全局 fresh 结论

#### Scenario: writer 实例 coverage 不完整

- **WHEN** target health 只覆盖 expected instance set 的子集，任一 heartbeat 超过既有 TTL，build/contract 不受允许，或旧 artifact 仍在 restartable deployment inventory 中
- **THEN** target writer readiness SHALL 为 unavailable/incompatible，phase 即使已记录也不得满足发布门禁
- **AND** API MUST NOT 跨库补查或用 observed legacy count 为零替代完整集合证明

### Requirement: 十一组依赖必须采用各自裁定的最小本地读形态

实现 SHALL 按 inventory 逐项采用下列最小形态，MUST NOT 为方便而把整份 owner store、连接池、密钥或无消费者字段跨进程复制：

- `weekActiveMask`：api 本地单值镜像；
- 排期自动化目录：kernel 编译期静态表与纯 reader；
- Edge presence：api 本地计数与 account→edge 索引，绝不包含 `resumeEdgesForAccount`；
- publish in-flight：api 本地 recordId 集合；
- captcha：api 本地 capability 状态；
- health：api 本地 health 加 automation health snapshot；
- persona：automation 本地 account→binding/persona/soul 查表；
- environment gate/slow-start/Facebook mode policy：automation 本域 environment projection、两个 target-applied current 定义、active slow-start pin 所需不可变定义、env-scoped capability positive/negative observation 及 applied cursor/digest；
- freshness runtime：每进程本地实例；
- account identity/status：扩展 automation account projection；
- 四张业务配置：automation 本地配置镜像。

#### Scenario: 排期目录装配

- **WHEN** api 构造 `ContentScheduleStore`
- **THEN** `ScheduledAutomationCatalogReader` SHALL 来自与 automation 相同版本的 kernel 静态目录
- **AND** MUST NOT 发 HTTP、建立投影表或从 automation 运行时复制该编译期表

#### Scenario: config freshness 装配

- **WHEN** api 或 automation 以独立进程运行并持有远端事实镜像
- **THEN** 该进程 SHALL 安装只描述本进程镜像的本地 freshness runtime
- **AND** MUST NOT 通过网络同步调用另一进程的 ambient singleton

#### Scenario: 账号投影用于目标解析

- **WHEN** automation 按昵称或平台解析账号用于真实命令
- **THEN** 它 SHALL 只读 fresh 的本域 account projection 并保留歧义
- **AND** 缺行、陈旧或多匹配 MUST NOT 猜测目标

#### Scenario: 模式策略最小投影不泄露管理域

- **WHEN** automation 消费 client-environment automation snapshot
- **THEN** payload 只含执行所需 published revisions、owner current/active 引用、数值、schema/freshness 与 capability supported/observedAt/freshUntil，consumer 本地另记 applied current/cursor/digest
- **AND** 不包含草稿、审计 actor、Panel JWT、客户密钥或 Console 影响预览
