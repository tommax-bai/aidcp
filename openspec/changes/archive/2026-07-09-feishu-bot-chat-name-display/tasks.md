<!-- 代码落 aidcp-cloud 8ca2006 / aidcp-console 998ca69，2026-07-09 部署 dev 并验证。 -->

## 1. aidcp-cloud — 飞书群名获取

- [x] 1.1 `FeishuMessenger.listChats()`：调 `GET im/v1/chats`（复用 tokenManager；分页 page_size=100 + page_token，MAX_CHAT_PAGES=20 上限）；返回 `[{chatId,name}]`；HTTP 非 2xx / code≠0 抛错供降级（绝不静默空）。 <!-- aidcp-cloud 8ca2006 -->
- [x] 1.2 `src/server.ts` `botChatsProvider`：实时 `messenger.listChats()` + `resolveDefaultChatId` 算 `defaultChatId`，合出 `{chats,defaultChatId,source:'feishu'}`，60s 缓存；飞书失败降级 `botChatStore.listActive()`（`source:'store'`、name=chatName、defaultChatId 尽力解析），不缓存降级（下次重试）。 <!-- aidcp-cloud 8ca2006；dev restart 后 route 已连线 -->

## 2. aidcp-cloud — 面板路由响应扩展

- [x] 2.1 `src/panel/types.ts` 加 `botChats` provider 依赖；`panel-server.ts` `GET /api/bot-chats` 优先用 provider，未注入回落 `botChatStore.listActive()`（老形状兼容）；响应 `{chats:[{chatId,name,isDefault}],defaultChatId,source}`。 <!-- aidcp-cloud 8ca2006 -->

## 3. aidcp-console — 群名展示

- [x] 3.1 `src/types/api.ts`：`PanelBotChat` 改 `{chatId,name,isDefault}`；新增 `PanelBotChatsResponse{chats,defaultChatId,source}`；`useBotChats` 返回类型更新。 <!-- aidcp-console 998ca69 -->
- [x] 3.2 `NotificationRoutesPage.tsx`：下拉/映射以群名为主（`name ?? chatId`），chatId 悬浮小字可复制；顶部提示条「未映射 → 默认群：<群名/id>」；`source==='store'` 时黄条提示补 `im:chat:readonly` 权限。 <!-- aidcp-console 998ca69 -->

## 4. 测试

- [x] 4.1 cloud 单测：`listChats()` 分页聚合 + code≠0 / HTTP 非 2xx 抛错。 <!-- aidcp-cloud 8ca2006 test/feishu-list-chats.test.ts -->
- [x] 4.2 panel 路由单测：provider 注入 → name/defaultChatId/source=feishu；未注入 → 回落 store。 <!-- aidcp-cloud 8ca2006 test/panel-bot-chats.test.ts -->
- [x] 4.3 console：NotificationRoutesPage 展示（并入既有 18 文件套件全绿）；typecheck + build。 <!-- aidcp-console 998ca69 -->
- [x] 4.4 全量绿：cloud test:acceptance + test(1640) + typecheck；console test(18 files) + build + typecheck。 <!-- 8ca2006 / 998ca69 -->

## 5. 部署与验收

- [x] 5.1 dev 部署（探 ECS 无并发在写 → 干净 git archive 快照 → 备份 → rsync → restart → healthcheck；console 干净 worktree build → 备份 → rsync 无 --delete；不碰 isales）。 <!-- 2026-07-09 deployed dev：cloud 8ca2006 / console 998ca69 -->
- [x] 5.2 验证：service active + 8787 + `GET /api/bot-chats` 已连线（401）+ listChats 代码在 ECS + 无异常日志；console 新 bundle 上线。**注：当前飞书应用未加 `im:chat:readonly` → 降级 source=store（显示 id）；加权限后自动显示真实群名。** <!-- 2026-07-09 dev -->
- [x] 5.3 真机项登记 backlog 簇 20（新增群名显示两条：加 im:chat:readonly 后群名显示 / 缺权限降级提示）。 <!-- 簇 20 补充 -->
