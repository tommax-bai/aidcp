## Why

客户端的慢启动入口按 Facebook 环境展示和操作，但云端当前把开关起点持久化在 `accounts.slow_start_since`，导致环境更换登录账号后设置丢失、旧账号离开环境后仍携带设置。账号与环境在运行时是一对一关系，产品配置应属于稳定的环境，而账号只应是该环境当前的执行对象。

## What Changes

- 将慢启动事实源从账号记录迁移到 `client_environments` 环境记录，开关、起点和 7 天进度均随 `envKey` 保留。
- customer-auth 的 env-scoped 读写直接授权并更新环境设置，不再把环境解析为账号后写账号字段；请求仍不接受 `accountId`、`since` 或其它选择器。
- 风控热路径通过当前环境↔账号一对一映射读取环境慢启动起点；环境换绑账号后，新账号立即继承该环境设置，旧账号立即不再受该环境设置影响，且无需重启。
- 环境尚未绑定账号时仍可保存并读取慢启动设置；投影明确区分“环境已开启”与“当前无账号、尚未实际生效”，不编造配额或绑定效果。
- 迁移现有账号级值到当前绑定环境以保留已配置状态；旧 `accounts.slow_start_since` 停止参与新读写和 clamp，但暂留作可回滚数据，不在本变更执行破坏性删列。
- 保持 Facebook 平台边界、7 天曲线、自然日对齐、全局停用闸以及“曲线与风控档位取更严者”的计算规则不变。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `client-customer-auth`: 慢启动 env-scoped API 从“环境授权、账号持久化”改为真正的环境级持久化，并支持未绑定环境保存设置。
- `interaction-risk-gating`: 慢启动 clamp 的显式起点从账号字段改为当前绑定环境字段，并定义换绑、冲突和迁移行为。
- `edge-companion-ui`: 客户端按环境展示慢启动配置，在未绑定账号时诚实区分“已配置”与“未生效”。

## Impact

- `aidcp-cloud`: `client_environments` schema/内存镜像、环境注册与换绑同步、customer-auth 慢启动路由、RiskController nurture provider、服务接线及相关测试。
- `aidcp-edge`: 慢启动投影与文案的未绑定环境态、聚焦 renderer/API 测试；API 路径和请求体保持不变。
- 数据：新增可空的环境级慢启动起点，并从当前绑定账号回填；旧账号列不再是运行时事实源。
- 协议：`ui.snapshot.dailyUsage.slowStart` 的字段形状保持兼容，但语义从账号级改为选中环境级；customer-auth 回包允许未绑定环境携带配置态但不携带伪造的生效配额。
