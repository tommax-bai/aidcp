## Context

现状（监查 + 设计 workflow 已坐实，带 file:line）：

- 云端**无 Web 框架**（依赖只有 `ws` / `pg` / `@larksuiteoapi`）。唯一 HTTP 是 `127.0.0.1:8788` 调试桩（`src/server.ts:285`，`TODO temp`，将被 `activate-publish-pipeline` 删）；唯一 WebSocket 是边-云协议 `:8787`（`src/comm/ws-server.ts`）。无 `/api/*`、无 panel-WS、无前端。
- **已持久化、可直接喂面板**：每账号风控状态+档位（`risk_state`，单写经 `RiskController` 状态机，`pg-risk-store.ts`；只按 PK 点查、无 list）；按笔记互动去重（`risk_interactions`，但**从未在 live 路径实例化**，孤儿表）；发布历史+回执（`publish_log`）；概念池（`concept-store`）。
- **只在内存、重启即丢**：账号暂停态（`account-state.ts`，显式非持久，且**未知账号默认 active**）；在线边缘登记（`ws-server.ts` 的 `Map<sessionId>`，只暴露 `edgeCount()`）；在途发布（`publish-orchestrator.ts` 单槽）。
- **完全无数据**：账号/人设/分组主数据（系统跑**一个硬编码 `default` 账号**，`server.ts:158`；人设是单份静态 YAML 非按账号）；告警日志（P0–P3 只 bump `risk_state.signalCount` + 临时飞书卡）；涨粉时序（作者粉丝数取完即丢）；会话统计（`event-bus/types.ts` 定义但从不发射）。
- **归因缺口**：`interaction.occurred` 发射时只带 `{action}`、无 `accountId`；点赞/收藏在计数层无 `noteId`（`handler.ts:203`）；且一切跑在 `accountId='default'` 下——任何聚合都是**全局**，不补归因就做不出诚实的「按账号」。
- **飞书伴侣 live**：审批回写经信号文件 `/tmp/aidcp-publish-approve-<requestId>.json`（`getApprovalSignalPath` ↔ edge `buildPublishApprovalSignalPath`，AC-PUB-*）；群绑定（`bot_chats`）；验证码 P0/P1 卡。`publish-executor.ts:148` 那条审批卡**缺 `requestId`**、属未激活的 `activate-publish-pipeline`，**不接**。
- **协议已有 `ping`/`pong`**（`protocol.ts:74`、`handler.ts:130`，被动回应），但**无主动探活 / 无 `last_seen` / 无 staleness 判定**。

技术选型由契约 `docs/product-dashboard.md §3` 固定：React+Vite+TS、AntD、ECharts/Recharts、浏览器↔云 WebSocket、TanStack Query、JWT、Nginx 反代静态 + `/api`；后端 = 进程内面板 API 层，不引入新后端。

## Goals / Non-Goals

**Goals：** 基于现有接口与数据，端到端上线一个内部管理后台（只读总览 + 实时日志流 + 两类不需重构的写：发布审批、账号暂停/恢复），并为「按账号写」铺好诚实地基（账号主表 + 暂停态持久 + `accountId` 归因）；务实最小、留干净扩展缝；不触碰运行中的边缘浏览闭环；不破坏任何红线。

**Non-Goals（YAGNI，明确不做）：** Web 框架（用现有 `http.Server` + 小路由）；持久 `edge_bindings` 表（`account→machine` 近静态、放账号表）；涨粉采样表 + 定时采集器 + 新 edge 自身粉丝数能力（今天无数据源）；分组/团队层级（一个可空 `group_label` 列足够）；人设表/Web 人设编辑器（人设留版本控制 YAML，`persona_ref` 指文件）；计数器物化视图/rollup（日增千行级，窗口 GROUP BY 够）；告警三态 `pending|ack|resolved` 工作流（V1 先扁平 append-only + 验证码清除点 set `resolved_at`）；双仓 enum 快照测试（改为单仓对 `/api/version` 断言）；契约 npm 包/codegen/GraphQL/OpenAPI（DTO 数 <15）；乐观更新 / per-account WS 房间 / 订阅协议 / 连接时历史回放（单一全局流 + 客户端过滤）；接受/未生效写的 saga 追踪器（轮询既有投影）；RBAC / 按组数据域 / 设置权限页 / 操作审计 / 飞书 SSO（V3）；`qualityIndex` / 平台侧内容表现（无源，V2+ 采集项目）；会话计数发射管线（定义未发射，后续小切片）；Docker/蓝绿/CDN（回滚 = 换静态目录 + restart）；不接 `activate-publish-pipeline` 的孤儿审批分支。

