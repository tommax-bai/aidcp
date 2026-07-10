## ADDED Requirements

### Requirement: 浏览打开前必须先过 view 配额闸

云端 SHALL 在把候选卡片下发为 `open_note` 之前，按该连接的真实账号调用
`RiskController.explain('view')` 或等效只读判定。判定拒绝时，云端 MUST NOT 下发
`open_note`，MUST NOT 伪造成功浏览，MUST 进入浏览额度休眠而不是下发 `session.end`。
若拒绝原因为 `quota:minute`、`quota:hour`、`quota:day`，云端 SHOULD 按滑动窗口释放时间安排重判；
无可计算释放时间时，云端 MAY 以保守周期重判，直到判定恢复或会话被其它正常终止条件结束。

该闸用于阻止新的笔记详情被打开；既有 `note.detail` 到达后的 `record('view')` 计数路径
仍作为真实成功浏览的记账来源保留。浏览额度休眠期间，普通浏览推进、打开和互动命令 MUST 被扣住；
窗口释放后，云端 SHOULD 发送一次轻量恢复指令重新驱动浏览闭环。该休眠只作用于浏览闭环，不得影响
定时或手动的笔记创作、发帖生成、发帖审批或发帖下发；这些流程不需要前置浏览。点赞、收藏、关注、
评论等浏览衍生行为不会被主动触发，因为休眠期间没有新的笔记详情被打开。

#### Scenario: view 配额已满时不打开下一篇笔记

- **WHEN** 账号的 `RiskController.explain('view')` 返回 rejected
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端 MUST NOT 下发 `open_note`
- **AND** 云端 MUST NOT 下发 `session.end`
- **AND** 云端 MUST 进入浏览额度休眠并安排后续重判

#### Scenario: view 配额可用时照常打开笔记

- **WHEN** 账号的 `RiskController.explain('view')` 返回 allowed
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端照常下发 `open_note`

#### Scenario: view 配额窗口释放后恢复浏览

- **WHEN** 浏览额度休眠到期
- **AND** 账号的 `RiskController.explain('view')` 返回 allowed
- **THEN** 云端 SHOULD 解除浏览休眠
- **AND** 云端 SHOULD 下发一次恢复浏览的推进指令

#### Scenario: 临时 view 配额不阻止会话启动

- **WHEN** 账号因 `quota:minute` 或 `quota:hour` 临时无法新增 view
- **THEN** 云端 MAY 启动或保持浏览会话
- **AND** 云端 MUST 在 `open_note` 前进入浏览额度休眠
- **AND** 云端 MUST NOT 因临时 view 配额拒绝阻断手动或定时笔记创作、发布
