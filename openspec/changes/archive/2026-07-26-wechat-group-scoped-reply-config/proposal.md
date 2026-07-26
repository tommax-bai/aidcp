## Why

视频号互动回复配置目前按账号独立保存和发布，同一运营分组中的账号必须重复配置，且后续修改容易产生漂移。系统已经以 `accounts.group_label` 表示账号分组，因此应让回复策略按分组复用，并为未分组账号提供一份明确的默认策略，同时继续保留账号级运行开关和风控硬门禁。

## What Changes

- **BREAKING** 将版本化回复配置的最终归属从 `accountId` 调整为稳定配置作用域：`group` 或单例 `default`；最终不再提供账号级策略覆盖。
- 以账号当前 `group_label` 解析生效策略：有分组时只使用该分组已发布策略，未分组时只使用默认已发布策略；作用域缺少已发布策略时 fail closed，不静默跨作用域回落。
- 将账号级 runtime controls、登录态、身份、capability、熔断与 `RiskController` 保持为独立硬门禁；共享策略只复用策略值，额度计数仍按账号执行。
- 为每个回复任务冻结稳定的配置作用域和不可变版本，使换组或重新发布只影响后续新任务。
- 新增分组/默认策略的管理、预览、发布、审计和账号生效来源 API；账号级策略读写 API 直接退役，不再提供兼容读取。
- 在 Console 增加“视频号策略”管理面，按默认策略和现有分组编辑；账号页移除“查看策略”和旧策略来源，仅保留独立运行控制。
- Cloud 只按 scoped 规则解析，不再支持 `legacy`/`shadow` 模式；历史账号策略数据按用户确认作为测试数据精确清理，旧策略表暂不删除以避免共享数据库上的破坏性 DDL。
- 账号表取消通用“操作”列：状态、风控、档位分别点击对应标签操作，视频号运行控制使用具名列，Facebook 配置随平台标签进入。

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
- 部署涉及 PostgreSQL 账号旧策略数据清理；`dev`/`ol` 共用数据库时必须先备份并按精确表/行数执行，不能删除运行控制、风险、互动消息或任务记录。
