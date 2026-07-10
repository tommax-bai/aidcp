## MODIFIED Requirements

### Requirement: 缺时间指令时的安全降级

边缘在未收到时间字段（旧云端 / 断连 / 自主动作）时 SHALL 回退到内置默认下限，MUST NOT 退化为零延迟。兜底默认经 `welcome` 握手响应的可选 `pacing` 快照下发（`tempo?` 标量 + 每类操作 floor 区间 `opFloorsMs?`）供边缘最小间隔 gating、详情页停留兜底与断连兜底使用；该快照 MUST NOT 包含 read / pause / fatigue 系数（这些收口在云端，随决策指令以 `dwellMs` / `thinkMs` 下发）。快照缺失或某字段缺失时边缘 SHALL 逐字段回落内置非零默认，MUST NOT 回落零。

边缘在缺 `dwellMs` 而回落内置详情页停留兜底（从 `dwellFloorTiming` 采样）时 SHALL 对采样中心值叠加**当前生效的 `tempo` 档位**放大（与云端计算 `dwellMs` 同向：风控越差、兜底停留越长），但 MUST NOT 对云端**已下发的 `dwellMs`** 再叠 `tempo`（云端 `computeDwellMs` 已烘入 `tempo`，二次叠会 double-count）。

`session.budget.pacing` 通道 SHALL 从协议中移除（删除 `PacingDefaultsPayload` 类型与 `SessionBudgetPayload.pacing` 字段）：边缘从不请求 `session.budget`、也从不消费其 `pacing` 字段，云端 MUST NOT 再以该通道下发任何兜底默认；兜底默认的唯一下发路径为 `welcome` 快照。`session.budget` 消息其余字段（预算 + `viewOnly`）不受影响。

#### Scenario: 断连仍非零延迟

- **WHEN** 边缘在没有任何时间指令、且无 `welcome` pacing 快照的情况下运行
- **THEN** 各决策节点与详情页返回仍使用边缘内置非零默认下限，不出现零延迟秒退

#### Scenario: 握手快照仅含兜底参数

- **WHEN** 云端在 `welcome` 下发 `pacing` 快照
- **THEN** 该对象仅含 `tempo` 与每类操作 floor 区间等兜底字段，不含内容相关的 read / pause / fatigue 系数

#### Scenario: 兜底停留随档位放慢

- **WHEN** 边缘在缺 `dwellMs` 时回落内置详情页停留兜底，且当前生效 `tempo` 为 `warned` / `restricted` 档（>1）
- **THEN** 采样得到的兜底停留中心值按 `tempo` 放大（风控越差停留越长），仍叠 lognormal 抖动与非零下限

#### Scenario: 云端已下发 dwellMs 不再叠 tempo

- **WHEN** 云端下发带 `dwellMs` 的 `navigation.back` / `note.close`（该值已含云端烘入的 `tempo`）
- **THEN** 边缘以该 `dwellMs` 为中心值、只叠抖动，MUST NOT 再乘 `this.tempo`（避免风控放慢被计两次）

#### Scenario: 不经废弃通道下发

- **WHEN** 云端需要向边缘提供兜底默认
- **THEN** 经 `welcome` 快照下发；协议中不再存在 `session.budget.pacing` 字段，边缘不请求也不消费 `session.budget` 的节奏字段

## ADDED Requirements

### Requirement: 风控档位中途变化实时传播到边缘兜底

当账号风控状态在**一次稳定连接的会话中途**迁移（如 `normal → warned → restricted`）导致 `tempo` 档位变化时，云端 SHALL 主动把新的 `tempo` 推送给边缘（不依赖断连重连）；边缘 SHALL 据此更新其兜底节奏所用的 `tempo`，使最小间隔 gating 与内置停留兜底随实时风控状态放慢。

该推送 MUST NOT 重置边缘的最小间隔锚点（`lastActionEndAt`）——中途档位刷新不等于重连，MUST NOT 借此跳过一次操作间隔。云端 SHALL 仅在 `tempo` 相对**上次已推送值**变化时推送（去抖，避免每命令冗余下发）；握手时边缘已由 `welcome` 快照取得初始 `tempo`，云端 MUST NOT 在无变化时重复推送。该推送为控制消息，MUST 经统一命令出口的原始下发通道直发，MUST NOT 消耗互动配额、MUST NOT 被软暂停闸抑制。该推送为向后兼容的可选消息：旧边缘忽略即可，行为不劣化。

#### Scenario: 中途升档实时放慢边缘兜底

- **WHEN** 会话稳定连接期间账号风控由 `normal` 迁移至 `warned`（`tempo` 1.0→1.3），且期间无断连重连
- **THEN** 云端把新 `tempo` 推送给边缘，边缘后续最小间隔 gating 与内置停留兜底按新 `tempo` 放大，无需等待一次重连

#### Scenario: 档位刷新不重置操作间隔锚点

- **WHEN** 边缘在两次操作之间收到中途 `tempo` 推送
- **THEN** 边缘更新 `tempo` 但保留 `lastActionEndAt` 锚点，不因此跳过或重置当前的最小间隔计时

#### Scenario: 无变化不冗余推送

- **WHEN** 账号风控状态在会话中途保持不变（`tempo` 未变）
- **THEN** 云端不重复推送 `tempo`（仅在档位实际变化时推送一次）

#### Scenario: 旧边缘忽略档位推送

- **WHEN** 边缘版本早于本 change、收到中途 `tempo` 推送消息
- **THEN** 边缘忽略该消息、继续用握手时的 `tempo`，行为不劣化（向后兼容）
