## Context

当前 Electron 主进程已经把人设、待审稿编辑和审批等操作迁到 customer-auth HTTP，但登录后仍为每个可信环境无条件启动一个浏览器无关 Edge 子进程，并把子进程存在和其 WebSocket 分别投影为 `coreState` 与 `cloudState`。同一 WebSocket 同时承载控制投影、平台 API 自动化和页面自动化，因此产品上仍把“客户端可用”“Cloud 数据可用”“自动化已启用”和“浏览器可执行”混为一体。

本 change 把边界提升一层：Electron 应用就是客户端；Edge 子进程是按需自动化引擎；AdsPower/CDP 是引擎的页面执行器。Cloud 自有数据走请求式 HTTP，自动化实时调度才走 WebSocket。旧客户端仍依赖 `client_core_browser_executor_v1`，迁移必须 additive 且不可把新状态回投给旧版本。

## Goals / Non-Goals

**Goals:**

- 客户端数据管理在引擎停止、暂停、异常或 WebSocket 离线时通过 HTTP 正常工作。
- 登录/roster 刷新不再自动 spawn 普通环境引擎；自动化启动/恢复才建立引擎连接。
- 用户只看到客户会话、自动化和必要的浏览器阻塞状态；引擎连接作为诊断详情。
- API-only 外部平台动作仍属于自动化，但不取得浏览器槽位或页面租约。
- 启动/暂停/恢复/关闭有明确、安全、可观测的状态转换，且不把连接成功冒充任务执行。
- 保留页面身份复核、任务租约、幂等/CAS、账号归属和审计安全边界。

**Non-Goals:**

- 不把平台持久凭据迁移到 Cloud。
- 不在本 change 删除旧客户端协议或历史状态字段；仅为新能力客户端停止使用和展示。
- 不把所有实时通知强制改成轮询；如需推送，应使用独立用户级事件通道，不得复用环境自动化在线状态作为数据管理准入。
- 不构建或发布桌面安装包。

## Decisions

### 1. Electron 应用是唯一客户端，不再建立产品级“客户端核心”

Electron main 持有客户会话、本地设置、环境 roster、窄 HTTP 适配器和本地自动化监督器。登录成功只刷新这些客户端事实，不为每个环境 spawn 普通 Edge 子进程。原 `coreState` 可在兼容快照中暂留，但新能力客户端的 renderer 不展示、不参与准入，也不把它解释为客户端在线。

不选择继续把浏览器无关 Edge 子进程命名为 core，因为该进程仍包含自动化命令路由、外部平台 API 执行和页面执行代码；常驻它会把自动化生命周期重新绑回客户端数据面。

### 2. Cloud 自有数据统一经逐请求 customer-auth HTTP

所有读取或修改 AIDCP 自有数据库的客户操作使用 Electron main 的窄 IPC→HTTP 适配器。请求只携带客户令牌、`envKey`、幂等/CAS 字段和最小业务载荷；Cloud 每次重新校验客户启用状态、环境归属与权威账号绑定。renderer 不获得令牌、`accountId` 或通用 fetch 能力。

HTTP 没有 `connecting/connected/reconnecting` 生命周期。每个请求独立呈现 pending、confirmed、failed；读取可显式标记缓存及鲜度，不可把缓存显示成实时 Cloud 成功，写失败不可乐观冒充已保存。

现有 persona、draft、approval、interaction workspace HTTP 路径作为迁移模板；盘点发现仍经 WS 的 Cloud 自有数据操作时，必须先补窄 HTTP 端点并复用同一领域方法，再停止新客户端的 WS 路由。

这是一条方向性边界，不只是传输优化：管理后台或 Cloud 不能把普通数据操作包装成命令，经环境 automation WebSocket 推给客户端。常规数据交互采用 Web 式客户端 pull/request-response 模型。将来需要实时提示时另建用户级 notification/invalidation 通道，它只能促使客户端重新 HTTP 拉取，不能代替业务写接口或借引擎在线表示客户端在线。

### 3. Edge 子进程明确为自动化引擎，WebSocket 明确为自动化通道

