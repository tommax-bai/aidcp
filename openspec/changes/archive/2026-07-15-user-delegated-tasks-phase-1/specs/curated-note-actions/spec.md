## ADDED Requirements

### Requirement: 精选行级写动作必须先创建委托确认而非直接触发

精选内容的参照创作和定向评论入口 SHALL 先创建绑定该行账号与来源快照的 `awaiting_confirmation` DelegatedTask；console 展示结构化确认后才可入队。行归属账号、content type、noteId/标题/来源血缘与既有后端约束 MUST 保持，确认后仍复用既有完整发布/评论链路。

#### Scenario: 定向评论确认前不接管边端
- **WHEN** 管理员点击精选笔记“定向评论”并尚未确认结构化卡片
- **THEN** 系统仅持久化待确认任务和目标快照
- **AND** MUST NOT 取得 edge 租约、搜索笔记或生成评论

#### Scenario: 目标行在确认前被删除
- **WHEN** 待确认任务引用的精选行在用户确认前已删除或归属发生变化
- **THEN** 确认时重新校验失败并保持不可执行
- **AND** MUST NOT 换用相似精选内容

