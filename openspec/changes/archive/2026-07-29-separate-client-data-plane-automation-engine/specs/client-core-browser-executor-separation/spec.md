## MODIFIED Requirements

### Requirement: 每项操作 MUST 由集中式注册表显式分类

系统 SHALL 将客户端和 Cloud→Edge 操作显式且唯一地分类为 `local`、`cloud_data`、`automation_control`、`platform_api_automation`、`browser_lifecycle` 或 `page_automation`，并为每类声明允许的传输、身份事实、引擎与浏览器前置。路由 MUST 使用该声明，不得以子进程、WebSocket、浏览器、CDP 或槽位当前状态反推操作类别。未登记操作 MUST 拒绝为 `operation_unclassified`，不得默认拉起引擎/浏览器或绕过页面准入。

#### Scenario: Cloud 数据操作绕过自动化调度

- **WHEN** 已登记为 `cloud_data` 的人设或待审草稿操作被触发，而自动化引擎停止且浏览器槽位已满
- **THEN** 操作按 customer-auth HTTP 及绑定合同执行，MUST NOT 启动引擎、等待槽位、启动浏览器或附着 CDP

#### Scenario: 未登记命令 fail-closed

- **WHEN** 客户端收到注册表中不存在的新命令或动作
- **THEN** 系统拒绝 `operation_unclassified` 并记录协议漂移，MUST NOT 猜测为任一执行类别

### Requirement: 页面自动化取得执行器 MUST 保留完整安全准入链

`page_automation` 操作 SHALL 在自动化引擎启用后依次经过浏览器槽位与内存准入、provider 启动、CDP 附着、真实页面身份读取与预期账号比对、页面任务租约后方可执行页面读写。历史绑定、引擎连接或 Cloud 已受理 MUST NOT 替代页面身份复核。执行结束或空闲回收后系统 MAY 释放执行器；释放浏览器 MUST NOT 被投影为客户端数据面离线。

#### Scenario: 历史绑定与真实页面账号不一致

- **WHEN** 引擎预期账号 A，但按需启动的浏览器真实页面身份为账号 B
- **THEN** 系统 MUST NOT 以账号 A 上下文执行页面操作，并 SHALL 先完成账号变化处理或诚实拒绝

#### Scenario: 页面任务等待槽位不阻塞数据操作

- **WHEN** 一个页面任务因无槽位而排队，同时客户发起同环境的 Cloud 配置读取
- **THEN** 页面任务保持排队，配置读取经 HTTP 独立完成，二者状态不得互相冒充

## REMOVED Requirements

### Requirement: 客户端核心在线与浏览器执行器就绪 MUST 是两个独立生命周期

**Reason**: 普通 Edge 子进程本质是自动化引擎，不是客户端核心；客户登录后常驻该进程仍把客户端可用性绑定到自动化连接。

**Migration**: Electron 应用作为客户端数据面；自动化引擎仅在启动/恢复时运行，浏览器继续作为其按需页面执行器。旧客户端在能力兼容窗口内保留原投影。
