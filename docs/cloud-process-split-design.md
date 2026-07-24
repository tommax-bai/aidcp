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

## 5. 第一步（现在做）

**2a-①：DB outbox 事件传输原语。** 建事件表 + 发/收（pg_notify+轮询兜底），先接风控事件双写、单进程内验证消费与现有 EventBus 等价。行为零变更、可回滚、dev 冒烟。这是拆进程的承重地基，且完全可逆。
