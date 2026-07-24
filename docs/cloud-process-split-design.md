# Cloud 拆进程设计 · Block ②（Process Split）

> 2026-07-24。承接 Block ① 代码解耦（266→101，见 `cloud-decoupling-seam-inventory.md`）。三条设计决定已由用户拍板：**① api/panel 收口成数据网关；② 风控走异步事件；③ 保持三服务**。本文件是 Block② 的落地设计与分阶段执行计划。**全程跑在共享库上（Block③ 物理拆库仍 gated，不碰 ol 生产）。**

## 0. 现状地基（坐实）

- **组合根已按层分段**：`server.ts` 的 `main()` = `segAApiFoundation` → `segBContent` → `segCAutomation` → `segDApiServing`。**segA+segD → api 服务，segB → content 服务，segC → automation 服务**。入口天然可切。
- **监听面**：8787 边缘 WS（automation，边缘端 orchestration）、8090 panel API、8091 client-auth、飞书长连接。
- **传输基础设施**：EventBus 是**纯进程内** typed EventEmitter；**无** Redis/MQ；但已有 **`pg_notify` + 轮询兜底** 成熟模式（`config/mirror-version-store.ts`）。
- **DB 共享**：所有连接同一 PG（Block③ 前不变）。

## 1. 目标拓扑

三进程 + 一个共享包：

| 服务 | 层/段 | 职责 | 对外面 |
| --- | --- | --- | --- |
| **automation** | segC | 边缘 WS、浏览/互动闭环、RoleDispatcher、**风控单写**、EventBus | 8787（edge）+ 内部读 API |
| **content** | segB | 发布管线、洗稿、精选内容、配图 | 内部读/写 API |
| **api（面）** | segA+segD | panel 后端、client-auth、飞书 bot、**数据网关** | 8090/8091 + 飞书 |
| **@aidcp/kernel** | kernel（~44 文件） | 纯共享契约/类型/纯函数 | 三仓共享内部包 |

## 2. 传输选型（不引新中间件，共享库期即可用）

- **异步事件（决定②，风控 13 条 + 跨服务通知）**：**DB 事件表 outbox + `pg_notify` 加速 + 轮询兜底**（复用 config-mirror 范式）。发方写 outbox 行 → `pg_notify` 唤醒 → 收方消费；漏了靠轮询补。风控：服务提交「风控事件」到 outbox，automation 的 RiskController 单写者消费；读侧读 `risk_state` 投影（已在库）。**天然跨进程、无新依赖、活到拆库之后**（拆库时每服务自带 outbox）。
- **同步 RPC（决定①，数据网关 37 条读）**：**HTTP + JSON**。automation/content 暴露「内部读 API」；api 经**数据网关**统一调，不散点直连。
- **共享契约（27 条）**：随 `@aidcp/kernel` 走，三仓共享。protocol/RoleName 因 §2 edge↔cloud 逐字同步，作为 kernel 特例登记（留 comm/，打进各服务包）。

## 3. 三决定落地

1. **数据网关（收）**：api 侧 37 条读接缝已多数在 Block① 做成注入端口/接口（如 `CuratedContentReader`/`DelegatedTaskServicePort`/`InteractionStoreReaderPort`）。**这些接口正是网关的 client stub**——把它们的实现从「本地实例」换成「HTTP 调用 automation/content 读 API」即可。api 内部收口成一个 `DataGateway`，聚合这些读 client。
2. **风控异步（异步）**：13 条风控接缝改为 outbox 事件流，不做同步 RPC。见 §2。
3. **三服务（三个）**：按 §1 拓扑，不合并。

## 4. 分阶段执行（先可逆、后不可逆；每步 dev 冒烟）

- **2a 传输原语（在单体内先建，完全可逆）**：① 建 DB outbox 事件表 + 发/收原语（pg_notify+轮询），先让风控事件**双写**（EventBus 照旧 + 也进 outbox），单进程内验证消费等价。② 建 HTTP 内部读 API 的 server/client 骨架；api 的读端口实现加一层「本地直调 or HTTP」开关（默认仍本地）。**全部单进程内，行为零变更、可回滚。**
- **2b 数据网关（api 收口）**：api 的 37 条读接缝收进一个 `DataGateway`；automation/content 落地对应内部读 HTTP endpoint。单体内网关先走本地实现。
- **2c 风控切异步**：13 条风控接缝从直调切到 outbox 事件；read-side 读投影。撤掉双写的旧直调。
- **2d 拆进程（一次拆一个，最独立的先）**：先把 **content（segB）** 拆成独立进程，经传输与单体（api+automation）通信，dev 验证；再拆 **api（segA+segD）**；剩 **automation** 为核。deploy-target 扩多服务。
- **2e 三仓 + 多服务部署**：三进程稳定后建三个 git 仓、搬码、kernel 抽成共享包、部署脚本多服务化。

**可逆边界**：2a–2c 全在单体内（传输抽象默认本地直调）→ 完全可逆、dev 可测。2d 起是真拆进程（仍可合回）。2e 建仓是提交点。**Block③ 物理拆库全程不碰**——传输是 DB-backed，正好借共享库，拆库时再各自带走 outbox。

## 5. 执行进度（2026-07-24）

