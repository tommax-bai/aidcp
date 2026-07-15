## Context

`ipcMain.handle('persona:persist')` 在成功后先执行 `updateStatus(...personaBound:true)`，再把 Cloud 回执返回 renderer。状态推送与 IPC response 是两条独立通道，renderer 不能假设回执一定先到。现有自动收起规则只看“弹窗由系统自动打开 + 当前已绑定”，没有区分“persist 正在收敛”或“首作卡正在展示”。

## Decisions

### 1. 在 renderer 记录账号级 persist 收敛态

确认人设前记录草稿所属环境，直到 IPC promise settle 才清除。`updatePersonaGate` 仅对同一弹窗环境检查该状态，避免 A 账号的在途保存影响 B 账号的人设浮层。

### 2. 自动收起必须排除收敛态与首作卡活跃态

权威绑定态仍负责收起真正的系统误弹，但 `persistSettling` 或 `growthActive` 时不得关闭。这样不依赖主进程与 renderer 的消息先后顺序，也能抵抗首作卡展示后的后续心跳。

### 3. 无首作信号时显式恢复原收起行为

如果保存成功但回执没有 `firstPostOnboarding:true`，系统自动打开的浮层按原行为关闭；手动打开的更新/查看浮层不替用户关闭。

## Risks / Trade-offs

- [在途标志未清] → `finally` 按环境清除，失败与异常同样收敛。
- [跨环境串扰] → 标志与 `personaPopOpenEnvId` 精确比对，不使用全局布尔值。
- [首作卡被后续心跳关闭] → 活跃首作状态作为自动收起的明确否决条件，CTA 自己负责结束引导并关窗。
