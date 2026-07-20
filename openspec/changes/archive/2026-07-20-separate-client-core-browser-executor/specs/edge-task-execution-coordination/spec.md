## ADDED Requirements

### Requirement: 页面任务协调 SHALL 仅接收已分类的 page_automation 操作

页面任务租约、同账号排他、CDP 准入和浏览器槽位协调 SHALL 仅用于注册表中声明为 `page_automation` 的操作。`local`、`cloud` 和 `platform_api` 操作 MUST NOT 创建页面任务租约、等待浏览器槽位或因 `browser_control_unavailable` 被拒；`browser_lifecycle` 只协调执行器生命周期，不得冒充页面任务成功。

#### Scenario: API-only 操作不取得页面租约

- **WHEN** 已登记为 `platform_api` 的互动同步被触发且同账号页面任务正在运行
- **THEN** API-only 操作按其自身并发与身份合同执行，MUST NOT 等待页面任务租约或抢占浏览器槽位

#### Scenario: 页面自动化仍受同账号租约保护

- **WHEN** 两个已登记为 `page_automation` 的任务同时请求同一账号
- **THEN** 系统仍按既有租约合同串行/拒绝，核心常驻不得放宽同账号并发保护

### Requirement: 浏览器执行器获取失败 MUST 与核心在线状态分离

页面任务申请执行器失败时，协调器 SHALL 返回槽位排队、provider 启动失败、CDP 附着失败或身份不匹配等可区分状态；MUST NOT 把这些状态投影为 core/Cloud 离线。执行器释放后 SHALL 释放页面租约与槽位，但 MUST NOT 关闭核心控制连接。

#### Scenario: 槽位已满时页面任务排队

- **WHEN** 页面任务需要浏览器而所有槽位已占用
- **THEN** 页面任务进入真实排队态，core 与 Cloud 保持在线，浏览器无关操作继续可用

#### Scenario: CDP 附着失败

- **WHEN** provider 已启动但 CDP 在时限内不可用
- **THEN** 协调器诚实回报 `cdp_unavailable` 并回收本次执行器资源，MUST NOT 杀死 core 或宣称页面操作成功
