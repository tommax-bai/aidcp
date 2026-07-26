## Why

自动内容排期目前由每个 Cloud 进程按分钟扫描本地在线账号并直接启动发布管线，但触发只携带 `accountId`，没有把该在线连接的 `envKey` 和当前 Cloud 的 `executionTarget` 固定下来；同库多 Cloud、进程重启或连接切换时，稿件可能由代码或文字卡配置不同的进程生成，且现有审计无法证明执行归属。

## What Changes

- 让自动发帖扫描消费经过欢迎握手的完整在线身份 `accountId + envKey`，其中 `envKey` 复用现有 `ads-<profileId>` 连接身份，不新增 Edge 协议字段。
- 由 Cloud 从严格解析的 `AIDCP_DEPLOY_ENV` 注入 `executionTarget=dev|ol`；客户端不得自报或覆盖部署目标。
- 自动发帖命中后先以 `(accountId, post, hourCell)` 做数据库原子占位，再直接启动现有发布管线；这是一张最小幂等台账，不引入待消费队列、跨 Cloud 接管或重试编排。
- 将 `envKey + executionTarget` 冻结进当轮发布上下文、候审记录元数据和运行审计，后续审批与下发只允许当前 Cloud 处理属于自身 target、且仍连接原 `envKey` 的自动稿件。
- 保留人工隔离前提：同一账号不会同时连接 dev 与 ol；不增加双在线检测、冲突仲裁或自动迁移账号归属。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `content-schedule`: 自动发帖按当前已验证连接环境和 Cloud target 触发，使用持久化小时格占位防止重启重复，并把执行归属贯穿到候审与下发。

## Impact

- Cloud：连接运行时只读在线身份、内容调度器、内容排期存储、发布触发/元数据/下发恢复与相关测试。
- PostgreSQL：增加一张只保存每账号最新自动发帖小时格的幂等台账；无破坏性迁移。
- Edge、Console、协议版本、人工发布、参照稿人工创建、排期 UI 与 ol 部署均不在本次范围内。
