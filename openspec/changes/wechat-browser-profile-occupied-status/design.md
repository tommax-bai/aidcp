## Context

视频号授权协调器已经先读取本地加密会话，并在浏览器关闭时调用身份接口与已启用只读探针；全部通过即可进入 `api_only_running`。现场失败发生在失效会话转入浏览器补授权后：AdsPower V2 `browser-profile/start` 返回稳定的 “profile is being used by … and is not allowed to open”，provider 抛出普通 `Error`，sidecar 进入 `unavailable`，但授权状态仍停在 `browser_opening`，最终 Cloud/客户端看到 `authenticating + INTERACTION_INTERNAL_ERROR`。

授权状态经 `interaction.auth.status` 从 Edge 发送到 Cloud，Cloud 将 `reasonCode` 作为文本持久化并通过客户 API 原样投影，因此新增枚举不需要数据库迁移，但 Edge、Cloud、JSON Schema、fixture 和文档必须同步。客户工作区已有 `reauth_required` 的重新鉴权入口，可以复用为解除占用后的显式重试。

## Goals / Non-Goals

**Goals:**

- 保持并测试 API-only 启动快路径，浏览器只用于缺失/失效会话的补授权。
- 将 AdsPower profile 占用与网络、未知 provider 故障区分，且不泄露原始占用邮箱。
- profile 被占用后退出 `authenticating`，上报可理解、可重试、写能力关闭的真态。
- Cloud 和客户工作区原样保留该真态，解除占用后可通过既有重新鉴权动作恢复。

**Non-Goals:**

- 不自动强制关闭、抢占或删除其他设备上的 AdsPower profile。
- 不把占用方邮箱发送到 Cloud、数据库或客户 API。
- 不把“本地存在加密记录”本身当作鉴权成功；身份与已启用只读探针仍是硬门禁。
- 不新增数据库迁移、不改变视频号 Cookie/请求上下文采集方式、不制作 Edge 安装包。

## Decisions

### 1. Provider 在收到响应体时做窄分类

`browser-provider.ts` 在 `browser-profile/start` 的 `code != 0` 分支只匹配 AdsPower 已验证的占用句式，并抛出导出的 `BrowserProfileInUseError`。该错误携带稳定的本地错误码和可选、已脱敏的 `ownerHint`；异常 message 与日志不得包含原始邮箱。其他 path、其他 code 或措辞不匹配的错误继续走既有诚实失败，不扩大误分类面。

选择在 provider 层分类，是因为这里同时拥有 path、code 与原始 `msg`；若在运行时从通用 Error 文本反推，会继续依赖已拼接日志且容易误命中。未选择新增通用浏览器协议 payload，因为占用方详情只服务于本机诊断，不应越过 Edge 边界。

### 2. 授权协调器吸收已知占用并落到 `reauth_required`

`runBrowserAuthentication()` 捕获 `BrowserProfileInUseError` 后，将本地授权态转为 `reauth_required`、原因码设为 `INTERACTION_BROWSER_PROFILE_IN_USE`，保留 sidecar 的 `unavailable` 真态，记录只含 profile 与脱敏 owner hint 的安全日志，然后结束本次补授权。它不得继续轮询 Cookie、不得保存会话，也不得把该分支冒充成功。

该已知运营阻塞不继续抛给顶层 generic catch，避免再次被压成 `INTERACTION_INTERNAL_ERROR`；状态变更会经 connector 既有订阅立即上报。其他浏览器启动错误保持既有 fail-closed 通用错误路径，避免本变更顺带重画全部 provider 故障状态。

### 3. 新原因码跨 Edge/Cloud 契约同步，数据库保持不变

在 Edge 与 Cloud 的 `InteractionErrorCode`、`InteractionAuthReasonCode`/授权集合和 JSON 校验中加入 `INTERACTION_BROWSER_PROFILE_IN_USE`。Cloud 继续把 reason code 写入现有文本列并从客户 API 原样返回；不新增字段或表结构。

部署顺序为 Cloud 先、Edge 后：新 Cloud 可同时接受旧 Edge 与新 Edge；若 Edge 先上线，旧 Cloud 会按现有严格校验拒绝未知枚举，因此不得倒序发布。

### 4. 客户工作区用原因码覆盖通用 `reauth_required` 文案

当 `reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE` 时，状态徽标显示“视频号：浏览器被占用”，主提示说明已保存登录信息未通过、历史仍可查看、写操作已暂停，并把既有重新鉴权按钮改为“重试打开浏览器”。UI 不展示占用邮箱，也不把 HTTP/WS accepted 当作已经解除占用；只有后续 auth status 回到 `active` 才显示鉴权通过。

不增加高频自动重试。AdsPower 的只读 active 接口只能说明本机是否 active，不能证明远端安全锁已释放；显式重试既避免打扰占用者，也符合现有 Idempotency-Key/命令入口。

## Risks / Trade-offs

- [AdsPower 调整英文错误文案导致无法命中] → 使用窄正则并保留通用诚实失败；测试冻结当前已验证句式，现场出现新句式时再增量兼容。
- [邮箱脱敏实现遗漏边界输入] → provider 只输出独立 `maskOwnerHint()` 结果，覆盖普通邮箱、非邮箱标识、空值和超长输入；协议层完全不含 owner 字段。
- [Cloud/Edge 枚举发布顺序漂移] → Cloud 先部署并验证契约，再合入/发布 Edge；回滚 Edge 不影响 Cloud 对旧枚举的兼容。
- [客户误以为点击重试即恢复] → UI 明确“已请求，仍需等待平台登录状态确认”，只有读回 `active` 才显示成功。

## Migration Plan

1. 先合入并部署 Cloud 的枚举接受、持久化投影与契约测试；验证服务、监听和健康路由。
2. 合入 Edge provider/授权/UI 与协议镜像；不打包安装器。
3. 更新 control 协议文档、冻结 schema/fixture 与 OpenSpec 任务证据。
4. 回滚时先回滚 Edge 行为，再回滚 Cloud 枚举接受；数据库无需回退。

## Open Questions

无。
