## Context

评论审批目前由来源各自决定：普通浏览评论固定进入 `CommentApprovalGate`，排期评论携带 `review|auto_approve`，mandatory 规则携带 `comment_approval`，手工 `/comment` 与结构化委托默认回到 `review`。这让“账号已经免审”无法成为真实的账号级站立授权。

发布侧已经具备两个共享 first-writer-wins 信号的审批入口：飞书按钮回调与客户端 customer-auth HTTP。Cloud 会把所有 `review` 稿件落为 `pending_approval`，客户端可独立列出、读取并审批；`PublishExecutor` 仍默认发送飞书审批卡。现有 `group_route` 只负责 `group_label→chat_id`，不表达某分组是否需要飞书审批入口。

约束：存量行为必须默认不变；策略写入只由受内部 JWT 保护的后台完成；客户端不得自报免审；评论免审不能削弱 Cloud 风控或平台确认；隐藏飞书卡之前必须证明账号仍可由有效客户环境读取；策略读取失败时必须向更保守的可见/需审方向回退。

## Goals / Non-Goals

**Goals:**

- 让账号显式的全局评论免审成为所有评论来源的最高优先级授权。
- 让分组可选择仅客户端处理稿件审批，而不改变稿件状态机和授权信号。
- 保持存量账号/分组零行为扩张，并让每次策略解析与回退可观察、可审计。
- 复用现有账号分组、客户端归属和 customer-auth HTTP 权威边界。

**Non-Goals:**

- 不关闭评论或发布的风险、配额、去重、页面复核与平台确认。
- 不允许客户端请求体自行声明 `auto_approve_all` 或 `client_only`。
- 不把“仅客户端审核”扩展成屏蔽发布结果、失败、运维告警或飞书命令回执。
- 不改变 Edge 协议、客户端审批 IPC/HTTP DTO 或构建安装包。
- 不将本变更推广到发帖自动免审；这里只控制 `review` 稿件的飞书审批入口。

## Decisions

### 1. 使用两个窄策略表，不复用排期模式或 `group_route`

Cloud 新增单一 `ApprovalPolicyStore`，自愈创建：

- `account_comment_approval_policy(account_id PK, mode, updated_by, updated_at)`，`mode∈{source_rules,auto_approve_all}`；无行等价 `source_rules`。
- `group_publish_approval_policy(group_label PK, delivery, updated_by, updated_at)`，`delivery∈{client_and_feishu,client_only}`；无行等价 `client_and_feishu`。

两表都使用枚举约束、UPSERT + `RETURNING` 回读真态、账号/分组存在性校验和审计字段。选择独立表而不是给 `group_route` 加布尔列，是因为 `client_only` 分组可能刻意不配置任何飞书群；路由目的地与投递策略是两个正交事实。也不复用 `account_content_schedule.comment_mode`，因为排期开关只描述排期来源，不能代表普通浏览和手工命令的全局授权。

### 2. 账号全局免审是评论来源模式之上的显式覆盖

Cloud 统一解析有效模式：

```text
account mode == auto_approve_all  -> auto_approve
otherwise                         -> source-provided mode or review
```

因此显式全局免审覆盖普通浏览、排期、联系评论、mandatory、飞书 `/comment` 与委托评论；`source_rules` 保持今天所有来源规则不变。该设计避免迁移时把已有“排期局部免审”静默扩大成账号全局免审，也避免把存量 mandatory 授权收紧。

全局免审在授权边界直接生效；免审通知是无批准/拒绝按钮的旁路可观测消息，带账号、目标和正文预览，来源为飞书命令时回来源会话，否则按账号团队群解析。评论提交链不等待通知，通知缺失或发送失败只记日志，既不阻止提交，也不回退为审批卡。最终成功仍只来自边端/平台确认。

不选择把 `/comment` 永久固定为人审，因为它与“账号全局免审”语义冲突，而且受权飞书命令本身已是一层显式操作员意图；现有 `manualOverride` 只控制风控/配额的事实保持不变，审批是否等待改由有效模式单独决定。

### 3. 分组仅客户端策略只抑制无来源会话的 `review` 审批卡

