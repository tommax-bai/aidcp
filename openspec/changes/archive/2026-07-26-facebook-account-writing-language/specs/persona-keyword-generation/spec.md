## ADDED Requirements

### Requirement: 人设向导仅为 Facebook 显示受控发言语言
Electron 人设向导 SHALL 在“语气调性”下为当前平台明确为 Facebook 的环境显示“发言语言”单选，提供中文、英文、越南语；小红书与视频号 MUST NOT 显示该设置或发送其值。语言选择 SHALL 独立于自由关键词和点赞倾向，MUST NOT 编码进 `keywordSelections`。

#### Scenario: Facebook 环境要求选择语言
- **WHEN** 用户打开 Facebook 环境的人设初始化或更新向导
- **THEN** 向导显示中文/英文/越南语单选，未选择时禁止生成并给出明确提示

#### Scenario: 小红书不显示或发送语言
- **WHEN** 用户打开小红书环境的人设向导并生成草稿
- **THEN** 向导不显示发言语言，`persona.generate` 不携带 `writingLanguage`，现有关键词行为保持不变

#### Scenario: 切换环境不串语言选择
- **WHEN** 用户从一个已选越南语的 Facebook 环境切换到另一个环境
- **THEN** 向导从目标环境的 Cloud 权威快照回显或显示待选择，MUST NOT 沿用上一环境的越南语 DOM 状态

### Requirement: persona 请求以独立字段传递并回显写作语言
Edge 与 Cloud 的 `persona.generate` 请求 SHALL 以独立 `writingLanguage` 字段传递 Facebook 选择；Cloud 生成器 SHALL 在模型结果通过后确定性写入 soul。Cloud UI snapshot SHALL 以可选 `personaWritingLanguage` 回显账号真态，Edge MUST NOT 本地推断已保存值。

#### Scenario: 生成结果确定性包含语言
- **WHEN** Cloud 收到合法 Facebook `writingLanguage=en` 并成功生成人设
- **THEN** 返回的 soul 草稿包含 `writing_language: en`，该值不是模型自由输出

#### Scenario: 存量缺字段回显待补充
- **WHEN** Cloud 读取到已绑定但无 `writing_language` 的 Facebook 人设
- **THEN** snapshot 显式投影缺失状态，Edge 显示语言待补充，MUST NOT 默认勾选中文