新客户端只在自动化意图为 start/resume 时 spawn 对应环境引擎。引擎 WebSocket 的公开含义是“自动化调度通道”，内部状态命名为 `engineLinkState = disconnected|connecting|connected|reconnecting|error`。它只进入开发者详情；`connected` 只使自动化进入 `ready`，没有活动任务时不得显示 `running`。

暂停按安全顺序执行：先停止接收新任务、让在途任务在有界安全边界收敛并回报暂停，再断开/停止普通自动化引擎。若回报失败，本地仍以停止继续执行为安全优先，并向 UI/Cloud 保留未确认原因。当前浏览器/CDP/槽位由该引擎持有，因此暂停退出时一并释放；恢复重新建立引擎并自动确保浏览器可用。关闭与暂停都释放自动化资源，但关闭表达停止意图，暂停保留可恢复意图。

受限 offboard 清理 worker 是最小权限恢复机制，不是普通引擎，也不投影为客户端/自动化在线。

因此 Cloud 向该 WebSocket 主动推送的每条消息都必须是自动化引擎职责。`cloud_data` 没有“兼容性便利”例外；后台发起的数据变更应先持久化，客户端自行 HTTP 拉取。平台 API 同步/回复仍可推送，是因为它会自动读取或修改外部平台，属于 `platform_api_automation`，而不是因为它恰好不需要浏览器。

### 4. 自动化按执行器而不是传输分类

集中注册表改为 `local`、`cloud_data`、`automation_control`、`platform_api_automation`、`browser_lifecycle`、`page_automation`：

| 类别 | 主要传输 | 引擎 | 浏览器 |
|---|---|---:|---:|
| `local` | Electron IPC/local | 否 | 禁止 |
| `cloud_data` | customer-auth HTTP | 否 | 禁止 |
| `automation_control` | automation WS | 是 | 禁止 |
| `platform_api_automation` | automation WS + 本地平台 API | 是 | 禁止，除显式 reauth |
| `browser_lifecycle` | Electron IPC 或 automation WS | 按调用者 | 按需 |
| `page_automation` | automation WS + CDP | 是 | 必须 |

是否操作 AIDCP 自有数据决定它是否为 `cloud_data`；是否自动读取/修改外部平台决定它是否为自动化。未知项继续 `operation_unclassified` fail-closed。

### 5. 自动化状态是唯一主运行状态

新客户端每环境公开：

- `automationState = stopped|starting|waiting_resource|ready|running|pausing|paused|stopping|error`
- `browserState = closed|queued|starting|ready|blocked|closing|error`，仅在人工处理、等待或诊断时突出。
- `engineLinkState` 仅在开发者详情中显示。

客户会话是客户端级 `signed_out|restoring|ready|expired`。HTTP 请求状态属于具体操作，不产生全局 `cloudState`。当前任务的 queued/executing/result 是任务事实，不与 automation `ready` 混用。

### 6. 主操作合并自动化与正常浏览器准备，人工浏览器控制保留为辅助动作

- 启动：创建启动意图，spawn 引擎、建立 automation WS、申请槽位、打开浏览器、附着 CDP、复核页面身份，完成后进入 `ready`。
- 暂停：停止任务并断开普通引擎；当前实现同时释放其浏览器/CDP/槽位，避免无引擎却继续占用槽位。
- 恢复：自动重新申请槽位、打开浏览器、复核并连接引擎；用户无需先点“打开浏览器”。
- 关闭：停止引擎、关闭 provider/CDP、释放租约和槽位，客户端 HTTP 数据面继续可用。
- 手动打开：仅供首次登录、重新授权、验证码和人工检查，并明确目的。

### 7. Cloud 环境配置同时解析 HTTP 与 automation WS，但两者状态独立

客户端保存一个结构化 Cloud 目标，由单一环境映射解析 `customerAuthBase` 和 `automationWsUrl`。dev/ol 使用内置同源映射；自定义配置必须分别提供合法的 `http(s)` API base 与 `ws(s)` automation URL，不能从一个协议字符串静默猜测另一个。

切换目标时，后续 HTTP 请求立即使用新 API base；正在运行的自动化不被静默打断，只有显式恢复/重连后引擎才使用新 WS 目标。UI 分别报告“数据请求目标”和“自动化实际/目标”，不得把 HTTP 保存成功冒充引擎已切换。

