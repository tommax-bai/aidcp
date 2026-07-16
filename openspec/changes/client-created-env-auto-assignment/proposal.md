## Why

客户已登录后在客户端内明确点击“新建环境”，本机 AdsPower 已成功建号，却仍被要求管理员手工登记和分配，导致新环境不能进入运行花名册；而云端现有自动登记又要等环境先连接，形成创建后的引导闭环断点。需要在不恢复任意 `envKey` 自认领能力的前提下，让这条受控新建路径自动完成权威归属。

## What Changes

- 客户登录态下，从 Electron 主进程的程序化建号路径新建环境时，使用一次性创建意图把“这次新建”绑定到当前客户会话；AdsPower 返回真实 `userId` 后，由 Cloud 原子完成环境登记与当前客户唯一归属。
- 自动归属成功后，Edge 必须重新读取 `/my-environments` 权威真态，确认新环境已在可见集后再加入并落盘运行花名册；加入后保持离线，不自动启动。
- “加入已有环境”、手填分身 ID、普通客户请求提交任意 `envKey` 继续禁止自认领；已登记或已归属环境不得借新建接口转移 owner。
- Cloud 归属失败时如实保留“本机已创建、未完成分配”的状态，不得乐观加入花名册；支持同一创建意图幂等重试，并保留管理员分配兜底。
- 未配置代理仍只作提醒，不阻止创建、自动归属或加入花名册，也不触发自动启动。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `client-customer-auth`: 将“登录态新建环境自动归属”收窄为可信的程序化创建意图链路，并明确普通客户自报 `envKey`、已有环境认领和 owner 转移仍被拒绝。

## Impact

- `aidcp-cloud`: customer-auth 新增创建意图/完成端点；`ClientUserStore` 新增幂等、事务化的“登记 + 唯一 owner”单写方法、审计与过期意图存储；测试覆盖双客户冲突、重放、未知/过期意图和旧自绑定路由拒绝。
- `aidcp-edge`: `ads:createEnv` 在主进程内协调创建意图、本地建号、Cloud 完成归属、权威范围刷新和花名册落盘；renderer 仅消费结果，不得提交或改写待归属的 `envKey`。
- `edge-fleet-console` / `adspower-desktop-env-picker`: 恢复既有“新建成功即时入栏”契约；新环境加入后为离线态，启动仍由用户显式触发。
- 不改边云 WebSocket protocol v2，不改风险状态机，不改 console 管理员分配入口；客户端行为变更不自动触发桌面安装包构建。