## Decisions

### D1 后端 HTTP 框架：不引入框架，复用 `http.Server` + 小路由
~12–15 个内部工具路由、两个简单写体（`{action}`、`{approved}`），用几行 `typeof` 校验即可。新 `src/panel/` 模块用注入拿到 `main()` 已接好的单例（风控注册表、`publishLogStore`、`conceptStore`、`botChatStore`、`EventBus`、`EdgeCloudServer`、账号存储），镜像 `DefaultMessageHandler` 的构造方式。**拒绝**：Fastify / Express（为两个端点引入 schema 校验器是未挣得的表面积）、GraphQL/OpenAPI codegen（远超规模）。

### D2 面板 API 层挂载位置：消息处理器之上的进程内 BFF
云端是单长驻进程、持有 live 内存态（edge Map、在途发布槽），面板必须**住在进程内**才能读到这些活态与事件总线 firehose；分离的微服务看不见内存态、且违背「不引入新后端」契约。面板是纯读侧组合器 + 薄命令外观，**绝不触碰 `protocol.ts` 与 `command-bridge`**。

### D3 归因缺口：上游修复，分期且诚实标注
`accountId` 加到 `interaction.occurred` 的 EventMap 条目、在发射点从 `session.accountId` 填入——`accountId` 已经过 `HelloPayload` 到达，**这是云内类型改动、不是协议改动**。`noteId` 是 `interaction.occurred` 上**已声明的可选字段**（`event-bus/types.ts:123`），只需在发射点填。在 `accountId` 流通前，按账号面板切片**不展示**或标「全部账号 / 归因待补」，绝不显示为按行的按账号数字（否则即静默假成功）。

### D4 undefined-accountId 回退契约
`accountId` 端到端可选（`protocol.ts:99`、`ws-server.ts:29`）。显式定义缺失契约：路由到保留键 `default` **并**在投影里把该流量标 `unattributed`；**绝不**静默并入某个真名账号。**拒绝**：缺 `accountId` 抛错（会打断 legacy edge 的 live 路径）、静默并入第一个真账号（静默误归因）。

### D5 `status` 与 `quotaLevel` 是两个独立写
`RiskState` 有两个独立字段 `status` 与 `quotaLevel`（`types.ts:9,17`）；状态机**只**改 `status`、**从不**碰 `quotaLevel`（`risk-state-machine.ts`），后者只在构造时设。故拆成两个显式命名操作：(a) STATUS 经 `RiskController.applySignal`（约束图、返回 `getState()` 写回、拒绝可辨）；(b) QUOTA-TIER 经**新** `RiskController.setQuotaLevel(level)`（改+持久 `saveState`+emit，controller 仍是唯一写者）。**拒绝**：用 `applySignal` 改档位（它根本改不了 `quotaLevel`，会静默无事发生）、面板 raw UPDATE `quotaLevel`（破坏单写）。

### D6 运营可执行的 status 迁移：枚举化命名信号种类
状态机是约束图非 setter——恢复是时间门控的（`recoverIfEligible` 在恢复窗口内拒绝，`risk-state-machine.ts:33`），且没有 `restricted→normal` / `normal→restricted` 的种类。API **只**接受枚举的运营信号种类：在现有种类基础上加 `manual_restrict`（normal/warned→restricted）、`manual_freeze`（any→frozen）、`operator_override_recover`（绕过恢复窗口、**需审计理由**）。每个写返回 `getState()` 写回，使时间门控拒绝渲染为「refused」而非「ok」。**拒绝**：通用「set 任意 status」（多数目标不可表达、会静默 no-op）、无审计理由的恢复覆盖（静默削弱恢复窗口安全）。