- **2a 传输原语 ✅ landed + dev**：① DB 事件 outbox（`src/transport/event-outbox.ts` + 迁移 0074）——emit（事务内 INSERT + pg_notify）+ OutboxConsumer（快照安全水位 `xmin<txid_snapshot_xmin` 治乱序提交丢事件 + 轮询兜底 + per-consumer 游标 + execution_target 隔离）。**审计抓到经典"乱序提交空洞"blocker、已用安全水位修复，并在 dev 真 PG 上验证通过**（并发乱序不吞事件）。② 内部 HTTP 读 API 骨架（`src/transport/internal-http.ts`：InternalHttpServer/Client + `makeReadPort` 默认 local）。两者纯 additive、默认零行为、未接 server.ts。`src/transport/` 暂归 automation（属主待接线时定，见 §待定项）。
- **2b 数据网关 ✅ landed + dev**：`src/gateway/data-gateway.ts`（api）聚合三个 kernel 读端口（CuratedContentReader / DelegatedTaskServicePort / InteractionStoreReaderPort），经默认 local 开关（`AIDCP_GATEWAY_MODE`，缺省 local ⇒ 返回同一注入实例、零 HTTP、零行为）；三端口各有 server route + http client；client-auth/panel 的干净消费者已收口经网关，interaction 宽端口消费者留 residual（渐进）。frozenTotal 守 101（网关只引 kernel）。**内部 HTTP server 的实际 listen 属 2d，本阶段只建能力。**
- **2c 风控异步 —— 已消解，无需单独做**：核查 13 条"风控接缝"发现**全是别的服务"读"风控策略/类型**（session-limits 预算函数、RiskStatus、QUOTA_MAX、panel 读状态展示），**没有一条是跨服务写风控**。风控最终状态本来就单写在 RiskController（3 入口 1 出口 + `risk_state` 条件写），已符合"异步/单写解耦"意图。这 13 条作为**共享风控策略读接缝**保留（§9/风控域禁碰，不 kernel-lift）；拆进程时走共享策略包或读投影。**用户选的"风控异步"已成立。**

**待定项（接线时定）**：`src/transport/` 归属——outbox 首消费者是 automation、http server 端点在 automation/content、client 在 api，是跨层共享运行时基础设施；现 frozenTotal-neutral（只引 kernel），拆进程时随各服务分（client→api、server→各服务、outbox→共享运行时包）。

**发现的隐患（已修/登记）**：① 解耦把 `DEFAULT_PG_CONFIG` 搬 kernel 后，`scripts/`（不在 tsconfig typecheck 范围）里 3 个脚本仍引旧路径 → 迁移执行器运行时崩、挡住所有迁移；已修（repoint kernel）+ 部署验证。**建议把 scripts/ 纳入 typecheck 防复发。** ② dev 迁移账本整个未 baseline（表历史自建、账本空，执行器视全部迁移为待应用）——已登记真机 backlog，需单独 baseline，非本阶段副作用。

## 6. 2d 拆进程 · 第一刀 ✅ landed + dev（2026-07-24，master 87b3429）

给 `server.ts` 的 `main()` 加 `AIDCP_SERVICE` 三模式（一套代码、多入口，非三仓）：**monolith**（默认/未设/未识别值 = 四段全跑、无新监听、gateway 默认 local、**逐字节等价**，唯一不可破不变量）、**content**（segA+segB、跳 C/D、起 InternalHttpServer 在 `AIDCP_CONTENT_PORT ?? 8092` 只服务自有 curated 读端点）、**core**（segA+segC+segD、跳 segB、配 `AIDCP_GATEWAY_MODE=http`+`AIDCP_GATEWAY_BASE_URL` 时 curated 读走网关 HTTP）。新增零 import 纯模式选择器 `src/gateway/service-mode.ts`（+单测）；对抗审计 verdict clean、命门独立复跑坐实（`env -u AIDCP_SERVICE npm test` 3155/3155 绿）；frozenTotal 守 101、热文件零改动。dev 部署后进程照常开机（active+8787+飞书 onReady+config-mirror 变化=0）。

### ⚠️ 关键真实发现：core 现在起不来（开机崩，非运行路径坏）

原设计假设「segB = content only」**是错的**。实测 segB 还构造了 **~34 个共享地基对象**（eventBus、账号/人设各类 store、概念池、图片、委托任务、发布编排、审批策略、路由、各类 feed/like store、回调解析器…，全清单见 `cloud-process-split-handoff.md`），segC/segD 在**构造期**硬依赖它们。跳过 segB 起 core = 启动即崩。impl 特意**没硬拆**（大改、威胁 monolith 等价），只铺骨架 + 如实列 brokenPaths。

**下一大刀（2d 第二步）：把这 ~34 个共享地基从 segB 抽到 segA**（基础段，content+core 都跑它）。抽完 segB 只剩真 content 私有构造（发布/洗稿/精选/配图）。必守 monolith 逐字节等价。这是 core 能开机、两进程 dev 真跑起来的解锁点。**详细剧本 + 红线见交接文档 `docs/cloud-process-split-handoff.md`。** 之后：2d 第三步 dev 起两进程验证 → 再拆 api、剩 automation 为核 → 2e 三仓 + kernel 共享包 + deploy-target 多服务。
