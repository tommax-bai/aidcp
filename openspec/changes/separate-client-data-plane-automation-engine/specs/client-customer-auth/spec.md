## MODIFIED Requirements

### Requirement: 客户态 Cloud 操作 MUST 逐请求解析环境归属与账号绑定

由客户鉴权直接执行的人设、内容、待审编辑、审批受理、配置及其他 AIDCP 自有数据操作 SHALL 只接收客户令牌上下文、`envKey` 与最小业务入参，并 SHALL 通过逐请求 customer-auth HTTP 执行。Cloud MUST 每次验证客户状态和环境归属并从权威绑定解析 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。该类操作 MUST NOT 以普通自动化引擎进程、automation WebSocket、浏览器登录、CDP 或槽位为准入条件；renderer MUST NOT 获得客户令牌、权威 `accountId` 或通用 HTTP 能力。

#### Scenario: 引擎和浏览器均缺席时生成客户人设

- **WHEN** 客户已登录、拥有环境且其账号绑定可信，但自动化引擎停止、浏览器关闭且无 CDP
- **THEN** Cloud 由 customer-auth HTTP 请求解析账号归属并执行人设生成，MUST NOT 返回“请启动自动化/浏览器”或等待浏览器槽位

#### Scenario: 自动化 WebSocket 离线时审批待审稿

- **WHEN** automation WebSocket 不可用但 customer-auth HTTP 可达，客户批准一份待审稿
- **THEN** Cloud 记录并返回“决定已受理/平台执行待完成”，MUST NOT 因引擎离线拒绝受理，也不得显示已发布

#### Scenario: 客户请求越权环境

- **WHEN** 客户请求中的 `envKey` 不属于当前客户，或该环境绑定无法权威解析
- **THEN** Cloud 以可区分拒因 fail-closed，MUST NOT 使用请求体账号、历史 UI 缓存或浏览器启动来绕过校验

## REMOVED Requirements

### Requirement: 客户登录后 SHALL 自动建立可信环境的浏览器无关核心

**Reason**: 登录后自动启动每环境普通 Edge 子进程把客户端数据管理错误绑定到自动化引擎生命周期，并制造“客户端核心在线”产品概念。

**Migration**: 登录只恢复客户会话、roster 和 HTTP 数据面；普通引擎仅在客户启动/恢复自动化后创建。受限 offboard 清理 worker 按其最小权限合同独立恢复。
