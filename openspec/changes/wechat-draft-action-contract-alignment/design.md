## Context

客户工作区把互动草稿分为两层动作：生成、编辑、批准属于 Cloud 中的草稿生命周期；点击发送或自动发送才会触达视频号平台。Edge 已按公开契约请求 `/replies/:jobId/draft`，并在界面中只用平台写能力禁用发送按钮。Cloud 当前实现却在路由和工作流两处偏离该边界：草稿保存路由少匹配了 `/draft` 段，回复工作流又在所有草稿动作前要求平台写能力。

客户环境越权仍通过现有环境作用域和资源归属检查隐藏为 `404`；渠道授权失效仍阻止草稿动作。此次变更只移除“平台写能力”对纯 Cloud 草稿动作的过早限制。

## Decisions

### Make the documented draft route canonical

Cloud SHALL 精确匹配 `PUT /environments/:envKey/replies/:jobId/draft`，从第四个路径段取得 `jobId`。未带 `/draft` 的旧内部形态不作为兼容别名，避免继续形成双契约。

### Separate draft-session admission from send capability

回复工作流中的生成、编辑与批准继续校验渠道授权为 `active` 且存在已确认身份，但不再读取 `commentsReply`、`dmSendText` 或 `dmSendImage` 决定是否允许纯 Cloud 草稿动作。环境归属、互动归属、配置完整性、状态机与 CAS 版本检查保持原样。

平台写能力仍由发送编排器在真实发送前检查。自动发送只有在该能力及既有运行控制、熔断、暂停、风险和幂等条件全部满足时才可入队或派发。

### Keep permission copy aligned with the actual boundary

客户作用域越权继续使用资源不可见语义。Edge 对显式 `INTERACTION_PERMISSION_DENIED` 不再解释为“当前登录没有权限”，而是提示平台尚未确认当前操作所需的渠道能力。发送按钮仍由能力快照预先禁用。

## Testing

- Cloud 客户 API 测试固定 `/replies/:jobId/draft` 可达，并拒绝未带 `/draft` 的旧形态。
- Cloud 回复工作流测试覆盖活动授权但平台写能力为 false 时仍可生成、编辑和批准草稿，授权非活动时仍阻止这些动作。
- Cloud 发送编排器测试继续证明平台写能力为 false 时不会实际发送。
- Edge 测试固定草稿保存路径和平台能力错误文案，并证明无发送能力时只有发送被禁用。
- 运行 Cloud/Edge focused、acceptance、full tests 与 typecheck。
