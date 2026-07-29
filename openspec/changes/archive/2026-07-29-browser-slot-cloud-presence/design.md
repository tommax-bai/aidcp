## Context

桌面端当前只有在 `admitBrowserSlot()` 成功后才 `spawnEdgeChild()`。因此槽位外环境没有核心进程、没有 Cloud WebSocket、没有 `ui.snapshot`，Cloud 的 `onlineAccountIds()` 也永远看不到它。`browser-slot-scheduling` 已把这个问题登记为 5.2“未启动黑洞”，但当时受阻于握手前必须从活浏览器读取账号身份。

现有 customer-auth 已持久保存 `client_environments.env_key -> account_id`，并通过 `resolveBoundAccountForEnv(userId, envKey)` 同时执行环境归属、未绑定、跨客户冲突与存储可用性检查。现有 Edge 冷待机又已经证明核心和 Cloud 可以在浏览器关闭后继续存活，并能经 FIFO 槽位队列重新唤醒浏览器。缺失的是“首次就以浏览器缺席态出生”的受信任身份引导。

真机排查还暴露出独立缺陷：`EdgeClient.openAndHello()` 将相同 request id 的任意响应都强制转换成 `WelcomePayload`，未检查 `type === 'welcome'` 或非空 `sessionId`。实际出现了 `sessionId=?`、本地绿色“已连接”、Cloud 无 runtime/无调度日志的假连接。

## Goals / Non-Goals

**Goals:**

- 浏览器槽位只约束浏览器执行层，不再决定环境能否连接 Cloud。
- 用客户登录态和持久绑定给无浏览器核心提供最小、可审计、fail-closed 的账号引导。
- 复用冷待机唤醒链，在浏览器取得槽位后重新确认真实平台身份再执行。
- 严格验证 Cloud welcome，使连接状态、人设状态和任务回执都以真实 Cloud 会话为准。
- 兼容旧 Cloud/未绑定环境：不能安全引导时保持排队且如实说明，不猜账号。

**Non-Goals:**

- 不提高浏览器并发或启动排队上限，不驱逐正在运行的环境。
- 不把 renderer、环境昵称、AdsPower profile id 或本地历史值变成账号授权来源。
- 不改变账号人设的 Cloud 单写者原则。
- 不在本 change 打包或发布 Edge 安装程序。

## Decisions

### 1. 由 Electron 主进程取得最小控制面引导

Cloud 新增客户鉴权的 env-scoped 只读接口，输入 URL 中的 `envKey`，返回 `{ envKey, accountId }`。实现必须复用 `resolveBoundAccountForEnv(userId, envKey)`，将 `environment_not_owned`、`binding_unknown`、`binding_conflict`、`binding_unavailable` 保持为可区分失败。renderer 不接触客户 token，也不接收额外账号数据。

选择该方案而不是本地缓存账号，是因为本地环境名/旧日志均可能陈旧，且无法证明客户所有权。选择独立窄接口而不是扩展 `/my-environments`，是为了不把所有环境的账号 id 批量暴露给列表层，并让失败语义保持 env-scoped。

### 2. 控制面身份与人工账号覆盖使用不同变量

主进程只在引导成功时为子核心传入 `AIDCP_START_BROWSER_ABSENT=1` 与 `AIDCP_CONTROL_ACCOUNT_ID=<bound account>`。现有 `AIDCP_ACCOUNT_ID` 保留其人工/测试覆盖语义，绝不能拿来承载引导身份。

浏览器唤醒后，Edge 必须重新从页面读取真实身份，且只允许既有人工覆盖影响该真实读取。若真实账号与 control account 不同，先关闭旧 Cloud 会话并以真实账号重新握手，再回报唤醒完成；身份缺失、登录失效或重连失败时不得执行页面命令。

选择两变量方案是为了避免引导身份反过来覆盖真实页面身份，导致换号后在错误账号上执行不可逆动作。

