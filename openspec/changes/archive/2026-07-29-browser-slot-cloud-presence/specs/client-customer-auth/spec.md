## ADDED Requirements

### Requirement: 客户端控制面启动引导必须经环境归属与绑定解析

customer-auth SHALL 提供 env-scoped 的最小只读控制面引导。接口 MUST 先验证 enabled customer 与环境归属，再复用权威环境→账号绑定解析器；成功时只返回请求 envKey 与已解析 accountId。该接口 MUST NOT 创建、修改、推断或修复环境归属/账号绑定。

#### Scenario: 已归属已绑定环境取得引导
- **WHEN** 已登录客户请求其拥有且唯一绑定账号 A 的环境 E 的控制面引导
- **THEN** Cloud 返回 `{envKey: E, accountId: A}`
- **AND** 该结果可用于无浏览器核心的首次 hello

#### Scenario: 越权环境 fail-closed
- **WHEN** 客户请求不归其所有的环境
- **THEN** 接口以 `environment_not_owned` 拒绝
- **AND** MUST NOT 暴露该环境是否绑定、绑定到谁或是否在线

#### Scenario: 不可解析原因保持可区分
- **WHEN** 环境尚未绑定、存在跨客户绑定冲突或绑定存储不可用
- **THEN** 接口分别以 `binding_unknown`、`binding_conflict` 或 `binding_unavailable` 拒绝
- **AND** MUST NOT 返回空 accountId、成功空对象或猜测值

### Requirement: 控制面引导 MUST 限于 Electron 主进程客户会话

控制面引导请求 SHALL 使用既有 customer bearer session 并遵守其失效、禁用与轮换边界。renderer MUST NOT 获得 customer token，Cloud MUST NOT 提供未鉴权的 envKey→accountId 查询入口。

#### Scenario: 登录失效后不可继续引导
- **WHEN** 客户已退出、被禁用或 token 已失效
- **THEN** 控制面引导请求被鉴权层拒绝
- **AND** 客户端 MUST NOT 以本地缓存绕过该拒绝建立新的 Cloud 会话
