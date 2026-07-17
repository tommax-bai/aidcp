## Context

上一阶段已经实现视频号 interaction 的 Edge connector、Cloud inbox/workflow、Console 配置和 Electron 工作区，但真实运行路径仍停在合成合同层。当前 Edge 多环境监督器会剔除继承的 `AIDCP_ACCOUNT_ID`，而 `runWechatChannelsRuntime` 又在连接 Cloud 前强制要求该值，并把 Cloud 逻辑账号 ID 与 `/auth/auth_data` 返回的 finder identity 当成同一个值。这使首次扫码形成启动死锁。

Cloud migration `0039_interaction_inbox.sql` 已有按 `(platform, account_id)` 保存的 `interaction_runtime_controls`，Console/internal API 也用 CAS 更新这张表；Edge 却只读取本机 `AIDCP_WECHAT_*` 环境变量，因此管理侧显示的账号开关不是 Edge 执行真值。请求层则把全部私有端点统一假设为 JSON POST，缺少真实授权会话的 method/query/body/header 证据。

约束包括：私有接口随时可能漂移；Cookie/session 只能留在 Edge；所有新能力缺失或不确定时必须关闭；协议变更必须同步 Edge、Cloud、路由和 `docs/protocol.md`；真实写操作只允许对用户明确批准的一次性目标执行；Edge 本轮不构建安装包。

## Goals / Non-Goals

**Goals:**

- 让全新视频号环境无需预先知道 finder ID 即可建立 Cloud 作用域并进入可理解的首次授权流程。
- 首次成功授权后把 finder identity 与该环境持久绑定；后续身份变化继续阻断读写，绝不自动改绑。
- 让 Cloud 账号级 runtime controls 成为 Edge 能力开关唯一授权来源，并支持握手快照与在线更新。
- 用真实授权会话的脱敏网络证据冻结评论/私信 request descriptor，并用序列化测试防止再次回到猜测格式。
- 保留旧 Cloud/旧 Edge 安全兼容：拿不到新控制快照时能力全关，而不是沿用过期本地开关。

**Non-Goals:**

- 不在没有一次性可丢弃目标时执行真实评论或私信写入。
- 不把微信私有接口描述为官方稳定 API，也不承诺自动回复合规已经通过。
- 不开放图片私信、不新增浏览/发布能力、不改变现有 XHS/Facebook 身份语义。
- 不把 Cookie、token、二维码、完整评论/私信正文或原始 HAR 提交到仓库、Cloud、日志或 fixtures。

## Decisions

### 1. 视频号逻辑账号使用稳定环境作用域，finder identity 独立绑定

对 `wechat_channels`，Edge 以 `AIDCP_ENV_KEY`（实际为 AdsPower profile/env key）作为缺省逻辑 `accountId`；显式 `AIDCP_WECHAT_ACCOUNT_ID` 只保留为迁移逃生阀。这样 Edge 能在首次授权前完成 hello，Cloud 可按 `accounts.platform` 建立稳定作用域并下发该账号控制。

`WechatSessionBinding.accountId` 表示 Cloud 逻辑作用域，`finderIdentity` 表示平台真实身份，二者不再要求字符串相等。第一次没有既有密文绑定时，成功的 `/auth/auth_data` 候选可绑定 finder identity；以后初始化、恢复、发送和周期核验都必须与持久化的 `finderIdentity` 相等。检测到另一身份时只进入 `WECHAT_IDENTITY_MISMATCH`，不覆盖绑定、不同步该账号数据。

备选方案是“先在浏览器完成登录，拿到 finder ID 后才连接 Cloud”。它会让首次登录期间 Cloud/customer UI 完全看不到状态，也无法从 Cloud 下发账号开关，仍形成控制面死区，因此不采用。另一方案是新增 provisional account 协议并在登录后迁移所有主键，复杂度和串号风险远高于稳定 env 作用域。

### 2. 用户引导来自结构化 auth/binding 状态

Electron 工作区继续只读 customer-auth 的结构化 `interaction_auth_state`。首次登录显示“此环境将绑定当前扫码的视频号”，并展示环境可读名；成功后展示脱敏的 finder 昵称/ID 摘要。身份不匹配时明确要求退出错误账号并重新打开原环境，而不是提示配置 `AIDCP_ACCOUNT_ID`。`interaction.auth.reopen` 的 HTTP 受理只显示“已请求打开”，只有后续 `status=active` 且 identity match 才显示完成。

不从进程日志解析身份，也不允许 renderer 读取本地 Cookie/密文。

### 3. 版本化账号控制使用 welcome 快照 + 在线更新

新增协商能力 `interaction_runtime_controls_v1`、`WelcomePayload.interactionRuntime` 和 Cloud→Edge 主动消息 `interaction.runtime.controls`。payload 固定携带 `accountId`、`envKey`、单调 `version` 及四项文本能力布尔值；图片发送永远 false。Cloud provider 从 `interaction_runtime_controls` 读取账号行，并把 `write_paused`、Cloud 全局写开关共同投影到写能力。查询失败、作用域缺失或 offboard pending 时返回全 false 的 fail-closed 快照。

Edge 在完成 hello 后才应用快照；主动更新必须同时匹配当前 `accountId + envKey` 且 `version >= currentVersion`。错绑、回退版本、未协商能力或畸形 payload 均丢弃并保持当前/关闭状态。断线后本地缓存不得授权新写；重连必须用 welcome 最新快照重建。

internal API 只有在 runtime-controls CAS 更新和审计成功后才向该账号唯一在线 Edge 推送更新。若 Edge 离线，数据库仍是权威真值，下次 hello 补齐；推送失败不回滚已提交配置，也不得回报 Edge 已应用。