### D7 每账号写串行化（mutation queue）
`applySignal` 是对 `this.state` 的 read-modify-write，mutate 与 `saveState` 间有 `await`、无锁（`risk-controller.ts:83`）。面板给同一进程内 controller 加了**第三个**并发写者；last `saveState` wins，手动覆盖与 live `quota_exceeded` 互相覆盖。给 `RiskController` 加每账号 async mutation queue（promise 链/async-mutex），让 transition+saveState、setQuotaLevel+saveState 原子；**所有**写者（live `record()`、验证码协调器、新 Web 写）都经它。验收：并发 manual + `quota_exceeded` 断言合法串行组合（无丢更新）。「单写 OBJECT」≠「单线程写」。

### D8 发布审批写回：唯一共享函数 + first-writer-wins
从 `feishu/ws-receiver.ts` 抽出唯一 `writeApprovalSignal(requestId, approved, payload)`，写**逐字节一致**的 `/tmp/aidcp-publish-approve-<requestId>.json`（AC-PUB-*）；飞书卡处理器与 Web 端点用**同一个** `requestId`（卡铸造时的那个）调它。**first-writer-wins**：原子写（temp + rename，`O_EXCL`/`wx`），第二个决定（Web vs 飞书 vs 重复点击）快速失败，API 返回 `{alreadyDecided:<approved>}`（真结果）。API 返回 `{written:true}` 或 `{alreadyDecided}`，**绝不** `{published:true}`——edge 对文件的动作才是真相。**拒绝**：接 `publish-executor.ts:148`（缺 `requestId`、属未激活管线）、last-write-wins 普通 `writeFile`（陈旧二次点击静默翻转决定）。

### D9 edge online：live Map AND staleness，绝不只看 Map 成员
协议已有 `ping`/`pong` 但只被动回应。加主动探活（ws ping/pong 或协议心跳）+ 每入站帧戳 `last_seen`；`online = inMap AND (now-last_seen < N×heartbeat)`。进程未发关闭帧就死会留下陈旧 Map 项——「还在 Map 里 = online」正是要防的「陈旧权威连接」失败模式。**拒绝**：Map 成员即 online（非优雅断连时陈旧）、持久一个权威 connected 标志（进程无关闭帧死时重造静默假成功）。

### D10 前端仓形态 + 写不乐观
独立单 app 仓 `../aidcp-console`（第 4 仓）。栈由契约固定：AntD + `echarts-for-react` + TanStack Query + react-router。TanStack Query 管所有 `/api` 读**与**写 mutation；独立 panel-WS 客户端喂 live 日志/告警流并 `invalidateQueries`/`setQueryData`。**审批/status/tier 写绝不乐观更新**——永远 round-trip 云端真态。`status`（normal/warned/restricted/frozen）与 `quotaLevel`（conservative/normal/aggressive）渲染为**两个独立徽标/控件**接两个端点。**拒绝**：Nx/Turborepo monorepo（此规模纯仪式）、Redux/Zustand（TanStack Query 即 store）、写乐观更新（在最高危写上静默假成功）。

### D11 enum 漂移防护：单仓对 `/api/version` 断言
console 内 committed `src/types/aidcp-enums.ts`（`RiskStatus`/`RiskQuotaLevel`/`RISK_ACTIONS` 镜像 cloud `src/risk/types.ts`）；`/api/version` 也暴露 live enum 值；一个 console 端测试断言 committed 文件对 live `/api/version` 响应。无 cloud 侧测试义务。徽标/档位/告警分级必须与 `risk-control §7`、`product-exception §1` 同一套枚举，避免三处漂移。**拒绝**：双仓快照测试（跨仓测试耦合）、契约 npm 包/codegen（<15 DTO 过早）。

