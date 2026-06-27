## 1. aidcp-cloud — 预览按选定账号人设渲染（纯只读）

- [x] 1.1 `src/config/role-prompt-preview.ts`：`RolePromptProvider.get` 增加可选 `accountId` 入参；provider 接线增加两个注入函数 `withAccount(accountId, fn)`（封装「切预览账号→同步渲染→`finally` 还原」）与 `hasPersona(accountId): boolean`（不回落判定），provider 不直连 dispatcher/store。<!-- aidcp-cloud bab4339 RolePromptProviderOptions{withAccount,hasPersona}，render() 抽出 -->
- [x] 1.2 `role-prompt-preview.ts`：accountId 给定时用 `withAccount` 包裹同步渲染；用 `hasPersona` 判定，无人设行（且 accountId≠'default'）时置返回体 `personaFallback:true` + 诚实 `note`；记 `accountId` 字段。绝不把默认人设冒充为该账号人设。<!-- aidcp-cloud bab4339 FALLBACK_NOTE，default 豁免 -->
- [x] 1.3 `src/server.ts`：接线 provider 时传入 `withAccount`（用 `previewDispatcher.accountId` 读回 + `setCurrentAccountId` 切/还原）与 `hasPersona`（用 `personaStore.getForAccount(accountId)!==null`）。`createRolePromptProvider` 仍只借读角色，不改预览 dispatcher 构造。<!-- aidcp-cloud bab4339 -->
- [x] 1.4 `src/panel/panel-server.ts`：预览路由解析可选 `?accountId=`（缺省/未知不报错，透传 provider 按回落标注处理），传给 `rolePromptPreview.get(roleId, accountId)`。<!-- aidcp-cloud bab4339 URLSearchParams 范式 -->
- [x] 1.5 `src/panel/types.ts`：`RolePromptView` 增加可选字段 `accountId?: string` 与 `personaFallback?: boolean`（向后兼容，旧字段不动）。<!-- aidcp-cloud bab4339 + PanelRolePromptPreview.get(roleId,accountId?) -->

<!-- 并发坑：三个共享文件（panel/types.ts、panel-server.ts、server.ts）与并发 WIP（session-auto-resume、account-real-nickname）在同文件交织；用 HEAD-blob + 单 hunk 外科手术（hash-object/update-index）只提交本变更，工作树并发 WIP 完好保留。 -->

## 2. aidcp-console — 「角色模型配置」卡片加人设选择框

- [x] 2.1 `src/api/queries.ts` / `src/types/api.ts`：复用/补账号列表查询（`GET /api/accounts`）；`RolePromptView` 类型补 `accountId?` / `personaFallback?` 可选字段。<!-- aidcp-console: queries 复用既有 useAccounts；类型字段被并发会话 git add 连带提交进 b8484ce -->
- [x] 2.2 `src/pages/RolesPage.tsx`：在「角色模型配置」卡片加账号/人设选择框（选项取账号列表，未配人设账号灰标；默认空=系统默认人设），值存页面 state。<!-- aidcp-console 4e35cbf Card extra Select + PanelAccount.personaBound 灰标 -->
- [x] 2.3 `RolesPage.tsx`：「查看 Prompt」按当前选框值拉 `GET /api/roles/:id/prompt?accountId=<选定>`；选框改变且弹窗已开时重拉刷新。<!-- aidcp-console 4e35cbf loadPrompt(row,accountId) + useEffect([previewAccountId]) -->
- [x] 2.4 `RolesPage.tsx`：弹窗内 `personaFallback` 为真时顶部 Alert 明示「该账号未配人设，下示为默认人设」；正常时可标注所用账号；分段渲染逻辑复用既有。<!-- aidcp-console 4e35cbf -->

## 3. 验证（代码级，落 sub-repo 执行）

- [x] 3.1 cloud：`npm run test:acceptance`（AC-* 安全红线全过 26/26）→ `npm test`（含 prompt 预览既有用例 + 新增 accountId/回落用例，**745/745**）→ `npm run typecheck`。<!-- 全局 typecheck 仍红但 38 个错误全部来自并发 WIP（publish-multi-image/session-auto-resume），本变更所碰文件零报错 -->
- [x] 3.2 cloud：补/核单测——按选定账号渲染、未配人设诚实回落标注、不传 accountId 行为不变、渲染抛错账号仍还原。<!-- test/role-prompt-preview.test.ts +5、test/role-prompt-panel.test.ts +1（?accountId 透传），均绿 -->
- [x] 3.3 console：`npm run typecheck` + `npm run build` 绿。<!-- HEAD 前移（b8484ce 含 nickname）后复测仍绿 -->
- [x] 3.4 `openspec validate prompt-preview-persona-selector --strict` 通过。

## 4. 部署与归档（显式动作，gated）

- [x] 4.1 部署 cloud（备份→rsync 排除 .env/node_modules/.git→restart→healthcheck）+ console 重 build 出静态；按 ECS 全量快照纪律先 dry-run 看范围。<!-- 06-27 部署成功: 从干净 origin/master worktree(cloud 4c7fea2 typecheck+751测试绿 / console a5e35d2 build绿)出, 内容级 --checksum dry-run; cloud 仅 8 内容变更文件(3我源+2我测试+3他人测试, server.ts 已随他人部署在线)→restart→healthcheck全绿(active+8787+8090+所有存储就绪+飞书 onReady+零错误, isales 四服务未碰); console rsync --delete 换新 bundle index-Dv1xOKuX.js, 8088 返200; 备份 cloud/console.bak.20260627-pps.tar.gz + .env.bak. 连带上线 account-real-nickname(他人已部分部署) -->

- [ ] 4.2 真机/后台核对：选不同账号查看同一角色 prompt，人设段随账号变化；未配人设账号显示回落标注。
- [ ] 4.3 `openspec archive prompt-preview-persona-selector`（delta 合并进 `openspec/specs/role-llm-config`）。
