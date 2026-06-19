## 1. 协议同步（两仓 + docs，最先做，后续都依赖它）

- [ ] 1.1 aidcp-cloud `src/comm/protocol.ts`：新增 `MessageType` 成员 `risk.captcha_detected` / `risk.captcha_cleared`，新增 `CaptchaDetectedPayload{edgeId?,kind:'captcha'|'unknown',url?,accountId?,reason?}` / `CaptchaClearedPayload{edgeId?,url?,accountId?}`，并补 `PayloadMap` 两项（与 edge 现有定义逐字一致）
- [ ] 1.2 两仓 `src/comm/protocol.ts` `HelloPayload`：新增 `accountId?: string` 与机器定位字段（`machineLabel?: string` / `remoteAddr?: string`），两份逐字一致
- [ ] 1.3 两仓 `test/acceptance/protocol-contract.test.ts`：`ALL_MESSAGE_TYPES` 含两 captcha key、消息数断言 = 44（edge 已是 44，云端从 42 同步上来）
- [ ] 1.4 `aidcp-cloud/docs/protocol.md`：头部消息计数同步、§2 表补 `risk.captcha_detected` / `risk.captcha_cleared` 两行与 HelloPayload 字段说明（人工维护，勿漏）
- [ ] 1.5 验证协议不漂移：两仓各跑 `npm run typecheck`（`Record<MessageType,true>` 穷举过）+ `AC-PROTO-*` 绿

## 2. aidcp-cloud — 验证码消费端闭环（captcha-incident-handling）

- [ ] 2.1 `src/comm/handler.ts`：在 `DefaultMessageHandler.handle` switch 增 `risk.captcha_detected` / `risk.captcha_cleared` 两个 case，路由到新建 `CaptchaCoordinator`（emit-event + ack/null，仿 `page.cards` 形态），不再落 `unsupported_type`
- [ ] 2.2 `src/comm/handler.ts` `onHello`：把 `accountId` / `machineLabel` / `remoteAddr` 落到 `EdgeSession`；`src/comm/ws-server.ts` `EdgeSession` 接口加这些字段（缺失安全降级）
- [ ] 2.3 `src/comm/ws-server.ts`：加 `pausedEdges: Set<string>` + `pauseEdge(edgeId)` / `resumeEdge(edgeId)`，在 `pushToEdges` 连接循环跳过 `session.edgeId ∈ pausedEdges`；确保 `session.end` 不被该闸拦（必达）
- [ ] 2.4 新建 `src/risk/captcha-coordinator.ts`（或就近目录）`CaptchaCoordinator`：detected → 据 `kind` 调 `RiskController.applySignal`（captcha=`confirmed`、unknown=`light`）+ `pauseEdge` + 触发飞书通知；cleared → `resumeEdge`（不自动回滚风控态）
- [ ] 2.5 `src/feishu/`：抽出共享 chatId 解析 helper（替换 `handler.ts:362` / `publish-executor` / `commands.ts` 的重复），`CaptchaCoordinator` 用它 + `messenger.sendCard(buildAlertCard(...))`；`AlertData`（`types.ts`）加机器 / 远程地址字段或映射进 `accountName/detail`
- [ ] 2.6 飞书去重冷却：在发卡调用点维护 `Map<edgeId,lastSentTs>`，默认 ~10min 窗内同一 edge 只发一卡（可配）；发送失败记录日志、不静默吞（红线）
- [ ] 2.7 `src/feishu/commands.ts`：新增手动恢复命令（复用 `/pause /resume` 设施）→ `resumeEdge` + 可选风控降级，作为 3 天恢复窗的人工快路

## 3. aidcp-cloud — 唤活 RiskController（interaction-risk-gating）

- [ ] 3.1 `src/server.ts:134`（及 `src/comm/handler.ts:114` 兜底）：改用 `RiskController.create({store: new PgRiskStore(), ...})`，状态 / 计数落库 + 启动回放（替换无 store 的 `new RiskController()`）
- [ ] 3.2 `src/server.ts`：在 `action.completed{action∈{like,collect,follow}, ok:true}` 路径补发 `interaction.occurred`，驱动既有订阅者 `RiskController.record()` 按账号计数（记真实成功，不在下发时记）
- [ ] 3.3 `src/orchestrator/role-dispatcher.ts:312-318`（like/collect）与 `344-350`（follow）：`sendCommand` 前查 `RiskController.canDo(action)`；拒则跳过、**不 `consumeBudget`**、如实记被拦（MUST NOT 假成功）；`page.scroll` / `navigation.back` 不加闸
- [ ] 3.4 自测：`restricted` 账号下 like/collect/follow 被拦但 scroll/back 继续（不死锁）；`frozen`/超额账号 `record` 返 false（`AC-RISK-*`）

## 4. aidcp-edge — hello 上报 + 删死包装

- [ ] 4.1 `src/main.ts` hello 构造：上报 `accountId` 与机器定位（`machineLabel`/`remoteAddr`，来源依实际部署：env / 配置）
- [ ] 4.2 可选：验证码 payload 在已知账号时填 `accountId`（`main.ts:191/201`，字段已声明、当前 undefined）
- [ ] 4.3 删除 `src/client/edge-client.ts:225-238` 的 `canDo` / `recordRiskAction` / `requestSessionBudget` 三个死包装及其无用类型 import（保留 `risk.canDo/record/session.budget` 协议类型为 reserved，勿动协议数除 1.x 外）
- [ ] 4.4 确认浏览闭环（`browse-session.ts`）无任何互动前 `risk.canDo` / 互动后 `risk.record` 调用（风控全在云端）

## 5. 测试与回归（两仓，先 acceptance 再全量再 typecheck）

- [ ] 5.1 aidcp-cloud：`npm run test:acceptance && npm test && npm run typecheck` 全过（含新 `CaptchaCoordinator` / pauseEdge / canDo 闸 / RiskController 持久化单测）
- [ ] 5.2 aidcp-edge：`npm run test:acceptance && npm test && npm run typecheck` 全过（验证码本体已有测试 + hello 字段 + 删包装后无回归）
- [ ] 5.3 安全红线全过：`AC-PROTO-*`（两仓数 44 不漂移）、`AC-RISK-*`（绝不自残）、`AC-PUB-*`（不受影响）

## 6. 提交与部署

- [ ] 6.1 aidcp-edge：把验证码功能（含本 change 的 hello 字段 + 删包装）单独成 commit，与无关的 chrome-launcher 登录探测修复**分开**；aidcp-cloud 提交云端改动；两仓一并提交（用户决定）
- [ ] 6.2 本仓回写 tasks 进度（HTML 注释标 `[x]` + commit-sha + 偏离说明），按 sub-repo 分节
- [ ] 6.3 ECS 部署（带安全闸）：先备份 → rsync(exclude .env/node_modules/.git) → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连 + PG `select 1` + `risk_state`/`risk_counters` 可读）→ 失败回滚；部署后 tasks 追加 `<!-- <date> deployed -->`
- [ ] 6.4 真机验证：人为触发一次验证码 → 确认云端置 `restricted` + 停下发 + 飞书卡（账号/机器/地址）+ DOM 清除后恢复；归档 change（`openspec validate --strict` → archive）
