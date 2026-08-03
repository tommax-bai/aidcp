## Why

拆仓做到今天，**五个派生仓一次都没在任何机器上跑起来过**。`/opt/aidcp/` 下只有 `cloud` 一个部署位；
api / automation / content 三个仓的手写 `main()` 至今只被 typecheck 和单测碰过。

这不是"还差最后一步"，而是**整批工作至今没有任何证据**。本项目已经反复付过这一类代价：客户端建得出来、
调用点编译得过、六仓测试各自全绿——**只有真把进程一起跑起来才 404**，而那个 404 会被读成"对面版本落后"。
上一个 change（`wire-content-scheduler-into-api-process`）为此连撞五次的记载，正是在没有运行证据的前提下累积的。

现在是最省事的时机：六仓刚完成一次全量对账，`src/` 逐字对齐、三个共享包 pin 全对、六仓测试全绿。
这个状态不会自己维持——车队每天都在推进主干。

**另有一件必须同批裁定的事**：dev 上早有四个 systemd unit（`aidcp-cloud-{api,automation,content,core}.service`，
全部 `disabled`，2026-07-26 三个真跑过约一分钟）。它们跑的是**单体按 `AIDCP_SERVICE` 切段**，
不是派生仓。而单体切分下排期器在 `segCAutomation` 里构造 ⇒ 跑在 automation 进程；
刚归档的 spec `api-process-content-scheduling` 却明写"只由接口服务承载、自动化装配 MUST NOT 构造它"。
**两条路径对同一个后台任务给出相反的归属答案**，留着不管就是两份互斥的权威。

## What Changes

- **三个业务仓真部署到 dev**：各自独立目录、各自依赖安装、各自 `.env`、各自 systemd unit，
  跑各自手写的 `main()`——**不是**单体按角色切分。
- **补齐三仓的启动外壳缺口**：`aidcp-api` 与 `aidcp-content` 今天没有可执行入口
  （`src/index.ts` 是纯出口桶，`server.ts` 靠 `import.meta.url` 自举）；automation 有 `automation-service-entry.ts`。
  三仓 MUST 有同一形态的启动外壳与就绪/退出语义。
- **三仓各自过 schema 契约门**：三个属主库各自的迁移账本、各自的 REQUIRED 版本。
  部署顺序对每个属主库都是硬的（迁移先于重启）。
- **裁定并消除排期器归属的两份权威**：派生仓形态按已上线 spec（归接口服务）；
  单体按角色切分这条路径 **MUST 显式声明其地位**——退役、或写清它是过渡形态且其归属不受该条约束。
  **MUST NOT** 留着两条相反的活路径。
- **soak 与验收**：跑够一段连续时间，并逐条走 `docs/real-machine-acceptance-backlog.md` 簇 60 里
  已登记的验收项；**逐条记录"验到了什么、没验到什么"**，MUST NOT 用"跑起来了"概括。
- **不做**：ol 上线（须用户明确要求并从发布分支走）；单体退役（单体仍是 dev/ol 的现役形态，本批只是让派生仓
  在旁边同时跑得起来）；任何业务行为改动。

## Capabilities

### New Capabilities

- `split-service-runtime-deployment`: 三个业务服务在一台机器上作为**独立进程**部署与运行的形态约束——
  部署位与依赖隔离、启动外壳与就绪语义、三个属主库各自的迁移顺序、进程间基址与令牌的配置事实源、
  以及"哪些东西 MUST NOT 由部署方猜"。
- `split-service-runtime-evidence`: 三进程跑起来之后**什么才算被验证**的判据——
  逐条声明已验 / 未验、区分"进程起来了"与"这条链真走通了"、
  以及跨进程调用失败时哪些原因码 MUST 保持可区分（漏注册 ≠ 对面不可达 ≠ 版本落后）。

### Modified Capabilities

- `api-process-content-scheduling`: 补写**适用范围**——该 capability 的归属条款（调度器只由接口服务承载、
  自动化装配 MUST NOT 构造它）针对**派生仓三进程形态**；单体按 `AIDCP_SERVICE` 切段那条路径的处置须同批裁定并写明，
  不留两份互斥权威。

## Impact

**新增（部署面，非代码）**：dev ECS 上三个部署位（`/opt/aidcp/{api,automation,content}`）、
三份 `.env`、三个 systemd unit、端口与 Nginx（若面板/客户端 API 需要经派生 api 进程暴露）。

**代码面**：
- `aidcp-api` / `aidcp-content`：补启动外壳（照 `aidcp-automation/src/automation-service-entry.ts` 的既有形态）。
- `aidcp-cloud`：若裁定"单体切分路径退役"，则 `segmentsForMode` 与四个 unit 的处置随之确定；
  若裁定"保留为过渡形态"，则须在 spec 侧写清适用范围。**两者都不许沉默**。
- 控制仓：`docs/cloud-composition-root-trisection.md` §9.7.4 与 `docs/deployment-environments.md` 的部署形态描述。

**依赖 / 环境**：三仓在 ECS 上各自 `npm ci`——内网 registry 对 `@types` 域的劫持已知，
绕法 `--userconfig /dev/null` 已在本机实测可用，ECS 上须复验。三个共享包走 git+ssh pin，
ECS 需具备拉取权限。

**红线不变**：同机 isales 一根手指不碰；dev/ol 长期共库，三仓的 `execution_target` 隔离照旧；
单体仍在 8787 服役，派生仓的端口 MUST 与之物理隔离，MUST NOT 抢占。
