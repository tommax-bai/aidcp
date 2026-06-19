## 1. 协议同步（两仓 + docs，最先做，后续都依赖它）

- [x] 1.1 aidcp-cloud `src/comm/protocol.ts`：新增 `MessageType` 成员 `risk.captcha_detected` / `risk.captcha_cleared`，新增 `CaptchaDetectedPayload{edgeId?,kind:'captcha'|'unknown',url?,accountId?,reason?}` / `CaptchaClearedPayload{edgeId?,url?,accountId?}`，并补 `PayloadMap` 两项（与 edge 现有定义逐字一致） <!-- aidcp-cloud pending-commit 镜像 edge captcha 类型+payload+PayloadMap -->
- [x] 1.2 两仓 `src/comm/protocol.ts` `HelloPayload`：新增 `accountId?: string` 与机器定位字段（`machineLabel?: string` / `remoteAddr?: string`），两份逐字一致 <!-- aidcp-cloud+aidcp-edge pending-commit HelloPayload +accountId/machineLabel/remoteAddr -->
- [x] 1.3 两仓 `test/acceptance/protocol-contract.test.ts`：`ALL_MESSAGE_TYPES` 含两 captcha key、消息数断言 = 44（edge 已是 44，云端从 42 同步上来） <!-- aidcp-cloud pending-commit 云端 42→44 + 2 key；edge 已是 44 -->
- [x] 1.4 `docs/protocol.md`（控制仓权威版，云端无此文件）：头部计数 42→44、§2.5 表补两行、§3.9 补 captcha payload 定义 <!-- aidcp(本仓) pending-commit 计数+表+payload 定义 -->
- [x] 1.5 验证协议不漂移：两仓各跑 `npm run typecheck`（`Record<MessageType,true>` 穷举过）+ `AC-PROTO-*` 绿 <!-- 两仓 typecheck 干净；AC-PROTO 各 5/5 绿，数 44 -->

## 2. aidcp-cloud — 验证码消费端闭环（captcha-incident-handling）

- [x] 2.1 `src/comm/handler.ts`：在 `DefaultMessageHandler.handle` switch 增 `risk.captcha_detected` / `risk.captcha_cleared` 两个 case，路由到新建 `CaptchaCoordinator`（emit-event + ack/null，仿 `page.cards` 形态），不再落 `unsupported_type` <!-- aidcp-cloud 3c84ccf -->
- [x] 2.2 `src/comm/handler.ts` `onHello`：把 `accountId` / `machineLabel` / `remoteAddr` 落到 `EdgeSession`；`src/comm/ws-server.ts` `EdgeSession` 接口加这些字段（缺失安全降级） <!-- aidcp-cloud 3c84ccf -->
- [x] 2.3 `src/comm/ws-server.ts`：加 `pausedEdges: Set<string>` + `pauseEdge(edgeId)` / `resumeEdge(edgeId)`，在 `pushToEdges` 连接循环跳过 `session.edgeId ∈ pausedEdges`；确保 `session.end` 不被该闸拦（必达） <!-- aidcp-cloud 3c84ccf bypassPause=session.end；另加 resumeEdgesForAccount + address() -->
- [x] 2.4 新建 `CaptchaCoordinator`：detected → 据 `kind` 调 `RiskController.applySignal`（captcha=`confirmed`、unknown=`light`）+ `pauseEdge` + 触发飞书通知；cleared → `resumeEdge`（不自动回滚风控态） <!-- aidcp-cloud 3c84ccf 落在 src/comm/captcha-coordinator.ts（与 handler 同层，避开 risk→comm/feishu 循环依赖） -->
- [x] 2.5 `src/feishu/`：抽出共享 chatId 解析 helper，`CaptchaCoordinator` 用它 + `messenger.sendCard(buildAlertCard(...))`；机器/远程地址映射进 `detail` <!-- aidcp-cloud 3c84ccf 新增 src/feishu/chat-target.ts(resolveDefaultChatId)；publish 审批路径暂不迁移（避免 churn AC-PUB 红线路径）；AlertData 未扩字段，机器/地址走 detail -->
- [x] 2.6 飞书去重冷却：发卡调用点维护 `Map<edgeId,lastSentTs>`，默认 ~10min 窗内同一 edge 只发一卡（可配）；发送失败记录日志、不静默吞（红线） <!-- aidcp-cloud 3c84ccf cleared 清掉该 edge 冷却 -->
- [x] 2.7 飞书手动恢复：复用 `/resume <accountId>` 命令 → `server.resumeEdgesForAccount` 解除该账号 edge 暂停，作为恢复窗人工快路 <!-- aidcp-cloud 3c84ccf 改 server.ts actions.resume；风控态降级未做（保守，留待需要时） -->

