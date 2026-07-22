## Why

账号风控是本系统唯一直接决定「真实平台动作发不发得出去」的闸，它今天的正确性只在单进程内成立，而线上正跑着两个进程。

四个已在代码里坐实的缺口：

1. **状态盲写**。`risk_state` 在 controller 创建时读一次库（`aidcp-cloud/src/risk/risk-controller.ts:140-149`），此后纯内存变更 + 全列 upsert 写回，无版本列、无条件谓词（`aidcp-cloud/src/risk/pg-risk-store.ts:191-204`）；注册表的 controller Map 无 delete / TTL / 失效（`aidcp-cloud/src/risk/risk-controller-registry.ts:29,49-56`）。后写方以自己创建时的快照覆盖先写方的全部列。
2. **配额计数只回放一次**。滑动窗计数只在 `RiskController.create` 时按一天窗口回放（`risk-controller.ts:145-148`），之后只累加本进程 `record` 的那些（`risk-controller.ts:221-227`），而准入判定 `explain` 读的就是这份内存计数（`risk-controller.ts:160-172`）。库里由别的写者产生的行永远不会被它看见。
3. **今天就在发生的跨进程写冲突**。dev 与 ol 是两个进程、共用 `121.89.85.150/aidcp` 同一个库（`docs/deployment-environments.md:62-64`），共写同一张 `risk_state` / `risk_counters`。面板首页汇总还会为库里**全部**账号（`aidcp-cloud/src/panel/panel-store.ts:471-474` 无 target 过滤）物化并永久缓存 controller（`aidcp-cloud/src/panel/panel-server.ts:711-720`），配合两个整行盲写口（`panel-server.ts:1628-1636` 的 `/risk/signal`、`panel-server.ts:1655-1656` 的 `/risk/quota`），当前就能把另一个 target 刚写下的 `restricted` 盖回 `normal`。后果不是性能问题：配额按进程各算一份 ⇒ 合计放行的点赞 / 评论 / 发帖是单份上限的两倍；受限状态被陈旧的正常状态静默盖回 ⇒ 已被平台警告的账号继续被驱动。这直接违反「状态单写」与「禁止静默假成功」两条红线。
4. **跨重启丢账**。边缘回执 → 风控记账这条路径今天是进程内事件总线上一句 fire-and-forget、异常只打 `console.warn`（`aidcp-cloud/src/server.ts:1592-1612`，搜索侧同形 `server.ts:1677-1687`）。进程崩在「回执已到、`appendCounter` 未提交」之间，这次真实发生的平台动作就此从账本上消失；后续 `canDo` 据此误以为尚有余量而放行更多真实动作。

云端拆分方案 §14.1 红线表第 9 行（`AC-DECOMP-09`）把「账号最终风险状态 MUST 由 RiskController 单写」列为验收红线，但全文没有一句说明拆分后 `aidcp-automation` 对同一 `executionTarget` 必须单实例——这句红线在多进程下会自动「通过」。（该方案顶层编号 §1–§17 冻结、§14 下只有 §14.1 红线表与 §14.2 附注，**不存在 §14.9**；本 change 早期稿引用的 `§14.9` 一律指 §14.1 表内 `AC-DECOMP-09` 行。）拆三仓的决定已定，本变更要在拆分之前把这条不变量写成可验收形式并落地，否则拆分只是把一个进程内的假设分发到三个仓里。

## What Changes

- 把「风控单写」从进程内约定升级为**可验收的全局不变量**：对任一 `accountId`、任一时刻，`risk_state` 的写入者唯一，且配额判定所依据的计数与库内事实一致。
- **选定单实例路线（路线 A）并写清理由**，不做去单实例改造（路线 B）：承载风控写的自动化进程对每个 `executionTarget` 单实例，部署形态保持 stop→start，禁止滚动 / 蓝绿。
- 单实例不再只是文档纪律：启动时以 PostgreSQL 会话级 advisory lock 按 target 抢写者锁，抢不到即拒绝启用风控写路径并告警，不降级为无锁照写。
- 引入**账号归属 target** 这一事实（`accounts.execution_target`，服务端注入、不从客户端 / `envKey` / 边缘上报推导），解决跨 target 冲突：非属主 target 拒绝该账号握手，非属主实例不物化可写 controller。
- `risk_state` 的每次写改为**带属主谓词的条件写**，影响行数为 0 即诚实拒绝（`risk_state_not_owned`）并驱逐本地缓存 controller，绝不重试覆盖、绝不静默成功。
- `risk_counters` **刻意不按 target 分裂**：它是 append-only 的既成事实账本，同一账号的当日额度必须是一份而不是两份。
- 为「边缘确认的真实动作 → 风控记账」建一张带 `execution_target` 的 outbox 表（`risk_counter_outbox`），照抄委托任务的认领令牌 + 租约 + 跳锁 + 启动回收范式；回执处理先提交 outbox 行再推进浏览闭环，apply 与计数落库同事务、按 `outbox_id` 唯一约束做到 exactly-once，尝试超限进死信并告警。
- 增加内存计数与库内事实的周期对账：偏差非零即告警并以库为准重建计数，不静默沿用偏差计数。
- 在方案文档补一张「单实例 / 可多实例」组件分类表：委托任务 worker 与内容排期小时格认领为可照抄的正例，发布下发器、验证码协助、连接运行时注册表列入必须单实例。
- 面板与控制台按归属 target 呈现只读 / 可写，非属主账号的风控写口返回可区分拒绝而不是 200。

## Capabilities

### New Capabilities

<!-- 无。本变更加固既有风控准入、同账号并行安全与部署目标隔离三项能力，不新增能力。 -->

### Modified Capabilities

- `interaction-risk-gating`: 风控状态写入者全局唯一、计数与库内事实一致、记账经 outbox 跨重启不丢。
- `same-account-parallel-safety`: 账号归属单一 `executionTarget`，非属主 target 拒绝驱动该账号且不持有可写控制器。
- `deployment-environments`: 自动化写者每 target 单实例、部署形态禁止滚动 / 蓝绿，后台组件必须登记单实例 / 可多实例分类。

## Impact

- Cloud：新增迁移 `0057`（`accounts.execution_target`、`risk_counter_outbox`、`risk_counters.outbox_id`，全部 additive）；改 `src/risk/pg-risk-store.ts` 的 `saveState` 为条件写、`src/risk/risk-controller.ts` 的记账入口、`src/risk/risk-controller-registry.ts` 的只读 / 可写解析与失效、`src/server.ts` 的 `interaction.occurred` / `search.occurred` 订阅、`src/orchestrator/connection-runtime.ts` 的握手准入、`src/panel/panel-server.ts` 的风控读写口；新增写者锁与 outbox worker。
- Edge：无协议改动、无新消息类型；只需把握手拒绝码 `execution_target_mismatch` 如实呈现给运营，不得渲染成通用离线。
- Console：账号列表与风控操作按归属 target 显示；非属主账号的风控写按钮禁用并显示归属，收到可区分拒绝时不显示成功。
- Control：更新 `docs/cloud-service-decomposition-proposal.md` §14.1 红线 9（`AC-DECOMP-09`）/ §12 阶段 2 / §5.1 / §11，更新 `docs/risk-control.md` 与 `docs/deployment-environments.md`。**MUST NOT 新增 §14.x 小节**——该文档顶层编号 §1–§17 冻结，红线按 `AC-DECOMP-*` 稳定 ID 引用、不按序号引用。
