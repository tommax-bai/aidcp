## ADDED Requirements

### Requirement: 4b 必须封闭且仅封闭十一组同步读缺口
系统 SHALL 以 `aidcp-cloud@67941e4` 的组合根消费点为准，维护 api 六组与 automation 五组同步依赖
的穷举清单。4b MUST NOT 重复 3a/3b 已交付的异步 owner route、受限恢复、审批触发或面板事件，
也 MUST NOT 将 4a 的异步 authority 端口并入本 change。

api 六组 SHALL 是：全局 `weekActiveMask`、排期自动化静态目录、Edge presence 三读
`edgeCount` / `onlineEdgeCount` / `resolveEdgeIdForAccount`、
publish in-flight ids、captcha availability、分域 config-mirror health。
automation 五组 SHALL 是：persona/binding/soul、client-environment automation gate 与
slow-start anchor、每进程 config freshness runtime、账号身份/状态、四张 api-owner 业务配置。

`resumeEdgesForAccount` 会改变 automation 的 paused-edge 内存态，MUST NOT 进入 A3 snapshot 或本地镜像。
它 SHALL 由 4a 提供独立 api → automation command，验证本地 target、内部 Bearer 与稳定 requestId，
保持幂等，并将明确结果、拒绝、transport unavailable 与写后响应丢失的 `result_unknown` 分开。

#### Scenario: 边界 census 精确匹配十一组
- **WHEN** 对 api/automation 受管组合根运行同步跨属主读 census
- **THEN** 每条结果 MUST 映射到上述一个且仅一个 inventory 编号
- **AND** 3a/3b/4a 的契约方法 MUST NOT 出现在 4b 镜像成员清单

#### Scenario: 新增未登记同步跨属主读
- **WHEN** 组合根新增一个同步读取另一属主运行时或存储的调用点
- **THEN** 穷举边界检查 MUST 失败
- **AND** 实现 MUST 先为其明确 owner、投影形态、新鲜度档位与 unknown 语义

#### Scenario: API 请求恢复账号 Edge
- **WHEN** API 因面板或飞书账号恢复动作需要调用 `resumeEdgesForAccount`
- **THEN** 它 SHALL 使用 4a 的 authenticated target-bound automation command
- **AND** 4b presence mirror MUST NOT 删除 paused edge、推算恢复数或把未知结果当零

### Requirement: 远端事实必须以带 target 和单调 cursor 的完整快照交付
每个跨进程同步读 stream SHALL 以完整 snapshot 作为承重面。snapshot MUST 包含
`contractVersion`、server-injected `executionTarget`、`factScope=shared|target`、闭集合 `stream`、
owner fact scope 内单调不透明
`cursor`、`asOf`、`freshUntil`、`complete:true` 与已校验 payload。payload 与 cursor MUST 来自
同一一致读边界；cursor SHALL 按无符号整数语义比较而非字符串字典序。调用方提供的 target
MUST NOT 覆盖 server target。

#### Scenario: 消费方收到有效的新快照
- **WHEN** snapshot 的 target 等于本进程 target、contractVersion 受支持、结构完整且 cursor 大于已应用值
- **THEN** 消费方 SHALL 原子应用整份 payload 与其 cursor/freshness 元数据
- **AND** 同步读只能在原子提交之后看到新值

#### Scenario: 快照 target 不匹配
- **WHEN** dev 消费方收到标记为 ol 的 snapshot
- **THEN** 消费方 MUST 拒绝整份 snapshot 且 MUST NOT 推进 dev cursor 或 freshUntil
- **AND** ol 的 projection/cursor MUST 保持不受影响

#### Scenario: 空 payload 不能冒充完整真态
- **WHEN** owner 响应空 payload 但未明确给出 `complete:true`，或该 stream 不允许空稳态
- **THEN** 消费方 MUST 拒绝响应并保留最后好值
- **AND** MUST NOT 将空数组、false、null 或零写成新的权威结果

