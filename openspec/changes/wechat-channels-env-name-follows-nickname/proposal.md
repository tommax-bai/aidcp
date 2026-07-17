## Why

小红书环境在冷启动后读到真实账号昵称会自动把 AdsPower 环境名更新为昵称，但视频号虽然已经在认证 sidecar 中拿到权威 `identity.displayName`，没有把该身份送到桌面外壳的既有改名链，导致已绑定账号“tom白”仍显示旧环境名。视频号也需要在每次冷启动完成身份校验后沿用同一条渐进改名机制。

## What Changes

- 视频号认证状态只有在身份已由当前会话验证匹配时，才向桌面外壳发出结构化账号身份事件。
- 桌面外壳把视频号身份事件视为真实平台昵称，复用既有 AdsPower `user/update` 改名封装、幂等去抖、串行限速与失败诚实降级。
- 冷启动恢复已加密会话和首次扫码绑定两条路径都覆盖；身份未验证、昵称为空或身份不匹配时不触发改名。
- 增加 Edge 回归测试，锁定视频号身份事件的验证门槛与 Electron 平台来源标记。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `adspower-environment-provisioning`: 明确视频号冷启动完成身份校验后也必须沿用“真实昵称驱动环境改名”要求，且未验证身份不得触发改名。

## Impact

- 仅影响 `aidcp-edge`：视频号认证运行时的本地结构化 UI 事件，以及 Electron 主进程身份事件的平台来源标记。
- 不修改 Cloud、跨端协议、账号主键或 AdsPower 写能力边界；继续复用现有 name-only `user/update` 封装。
- 不做存量环境批量改名；存量视频号环境在下次正常冷启动并验证身份后渐进更新。