## 3. aidcp-cloud — 唤活 RiskController（interaction-risk-gating）

- [x] 3.1 `src/server.ts`：改用 `RiskController.create({store: new PgRiskStore()})`，状态/计数落库 + 启动回放；PG 不可用回退 `new RiskController()`（不阻塞启动） <!-- aidcp-cloud 3c84ccf handler.ts:114 兜底保持 new RiskController() 不变（仅 server 主路径接 store） -->
- [x] 3.2 `src/comm/handler.ts` `action.completed{like/collect/follow, ok:true}` 路径补发 `interaction.occurred`，驱动既有订阅者 `RiskController.record()` 按账号计数（排除 already_followed；失败不计） <!-- aidcp-cloud 3c84ccf 同时把 EventMap interaction.occurred 拓宽含 follow、noteId 可选 -->
- [x] 3.3 `src/orchestrator/role-dispatcher.ts`：新增 `canInteract` 选项，在 interaction.completed(like/collect) 与 profile.done(follow) 出口 `sendCommand` 前查 `canDo`；拒则跳过、不 `consumeBudget`；scroll/back 不加闸 <!-- aidcp-cloud 3c84ccf server 接线 canInteract=(a)=>riskController.canDo(a) -->
- [x] 3.4 自测：`restricted` 下 like/collect/follow 被拦但 scroll 继续（不死锁）；`frozen`/超额 `record` 返 false（`AC-RISK-*`） <!-- aidcp-cloud 3c84ccf test/integration/risk-gating-dispatch.test.ts + AC-RISK 既有用例仍绿 -->

## 4. aidcp-edge — hello 上报 + 删死包装

- [x] 4.1 `src/main.ts` hello 构造：上报 `accountId` 与机器定位（`machineLabel`/`remoteAddr`），来源 env `AIDCP_ACCOUNT_ID`/`AIDCP_MACHINE_LABEL`/`AIDCP_REMOTE_ADDR`；EdgeClientOptions+hello payload 同步加字段 <!-- aidcp-edge 9126e04 条件 spread，缺省不带 -->
- [x] 4.2 验证码 payload 在已知账号时填 `accountId`（`main.ts` detected/cleared 两处） <!-- aidcp-edge 9126e04 -->
- [x] 4.3 删除 `src/client/edge-client.ts` 的 `canDo`/`recordRiskAction`/`requestSessionBudget` 三个死包装及其无用类型 import（保留协议 reserved 类型，协议数不变） <!-- aidcp-edge 9126e04 -->
- [x] 4.4 确认浏览闭环（`browse-session.ts`）无任何互动前 `risk.canDo` / 互动后 `risk.record` 调用（风控全在云端） <!-- aidcp-edge 9126e04 grep 确认零调用，仅剩 reserved 协议类型 -->

## 5. 测试与回归（两仓，先 acceptance 再全量再 typecheck）

- [x] 5.1 aidcp-cloud：`test:acceptance` + 全量 `npm test` + `typecheck` 全过 <!-- aidcp-cloud 3c84ccf 185/185 pass、typecheck 干净；新增 captcha-coordinator/ws-server-pause/risk-gating-dispatch 共 +12 -->
- [x] 5.2 aidcp-edge：`test:acceptance` + 全量 `npm test` + `typecheck` 全过 <!-- aidcp-edge 9126e04 251/251 pass、typecheck 干净 -->
- [x] 5.3 安全红线全过：`AC-PROTO-*`（两仓数 44 不漂移）、`AC-RISK-*`（绝不自残）、`AC-PUB-*`（不受影响） <!-- 两仓 AC-PROTO 44 绿；cloud AC-RISK/AC-PUB 绿；edge AC-PUB 绿 -->

## 6. 提交与部署

- [x] 6.1 aidcp-edge 验证码功能单独成 commit（与 chrome-launcher 分开）；aidcp-cloud 提交云端改动 <!-- aidcp-cloud 3c84ccf / aidcp-edge 9126e04；edge chrome-launcher 与 cloud recency-aware-revisit-pacing(并行在制) 均留工作区未提交 -->
- [x] 6.2 本仓回写 tasks 进度（HTML 注释标 `[x]` + commit-sha + 偏离说明），按 sub-repo 分节
- [ ] 6.3 ECS 部署（带安全闸，**显式动作待确认**）：先备份 → rsync(exclude .env/node_modules/.git) → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连 + PG `select 1` + `risk_state`/`risk_counters` 可读）→ 失败回滚；部署后 tasks 追加 `<!-- <date> deployed -->`
- [ ] 6.4 真机验证：人为触发一次验证码 → 确认云端置 `restricted` + 停下发 + 飞书卡（账号/机器/地址）+ DOM 清除后恢复；归档 change（`openspec validate --strict` → archive）
