## ADDED Requirements

### Requirement: 鉴权浏览器启动失败必须退出进行中状态并保留恢复入口

视频号鉴权流程在本地浏览器 sidecar 打开失败时 SHALL 立即退出 `authenticating`，MUST NOT 无限停留在 `browser_opening`。若已有失效的绑定会话，授权态 SHALL 回到 `reauth_required`；若尚未建立会话，授权态 SHALL 回到 `login_required`。两条路径均 SHALL 使用既有 `WECHAT_AUTH_REQUIRED` 原因码、保持所有写能力关闭，并保留客户重新鉴权入口。

浏览器状态 SHALL 独立报告为 `unavailable`，MUST NOT 因 Cloud 控制面仍在线而冒充浏览器已打开或鉴权通过。

#### Scenario: 旧会话过期且浏览器打不开时提示重新鉴权

- **WHEN** Edge 发现已保存的视频号会话过期，尝试打开绑定 AdsPower profile 时失败
- **THEN** 授权态 SHALL 为 `reauth_required`、原因码 SHALL 为 `WECHAT_AUTH_REQUIRED`、浏览器状态 SHALL 为 `unavailable`
- **AND** workspace SHALL 提供现有重新鉴权入口，MUST NOT 继续显示“鉴权中”

#### Scenario: 首次登录浏览器打不开时仍可重新检查登录

- **WHEN** 环境尚无已保存会话且鉴权浏览器启动失败
- **THEN** 授权态 SHALL 为 `login_required`、原因码 SHALL 为 `WECHAT_AUTH_REQUIRED`、浏览器状态 SHALL 为 `unavailable`
- **AND** 客户后续 SHALL 能通过既有登录检查入口重试

### Requirement: 本地鉴权浏览器失败诊断不得泄露凭据

Edge SHALL 为鉴权浏览器打开失败记录结构化、脱敏的本地诊断，并把运行时错误码归入既有授权错误 `WECHAT_AUTH_REQUIRED`，MUST NOT 把该已知失败压成 `INTERACTION_INTERNAL_ERROR`。诊断 MAY 包含白名单化的 provider、operation、失败类别、HTTP 状态或 AdsPower 错误码；MUST NOT 包含 API key、Authorization header、cookie、会话材料、原始响应正文或带 query 的 URL。

#### Scenario: AdsPower 拒绝启动时记录可操作且脱敏的诊断

- **WHEN** AdsPower `browser-profile/start` 返回非成功状态
- **THEN** Edge 日志 SHALL 标明 provider、operation 与安全错误类别，并在可安全解析时包含 HTTP 状态或 AdsPower code
- **AND** 运行时 SHALL 回报 `WECHAT_AUTH_REQUIRED`，MUST NOT 回报 `INTERACTION_INTERNAL_ERROR`
- **AND** 日志 MUST NOT 包含任何本地 API 凭据或视频号会话材料
