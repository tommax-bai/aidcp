## ADDED Requirements

### Requirement: 授权请求上下文漂移 MUST 精确恢复

Edge SHALL 区分浏览器页面登录态与加密 API 会话真态。平台明确返回已知的授权请求上下文失效业务码时，Edge MUST 把现有 API 快照视为失效，进入既有浏览器重新授权路径，重新采集 Cookie 与请求上下文，并在身份和已启用只读探针均通过后才保存新快照、恢复 `active`。浏览器页面可见或 profile 仍在运行 MUST NOT 单独作为鉴权成功证据。

只有经过证据确认的授权请求上下文失效码 MAY 触发该路径；其他未知平台拒绝 MUST 保持原分类，MUST NOT 因共享通用错误文案而自动打开浏览器。

#### Scenario: 业务码 300334 触发会话重新采集

- **GIVEN** Edge 正以已保存的加密会话运行，浏览器页面仍可显示登录状态
- **WHEN** 身份或已启用读取接口返回 HTTP 200、平台业务码 `300334`
- **THEN** Edge 将当前 API 会话判为失效并上报 `WECHAT_AUTH_REQUIRED`
- **AND** Edge 通过既有 sidecar 打开或接管原 profile、刷新页面并重新采集授权材料
- **AND** 只有身份和已启用只读探针通过后才重新进入 `active`

#### Scenario: 未知平台拒绝不冒充授权失效

- **WHEN** 平台返回并非 `300334` 的未知非零业务码，且没有登录失效、验证挑战或权限拒绝证据
- **THEN** Edge 保持该结果为一般平台拒绝
- **AND** MUST NOT 仅因通用 `request failed` 文案自动打开浏览器

### Requirement: 客户工作区鉴权真态 MUST 持续收敛

视频号工作区在可见且环境在线时 SHALL 持续低频读取 Cloud 真态。当前鉴权状态不是 `active`、读取开关关闭或读取能力尚未生效 MUST NOT 永久停止该刷新通道。重新授权请求被接受后，界面 MUST 等待 Edge 实际状态回报，MUST NOT 合成鉴权成功。

明确收到 `browserState=closed` 时，界面 MUST 将其视为已回报：`active` 时显示后台模式，其他状态显示浏览器已关闭；只有缺失 browserState 回报时才显示未回报。

#### Scenario: 首次旧状态随后收敛为 active

- **GIVEN** 工作区首次读取到 `login_required + browserState=closed`
- **AND** Cloud 随后持久化 `active + browserState=closed`
- **WHEN** 工作区保持可见且环境在线
- **THEN** 后续低频刷新取得新快照并显示鉴权通过与后台模式
- **AND** MUST NOT 永久停留在等待登录或未回报

#### Scenario: 读取关闭不切断鉴权刷新

- **WHEN** 评论和私信读取开关均关闭，但工作区可见且环境在线
- **THEN** 工作区仍安排后续真态刷新
- **AND** 读取与写入操作继续由现有能力门禁关闭

### Requirement: 平台拒绝诊断 MUST 安全且可定位

Edge 对平台 API 失败的运行日志 SHALL 至少包含稳定 endpoint 与协议错误码；当响应提供 HTTP 状态或平台业务码时 SHALL 记录对应标量。日志 MUST NOT 包含 Cookie、请求头、请求正文、响应正文、平台 message、身份原文或其它授权材料。

#### Scenario: 定时同步输出安全诊断字段

- **WHEN** 定时同步收到 HTTP 200、平台业务码 `300334`
- **THEN** 日志包含同步渠道、稳定 endpoint、HTTP 状态 `200`、平台码 `300334` 和协议错误码
- **AND** 日志不包含 Cookie、请求或响应正文
