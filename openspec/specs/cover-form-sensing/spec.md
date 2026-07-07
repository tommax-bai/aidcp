# cover-form-sensing Specification

## Purpose
TBD - created by archiving change textcard-cover-form. Update Purpose after archive.
## Requirements
### Requirement: 发布时按需形态感知与素材行缓存回写

系统 SHALL 在洗稿发布管线内、封面形态决策消费前，对参照图中第一张有可用 URL 的图片（ossUrl 优先、缺则 sourceUrl）执行视觉形态判定。判定前 SHALL 先检查素材行 `reference_images` 对应 item 上已缓存的形态注解：注解的判定锚 `detectedFor` 等于该 item 当前 `capturedAt` 时 SHALL 直接使用缓存、不发起视觉调用。缓存未命中时 SHALL 发起单次视觉模型调用，并将结果 best-effort 回写素材行。回写 SHALL 实现为单条 UPDATE 定点写目标 item（jsonb 路径写入），WHERE 子句内嵌 `capturedAt` 锚比对——锚不符即 0 行弃写，MUST NOT 以读-改-整数组回写的方式实现（避免与浏览闭环观测刷新的并发整体替换互相覆盖）。对存量缺 `capturedAt` 的 item，同一条写入 SHALL 顺带把归一化 `capturedAt` 落盘作锚（否则缓存永不命中）。回写 MUST NOT 改变行的 `updated_at`（创作召回按其排序）。回写失败 SHALL 只记日志、不影响本次发布。

#### Scenario: 缓存命中零调用
- **WHEN** 素材行首图已有注解且 `detectedFor === capturedAt`，同一笔记再次洗稿发布
- **THEN** 零视觉调用、直接消费缓存判定，审计 `sensedSource='cached'`

#### Scenario: 缓存未命中调用并回写
- **WHEN** 素材行首图无注解或图片已被重抓（`capturedAt` 变化），发布触发感知
- **THEN** 发起一次视觉调用，结果以单条守卫 UPDATE 回写该 JSONB item，且行 `updated_at` 不变

#### Scenario: 并发刷新下守卫弃写
- **WHEN** 回写执行时目标 item 的 `capturedAt` 已不等于判定锚（浏览闭环刚整体替换了图集数组），或 PG 写入失败
- **THEN** 弃写并只记日志，本次管线内判定照常生效、发布不受影响，绝不覆盖新图集数组

#### Scenario: 无可用参照图诚实短路
- **WHEN** 素材行 `reference_images` 为空或全部 URL 不可用
- **THEN** 感知返回 `no_image`、审计如实记录，封面走生成式路径，绝不因缺原图阻断发布

### Requirement: 判定输出收窄与弃权语义

视觉判定输出 SHALL 限定为形态枚举（`text_card|photo|illustration|other`）+ 置信度（0..1），SHALL NOT 包含颜色、坐标或 OCR 文本字段（防搬运结构隔离）。模型输出不可解析或核心字段缺失/类型不符 SHALL 按 error 处理，MUST NOT 默认成功。调用失败/超时（内层闸 env `AIDCP_COVER_FORM_TIMEOUT_MS`，默认 30s）SHALL 返回 error 且 error 结果 MUST NOT 持久化（无负缓存）。置信度阈值（env `AIDCP_COVER_FORM_MIN_CONFIDENCE`，默认 0.75）SHALL 在消费端施加、判定原样持久化（存观测不存策略）。低置信/unknown/error 任何弃权路径 SHALL NOT 默认猜测形态、SHALL NOT 阻断发布。素材行注解经归一化白名单读写 SHALL 双向兼容：`formGuess` 字段非法（枚举外 form、越界 confidence、非正整数时间戳）时 SHALL 只丢弃 `formGuess`、保留图片本体字段。

#### Scenario: 脏输出判 error 不持久化
- **WHEN** 视觉模型返回脏 JSON 或缺 `form` 字段
- **THEN** 判 error、不持久化任何注解，封面走生成式且审计 gateReason 如实记录

#### Scenario: 低置信弃权但观测保留
- **WHEN** 判定 `form='text_card'` 但 `confidence=0.6` 低于阈值
- **THEN** 判定原样持久化，但消费端门禁弃权、封面走生成式、审计 `gateReason='low_confidence'`

#### Scenario: 感知旗标关闭零调用
- **WHEN** `AIDCP_COVER_FORM_SENSING=false`（默认）时发布触发
- **THEN** 感知立即返回 disabled、零视觉调用零注解写入，全链路与现版行为一致

#### Scenario: 非法注解读取时被剥离
- **WHEN** 素材行某 item 的 `formGuess` 含枚举外 form 或越界 confidence
- **THEN** 归一化读取只丢 `formGuess`、图片本体字段照常返回，不报错不丢图

### Requirement: 多模态客户端隔离与模型解析链

视觉调用 SHALL 走独立的 OpenAI 兼容多模态客户端（消息 content 支持 image_url 数组），复用既有厂商凭据运行时与 token 记账钩子。模型解析链 SHALL 固定为「env（`AIDCP_COVER_FORM_MODEL` / `AIDCP_COVER_FORM_PROVIDER`）→ 代码默认」，SHALL NOT 回落到全局文本模型或文本分类默认层（文本模型收到 image_url 必错，属正确性问题），单测 SHALL 锁死该链。角色 SHALL 在 role-catalog 登记（llmKind 'vision'）但 v1 仅作展示、不开面板写入。该客户端为后续产后校验等多模态需求的共享缝；本能力 MUST NOT 实装产后校验。

#### Scenario: 解析链绝不落文本模型
- **WHEN** 未配置视觉模型 env 时发起感知调用
- **THEN** 使用代码默认视觉模型，绝不把含 image_url 的消息发给全局文本模型（单测断言锁死）

#### Scenario: 模型下架经 env 换名恢复
- **WHEN** 视觉模型名被厂商下架返回 400
- **THEN** 按 error 弃权 + 显式日志，经 env 换名 + 重启恢复，无需代码改动