### Requirement: api-owner 事实必须落入 automation 本域投影
系统 SHALL 由 api owner internal route 为 persona、client environment gate/slow-start、账号身份/状态
以及 content schedule、hot-lead、Facebook comment、Facebook join 配置提供全量 snapshot，
由 automation 在自己的内存或属主数据库中原子应用。这些业务事实与 projection payload SHALL 在
DEV/OL 间共享，并复用现有 `config_mirror_version`/owner version；相关 mutation SHALL 在 owner
事务内推进对应现有 key，MUST NOT 新建 target-scoped 业务 revision 或复制两份 projection 内容。
automation MUST NOT 连接 api 数据库或在热读路径调用 HTTP。

#### Scenario: api-owner 写入后投影刷新
- **WHEN** api owner 成功提交一项 persona、environment、account 或业务配置变更
- **THEN** 对应共享 owner version SHALL 在同一 owner 事务内前进
- **AND** automation 下一次 snapshot 应用后 SHALL 以同步本地读看到新值

#### Scenario: owner 写入回滚
- **WHEN** api owner 的业务 mutation 回滚
- **THEN** 对应 snapshot revision MUST NOT 前进
- **AND** automation MUST NOT 观察到只存在 revision 而不存在业务值的半提交

#### Scenario: automation 无法刷新 api-owner 投影
- **WHEN** api route 不可达或 projection apply 失败
- **THEN** automation MUST 保留最后好值但 MUST NOT 延长其 freshUntil 或推进 cursor
- **AND** 到达陈旧上限后所有 gate 读 SHALL fail-closed

### Requirement: automation-owner 动态事实必须由完整 snapshot 承重并由 event outbox 加速
系统 SHALL 由 automation owner 为全局周掩码、Edge presence、publish in-flight、captcha availability
与 automation config-mirror health 生成 runtime snapshot。状态变化 SHALL 向
automation 属主 `event_outbox` 写入 target-scoped `sync_read.changed` 通知；通知仅作唤醒和积压重放，
完整 snapshot SHALL 是崩溃恢复与漏通知自愈的承重来源。

#### Scenario: runtime 状态变化触发快速刷新
- **WHEN** automation 的 Edge presence、in-flight、captcha 或 health generation 前进
- **THEN** automation SHALL 为同一 target/stream 写入或合并一条持久 outbox 通知
- **AND** api 收到通知后 SHALL 拉取不低于该 generation 的完整 snapshot

#### Scenario: outbox 通知丢失但周期 snapshot 成功
- **WHEN** 状态已经变化但通知写入或 LISTEN 唤醒失败
- **THEN** api SHALL 由下一轮完整 snapshot 收敛到 owner 当前值
- **AND** 系统 MUST NOT 依赖每条 runtime delta 都曾成功投递

#### Scenario: outbox handler 未成功应用快照
- **WHEN** api 因结构、target、网络或 apply 错误未成功应用相应 snapshot
- **THEN** automation 的 `(consumer,target,topic)` cursor MUST 停在该通知之前
- **AND** 后续轮询 SHALL 重放积压而不是确认丢弃

### Requirement: 本地镜像应用必须幂等、不回退且可从断链积压恢复
每个 `(executionTarget, stream)` 的消费状态 SHALL 持久记录 applied cursor、source `asOf`、
`freshUntil`、last applied time 与 last error。同 cursor 重放 SHALL 幂等；旧 cursor、
未知 contractVersion、非法 cursor 或不完整 payload MUST NOT 覆盖现值。

#### Scenario: 相同 snapshot 重放
- **WHEN** 消费方再次收到已应用 cursor 的同一完整 snapshot
- **THEN** 消费方 SHALL 返回 already-applied 并保持值与 cursor 不变
- **AND** outbox 可据该确认安全推进

