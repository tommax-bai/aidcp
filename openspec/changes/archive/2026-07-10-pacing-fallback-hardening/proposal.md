## Why

对节奏兜底（Command Pacing 的兜底层）做端到端溯源后发现三条真实缺口 + 两条被误报的「洞」。真实缺口：

1. **中途档位到不了边缘兜底**：`welcome` 快照下发的 `tempo`（风控档，`normal=1.0`/`warned=1.3`/`restricted|frozen=1.6`）在**握手期采一次即冻结**，边缘只在**（重）连接边界**经 `applyPacingSnapshot` 刷新。会话稳定连接期间风控升档（如验证码/配额触发 `normal→warned→restricted`）**传不到边缘的兜底节奏层**——边缘最小间隔 gating 仍用握手时的旧 `tempo`。唯一实时跟随风控的是骑在决策命令上的 per-command 中心值（`thinkMs`/`dwellMs`），那是**决策路径不是兜底路径**。
2. **档位不缩放边缘停留兜底**：边缘在缺 `dwellMs` 而回落内置详情页停留兜底（`dwellFloorTiming` 采样）时**不叠 `tempo`**。风控升档只拉长三个 gated op 的最小间隔，**拉不长在页停留兜底**。
3. **`session.budget.pacing` 是双死通道**：云端 `buildPacingDefaults` 仍构造 `{tempo, dwellFloorMs}` 挂在 `session.budget` 回执，但边缘**从不请求** `session.budget`（reserved 通道）、`onMessage` 路由白名单里也没有它、`SessionBudgetPayload.pacing` 全仓无 runtime reader。发端收端皆死，纯冗余。现役 `command-pacing` spec 已把该通道标为「已废弃、MUST NOT 再作为兜底下发路径」，本 change 落实为**从协议移除**。

两条**被误报、实为设计如此**的「洞」（本 change 只文档化、不改代码）：

- feed 翻页「裸奔」：现役 spec 明确「无新卡时云端不带 `dwellMs`、边缘不叠加任何额外延迟」——翻页没新内容就该快速划过，与详情页有停留的不对称是**有意设计**。给它加停留反而违反 spec。
- `content_read`/`content_glance` op floor 边缘收到不用：它们是**云端计算 `dwellMs` 时的夹逼上下界**，不是边缘 gating 用的四类 op（`action`/`scroll`/`card_gap`/`detail_dwell`），边缘不消费属正常。

## What Changes

- **新增 cloud→edge 主动控制消息 `pacing.update`**（独立消息类型，payload `{ tempo }`）：云端在**统一命令出口**检测到 `tempo` 相对上次已推送值变化时推送一次（去抖）；边缘据此更新兜底节奏所用 `tempo`，**不重置最小间隔锚点**（中途刷新 ≠ 重连）。协议四处同步 + 边缘主动命令白名单 + 边缘 switch 分支。
- **边缘停留兜底叠档位**：`ensureDetailDwell` 在缺 `dwellMs` 回落 `dwellFloorTiming` 采样时，对采样中心值叠当前 `tempo` 放大；**MUST NOT** 对云端已下发的 `dwellMs` 再叠（云端已烘入、防二次放大）。
- **移除 `session.budget.pacing`**：删两端 `PacingDefaultsPayload` + `SessionBudgetPayload.pacing`、云端 `buildPacingDefaults` + `PacingDefaults` + `onSessionBudgetRequest` 的 `pacing` 字段与相关测试。`session.budget` 消息其余字段（预算 + `viewOnly`）不动。
- **文档化两条误报**为设计意图（spec 注 + design）。
- **协议消息类型计数** +1（本地基线 70→71；与并发 change `feed-refresh-on-depth` 撞 `protocol.ts`，集成时 rebase 串行，二者各 +1）。

## Capabilities

### Modified Capabilities
- `command-pacing`：
  - MODIFIED「缺时间指令时的安全降级」——`session.budget.pacing` 由「废弃」收紧为「从协议移除」；新增「边缘停留兜底叠当前 `tempo` 档位」子约束与场景。
  - ADDED「风控档位中途变化实时传播到边缘兜底」——中途升档经 `pacing.update` 推送、边缘刷新兜底 `tempo`、不重置操作间隔锚点、去抖、向后兼容。

## Impact

- **aidcp-cloud**：`src/comm/protocol.ts`（新消息类型 + payload；移除 `PacingDefaultsPayload` + `SessionBudgetPayload.pacing`）、`src/comm/command-bridge.ts`（`pacing_update`→`pacing.update` 映射）、`src/orchestrator/role-dispatcher.ts`（`EdgeCommand.action` 并集加 `pacing_update` + 统一出口 tempo 变化去抖推送）、`src/comm/handler.ts`（`onSessionBudgetRequest` 去 `pacing` 字段 + 去 import）、`src/risk/pacing.ts`（删 `buildPacingDefaults` + `PacingDefaults`）、`src/risk/index.ts`（去导出）、`test/acceptance/protocol-contract.test.ts`（`AC-PROTO` 计数 +1 + `pacing.update` round-trip）、`test/risk-pacing.test.ts`（删 `buildPacingDefaults` 用例）。
- **aidcp-edge**：`src/comm/protocol.ts`（与云端逐字一致）、`src/client/edge-client.ts`（`onMessage` 白名单加 `pacing.update`——typecheck 抓不到，漏则静默丢弃）、`src/browse/browse-session.ts`（`executeCommand` 加 `pacing.update` case + `applyTempoUpdate` + `ensureDetailDwell` 兜底叠 tempo；移除对 `PacingDefaultsPayload` 的类型引用）、`test/acceptance/protocol-contract.test.ts`（计数同步）。
- **aidcp（本仓）**：`docs/protocol.md`（消息类型计数 + §2 表新增 `pacing.update` 行）。
- **协议**：`PROTOCOL_VERSION` 不变（仍 2）；消息类型 +1；移除一个 payload 类型 + 一个可选字段（向后兼容：旧边缘忽略 `pacing.update`；`session.budget.pacing` 本就无人消费）。
- **风控 / 配额**：`pacing.update` 是控制消息、经统一出口的 `rawSendCommand` 直发、**不**消耗互动配额、**不**过软暂停闸（档位刷新不应被暂停抑制）。
- **部署**：随 dev 默认部署；无 env 开关（去抖推送本身零回归——无变化不发；有变化才发一条极小控制消息）。真机验收项登记 backlog（真机难触发升档，属 latent）。
