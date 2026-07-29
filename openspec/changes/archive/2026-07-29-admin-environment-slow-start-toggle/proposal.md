## Why

管理后台的环境资产页目前明确为只读，无法查看或调整已经存在于 Cloud 的环境级慢启动设置；运营只能进入客户客户端操作，形成不必要的工单和权限绕行。Cloud 已将慢启动事实收口到 `client_environments.slow_start_since`，因此后台应复用同一事实源提供受内部 JWT 保护的显式开关。

## What Changes

- 在管理后台「环境」页逐环境展示慢启动状态，并为 Facebook 环境提供开启/关闭开关。
- 内部 Panel 环境资产投影 additive 返回环境级慢启动配置；新增按 `envKey` 写入 `{ enabled }` 的内部管理接口。
- 开启时由 Cloud 写入上海自然日当天 00:00 作为第 1 天起点，关闭时清空环境起点；不接受客户端提交起点、账号或平台选择器。
- 写入成功后返回写后环境真态并刷新后台列表；请求在途明确显示，失败回滚到权威值并提示错误。
- 保持环境级事实所有权：设置随环境保留，未挂载账号时也可配置，换绑账号后由既有风险链即时采用。
- 只允许 Facebook 环境开启；非 Facebook、平台未知、已删除环境或全局停用不被伪装为可生效。
- 不改变 7 天曲线、风控档位、风险状态、客户侧开关、协议或全局停用闸。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `admin-environment-lifecycle`: 环境资产页从纯只读投影扩展为可查看并操作 Facebook 环境的慢启动设置。
- `console-panel-api`: 内部 Panel 环境投影增加慢启动配置，并提供受内部 JWT 保护、按环境写同一事实源的管理接口。

## Impact

- `aidcp-cloud`: Panel 路由、环境资产 DTO、`ClientUserStore` 的内部环境慢启动写方法及聚焦测试。
- `aidcp-console`: 环境页表格、API 类型/查询 mutation、提交中与失败反馈及组件测试。
- 数据：复用现有 `client_environments.slow_start_since` 与镜像刷新机制，不新增表或列。
- 部署：Cloud 与 Console 需要同批进入 dev；接口为 additive，滚动期间旧 Console/Cloud 可继续只读运行。
