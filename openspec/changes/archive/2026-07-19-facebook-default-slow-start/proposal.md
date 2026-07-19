## Why

Facebook 环境在单个创建和批量创建完成后，当前都会以 `client_environments.slow_start_since = NULL` 注册到 Cloud，运营需要再逐个手动开启慢启动。新建 Facebook 账号最需要从第一天受每日额度曲线约束，遗漏手动操作会直接放大新号操作量；小红书和视频号没有慢启动产品概念，不能被同一默认值波及。

## What Changes

- Facebook 单个创建与批量创建都把“默认开启慢启动”作为程序化创建意图的一部分。
- Cloud 在完成新环境注册和客户归属的同一事务中写入环境级慢启动起点，起点使用服务端当前上海自然日 00:00。
- 小红书与视频号创建请求不携带慢启动意图；Cloud 对非 Facebook 的开启意图 fail-closed。
- 创建完成重试保持幂等，不重置慢启动起点，也不重新开启之后被运营手动关闭的环境。
- 客户端回执只在 Cloud 权威事务确认后声明慢启动已开启；归属未确认时如实提示，不自动删除已创建的本地环境。

## Capabilities

### Modified Capabilities

- `adspower-environment-provisioning`: Facebook 单建/批量建默认开启环境级慢启动，并保持跨平台门禁与诚实回执。
- `client-customer-auth`: 程序化环境归属完成接口原子接收并落库 Facebook 慢启动意图。

## Impact

- `aidcp-edge`: Electron 主进程环境创建/归属完成请求、创建回执和 Facebook 创建说明。
- `aidcp-cloud`: customer-auth provisioning 完成接口、`ClientUserStore` 原子注册事务及测试。
- 数据：复用既有 `client_environments.slow_start_since` 与 `slow_start_initialized`，不新增迁移或账号级字段。

