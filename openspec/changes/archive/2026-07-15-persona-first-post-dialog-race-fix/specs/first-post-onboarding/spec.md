## ADDED Requirements

### Requirement: 首作持久化竞态不得吞掉首次引导

Edge SHALL 在账号首次人设持久化请求正在收敛时保持该账号由系统自动打开的人设浮层，直至收到持久化结果。若结果明确包含 `firstPostOnboarding:true`，Edge SHALL 展示首作引导，并在引导活跃期间忽略仅用于确认绑定态的后续 `personaBound:true` 收起信号。该保护 MUST 只作用于同一环境的在途保存或活跃首作引导，不得阻止普通已绑定账号的系统误弹自动收起。

#### Scenario: 绑定态先于持久化回执到达
- **WHEN** 用户首次确认人设，主进程先推送 `personaBound:true`
- **AND** 随后持久化回执返回 `firstPostOnboarding:true`
- **THEN** 人设浮层在两条消息之间保持打开
- **AND** 回执到达后用户能看到完整首作引导与 CTA

#### Scenario: 首作卡展示后收到绑定态心跳
- **WHEN** 首作引导已经展示
- **AND** 后续状态心跳继续携带 `personaBound:true`
- **THEN** Edge MUST NOT 自动关闭首作引导
- **AND** 只有用户点击 CTA 或显式关闭才结束该引导

#### Scenario: 普通绑定态仍收起系统误弹
- **WHEN** 没有同环境持久化请求在途，也没有首作引导活跃
- **AND** 系统自动浮层收到权威 `personaBound:true`
- **THEN** Edge 仍按既有规则自动收起该浮层
