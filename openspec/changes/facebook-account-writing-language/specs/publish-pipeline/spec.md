## ADDED Requirements

### Requirement: Facebook 稿件正文按账号写作语言首次生成
当普通 Facebook 发布/候选稿流程生成正文时，正文角色 SHALL 从 `trigger.generateInput.soul.writing_language` 读取目标语言并以该语言首次产文。Facebook 分支 MUST NOT 复用会诱导小红书标题、篇幅、话题或中文范文的产文模板；小红书 ContentCreator 行为 SHALL 保持不变。

#### Scenario: 英文 Facebook 普通稿件首次产文
- **WHEN** `platform=facebook` 且账号 `writing_language=en` 触发普通稿件/候选稿生成
- **THEN** ContentCreator 使用 Facebook 正文语境并只输出英文正文，MUST NOT 先生成中文再在发布前翻译

#### Scenario: 小红书创作逐位兼容
- **WHEN** `platform=xiaohongshu` 触发既有灵感或普通发布创作
- **THEN** 继续使用既有小红书 prompt、标题/话题/配图流程，MUST NOT 要求或读取 Facebook 写作语言

### Requirement: Facebook 正文改写保持输入语言且审核后不重写
Facebook 正文在去 AI 味或其它生成期改写时 SHALL 保持已经确定的写作语言，并在进入 `pending_approval` 前完成语言守卫。审批后的 dispatcher/sequencer SHALL 从落库草稿逐字重建发布输入，MUST NOT 重新读取人设语言并翻译或重生成。

#### Scenario: 去 AI 味保持越南语
- **WHEN** 越南语 Facebook 正文触发 ContentCleaner 重写
- **THEN** 重写提示明确保持原语言，终稿仍须通过越南语守卫后方可进入待审

#### Scenario: 配置变化不改已审稿件
- **WHEN** Facebook 草稿进入审核后账号写作语言发生变化
- **THEN** 已审草稿仍按内容版本逐字下发或由运营显式编辑/重生成，发布执行层 MUST NOT 静默改写已审正文
