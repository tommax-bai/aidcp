<!-- 进度回写本仓；代码落 aidcp-cloud / aidcp-console。标 [x] 附 <!-- <repo> <sha> 备注 -->，部署后追加 deployed。 -->

## 1. aidcp-cloud — 飞书群名获取

- [ ] 1.1 `FeishuMessenger` 加 `listChats()`：调 `GET open-apis/im/v1/chats`（复用 tokenManager 取 token；分页 page_size=100 + page_token，设最大页数上限防无限翻页）；返回 `[{chatId, name}]`；best-effort——异常/非 0 code 抛给调用方降级（不静默空）。
- [ ] 1.2 `src/server.ts` 组装 `GET /api/bot-chats` 的 provider（注入 PanelDeps）：实时 `messenger.listChats()` + `resolveDefaultChatId` 算 `defaultChatId`，合出 `{chats:[{chatId,name,isDefault}], defaultChatId, source:'feishu'}`；加进程内 ~60s 缓存；飞书失败 → 回落 `botChatStore.listActive()`（`source:'store'`、name 用 chatName、isDefault 用表内 is_default，defaultChatId 尽力解析）。

## 2. aidcp-cloud — 面板路由响应扩展

- [ ] 2.1 `src/panel/types.ts` + `panel-server.ts`：`GET /api/bot-chats` 改用新 provider（未注入则仍回 `botChatStore.listActive()` 老形状兼容）；响应形状 `{chats:[{chatId,name,isDefault}], defaultChatId, source}`。

## 3. aidcp-console — 群名展示

- [ ] 3.1 `src/types/api.ts`：`PanelBotChat` 增 `name`（保留 chatId/isDefault）；`GET /api/bot-chats` 响应类型增 `defaultChatId`/`source`。
- [ ] 3.2 `NotificationRoutesPage.tsx`：下拉与映射表**以群名为主**（`name ?? chatId`）、chatId 悬浮/次要；顶部提示条「未映射的账号 → 默认群：<群名/id>」；`source==='store'` 时提示需在飞书后台加 `im:chat:readonly` 权限。

## 4. 测试

- [ ] 4.1 cloud 单测：`listChats()` 分页聚合 + 非 0 code / 网络失败抛错；provider 降级路径（飞书失败 → store 源、不空不崩）+ defaultChatId 解析。
- [ ] 4.2 panel 路由单测：新响应形状（chats 带 name、defaultChatId、source）；provider 未注入时老形状兼容。
- [ ] 4.3 console：NotificationRoutesPage 以群名展示 + 默认群提示；typecheck + build。
- [ ] 4.4 全量绿：cloud test:acceptance + test + typecheck；console test + build。

## 5. 部署与验收

- [ ] 5.1 dev 部署（探 ECS → 干净快照 → 备份 → rsync → restart → healthcheck；console 干净 worktree build → rsync 无 --delete；不碰 isales）。
- [ ] 5.2 验证：`GET /api/bot-chats` 有权限时回真实群名 + defaultChatId；无权限时 `source=store` 降级不崩；后台以群名展示、默认群提示条正确。
- [ ] 5.3 真机项登记 backlog 簇 20 补一条：加 `im:chat:readonly` 后群名显示；缺权限降级提示。
