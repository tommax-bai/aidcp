## Why

上一轮只把浏览器执行器从常驻 Edge 子进程中拆出，却仍把该自动化子进程及其 WebSocket 包装为“客户端核心”和“Cloud 连接”。这会继续把客户端数据管理、平台 API 自动化和页面自动化混成一条生命周期，使用户误以为客户端必须维持引擎长连接才能管理人设、草稿、审批和配置。

## What Changes

- **BREAKING（产品与生命周期语义）**：删除用户可见的“客户端核心”概念；桌面应用在客户会话有效时即为可用客户端，不再用每环境 Edge 子进程是否存在定义客户端在线。
- **BREAKING（连接语义）**：删除用户可见的 `cloudState`；客户数据管理统一使用逐请求 customer-auth HTTP，现有 Edge↔Cloud WebSocket 只表达自动化引擎连接，并在内部更名为 `engineLinkState`。
- 客户端自身数据管理、本地设置和 Cloud 原生业务写在引擎停止、暂停、异常、WebSocket 离线、浏览器关闭或槽位为零时仍可使用；失败只报告该次 HTTP 请求的真实结果。
- 自动化引擎仅在自动化启动或恢复后运行并连接 Cloud 调度器；连接成功表示自动化已启用/等待任务，不等于正在执行任务。
- 平台外部操作按执行性质拆为无浏览器的 `platform_api_automation` 和需要页面的 `page_automation`；两者都属于引擎，只有后者取得浏览器槽位、CDP 和页面任务租约。
- 主操作收口为启动、暂停、恢复、关闭自动化：启动/恢复自动准备浏览器，暂停先安全停止任务再断开引擎连接且不影响 HTTP 数据管理，关闭同时停止引擎并释放浏览器。
- 浏览器手动打开仅保留给首次登录、重新授权、验证码和人工检查；浏览器、引擎连接和任务执行状态仅在等待、阻塞或诊断场景分别展示。
- 客户端首页“今日进展”和最近发布摘要统一通过环境级 customer-auth HTTP 拉取；自动化事件只触发重新拉取，新能力客户端不再从 automation WebSocket 接收 `dailyUsage` 或发布记录。
- 首页 overview 只承载待审发布摘要；当摘要为待确认时，发布卡 SHALL 保留“查看稿件”审批入口，并在用户打开后通过既有 customer-auth HTTP 待审列表/详情接口拉取完整稿件，不依赖 WebSocket 内联 `publishPreview`。
- 以可选能力位和 Cloud additive-first 双路径迁移，旧客户端在兼容窗口内继续使用旧 core/Cloud 状态与命令链，不将新语义错误投影给旧客户端。

## Capabilities

### New Capabilities

- `client-data-plane-automation-engine`: 定义桌面客户端 HTTP 数据面、自动化引擎长连接、API/浏览器两类自动化执行器，以及用户意图与运行状态的独立合同。

### Modified Capabilities

- `client-core-browser-executor-separation`: 废止“登录后每环境常驻客户端核心”的产品合同，改由按需自动化引擎与浏览器执行器承载外部平台自动化。
- `client-customer-auth`: 明确客户数据管理逐请求经 HTTP 完成，不得以自动化引擎、WebSocket、浏览器或槽位状态作为准入条件。
- `edge-multi-environment-supervisor`: 每环境子进程改为按自动化意图启动、暂停和关闭，不再在登录/花名册刷新时无条件 bootstrap。
- `edge-fleet-console`: 移除客户端核心和 Cloud 长连接一级状态，改为客户会话、自动化状态与必要的浏览器阻塞信息。
- `edge-task-execution-coordination`: 将平台 API 自动化与页面自动化都归入引擎域，同时保持仅页面自动化取得浏览器槽位和页面租约。
- `edge-cloud-env-selection`: Cloud 选择只配置 HTTP API 和自动化调度目标；切换时不得把数据管理可用性绑定到引擎重连结果。

## Impact

- `aidcp-edge`: Electron 客户会话/HTTP 桥、环境监督器、Edge 子进程启动与暂停语义、操作注册表、WebSocket 状态命名、浏览器调度、renderer 状态与按钮。
- `aidcp-cloud`: customer-auth 数据管理端点覆盖、自动化连接能力协商、命令分类与兼容投影；数据领域方法继续复用现有幂等、CAS、归属与审计闸。
- 协议和文档：新增可选 `client_data_plane_automation_engine_v1` 能力及引擎状态字段；同步 Edge/Cloud 类型、命令路由和 `docs/protocol.md`。
- 兼容和部署：Cloud 先 additive 部署，Edge 后部署；新旧客户端双路径经过兼容测试后另行移除旧 core 语义。
- 安全：HTTP 逐请求校验客户、环境归属和权威账号绑定；页面写入仍在真实页面身份复核后执行，不以本地缓存身份替代。
