## Context

委托发帖的 governed 路径先读取 `RiskController.getState().status`，再以 `canDo('publish')` 得到一个布尔值。`RiskController.explain()` 实际能区分威胁态拒绝与 `quota:minute|hour|day`，但 scheduler 当前丢掉该解释，只落 `risk_denied(status=normal)`；终态 humanizer 因而无法告诉运营生效配额档位和真正命中的窗口。

Console 与 Edge 的精选内容“洗稿”都是服务端专用端点在用户明确点击后创建的单篇、必审任务，但当前分别写成普通 `source=console` / `source=edge`。executor 因此把它们与通用结构化自动任务一并走 governed 风控闸。直接把所有 console/edge 发布放开会扩大权限面；把可由客户端提交的约束字段当授权标记也可伪造。

## Goals / Non-Goals

**Goals:**

- 发帖拒绝回执分别展示风控状态、配额档位与实际拒绝原因。
- 保持拒绝原因机器可读、可持久化、旧 attempt 可继续人话化。
- 仅让两个服务端专用的人工精选洗稿入口获得操作员主动指令权限。
- 人工洗稿绕过发布前风控／配额闸但保留人审；平台确认发布后仍写真实 `publish` 计数。

**Non-Goals:**

- 不修改任何账号档位、配额数字、风险状态或任务重试预算。
- 不放开自然语言、通用 Edge/Console/API 发帖、自动排期或后台自动创作。
- 不改变发布成功判据，不把“已受理／已授权”表述为平台已发布。
- 不改协议 v2、Edge/Console 客户端或数据库表结构。

## Decisions

### D1：一次解释，结构化保留拒绝事实

governed 发布使用 `risk.explain('publish')` 作为唯一判定；`CanDoResult` 在配额拒绝时同时给出窗口、已用量和生效上限。scheduler 从同一份解释构造稳定原因：

- 非 normal：`risk_status(status=<status>,tier=<tier>)`
- 配额拒绝：`risk_denied(status=<status>,tier=<tier>,cause=quota:<window>,used=<n>,limit=<n>)`

这样提示不再从 `status` 猜原因，也避免另一次读取热配置后出现原因与上限不一致。humanizer 同时保留旧 `risk_status(<status>)` / `risk_denied(status=<status>)` 兼容，历史 attempt 不受影响。

备选“只改中文模板，说可能是档位限制”被否决：它仍是猜测，无法回答命中哪个窗口。备选“scheduler 再读 effectiveQuotas”被否决：热配置可能在两次读取之间变化。

### D2：人工洗稿使用服务端可信来源，不采信客户端布尔标记

新增任务来源 `operator_action`。只有 Panel `POST /api/curated/contents/:id/create-post` 与 Client Auth `POST /curated-contents/:id/create-post` 两个专用服务端入口写该来源；通用建任务端点继续把来源收口为既有 `console` / `edge` / `api`，客户端不能自报 `operator_action`。

executor 仅在以下白名单之一成立时传 `operatorOverride=true`：

1. 既有精确 slash：`legacy_command + manualSingle`；
2. `operator_action + publish_post + 单篇目标 + 有已校验精选参照快照`。

第二项同时要求可信来源与洗稿形状，避免未来误用 `operator_action` 时把其他动作静默放开。自然语言、通用结构化发帖与自动任务保持 governed。

### D3：越权只控制前置放行，真实计数沿用统一事后事实链

`operatorOverride` 只让 scheduler 跳过发布前 `status/canDo` 判定，不修改 `RiskController.record('publish')`。平台确认发布后的既有事件订阅仍无条件写 `risk_counters`；即使该次动作在当时配额外，也记录既成事实，但不得把配额超限升级为威胁态。

备选“人工洗稿不计数”被否决：会让后续自动任务误以为仍有余额，也违反用户要求的“占用配额”。

## Risks / Trade-offs

- **[机器原因字符串变长，旧消费者可能只认识旧格式]** → humanizer 同时支持新旧格式；未知格式继续原样透传，绝不编造。
- **[过宽的操作员来源造成配额绕过]** → 来源只能由两个专用服务端入口写入，executor 再校验动作、单篇目标与参照快照。
- **[操作员越权后在受限账号上真实发布]** → 这是与精确 `/publish` 一致的主动权限语义；发布前 `review` 人审仍强制，平台成功后完整计数。
- **[热配置变更导致提示上限漂移]** → `explain()` 在同一次判定中返回 used/limit，原因与判定同源。

## Migration Plan

1. 先部署兼容新旧原因的人话化与结构化解释，再启用两个入口的新来源及 executor 白名单。
2. 无数据库迁移；旧任务 source 与旧 attempt reason 原样可读。
3. dev 验证包括：零发布配额的 governed 任务显示状态／档位／窗口／用量上限；人工洗稿可进入候选生成与人审；未真实发布前计数不变。
4. 回滚为代码回滚；已创建的 `operator_action` 任务若回滚到旧代码会因 source 联合类型只存在于编译期而仍可读，但 executor 不再越权，安全地回落 governed。

## Open Questions

无。
