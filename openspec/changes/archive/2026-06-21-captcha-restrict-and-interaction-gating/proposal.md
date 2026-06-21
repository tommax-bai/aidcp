## Why

边缘已经能发现验证码 / 阻断弹窗并向云端发 `risk.captcha_detected` / `risk.captcha_cleared`，但**云端没有任何消费端**——消息撞到 handler switch 的 default、回一条 `unsupported_type` 被静默丢弃，云端 `protocol.ts` 连这两个类型都没有。与此同时，代码核查暴露出一个更深的洞：**点赞 / 收藏 / 关注的风控在边缘与云端两侧都是死的**——边缘 `risk.canDo/record` 零调用，云端 `RiskController`（配额 / 状态机 / canDo / dedup 全套引擎）从不接数据库、`record()` 挂在一个从没人发的事件上、`applySignal()` 没有活调用者、状态永远钉在 `normal`；唯一限制互动的是一个每次重连就清零的内存计数器。结果是互动在**没有任何按账号、可持久、带比例 / 去重约束**的情况下发出。验证码恰好是能让这套休眠的 `RiskController` 第一次接到**真实平台信号**的入口，接对它就同时堵上了这个洞。

## What Changes

- **云端接住验证码上报**：镜像 `risk.captcha_detected` / `risk.captcha_cleared` 两个消息类型与 payload，新增 `CaptchaCoordinator` 消费。
- **验证码 → 风控状态迁移**：`kind:'captcha'` 触发 `applySignal('confirmed')` → `restricted`；`kind:'unknown'` 触发 `applySignal('light')` → `warned`（更温和，unknown 可能只是未识别的普通弹窗）。这是 `RiskController` 状态机第一次被真实信号驱动。
- **按 edge 暂停指令下发**：在传输层 `EdgeCloudServer.pushToEdges` 加 `pausedEdges` 闸（按 `session.edgeId` 跳过），验证码期间停发该 edge 的浏览 / 互动指令，`session.end` 仍可达；清除后恢复。
- **飞书通知（notify-only）**：复用现成的 `buildAlertCard` 只读告警卡发"验证码弹出 / 账号 X / 机器 Y / 远程地址"，新增按 edge 的冷却防刷屏；无审批按钮、无 `/tmp` 信号文件（与发布审批不同）。
- **唤活 RiskController 让 `restricted` 真正咬得动（关键修复）**：用 `RiskController.create({store: PgRiskStore})` 构造以持久化状态；补发缺失的 `interaction.occurred` 让 `record()` 按账号计数；在下发 like/collect/follow 前查 `canDo()`，拒了就**诚实跳过**（不伪装成功、不误扣 budget）。
- **边缘 hello 上报身份**：`HelloPayload` 增加 `accountId` 与机器 / 远程桌面定位（`machineLabel` / `remoteAddr`），云端落到连接登记表——同时解决"该 restrict 哪个账号"（今硬编码 `acc-default`）与"叫人去哪台机器解"两个缺口。
- **清理边缘死代码**：删除 `EdgeClient.canDo/recordRiskAction/requestSessionBudget`（风控云端单写，边缘保持轻量）；`risk.canDo/record/session.budget` 协议类型保留为 reserved 通道。
- **协议 v2 三处同步**：两份 `protocol.ts` 逐字一致（消息数 → 44）+ `command-bridge` + `docs/protocol.md` 计数与表。

## Capabilities

### New Capabilities

- `captcha-incident-handling`: 云端接收边缘验证码 / 阻断弹窗上报后的完整事件闭环——识别归属账号 / 机器、迁移风控状态、按 edge 暂停下发、去重冷却后发飞书通知、收到清除后恢复，全程不伪装成功、不死锁浏览循环。
- `interaction-risk-gating`: 云端在下发 like/collect/follow 前依 `RiskController` 真实判定（状态 + 按账号持久配额），唯一单写账号风控状态；被拒互动诚实跳过。把休眠的风控引擎接入现役下发路径并持久化。

### Modified Capabilities

<!-- 无：command-pacing 的 tempo 放慢已是既有 requirement（"风控降级整体放慢"场景），本 change 只是首次提供其触发信号（验证码→状态迁移），不改其 requirement；browse-loop-resilience 的看门狗与按-edge 暂停兼容（发给已暂停 edge 的 nudge 在传输层被丢弃，session.end 仍可达），无 requirement 变更。 -->

## Impact

- **aidcp-cloud（主体）**：`comm/protocol.ts`（+2 消息 +2 payload，HelloPayload 加字段）、`comm/handler.ts`（2 个 case + onHello 落身份）、`comm/ws-server.ts`（`pausedEdges` + `pauseEdge/resumeEdge`，`EdgeSession` 加 accountId/machine）、新增 `CaptchaCoordinator`、`server.ts`（`RiskController.create` + `PgRiskStore` 接线、补发 `interaction.occurred`）、`orchestrator/role-dispatcher.ts`（互动下发前 `canDo` 闸）、`feishu/cards.ts` + `types.ts`（`AlertData` 加机器字段）、`feishu/messenger` 调用点 + 共享 chatId 解析、`feishu/commands.ts`（手动恢复命令）。
- **aidcp-edge**：`comm/protocol.ts`（HelloPayload 镜像加字段）、`main.ts`（hello 上报 accountId/machine）、`client/edge-client.ts`（删 3 个死包装）。验证码功能本体（已在工作区、测试全绿）随本 change 一并提交，与无关的 chrome-launcher 登录探测修复**分开提交**。
- **数据库**：首次实际使用既有 `risk_state` / `risk_counters` 表（`PgRiskStore`，迁移已存在）。
- **协议 / 风控红线**：协议 v2 三处同步 + `Record<MessageType,true>` 穷举 + `AC-PROTO`（数 44）；`AC-RISK`（绝不自残、被禁 record 返 false）；MUST NOT 静默假成功；账号风控终态仅云端单写。
- **运维**：飞书凭证仍仅云端持有；验证码卡片为单向通知、无需信号文件回写；部署后 `restricted` 账号在恢复窗口（默认 3 天）内仅浏览不互动——安全姿态，可经飞书手动恢复加速。
