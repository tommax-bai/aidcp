## Why

客户端外侧环境栏已经按“人工昵称 → 平台昵称 → 环境名 → 环境尾号”展示，但“环境管理”浮层仍直接渲染 AdsPower `user/list` 的原始 `name`，导致同一个环境在内外显示不同昵称。需要让管理列表及其操作提示复用现有共享解析器，避免运营误认目标环境。

## What Changes

- 环境管理列表按稳定 `profileId/envKey` 关联当前花名册与运行环境，并复用共享环境显示名解析器。
- 管理列表行、批量选择可访问名称、代理弹层、平台修改和删除确认统一使用同一个已解析显示名。
- 未加入花名册或尚无运行投影的环境继续回落 AdsPower 原始环境名，再回落环境尾号；不把显示名用于选择、代理写入、删除或平台保存。
- 补 renderer 集成测试，锁定人工昵称覆盖管理浮层旧环境名，同时保持环境 ID 与操作载荷不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `adspower-desktop-env-picker`: 将已加入环境的管理列表主昵称从 AdsPower 实时名改为客户端统一解析后的环境显示名，未加入环境仍使用 AdsPower 名称回落。
- `edge-fleet-console`: 将环境管理浮层纳入客户端环境身份锚点，明确其列表及相关动作必须复用共享显示名解析规则。

## Impact

- 代码：`aidcp-edge/src/electron/renderer/renderer.js` 及对应 Electron renderer 测试。
- 契约：同步收紧 `adspower-desktop-env-picker` 的旧面板昵称语义，并补充 `edge-fleet-console` 的环境身份锚点与环境管理场景。
- 无 Cloud、Console、协议、数据库或 AdsPower API 变更；源代码合入后需要重启包含该提交的客户端，且本变更不构建安装包。
