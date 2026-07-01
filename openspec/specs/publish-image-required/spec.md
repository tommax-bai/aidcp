# publish-image-required Specification

## Purpose
TBD - created by archiving change publish-image-required-or-fail. Update Purpose after archive.
## Requirements
### Requirement: 图文帖无图时诚实失败

发布执行端 SHALL 在驱动发布**之前**判定：图文帖在配图缺失（全部生图失败/降级，`assembledContent.imageUrls` 为空、成功图数 M=0）时 **诚实判本次发布 `failed`**，并 MUST NOT 继续驱动边缘进入注定 `no_target` 的纯文字路径（小红书图文编辑器「先传图门控」下标题/正文框不渲染）。失败 SHALL 不发审批卡、不下发指令、`images_attached` 记为 false、`images_attached_count` 记为 0。判据 SHALL 以成功图数组是否为空为准（取代旧的单图 URL 判定），使部分成功（M≥1）不被误判为无图。

#### Scenario: 全部配图缺失（M=0）→ 提前诚实失败
- **WHEN** 进入发布执行且该图文帖 `assembledContent.imageUrls` 为空（成功图数 M=0）
- **THEN** 执行端 SHALL 落库 `status='failed'`、`images_attached=false`、`images_attached_count=0`，返回 `failed`，且 MUST NOT 发审批卡、MUST NOT 下发任何发布指令到边缘

#### Scenario: 有配图（M≥1）→ 正常走发布门
- **WHEN** `assembledContent.imageUrls` 非空（至少一张成功图）
- **THEN** 执行端 SHALL 按既有路径继续（人审 → 驱动序列下发 M 张上传），不因"未满计划张数"而失败

### Requirement: 配图生成时长可配且充足

配图生成的时长 SHALL 可经环境变量配置，且默认值足以容纳较慢的文生图。多图下 N 张 SHALL **并行**生成，计时 SHALL **下沉到每张图**（env `AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`）：单张超时只丢该张、不影响其余张；角色级总闸 SHALL 设为 ≈ 每图超时 + 余量（并行下 wall-clock 为最慢单张、非各张相加），且 MUST NOT 因总闸超时把已成功生成的图整体清零（超时须用已 settle 结果产出）。单图轮询总预算（轮询次数 × 间隔）SHALL 严格小于每图超时，使慢图在被砍断前完成。发布执行角色的超时 SHALL 覆盖"审批等待 + 张数 × 单图上传 + 余量"（上传仍逐条 FIFO、与生成并行无关），且 `submit_publish` 成功后 MUST NOT 因超时把记录翻成 `failed`。

#### Scenario: 每图超时 env 可调且大于单图轮询预算
- **WHEN** 设置文生图轮询次数与每图超时的环境变量
- **THEN** 二者 SHALL 生效，且每图超时（毫秒）SHALL > 轮询次数 × 轮询间隔，使慢图能在被砍断前完成；并行下角色级总闸 SHALL ≈ 每图超时 + 余量（非 张数 × 单图预算）

#### Scenario: 不配 env → 用充足默认
- **WHEN** 未设置相关环境变量
- **THEN** SHALL 采用充足默认（每图超时与轮询预算一致、足以容纳较慢文生图），并按张数放大发布执行角色超时

#### Scenario: 总闸超时不清零已成功图
- **WHEN** 角色级总闸在并行生成尚未全部 settle 时到点
- **THEN** SHALL 用已累积的成功 `imageUrls` 构造产出、MUST NOT 返回空产出丢弃已生成成功的图

