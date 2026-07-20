## Why

视频号互动回复配置目前按账号独立保存和发布，同一运营分组中的账号必须重复配置，且后续修改容易产生漂移。系统已经以 `accounts.group_label` 表示账号分组，因此应让回复策略按分组复用，并为未分组账号提供一份明确的默认策略，同时继续保留账号级运行开关和风控硬门禁。

## What Changes

- **BREAKING** 将版本化回复配置的最终归属从 `accountId` 调整为稳定配置作用域：`group` 或单例 `default`；最终不再提供账号级策略覆盖。
- 以账号当前 `group_label` 解析生效策略：有分组时只使用该分组已发布策略，未分组时只使用默认已发布策略；作用域缺少已发布策略时 fail closed，不静默跨作用域回落。
- 将账号级 runtime controls、登录态、身份、capability、熔断与 `RiskController` 保持为独立硬门禁；共享策略只复用策略值，额度计数仍按账号执行。
- 为每个回复任务冻结稳定的配置作用域和不可变版本，使换组或重新发布只影响后续新任务。
- 新增分组/默认策略的管理、预览、发布、审计和账号生效来源 API；现有账号配置写 API 进入兼容迁移并停止作为最终写入口。
- 在 Console 增加“视频号策略”管理面，按默认策略和现有分组编辑；账号页展示生效来源并继续承载账号运行控制。
- 提供现有账号级配置盘点与迁移机制：一致配置可安全合并，冲突配置必须显式选择，切换前可比较新旧解析结果。

## Capabilities

### New Capabilities

- `wechat-group-reply-config`: 定义分组/默认回复配置作用域、解析优先级、不可变版本、运行时冻结、管理 API、迁移和 Console 操作面。

### Modified Capabilities

- `client-customer-auth`: 客户互动投影中的 `replyConfig` 从账号配置头调整为账号当前解析出的分组或默认配置状态，并加性暴露非敏感的生效来源。

## Impact

- Control：OpenSpec、视频号互动 internal/customer API schema、fixtures 与契约文档。
- Cloud：`ReplyConfigStore`、回复工作流、互动任务持久化、客户投影、internal API、账号下线清理、PostgreSQL migration 与相关测试。
- Console：视频号策略 API/DTO、分组策略管理页面、账号生效来源展示、现有回复设置组件拆分与测试。
- Edge 协议不变；Edge 继续只消费账号级 runtime controls，不承担策略选择。
- 部署涉及 PostgreSQL 加性 schema 与分阶段迁移；切换前不得删除现有账号级配置。
