## ADDED Requirements

### Requirement: 浏览打开前必须先过 view 配额闸

云端 SHALL 在把候选卡片下发为 `open_note` 之前，按该连接的真实账号调用
`RiskController.canDo('view')` 或等效只读判定。判定拒绝时，云端 MUST NOT 下发
`open_note`，MUST NOT 伪造成功浏览，MUST 诚实结束当前浏览会话并下发 `session.end`
（原因可含 `view_quota_exhausted` / `quota:*`）。

该闸用于阻止新的笔记详情被打开；既有 `note.detail` 到达后的 `record('view')` 计数路径
仍作为真实成功浏览的记账来源保留。`scroll` / `back` 等推进与恢复指令不因互动风控闸被泛化拦截，
但当 `view` 闸拒绝时，当前会话应以正常结束路径收口，避免继续尝试开新笔记。

#### Scenario: view 配额已满时不打开下一篇笔记

- **WHEN** 账号的 `RiskController.canDo('view')` 返回 false
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端 MUST NOT 下发 `open_note`
- **AND** 云端 MUST 下发 `session.end` 并结束当前会话

#### Scenario: view 配额可用时照常打开笔记

- **WHEN** 账号的 `RiskController.canDo('view')` 返回 true
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端照常下发 `open_note`

#### Scenario: 启动与续场同样受 view 配额约束

- **WHEN** 账号的 `RiskController.canDo('view')` 返回 false
- **THEN** 云端 MUST NOT 启动或自动续开新的浏览会话
