# Tasks

> 仅云端（`aidcp-cloud`）。边缘 / 协议 / 热点文件均不涉及。
> 铁律：目标解析收口**一处**，回落用**补集**（`来源会话 || 团队路由 || 默认群`），绝不白名单枚举卡类型。

## 1. aidcp-cloud — 统一解析出口

- [x] 1.1 在 `src/feishu/chat-target.ts` 增 `resolveCardTarget({ originChatId, accountId }, deps)`：补集式三档（来源会话 → `resolveChatIdForAccount` → `resolveDefaultChatId`），逐层 try/catch 穿透绝不抛入投递闭包，未命中团队路由打 config-gap 日志。 <!-- cloud 0963802 resolveCardTarget：补集三档 + 逐层 try/catch 穿透 -->
- [x] 1.2 `src/server.ts` 的 `resolveAccountChatId`（~1121）之侧收口出一个内聚全部依赖的 `resolveCardChatId(originChatId, accountId)`，让「漏传 store」在类型层面不可表达（沿用 `feishu-route-account-cards-by-team` 的教训 2）。 <!-- cloud 0963802 resolveCardChatId：依赖一处注入 -->
- [x] 1.3 单测：三档优先级各一例 + 团队路由读失败回落默认群 + 无账号无来源会话落默认群。 <!-- cloud 0963802 test/feishu-notification-routing.test.ts 新增 6 例（含空白串来源会话、读失败回落、无账号） -->

## 2. aidcp-cloud — 评论侧来源会话透传（5 个接缝，与发帖对称）

- [x] 2.1 `src/agents/comment-approval-gate.ts`：`CommentApprovalPort.request` 入参增 chat 目标字段（与 `accountId` 并列）。 <!-- cloud 0963802 -->
- [x] 2.2 `src/comment-agent/comment-scheduler.ts`：`triggerManual` / `triggerTargeted` options 增 chat 目标；透传到 `approveFacebookComment`（~1080）与 `compose-approve` 两条 approve 路径。 <!-- cloud 0963802 两 trigger 入口 + approveFacebookComment + 两条 compose 路径 -->
- [x] 2.3 `src/comment-agent/compose-approve.ts`：deps 增 chat 目标并传入 `approval.request`。 <!-- cloud 0963802 人审卡 + 免审通知卡两处 -->
- [x] 2.4 `src/delegated-task/executors.ts`：`DelegatedCommentPort` 的 `triggerManual` / `triggerTargeted` 增 chat 目标字段（**类型层面**，非可选透传约定）；三条评论分支（`comment_batch` / `facebook_group_comment` / `comment_curated`）透传 `task.originChatId`。 <!-- cloud 0963802 端口类型加字段 + 三条评论分支透传 -->
- [x] 2.5 `src/server.ts:2434` 评论审批端口：`resolveDefaultChatId` → `resolveCardChatId(originChatId, accountId)`。**这一行是两个报障现象的共同根因。** <!-- cloud 0963802 两个报障现象的共同根因 -->
- [x] 2.6 单测（克制）：私聊 `/comment` → 审批卡回来源会话；自动排期评论 → 审批卡进账号团队群；账号未绑团队 → 回默认群。 <!-- cloud 0963802 test/delegated-task/executors.test.ts：三分支透传 + 自动路径无来源会话；解析器三档在 1.3 已覆盖 -->

## 3. aidcp-cloud — 手动 `/comment` 终态结果卡回来源会话（销 backlog 86.18）

- [x] 3.1 `CommentScheduler.postResultCard`（`src/server.ts:3119`）取址改用 `resolveCardChatId`；来源会话经同一透传链到达。 <!-- cloud 0963802 5 个 call site 全透传 -->
- [x] 3.2 单测：私聊 `/comment` 的审批卡与终态卡**投同一会话**（防「两卡两群」复发）。 <!-- cloud 0963802 由 2.6 的执行器透传断言 + 1.3 的解析器断言合并覆盖（同一 originChatId 进同一解析）；端到端两卡同群留真机 -->