### 8. 兼容采用新能力位和双投影

新增可选 `client_data_plane_automation_engine_v1`。Cloud additive-first：新 HTTP 端点先上线，hello/welcome 仅在双方支持时协商新能力。新客户端发送新分类和引擎状态；旧客户端继续 `client_core_browser_executor_v1` 语义。Cloud 领域层保持单一写入口和幂等/CAS，HTTP/旧 WS 只是传输适配器。

### 9. 客户端首页采用 HTTP 单一读源，引擎事件只触发失效重拉

“今日进展”、配额/节奏和最近发布摘要属于 Cloud 持久化数据投影。Cloud 提供环境级 customer-auth 概览读取，逐请求把当前客户的 `envKey` 解析为权威账号，再复用既有今日用量构建器和发布记录存储。renderer 只能调用 Electron main 的具名 IPC，不得提交 `accountId`、URL 或令牌。

新能力客户端无论自动化引擎是否连接都使用同一 HTTP 读源。选择环境、窗口重新聚焦、展开进展区、定时刷新及本地自动化结果事件都可触发有界去抖重拉；引擎事件不得携带或直接覆盖今日计数、最近发布或发布历史。HTTP 失败时保留上次成功快照并标记陈旧/失败；首次读取未完成或失败且无缓存时不得把初始零值显示成已确认真态。

旧客户端在兼容窗口内继续接收 `ui.snapshot.dailyUsage`。对 `client_data_plane_automation_engine_v1`，Cloud 不再构建/推送 `dailyUsage`，Edge 也丢弃旧 Cloud 混入的新客户端 `dailyUsage`；`browserStandby` 仍属于自动化控制投影并保留独立续跳，不能因拆除用量推送而破坏浏览器待机唤醒。

## Risks / Trade-offs

- [停止登录后常驻引擎会让 API-only 自动同步停止] → 明确其属于自动化；只有自动化启用时运行。若未来需要“暂停自动化但继续收件”，另建独立 background-sync 产品能力，不偷用客户端数据面。
- [暂停后直接断连可能被 Cloud 误判崩溃] → 先发有界暂停回执再断开；失败时保留未确认诊断，Cloud 不把断线冒充已暂停。
- [HTTP 与旧 WS 双写] → 两种适配器复用同一领域方法、幂等键和 CAS；兼容测试断言单次业务效果。
- [结构化 Cloud 目标迁移破坏旧设置] → 旧单一 WS 设置只作为 automation URL 兼容读取，内置 dev/ol 补齐 HTTP base；无法安全推导的自定义目标要求用户补充，不静默猜测。
- [暂停后浏览器仍占槽位] → 当前实现随引擎暂停退出立即释放，恢复自动重开；若未来要保留热浏览器，必须先引入独立且可观测的 shell-owned 租约，不能隐式占槽。
- [旧 UI 字段残留造成冲突] → 新能力下 renderer 只以自动化状态为主事实，兼容字段进入开发者详情并用协议漂移测试限制消费点。

## Migration Plan

1. Cloud 先新增能力协商、缺失的 customer-auth HTTP 端点和新状态兼容映射；保留旧 WS 处理器。
2. Edge 更新集中注册表与协议类型，完成 HTTP 盘点，停止登录/roster 的普通引擎 bootstrap。
3. Edge 实现按意图的引擎 start/pause/resume/close、浏览器自动准备和新状态投影；保留受限清理 worker。
4. 更新 renderer 文案和按钮，移除核心/Cloud 一级状态与非自动化浏览器准入。
5. 运行 HTTP/WS parity、协议漂移、归属安全、页面租约、槽位、生命周期和多环境回归；执行 Edge/Cloud 完整相关测试和 typecheck。
6. Cloud `dev` additive 部署后再集成 Edge 默认分支并做浏览器关闭、WS 离线、槽位为零和启动/暂停/恢复/关闭联调。客户端不打包发布。
7. 回滚时先停用 Cloud 新能力协商，再回退 Edge；保留 HTTP additive 路径，不通过强开浏览器恢复数据管理。

## Open Questions

无阻塞设计问题。独立实时通知通道和“暂停时仍持续平台收件”属于后续产品能力，不在本 change 默认开启。
