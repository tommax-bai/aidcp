## ADDED Requirements

### Requirement: 内部 Panel 环境删除返回 Cloud 直调后的写后真态

内部 Panel SHALL 通过 JWT 守护的逐环境端点接收完整 envKey 确认和幂等键，并在 Cloud 直接完成 AdsPower 调用与 AIDCP 收口后返回写后真态。成功 SHALL 返回 `state=deleted`；AdsPower 或配置失败 SHALL 返回非成功 HTTP、稳定错误类别和脱敏写后失败状态。端点 MUST NOT 以 202、`waiting_edge`、请求已受理或等待客户端表示未完成调用。

#### Scenario: 直接删除成功返回终态
- **WHEN** 内部管理员提交合法删除且 AdsPower 与 AIDCP 收口均成功
- **THEN** Panel 返回 200 和 `state=deleted`，Console 刷新后默认列表不再显示该有效环境

#### Scenario: AdsPower 不可用返回真实失败
- **WHEN** AdsPower Key 未配置、API 不可达或业务拒绝删除
- **THEN** Panel 返回可辨认非成功状态且环境仍存在，不返回 waiting_edge 或 deleted

#### Scenario: 客户令牌无法调用内部删除
- **WHEN** 客户令牌请求内部环境删除端点
- **THEN** 请求被拒且不会调用 AdsPower

### Requirement: Panel 平台凭据接口展示并保存 AdsPower API Key 状态

现有 `GET /api/config/model` 与 `PUT /api/config/credential` SHALL 将 AdsPower API Key 作为平台凭据目录项处理，GET 只返回标签、来源、配置状态、掩码与 `restartRequired=false`，MUST NOT 返回明文；PUT SHALL 复用服务端加密存储、JWT、允许列表和非乐观写后结果。保存后的 Key SHALL 被下一次 Cloud 删除按需读取，无需重启。

#### Scenario: 设置读取只返回掩码
- **WHEN** AdsPower API Key 已加密保存在 Cloud
- **THEN** Panel 配置读返回已配置、服务端密文来源和掩码，不返回明文或 Authorization

#### Scenario: 保存后下一次删除生效
- **WHEN** 管理员通过凭据端点覆盖保存 AdsPower API Key
- **THEN** 返回加密保存后的掩码状态，下一次环境删除读取新 Key 且不要求重启 Cloud

#### Scenario: 主加密密钥缺失时拒绝保存
- **WHEN** Cloud 未配置有效 `AIDCP_CRED_KEY`
- **THEN** AdsPower Key 写入与其它平台凭据一致被拒，绝不明文落库或假称保存成功
