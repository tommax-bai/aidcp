## Why

Facebook 规则模式已经由 Cloud 持久化、执行并在管理后台提供开关，但桌面客户端无法查看或更改当前环境的配置，运营员必须离开账号工作现场进入后台。需要在客户端慢启动开关附近提供同一份 Cloud 权威配置的环境作用域入口，让两个互斥运行事实在同一处可见。

## What Changes

- 在桌面客户端 Facebook 环境的每日用量脚注区、慢启动开关附近增加“规则模式”开关；非 Facebook 环境不展示。
- 通过 customer-auth 增加按当前客户环境读取和写入规则模式的接口；客户端只提交 `envKey + enabled`，账号归属、平台支持和持久化目标均由 Cloud 解析。
- 客户端按 Cloud 写后回读呈现开关，不做乐观成功；未知、未绑定、不支持、接口不可用和写入失败不得显示为“已关闭”或“已生效”。
- 保持 Cloud 为规则模式的唯一配置与运行权威。客户端不保存本地规则开关、不启动本地规则计数器，也不改变慢启动优先于规则模式的现有仲裁。
- 开关允许在环境内核停止时读取和写入，只依赖客户登录、环境归属和持久账号绑定；这与纯 Cloud 配置的生效边界一致。

## Capabilities

### New Capabilities

- `client-facebook-rule-mode-toggle`: 定义客户桌面端对 Facebook 规则模式的环境作用域读写、慢启动邻近呈现、非乐观状态和 Cloud 权威边界。

### Modified Capabilities

无。

## Impact

- **Control**：新增客户端规则模式 OpenSpec 契约与交付记录。
- **Cloud**：扩展 customer-auth API，复用既有 `FacebookRuleModeStore`，按客户拥有的 `envKey` 解析唯一绑定账号并校验 Facebook 平台。
- **Edge**：增加具名 IPC/preload 方法和客户端静态开关行，复用慢启动行的离线读取、写后回读、环境切换隔离和失败呈现模式。
- **Data / protocol**：不新增迁移，不修改边云 WebSocket 协议，不复制规则进度或风险权威。
- **Delivery**：Cloud 运行时变更验证后部署 DEV；Edge 仅交付源码，不构建安装包、不声明已安装客户端可用；OL 与真实 Facebook 写入不在范围内。