### D12 ECS 部署隔离
面板 API 随常规 cloud 部署（住进程内）。`vite build → dist/` rsync 到 `/opt/aidcp/console`（**非** cloud 目录）。Nginx **给现有安装加 server block**（不另起 Nginx）serve `dist/`（SPA `try_files` fallback）、反代 `/api` 与 `/ws`(panel) 到 `127.0.0.1:AIDCP_PANEL_PORT`、**不反代/暴露 8787**。面板 `listen()` 包 try/catch：`EADDRINUSE` 或任何面板初始化错误**记日志并继续跑** `8787` 边缘闭环 + 飞书核心、绝不崩 `main()`。启动自检记录解析端口、拒绝绑 `8787/5432/8788/已知 isales`。**红线盘点先行**：绑端口或 80/443 前先在 live host 跑 `ss -ltnp` + 查现有 nginx sites；若 isales 拥有 Nginx，**加 server block**、不另起第二个 Nginx。`8090` 是占位、待 live 盘点定。**拒绝**：硬编码端口不盘点、让 `listen()` 抛未捕获（崩关键闭环）、另起第二 Nginx、Docker/蓝绿/CDN。

## Multi-Account Refactor（有序、最小、浏览闭环安全）

1. **新 `accounts` 表 seed 一个 `default` 行**（MVP）——零行为变化，对运行闭环不可见。
2. **运营暂停态持久进 `accounts.status`/`paused_at`**（MVP）——折叠非持久的 `AccountStateManager`；**去掉「未知账号默认 active」回退**（否则被暂停账号重启静默复活）；与传输层 `pausedEdges`（验证码门控）保持区分；迁移测试断言「暂停跨重启存活」。
3. **`accountId` 上 `interaction.occurred`**（MVP）——云内事件，从 `session.accountId` 填；undefined 回退标 `unattributed`。
4. **每账号写串行化**（V1）——任何 Web 风控写的前置；mutation queue。
5. **`RiskControllerRegistry` + `listStates()`**（V1）——按账号路由 `interaction.occurred`；单写**按账号**保持。
6. **`noteId` 填充 + 接线孤儿 `risk_interactions`**（V1）——`noteId` 已声明字段，trivial 填。
7. **`ALTER publish_log + concepts ADD account_id DEFAULT 'default'`**（V1）——additive、自动回填；概念查询保持账号无关直到隔离搜索记忆成真需求。
8. **每边缘/账号 dispatcher**（V1）——按 `account→machine` 映射，一边缘一 dispatcher，**非** god-object（否则跨账号泄漏 `currentNote`/上下文）；运行中的单账号闭环在此落地前不被触碰。

## Phasing

- **MVP（首个可上线切片）**：D1/D2 面板层 + JWT；D3 的 `accountId` 上事件 + D4 回退；账号主表 seed default + 暂停态持久（重构步骤 1–3）；只读接口 + panel-WS 单一全局流；D8 审批 first-writer-wins + D9 edge 心跳 + pause/resume command；console 骨架 + 只读页 + 两个写（审批、暂停/恢复）；ECS 部署（红线盘点 + Nginx server block + 安全序列）。按账号切片此期标「归因待补」。
- **V1**：D5/D6/D7 风控写（串行化 + `setQuotaLevel` + 枚举信号）；重构步骤 4–8；`noteId` + monitor/alerts + per-edge dispatcher；console 风控控件 + dispatch + monitor/alerts；移除「归因待补」标、上真按账号切片。
- **V2/V3（本 change 外）**：涨粉/内容表现采集（需新数据源）、告警规则自定义、RBAC/审计、回放分析。

## Open Questions

- **`operator_override_recover`**（绕过恢复窗口的特权强制降级、需审计理由）：确认 V1 该存在，还是「降到 normal」严格保持时间门控。涉及恢复窗口安全语义，落地 V1 前定。
- **JWT 存储**：面板 Nginx-public 且有写权限，推荐**同站 httpOnly cookie**（优于 localStorage）；in-memory（刷新即重登）为更保守备选。实现时定，倾向 cookie。
- **`AIDCP_PANEL_PORT` 最终值**：必须来自 live ECS `ss -ltnp` 盘点（`8090` 占位）；部署 task 内现场定，不阻塞立项。