`PublishExecutor` 仍先持久化 `pending_approval`，随后在发送飞书审批卡前解析：

1. 有 `originChatId`：始终回来源会话，分组策略不抑制。
2. 无来源会话且分组为 `client_and_feishu`/无策略：照常发送。
3. 无来源会话、分组为 `client_only` 且账号可由启用客户的活跃环境经现有 customer-auth 绑定触达：不发按钮卡，记录 `suppressed_by_client_only_policy`，客户端队列成为主动审批入口。
4. 策略读取失败、账号未分组、客户端归属/绑定不可证或客户被禁用：回退发送飞书卡并记录具名原因。

该决策只应用于 `review` 卡。`auto_approve` 的通知卡、发布结果、失败和运维告警继续走统一消息路由。客户端离线不触发回退：稿件是 HTTP 持久数据，离线不等于不可达；只有授权归属不可证才回退。

### 4. 客户端可审批判据复用现有授权事实

`ClientUserStore` 新增账号反向只读判据，基于启用 `client_users`、`source='admin'` 的 `client_env_scope`、活跃 `client_environments` 和现有账号绑定查询 `EXISTS`。缺表、争用或查询异常都返回不可证/向上抛给发送决策回退，绝不以“客户端最近在线”作为业务数据可达性的前置条件。

不检查 Edge 版本或 WebSocket 在线状态：现有客户数据面合同已经规定稿件读取和审批不依赖自动化引擎；若安装包过旧，管理员应保留默认双通道，不能让 Cloud 用不可靠的在线启发式猜版本。

### 5. 后台用一个“审批与通知策略”模型展示生效态

Panel 提供窄 API 读取/写入账号和分组策略；写入校验账号/分组存在、枚举合法并回读真态。Console：

- 账号表显示“评论审批：按来源规则 / 全局免审”。
- 通知路由表显示“稿件审核入口：客户端+飞书 / 仅客户端”，并展示该分组活跃账号中多少具备客户审批归属。
- 选择 `client_only` 但覆盖不完整时明确提示运行时会对不可证账号回退飞书，绝不假称已完全静默。
- 修正旧文案：审批卡当前已按来源会话/账号团队群路由，并非固定默认管理群。

API 与 Console 类型使用显式字符串联合，未知未来枚举在 Cloud 写侧拒绝；读侧异常按默认值展示并带不可用提示，不以乐观缓存宣称保存成功。

## Risks / Trade-offs

- [账号全局免审扩大公开写动作权限] → 默认无行=`source_rules`，仅内部后台可写并记录操作人/时间。
- [免审通知失败降低可观测性] → 旁路发送结果记日志；通知不得拥有授权否决权，也不得失败回退为按钮审批。
- [分组仅客户端导致无人看到待审稿] → 每稿运行时验证客户授权归属；不可证或读取失败回退飞书，策略状态页展示覆盖缺口。
- [分组成员变化后策略失真] → 决策在每份稿件发送卡前现读账号 `group_label` 与客户端授权，不缓存成员快照。
- [飞书与客户端并发审批] → 继续共享 Cloud first-writer-wins 信号，后到入口返回已处理，不二次下发。
- [策略表初始化失败] → 评论回落来源规则、稿件回落双通道；启动与单次决策均记录退化原因。
- [Console 与 Cloud 枚举漂移] → 聚焦 API/类型测试覆盖未知枚举、回读真态与默认退化；不把数据库原始值直接渲染成不可控选项。

## Migration Plan

1. Cloud 先上线自愈表、默认解析与 API；空表行为与当前一致。
2. Console 上线配置入口与覆盖提示；管理员显式选择后策略才生效。
3. 在 dev 用一个测试账号验证全局免审的浏览/手工评论通知与终态，再验证双通道和仅客户端稿件各一份；不执行 OL 变更。
4. 回滚时先把策略行恢复默认，再回滚 Console/Cloud；即使只回滚代码，未知表仍无副作用，旧代码忽略它们并恢复现状。

## Open Questions

- 无；本次已确认账号全局免审必须覆盖飞书 `/comment`。
