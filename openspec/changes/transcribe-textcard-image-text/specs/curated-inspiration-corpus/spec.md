## MODIFIED Requirements

### Requirement: 观测捕获诚实且为采集时刻快照

系统 SHALL 在笔记详情到达云端时按门槛判定是否纳入精选；纳入则落详细行，未纳入则不囤积详情。计数 MUST 记为采集时刻快照，缺失字段 MUST 诚实置空，MUST NOT 编造。

对通过共鸣预筛的图片笔记，系统 MAY 按 `textcard-image-transcription` 能力识别并转写其自身的高置信文字卡。成功文字 SHALL 按参考图顺序增补本次 DOM 正文，并以有序逐卡结构随精选行记录；因此 DOM 正文为空的文字卡 MUST 在真实转写后按有效正文参与丰富度评估，MUST NOT 仅因 DOM 为空被丢弃。失败 MUST 保持原正文并诚实记录，MUST NOT 破坏计数快照和缺失置空红线。

#### Scenario: 过门槛笔记落详细行
- **WHEN** 一篇详情通过准入门槛
- **THEN** `curated_content` 写入全文、计数快照、话题、纳入原因和可用的参考图片信息

#### Scenario: 未过门槛不落精选
- **WHEN** 一篇详情未通过准入门槛
- **THEN** 不向 `curated_content` 写入该详情，其薄行为记录照旧由行为账本承载

#### Scenario: 计数缺失诚实置空
- **WHEN** 某计数或话题解析不到
- **THEN** 对应字段置空或空数组，MUST NOT 以臆造值填充

#### Scenario: 空 DOM 文字卡按真实图中文字评估
- **WHEN** 一篇文字卡 DOM 正文为空、通过共鸣预筛且至少一张卡转写成功
- **THEN** 有序转写组成有效正文后参与丰富度评估，通过后逐卡记录与有效正文一并落库

#### Scenario: 转写失败不改变原有诚实语义
- **WHEN** 文字卡识别或转写失败
- **THEN** 原 DOM 正文、计数快照和缺失字段语义保持不变，MUST NOT 编造正文或计数
