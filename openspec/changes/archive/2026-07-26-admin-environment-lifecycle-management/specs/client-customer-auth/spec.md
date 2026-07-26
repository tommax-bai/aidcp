## ADDED Requirements

### Requirement: Edge 通过客户鉴权 HTTP 拉取环境维护责任

系统 SHALL 提供客户鉴权 HTTP maintenance poll，使官方 Edge 主进程携带持久化随机 installationId 与本机非敏感 roster 摘要，主动拉取定位给该 installation 的环境删除责任。该能力 MUST NOT 新增 Cloud→Edge WebSocket 删除消息，MUST NOT 把删除加入自动化引擎命令，且维护责任 MUST 与 `/my-environments` 的正常可运行范围分离，使被冻结或已撤权但仍待物理清理的环境不会丢失责任。

#### Scenario: Edge 主动拉取删除责任
- **WHEN** 管理后台已为当前客户环境创建删除申请，且该 Edge installation 是唯一新鲜承载者
- **THEN** Edge 的 HTTP poll 返回匹配 requestId/envKey/version 的维护责任，Cloud 不发送任何新增 WS 删除消息

#### Scenario: 正常可见范围移除后责任仍可拉取
- **WHEN** 环境因删除申请已不再可运行但该客户会话仍承担物理清理
- **THEN** `/my-environments` 不把环境当正常可运行项，而 maintenance poll 仍按 durable request 返回清理责任

### Requirement: 删除责任按 installation 定位并经 HTTP 幂等收敛

Cloud SHALL 记录最近 installation observation，并仅在一个新鲜 installation 声明承载 envKey 时允许其通过 HTTP claim 删除责任。多个新鲜 installation、无定位或 installation 不匹配 MUST fail closed。Edge SHALL 先持久化 AdsPower 删除结果，再以 requestId/version/installationId 和 Idempotency-Key 经 HTTP 回写；Cloud 只接受匹配 claim 的结果，重复相同结果 MUST 幂等返回同一写后真态。

#### Scenario: 多 installation 承载冲突时不领取
- **WHEN** 两个新鲜 installation 都声明管理同一 envKey
- **THEN** Cloud 返回承载冲突并保持等待状态，任何一端都不得执行 AdsPower 删除

#### Scenario: 回执响应丢失后重试
- **WHEN** Edge 已删除 AdsPower profile 并提交 result，但 HTTP 响应在到达本机前丢失
- **THEN** Edge 保留本地 outbox 并用相同幂等键重试，Cloud 返回同一终态且不产生第二次生命周期迁移

#### Scenario: 非承载机器的不存在不算删除证明
- **WHEN** 未匹配 claim 的 installation 回报本机不存在该 envKey
- **THEN** Cloud 拒绝把它作为 `already_missing` 终态证据并保留原删除申请