#### Scenario: 相同 cursor 的新 owner observation 续鲜
- **WHEN** 消费方通过当前已鉴权 owner fetch 得到相同 cursor、相同 payload digest 且更晚 `asOf` 的 snapshot
- **THEN** 消费方 SHALL 保持 payload/cursor 不变，只推进本实例 `lastObservedAt/freshUntil`
- **AND** 该成功 observation SHALL 与事实长期未变化保持兼容

#### Scenario: 历史 envelope 不得续鲜
- **WHEN** 相同 cursor 的 envelope 来自重试/重放且 `asOf` 未前进，或相同 cursor 的 payload 已漂移
- **THEN** 前者 SHALL 幂等确认但 MUST NOT 延长 freshness，后者 SHALL 标记 invalid
- **AND** 两者均 MUST NOT 让已陈旧实例重新 ready

#### Scenario: 乱序旧快照到达
- **WHEN** snapshot cursor 小于本地 applied cursor
- **THEN** 消费方 MUST 拒绝回退且 MUST NOT 清空当前镜像
- **AND** health SHALL 记录 out-of-order 诊断

#### Scenario: 进程跨多条事件断链后恢复
- **WHEN** 消费方停机期间 owner 累积多条通知并在之后重连
- **THEN** 消费方 SHALL 先应用 owner 当前完整 snapshot，再从持久 cursor 恢复 replay
- **AND** 重复通知 SHALL 被 cursor/generation 幂等吸收，最终值 MUST 等于 owner 当前快照

### Requirement: 首次装载与恢复必须经过显式 ready gate
独立 api/automation 进程 SHALL 为 required streams 维护
`uninitialized | ready | stale | invalid | recovering` 状态。业务 readiness 只有在全部 required
streams 已成功首次装载、target/contract 校验通过且 required gate streams 尚未陈旧时才能为 ready。
D1 明确要求首装的 parameter stream SHALL 进入 required 集合。
listener 启动或 liveness 成功 MUST NOT 被解释为镜像 ready。

#### Scenario: 独立 automation 缺 persona 初始快照
- **WHEN** automation listener 已启动但从未成功装载 persona stream
- **THEN** liveness MAY 成功但 business readiness MUST 失败并列出 persona 阻塞
- **AND** dispatcher、scheduler 与 Edge push MUST NOT 开始新平台动作

#### Scenario: 独立 api 缺 Edge presence 初始快照
- **WHEN** api 尚未应用有效 presence snapshot
- **THEN** api MUST NOT 将 edgesOnline 投影为 0 或把账号判为无活体 Edge
- **AND** 依赖 presence 的 D5、preflight 或 offboard 动作 SHALL 返回 unknown/unavailable

#### Scenario: 真实 monolith 使用本地权威
- **WHEN** `AIDCP_SERVICE` 未设置且 owner 与 consumer 确实组装在同一进程
- **THEN** 组合根 MAY 使用显式标记为 `local-authority` 的同步 adapter
- **AND** 独立服务模式 MUST NOT 以该分支把缺失 remote mirror 当作 ready

### Requirement: unknown、stale 与业务否值必须保持可区分
同步镜像 SHALL 将值与读取状态分离。`0`、`false`、`[]`、`null`、unbound、normal 或 disabled
只有在 owner 明确确认时才是业务值；从未装载、源不可达、target 不明、结构无效或超时
MUST 表达为 unknown/stale，而非上述业务值。

#### Scenario: Edge presence 陈旧
- **WHEN** presence snapshot 超过 freshUntil
- **THEN** 面板 MUST 显示 presence unavailable/stale 而不是 0 个在线 Edge
- **AND** 账号到 Edge 解析、preflight 与下发 SHALL fail-closed

#### Scenario: persona 行缺失与镜像未知
- **WHEN** 一份 fresh 且 complete 的 persona snapshot 明确不含某账号
- **THEN** 消费方 MAY 将该账号判为 unbound
- **AND** 当 snapshot 本身 uninitialized/stale/invalid 时 MUST 返回 unknown 而不是 unbound

