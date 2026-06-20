# Tasks — aidcp-console-panel-mvp

> 分 **MVP（首个可上线切片）** 与 **V1（归因落地后的按账号能力）** 两期；按 sub-repo 分节。
> 回写格式：完成用 `[x]` + `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
> 红线见 design.md 的 D1–D12 与 proposal.md「风险面 / 红线」。

## 1. aidcp-cloud — MVP：面板 API 层骨架 + JWT（console-panel-api）

- [x] 1.1 新 `src/panel/` 模块：极小 switch 路由（**不引入 Web 框架**）；绑 `AIDCP_PANEL_PORT`；启动自检记录解析端口、拒绝绑 `8787/5432/8788` + env 补充的 isales（D1）<!-- aidcp-cloud 3752240 偏离：用独立 http.Server 绑 AIDCP_PANEL_PORT，而非"复用 8787 的 http.Server"——8787 是 ws-server 的 {port} 模式、未暴露 server 对象，独立更干净且符合"独立端口"意图；保留端口经 forbiddenPorts 配置 -->
- [x] 1.2 `listen()` 非致命：`EADDRINUSE`/初始化错误记日志并返回 `started=false`，保 `8787` 边缘闭环 + 飞书核心继续跑，绝不崩 `main()`（D2）<!-- aidcp-cloud 3752240 server.once('error') 捕获，resolve started=false；server.ts 外层再包 try/catch -->
- [x] 1.3 注入单例（`publishLogStore`/`conceptStore`/`botChatStore`/`EventBus`/`edgeServer`/`riskController`）入面板模块，镜像 `DefaultMessageHandler` 构造；纯读侧组合 + 薄命令外观，不碰 `protocol.ts`/`command-bridge`（D2）<!-- aidcp-cloud 3752240 PanelDeps 注入 6 单例；/api/dashboard/summary 骨架读 edgeServer.edgeCount() 证明链路打通 -->
- [x] 1.4 JWT：`POST /api/auth/login` 对 `.env` 内置用户签短 TTL JWT；`/api/*`（除登录/health/version）走校验中间件；密钥 `.env`<!-- aidcp-cloud 3752240 HS256 自实现(node:crypto)：强制 alg、timingSafeEqual、校验 exp；凭据 AIDCP_PANEL_USERS 明文 env + 定长比对（生产可升级 hash） -->
- [x] 1.5 验收/单测：面板端口冲突非致命；JWT 缺失/过期/篡改/alg 返 401；自检拒绝保留端口<!-- aidcp-cloud 3752240 panel-jwt(6)+panel-auth(6)+panel-server(5)=17/17；risk 回归 27/27；typecheck 在干净 HEAD 上零错误 -->

## 2. aidcp-cloud — MVP：账号主数据 + 暂停态持久（accounts-master-data 步骤 1–2）

- [x] 2.1 `accounts` 表 migration，**seed 一个 `account_id='default'` 行**对齐字面量（`account_id` PK + `label`/`platform`/`persona_ref`/`quota_level`/`status`/`paused_at`/`machine_label`/`group_label`/`created_at`）（重构步骤 1）<!-- aidcp-cloud ac3d0c2 src/account-store.ts ACCOUNTS_SCHEMA_SQL 幂等建表 + INSERT default ON CONFLICT DO NOTHING；status/quota_level 带 CHECK 约束 -->
- [x] 2.2 运营暂停态持久进 `accounts.status`/`paused_at`，折叠非持久 `AccountStateManager`；**去掉「未知账号默认 active」回退**（`account-state.ts`）；与传输层 `pausedEdges` 区分（重构步骤 2）<!-- aidcp-cloud ac3d0c2 AccountStateManager store-backed：同步缓存(热路径 isPaused/getStatus)+异步持久化(pause/resume)+启动加载(init)。"去默认 active 回退"落地=暂停态持久化+启动加载使被暂停账号不复活，缓存 miss(从未注册)视为 active。偏离/顺带：统一账号 id 字面量 acc-default→default(feishu/commands + handler 热路径)，对齐风控/accounts seed，否则持久化的暂停账号与表 seed 行是两个账号 -->
- [x] 2.3 迁移/验收测试：被暂停账号跨 cloud 重启仍为 `paused`，不静默复活<!-- aidcp-cloud ac3d0c2 account-state.test.ts 用内存 AccountStore 模拟重启(新 manager load 同 store)断言仍 paused；account-store.test.ts 断言 DDL；全量 typecheck 干净、handler/feishu/panel/risk 回归全过 -->

## 3. aidcp-cloud — MVP：归因修复 accountId（interaction-attribution 步骤 3）

- [ ] 3.1 给 `interaction.occurred` 的 EventMap 条目加 `accountId`，在发射点（`handler.ts:203`）从 `session.accountId` 填——**云内类型改动、不碰 `protocol.ts`**（D3，重构步骤 3）
- [ ] 3.2 undefined-accountId 显式回退：路由到保留键 `default` **并**在投影标 `unattributed`；不抛错、不静默并入真名账号（D4）
- [ ] 3.3 验收测试：缺 `accountId` 的事件被标 `unattributed` 而非误并；面板按账号切片在归因流通前标「全部账号 / 归因待补」

## 4. aidcp-cloud — MVP：写操作（审批 first-writer-wins + 账号命令）（console-write-operations 部分）

- [ ] 4.1 从 `feishu/ws-receiver.ts` 抽唯一 `writeApprovalSignal(requestId, approved, payload)`：写逐字节一致 `/tmp/aidcp-publish-approve-<requestId>.json`；**first-writer-wins**（temp+rename / `O_EXCL`）；返回 `{written}`/`{alreadyDecided}`，**绝不 `{published}`**（D8）
- [ ] 4.2 飞书卡处理器与 `POST /api/publish/:requestId/approve` 共用 4.1，用同一 `requestId`；**不接** `publish-executor.ts:148` 那条缺 `requestId` 的孤儿分支（D8）
- [ ] 4.3 抽共享 `CommandActions`（pause/resume）：飞书命令路由与 `POST /api/accounts/:id/command` 共用；durable 经 `accounts.status`、与 `pausedEdges` 区分；回报真实下发边缘数（绝不乐观）
- [ ] 4.4 验收：审批 first-writer-wins（二次决定返 `alreadyDecided` 不覆盖）；审批返 `written` 非 `published`；暂停回报真实下发事实

## 5. aidcp-cloud — MVP：只读接口 + 面板 WS + edge 心跳（console-panel-api 部分）

- [ ] 5.1 只读接口（全部走索引点查/范围查询、非阻塞）：`GET /api/version`（含 live enum 值）、`/api/dashboard/summary`、`/api/accounts(+/:id)`、`/api/content/queue`、`/api/content/published`、`/api/analytics/like-rate`
- [ ] 5.2 面板 WS：一个通配处理器订阅事件总线，过滤面板事件、归一化为 `docs/product-dashboard.md §2.3` 帧，**单一全局流 + 客户端过滤**；纯只读扇出、绝不碰 edge；JWT（query/首帧）（红线：边-云隔离）
- [ ] 5.3 edge 心跳：在已有 `ping`/`pong`（`protocol.ts:74`）之上加主动探活定时器 + 每入站帧戳 `last_seen`；`online = inMap AND (now-last_seen < N×interval)`（D9）——**云内、不碰协议**
- [x] 5.4 `/api/version` 暴露 live 风控状态/档位/告警分级枚举，作 console 漂移哨兵（D11）<!-- aidcp-cloud 3752240 task 1 顺带完成：暴露 RISK_STATUSES/RISK_QUOTA_LEVELS/RISK_ACTIONS（types.ts 补 runtime const 单源）；告警分级枚举待 V1 alerts 落地补 -->

## 6. aidcp-console（新仓 ../aidcp-console）— MVP：骨架 + 只读页 + 两个写

- [ ] 6.1 脚手架独立 Vite+React+TS 仓 `../aidcp-console`：`src/{api,pages,components,types,auth,ws}`；react-router；AntD；TanStack Query；`echarts-for-react`
- [ ] 6.2 committed `src/types/aidcp-enums.ts`（`RiskStatus`/`RiskQuotaLevel`/`RISK_ACTIONS`）+ 一个对 live `/api/version` 断言的漂移测试（D11）
- [ ] 6.3 鉴权：登录页 → `POST /api/auth/login`；token 优先**同站 httpOnly cookie**（面板 Nginx-public 且有写权限）而非 localStorage；fetch 拦截器挂 Bearer；401 → 登录（design 开放问题：JWT 存储）
- [ ] 6.4 TanStack Query 管所有 `/api` 读；独立 panel-WS 客户端喂 live 日志/告警流 → `invalidateQueries`/`setQueryData`
- [ ] 6.5 页面镜像 `docs/product-dashboard.md §1`（Dashboard/Accounts/Content）+ 顶层布局 + 全局账号筛选器；`status` 与 `quota_level` 渲染为**两个独立徽标**
- [ ] 6.6 写：发布审批 approve/reject + 账号 pause/resume——**绝不乐观更新**、永远 round-trip；诚实渲染 `{written}`/`{alreadyDecided}`、「已记录、0 个在线 edge」、原因说明（D10）

## 7. aidcp[deploy] — MVP：ECS 部署（安全序列 + 红线盘点）

- [ ] 7.1 ECS 红线盘点：`ss -ltnp` + 查现有 nginx sites；确认 `AIDCP_PANEL_PORT` 空闲 vs `8787/5432/8788/isales`；据盘点把最终端口写入 `.env`（D12，design 开放问题）
- [ ] 7.2 Nginx：**给现有安装加 server block**（不另起 Nginx）；serve `/opt/aidcp/console` 的 `dist`（SPA `try_files` fallback）；反代 `/api` 与 `/ws`(panel) 到 `127.0.0.1:AIDCP_PANEL_PORT`；**不暴露 8787**
- [ ] 7.3 `vite build` → rsync `dist/` 到 `/opt/aidcp/console`（**非** cloud 目录）
- [ ] 7.4 cloud 按 CLAUDE.md §5 安全序列部署：备份（`cloud.bak.<ts>.tar.gz` + `.env.bak`）→ rsync（`--exclude .env/node_modules/.git`）→ `systemctl restart aidcp-cloud.service`
- [ ] 7.5 Healthcheck：`active(running)` + 8787 监听 + 飞书长连 + PG `select 1` + **新面板端口监听** + **isales 仍在**；任一失败回滚
- [ ] 7.6 本仓回写：三仓关系文档（CLAUDE.md §1）补 `aidcp-console`；`docs/product-dashboard.md` 实现进度；如需新 edge 数据另起协议 change

## 8. aidcp-cloud — V1：风控写（串行化 + setQuotaLevel + 枚举信号）（console-write-operations 部分）

- [ ] 8.1 `RiskController` 加每账号 async mutation 队列，环绕「迁移+saveState」「setQuotaLevel+saveState」原子；**所有**写者（live `record()`、验证码协调器、Web 写）经它；验收：并发 manual + `quota_exceeded` 无丢更新（D7，重构步骤 4）
- [ ] 8.2 枚举化运营信号种类入 `RiskSignalKind` + `nextStatus` 分支：`manual_restrict`、`manual_freeze`、`operator_override_recover`（**需审计理由**、显式绕过恢复窗口）（D6，design 开放问题）
- [ ] 8.3 新 `RiskController.setQuotaLevel(level)`：改+持久（`saveState`）+emit；单写；经 mutation 队列（D5）
- [ ] 8.4 `POST /api/accounts/:id/risk/status`（`applySignal`、枚举种类、`getState()` 写回、拒绝可辨）+ `/risk/quota`（`setQuotaLevel`、写回）

## 9. aidcp-cloud — V1：Registry + noteId + monitor/alerts + per-edge dispatcher

- [ ] 9.1 `RiskControllerRegistry`（`Map<accountId, RiskController>` 懒加载）+ `listStates()`；按 `accountId` 路由 `interaction.occurred`（重构步骤 5）
- [ ] 9.2 在发射点填充已声明的 `noteId`；接线孤儿 `risk_interactions` 入互动完成路径；`GET /api/monitor/interactions`（重构步骤 6）
- [ ] 9.3 `ALTER publish_log + concepts ADD COLUMN account_id TEXT NOT NULL DEFAULT 'default'`；概念查询保持账号无关（重构步骤 7）
- [ ] 9.4 每边缘/账号 dispatcher 按 `account→machine` 映射（**非** god-object）；`POST /api/accounts/:id/dispatch {start|stop}` 回报真实 edge-online 事实（重构步骤 8）
- [ ] 9.5 `alerts` 表在飞书卡发送点写入（复用 P0–P3 枚举）；验证码清除点 set `resolved_at`；`GET /api/alerts`
- [ ] 9.6 移除按账号切片的「归因待补」标，上真按账号数字

## 10. aidcp-console — V1：风控控件 + dispatch + monitor/alerts 页

- [ ] 10.1 风控 STATUS 控件（枚举迁移）+ QUOTA-TIER 控件为**两个独立控件**接两个端点；「refused」与成功可辨；override 标特权/记录
- [ ] 10.2 dispatch 启停控件，回报真实 edge-online 事实
- [ ] 10.3 Monitor 页：按笔记互动；Alerts 只读流；真按账号总览切片
