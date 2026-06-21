## Why

给 AIDCP 加一个**内部运营管理后台**（统一 Web 控制台 / 多账号管理面板），承接运营对系统的人入口。上一轮监查坐实：契约 `docs/product-dashboard.md` 已是一份完整设计，但云端**零实现**——没有 Web 框架（依赖只有 `ws` / `pg` / `@larksuiteoapi`），没有任何 `/api/*` 路由，没有面向浏览器的实时通道，没有前端仓；唯一的 HTTP 是一个将被 `activate-publish-pipeline` 删除的 `127.0.0.1` 调试桩，唯一的 WebSocket 是边-云协议 `:8787`。今天运营对系统的人入口实际只落在飞书。

用户决策（本 change 的范围基线）：**一路到 ECS 部署**；**首版含写操作**（从 Web 手动改风控状态/档位 + 发布审批）；前端**新开独立仓 `aidcp-console`**（第 4 个仓）。

「含写操作」隐含一次**多账号重构**：今天系统只跑一个硬编码 `default` 账号（`aidcp-cloud/src/server.ts:158`、`risk-controller.ts:32`），没有账号主数据。要让「按账号写」诚实，必须先有真账号表、把运营暂停态持久化、并在云端内部事件上补 `accountId` 归因——否则面板会把全局数字冒充成「按账号」，违反「绝不静默假成功」红线。诚实的关键路径不是 UI，而是多账号管线与归因修复；本 change 把它们排在前面，且保证**运行中的边缘浏览闭环全程不被触碰**。

设计走「业界方案」四步法（现状坐实 → 业界模式 → 综合设计 → 对抗评审，见 design.md；分析详见 2026-06-19 design workflow）。对抗评审已纠正若干要害：风控 `status` 与 `quotaLevel` 是两个独立字段、写操作必须串行化、审批必须 first-writer-wins、edge online 必须查 staleness、`accountId` 已在协议线上无需改协议。

## What Changes

按 **MVP → V1** 两期推进；首版（MVP）即可上线、含两类不需要多账号重构与事件改造的写操作（发布审批、账号暂停/恢复）；按账号的风控写与按账号聚合放在 V1（归因修复落地后），避免把全局数字标成按账号。

**MVP（首个可上线切片）**

- **cloud / 面板 API 层（新）**：在现有进程内新增 `src/panel/` 模块，复用为 ws 升级而建的 `http.Server` + 一个极小的 switch 路由（**不引入 Web 框架**）；绑定独立端口 `AIDCP_PANEL_PORT`；启动自检拒绝绑定 `8787/5432/8788/已知 isales` 端口；`listen()` 失败（端口占用/初始化错误）**非致命**——记日志并保持 `8787` 边缘闭环 + 飞书核心继续跑，绝不让 `main()` 崩溃。
- **cloud / JWT 鉴权（新）**：`POST /api/auth/login` 对 `.env` 内置用户签发短 TTL JWT；`/api/*`（除登录外）走校验中间件；密钥在 `.env`。
- **cloud / 只读聚合接口（新）**：`/api/version`（含 live enum 值）、`/api/dashboard/summary`、`/api/accounts(+/:id)`、`/api/content/queue`、`/api/content/published`、`/api/analytics/like-rate`——全部走已有索引的点查/范围查询，**不阻塞事件循环**；组合现有存储（风控状态 / 计数器 / 发布记录）+ 进程内活态（在线边缘 Map、在途发布槽）。
- **cloud / 面板 WebSocket（新）**：一个通配处理器订阅进程内事件总线，过滤为面板事件、归一化为 `docs/product-dashboard.md §2.3` 帧，**单一全局流 + 客户端过滤**；纯只读扇出，**绝不与 edge 通信**、与 `:8787` 物理隔离。
- **cloud / 账号主数据（新，多账号重构第一步）**：新建 `accounts` 主表，**先 seed 一个 `account_id='default'` 行**与现有字面量对齐，使 `risk_state`/`risk_counters`/`risk_interactions`（已按账号 keyed）瞬间有父行；表上持久化运营暂停态（折叠掉非持久的 `AccountStateManager`，**去掉「未知账号默认 active」回退**，使被暂停账号重启不静默复活）、`persona_ref`、`quota_level`、`account→machine` 映射。
- **cloud / 归因修复（accountId，云内事件，不碰协议）**：给 `interaction.occurred` 事件加 `accountId`，在发射点从 `session.accountId` 填入（`accountId` 已经过 `HelloPayload` 到达，**不是协议改动**）；定义 undefined-accountId 显式回退——路由到保留键 `default` 并在投影里标 `unattributed`，绝不静默并入某个真名账号。
- **cloud / 发布审批写（Web，共享飞书契约）**：从 `feishu/ws-receiver.ts` 抽出唯一的 `writeApprovalSignal(requestId, approved, payload)`，写**逐字节一致**的 `/tmp/aidcp-publish-approve-<requestId>.json`（AC-PUB-*），**first-writer-wins**（`O_EXCL`/rename）；飞书卡处理器与 `POST /api/publish/:requestId/approve` 都调它；返回 `{written}`/`{alreadyDecided}`，**绝不返回 `{published}`**；明确**不**接 `publish-executor.ts` 那条缺 `requestId`、属未激活管线的分支。
- **cloud / 账号命令写（pause/resume）**：抽出共享 `CommandActions` 闭包，飞书 `CommandRouter` 与 `POST /api/accounts/:id/command` 共用；durable 经 `accounts.status`，与传输层 `pausedEdges`（验证码硬停）区分；回报真实「下发到几个 edge」事实。
- **cloud / edge 心跳（在已有 ping/pong 之上）**：协议已有 `ping`/`pong` 消息（`protocol.ts:74`、`handler.ts:130`，被动回应），但无主动探活/时间戳。加主动探活定时器 + 每帧 `last_seen` 戳；`online = inMap AND (now-last_seen < N×interval)`，绝不把「还在 Map 里」当 online。**云端内部，不碰协议。**
- **console / 前端仓骨架（新仓 `../aidcp-console`）**：Vite+React+TS+AntD+ECharts(echarts-for-react)+TanStack Query+react-router；登录页 → JWT；TanStack Query 管所有读 + 写 mutation；独立 panel-WS 客户端喂实时日志/告警流并 invalidate 查询；committed `src/types/aidcp-enums.ts` + 一个对 `/api/version` 断言的漂移测试；**写操作绝不乐观更新**，永远 round-trip 真态；`status` 与 `quota_level` 渲染为**两个独立徽标**。
- **deploy / ECS（安全序列）**：先做红线盘点（`ss -ltnp` + 现有 nginx sites），确认端口空闲、**给现有 Nginx 加 server block**（不另起 Nginx）、serve `/opt/aidcp/console` 静态（SPA fallback）、反代 `/api` 与 `/ws`(panel) 到 `127.0.0.1:AIDCP_PANEL_PORT`、**不暴露 8787**；cloud 按 CLAUDE.md §5 安全序列（备份 → rsync → restart → healthcheck → 失败回滚），**绝不碰同机 isales**。