备选方案是继续通过 per-process 环境变量启用。它无法按账号、无法热更新、也与 Console 真值分裂。只做 welcome 而无在线更新会要求重启才能止损，不满足 kill switch 的实时性。

### 4. 本机配置只保留构建/紧急熔断，不再授予账号能力

Edge 编译支持、身份匹配、端点 probe、schema circuit breaker 和本机紧急 kill switch 继续与 Cloud 快照做 AND。旧的 per-account `*_READ_ENABLED`/`*_REPLY_ENABLED` 环境变量不再作为授权来源。缺少 Cloud snapshot 时 effective capabilities 必须全 false；评论/私信写还必须通过已批准目标的 write probe，格式校准本身不等于写 probe 已通过。

### 5. 私有接口使用证据驱动的 request descriptor

`WechatChannelsApiClient` 不再用一个“所有接口都是 JSON POST”的通用假设。每个 endpoint 由显式 descriptor 定义：path、HTTP method、query key、body encoding、必要非秘密 header 名、是否需要普通/私信 cookie jar、重试安全性和成功码解析。

原始网络证据只在取证机临时保存。仓库只提交脱敏 manifest/fixture：采集时间、页面、method/path/content-type、query/body 的键名和类型、必要 header 名、响应状态/关键 schema；所有值、Cookie、token、finder 明文 ID、消息正文和原始 HAR 必须删除。descriptor 只有在真实授权会话证据覆盖后才能把对应 capability 标为 implemented；未覆盖写 endpoint 保持关闭。

参考开源 `wx_video_api`/`wx_sph_server` 仅能提供候选端点和成熟的 adapter/轮询模式，不能覆盖真实证据门。真实抓包与前端 bundle 构造相互印证时，仍以当前授权会话的实际网络请求为准。

### 6. 对抗性复核结论

- 如果把 env key 当 finder ID：首次身份探针仍会失败。设计明确分离两者并以持久 finder binding 做防串号。
- 如果 Cloud PUT 成功但 Edge 没收到：UI/审计只能声称“配置已保存”，不能声称“Edge 已应用”；重连快照完成最终收敛。
- 如果收到旧版本更新或另一个账号 payload：Edge 不降级、不跨 scope 应用。
- 如果真实页面改为另一 encoding/schema：对应 endpoint circuit 单独打开，不拖垮其它能力，也不自动切 DOM 写入。
- 如果只有读取抓包、没有写请求证据：读能力可以继续验收，写 capability 保持 false，不能用开源样本补成“已验证”。

## Risks / Trade-offs

- [稳定 `accountId=envKey` 与旧测试中 finder-style ID 不同] → 仅对视频号缺省路径生效，保留显式迁移覆盖；所有 WS/DB scope 继续逐字段匹配，并补充旧密文迁移/拒绝测试。
- [在线控制消息丢失或乱序] → CAS version + scope 校验；welcome 每次重连重建权威快照。
- [Cloud 全局写开关与账号控制投影造成 UI 误解] → 下发 effective write boolean，并在 internal API 保留原始 `writePaused`/账号字段；文案区分“账号配置”与“当前 Edge 可用”。
- [私有接口快速漂移] → descriptor、端点独立 schema breaker、脱敏 capture manifest、默认关闭与快速账号 kill switch。
- [真实会话取证泄露凭证/正文] → 不提交原始 HAR，取证脚本只导出键名/类型/摘要，提交前运行敏感词与 cookie/token 扫描。
- [登录流程需要用户扫码] → Edge 打开所属 AdsPower profile 并提供本地引导；超时保持 `login_required`，核心/Cloud 不假成功。

## Migration Plan

1. 先提交/部署 Cloud 协议兼容端：旧 Edge 不声明新 capability 时不下发控制消息；新字段可选。
2. 部署 Cloud `dev` 后验证 runtime-controls provider、CAS 更新、scope/version 和旧 peer 合同测试。
3. 发布 Edge 源码变更（本轮不构建安装包）：新 Edge 对旧 Cloud 缺 snapshot 时全关；对新 Cloud 应用 welcome/update。
4. 在命名 dev 视频号环境完成扫码、身份绑定和真实只读 capture；只对有证据的 endpoint 开 read probe。
5. 若用户另行提供 disposable comment/DM target，再执行一次受控写与平台可见性核验；否则写 probe 和旧变更 6.4 保持未完成。
6. 回滚 Cloud 时旧 Edge 会因缺 snapshot 安全停用 interaction；回滚 Edge 时新 Cloud 因 capability 未协商不下发新消息。

## Evidence Boundary After Capture

- 2026-07-16 的授权会话证明：公共 envelope 使用 JSON `POST`，`timestamp` 是 string；评论页是 `/micro/interaction/cgi-bin/mmfinderassistant-bin/post/post_list`，业务 body 仅有 `currentPage/pageSize/userpageType/stickyOrder`，评论位于匹配作品的内嵌 `commentList`。
- 当前账号只有一条作品且评论为 0；因此只证明“评论页空结果可同步”。非空评论字段、回复 endpoint 和回查仍未验证，不能把作品 `data.list` 当评论列表。
- 私信只证明 `get-history-msg(cookie)` 与 `get-session-info(sessionId[])` 的 HTTP 201 空结果。`data.msg` 的非空语义、非空 session/history 映射、`get-new-msg` 与发送 endpoint 均未验证。
- 是否开放真实写验收仍取决于用户是否提供明确的一次性评论和私信目标；本变更不自行选择目标，所有写开关继续关闭。
