## ADDED Requirements

### Requirement: Facebook 评论撰写与重写保持账号写作语言
Facebook `CommentComposer`、定向评论撰写器、强制互动评论以及 `CommentDeAiFlavor` 的去 AI 味/撞车重写 SHALL 使用账号 soul 的 `writing_language`。目标帖正文和评论区语言只作语境，MUST NOT 覆盖账号配置；重写结果语言不匹配时 SHALL 回退已验证原文或诚实停止。

#### Scenario: 通用 Facebook composer 使用账号语言
- **WHEN** Facebook CommentComposer 为 `writing_language=en` 的账号撰写评论
- **THEN** prompt 明确要求只输出英文，现有“跟随帖子语言”规则不得覆盖它

#### Scenario: 定向 Facebook composer 使用同一规则
- **WHEN** CommentScheduler 的 Facebook 定向路径为 `writing_language=vi` 的账号撰写评论
- **THEN** 定向 prompt 同样要求越南语并通过同一语言守卫，MUST NOT 与通用 composer 漂移

#### Scenario: 去 AI 味不切换语言
- **WHEN** 已验证为中文/英文/越南语的 Facebook 评论触发去 AI 味或撞车重写
- **THEN** 重写提示要求保持输入语言；若结果不匹配则回退原评论或停止，MUST NOT 把另一语言文本送审/提交
