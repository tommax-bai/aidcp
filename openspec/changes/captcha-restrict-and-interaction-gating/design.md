## Context

边缘已落地「弹窗旁路监测 + 验证码本地暂停 + 上报」：后台 `CdpOverlayMonitor` 每秒判类 `none|login|captcha|dismissible|unknown`，翻进 `captcha`/`unknown` 时向云端 fire-and-forget 发 `risk.captcha_detected{edgeId,kind,url}`，翻出时发 `risk.captcha_cleared{edgeId}`（`aidcp-edge/src/main.ts:181-207`）。`login` 只本地暂停、不打扰云端。这套已测试通过、在 edge 工作区未提交。

代码核查（6 路并行）确认当前云端两个事实：

1. **验证码无消费端**：`DefaultMessageHandler.handle` 是 `switch(env.type)`（`handler.ts:122`），未知类型落 default 回 `unsupported_type`。云端 `protocol.ts` 无这两类型（云端数 42，edge 已 44）。
2. **互动风控两侧皆死**：边缘 `EdgeClient.canDo/recordRiskAction/requestSessionBudget`（`edge-client.ts:225-238`）零调用；云端 `RiskController` 全套引擎建好但全空转——`server.ts:134` 用无 store 的 `new RiskController()`，状态永钉 `normal`；`record()` 订在从没人发的 `interaction.occurred`（`server.ts:137-141`）；`applySignal()` 无活调用者；`PgRiskStore` 从没被 new。唯一限互动的是 `RoleDispatcher` 易失内存 budget（`role-dispatcher.ts:210-212`，重连清零）。

约束（CLAUDE.md）：边轻云重 + 账号风控终态云端单写；MUST NOT 静默假成功；协议 v2 三处同步 + `Record<MessageType,true>` 穷举；浏览循环不死锁、`session.end` 必达。

## Goals / Non-Goals

**Goals:**

- 让 edge 已发的验证码上报在云端形成闭环：归属 → 迁状态 → 按 edge 停下发 → 去重发飞书 → 清除恢复。
- 让休眠的 `RiskController` 第一次被真实信号驱动并真正约束互动下发（持久化 + canDo 闸 + 按账号计数），以验证码为首个触发器。
- 用 hello 上报的 `accountId` + 机器定位解决「restrict 哪个账号 / 叫人去哪台机器」两个缺口。

**Non-Goals:**

- 不实现「验证码已解决」回写按钮 / 信号文件（验证码是单向通知；edge 靠 DOM 清除自动恢复）。
- 不改动边缘验证码检测本体（已落地），本 change 只加云端消费 + 边缘 hello 字段 + 删边缘死包装。
- 不重做 `command-pacing` 的 tempo 公式（其 requirement 已含「风控降级整体放慢」，本 change 只首次提供触发信号）。
- 不引入新的多账号路由架构；当前为单 dispatcher 广播，按 `edgeId` 跳过即可满足按-edge 暂停。

## Decisions

### D1：按 edge 暂停下发的落点 = 传输层 `pushToEdges`，而非会话层

在 `EdgeCloudServer` 加 `pausedEdges: Set<string>` + `pauseEdge/resumeEdge`，在 `pushToEdges` 的连接循环里跳过 `session.edgeId ∈ pausedEdges` 的连接（`ws-server.ts:105-116`）。

- **为什么**：`pushToEdges` 是所有出站指令（角色驱动 / publish / trigger）的唯一传输汇聚点；广播循环本就逐个连接、拿得到每个 `session.edgeId`，跳过即按 edge 生效，**无需把 edgeId 串进 `sendCommand` 签名**。它独立于会话态，扛得住 `RoleDispatcher.restartSession`（每次 `edge.hello` 重连都会重建订阅，`role-dispatcher.ts:206`）。
- **否决的替代**：① 在 `RoleDispatcher.sendCommand` 早返——只盖角色流量，漏掉 publish/trigger；② `endSession`/丢 `SessionContext`——只有一个共享 `SessionContext`（`role-dispatcher.ts:110`），会冻结所有 edge，且下次 `edge.hello` 自动重启、暂停被静默清除；③ `edgeCommandToEnvelope` 里挡——无状态、无 edge 概念。
- **不变量**：`session.end` 不走该闸（必达，否则触发 `browse-loop-resilience` 的死锁类 bug）。被丢弃的指令不得回报成功——天然成立：edge 暂停期间不再上报 `page.cards`，云端无新事件即不产指令，传输层 drop 只是双保险。

### D2：验证码 → 状态迁移的强度（captcha=restricted，unknown=warned）

`kind:'captcha'` → `applySignal({kind:'confirmed'})`（`normal`→`restricted`，`risk-state-machine.ts:45`）；`kind:'unknown'` → `applySignal({kind:'light'})`（`normal`→`warned`）。

- **为什么**：验证码是强平台信号，`restricted`（保留 view、清零互动配额）是恰当姿态；`unknown` 可能只是没识别出来的普通弹窗，`warned`（配额 ×0.7、仍允许互动）更温和、避免误伤。两者都已是状态机现成转移，无需新增转移代码。
- **粘性**：`restricted` 经恢复窗口降级需 `RESTRICTED_RECOVERY_MS=3d` 无新信号（`risk-state-machine.ts:3-4`）。即一次验证码后账号默认 3 天内仅浏览不互动——安全姿态。**提供飞书手动恢复命令**（复用既有 `/pause /resume` 命令设施 + `AccountStateManager`/`resumeEdge`）作为加速通道。
- **否决的替代**：captcha 直接 `frozen`（过重，全停含浏览）；或一律 `warned`（验证码这种强信号下太轻）。

### D3：飞书通知复用 `buildAlertCard`，冷却放调用点

