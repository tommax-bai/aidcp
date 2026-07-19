## Context

桌面环境栏的 `updatedAt` 目前由核心子进程 stdout 间接刷新，超过五分钟没有输出就投影为“失联”。视频号是 API-only 运行时，正常空闲时业务日志很少；现有修复只在成功同步批次收到 Cloud ACK 后输出心跳，因此要求鉴权和只读探针已经成功。若旧会话失效、鉴权浏览器又启动失败，核心与 Cloud 的 WebSocket 仍在线，但业务同步无法开始，环境栏最终误报“失联”。

同一失败还有第二个表现：`WechatAuthCoordinator` 在 `browser_opening` 后直接等待 `sidecar.open()`；打开失败时没有状态回拨，运行时只把普通 `Error` 压成 `INTERACTION_INTERNAL_ERROR`，授权快照因此长期保持 `authenticating`，实际 AdsPower 错误也不可诊断。

约束：不得用本地定时器“自称在线”；不得把登录失败或鉴权通过冒充成另一种状态；不得把 AdsPower API key、会话材料或原始请求信息写入日志；不得为本修复新增协议消息或扩大写权限。

## Goals / Non-Goals

**Goals:**

- 在浏览器关闭、鉴权进行中或鉴权失败时，使用真实 Cloud 请求/响应往返维持视频号核心的桌面鲜活度。
- 心跳失败时不产生成功日志，让既有五分钟 stale 判定仍可发现真正失联。
- 鉴权浏览器打开失败后离开 `authenticating`，按是否已有失效会话回到 `reauth_required` 或 `login_required`，保留现有重新鉴权入口。
- 将本地浏览器失败归一成有限、脱敏的诊断字段，并把运行时错误码从笼统内部错误改成既有 `WECHAT_AUTH_REQUIRED`。

**Non-Goals:**

- 不改变 Cloud 在线判定、环境栏五分钟阈值或其他平台的浏览循环。
- 不自动重启 AdsPower、不增加无界浏览器重试，也不把浏览器启动成功等同于视频号鉴权成功。
- 不修改 Cloud/Edge 协议、数据库或视频号读写能力门禁。
- 不构建或发布桌面安装包。

## Decisions

### 1. 用既有 `ping` / `pong` 做独立控制面心跳

视频号运行时在 Cloud 握手完成后启动一个 60 秒周期的单飞探针，通过现有 `EdgeClient.request('ping', {})` 等待匹配的 `pong`。只有匹配响应返回后才输出一条良性 `control-plane heartbeat` 日志；请求失败、超时、响应类型不匹配或已有探针在飞行时不输出成功日志。

这条日志沿用桌面主进程既有 stdout → `updateStatus` 通道，因此无需新增 IPC 或 renderer 状态源。选择应用层 `ping/pong` 而不是 `readyState` 或本地定时打印，是因为前者同时证明核心进程存活、WebSocket 可用、Cloud 已收到请求并返回匹配响应。

备选方案是直接让环境栏读取 Cloud connectivity；它只能证明面板缓存中的连接投影，不能证明当前本地子进程仍在往返，且会把两个异步数据源再次混合，故不采用。

### 2. 控制面心跳与业务同步心跳并存

现有同步 ACK 心跳继续保留，它证明平台读、Cloud WS 和批次确认整条链路成功；新心跳只证明控制面在线。环境栏鲜活度接受任一真实证据，但互动工作区仍分别显示引擎连接与视频号鉴权/同步状态，不用控制面心跳提升鉴权或业务能力。

### 3. 浏览器打开失败回拨到可操作授权态

`sidecar.open()` 抛错时，鉴权协调器立即退出 `browser_opening`：已有旧会话/身份上下文时转为 `reauth_required`，首次登录尚无会话时转为 `browser_login_required`；两者原因码均使用既有 `WECHAT_AUTH_REQUIRED`。随后抛出结构化 `WechatChannelsError`，让运行时记录真实的既有协议错误码而不是 `INTERACTION_INTERNAL_ERROR`。

不新增 `browser_unavailable` 协议枚举：授权状态说明“仍需登录”，`browserState=unavailable` 独立说明本地浏览器不可用，现有 workspace 已能同时展示这两项且提供重新鉴权按钮。

### 4. 浏览器诊断只输出白名单字段

Browser sidecar 将原始异常归一为 `provider`、`operation`、`kind`，以及可安全解析时的 `http_status` / AdsPower `code`；不记录原始响应正文、Authorization header、API key、cookie、会话材料或任意 URL query。未知错误只记录 `kind=unexpected`。

## Risks / Trade-offs

- [Cloud 负载增加] → 仅视频号每个在线核心每 60 秒一个现有轻量 `ping`，单飞且超时有界；业务同步 ACK 仍按原节奏运行。
- [成功心跳日志增加] → 每分钟最多一条、使用固定短文本，不进入故障分类，也不携带账号或敏感信息。
- [短时心跳失败仍显示运行中] → 沿用五分钟 stale 窗口吸收偶发抖动；持续失败不会刷新 `updatedAt`，最终仍诚实进入“失联”。
- [浏览器失败后需要人工重试] → 这是既有重新鉴权入口的职责；本 change 不增加可能反复弹窗的自动浏览器重试。

## Migration Plan

1. 在 Edge 独立 worktree 实现并通过聚焦测试、acceptance、全量测试与 typecheck。
2. Fast-forward 集成到 `aidcp-edge/master` 并推送；不构建安装包。
3. 本地源码客户端需重启后才加载新 runtime；Cloud 无代码变更，不需要 ECS 服务重启。
4. 若出现异常，可回退单个 Edge 提交；协议和持久化状态均未变化。

## Open Questions

无。心跳周期、失败语义和授权回拨状态均由现有五分钟 stale 阈值与既有 UI 能力确定。