### 3. 核心以 detached CDP + 初始 standby 出生

无槽位路径不调用 AdsPower `start`，而是创建 detached `EdgeSession`，初始化 lifecycle 为 standby，连接 Cloud 后向 Electron 发 `lifecycle.standby`。浏览循环、平台 watcher 和任何需要页面的 supervisor 都不得在该状态启动。

取得 FIFO 槽位后沿用现有 wake 路径：启动 AdsPower、读取新调试端口、reattach CDP、解析身份、必要时重建 Cloud 会话，然后启动平台运行时。失败后核心保持可再次唤醒的待机态，槽位归还且调用方收到明确失败。

选择复用冷待机而不是另建第二套“轻核心”，是为了保持一个核心进程、一套 Cloud client、一条唤醒队列和一套状态 IPC。

### 4. Cloud welcome 是连接成功的唯一判据

`openAndHello()` 只有在响应 envelope 的 `type` 为 `welcome`、payload 为对象且 `sessionId` 与 `serverVersion` 为非空字符串时才能设置 connected/启动心跳/发出在线状态。`error` envelope 需要保留 Cloud 错误码和消息并抛出；其它类型或畸形 payload 以协议错误失败。

Cloud 侧也应记录握手拒绝的 edgeId/accountId/reason（不记录 token/secret），使“客户端没回复”能在双方日志闭环。WebSocket transport 打开不等于 Cloud 会话建立。

### 5. 引擎在线与浏览器就绪为正交状态

Edge hello capabilities 增加可选 `browser_absent_v1`；Cloud runtime 保留该在线会话并可发送 `ui.snapshot`、人设真态和唤醒型任务。需要浏览器的任务仍走 acquire/wake/FIFO 槽位链；在唤醒死线内未取得浏览器时回 `browser_wake_failed`，不归类为 edge offline，也不静默丢弃。

客户端分别呈现 Cloud 会话、浏览器运行/排队/待机与人设三态。“正在连接云端”只能覆盖真实握手在途；引导失败、握手失败与浏览器排队分别显示原因。

## Risks / Trade-offs

- [持久绑定可能陈旧] → 绑定只用于建立可纠正的控制面；第一次浏览器唤醒必须读取真实身份并在不一致时先重连，任何页面动作都在复核之后。
- [一次启动更多核心进程] → 核心不持有浏览器，资源远小于浏览器；仍受环境启动/队列管理与明确停止动作约束。
- [旧 Cloud 没有引导接口] → 主进程识别 404/不支持并回退旧的纯排队行为，UI 不宣告 Cloud 已连接。
- [无绑定环境仍不可在线] → 这是安全边界而非可用性回归；UI 明示“需先成功启动一次以确认账号”，不得用猜测填洞。
- [唤醒期间身份变化导致短暂重连] → wake 成功必须等待新 welcome，Cloud 调度获得明确的可恢复失败而非在旧身份下继续。
- [假握手修复后暴露更多红色错误] → 这是对既有失败的诚实呈现；错误码和日志用于定位 Cloud 拒绝原因。

## Migration Plan

1. 先部署向后兼容的 Cloud customer-auth 引导接口与 browser-absent 会话支持；旧 Edge 不受影响。
2. 发布 Edge 源码：严格 welcome 校验先落地；再启用无槽位控制面启动。若 Cloud 不支持，引导失败只回退旧排队路径。
3. 在 dev 验证：槽位数小于环境数时，槽位外已绑定环境仍有有效 sessionId、可收到 personaBound；任务触发后进入 FIFO 唤醒；错误 welcome 不再显示绿色成功。
4. 回滚 Edge 时停用无浏览器启动即可；回滚 Cloud 时保留旧 Edge 回退。接口和 capability 均为新增可选字段，无数据迁移。

## Open Questions

- 无阻塞的协议决策；Edge 安装包与真机升级由后续明确发布任务处理。
