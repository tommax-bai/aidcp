## Why

Facebook 环境明确处于“未启动”时，客户端仍可能依据缓存的首帖引导或今日成果数据展示获得感卡片，让用户误以为自动化正在推进。需要让该卡片服从当前环境的真实生命周期，同时保留普通数据卡片在未启动时可读取的既有能力。

## What Changes

- 当选中环境明确为 Facebook 且结构化自动化状态为 `stopped` 时，不展示运行价值/获得感卡片，即使状态中仍有缓存的首帖、浏览窗口或今日完成数据。
- 继续在 Facebook 的启动中、排队、运行、待任务、暂停、待机及异常状态按现有证据规则展示或隐藏卡片，不把这些状态扩大解释为“未启动”。
- 保持小红书和其他平台、今日进展、内容发布及环境级 HTTP 数据读取行为不变。
- 增加纯逻辑与 Electron DOM 回归测试，覆盖平台切换和旧状态兼容投影。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `runtime-value-guidance`: 运行价值说明新增 Facebook 未启动态的严格隐藏规则。

## Impact

- `aidcp-edge` Electron renderer 的运行价值视图判定与伴随式界面测试。
- 不改变 Cloud API、自动化状态机、HTTP 数据真源、协议或持久化数据。
- 不构建或发布桌面安装包；代码由后续客户端发布流程带出。