**V1（归因落地后的按账号能力）**

- **cloud**：风控写串行化（每账号 async mutation queue，所有写者经它，无丢更新）；枚举化运营信号种类（`manual_restrict`/`manual_freeze`/`operator_override_recover`，后者需审计理由、显式绕过恢复窗口）；新 `RiskController.setQuotaLevel()`（单写改档位，状态机从不碰 `quotaLevel`）；`RiskControllerRegistry`（每账号一个 controller + `listStates()`）；填充已声明的 `noteId` + 接线孤儿 `risk_interactions`；`ALTER publish_log/concepts ADD account_id DEFAULT 'default'`；按 `account→machine` 映射的每边缘 dispatcher（非 god-object）；`alerts` 表在飞书卡发送点写入（复用 P0–P3 枚举）。
- **API**：`POST /api/accounts/:id/risk/status`、`/risk/quota`、`/dispatch`；`GET /api/monitor/interactions`、`/api/alerts`。
- **console**：风控 status/quota 两个独立控件（拒绝可辨）、dispatch 启停、Monitor 页（按笔记互动）、Alerts 只读流、真按账号切片。

## Capabilities

### New Capabilities

- `console-panel-api`：进程内面板 API 层（独立端口、无框架、JWT、非阻塞只读组合、纯只读 panel-WS 扇出、启动自检 + listen 失败非致命、enum 漂移哨兵）。
- `console-write-operations`：经拥有写的进程内对象做写、绝不 raw UPDATE、绝不乐观假成功（风控 status/quota 分写 + 每账号串行化、审批 first-writer-wins 共享契约、pause/resume/dispatch 回报真实结果）。
- `accounts-master-data`：真账号主表替换硬编码单账号、持久运营暂停态（去默认 active 回退）、每账号单写 Registry、`account_id` 隔离列；运营暂停态与传输层 `pausedEdges` 区分。
- `interaction-attribution`：云内 `interaction.occurred` 补 `accountId`（不碰协议）+ undefined 回退标 `unattributed`、填充 `noteId` + 接线去重表；归因落地前按账号切片必须 withheld 或标「attribution pending」。

## Impact

- **aidcp-cloud**：新 `src/panel/`（router + JWT + 路由 + panel-WS）；新 `accounts` 存储 + migration（seed default）；折叠 `src/account-state.ts` 入账号表（去默认 active 回退）；`src/comm/handler.ts`（emit 点补 `accountId`/`noteId`）；`src/comm/ws-server.ts`（心跳 + `last_seen` + staleness）；抽 `writeApprovalSignal`（`src/feishu/ws-receiver.ts`）与共享 `CommandActions`（`src/feishu/` 命令路由）；`src/server.ts`（注入面板模块、非致命 listen）。**V1**：`src/risk/risk-controller.ts`（mutation queue + `setQuotaLevel`）、`src/risk/risk-state-machine.ts`（枚举运营信号种类）、`RiskControllerRegistry`、`risk-interactions` 接线、`alerts` 表、per-edge dispatcher（`src/orchestrator/role-dispatcher.ts`）。
- **aidcp-console（新仓 `../aidcp-console`）**：整个前端 SPA + API 客户端 + panel-WS 客户端 + 共享 enum + 漂移测试。需在本仓三仓关系文档登记为第 4 个仓。
- **aidcp（本仓）**：`docs/product-dashboard.md` 实现进度回写；如未来需要新 edge 数据（如自身粉丝数采样），**另起协议 change**，不在本 change 静默加。三仓关系（CLAUDE.md §1）补 `aidcp-console`。
- **风险面 / 红线**：风控状态单写（status 经 `applySignal`、档位经新 `setQuotaLevel`，无 raw UPDATE，每账号串行化）；不静默假成功（写回真态、拒绝可辨、审批返 `written`/`alreadyDecided` 非 `published`、按账号聚合归因前不冒充）；边-云隔离（panel-WS 纯只读扇出、绝不碰 edge、与 `:8787` 物理隔离）；协议 v2 不被面板层触碰（`accountId` 已在线上、`noteId` 已声明字段）；飞书审批信号文件契约逐字节一致共享；ECS 独立端口 + 加 server block + listen 失败非致命 + 绝不碰 isales。
