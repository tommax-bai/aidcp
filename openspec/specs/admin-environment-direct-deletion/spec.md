# admin-environment-direct-deletion Specification

## Purpose
TBD - created by archiving change cloud-direct-adspower-environment-delete. Update Purpose after archive.
## Requirements
### Requirement: 管理后台环境删除由 Cloud 直接调用 AdsPower

系统 SHALL 在管理员查看影响并逐字确认完整 envKey 后，由 Cloud 直接调用服务端配置的 AdsPower `user/delete`，MUST NOT 创建需要 Edge poll/claim/result 的远程删除责任，也 MUST NOT 通过 Cloud→Edge WebSocket 或客户端 outbox 执行该管理删除。一次请求只能删除一个 envKey，任何批量、自动清理、过期 ledger 或未确认路径 MUST NOT 触发 AdsPower 删除。

#### Scenario: 精确确认后 Cloud 直接删除
- **WHEN** 管理员对一个 active 环境提交匹配 envKey 的确认且 Cloud AdsPower 凭据与端点可用
- **THEN** Cloud 直接向 AdsPower 发出单 profile 删除，不等待或定位任何 Edge installation

#### Scenario: 不再依赖客户端在线
- **WHEN** 目标环境的 Edge 客户端离线或版本不支持 maintenance
- **THEN** 管理删除仍只由 Cloud 与其配置的 AdsPower API 决定，不进入 waiting_edge 且不向客户端下发删除责任

#### Scenario: 未精确确认不调用 AdsPower
- **WHEN** confirmEnvKey 为空、与 URL envKey 不同或请求尝试携带多个 envKey
- **THEN** Cloud 拒绝请求且不发出任何 AdsPower 写调用

### Requirement: AdsPower 成功先于 AIDCP 环境删除终态

Cloud SHALL 只在 AdsPower 返回明确成功后把环境标记为 deleted、移出有效环境/账号摘要和新调度候选。AdsPower 凭据缺失、服务不可达、鉴权失败、非 JSON、业务 code 非零或响应不确定时 MUST 保留 AIDCP 环境与审计，记录脱敏失败原因并返回非成功结果，MUST NOT 显示或返回“已删除”。

#### Scenario: AdsPower 成功后收口 AIDCP
- **WHEN** `user/delete` 对确认的 envKey 返回合法 JSON 且业务 `code=0`
- **THEN** Cloud 写入 deleted 终态和 AdsPower 成功审计，环境从默认列表、有效账号摘要和调度候选移除

#### Scenario: AdsPower 失败时 AIDCP 不删除
- **WHEN** AdsPower 不可达、鉴权失败或返回非零业务 code
- **THEN** Cloud 保留环境记录和挂载账号数据，返回真实失败并允许管理员修正配置后重试

#### Scenario: 请求接收不等于删除成功
- **WHEN** Cloud 已验证 JWT、确认文字和幂等键但 AdsPower 调用尚未完成
- **THEN** 系统只显示正在删除，不返回 202 已受理或任何已删除口径

### Requirement: 直接删除在跨系统非原子窗口中幂等且诚实

Cloud SHALL 对同一 envKey 串行化直接删除并记录 requestId/idempotencyKey，MUST NOT 因并发重复提交发出并行删除。若 AdsPower 可能已经删除但 Cloud 未写成终态，重试只有在同一服务端 AdsPower API 的完整 profile 查询明确证明 envKey 不存在时，才可记录 `already_missing` 并收口；错误字符串、查询失败、截断结果或错误端点的不存在 MUST NOT 作为成功证据。

#### Scenario: 并发提交只执行一次
- **WHEN** 两个管理员请求并发删除同一 envKey
- **THEN** Cloud 只允许一个请求进入 AdsPower 调用，另一个复用在途/写后结果或返回冲突，不并行调用两次 `user/delete`

#### Scenario: AdsPower 已删但 Cloud 首次收口失败
- **WHEN** 首次 `user/delete` 成功后 Cloud 终态写失败，重试的权威 profile 查询完整成功且明确没有 envKey
- **THEN** Cloud 以 `already_missing` 记录证据并完成 AIDCP deleted 终态

#### Scenario: 不确定的不存在不得收口
- **WHEN** profile 查询不可达、响应非法、分页不完整或仅从错误文案猜测目标不存在
- **THEN** Cloud 保持失败/未知状态并不把 AIDCP 环境标记为 deleted

### Requirement: 删除环境保留账号域真态和最小审计

环境删除 SHALL 仅移除环境的有效注册、归属投影和调度资格，MUST NOT 删除账号、清空账号风控/分组/人设/内容/历史或改变账号运营暂停态。系统 MUST 保留删除操作者、envKey、请求/结果时间、AdsPower 结果种类和脱敏失败原因；默认环境列表 MAY 隐藏 deleted 行，但历史筛选 SHALL 可查询。

#### Scenario: 删除最后一个环境后账号仍存在
- **WHEN** 某账号最后一个有效环境完成 AdsPower 与 AIDCP 删除
- **THEN** 账号仍保留原风险、分组、人设和运营状态，只显示无可执行环境

#### Scenario: 查看删除审计
- **WHEN** 管理员在环境页查看 deleted 历史
- **THEN** 可看到 envKey、操作者、结果种类和时间，但看不到 AdsPower API Key、Authorization 或原始敏感响应

### Requirement: Cloud AdsPower 出口是服务端受限接口

Cloud AdsPower 客户端 SHALL 只允许单 profile 删除与用于幂等证明的 profile 查询，写 body MUST 固定为 `{ user_ids: [envKey] }`；API base 只能来自服务端配置，浏览器 MUST NOT 提交或覆盖。请求 SHALL 有超时和每秒节流，Authorization、API Key 和完整请求/响应体 MUST NOT 进入日志、错误或 Panel 返回。

#### Scenario: 浏览器不能覆盖 AdsPower 地址
- **WHEN** 管理删除请求携带 apiBase、Authorization 或 API Key 字段
- **THEN** Cloud 忽略/拒绝这些字段并只使用服务端配置与加密凭据

#### Scenario: 非允许 AdsPower 写端点不可达
- **WHEN** Cloud 代码尝试通过该客户端调用 user/create、user/update、group/create 或 browser lifecycle
- **THEN** 客户端结构性拒绝且不发出请求

#### Scenario: 日志与错误脱敏
- **WHEN** AdsPower 请求失败或返回异常响应
- **THEN** 审计与 Panel 只包含稳定错误类别和安全摘要，不包含 API Key、Authorization 或原始敏感响应体

