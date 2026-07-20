## ADDED Requirements

### Requirement: 客户端核心在线与浏览器执行器就绪 MUST 是两个独立生命周期

每个已归属且可信绑定的环境 SHALL 在客户登录后建立浏览器无关的客户端核心；核心启动、连接 Cloud、重连和停止 MUST NOT 启动 provider 浏览器、附着 CDP 或占用浏览器槽位。浏览器 SHALL 仅作为真实页面操作按需取得和释放的执行器；浏览器关闭、释放或故障 MUST NOT 自动终止核心或 Cloud 会话。

#### Scenario: 浏览器关闭时核心正常在线

- **WHEN** 客户已登录且环境绑定可信，但 AdsPower 未运行、CDP 不存在且浏览器槽位上限为零
- **THEN** 该环境核心仍建立并维持 Cloud 控制连接，浏览器状态为 `closed`，且不进入槽位队列

#### Scenario: 浏览器崩溃不拖垮核心

- **WHEN** 页面任务期间浏览器或 CDP 意外退出
- **THEN** 对应执行器和页面任务诚实进入失败/恢复状态，但核心与 Cloud 会话保持在线并继续承载浏览器无关操作

### Requirement: 每项操作 MUST 由集中式注册表显式分类

系统 SHALL 将客户端和 Cloud→Edge 操作显式且唯一地分类为 `local`、`cloud`、`platform_api`、`browser_lifecycle` 或 `page_automation`，并为每类声明允许的传输、身份事实和浏览器前置。路由 MUST 使用该声明，不得以子进程、Cloud、浏览器、CDP 或槽位当前状态反推操作类别。未登记操作 MUST 拒绝为 `operation_unclassified`，不得默认拉起浏览器或默认绕过页面准入。

#### Scenario: Cloud 操作绕过浏览器调度

- **WHEN** 已登记为 `cloud` 的人设或待审草稿操作被触发，而浏览器槽位已满
- **THEN** 操作按其客户鉴权/绑定合同执行，MUST NOT 排队等待槽位、启动浏览器或附着 CDP

#### Scenario: 未登记命令 fail-closed

- **WHEN** 客户端收到注册表中不存在的新命令或动作
- **THEN** 系统拒绝 `operation_unclassified` 并记录协议漂移，MUST NOT 猜测为任一执行类别

### Requirement: 页面自动化取得执行器 MUST 保留完整安全准入链

`page_automation` 操作 SHALL 依次经过浏览器槽位与内存准入、provider 启动、CDP 附着、真实页面身份读取与预期账号比对、页面任务租约后方可执行页面读写。历史绑定、核心在线或 Cloud 已受理 MUST NOT 替代页面身份复核。执行结束或空闲回收后系统 MAY 释放执行器，但 SHALL 保持核心在线。

#### Scenario: 历史绑定与真实页面账号不一致

- **WHEN** core 为账号 A 在线，但按需启动的浏览器真实页面身份为账号 B
- **THEN** 系统 MUST NOT 以账号 A 上下文执行页面操作，并 SHALL 先完成账号变化处理或诚实拒绝

#### Scenario: 页面任务等待槽位不阻塞控制操作

- **WHEN** 一个页面任务因无槽位而排队，同时客户发起同环境的 Cloud 配置读取
- **THEN** 页面任务保持排队，配置读取独立完成，二者状态不得互相冒充

### Requirement: 操作受理与平台执行结果 MUST 分阶段表达

需要先由 Cloud 记录客户决定、后由浏览器执行平台写入的操作 SHALL 拆分为“受理/排队”和“平台执行/确认”两个阶段。客户端 MUST NOT 把受理成功、已授权或已排队显示成平台写入成功。

#### Scenario: 批准时浏览器关闭

- **WHEN** 客户批准一份待审稿且 Cloud 成功记录决定，但当前没有浏览器执行器
- **THEN** 客户端显示决定已受理且发布待执行，MUST NOT 显示已发布；后续取得执行器并获平台确认后才显示发布成功
