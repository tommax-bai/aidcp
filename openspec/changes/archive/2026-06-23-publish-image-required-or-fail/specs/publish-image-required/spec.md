## ADDED Requirements

### Requirement: 图文帖无图时诚实失败
发布执行端 SHALL 在驱动发布**之前**判定：图文帖在配图缺失（生图失败/降级，`assembledContent.imageUrl` 为空）时 **诚实判本次发布 `failed`**，并 MUST NOT 继续驱动边缘进入注定 `no_target` 的纯文字路径（小红书图文编辑器「先传图门控」下标题/正文框不渲染）。失败 SHALL 不发审批卡、不下发指令、`images_attached` 记为 false。

#### Scenario: 配图缺失 → 提前诚实失败
- **WHEN** 进入发布执行且该图文帖 `assembledContent.imageUrl` 为空
- **THEN** 执行端 SHALL 落库 `status='failed'`、`images_attached=false`，返回 `failed`，且 MUST NOT 发审批卡、MUST NOT 下发任何发布指令到边缘

#### Scenario: 有配图 → 正常走发布门
- **WHEN** `assembledContent.imageUrl` 非空
- **THEN** 执行端 SHALL 按既有路径继续（人审 → 驱动序列），不受本要求影响

### Requirement: 配图生成时长可配且充足
配图生成的时长 SHALL 可经环境变量配置，且默认值足以容纳较慢的文生图；配图角色闸超时 SHALL 严格大于文生图轮询总预算（否则角色超时先于轮询完成砍断生图）。

#### Scenario: 轮询预算与角色闸 env 可调且一致
- **WHEN** 设置文生图轮询次数与配图角色闸超时的环境变量
- **THEN** 二者 SHALL 生效，且角色闸超时（毫秒）SHALL > 轮询次数 × 轮询间隔，使慢图能在被砍断前完成

#### Scenario: 不配 env → 用充足默认
- **WHEN** 未设置相关环境变量
- **THEN** SHALL 采用调大后的默认（轮询预算与角色闸一致、足以容纳较慢文生图），相对旧 90s 预算降低"慢图被砍断→无图"概率
