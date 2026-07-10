## ADDED Requirements

### Requirement: 高风险配图产后视觉安全校验

发布配图链路 SHALL 对**高风险生成图**执行产后视觉安全校验。高风险图至少包括：prompt / 风格档 / provider metadata 显示可能含真人、人脸、局部人体、背影、POV、封面文字或模型渲染文字的图片。校验 MUST 真实读取本次生成的新图 URL，并用视觉 / 多模态判定识别：是否像可识别真实人物 / 名人、是否含乱码文字或不可控文字。系统 MUST NOT 因 prompt 含 `faceless` / `no text` / `no realistic human face` 就假定产物安全。

校验输出 SHALL 至少区分 `pass`、`reject`、`unavailable`。当结果为 `reject` 时，该图 MUST 不进入 `imageDirective.imageUrls`，系统 MAY 按受控上限重生成该张；重试后仍无合格图时，按既有部分成功 / 全失败语义诚实收敛。当视觉校验不可用、超时或返回非法结果时，系统 MUST 记录 `unavailable` 或等价状态，MUST NOT 标记为已通过视觉校验。

#### Scenario: 高风险图必须真实看图后才通过
- **WHEN** 一张生成图因人物或文字策略被判为高风险
- **THEN** 系统必须让视觉 / 多模态判定读取该生成图 URL 后才能记录 `pass`，MUST NOT 仅凭 prompt 约束记录通过

#### Scenario: 命中真人或乱码风险即丢弃
- **WHEN** 视觉校验判定生成图像可识别真实人物 / 名人，或含乱码文字 / 不可控文字
- **THEN** 该图 MUST 不进入 `imageDirective.imageUrls`，并按受控策略重生成或少图继续

#### Scenario: 校验不可用不得伪装通过
- **WHEN** 视觉校验 provider 超时、报错、缺配置或返回非法结构
- **THEN** 系统 MUST 记录 `unavailable`，MUST NOT 把该图标记为已通过视觉校验
