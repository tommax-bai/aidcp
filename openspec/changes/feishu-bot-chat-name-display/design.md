## Context

`GET /api/bot-chats`（change feishu-per-team-notification-routing 引入）当前只读 `bot_chats` 表（`listActive()`），而 `bot_chats.chat_name` 长期为空——飞书「机器人进群」事件不带群名。故后台只能显示 opaque `chat_id`。飞书提供 `im/v1/chats`（获取机器人所在群列表）可拿真实群名，需 `im:chat:readonly` 权限。

## Goals / Non-Goals

**Goals:** 后台以真实群名展示目标群；标明默认（兜底）群；飞书取名失败优雅降级、不崩、诚实标来源。

**Non-Goals:** 不改路由键（仍 opaque chat_id）；不改投递解析 / 入站闸；不物化群名进库（实时取 + 短缓存即可，避免与飞书真态漂移）。

## Decisions

- **D1：实时取 + 短缓存，不物化**。`GET /api/bot-chats` 实时调 `im/v1/chats`（分页取全），进程内 ~60s 缓存。理由：群名/成员随时变，实时取避免库内陈旧；不改「机器人进群」写库路径（那条本就拿不到名）。
- **D2：优雅降级回 `bot_chats` 表**。飞书调用 best-effort：失败（缺权限 / 网络 / 限频）→ 回落 `botChatStore.listActive()`，`source='store'`（名可能空）。绝不空列表、绝不抛崩页。前端据 `source` 提示补权限。
- **D3：`defaultChatId` 服务端解析**。复用既有默认链（`bot_chats.is_default` → `FEISHU_CHAT_ID`）算出并随响应下发；无则 null。前端据此渲染「未映射 → 默认群」。
- **D4：`listChats()` 复用 `FeishuTokenManager`**。加在 `FeishuMessenger`（已持 tokenManager + fetch 的 IM API 客户端）上，避免另起 token 管理；分页循环有界（page_size=100 + page_token，设最大页数上限防异常无限翻页）。

## Risks / Trade-offs

- **[缺 `im:chat:readonly` 权限]** 名取不到 → 降级显示 id。→ 缓解：`source=store` 前端明确提示需补权限；加权限后自动生效，无需改代码。
- **[飞书限频 / 慢]** 每次开页打飞书。→ 缓解：60s 进程缓存；失败降级不阻塞。
- **[分页异常]** → 缓解：最大页数上限 + best-effort（异常即用已取到的部分或降级）。

## Migration Plan

纯读增强，无 schema、无迁移。部署后：有权限即显示真实群名；运营需在飞书开发者后台给应用勾选 `im:chat:readonly` 权限（一次性）。回滚 = 前端仍容忍旧响应（name 缺省回落 id），后端降级路径等价旧行为。
