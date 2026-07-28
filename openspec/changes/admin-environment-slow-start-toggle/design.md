## Context

慢启动已经由 `environment-level-slow-start` 收口到 `client_environments.slow_start_since`：`NULL` 表示关闭，非空值是对齐上海自然日的第 1 天起点。客户侧通过 env-scoped customer-auth API 写入，`ClientUserStore` 在事务成功后刷新 `client_environment_slow_start` 镜像，已缓存的 `RiskController` 下一次同步读即可采用新值。

管理后台 `/environments` 目前只消费内部 JWT 保护的 `GET /api/environments`，`ClientUserStore.listAllEnvironments()` 没有投影慢启动字段，Panel 也没有内部写路由。Console 页面还以“只读展示环境资产及历史状态”自我描述。新入口必须写同一环境事实，不能恢复旧的 `accounts.slow_start_since`，也不能让 Console 自行生成起点或推算“已经生效”。

## Goals / Non-Goals

**Goals:**

- 让内部管理员在环境资产页查看并切换 Facebook 环境的慢启动配置。
- 未挂载账号时允许预配置；设置随环境保留，并由既有环境↔账号镜像即时进入风险计算。
- 区分“环境配置已开启”与“当前 Cloud 全局停用”，避免开关状态冒充实际 clamp。
- 写请求严格按 `envKey` 定位、服务端生成起点、回写后返回权威配置，且重复开启不重置 7 天起点。

**Non-Goals:**

- 不修改 7 天曲线、平台白名单、风险档位、风险状态或全局停用闸。
- 不新增数据库列、账号级设置、协议字段或客户侧 API。
- 不为小红书、视频号或平台未知环境开放后台开关。
- 不打包 Edge 安装器，不部署 OL。

## Decisions

### 1. 后台复用 `client_environments.slow_start_since`

Panel 新增 `PUT /api/environments/:envKey/slow-start`，请求体只接受 `{ "enabled": boolean }`。`envKey` 来自路径，起点由 Cloud 在首次开启时写为服务器当前时刻所属上海自然日的 00:00；重复提交 `enabled=true` 使用 `COALESCE` 保留原起点，关闭则写 `NULL`。

替代方案是在 `accounts` 增加后台开关，或调用客户鉴权路由。前者会重新制造“设置随账号移动”的已修复缺陷；后者要求伪造客户身份并错误跨越内部管理与客户权限边界，均拒绝。

### 2. 管理写入由 `ClientUserStore` 提供独立的内部方法

客户侧 `setEnvironmentSlowStart(userId, envKey, ...)` 必须验证客户 ownership；内部管理员不应伪造 `userId`。新增管理方法只接受 `envKey`、`enabled` 与服务端 `now`，在同一 SQL 条件写中验证环境存在、生命周期为 `active`、规范平台为 `facebook`，成功后推进 `client_environment_slow_start` 镜像版本并刷新本地镜像。

返回稳定拒绝原因，Panel 映射为 404（不存在）、409（生命周期不可写 / 平台不支持）或 503（存储不可用）。已删除或历史删除态不会因管理写入被复活。

### 3. 资产投影表达配置真态，不伪造生效真态

`listAllEnvironments()` additive 返回 `slowStart.enabled` 与 `slowStart.since`，两者直接来自环境行。Panel 在响应中再附加进程启动时解析出的 `globallyDisabled`；这是 Cloud 全局闸真态，不由 Console猜测。

页面把开关解释为“环境配置”。当 `globallyDisabled=true` 时仍如实显示已保存的勾选值，但同时标记“全局停用，当前不生效”。是否具体收紧了某个账号的某项配额仍由既有 `RiskController.slowStartView()` 负责，本页不自行计算 `binding` 或当日配额。

### 4. Console 使用写后收敛，不做成功乐观冒充

Facebook 且 `lifecycle.state=active` 的环境行显示开关；非 Facebook、平台未知和非 active 行显示“不适用”或“不可操作”。提交期间开关禁用并显示“正在开启/关闭”；成功后以 API 写后回包更新缓存并刷新环境列表，失败则保留原权威值并展示错误。

不先本地翻转为已生效，因为网络成功、数据库写入和镜像刷新是三个不同事实。提交中状态只表达请求在途。

## Risks / Trade-offs

- [Cloud 已更新而 Console 刷新失败] → 写接口返回写后配置，mutation 先更新对应缓存行再触发后台刷新。
- [重复开启意外重置为第 1 天] → SQL 使用 `COALESCE(existing_since, new_day_start)`，测试锁定幂等语义。
- [全局停用时勾选被理解为生效] → 投影显式携带 `globallyDisabled`，页面展示配置保留但当前不生效。
- [同一账号异常绑定多环境] → 本入口只写环境事实，不选择账号；既有镜像冲突检测继续 fail-closed，后台不声称 clamp 已生效。
- [Cloud/Console 滚动版本不一致] → 所有字段与路由均为 additive；新 Console 写到旧 Cloud 时明确失败并回滚显示，旧 Console 忽略新字段。

## Migration Plan

1. 先部署含 additive 读写接口的 Cloud；验证旧 Console 的环境页仍可读取。
2. 再发布 Console 静态资源；在 dev 对一个明确的 Facebook 测试环境验证开启、重复开启不改起点、关闭和全局停用文案。
3. 回滚 Console 只会失去后台入口，不改变已保存设置；回滚 Cloud 前先停用新 Console 写入口。数据列与既有客户侧功能不需要回滚。

## Open Questions

无。现有环境级事实源、平台范围与全局停用语义已由基线规格确定。
