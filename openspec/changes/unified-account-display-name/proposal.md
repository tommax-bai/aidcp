## Why

客户端人工昵称目前只存在 Edge 本地环境花名册，管理后台、飞书通知和指令仍各自读取平台昵称、运营标签或裸账号 ID，导致同一账号跨入口显示不一致。需要把人工命名升级为 Cloud 账号级运营别名，并由一个统一解析器向所有人类可见入口提供名字与来源，同时保持平台真实昵称和机器身份不被污染。

## What Changes

- 在 Cloud 账号主数据中新增独立的账号级运营别名；显示优先级统一为运营别名 → 平台真实昵称 → 运营标签 → 账号 ID，解析器同时返回来源。
- 客户端环境昵称编辑通过客户鉴权下的窄接口，把已归属且已绑定账号的人工别名同步到 Cloud；页面先进入 pending，任一本地或 Cloud 写入失败都恢复提交前状态并提示真实原因。
- 人工提交空内容改为“清除人工昵称”：删除本地 `nameSource: manual` 和 Cloud 运营别名，然后按系统昵称规则回落；清除失败恢复原人工昵称。
- 管理后台账号列表及所有只拿 `accountId` 的账号展示入口改为消费 Cloud 已解析的 `displayName` / `displayNameSource`，不在 Console 重复实现优先级。
- 飞书审批、告警、指令回执、委托任务及昵称选号统一经 Cloud 账号显示名目录取名；机器回调、路由、风控、任务归因继续只用稳定 `accountId`。
- 平台验证得到的昵称仍只更新 `accounts.nickname`，MUST NOT 覆盖运营别名；运营别名也 MUST NOT 参与身份确立或改写账号主键。

## Capabilities

### New Capabilities

- `account-display-name`: 定义 Cloud 账号级运营别名、统一显示名解析优先级、来源语义及机器身份隔离。

### Modified Capabilities

- `client-customer-auth`: 增加客户只能为自己已归属、已绑定账号的环境设置或清除运营别名的窄写接口。
- `edge-fleet-console`: 人工昵称保存扩展为本地与 Cloud 一致确认，空内容清除人工来源并回落系统昵称。
- `console-panel-api`: 账号 DTO 暴露 Cloud 统一解析后的显示名与来源，Console 所有账号展示统一消费。
- `feishu-command-ingestion`: 飞书昵称选号统一接受账号目录提供的运营别名/平台昵称候选，并按统一显示名回执。
- `feishu-notification-routing`: 飞书人类可见通知统一使用账号目录显示名，路由与机器载荷继续使用账号 ID。

## Impact

- `aidcp-cloud`: `accounts` additive 字段、自愈建列、账号显示名解析器与缓存、客户环境别名写接口、panel DTO、飞书通知与昵称选号装配。
- `aidcp-edge`: Electron 昵称 IPC、客户鉴权请求、空值清除语义、pending/失败回滚和环境显示名回落。
- `aidcp-console`: `PanelAccount` 类型、统一账号名消费方法及相关页面/测试。
- `aidcp`：OpenSpec 契约与必要的架构/协议说明；不新增 Edge↔Cloud WebSocket 消息类型。
- PostgreSQL 仅做 additive 自愈加列，不删除或重写现有 `nickname` / `label` 数据。
