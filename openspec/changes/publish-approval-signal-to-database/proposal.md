## Why

发布与评论的「已授权」这一位今天不在数据库里，而在一个本机临时文件上：`/tmp/aidcp-publish-approve-<requestId>.json`（`aidcp-cloud/src/feishu/ws-receiver.ts:98`、`:123`）。写方是飞书卡片回调（`ws-receiver.ts:321`）、管理后台审批路由（`src/panel/panel-server.ts:1302`）、客户端内审批（`src/server.ts:2815`）与委托任务审批（`src/server.ts:3991`、`:4005`）——拆分后全部归 `aidcp-api`；读删方是发布下发器（`src/publish-agent/publish-dispatcher.ts:373`、`:453`、`:464`、`:641`）与评论审批闸（`src/agents/comment-approval-gate.ts:218`）——拆分后归 `aidcp-automation`。同一路径还被登记为与 `aidcp-edge` 的两端契约（CLAUDE.md §4；`openspec/specs/publish-pipeline/spec.md:735`、`:751`）。

`aidcp-api` 与 `aidcp-automation` 一分进程即断：文件系统不再共享（systemd `PrivateTmp=yes`、容器化、或分机部署任一发生即触发），读方永远读不到 `approved === true`。失败方向是 fail-closed 的**静默停滞**——运营点了「通过」，稿件永远发不出去，`AC-PUB-*` 安全断言全绿，界面上仍显示「待审批」，看不出任何异常。这正是本项目红线明令禁止的形态。

同类第二处是数据库级 advisory lock `interaction-env:<envKey>`：`ClientUserStore`（api 域）在 4 处取它（`src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`），`InteractionStore.upsertAuthStatus`（automation 域，由边缘 WebSocket 的 `interaction.auth.status` 驱动，`src/comm/handler.ts:869`）在 1 处取它（`src/interactions/interaction-store.ts:339`）。拆 schema 仍成立，**拆库即静默失效**：两侧各自加锁成功、互斥消失，首次授权与客户解绑可以交叉执行。

第三处是盘点方法论缺口：方案 §12 阶段 0 的清单只列「进程内状态、EventBus 事件、Store 和每张表」，结构上盘不到本机文件信号、本地锁、库级 advisory lock、常驻定时任务这四类——上述两个问题都恰好落在盘点范围之外，所以它们至今没有被登记为拆分阻塞项。

## What Changes

- 把发布与评论的人审授权从本机文件改为 `aidcp-api` 单写的持久授权记录，至少含候选版本标识、决策人、决策时间、决策渠道、目标环境 `envKey`、执行目标 `executionTarget` 与决策本身；`first-writer-wins` 由部分唯一索引承担，替代 `O_EXCL`。
- 授权作废改为记录内状态迁移 + 新一轮授权版本，保留审计轨迹；不再靠删文件表达「可重新审批」。
- `aidcp-automation` 经持久命令（`PublishApproved`）与窄内部查询获知授权，不再读文件；查询不可用时 fail-closed 为「待下发·授权状态不可读」，不下发也不烧成终态。
- 新增「已批准·待下发」这一独立可见状态：审批落库即进入该状态，下发侧不可用时必须显示阻塞原因与等待时长，并在阈值后主动告警，MUST NOT 停留在与「待审批」不可区分的呈现上。
- 处理与 `aidcp-edge` 的两端契约：生产链路已无文件读者（`aidcp-edge/src/main.ts:769`、`src/client/operation-registry.ts:104`、`src/client/edge-client.ts:797`），把文件闸降级为本机开发夹具；兼容窗口内 api 继续影子写同路径文件，影子写失败不影响授权成败；客户端内审批的应答增量携带真实下发态字段。
- 盘点并替换跨模块共用的 advisory lock `interaction-env:<envKey>`：环境级串行的权威归 api，automation 侧的环境登录态写改经窄内部端点，锁与被保护数据保持同库。
- 把方案 §12 阶段 0 的盘点范围扩展为六类，新增本机文件系统信号与共享路径、本机进程内锁与内存事实表、数据库级 advisory lock、常驻定时任务四类，并规定每类盘点产出的必填字段。

## Capabilities

### New Capabilities

- `publish-approval-authority`: 发布与评论人审授权以 api 单写的持久记录为唯一权威，跨服务经命令与窄查询传递，并暴露诚实的待下发态。
- `cross-service-shared-state-inventory`: 拆分前对非表状态（本机文件信号、本机锁、库级 advisory lock、常驻定时任务）的强制盘点范围与替换规则。

### Modified Capabilities

- `publish-pipeline`: `submit_publish` 前的人审闸判据从审批信号文件改为持久授权记录，两端契约随之重述。
- `console-write-operations`: 发布审批写回从共享文件写入函数改为唯一持久授权写出口，`first-writer-wins` 语义保持。
- `publish-dispatch-resilience`: 授权保留与作废改为记录状态迁移，并要求下发阻塞对运营可见。
- `comment-interaction`: 评论人审授权查询改读持久记录，查询失败 fail-closed 且与「被拒」可区分。
- `content-schedule`: `auto_approve` 预授权写入同一持久授权记录，而非同形授权信号文件。
- `console-panel-api`: 审批 `requestId` 校验从「参与文件路径拼接」改为「记录主键」，并新增待下发态投影。
- `edge-desktop-packaging`: 审批信号目录从跨端契约降级为本机开发夹具，生产路径不得依赖。

## Impact

- Cloud（迁移期 `aidcp-cloud`，目标态 `aidcp-api` + `aidcp-automation`）：新增 `publish_approval_decision` 表与其单写 Store；替换 6 处写点、4 处读点、4 处作废点；新增内部授权查询与作废端点、`PublishApproved` Outbox 命令与 automation Inbox；替换 `interaction-env:<envKey>` advisory lock 的跨界用法；新增 advisory-lock 归属静态检查与非表状态盘点清单。
- Edge：`src/publish/approval-gate.ts` 与 `src/flows/publish-post.ts` 的文件闸降级为开发夹具并加显式启用门；`PublishApprovalActionResultPayload` 增量可选字段（两份 `protocol.ts` 逐字同步）；新增「生产算子表无整页发布处理器」的回归断言。
- Console：发布队列与待审详情增量呈现「已批准·待下发」及其阻塞原因、等待时长。
- Control：本 change 的 spec delta；`docs/cloud-service-decomposition-proposal.md` 的 §5.2、§6.4、§12 阶段 0、§12 阶段 4、§14 同步更新；`CLAUDE.md` §4 的两端契约描述随过渡阶段推进而更新。
