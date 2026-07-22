## Context

### 现状一：授权这一位存在本机文件里

授权的唯一载体是 `/tmp/aidcp-publish-approve-<requestId>.json`。

写侧（拆分后归 `aidcp-api`）：

| 入口 | 位置 | 说明 |
| --- | --- | --- |
| 飞书卡片回调 | `aidcp-cloud/src/feishu/ws-receiver.ts:321` | 经 `writeApprovalSignal`（`:151`） |
| 管理后台审批路由 | `aidcp-cloud/src/panel/panel-server.ts:1302` | `POST /api/publish/<requestId>/approve` |
| 客户端内审批 | `aidcp-cloud/src/server.ts:2815` | `publish.approval_action` → `createClientPublishApprovalHandler`（`src/publish-agent/client-publish-approval.ts:70`） |
| 委托任务批准 / 拒绝 | `aidcp-cloud/src/server.ts:3991`、`:4005` | `approveCandidate` / `rejectCandidate` |
| 排期 `auto_approve` 预授权 | `openspec/specs/content-schedule/spec.md:8` | 写「同形 `approved===true` 授权信号」 |

读侧与作废侧（拆分后归 `aidcp-automation`）：

| 动作 | 位置 |
| --- | --- |
| 下发前复核 | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:453` |
| 60s 兜底扫描 | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:373` |
| 评论审批闸轮询 | `aidcp-cloud/src/agents/comment-approval-gate.ts:218`（端口定义 `:16`-`:36`） |
| 版本闸作废 | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:464` |
| 抢占退避作废 | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:275` |
| 租约未确认作废 | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:641` |
| 实现 | `aidcp-cloud/src/server.ts:2076`（读）、`:2088`（布尔视图）、`:2093`（删） |

互斥语义靠文件系统：`writeApprovalSignal` 用 `flag:'wx'`（`O_EXCL`）实现 first-writer-wins，撞 `EEXIST` 即读回既有决定返回 `alreadyDecided`（`ws-receiver.ts:158`-`:175`）。作废语义靠 `unlink`（`src/server.ts:2093`-`:2098`），删掉即代表「可重新审批」。

「授权 → 下发」的触发今天是进程内直调：`triggerPublishDispatchOnApprove`（`src/server.ts:2720`）在写文件成功后同步调 `publishDispatcher.dispatch()`。拆分后这是一次跨进程调用，必须换成持久命令。

`requestId` 是不透明关联令牌，且**因为要拼进文件路径**才被强制归一到 `[A-Za-z0-9_-]`（`src/agents/comment-approval-request-id.ts:23`-`:30`；面板白名单 `src/panel/panel-server.ts:1246`-`:1252`）。历史事故：Facebook 的 `noteId` 是完整 URL，直接嵌进 `requestId` 会让 `posix.join` 把 `/` 当目录分隔 → `writeFile` 抛 `ENOENT` → 读侧恒 false → 人点了同意仍超时丢评论。

### 现状二：edge 侧的两端契约已是空契约

`aidcp-edge` 侧确有同路径实现：`src/publish/approval-gate.ts:56`（`buildPublishApprovalSignalPath`）、`:95`（`waitForPublishApproval`），被 `src/flows/publish-post.ts:407` 调用。但生产链路上没有调用者：

- `aidcp-edge/src/main.ts:769` 明确记录整页发布处理器 `client.onPublishCommand`（`publish.request`）已删除；
- `aidcp-edge/src/client/operation-registry.ts:104` 把 `publish.request` 标为协议兼容墓碑，注释写明 main 没有处理器、生产只执行 `publish.command` 原子；
- `aidcp-edge/src/client/edge-client.ts:797` 收到 `publish.request` 时因 `publishHandler` 未注册直接回 `handler_unavailable`；
- `publishPost` 在 `src/` 下零调用者，唯一实际调用点是 `aidcp-edge/scripts/dev-publish.ts:1039`。

也就是说：这条「两端契约」今天只在开发脚本与两侧的契约测试里活着（`aidcp-cloud/test/acceptance/publish-approval-contract.test.ts:16`、`aidcp-edge/test/acceptance/publish-approval-contract.test.ts:32`），生产发布走的是云端 `CommandSequencer` 逐条下发 `publish.command`，人审闸在云端。这决定了 edge 侧的处理成本远低于 api/automation 侧。

客户端内审批走的是另一条协议路径：`publish.approval_action` / `publish.approval_action.result`（`protocol.ts:78`-`:79`、`:942`-`:960`），按信封 id 应答，不进主动命令白名单。它的写侧在云端，本身不读文件。

### 现状三：advisory lock 跨模块共用

`interaction-env:<envKey>` 的全部引用点：

| 位置 | 拆分后归属 | 场景 |
| --- | --- | --- |
| `src/client-auth/client-user-store.ts:619` | api | `beginEnvironmentOffboard`：客户主动解绑 |
| `src/client-auth/client-user-store.ts:1468` | api | 客户禁用时批量解绑其全部环境 |
| `src/client-auth/client-user-store.ts:2001` | api | 环境归属批量改派 |
| `src/client-auth/client-user-store.ts:2128` | api | `reconcileRevocationHolds` 常驻对账 |
| `src/interactions/interaction-store.ts:339` | automation | `upsertAuthStatus`：边缘上报的环境登录态首写 |

`interaction-store.ts:337`-`:338` 的注释逐字写明「Same lock as `ClientUserStore.beginEnvironmentOffboard`：首次授权与客户解绑必须对同一环境观察到同一串行顺序」。这是一把**跨未来服务边界**的锁。

同文件另有两把锁不跨边界，但必须在盘点表里登记：`interaction-store.ts:409`（`<platform>|<accountId>|<batchId>` 批次幂等）、`:989`（`interaction-send|<accountId>` 发送串行）。

## Goals / Non-Goals

**Goals：**

- 授权成为 api 单写的持久事实，automation 经命令与窄查询获知，跨进程、跨主机、跨容器都成立。
- 保留今天已被验收覆盖的四条语义：`approved === true` 严格判定、first-writer-wins、版本闸「审=发」、作废后可重新审批。
- 让「已批准但尚未下发」成为一个用户能看见、能区分、能追问的状态。
- 消除跨服务共享的 advisory lock，且替换后的机制在拆库后仍然有效。
- 把这两类问题背后的盘点方法论缺口补进阶段 0，使同类问题在后续拆分中被机械发现。

**Non-Goals：**

- 不改变审批的业务判据（谁能批、批什么、版本闸规则）。
- 不改变发布下发序列、租约、抢占、熔断的既有分类与副作用边界。
- 不在本 change 内完成仓库物理拆分；本 change 按 §12 阶段 1 的要求，先在 `aidcp-cloud` 内以未来 HTTP/消息的合同形状落地。
- 不引入外部消息中间件；Outbox/Inbox 用现有 PostgreSQL 承载。

## Decisions

### 1. 授权载体 = `publish_approval_decision` 表，api 单写

字段（最小集，全部为真列而非塞 JSONB，使闸成为原子 WHERE 谓词）：

```text
request_id        TEXT NOT NULL     -- 不透明关联令牌，沿用 publish-<recordId> / comment-<noteId>-<ts>
revision          INT  NOT NULL     -- 同一 request_id 的第 N 轮授权（作废后 +1）
subject_kind      TEXT NOT NULL     -- 'publish' | 'comment'
candidate_ref     TEXT NOT NULL     -- publish=recordId，comment=noteId
content_version   INT  NOT NULL     -- 候选版本标识（对应 publish_log.content_version）
approved          BOOLEAN NOT NULL  -- 决策本身
decided_by        TEXT NOT NULL     -- 决策人：飞书 open_id / 后台用户 / 客户端 accountId / 排期规则 id
decided_via       TEXT NOT NULL     -- 'feishu' | 'console' | 'client' | 'delegated_task' | 'schedule_auto_approve'
decided_at        TIMESTAMPTZ NOT NULL
env_key           TEXT              -- 目标环境（无环境归属的手动稿可为 NULL）
execution_target  TEXT NOT NULL     -- 'dev' | 'ol'，服务端注入
frozen_payload    JSONB NOT NULL    -- 审批面所审的那一份字节（title/content/tags/contentVersion）
dispatch_state    TEXT NOT NULL     -- 'pending_dispatch' | 'dispatching' | 'consumed' | 'void'
dispatch_blocked_reason TEXT        -- 阻塞原因（可为空）
dispatch_state_at TIMESTAMPTZ NOT NULL
void_reason       TEXT              -- 作废原因（dispatch_state='void' 时必填）
```

- 主键 `(request_id, revision)`；
- **first-writer-wins 由 `CREATE UNIQUE INDEX ... ON publish_approval_decision (request_id) WHERE dispatch_state <> 'void'` 承担**。写出口用 `INSERT ... ON CONFLICT DO NOTHING RETURNING *`：返回行即 `{written:true}`，返回空即读回活跃行返回 `{alreadyDecided:<approved>}`。这与 `O_EXCL` 语义逐条对应，且是数据库层的原子性，不依赖文件系统。
- **作废不删行**：`dispatch_state='void'` + `void_reason`，活跃部分索引随即让出，下一轮授权以 `revision+1` 插入成功。今天「删文件 = 可重新审批」的语义保留，且多出完整审计轨迹（谁在什么时候作废了哪一版）。
- 不复用 `publish_log` 的列：评论审批没有 `publish_log` 行，`candidate_ref` 是 `noteId`；两类审批必须共用一张表才能共用一个写出口，这是今天 `writeApprovalSignal` 被评论链原样复用的前提（`src/feishu/comment-approval-card.ts:6`）。

`requestId` 的字符集归一（`sanitizeApprovalRequestSegment`）保留，理由改变但结论不变：它不再是文件路径片段，但仍是面板 URL 路径段与跨服务消息键，保持受控字符集消除注入面。

### 2. automation 经「命令 + 窄查询」获知授权，两条路都 fail-closed

- **主路径（事件驱动）**：api 在决策落库的同一事务写 Outbox `PublishApproved{requestId, candidateRef, contentVersion, envKey, executionTarget}`；automation Inbox 去重后触发一次下发。它替代今天的进程内直调 `triggerPublishDispatchOnApprove`（`src/server.ts:2720`）。
- **复核路径（同步查询）**：automation 在真正下发 `submit_publish` 前必须再查一次 `GET /internal/publish-approvals/{requestId}`，拿 `{approved, contentVersion, dispatchState, envKey, executionTarget}`。这保留今天下发前复核那道纵深防御（`publish-dispatcher.ts:453`）。查询超时 / 5xx / 不可达 → 视为未授权、不下发、记 `dispatch_blocked_reason='approval_unreadable'`，**不写任何终态**。
- **兜底扫描改造**：今天是 automation 遍历 `pending_approval` 的 id 再逐个读文件（`publish-dispatcher.ts:370`-`:378`）。改为查 api 的 `GET /internal/publish-approvals?dispatchState=pending_dispatch&executionTarget=<本机 target>`，按 §8 的 target 隔离规则过滤。这同时修掉一个现存放大器：今天扫描对每条待审 id 都做一次文件系统读，拆分后会变成对每条 id 一次跨服务 HTTP。
- **作废改为 api 端点**：`POST /internal/publish-approvals/{requestId}/void{reason}`，reason 取自现有四个作废场景的枚举（`version_stale` / `edge_offline` / `preempt_exhausted` / `lease_unconfirmed`）。automation 不得直接写 api 的表（§5.1 单写者）。

为什么不选「automation 直接读 api 的库表」：违反 §5.1 与 §6.4 第 2 条；且授权表要跟着 api 迁 schema/库，直接读表会在阶段 4 提取 api 时二次断裂。

为什么不选「只用事件、不做同步复核」：`PublishApproved` 是至少一次投递，重放可能携带过期版本；下发前复核是版本闸「审=发」的最后一道（`publish-pipeline` 的「下发前版本一致性闸」）。丢掉它等于把 TOCTOU 窗口拉大到消息延迟。

为什么不选「只用同步查询、不发命令」：那需要 automation 高频轮询 api，等于把今天 60s 兜底扫描升级为唯一路径，通过即切的时延语义（`publish-pipeline:302`）会退化。

### 3. 「已批准·待下发」是一个独立可见状态

今天审批通过后，`publish_log.status` 仍是 `pending_approval`，直到下发成功才变。控制台与客户端把它渲染成「待审批」（`src/panel/publish-stage-lifecycle.ts:326`-`:329` 用「有无在途」区分，而在途是进程内事实）。automation 整体不可用时，运营看到的与「还没人批」完全一样——这就是静默停滞。

改为：

- 授权落库即 `dispatch_state='pending_dispatch'`，投影上是「已批准·待下发」，且必须带 `decidedAt` 与「自批准起已等待时长」；
- automation 领取执行时经 `ExecutionDispatched` 事件把它推到 `dispatching`；
- 任何已知阻塞（边缘离线、浏览器槽位等待、账号熔断、授权查询不可读、Outbox 积压）必须落到 `dispatch_blocked_reason` 并在投影上出现；
- 超过阈值（默认 15 分钟，env 可配）仍在 `pending_dispatch` 且无阻塞原因 → api 主动告警，因为「没有原因的长时间待下发」恰恰是 automation 静默失联的形态；
- `dispatch_state` 与 `publish_log.status` 是两个轴：前者是授权的下发进度，后者是稿件的业务态。合并两者会让「已批准但下发侧不可用」重新变得不可表达。

### 4. edge 侧：文件闸降级为开发夹具，协议侧只做增量字段

依据现状二，edge 生产链路没有文件读者。因此不需要新增协议消息来「替代」文件闸——需要替代的是**契约的性质**，不是机制：

- **阶段 A（兼容窗口，默认开）**：api 写持久记录成功后，best-effort 影子写同路径同格式文件，由 `AIDCP_PUBLISH_APPROVAL_LEGACY_SIGNAL_FILE`（默认 `true`）控制。影子写失败只记日志，MUST NOT 影响授权成败——持久记录是唯一权威。影子写只在 api 与读者同机时有意义，这一点必须写进部署文档，不得默认它一定生效。
- **阶段 B**：edge `waitForPublishApproval` 加显式启用门（同时要求 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 与 `AIDCP_DEV_PUBLISH=1`），未同时满足即抛 `approval_gate_disabled`，不静默通过也不静默等待到超时。新增回归断言：生产算子表内 `publish.request` 无处理器（对照 `src/client/operation-registry.ts:104` 的墓碑）。
- **阶段 C**：两侧 `publish-approval-contract` 验收从「同一文件路径」改判为「同一 `requestId` + 同一 `contentVersion` 的授权判定」；edge 侧断言改为「生产路径无文件依赖」。关闭影子写是**独立一步**，前置条件是盘点确认零读者且 dev 与 ol 各观察满一个发布周期，且必须可单独回滚。

协议侧唯一改动是增量可选字段：`PublishApprovalActionResultPayload` 增 `dispatchState?: 'pending_dispatch' | 'dispatching' | 'blocked'` 与 `dispatchBlockedReason?: string`（`aidcp-cloud/src/comm/protocol.ts:953`-`:960` 与 edge 同名文件逐字同步）。

- 不动 `state?: 'approved' | 'rejected'` 的既有取值。旧客户端对新增取值会落进 else 分支显示为失败；新增**可选字段**则被旧客户端忽略，行为不变。这是「不得一刀切断」的具体落法。
- 该消息按信封 id 应答，不进 `edge-client.ts` 的主动命令路由白名单（CLAUDE.md §2 第 4 处的例外条款）。
- `action.completed.action` 的动作名口径不受影响。

### 5. advisory lock：环境级串行的权威归 api，锁与数据同库

替换 `interaction-env:<envKey>` 的跨界用法：

- automation 侧唯一跨界写点 `InteractionStore.upsertAuthStatus`（`interaction-store.ts:333`）改经 api 的窄内部端点 `PUT /internal/environments/{envKey}/auth-state`；
- api 在该端点的事务内先 `SELECT ... FROM client_environments WHERE env_key = $1 FOR UPDATE`（行锁）再写，替代 advisory lock。行锁与 advisory lock 的关键差别：行锁绑定被保护数据所在的那张表，**服务拆库后锁与数据仍在同一库**，不会出现「两侧各自加锁成功、互斥消失」；
- api 侧现有 4 处 `interaction-env:` 调用改为对同一批 `client_environments` 行按 `env_key` 升序取行锁（现有代码在 `:1468`、`:2001` 已经在做排序取锁，死锁序保持不变）；
- `interaction-store.ts:409`、`:989` 两把锁不跨边界，随 `InteractionStore` 整体归属一个服务，只需在盘点表登记，不改实现。

为什么不选「保留 advisory lock，靠部署纪律保证同库」：这正是「静默失效」的定义——一次拆库、一次读写分离、一次连接池指向副本，互斥就没了，而且没有任何报错。项目红线禁止这种形态。

为什么不选「引入分布式锁（Redis / etcd）」：§15 明确当前阶段不引入新中间件；且这里根本不需要跨库互斥——把写点收敛到数据所有者之后，单库行锁足够。

### 6. 阶段 0 盘点清单扩展为六类

现清单四类（`docs/cloud-service-decomposition-proposal.md:495` 一行）只覆盖进程内状态、EventBus 事件、Store、表。补四类：

1. **本机文件系统信号与共享路径**：审批信号文件、安装包清单扫描目录、协助基址等以本机路径为事实源的项；
2. **本机进程内锁与内存事实表**：配置内存镜像、验证码协助事故表等非表、非事件的运行时事实；
3. **数据库级 advisory lock**：按 key 命名空间登记全部引用点及其归属服务；
4. **常驻定时任务**：`setInterval` 宿主（`aidcp-cloud/src` 下 24 处调用点）及其扫描 / 写入的表、其 `execution_target` 归属。

每类盘点行的必填字段统一为：引用点 `文件:行` → 拆分后归属服务 → 是否跨服务 → 跨服务时的替代机制 → 不替代会怎样失效（一句话，必须写出失效**方向**是静默还是报错）。「失效方向」这一列是本次两个问题共同暴露的：两者都是静默方向，都因此长期未被登记。

## Risks / Trade-offs

- **迁移期双事实源**：影子写文件与持久记录并存，可能出现文件有、记录无（api 崩在两步之间）。取舍：持久记录先写、文件后写，且读侧一律只信记录；文件在阶段 C 删除。任何「读文件补记录」的回填逻辑都不做——那会重新造出第二事实源。
- **`ON CONFLICT DO NOTHING` 与部分唯一索引的行为差异**：部分索引上的 `ON CONFLICT` 需要显式 `WHERE` 谓词匹配推断。取舍：写出口收敛在唯一一个 Store 方法内，并加一条并发写测试（两个并发授权只有一个 `written:true`）。
- **跨服务查询把下发链路变长**：下发前复核多一次 HTTP。取舍：查询有超时与预算，失败 fail-closed 为待下发而非失败；同时兜底扫描从「逐 id 查询」改为「按 target 批量拉取」，净调用量下降。
- **`revision` 让 `requestId` 不再唯一**：读侧若按 `request_id` 取多行会拿到历史轮次。取舍：所有读接口只返回活跃行（`dispatch_state <> 'void'`），历史轮次只经审计接口暴露。
- **告警噪声**：`pending_dispatch` 超时告警在 automation 正常但边缘长期离线时会响。取舍：有 `dispatch_blocked_reason` 的不告警（那是已解释的等待），只对「无原因的长时间待下发」告警。
- **edge 影子写关闭的时点判断错误**：若仍有未知读者，关闭即断。取舍：关闭前必须有盘点结论 + 双 target 观察期，且关闭是独立可回滚的一步。

## Migration Plan

1. 建表与单写 Store，写出口双写（持久记录为准 + 影子写文件），读侧仍读文件。此步可独立部署与回滚，行为不变。
2. 读侧切到持久记录（下发前复核、兜底扫描、评论审批闸），影子写保留。此步暴露任何遗漏的读者。
3. 接入 `PublishApproved` Outbox/Inbox 与 `dispatch_state` 投影，控制台与客户端呈现待下发态。
4. 替换 `interaction-env:<envKey>` 的跨界用法，automation 侧改经内部端点。
5. edge 文件闸加启用门、契约测试改判据。
6. 关闭影子写（独立一步，可单独回滚）。
7. 阶段 4 提取 `aidcp-api` 时，内部端点从进程内适配器切为真实 HTTP，合同形状不变。

回滚：第 1–5 步各自可回滚且不丢数据（`publish_approval_decision` 只增不改语义）；第 6 步回滚即重新打开影子写。

## Open Questions

- 无。`pending_dispatch` 告警阈值默认 15 分钟为初值，按 dev 观察调整，不阻塞本 change。
