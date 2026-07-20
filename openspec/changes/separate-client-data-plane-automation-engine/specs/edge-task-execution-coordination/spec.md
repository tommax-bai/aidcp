## MODIFIED Requirements

### Requirement: 页面任务协调 SHALL 仅接收已分类的 page_automation 操作

页面任务租约、同账号排他、CDP 准入和浏览器槽位协调 SHALL 仅用于注册表中声明为 `page_automation` 的操作。`local` 和 `cloud_data` 操作 MUST NOT 依赖自动化引擎；`automation_control` 与 `platform_api_automation` SHALL 依赖引擎但 MUST NOT 创建页面任务租约、等待浏览器槽位或因 `browser_control_unavailable` 被拒；`browser_lifecycle` 只协调执行器生命周期，不得冒充页面任务成功。

#### Scenario: API-only 自动化不取得页面租约

- **WHEN** 已登记为 `platform_api_automation` 的互动同步被触发且同账号页面任务正在运行
- **THEN** API-only 操作按其自身并发与身份合同经引擎执行，MUST NOT 等待页面任务租约或抢占浏览器槽位

#### Scenario: API-only 自动化不在引擎停止时偷偷执行

- **WHEN** 自动化状态为 `stopped` 或 `paused`
- **THEN** 新的 `platform_api_automation` 外部平台动作不得执行，但 `cloud_data` HTTP 操作继续可用

#### Scenario: 页面自动化仍受同账号租约保护

- **WHEN** 两个已登记为 `page_automation` 的任务同时请求同一账号
- **THEN** 系统仍按既有租约合同串行或拒绝，自动化引擎生命周期不得放宽同账号并发保护

### Requirement: 浏览器执行器获取失败 MUST 与客户端数据面和引擎连接状态分离

页面任务申请执行器失败时，协调器 SHALL 返回槽位排队、provider 启动失败、CDP 附着失败或身份不匹配等可区分状态；MUST NOT 把这些状态投影为客户会话或 HTTP 数据面离线。若引擎仍连接，失败只影响当前页面执行和浏览器状态；执行器释放后 SHALL 释放页面租约与槽位，是否继续保持引擎连接由自动化意图决定。

#### Scenario: 槽位已满时页面任务排队

- **WHEN** 页面任务需要浏览器而所有槽位已占用
- **THEN** 自动化进入真实 `waiting_resource`，HTTP 数据管理继续可用，MUST NOT 显示客户端离线或正在执行

#### Scenario: CDP 附着失败

- **WHEN** provider 已启动但 CDP 在时限内不可用
- **THEN** 协调器诚实回报 `cdp_unavailable` 并回收本次执行器资源，MUST NOT 宣称页面操作成功或破坏客户会话