#### Scenario: publish in-flight 镜像未知
- **WHEN** api 无法确认当前 in-flight ids
- **THEN** 发布 lifecycle MUST 显式标记 in-flight 状态不可用
- **AND** MUST NOT 将批准记录显示为“未下发”或用空集合补造结论

#### Scenario: captcha 显式关闭
- **WHEN** owner snapshot 明确报告 captcha capability 因配置 disabled
- **THEN** api SHALL 将其视为已知 disabled
- **AND** 未收到 snapshot 时 MUST 保持 unknown，不能同样解释为 disabled

### Requirement: gate 镜像陈旧必须停手，parameter 镜像只能沿用最后好值
系统 SHALL 复用 `CONFIG_MIRRORS` 的 gate/parameter 分类和既有陈旧上限。gate stream 在
uninitialized、stale 或 invalid 时 MUST 拒绝新的平台动作；parameter stream 只有在至少成功装载过
一次后才可沿用最后好值，并 SHALL 告警与投影 stale。consumer 只有在当前 authenticated owner fetch
成功生成更晚 observation 时才能续 freshness，MUST NOT 由本地读或历史 envelope 自行延长。

#### Scenario: client environment automation gate 陈旧
- **WHEN** `client_environment_automation_gate` 或 slow-start snapshot 陈旧
- **THEN** automation MUST 拒绝向对应 Edge 推送新动作
- **AND** MUST NOT 把未知 gate 当 allowed 或把未知 slow-start 当“不限”

#### Scenario: 业务配置 gate 陈旧
- **WHEN** content schedule、Facebook comment 或 Facebook join enablement 的镜像陈旧
- **THEN** 对应 scheduler SHALL 停止领取/开始新的平台动作并记录具名 stale reason
- **AND** 已经执行中的动作按既有自然收敛路径结束

#### Scenario: hot-lead 参数镜像刷新失败
- **WHEN** hot-lead parameter 曾成功装载但之后刷新失败
- **THEN** automation MAY 沿用最后好值
- **AND** health/告警 MUST 显示 stale，MUST NOT 宣称刷新成功或改用代码默认

### Requirement: 十一组依赖必须采用各自裁定的最小本地读形态
实现 SHALL 按 inventory 逐项采用下列最小形态，MUST NOT 为方便而把整份 owner store、连接池、
密钥或无消费者字段跨进程复制：

- `weekActiveMask`：api 本地单值镜像；
- 排期自动化目录：kernel 编译期静态表与纯 reader；
- Edge presence：api 本地计数与 account→edge 索引，绝不包含 `resumeEdgesForAccount`；
- publish in-flight：api 本地 recordId 集合；
- captcha：api 本地 capability 状态；
- health：api 本地 health 加 automation health snapshot；
- persona：automation 本地 account→binding/persona/soul 查表；
- environment gate/slow-start：automation 本域 environment projection；
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

### Requirement: 配置镜像健康必须按消费进程分域并保留传输新鲜度
api SHALL 直接投影 api 本地 refresher health；automation SHALL 生成只描述 automation 本地镜像的
health snapshot。面板聚合 SHALL 带 `sourceService`、source `asOf` 与 delivery state。
automation health 的 delivery 已陈旧时，api MUST 将该整段标为 unavailable，而不是继续展示旧条目
为 fresh。

#### Scenario: automation health 传输陈旧
- **WHEN** api 上一次收到的 automation health snapshot 已超过 freshUntil
- **THEN** 面板 SHALL 将 automation health 标为 unavailable/stale
- **AND** 即使 payload 内旧条目写着 fresh，也 MUST NOT 对外宣称 automation 镜像健康

#### Scenario: api 本地与 automation 远端状态不同
- **WHEN** api 本地镜像 fresh 而 automation 某 gate mirror stale
- **THEN** 面板 SHALL 分别展示两个 source service 的真态
- **AND** MUST NOT 聚合成一个全局 fresh 结论

