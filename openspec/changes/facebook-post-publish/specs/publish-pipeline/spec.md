## ADDED Requirements

### Requirement: 发布生产和下发按平台 publish profile 路由

发布流水线 SHALL 按 `accounts.platform` 选择平台 publish profile，决定内容形态、图片来源、标题语义、元数据支持范围和命令序列。Xiaohongshu SHALL 保持现有生图、标题、话题、图文发布行为；Facebook SHALL 使用账号图片素材池作为图片来源，不调用图片模型，不下发 XHS-only 的 title/topic/cover/creator-page steps。平台 profile 缺失或目标平台不支持 publish 时，发布 MUST fail-closed 并给出原因，MUST NOT 回落到默认 XHS profile。

#### Scenario: Facebook 使用账号素材池而非生图
- **WHEN** Facebook 账号触发发布草稿生成
- **THEN** 发布流水线 SHALL 从该账号 Facebook 图片素材池锁定图片并写入草稿，MUST NOT 调用 `ImageGenerator` 或图片模型为 Facebook 生成配图

#### Scenario: XHS 发布行为不变
- **WHEN** Xiaohongshu 账号触发发布
- **THEN** 发布流水线 SHALL 继续使用现有 XHS publish profile、标题/话题/配图生成和 XHS 命令序列，不受 Facebook 素材池影响

#### Scenario: Facebook 序列不含 XHS-only 指令
- **WHEN** `CommandSequencer` 为 Facebook draft 构建下发序列
- **THEN** 序列 SHALL NOT 包含 XHS creator URL 导航、`select_mode` 上传图文 tab、topic candidate、XHS cover 设置或 XHS 标题字段填充等 XHS-only 步骤

#### Scenario: 缺平台 profile 时 fail-closed
- **WHEN** 某账号平台没有 publish profile 或 profile 声明 `supportsPublish=false`
- **THEN** 发布流水线 SHALL fail-closed 并返回明确原因，MUST NOT 使用 XHS profile 作为默认兜底

### Requirement: Facebook 草稿的图片记录等于素材池锁定结果

Facebook 发布草稿写入 `publish_log` 时，`images` SHALL 等于素材池本次锁定图片组的 OSS URL 有序列表，`image_url` SHALL 为该数组首项或 null。草稿编辑阶段只能删除当前草稿已有图片，MUST NOT 注入不属于该草稿锁定图片组的新 URL。下发段 MUST 忠于草稿快照，不重新选择图片、不重新生成图片、不替换图片。

#### Scenario: 草稿图片与锁定素材一致
- **WHEN** Facebook 草稿由素材池图片组生成
- **THEN** `publish_log.images` SHALL 与锁定图片组的 OSS URL 顺序一致，`image_url` SHALL 等于第一张图片 URL

#### Scenario: 编辑只能删除不能注入
- **WHEN** 运营编辑 Facebook 待审草稿图片列表
- **THEN** 提交的图片列表 SHALL 是当前草稿 `images` 的保序子序列；任一外部 URL 或其它素材池 URL MUST 被拒绝

#### Scenario: 下发段不重新选图
- **WHEN** 人审批准一个 Facebook 草稿
- **THEN** 下发段 SHALL 使用草稿快照中的 `images`，MUST NOT 再从素材池选择新图或调用图片生成
