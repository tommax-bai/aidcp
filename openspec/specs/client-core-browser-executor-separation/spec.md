# client-core-browser-executor-separation Specification

## Purpose
TBD - created by archiving change separate-client-core-browser-executor. Update Purpose after archive.
## Requirements
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

### Requirement: 操作受理与平台执行结果 MUST 分阶段表达

需要先由 Cloud 记录客户决定、后由浏览器执行平台写入的操作 SHALL 拆分为“受理/排队”和“平台执行/确认”两个阶段。客户端 MUST NOT 把受理成功、已授权或已排队显示成平台写入成功。

#### Scenario: 批准时浏览器关闭

- **WHEN** 客户批准一份待审稿且 Cloud 成功记录决定，但当前没有浏览器执行器
- **THEN** 客户端显示决定已受理且发布待执行，MUST NOT 显示已发布；后续取得执行器并获平台确认后才显示发布成功

### Requirement: Migrated platforms share selector-free Native supervision
The browser-independent Edge core SHALL supervise the Native process and typed sessions for every migrated platform while retaining ownership of browser-provider launch, Cloud connectivity, task admission, lifecycle, and receipt forwarding. Platform facades in JavaScript SHALL be selector-free and MUST NOT attach to or actuate a migrated page target directly.

#### Scenario: Facebook browser is launched
- **WHEN** the provider returns a loopback DevTools endpoint for an admitted Facebook task
- **THEN** Edge opens a Facebook Native session with the endpoint and typed task identity
- **AND** the Facebook facade performs page work only through Native

#### Scenario: WeChat API runtime does not need browser inspection
- **WHEN** the WeChat runtime can continue with a valid stored API session
- **THEN** ordinary API orchestration remains independent of Native page execution and no browser session is opened merely for encapsulation

### Requirement: The browser-independent core SHALL supervise Native only after page admission

The Edge core SHALL remain online without a browser or Native page session. For Xiaohongshu `page_automation`, it SHALL start/attach the browser provider, complete existing CDP readiness and real-page identity admission, acquire the page-task lease, then supervise the Native Page Engine for that executor. Starting the core or performing `local`, `cloud`, or `platform_api` operations MUST NOT start Native or acquire a browser slot.

#### Scenario: Core is online with browser closed
- **WHEN** a trusted environment has no admitted page-automation work
- **THEN** the Edge/Cloud core remains online while no Xiaohongshu Native session or browser slot exists

#### Scenario: Page automation is admitted
- **WHEN** a Xiaohongshu page operation passes the complete existing admission chain
- **THEN** the core starts or reuses the matching Native executor session and hands it the admitted loopback endpoint

### Requirement: Native failure MUST remain scoped to the page executor

A Native process crash, protocol failure, or CDP-session failure SHALL fail or recover the active page task honestly while the browser-independent Edge core and Cloud connection remain alive. The core MUST NOT hide the failure by reporting the environment as successfully executing, and MUST NOT start the legacy Xiaohongshu JavaScript executor.

#### Scenario: Native crashes during page read
- **WHEN** Native exits before any write dispatch
- **THEN** the page task receives an explicit executor failure while the Edge core stays connected and can accept browser-independent operations

#### Scenario: Native crashes after a possible write
- **WHEN** Native exits after dispatch may have occurred
- **THEN** the task is surfaced as ambiguous/needs-review under the existing contract and is not replayed through JavaScript

### Requirement: Non-Xiaohongshu executors MUST remain isolated

The Native Xiaohongshu cutover MUST NOT route Facebook, Douyin, WeChat Channels, or other platform operations into the Xiaohongshu Native adapter and MUST NOT remove their required executors from the package.

#### Scenario: Facebook page command is admitted
- **WHEN** the active platform is Facebook
- **THEN** the existing Facebook executor handles it and no Xiaohongshu Native session is created

