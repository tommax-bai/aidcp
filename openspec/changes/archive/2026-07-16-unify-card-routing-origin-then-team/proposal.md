## Why

运营在**私聊**里下评论命令，随后的「待审核评论」卡落到了默认管理群；同一批账号的**自动化**评论审批卡也落默认群，而不是该账号团队已配好的路由群。

根因是一个单点：评论审批卡在全仓**只有一个发送口**（`src/server.ts:2434` 的 `CommentApprovalPort.request`），它调 `resolveDefaultChatId` —— 既不看命令来源会话，也不看手里已有的 `accountId`。同一个端口实例被浏览闭环的审批闸与 `CommentScheduler` 共用，所以**每一张**「待审核评论」卡（命令 / 排期 / 自然浏览 / FB 覆盖模式 / 联系评论，XHS 与 FB 同）都从这一个口落进默认群。

来源会话这半边不是配错、是**没接线**：`restore-delegated-command-card-origin-chat`（`f248a1e`）给委托任务加的 `originChatId` 一等字段**评论任务照样存了**，但执行器的三条评论分支不往下传，且下游 `DelegatedCommentPort` / `CommentScheduler.triggerManual` / `triggerTargeted` / `compose-approve` / `CommentApprovalPort` 全链**没有这个字段的位置**——类型层面就不可表达。上一次只修了发帖那一半。

同一批症状还有三处镜像缺口：**自动 / 排期发帖**的审批卡（`publish-executor.ts:547` 回落 `getDefaultChat`，从无团队路由）、**边缘发起**的发布审批卡（`comm/handler.ts:1059` 写死默认群，依赖类型只暴露了 `getDefaultChat`）、**手动 `/comment` 终态结果卡**（`CommentScheduler.postResultCard` 走团队群、不回来源会话——已登记 backlog 86.18）。

更深的成因是**规则本身是碎的**：今天「卡该发哪」由四五段各自内联的解析链分别决定（来源会话 / 团队路由 / 默认群 / `getDefaultChat`），同一条命令的两张卡可以分到两个群。这正是 `feishu-per-team-notification-routing` 归档时记下的两条教训——「机制建齐、只接一个调用点＝运营视角的静默失败」「逐处手工注入依赖＝同类失败的温床」——在评论侧的重演。

## What Changes

- **收敛为一条统一规则（本变更的核心）**：所有出站卡片 / 告警的投递目标 SHALL 由**一处** helper 按补集式优先级解析——**来源会话（命令触发）→ 账号团队群 → 默认群**。取代现有各处内联的解析链。用补集回落（`origin?.trim() || await resolveAccountChatId(accountId)`），不用白名单枚举。
- **推翻两条既有 MUST NOT（运营方显式定案，2026-07-16）**：
  - 审批卡不再硬绑默认（管理）群——命令触发的回来源会话，自动化的走账号团队群。
  - 运维 / 告警类同样按这条规则走——**带账号**的告警（人设未绑、验证码、边缘离线、CDP 不健康、发布熔断）投递到该账号团队群；**无账号**的（握手 config-error 等）落默认群。
  - **已知代价，运营方已接受**：审批回调**无任何权限校验**（只认 `requestId`，不校验点按者与来源群），因此「谁看得见卡＝谁能批准」；`group_route` 表**无内部 / 外部标记**，故本规则对全部已映射团队一视同仁。若将来映射外部客户群，该客户即获得批准按钮与运维可见性，**系统内无闸可拦**——此约束 SHALL 在 spec 中显式记载，作为后续引入路由可信标记的依据。
- **评论侧补齐来源会话透传**（与发帖对称的 5 个接缝）：`DelegatedCommentPort` 两个入口 → `CommentScheduler.triggerManual` / `triggerTargeted` → `compose-approve` / `approveFacebookComment` → `CommentApprovalPort.request` 增加 chat 目标字段；执行器三条评论分支透传 `task.originChatId`。
- **手动 `/comment` 终态结果卡回来源会话**（对齐 `/publish`，销 backlog 86.18）。
- 诚实红线不动：投递失败绝不当成功（发送失败记日志 + 保持诚实待审态）；`AC-PUB-*` 免审 / 人审闸逐字不动——本变更只改**卡发到哪**，不改**谁能批 / 批了才发**。
- **仅云端**（`aidcp-cloud`），边缘不动，协议不动。

## Capabilities

### New Capabilities
<!-- 无新增能力，均为既有能力的要求修改 -->

### Modified Capabilities
- `feishu-notification-routing`: 把「审批卡 / 运维告警 MUST NOT 按账号路由、SHALL 维持默认（管理）群」整条要求**替换**为统一的「来源会话 → 账号团队群 → 默认群」优先级规则；显式记载「审批回调无权限校验 + 路由无内外部标记」这一已接受的暴露面。
- `user-delegated-tasks`: 「命令触发的委托任务必须捕获来源会话并回投操作员向卡片」中的**操作员向卡片**范围从「内容审批卡、发帖终态卡」**扩展到评论审批卡与评论终态结果卡**；补一条评论路径的回归场景，堵住「只修一半」的复发。
- `publish-pipeline`: 审批卡目标解析从「来源会话 → 默认群」**扩展为**「来源会话 → 账号团队群 → 默认群」，使自动 / 排期发帖的审批卡进入账号团队群。

## Impact

- 代码（`aidcp-cloud`）：`src/server.ts`（统一 helper；评论审批端口 2434；`postResultCard` 3119）、`src/agents/comment-approval-gate.ts`（端口入参加 chat 目标）、`src/comment-agent/{comment-scheduler,compose-approve}.ts`（两个 trigger 入口 + 两条 approve 路径透传）、`src/delegated-task/executors.ts`（`DelegatedCommentPort` 加字段 + 三条评论分支透传）、`src/publish-agent/roles/publish-executor.ts`（`resolveApprovalCardTarget` 加团队回落）、`src/comm/handler.ts`（边缘发起审批卡依赖类型扩到账号路由）。
- 数据：**无迁移**。`delegated_tasks.origin_chat_id` 列已存在（`f248a1e` 已加），评论任务已在写入该列——本变更只是把它读回来。`group_route` 表结构不动。
- 热点文件：**均不涉及**（两份 `protocol.ts` / `command-bridge` 动作映射 / `role-catalog` / `risk-state-machine` 都不碰），可与其他并行流同时进行。
- 行为面：命令触发者「在哪下、结果回哪」可预期；团队只在自己群里看到自己账号的全部流量（含审批与告警）。默认群从「什么都收」收敛为「无账号归属的兜底」。
- 回归风险集中在**回落链**：账号未绑团队 / 团队键未命中路由 / 读路由失败 → 必须仍落默认群、绝不静默丢卡。
- 测试（克制）：统一 helper 的三档优先级 + 读失败回落；评论审批卡按来源会话 / 团队群 / 默认群三分支；手动 `/comment` 终态卡回来源会话；自动发帖审批卡走团队群。安全红线 `AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 不受影响、须全绿。
