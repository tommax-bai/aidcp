## MODIFIED Requirements

### Requirement: Startup login gate blocks Cloud connect until target-scoped authentication

Edge 客户端启动时 MUST 先恢复部署目标并校验同目标客户会话。仍有效且 `deploymentTarget` 匹配的客户令牌 SHALL 按既有续签与客户范围校验继续启动；令牌缺少目标、本地过期、目标不匹配或被服务端明确拒绝时，客户端 MUST 保持所有环境停止。只有目标匹配的现有令牌或一次同目标自动登录建立有效会话后，客户端才 SHALL 建立主界面和自动化连接。无可用同目标加密凭据或自动登录失败时，客户端 MUST 显示登录门且不得循环自动重试。

#### Scenario: Matching target session restores

- **WHEN** 客户端选择 DEV 且持有通过 DEV 续签与范围校验的 DEV 令牌
- **THEN** 客户端继续正常启动，不额外提交保存的凭据

#### Scenario: Legacy or mismatched session fails closed

- **WHEN** 保存令牌缺少部署目标或其目标与当前选择不一致
- **THEN** 客户端清除该短期会话并显示登录门，不建立主界面或启动环境

#### Scenario: Matching saved credentials restore once

- **WHEN** 当前目标没有有效令牌但存在同目标可解密的最近成功凭据
- **THEN** 客户端在主进程内向该目标 `/login` 自动提交至多一次
- **AND** 成功后保存带目标的新令牌并刷新该目标环境范围

#### Scenario: Automatic login failure does not loop

- **WHEN** 同目标自动登录因凭据拒绝、限流或网络错误失败
- **THEN** 客户端显示带当前目标的登录门，且本次启动不得再次自动提交

### Requirement: Login view selects target and credentials without exposing URLs

登录门 SHALL 延续现有蓝灰简约视觉，提供 DEV/OL 目标选择、name、key、目标化登录按钮、明确错误态与无障碍降级。DEV SHALL 明示测试环境，OL SHALL 明示正式环境。登录 renderer 只能提交目标枚举与凭据，MUST NOT 接收或提交 Cloud URL、token、环境归属或任意请求配置。除主界面的目标状态/切换入口外，其余现有功能区 MUST NOT 被重绘。

#### Scenario: Login clearly names the target

- **WHEN** 客户在登录门选择 DEV 或 OL
- **THEN** 选择器与提交按钮清楚显示“测试环境 DEV”或“正式环境 OL”

#### Scenario: Login renderer cannot provide endpoints

- **WHEN** 登录 renderer 发起登录
- **THEN** IPC 仅接受 `deploymentTarget`, `name`, `key` 的冻结形状，主进程自行解析端点

#### Scenario: Target persistence failure is visible

- **WHEN** 客户选择的目标无法写入当前 `userData`
- **THEN** 登录门显示环境设置未保存且不提交凭据

### Requirement: Token persistence and session lifecycle are target-scoped

客户令牌 MUST 在当前 `userData` 内与 `deploymentTarget` 一起持久化。客户端 SHALL 仅向令牌所属目标续签和发送受保护请求。显式退出、目标切换、目标不匹配或令牌失效时，客户端 MUST 停止所有环境、清除该会话与目标权威投影并回到登录门；目标切换 MUST NOT 保留旧目标令牌供新目标尝试。

#### Scenario: Refresh uses token target

- **WHEN** OL 令牌进入续签窗口
- **THEN** 客户端只向 OL customer-auth 请求续签，且当前目标不是 OL 时不发送该令牌

#### Scenario: Target switch clears authority

- **WHEN** 已登录客户请求切换部署目标
- **THEN** 客户端停止环境并清除 token、可见环境、平台/绑定投影和客户范围排除状态后返回登录门

#### Scenario: Token rejection retains only same-target credential memory

- **WHEN** 受保护请求明确拒绝当前目标令牌
- **THEN** 客户端清除 session、停止环境并返回同目标登录门，且只可回填同目标加密凭据

### Requirement: Login credential prefill is encrypted and target-scoped

登录成功后，客户端 SHALL 在当前实例保存包含 `deploymentTarget`, name 与 key 的加密凭据记录。只可在记录目标等于登录门当前目标时回填或自动登录；目标切换 SHALL 清除旧目标回填，MUST NOT 将凭据静默复制到新目标。访问密钥 MUST NOT 明文落盘、日志、renderer、协议或 Cloud。

#### Scenario: Same-target prefill

- **WHEN** 客户在 DEV 成功登录后回到仍选择 DEV 的登录门
- **THEN** 客户端可回填 DEV 加密凭据或按启动契约自动登录一次

#### Scenario: Cross-target prefill is forbidden

- **WHEN** 保存凭据属于 OL 而登录门当前选择 DEV
- **THEN** 客户端不回填、不自动提交并清除旧目标凭据记忆

#### Scenario: Legacy prefill has no target

- **WHEN** 升级后读取到不含目标的旧加密凭据
- **THEN** 客户端不提交该凭据并要求客户重新登录一次

### Requirement: Edge client login gate activation follows the official target catalog

桌面客户端 SHALL 始终为官方 DEV/OL 目标启用客户登录门，并仅从主进程目标目录解析 customer-auth base URL。旧 `AIDCP_CLIENT_AUTH_URL`、持久化 `clientAuthUrl` 或 `aidcpClientAuthUrl` 构建元数据 MUST NOT 成为官方会话的活动路由。目标目录缺失任一端点时启动 MUST fail closed，不得关闭登录门或从另一个目标借用地址。

#### Scenario: DEV login gate uses DEV catalog

- **WHEN** 当前目标为 DEV
- **THEN** 登录门启用且登录、续签和客户数据请求使用 DEV customer-auth base

#### Scenario: OL login gate uses OL catalog

- **WHEN** 当前目标为 OL
- **THEN** 登录门启用且登录、续签和客户数据请求使用 OL customer-auth base

#### Scenario: Catalog entry is incomplete

- **WHEN** 当前官方目标无法同时解析 customer-auth 与 automation 端点
- **THEN** 客户端显示配置错误并保持所有环境停止，MUST NOT 回退到旧绝对 URL
