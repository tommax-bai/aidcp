## Why

Facebook 加群在页面导航或加载失败后会保留 `assigned` 记录并进入分钟级冷却；冷却期间旧认领不可执行、新目标又被旧认领阻塞，最终向运营误报 `no_targets`。用户已明确裁决：页面打开失败就是本次失败，不需要自动冷却或隐藏式重试。

## What Changes

- **BREAKING**：加群的网络、导航、页面未就绪和任务租约瞬态失败不再进入分钟级冷却，也不再保留待重试的 `assigned`/`joining` 占位。
- 将这类失败立即记为真实终态失败并写审计；本次 `/comment --join` 直接返回具体失败原因且不评论。
- 下一次加群触发可从账号分组目标池选择其它未占用目标，不得因上一条失败占位而误报 `no_targets`。
- 保留账号登录、验证码/检查点等账号级暂停策略，以及已加入群的评论覆盖冷却；本变更只删除“尚未加入时页面/执行瞬态失败”的自动冷却重试。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `facebook-group-join-resilience`: 将尚未加入阶段的网络/导航/页面/租约瞬态从冷却重试改为立即终态失败，并保证不阻塞后续目标。
- `facebook-manual-join-comment`: 手动加群评论须直接呈现真实页面执行失败，不得把失败占位误报成目标库为空。

## Impact

- Cloud：`facebook-group-join-scheduler`、membership 终态写入及加群回执测试。
- 数据：不改 schema；失败 membership 继续作为真实终态事实保留，借助现有全局唯一约束避免无界重试同一坏目标。
- Edge/协议/Console：不变。
- 风险：基础设施偶发失败会消耗当前目标而非自动重试；这是本次明确选择的 fail-fast 语义，运营可在审计中看到真实原因。
