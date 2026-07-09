## Why

「通知路由」后台的目标群只显示 opaque `chat_id`（如 `oc_144e761f…`），运营看不出是哪个群。根因：群名只在「机器人进群」事件里才可能带过来，而飞书该事件**实际不带群名**，故 `bot_chats.chat_name` 长期为空，`GET /api/bot-chats` 只能回落显示 id。且后台**未展示哪个是默认群**（未映射账号的兜底目的地）。

## What Changes

- **【实时取真实群名】** `GET /api/bot-chats` 改为实时调用飞书「[获取机器人所在的群列表](https://open.feishu.cn/document/server-docs/group/chat/list?lang=zh-CN)」（`GET im/v1/chats`，分页）取每个群的**真实群名**；调用失败（缺 `im:chat:readonly` 权限 / 网络）**优雅降级**回 `bot_chats` 表（名可能为空 → 显示 id），并在响应里标 `source`（`feishu` / `store`）供前端提示。
- **【标明默认群】** 响应新增 `defaultChatId`（`bot_chats.is_default` → `FEISHU_CHAT_ID` 兜底解析），供后台一眼看出未映射账号落哪个群。
- **【后台以群名为主】** 「通知路由」页下拉与映射表**以群名为主**、`chat_id` 悬浮/次要显示；顶部加「未映射的账号 → 默认群：<群名>」提示条；`source=store`（群名不可用）时提示需在飞书后台加 `im:chat:readonly` 权限。
- **【短缓存】** 群列表加进程内 ~60s 缓存，避免每次开页打飞书。

> 非 BREAKING：仅丰富 `GET /api/bot-chats` 响应（新增 `name`/`defaultChatId`/`source`，`chatId`/`isDefault` 不变）+ 前端展示；路由映射逻辑、投递解析、入站闸均不动。**前置**：群名显示需飞书应用具备 `im:chat:readonly` 权限（运营在开发者后台勾选；未加则降级显示 id，加后自动生效）。

## Capabilities

### New Capabilities
<!-- 无新增 capability。 -->

### Modified Capabilities
- `feishu-notification-routing`: `GET /api/bot-chats` 的机器人所在群清单从「只读 `bot_chats` 表」升级为「实时取飞书真实群名 + 缺失时降级回表」，并在响应中标明默认群与数据来源，供后台以群名展示、并标注未映射账号的兜底默认群。

## Impact

- **aidcp-cloud**：`src/feishu/messenger.ts`（或新增小模块）加 `listChats()` 调 `im/v1/chats`（复用 `FeishuTokenManager`，分页 + best-effort）；`src/server.ts` 组装 `GET /api/bot-chats` 的 provider（实时名 + `defaultChatId` + `source` + 60s 缓存，失败降级 `botChatStore.listActive()`）；`src/panel/panel-server.ts` + `types.ts` 该路由响应形状扩展。
- **aidcp-console**：`src/pages/NotificationRoutesPage.tsx` 以群名为主展示 + 默认群提示条 + `source=store` 权限提示；`src/types/api.ts` `PanelBotChat` 增 `name`、响应增 `defaultChatId`/`source`。
- **红线**：飞书取名失败绝不静默空列表——降级回表并诚实标 `source`；绑定目标仍是 opaque `chat_id`（名仅展示层，不参与路由键、不引入枚举）；不触协议 / 风控 / 边缘。
- **前置权限**：`im:chat:readonly`（飞书开发者后台，运营侧一次性操作）。