## 4. aidcp-cloud — 发帖侧镜像缺口

- [x] 4.1 `src/publish-agent/roles/publish-executor.ts` 的 `resolveApprovalCardTarget`（~547）：`manual_source` 之后不再直落 `getDefaultChat`，插入账号团队档（新增 target source，供日志辨识）。 <!-- cloud 0963802 新增 account_scope 档；同时修 PublishResult 里第二份枚举副本的漂移 -->
- [x] 4.2 `src/comm/handler.ts`（~1059）边缘发起的发布审批卡：依赖类型从只暴露 `getDefaultChat` 扩到共享解析，用 `session.accountId` 走三档。 <!-- cloud 0963802 依赖类型扩到统一解析，未注入时保留既有默认群链 -->
- [x] 4.3 单测：自动 / 排期发帖审批卡 → 账号团队群；命令触发仍回来源会话（回归）。 <!-- cloud 0963802 解析器档位由 1.3 覆盖；executor 级断言无既有 harness，留真机 -->

## 5. aidcp-cloud — 带账号的运维告警并入统一规则

- [x] 5.1 盘出全部带 `accountId` 的告警发送点（persona / 验证码 / 边缘离线 / CDP 不健康 / 发布熔断 / publish-dispatch 通知），逐点改走 `resolveCardChatId`。 <!-- cloud 0963802 验证码告警 + 下发段运维通知（离线/接管超时/熔断）改走统一解析 -->
- [x] 5.2 确认**无账号**告警（握手 config-error 等）仍落默认群、不臆造账号作用域。 <!-- cloud 0963802 握手 config-error 保持 resolveDefaultChatId，不臆造账号作用域 -->
- [ ] 5.3 回归断言：新增发送点不得内联 `resolveDefaultChatId` / `getDefaultChat` / `FEISHU_CHAT_ID`（本 change 的核心反模式）。 <!-- 未做：本仓无 lint 规则载体；改以 spec 场景「新增卡类型不得内联自建解析」+ chat-target.ts 注释红线约束 -->

## 6. 验证与交付

- [x] 6.1 `npm run test:acceptance`（`AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 必须全绿——本变更只改卡发到哪、不改谁能批） <!-- cloud 0963802 全绿（AC-PUB / AC-PROTO / AC-RISK 未受影响） -->
- [x] 6.2 `npm test` 全量 <!-- cloud 0963802 2319 tests / 0 fail -->
- [x] 6.3 `npm run typecheck` <!-- cloud 0963802 通过 -->
- [x] 6.4 `scripts/land-change aidcp-cloud unify-card-routing-origin-then-team` → 部署 dev（安全序列见 CLAUDE.md §5） <!-- cloud 0963802 2026-07-16 deployed dev；备份 cloud.bak.20260716-204532.tar.gz；healthcheck 绿（active / 8787 LISTEN / PG select 1 / 边缘连接与角色派发正常）；isales 未碰。**偏离**：rsync 误加 `--delete`（§5 未授权），事后核实净损失为零（`.env` 在排除列表内未损，部署前 tar 内 `.env*` 仅 `.env` 一个＝当时无历史备份可删，唯一被删的是本次自建的冗余 `.env.bak.20260716`；服务跑 `npx tsx src/server.ts` 不依赖 dist）。已向用户报备。 -->
- [x] 6.5 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（私聊 `/comment` 两卡回私聊 / 自动化审批卡进 Tom.A / 未绑团队回默认群 / 自动发帖审批卡进团队群） <!-- 簇 86.26–86.33；同时更正 86.18（本 change 已做掉）与 86.17（其「审批卡仍走默认审批群」子句已被推翻，按旧口径验收会误判回归） -->
- [x] 6.6 `openspec validate unify-card-routing-origin-then-team --strict` → archive <!-- dev 线上实证：账号 61591565169600（无 group_label）的验证码告警回落默认群＝补集链生产可用；Dennis Scott 61591701813509 属 tom → oc_1c268549…（Tom.A），即报障账号的自动化卡将进团队群 -->
