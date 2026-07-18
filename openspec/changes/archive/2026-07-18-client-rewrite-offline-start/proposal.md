## Why

客户端从精选内容发起洗稿时，云端已经能通过昨天落地的持久环境账号绑定确认目标账号，但当前入口仍要求浏览器在线，导致纯云端的内容生成在浏览器未启动时被 `binding_unverified` 提前拒绝。洗稿只生成并落库候审稿，真正的平台发布发生在后续审批与下发阶段，因此在线前置应放在需要浏览器兑现的平台动作处，而不是洗稿任务创建处。

## What Changes

- 客户端按已归属、已绑定环境发起精选内容洗稿时，使用持久绑定解析出的账号创建 `review` 模式任务，不再要求该账号此刻存在活浏览器会话。
- 保留环境归属、绑定未知、跨客户争用、悬空账号和绑定查询失败的现有 fail-closed 语义；客户端仍不得提交或选择 `accountId`。
- 保留候审与发布边界：洗稿产物仍为 `pending_approval`，不得因离线启动洗稿而免审或宣称已发布。
- 真正需要向平台下发时仍必须解析到活边缘；浏览器离线时不得广播、不得猜测执行端、不得伪造发布成功。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `client-customer-auth`: 将“由精选内容发起洗稿”从必须活会话佐证的不可逆写中拆出，允许经持久环境账号绑定离线创建必审洗稿任务，同时保留最终平台下发的在线前置。

## Impact

- `aidcp-cloud/src/client-auth/client-auth-server.ts`: 调整客户端精选内容 `create-post` 路由的绑定判据与注释。
- `aidcp-cloud/test/client-auth-server.test.ts`: 增加浏览器离线但持久绑定有效时可创建洗稿任务的回归覆盖，并保持通用发布类委托任务的在线拒绝覆盖。
- 无协议字段、Edge IPC、数据库 schema 或客户端安装包变化；运行时行为变化需部署到 `dev`。
