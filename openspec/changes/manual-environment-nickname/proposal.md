## Why

客户端左栏环境昵称目前完全由 AdsPower 环境名与平台登录昵称自动更新，运营无法给环境保留一个稳定、易辨认的人工名称；即使临时改动，也会在身份探测或环境列表刷新后被系统覆盖。需要提供就地改名，并把人工意图明确持久化为最高优先级来源。

## What Changes

- 左栏环境昵称支持双击后就地编辑，提交非空人工昵称并即时保存。
- 环境花名册持久化人工昵称来源；显示优先级调整为人工昵称 → 平台真实昵称 → AdsPower 环境名 → 尾号兜底。
- 人工昵称存在时，平台身份事件自动改名与 AdsPower 列表实时名回填均不得覆盖该昵称。
- 人工昵称在左栏使用轻微不同的颜色与可理解提示，便于识别但不改变环境状态、平台色或选中态。
- 保存失败时如实提示，保留本次内存显示但不得声称已经持久化。

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `edge-fleet-console`: 左栏昵称增加双击就地编辑、人工来源视觉区分，并将人工昵称置于显示优先级最高位。
- `adspower-desktop-env-picker`: 环境列表实时名回填增加人工昵称保护，不再无条件覆盖所有花名册名称。
- `adspower-environment-provisioning`: 登录后自动跟随平台昵称的改名链增加人工昵称保护。

## Impact

- `aidcp-edge` Electron renderer：环境花名册归一、保存、刷新回填、左栏渲染与交互样式。
- `aidcp-edge` Electron main/fleet：环境设置归一、句柄快照和自动 AdsPower 改名闸。
- 本地 `settings.json` 中每个环境成员新增可选的人工昵称来源标记；旧设置保持兼容。
- 不改 Cloud 协议、账号主键、平台昵称采集、风险逻辑或安装包发布流程。
