## ADDED Requirements

### Requirement: 客户登录后 SHALL 自动建立可信环境的浏览器无关核心

客户登录完成并取得权威环境 roster 后，客户端 SHALL 对每个归属可用且已解析可信绑定的环境自动启动或恢复浏览器无关核心，无需用户点击“启动环境”。该 bootstrap MUST 使用有界并发和独立退避，MUST NOT 调用浏览器 provider、申请浏览器槽位或要求 CDP。环境未绑定、归属冲突或绑定不可用时 SHALL fail-closed 显示具名原因，不得猜测账号或通过打开浏览器自动消除归属闸。

#### Scenario: 首次登录自动恢复全部可信环境

- **WHEN** 客户登录后 roster 返回三个已归属且可信绑定的环境
- **THEN** 客户端有界并发建立三个浏览器无关核心与其 Cloud 会话，三个环境的浏览器均保持关闭且不消费槽位

#### Scenario: 一个环境绑定冲突不牵连其他环境

- **WHEN** roster 中一个环境存在绑定冲突、另两个环境绑定可信
- **THEN** 冲突环境停在具名 fail-closed 状态，另两个环境正常建立核心，客户端不得为冲突环境自动打开浏览器

### Requirement: 客户态 Cloud 操作 MUST 逐请求解析环境归属与账号绑定

由客户鉴权直接执行的人设、内容、待审编辑、审批受理和配置操作 SHALL 只接收客户令牌上下文、`envKey` 与最小业务入参；Cloud MUST 逐请求验证客户拥有该环境并从权威绑定解析 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。该类操作 MUST NOT 以 Edge 活会话、浏览器登录、CDP 或槽位为准入条件；renderer MUST NOT 获得客户令牌、权威 `accountId` 或通用 HTTP 能力。

#### Scenario: 浏览器和 Edge 页面会话均缺席时生成客户人设

- **WHEN** 客户已登录、拥有环境且其账号绑定可信，但该环境浏览器关闭且无 CDP
- **THEN** Cloud 由 customer-auth 请求解析账号归属并执行人设生成，MUST NOT 返回“请启动浏览器”或等待浏览器槽位

#### Scenario: 客户请求越权环境

- **WHEN** 客户请求中的 `envKey` 不属于当前客户，或该环境绑定无法权威解析
- **THEN** Cloud 以可区分拒因 fail-closed，MUST NOT 使用请求体账号、历史 UI 缓存或浏览器启动来绕过校验
