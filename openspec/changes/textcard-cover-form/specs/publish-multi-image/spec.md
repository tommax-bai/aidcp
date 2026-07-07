# publish-multi-image — delta（textcard-cover-form）

## MODIFIED Requirements

### Requirement: 并行出图且每张独立计时绝不清零已成功图

配图生成角色 `ImageGenerator` SHALL 按 `imagePlan.imagePrompts` **并行**调图源生成（`Promise.allSettled`），全部 settle 后把成功的真实 URL 按**规划顺序**收进 `imageDirective.imageUrls`（[0] 为钩子图/封面位）。计时 SHALL **下沉到每张图**：每张独立超时（env `AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`），某张超时 / 失败 SHALL 只丢该张、不影响其余张，MUST NOT 把已成功生成的图整体清零。并发上限 SHALL 可经 env `AIDCP_PUBLISH_IMAGE_CONCURRENCY` 配置（防图源突发限流）。角色级总闸 SHALL 设为 ≈ 每图超时 + 余量（并行下 wall-clock 为最慢单张、非各张相加），且即便触发 SHALL 用"已 settle 的成功 URL"构造产出、MUST NOT 返回空产出丢弃已成功图。失败那张 MUST NOT 进入 `imageUrls`（不补空、不复用别张 URL）。

例外（textcard-cover-form）：当配图计划决策为 text_card 且渲染依赖（文案、渲染器、OSS 上传器）俱备时，0 号封面槽 MAY 由注入的确定性文字卡渲染器产出以替换该槽结果（不前插、不移位）。渲染+字节直传 SHALL 在进入每图超时槽机制**之前独立结算**（独立内层闸，默认 30s），渲染失败后 0 号 SHALL 以**完整每图槽预算**用计划内恒在的生成式提示词走图源路径（角色级总闸公式相应加渲染超时项，MUST NOT 让渲染耗时挤占生成式兜底的每图预算）。渲染器 MUST NOT 实现生图提供方接口、MUST NOT 进入图源路由表；其余各张与全部失败语义不变。

#### Scenario: 部分图超时只丢该张、保留已成功
- **WHEN** 并行生成中第 k 张超时 / 失败，其余张成功
- **THEN** `imageDirective.imageUrls` 含所有成功张的真实 URL（按规划顺序）、不含第 k 张，不因单张失败清零或中断其余张

#### Scenario: 红线——总闸超时清零已成功图（反例）
- **WHEN** 任一实现让角色级总闸 `Promise.race` 在 `allSettled` 结算前到点即返回空产出，丢弃已生成成功的 URL
- **THEN** MUST 视为违规、不予合入（已成功图绝不被外层超时清零；总闸须 ≥ 每图超时 + 余量、超时也返回已 settle 结果）

#### Scenario: 生成角色单测只桩图源
- **WHEN** 为 `ImageGenerator` 写单测
- **THEN** 只需桩图源、无需桩任何 LLM；并行计时、保序累积、部分成功收集逻辑可脱离真实图源验证

#### Scenario: 文字卡渲染独立结算不挤占生成式兜底预算
- **WHEN** 0 号槽先尝试文字卡渲染并在 30s 内层闸耗尽后失败，随即落回生成式提示词走图源
- **THEN** 生成式兜底享有完整每图槽预算（渲染耗时不计入），不出现「渲染 30s + 图源轮询尾部 + OSS 转存 > 每图槽」导致兜底图在收尾前被总闸砍掉的尾部回归