### Requirement: 持久投影、outbox 与 cursor 必须按 deployment target 隔离
系统 SHALL 让 target-specific runtime snapshot、async outbox、topic cursor、消费实例 readiness/health、
重放与清理带 server-injected `execution_target`。缺失或非法 `AIDCP_DEPLOY_ENV` 时相关 worker MUST 禁用并令
business readiness 失败。persona/account/environment/config 事实、现有 owner version 与 projection
payload SHALL 继续共享，不加 target 过滤；它们 SHALL 标记 `factScope=shared`，但每个 target 的
delivery cursor/readiness/health 保持独立。

#### Scenario: dev 与 ol 使用相同业务 id
- **WHEN** dev 与 ol 对相同 accountId/recordId 分别生成 snapshot 或事件
- **THEN** target-specific runtime stream SHALL 使用独立 payload/cursor，shared stream MAY 读取同一事实版本
- **AND** 两类 stream 的消费 cursor/readiness/health 均按实例隔离，任一 target 的确认或清理 MUST NOT 改写另一实例状态

#### Scenario: deployment target 缺失
- **WHEN** 独立镜像 worker 启动时 `AIDCP_DEPLOY_ENV` 缺失或非法
- **THEN** worker MUST NOT 拉取、应用、确认或清理任何 stream
- **AND** 服务 health SHALL 报告 target_invalid 且 business readiness 不通过

### Requirement: 4b 热点实现必须等待 4a 并按 post-4a census 单写
系统 SHALL 允许公共 snapshot envelope、kernel 静态目录、transport 基元和本地
freshness/apply runtime 与 4a 并行实现。B1/B2/B4 的 owner mutation、`AccountRosterSourcePort`、`automation_account_projection`
和 `server.ts` composition root MUST 等 4a landed 后重新 census，并由 4b 单写者修改。
4a 已移到 API notification exit 的 display-name consumer MUST 从 4b payload 删除。

#### Scenario: 4a 尚未落地主分支
- **WHEN** 4b 并行分支准备修改 roster、persona/environment/account mutation 或 composition root
- **THEN** 该项 SHALL 保持 blocked，仅公共 contract/runtime 工作 MAY 继续
- **AND** MUST NOT 让两个 change 同时写同一 owner port/root 后再依赖冲突合并猜语义

#### Scenario: 4a landed 后重跑 census
- **WHEN** 4a 已落地并移动 notification/card 与 account roster 消费点
- **THEN** 4b SHALL 以新默认分支重新生成 B1/B2/B4 消费字段与写路径清单
- **AND** 已无 automation 消费者的 display/card 字段 MUST NOT 进入 projection

### Requirement: 4b 验收必须区分源码、单体与独立双进程事实
Cloud SHALL 覆盖 snapshot/route、cursor 幂等、乱序、target、首次装载、陈旧、outbox 积压与恢复
acceptance；kernel/transport SHALL 验证构建产物与导出；api/automation SHALL 验证受管组合根
typecheck、ready 与 fail-closed。DEV monolith 验收只证明本地 authority 零回归；只有命名 target
上的独立 api/automation 都实际启动并完成跨进程探针后，才可声明 4b 运行态完成。

#### Scenario: 只有 loopback 与 monolith 证据
- **WHEN** route/client 测试与 DEV monolith 均通过，但独立 api/automation 未启动
- **THEN** 交付记录 SHALL 写为 source complete、monolith regression passed、split runtime not_started
- **AND** MUST NOT 声明三进程或真实跨进程镜像已上线

#### Scenario: 独立进程完成断链恢复探针
- **WHEN** DEV 独立 api/automation 已验证首次 snapshot、积压 replay、越过 freshUntil 的停手、
  恢复后的 cursor 续跑与 target 隔离
- **THEN** 交付记录 MAY 声明该 target 的 4b split runtime accepted
- **AND** 仍 MUST 与 OL 部署、Edge installer 和真实客户账号结果分别记录
