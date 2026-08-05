## Why

2026-08-05 生产实测（dev + OL 同库）：**12 个 Facebook 账号的消费模式互动链全部冻死**，现象是「浏览照跑、点赞与加群永久停止」，日志零报错。

根因是两件事叠在一起：

1. **群评论时序策略在自动化进程里没有通道**。拆仓时按属主裁定，`facebook_group_comment_policy` 属接口域，自动化进程既无同步读流也无 HTTP 口去读它（`aidcp-automation/src/automation-main.ts` 两处显式 `state: 'unavailable'`）。当时登记的后果是「本进程的 Facebook 覆盖评论一条都不会发」。
2. **消费链的「当前待办」是单槽的**。`facebook_consumption_progress.active_action_id` 非空时，`applyConfirmedView` 连浏览事实都不记（直接返回 `action_active`）。评论义务一旦停在 `waiting_gate`，它后面的点赞与加群**一并停摆**。

于是第 1 条的真实后果远大于登记：不是「少发评论」，而是**整条链停摆**。实测账号 `61592103224459` 自 18:16:52 起卡住，其后 166 次浏览全部空转；最早一个账号（OL）自 08-04 10:32 起卡了一天多、重试 3325 次、期间零点赞。库内唯一能解冻的路径是运营策略换号（supersede），重启与新会话都无效。

这属于红线「静默假成功」的另一半：**下游把「一件事没做成」读成了「所以什么都别做了」**，而且这个状态是持久的、跨重启的、无任何告警。

第 2 条的危害与第 1 条是否修复**无关**：即使策略接通，只要账号名下暂时没有满足预热的历史群（`no_strict_eligible_historical_group`，新号必然如此），评论义务同样停在 `waiting_target`，同样冻住点赞与加群。

## What Changes

**A. 把群评论时序策略接进自动化进程**

- 群评论时序策略（`joinToFirstCommentHours` + 同群再评冷却）随**已有的 `content_schedule` 同步读流**下发到自动化进程。选这条流不是就近凑合：该策略的写入本来就 bump `content_mirror` 的 `content_schedule` 版本号，单体里读它的闸也正是 `isStale('content_schedule')`——放在同一条流上，游标天然覆盖载荷，语义与单体逐位一致。
- 自动化进程的两个取用点（覆盖评论调度器 / 消费模式协调器）由 `state: 'unavailable'` 改为经镜像取值；镜像陈旧时**仍返回 null**、仍报同一个具名 blocker（fail-closed 不变，MUST NOT 塞默认时长顶替）。

**B. 把「等待中的义务」与「当前待办」解耦**

- 「当前待办」槽位**只归可下发的动作**（点赞在途、或已绑定目标待下发的加群/评论）。处在**下发前等待态**（`waiting_target` / `waiting_gate`，`dispatch_phase='not_started'`）的加群 / 评论义务 MUST NOT 占住槽位——浏览事实照记、点赞机会照产生。
- 义务本身**不作废、不重置信用**（沿用现有 spec：一份义务持久留存），只是不再挡路；它由既有的在途扫描与浏览路径继续推进。
- 加一道**积压上限**：同一账号同一策略号下，同类型未终结义务至多一份。到点时若已有一份未终结的同类义务，MUST NOT 再造一份，MUST 响亮记一行（合并进已有那份），MUST NOT 静默丢弃。
- 同一次浏览里**至多驱动一个面向边缘的动作**：本次浏览产生了点赞就不在同一轮驱动等待义务，避免两条边缘动作叠在同一时刻。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `facebook-consumption-mode`: 明确「等待中的评论 / 加群义务不占用推进槽位」——浏览与点赞段 MUST NOT 因下游义务等待而停摆；并补「同类义务至多一份」的积压上限与「一次浏览至多一个边缘动作」的排他。原有「义务持久、不还信用、不造重复机会」的判据逐字不变。
- `facebook-group-comment-coverage`: 补一条**属主可达性**要求——真正执行覆盖评论与消费评论的那个进程 MUST 能读到群评论时序策略；读不到 MUST 具名失败且 MUST NOT 拖住无关动作段。

## Impact

- `aidcp-cloud/src/kernel/sync-read-facts.ts`：`content_schedule` 载荷新增群评论时序策略段 + 校验器。
- `aidcp-cloud/src/config/api-sync-read-source.ts`：新增策略取值口并写进 `content_schedule` 快照。
- `aidcp-cloud/src/server.ts`：单体装配处注入该取值口（保持整图一致）。
- `aidcp-cloud/src/orchestrator/facebook-consumption-mode-runtime-store.ts`：等待态义务让出槽位 + 同类义务积压上限。
- `aidcp-cloud/src/orchestrator/facebook-consumption-mode-types.ts`：浏览结果携带「被让位的义务」。
- `aidcp-cloud/src/orchestrator/role-dispatcher.ts`：消费浏览处理按新结果推进，并守「一次浏览至多一个边缘动作」。
- `aidcp-api/src/server.ts`：把策略存储接到同步读源。
- `aidcp-automation/src/automation-main.ts` / `automation-business-config.ts`：两个取用点由 unavailable 改为经镜像 wired。
- 不改协议 v2、不改数据库 schema、不改风控状态机、不改配额与审批路径。
- 部署：默认 `dev`。**OL 上的 10 个冻结账号需 OL 也更新后才自动解冻**；在此之前只能靠运营策略换号临时解冻。