复用既有 notify-only `buildAlertCard`（`cards.ts:116`，其 `AlertData` 注释示例正好是「验证码弹出」），经 `messenger.sendCard` 发送；用与发布审批同一套 chatId 解析（`handler.ts:362` `defaultChat→approvalChatId→FEISHU_CHAT_ID`，抽成共享 helper 避免第四处复制）。

- **为什么**：零新卡片代码；`FeishuMessenger` 保持无状态 dumb transport（可测）。冷却（默认 ~10min/edge）作为**新增**设施放在调用点的 `Map<edgeId, lastSentTs>`，不塞进 messenger。
- **`AlertData` 扩字段**：现仅 `accountId/accountName`，加机器 / 远程地址字段（或映射进 `accountName/detail`）。
- **否决的替代**：新建带按钮 / 信号文件的审批式卡片——验证码无需人工 yes/no 回写，纯通知；那套 `/tmp/aidcp-publish-approve-*.json` 契约不可被验证码复用 / 污染。

### D4：唤活 RiskController 的三处接线（让 restricted 真咬得动）

- **构造**：`server.ts:134`（及 `handler.ts:114` 兜底）改 `RiskController.create({store: new PgRiskStore(), ...})` → 状态 / 计数落库 + 启动回放。表与迁移已存在。
- **计数**：在 `action.completed{ok:true}` 的 like/collect/follow 处补发 `interaction.occurred`（`server.ts:137` 的订阅者已就位，只缺 emit）→ `record()` 按账号累加。**记真实成功**，不在下发时记。
- **闸**：在 `RoleDispatcher.setupCommandTranslation` 的两处互动出口（`role-dispatcher.ts:312-318` like/collect、`344-350` follow）于 `sendCommand` 前查 `canDo(action)`；拒则跳过且**不 `consumeBudget`**（红线：budget 不得漂移），如实记被拦。
- **否决的替代**：让 edge 调 `risk.canDo` 自挡——违背边轻云重 + 状态单写；且 edge 那套已是死代码，本 change 删之。

### D5：身份经 hello 上报（用户已选）

`HelloPayload` 加 `accountId` + 机器定位（`machineLabel`/`remoteAddr`），两份 `protocol.ts` 镜像；云端 `onHello`（`handler.ts:199-209`）落到 `EdgeSession`（`ws-server.ts:24-28`）/ 连接表。一举解决归属账号（今硬编码 `acc-default`）与机器定位。缺字段安全降级（卡片至少带 `edgeId`，状态落默认账号）。

- **否决的替代**：云端静态配置表 edgeId→{账号,机器}——用户更要动态准确；纯 edgeId 卡片——运维还得自己查机器。

## Risks / Trade-offs

- **[一次验证码 → 账号 3 天不互动]** `restricted` 恢复窗口 3 天，可能过严 → 飞书手动恢复命令作为快路；`unknown` 只 `warned` 减少误伤；窗口值后续可调。
- **[多 edge 下广播 + 单共享 SessionContext]** 当前 dispatcher 广播、一个 `SessionContext` 服务所有 edge → 按-edge 暂停靠传输层 `edgeId` 过滤可行，但「按账号独立浏览预算 / 状态」仍是后续架构债，本 change 不解决，仅按 edge 暂停下发。
- **[协议三处漂移]** 加 2 消息 + 改 HelloPayload → 两份 `protocol.ts` 逐字一致 + `command-bridge` + `docs/protocol.md` + 两仓 `AC-PROTO` 数 44，任一漏改 typecheck 挂 → 任务清单显式列每处。
- **[看门狗与暂停交互]** 长时间验证码未解 → `browse-loop-resilience` 看门狗可能 `session.end`；这是可接受的干净收尾（发给暂停 edge 的 nudge 被传输层丢弃、`session.end` 必达），edge 清除后下次会话重新生效。不改看门狗 requirement。
- **[飞书刷屏]** 无既有 outbound 去重设施 → 新增 per-edge 冷却是必须项，否则 edge 循环验证码会刷爆群。
- **[record 时机]** 必须在 `action.completed{ok:true}` 记、不在下发记，否则 `blocked_by_captcha` 的失败互动被误计 → 计数失真。

## Migration Plan

1. 边缘：`HelloPayload` 加字段 + `main.ts` hello 上报；删 3 个死包装；验证码本体随本 change 提交（与 chrome-launcher 修复分开 commit）。
2. 云端：协议镜像（数 44）→ `CaptchaCoordinator` + handler case → `pauseEdge/resumeEdge` → `RiskController.create+PgRiskStore` → `interaction.occurred` emit → canDo 闸 → 飞书卡 + 冷却 + 共享 chatId → onHello 落身份 → 飞书手动恢复命令。
3. 测试两仓：`npm run test:acceptance && npm test && npm run typecheck`，`AC-PROTO`/`AC-RISK` 必过。
4. **部署（ECS，带安全闸）**：先备份 → rsync（exclude .env/node_modules/.git）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连 + PG `select 1` + 新表可读）→ 失败回滚。`PgRiskStore` 首次启用注意库连接与表存在。
5. 回滚：云端回滚到备份即恢复「验证码无消费 / 风控空转」旧行为（edge 上报被忽略，无害）。

## Open Questions

- `restricted` 恢复窗口 3 天是否符合运营预期，还是要更短 / 接平台真实解封信号？（暂用 3 天 + 手动恢复，留待真机观测后调。）
- 机器定位字段命名与来源（环境变量 / 配置 / 远程桌面系统）以边缘实际部署形态为准，实装时定。
- 多账号 / 多 edge 的独立会话与按账号浏览预算是已知架构债，本 change 不含，后续单独 change。
