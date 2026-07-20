## ADDED Requirements

### Requirement: 回复配置必须按稳定分组或默认作用域管理
系统 SHALL 为 `wechat_channels` 提供稳定的 `group` 与单例 `default` 回复配置作用域。版本化 policy、templates、rules 与 profiles MUST 归属稳定 scope identity，MUST NOT 通过复制到成员账号或创建幽灵账号实现共享。

#### Scenario: 同组账号共享一份发布快照
- **WHEN** 两个视频号账号具有完全相同的非空 `group_label`
- **THEN** 二者的新回复任务解析到同一 group scope 的同一已发布版本，配置编辑和发布只执行一次

#### Scenario: 默认作用域独立存在
- **WHEN** 当前没有任何未分组账号但管理员准备默认策略
- **THEN** 系统仍允许创建、编辑和发布唯一 default scope，不要求选取代表账号承载配置

### Requirement: 生效解析必须明确区分分组与未分组
Cloud SHALL 通过唯一解析器读取账号当前 `group_label`：非空账号 MUST 只解析精确匹配的 group scope；空标签账号 MUST 只解析 default scope。作用域没有已发布配置时 MUST fail closed，MUST NOT 静默回落到另一作用域或账号级配置。

#### Scenario: 未分组账号使用默认策略
- **WHEN** 视频号账号的 `group_label` 为空且 default scope 存在有效 published 版本
- **THEN** 新回复任务使用该 default published snapshot，并标记来源为 default

#### Scenario: 有分组但组策略缺失
- **WHEN** 视频号账号属于分组 A，但分组 A 没有有效 published 版本
- **THEN** 生成流程返回具名 `group_config_missing` 阻断，绝不改用 default 或遗留账号配置

#### Scenario: 默认策略缺失
- **WHEN** 未分组账号没有可用 default published 版本
- **THEN** 生成流程返回具名 `default_config_missing` 阻断，收件箱读取不被伪装成已就绪

### Requirement: 历史回复任务必须冻结配置作用域和版本
新生成的回复任务 SHALL 持久化稳定 `configScopeId` 与 `configVersion`。后续审批、编辑、发送校验 MUST 按冻结引用加载不可变快照，MUST NOT 根据账号当前分组重新解析。

#### Scenario: 任务生成后账号换组
- **WHEN** 任务由分组 A 的 v3 生成后账号被移动到分组 B
- **THEN** 该任务继续使用分组 A v3；账号随后创建的新任务使用分组 B 当前 published 版本

#### Scenario: 分组发布新版本
- **WHEN** 一个任务引用 group scope v3，运营随后发布 v4
- **THEN** 历史任务仍使用 v3，新任务使用 v4

### Requirement: 共享策略不得削弱账号级安全门禁
group/default 配置 SHALL 只提供策略值。账号级 runtime controls、auth、identity、capability、write pause/circuit、幂等、配额计数和 `RiskController` MUST 在执行账号上继续独立检查；任何一层拒绝都 MUST 阻断写动作。

#### Scenario: 分组允许自动但账号已暂停
- **WHEN** group policy 允许自动发送但当前账号 runtime write 已暂停或 circuit open
- **THEN** 系统不排队也不发送回复，并返回账号级阻断原因

#### Scenario: 共享限额仍逐账号计数
- **WHEN** 同组两个账号继承相同的每小时限额
- **THEN** 两个账号分别按自己的计数器接受 `RiskController` 判定，不合并成分组额度池

### Requirement: Internal API 必须以 scope 管理共享配置
internal panel API SHALL 提供 scope 列表、读取、初始化、policy/templates/rules/profile 编辑、preview、publish 与 audit 能力，并继续使用统一 envelope、显式 grants 与 aggregate `expectedVersion` CAS。账号级 runtime-controls 路径 MUST 保留；账号 effective-config 路径 MUST 为只读。

#### Scenario: 发布分组策略
- **WHEN** 有 publish grant 的管理员以当前 expectedVersion 发布一个校验通过的 group draft
- **THEN** 系统原子生成不可变 published 版本并返回 scope head、影响成员数与版本，绝不声称成员平台动作已发生

#### Scenario: 旧账号写入口不扩大影响面
- **WHEN** 客户端在 scoped cutover 后调用旧 `/api/accounts/:accountId/reply-config` 写路径
- **THEN** API 明确返回 deprecated/拒绝状态，MUST NOT 偷偷把单账号写变成整组修改

#### Scenario: 预览必须绑定合法账号上下文
- **WHEN** 管理员预览 group scope 并选择一个当前不属于该组的账号
- **THEN** API 以 scope/account mismatch 拒绝，不读取其互动正文也不执行 AI preview

### Requirement: Console 必须以分组和默认策略作为主入口
Console SHALL 提供“视频号策略”管理面，列出 default、当前账号分组和已有零成员 scope，展示成员数、draft/published 版本及缺失状态。账号页 SHALL 展示 effective source 并保留账号运行控制，MUST NOT 让共享策略编辑看起来只影响当前账号。

#### Scenario: 从账号查看生效来源
- **WHEN** 运营查看一个属于分组 A 的视频号账号
- **THEN** 页面显示“来自分组 A”及当前 published 版本，并提供跳转分组策略而非账号级策略编辑

#### Scenario: 未分组账号显示默认来源
- **WHEN** 未分组账号命中 default published 策略
- **THEN** 页面明确显示“来自默认策略”，不显示为账号自有配置

### Requirement: 迁移必须先盘点冲突再切换
系统 SHALL 保留现有账号级配置作为迁移只读源，并支持 `legacy`、`shadow`、`scoped` 解析阶段。迁移盘点 MUST 以无正文 fingerprint 识别同一目标 scope 内的一致和冲突配置；冲突 MUST 显式处理，MUST NOT 自动选择任一账号为赢家。

#### Scenario: 同组配置冲突
- **WHEN** 同一 group 下两个账号的 published 配置 fingerprint 不同
- **THEN** 迁移报告列出冲突账号和版本摘要，scope 不被自动发布，scoped cutover 门禁保持关闭

#### Scenario: shadow 不改变真实执行
- **WHEN** 系统运行于 shadow 阶段
- **THEN** 回复流程继续执行 legacy 配置，只记录 scoped 覆盖和差异摘要，不记录模板或消息正文

### Requirement: 单账号下线不得删除共享策略
账号解绑、客户终止和到期 offboarding SHALL 只清除账号互动数据、账号 runtime controls 与 legacy 账号配置；group/default scope 配置及其审计 MUST 保留，除非管理员通过独立 scope 生命周期操作显式处理。

#### Scenario: 分组成员下线
- **WHEN** 分组 A 的一个账号完成 Cloud purge，分组内仍有其他账号
- **THEN** 分组 A 的 scope、published versions、templates、rules、profiles 和 audit 均保持可用
