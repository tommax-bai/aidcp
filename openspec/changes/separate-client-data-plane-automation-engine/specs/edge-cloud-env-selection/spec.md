## MODIFIED Requirements

### Requirement: Cloud environment is selectable in client settings

边缘客户端 SHALL 在设置界面提供 dev、ol、自定义三种 Cloud 目标并持久化。每个目标 SHALL 结构化解析 customer-auth `http(s)` API base 与 automation `ws(s)` URL；dev/ol 使用 edge 内单点映射，自定义目标必须分别校验两个地址，MUST NOT 从一个协议地址静默猜测另一个。旧单一 WS 设置 MAY 兼容读取为 automation URL，但缺失 HTTP base 时 SHALL 明确要求补充或使用可验证的内置映射。

#### Scenario: Operator selects a built-in cloud environment

- **WHEN** 运营选择 dev 或 ol 并保存
- **THEN** 客户端持久化该目标及映射出的 HTTP/WS 地址；写盘失败如实回报未持久化

#### Scenario: Custom endpoint validation

- **WHEN** 运营选择自定义并提交 API base 或 automation URL
- **THEN** 客户端分别要求合法 `http(s)` 与 `ws(s)` 地址，任一非法都拒绝保存且不静默补猜

### Requirement: Selection resolves cloud endpoint with UI-first precedence

客户端 SHALL 按“界面结构化选择 > 对应启动环境变量 > 缺省 dev”分别解析 customer-auth HTTP 与 automation WebSocket 目标。Electron HTTP 适配器使用解析后的 API base；派生自动化引擎时显式注入解析后的 `AIDCP_CLOUD_URL`。两者 SHALL 来自同一个目标环境配置但具有独立实际状态，MUST NOT 因引擎未启动而使 HTTP 无法使用。

#### Scenario: UI selection resolves both transports

- **WHEN** 外壳继承 dev 环境变量但界面已选择 ol
- **THEN** 后续客户 HTTP 请求使用 ol API，后续启动/重连的引擎使用 ol automation URL

#### Scenario: No selection falls back to configured defaults

- **WHEN** 界面没有显式选择
- **THEN** 客户端分别使用已配置的 HTTP/WS 环境变量或缺省 dev 映射，不得把 WS URL直接当 HTTP URL

### Requirement: Switching cloud takes effect only on explicit restart

保存新 Cloud 目标后，后续 customer-auth HTTP 请求 SHALL 使用新 API base；保存 MUST NOT 自动打断在途页面任务或静默重连引擎。automation WS 目标只在显式恢复、重连或下次启动引擎时生效。在途自动化需切换时 SHALL 先到安全边界再断开旧通道，MUST NOT 通过浏览器启动队列实现 Cloud 切换。

#### Scenario: 保存目标不打断当前自动化

- **WHEN** 运营保存新目标且某环境仍连接旧 automation Cloud
- **THEN** 新 HTTP 请求使用新 API，当前自动化连接保持旧目标直至显式重连，UI 分别显示两者

#### Scenario: 自动化停止时无需批量核心重绑

- **WHEN** 所有环境自动化均为 stopped/paused，运营保存新目标
- **THEN** 客户端不启动任何引擎或浏览器；各环境下次启动/恢复自动化时连接新目标

### Requirement: Current cloud is always visible and matches actual connection

客户端设置 SHALL 显示当前数据 API 目标；运行中的自动化 MAY 额外显示引擎实际 automation Cloud 与已保存目标。目标与实际不一致时 SHALL 明确为“数据 API X / 自动化实际 Y / 自动化目标 X”，MUST NOT 把 HTTP 保存或请求成功等同于引擎已连接，也不得在自动化停止时显示 Cloud 离线故障。

#### Scenario: 自动化未启动时只显示数据目标

- **WHEN** 客户端使用 dev HTTP API 且环境自动化未启动
- **THEN** 设置显示数据目标 dev，环境显示自动化未启动，MUST NOT 显示“Cloud 离线”

#### Scenario: 数据与自动化目标暂时不同

- **WHEN** HTTP 已切到 ol 而运行中引擎仍连接 dev
- **THEN** UI 如实显示数据 API ol、自动化实际 dev、目标 ol，MUST NOT 宣称自动化已切换

#### Scenario: ol marked as production

- **WHEN** 数据 API 或自动化实际/目标为 ol
- **THEN** 对应标签以醒目方式标注线上生产含义

### Requirement: Resolved cloud environment controls Facebook automatic browse mode

Facebook 自动浏览模式 SHALL 以自动化引擎实际连接的 Cloud 解析结果为准，不以当前 HTTP API 请求目标推断。新目标只在引擎成功启动或重连后成为实际模式；保存数据目标 MUST NOT 静默改变在途自动化。浏览器是否打开与 Cloud 目标状态正交。

#### Scenario: 下次启动连接 dev 后使用 dev 模式

- **WHEN** 自动化停止期间把目标设为 dev，随后启动引擎并成功握手
- **THEN** 引擎实际模式成为 dev，浏览器准备完成后的会话使用 dev 模式

#### Scenario: 保存未重连不改变在跑模式

- **WHEN** 引擎实际仍连接 dev、只把目标保存为 ol
- **THEN** 在途自动化继续使用 dev 模式直到显式重连成功，UI MUST NOT 显示模式已切换
