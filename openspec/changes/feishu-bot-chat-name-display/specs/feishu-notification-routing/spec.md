## ADDED Requirements

### Requirement: 机器人所在群清单取真实群名并优雅降级

`GET /api/bot-chats` SHALL 实时从飞书「获取机器人所在的群列表」接口（`im/v1/chats`，分页取全）解析每个群的**真实群名**返回，使后台以群名展示、而非仅 opaque `chat_id`。当飞书调用失败（缺 `im:chat:readonly` 权限 / 网络 / 限频）时，系统 MUST NOT 返回空列表或抛错致整页失败，SHALL **优雅降级**回本地 `bot_chats` 表（群名可能为空），并在响应中标明数据来源（`source`：`feishu` / `store`），供前端在降级时提示需补权限。为避免频繁打飞书，群名列表 MAY 加进程内短缓存（秒级）。绑定目标仍为 opaque `chat_id`——群名仅用于展示层，MUST NOT 参与路由键或引入枚举。

#### Scenario: 有权限时返回真实群名

- **WHEN** 飞书应用具备 `im:chat:readonly` 权限，运营打开路由配置
- **THEN** `GET /api/bot-chats` SHALL 返回各群的真实 `name` 与 `chatId`，`source` 为 `feishu`
- **AND** 后台 SHALL 以群名为主展示目标群

#### Scenario: 缺权限 / 调用失败时降级不崩

- **WHEN** 飞书群列表调用因缺权限或网络失败
- **THEN** 系统 SHALL 回落本地 `bot_chats` 清单（`name` 可能为空、退回显示 `chatId`），`source` 为 `store`
- **AND** MUST NOT 返回空列表或让路由配置页报错崩溃

### Requirement: 机器人所在群清单标明默认群

`GET /api/bot-chats` 响应 SHALL 标明**默认群** `defaultChatId`（按既有默认解析链：`bot_chats.is_default` → `FEISHU_CHAT_ID`），使后台能一眼看出**未映射账号通知的兜底目的地**。当无任何默认群可解析时，`defaultChatId` SHALL 诚实为 null（而非臆造）。

#### Scenario: 后台展示未映射账号的兜底默认群

- **WHEN** 运营打开路由配置页
- **THEN** 响应 SHALL 带 `defaultChatId`，前端据此展示「未映射的账号 → 默认群：<群名 / id>」
- **AND** 当默认群在群名清单中有名时，SHALL 以群名展示该默认群
