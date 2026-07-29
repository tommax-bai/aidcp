## ADDED Requirements

### Requirement: 客户端代理写入必须逐目标绑定当前客户可见环境

客户鉴权启用时，单环境和批量代理写入的主进程入口 SHALL 只接受当前有效客户会话下、最新可信 `allowedProfileIds` 中的明确 `user_id`。批量入口 SHALL 要求非空、去重、有序的 ID 数组，并在第一笔写入前验证每个目标；任一目标越权、重复、缺失，或会话/可见集不可信时 SHALL 整批失败关闭，不调用 AdsPower `user/update`。主进程 MUST NOT 仅依赖 renderer 已过滤列表、当前选中环境或平台筛选作为写权限证据。

未启用客户鉴权的兼容模式 SHALL 保持既有本地运维能力，但仍需明确 ID 和代理输入校验。错误与日志 MUST NOT 泄露其它客户环境名称、代理摘要或凭据。

#### Scenario: 单环境越权目标被拒绝
- **WHEN** renderer 或被篡改调用向单环境代理入口提交不在当前 `allowedProfileIds` 的 `user_id`
- **THEN** 主进程在调用 AdsPower 前拒绝且不返回该环境的名称、代理或其它信息

#### Scenario: 批量任一越权目标使整批失败关闭
- **WHEN** 批量目标中有一个 ID 不属于当前客户可见环境
- **THEN** 主进程在第一笔写入前拒绝整批，不更新其它合法目标，也不回落到本机全量环境

#### Scenario: 会话或可见集不可信时不写代理
- **WHEN** 客户会话失效、刷新可见集失败或 `allowedProfileIds` 未建立
- **THEN** 单个和批量代理入口诚实要求重新登录或重试，MUST NOT 沿用不可信旧集或调用 AdsPower 写接口

#### Scenario: 重复目标在写入前拒绝
- **WHEN** 批量请求包含重复 `user_id`
- **THEN** 主进程在第一笔写入前拒绝该请求，MUST NOT 对同一环境重复改代理
