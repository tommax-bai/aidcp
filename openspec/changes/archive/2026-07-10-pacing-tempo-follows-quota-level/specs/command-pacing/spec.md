## ADDED Requirements

### Requirement: 节奏 tempo 由风控状态与配额档共同取更慢者

云端计算节奏 tempo 时 SHALL 同时参考两个档位并取**更慢的一个**：`effectiveTempo(status, quotaLevel) = max(tempoForStatus(status), tempoForQuotaLevel(quotaLevel))`。其中配额档映射 `conservative` 放慢（与「被警告」同量级）、`normal` 与 `aggressive` 均不改变 tempo（`aggressive` 只放行更多配额、MUST NOT 提速到人类节奏基线以下——提速会削弱抗检测头寸）。

`effectiveTempo` MUST 作为所有 tempo 消费处的统一口径：决策中心值（`dwellMs`/`thinkMs`/feed 停留）、`welcome` 兜底快照、以及会话中途 `pacing.update` 推送与其去抖基线。两个因子 MUST 均为 ≥ 1.0 的放慢因子，故 `effectiveTempo` **只会更慢、绝不更快**（保守放慢、激进不提速）。默认账号 `quotaLevel=normal` 时 `effectiveTempo` 退化为 `tempoForStatus`（未配保守的账号行为零回归）。

#### Scenario: 保守账号即便风控正常也整体放慢

- **WHEN** 某账号风控状态为 `normal`（tempo 1.0）但配额档被后台配为 `conservative`
- **THEN** 其生效 tempo 为 1.3（保守放慢透出），决策中心值与兜底停留 / 最小间隔据此放大——保守 = 又少又慢

#### Scenario: 激进账号只多做、不提速

- **WHEN** 某账号配额档为 `aggressive`、风控 `normal`
- **THEN** 其生效 tempo 为 1.0（与 `normal` 账号相同）——激进只放行更多配额，动作停顿不压到人类基线以下

#### Scenario: 风控更差时盖过配额档

- **WHEN** 某 `conservative` 账号风控迁移到 `restricted`（status-tempo 1.6 > quota-tempo 1.3）
- **THEN** 生效 tempo 取更慢的 1.6（status 主导），配额档不再额外叠加

## MODIFIED Requirements

### Requirement: 风控档位中途变化实时传播到边缘兜底

当账号在**一次稳定连接的会话中途**，因风控状态迁移（如 `normal → warned → restricted`）**或后台配额档调整**（`setQuotaLevel`，如 `normal → conservative`）导致**生效 tempo**（`effectiveTempo` = 风控状态 tempo 与配额档 tempo 取更慢者）变化时，云端 SHALL 主动把新的 `tempo` 推送给边缘（不依赖断连重连）；边缘 SHALL 据此更新其兜底节奏所用的 `tempo`，使最小间隔 gating 与内置停留兜底随之放慢。

该推送 MUST NOT 重置边缘的最小间隔锚点（`lastActionEndAt`）——中途档位刷新不等于重连，MUST NOT 借此跳过一次操作间隔。云端 SHALL 仅在 `tempo` 相对**上次已推送值**变化时推送（去抖，避免每命令冗余下发）；握手时边缘已由 `welcome` 快照取得初始 `tempo`，云端 MUST NOT 在无变化时重复推送。该推送为控制消息，MUST 经统一命令出口的原始下发通道直发，MUST NOT 消耗互动配额、MUST NOT 被软暂停闸抑制。该推送为向后兼容的可选消息：旧边缘忽略即可，行为不劣化。

#### Scenario: 中途升档实时放慢边缘兜底

- **WHEN** 会话稳定连接期间账号风控由 `normal` 迁移至 `warned`（`tempo` 1.0→1.3），且期间无断连重连
- **THEN** 云端把新 `tempo` 推送给边缘，边缘后续最小间隔 gating 与内置停留兜底按新 `tempo` 放大，无需等待一次重连

#### Scenario: 后台改配额档实时调速

- **WHEN** 运营在会话中途经后台把某账号配额档由 `normal` 改为 `conservative`（生效 tempo 1.0→1.3）
- **THEN** 云端在该账号下一次统一出口下发前推送 `pacing.update`，边缘当场按新 tempo 放慢——无需断连重连（此路径使 `pacing.update` 通道从 latent 转为日常可触发）

#### Scenario: 档位刷新不重置操作间隔锚点

- **WHEN** 边缘在两次操作之间收到中途 `tempo` 推送
- **THEN** 边缘更新 `tempo` 但保留 `lastActionEndAt` 锚点，不因此跳过或重置当前的最小间隔计时

#### Scenario: 无变化不冗余推送

- **WHEN** 账号生效 tempo 在会话中途保持不变（风控状态与配额档都未致 tempo 变化）
- **THEN** 云端不重复推送 `tempo`（仅在生效 tempo 实际变化时推送一次）

#### Scenario: 旧边缘忽略档位推送

- **WHEN** 边缘版本早于 change `pacing-fallback-hardening`、收到中途 `tempo` 推送消息
- **THEN** 边缘忽略该消息、继续用握手时的 `tempo`，行为不劣化（向后兼容）
