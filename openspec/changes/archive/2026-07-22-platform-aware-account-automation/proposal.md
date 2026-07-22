## Why

“账号内容自动化”当前把所有账号按同一组发帖、评论、联系评论字段呈现，随着 Facebook、视频号等平台接入，这会把不受支持的动作伪装成可配置能力，也无法为 Facebook 后续的自动加群提供清晰入口。需要把页面和服务端契约升级为平台感知，同时保留统一的账号自动化入口。

## What Changes

- 将现有“账号内容自动化”页升级为平台感知的“账号自动化”视图，提供“全部平台 / 小红书 / Facebook / 视频号”筛选。
- “全部平台”只展示跨平台公共摘要；选中单个平台时，仅展示并允许编辑该平台服务端声明支持的自动化动作与限额。
- 内容排期目录接口为每个账号返回规范化平台及服务端权威的可用自动化动作，不由 Console 自行猜测。
- 账号自动化写接口按账号平台校验动作字段；对不支持动作的开启或配置写入整块拒绝并返回可区分错误，不能只靠前端隐藏。
- 保留现有三态周历、总开关、错峰和 fail-closed 行为；本变更不新增 Facebook 自动加群执行逻辑，也不改变协议或 Edge 行为。

## Capabilities

### New Capabilities

<!-- None. This change evolves existing account automation and panel contracts. -->

### Modified Capabilities

- `content-schedule`: 账号自动化目录和管理视图按平台声明、筛选并呈现各平台支持的动作。
- `console-panel-api`: 内容排期目录增量返回规范化平台与服务端权威动作能力投影。
- `console-write-operations`: 内容排期写通道按账号平台整块拒绝不受支持的动作配置。

## Impact

- Cloud：平台注册表、内容排期目录 DTO/查询和写入校验。
- Console：内容排期 API 类型、平台筛选、跨平台摘要与平台专属动作列，以及相应测试。
- Control：更新上述 OpenSpec 行为契约；不涉及数据库迁移、Edge 命令或 protocol v2。
