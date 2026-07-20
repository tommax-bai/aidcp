## Context

视频号 interaction 发送路径目前在 Cloud 先执行通用 `RiskController.explain(comment|dm_reply)`，随后再执行 reply policy 的账号分钟/小时/每日限额和同会话冷却；创建 attempt 的账号级事务又原子复核后者。通用 `dm_reply` 三档默认额度为零，而初始化 reply policy 的三窗口也为零，因此运维还必须在两处填入数字才能放行。通用 `comment` 数字来自主动社交互动语义，也不适合直接约束入站客户回复。

草稿生成、编辑和批准只修改 Cloud 已持久化的 job，却仍要求平台授权当前为 active。人工审核发送和无人值守自动发送也共同等待新登录冷却。客户端把 Cloud 为审计而分开的 `approval_required → approved → queued` 逐步暴露成两个按钮；Console 则把六个内部限速数字全部作为普通设置展示。

## Goals / Non-Goals

**Goals:**

- 视频号回复只有一套数量准入，且事务内最终防并发超额保持不变。
- `RiskController` 仍是最终风险状态单写者，未知风险拒因继续 fail closed，平台确认后的真实动作继续记账。
- 人工工作流能在离线/重新鉴权期间准备草稿，并在身份恢复后直接审核发送。
- 普通用户通过一次审核发送动作和限速预设完成常用工作，内部状态与高级控制仍可排障。
- 旧配置不被静默扩权，未主动保存时维持原值。

**Non-Goals:**

- 不修改 WS v2、数据库 schema、attempt 状态机、幂等键、单飞或 ambiguous 回查。
- 不开放图片私信，不放宽账号归属、客户权限、平台身份或写 capability。
- 不重做账号级连续失败熔断；该模型的渠道化与自动半开另立 change。
- 不构建或发布 Edge 安装包，不触达 `ol`。

## Decisions

### 1. Interaction limiter 单独负责视频号回复数量

Cloud 对 `comment` / `dm_reply` 继续取得 `RiskController.explain` 结果，但只有非 `quota:*` 的拒因阻断发送。这样 `state:restricted`、`state:frozen` 和未来未知拒因仍 fail closed，通用分钟/小时/每日 quota 不再成为第二套数量闸。自动入队和人工派发使用同一判据。

视频号数量上限只由 reply policy 的 `accountPerMinute`、`accountPerHour`、`accountPerDay` 与 `threadCooldownSeconds` 决定，并继续在 attempt 创建事务的账号 advisory lock 内原子复核。平台 `confirmed` 后仍调用 `RiskController.record` 保存真实动作事实，但其“是否落在通用 quota 内”的返回值不再被解释为视频号策略结果。

备选方案是给 `dm_reply` 和视频号 `comment` 再维护一套 `quota_config` 默认值。它仍保留两个配置入口和两个用量口径，因此拒绝。

### 2. 新配置默认可用，旧配置不静默扩权

新建 reply policy 使用保守预设：`2/min`、`20/hour`、`100/day`、同会话 `60s`、自动发送新登录冷却 `600s`、连续失败阈值 `3`。发送、渠道和自动化开关仍默认关闭，所以初始化本身不产生写权限；管理员选择人工审核并显式启用发送后不需要再猜三组非零数字。

Console 另提供标准预设：`4/min`、`60/hour`、`300/day`、同会话 `30s`、自动发送新登录冷却 `300s`、连续失败阈值 `3`。任何不逐位匹配预设的历史值显示为“自定义”。打开页面只做投影，不自动改写；历史零值只有在管理员主动选择预设并保存后才变化。

### 3. 新登录冷却只保护无人值守自动发送

是否自动以 job 缺少人工 `approvalActor` 为准。自动候选在生成和派发阶段都必须经过登录冷却；人工批准 job 跳过该冷却，但仍检查当前 active auth、identity、capability、运行开关、熔断、interaction limiter、CAS、幂等和 Edge 唯一路由。

人工审核本身提供了新登录后的人为确认，继续叠加固定等待不能证明更多身份事实。若身份或 capability 未确认，真实发送门禁仍直接拒绝。

### 4. 草稿生命周期不依赖平台在线状态

生成、编辑和批准根据已鉴权客户 API 的环境 scope、job/message 归属、published config、文本门禁和 CAS 工作，不读取当前平台 auth。自动入队不是草稿动作，仍由完整发送准入决定。这样登录过期不会阻止处理已经安全持久化的历史互动，也不会把“能编辑草稿”误写成“能向平台发送”。

### 5. 一次用户动作，保留两个后台事实

Electron 在 `approval_required` 上显示“审核并发送”或“保存并审核发送”。handler 先在需要时保存草稿，再调用现有 approve API；仅当返回 job 确认为 `approved` 时，使用返回的新 version 调用现有 send API。任一步失败立即停止，显示该步真实错误；approve 成功但 send 失败时状态保持“已批准，尚未发送”，不得显示绿色发送成功。

不新增组合 Cloud API。现有 CAS 和审计足以保证两步串行，避免扩大服务端协议面；用户仍可在重试时从 `approved` 状态直接发送。

### 6. Console 预设优先，数字进入高级设置

安全页默认展示当前档位、简短额度摘要和“保守 / 标准 / 自定义”选择。选择保守或标准会确定性替换完整 `rateLimits`；选择自定义只展开现有六个字段，不自行改值。高级设置始终可展开查看真值，保存仍写现有 policy draft，发布边界与 runtime controls 不变。

## Risks / Trade-offs

- [忽略通用 quota 后视频号发送量上升] → interaction limiter 仍在派发前与事务内双重检查；默认使用保守预设，旧配置不自动扩权。
- [未来 `RiskController` 增加新拒因] → 仅 `quota:*` 被识别为数量重复，所有未知拒因默认阻断。
- [组合审核发送的第二步失败] → 保留 `approved` 真态和可重试发送入口，不回滚或伪造未批准。
- [离线草稿基于旧互动] → message lifecycle、配置版本、最终文本和真实发送时 auth/capability 仍重新校验。
- [预设数字被误认为平台安全保证] → UI 明确标注为 Cloud 本地节流，不声称来自平台官方限制。

## Migration Plan

1. 先部署 Cloud：新默认与准入兼容旧客户端，现有配置不改写。
2. 部署 Console 静态资源：预设只影响主动保存的 draft。
3. Edge 仅提交源码并通过测试，不构建安装包；dev unpackaged 客户端更新后出现组合动作。
4. dev 核验配置初始化、人工发送准入与只读/健康状态；不以 shadow/gated 结果冒充真实平台发送。
5. 回滚时依次回退 Console、Edge、Cloud 提交；无 schema/data migration 需要逆向操作。

## Open Questions

无。预设数值为本 change 的产品默认，后续如需按账号规模动态分档另立 change，并先取得真实用量证据。
