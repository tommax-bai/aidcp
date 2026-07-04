> 实装进度（2026-07-04）：任务 1–4 已完成——cloud **c99745f**（store+发布参照+评论定向+panel 端点+接线+27 单测；全量 1295/1296 绿，唯一失败为既有 Windows-only AC-PUB-01 路径分隔符问题，与本变更零交集）、console **d817a29**（行内动作+弹窗+5 页面测试；34 测全绿+build 净）。剩部署与真机验收。
>
> 依赖序：1（cloud 存储/发布侧）→ 2（cloud 评论侧）→ 3（cloud panel 接线）→ 4（console）→ 5（部署验收）。
> 回写格式：完成任务标 `[x]` 并追加 HTML 注释 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
> 范围红线：零 edge 改动、零协议改动、零 DDL；console 只动 CuratedContentPage.tsx（+必要时 types/api.ts 镜像）；提交一律显式 pathspec（工作树有他会话 WIP）。

## 1. aidcp-cloud — 存储只读方法 + 发布侧参照注入

- [x] 1.1 curated-content-store.ts 新增只读 `getOneForAccount(id, accountId)`（WHERE id AND account_id，防越权同 deleteOne；42P01 诚实回 null）。验证：store 单测（命中/跨账号不命中/表缺失） <!-- aidcp-cloud c99745f getOneForAccount+3 单测 -->
- [x] 1.2 publish-agent/types.ts TriggerInput.generateInput 新增可选 `referenceNote {sourceId,title,body,topics,author?}`；publish-scheduler.ts triggerManual/doTrigger 支持携带参照（正文截断 ≤800 字）。验证：typecheck + scheduler 单测（参照透传进 TriggerInput） <!-- aidcp-cloud c99745f referenceNote 贯穿+4 单测(publish-scheduler-reference) -->
- [x] 1.3 prompts.ts buildCreatorPrompt 新增条件性【参照笔记——洗稿参照】独立块（借选题/结构/要点、人设口吻重写、禁止逐句照抄、可辨识差异），buildScoutPrompt forced 块同步注入参照标题/要点钉方向；既有素材块与「严禁照抄」红线原样保留。验证：prompts 单测（有参照/无参照两态、参照不混入素材块） <!-- aidcp-cloud c99745f 参照块独立于素材块+4 单测(prompts-reference) -->

## 2. aidcp-cloud — 评论侧定向任务

- [x] 2.1 comment-task-runner.ts 新增 `runTargetedCommentTask`（复用 CommentTaskSteps：searchAndHarvest→按 noteId 精确匹配→readNote 校验→composeAndApprove→post→recordCommented；≤2 次搜索尝试；终态含 note_not_found）。验证：runner 单测（命中/两次未命中/详情 noteId 不一致不评/已评论跳过在调度层） <!-- aidcp-cloud c99745f runTargetedCommentTask+9 单测 -->
- [x] 2.2 comment-scheduler.ts 新增 `triggerTargeted(accountId, {noteId, searchTitle, injectGroup})`：守卫同构 triggerManual（账号/人设/群口令 fail-closed/单飞/边端在线）+ 去重前置（hasInteraction→already_commented）；搜索词截断 ≤20 字；sort='comprehensive'/timeWindow='all' 覆盖；takeover 钩子与终态结果卡复用（卡面标注定向来源）。验证：scheduler 单测（各拒绝路径 + 触发路径 + 参数覆盖断言） <!-- aidcp-cloud c99745f triggerTargeted+10 单测(含 sort/timeWindow/截断断言) -->
- [x] 2.3 确认零协议/零角色新增：不登记新 role-catalog 条目、不动两份 protocol.ts 与 command-bridge.ts。验证：typecheck + AC-PROTO 通过（无 diff 即天然通过，任务留痕即可） <!-- aidcp-cloud c99745f protocol.ts/command-bridge/role-catalog 零 diff，typecheck 净 -->

## 3. aidcp-cloud — panel 端点与接线

- [x] 3.1 panel/types.ts 新增 `PanelDeps.curatedActions?`（createPostFromNote/commentOnNote，返回 {triggered, reason?}）；panel-server.ts 新增 POST /api/curated/contents/:id/create-post 与 POST /api/curated/contents/:id/comment（accountId 必带、行加载走 getOneForAccount、note_only/empty_body/404/503 语义按 spec；路由插位先于 DELETE :id 前缀匹配）。验证：panel 单测（越权 404/评论行 note_only/壳行 empty_body/依赖缺失 503/触发透传） <!-- aidcp-cloud c99745f 两路由+PanelCuratedActions+panel-curated-actions.test 全径 -->
- [x] 3.2 server.ts 接线：curatedActions 闭包 publishScheduler.triggerManual(accountId,{referenceNote}) 与 commentScheduler.triggerTargeted(...)，域内拒绝（publish_busy/skipped、needs_persona、edge_offline、running、group_code_missing、already_commented）逐一映射为 triggered=false+原因码。验证：接线单测或集成测（原因码映射表全覆盖） <!-- aidcp-cloud c99745f 原因码映射；publish fire-and-forget+异步飞书卡 -->
- [x] 3.3 cloud 回归：`npm run test:acceptance` + 全量 `npm test` + `npm run typecheck`；显式 pathspec 提交推送 master。验证：三项全绿 <!-- aidcp-cloud c99745f acceptance 42/43+全量 1295/1296(唯一失败=既有 Windows-only AC-PUB-01)+typecheck 净 -->

## 4. aidcp-console — 精选页行内动作

- [x] 4.1 CuratedContentPage.tsx 操作列（stopPropagation 容器内）新增「参照创作」Popconfirm（comment 行/空正文禁用）与「定向评论」Modal（Radio 内容评论/带群评论，comment 行禁用）；页面本地 useMutation（apiPost、非乐观、invalidate ['curated']）；回执诚实分支（triggered=true→success 引导飞书审核；false→info 中文原因映射；异常→error）。验证：页面单测（按钮禁用态/两端点调用参数/三分支提示） <!-- aidcp-console d817a29 行内动作+弹窗+5 测试 -->
- [x] 4.2 如需 DTO：types/api.ts 精选区块加触发回执类型并与 cloud panel/types.ts 手工镜像同步。验证：typecheck <!-- aidcp-console d817a29 CuratedActionReceipt 镜像 -->
- [x] 4.3 console 回归：`npm test` + `npm run typecheck` + `npm run build`；显式 pathspec 提交推送 master（避开 routes.tsx/api/queries.ts 等他会话 WIP）。验证：三项全绿 <!-- aidcp-console d817a29 34 测绿+typecheck 净+build 净(index-DgshMzg1.js) -->

## 5. 部署与验收

> 已上线 ECS（2026-07-04，用户授权后）：三仓均已推送 origin（cloud master 6ba1f50 / console master 46d0a0c 含并发 / umbrella main）；对抗审查确诊的 1 个真 bug（triggerTargeted 单飞闸 TOCTOU）已修（cloud 6ba1f50）+回归测试双向验证；其余 7 项审查发现经复核为误报。部署遇并发漂移（我的 server.ts 引用 pacing-config-store.js，ECS 跑旧快照无此文件）→ 改用 committed HEAD 全量 git-archive src 部署一次性消漂移。剩真机验收（5.3–5.5，用户侧）。

- [x] 5.1 cloud 部署 ECS：备份→全量 git-archive src 部署（消并发漂移）→restart aidcp-cloud.service→healthcheck。验证：active/8787 LISTEN/PG select 1=1/面板 :8090 起+/api/version 200/飞书长连 onReady/CommentScheduler·PublishScheduler 已就绪；成功启动 15:22:15 后零错误。<!-- aidcp-cloud 6ba1f50 deployed 2026-07-04；备份 cloud-curated-actions.bak.20260704-151846 + cloud-src.bak.20260704-152136.tar.gz -->
- [x] 5.2 console 部署 ECS：build dist（HEAD 46d0a0c，index-Bny7cQxP.js）→备份 console.bak.20260704-152359→tar-over-ssh 覆盖→验活。验证：index.html 引用新资产/:8088 root 200/新 JS 200/经 nginx /api/version 200。<!-- aidcp-console 46d0a0c deployed 2026-07-04 -->
- [ ] 5.3 【用户侧】真机验收①：对一条精选笔记触发参照创作→飞书人审卡→通过→边端发布成功，草稿正文与参照有可辨识差异
- [ ] 5.4 【用户侧】真机验收②：定向内容评论全链路（搜索定位命中→人审→发布→去重记账）；标定搜索命中率与截断策略
- [ ] 5.5 【用户侧】真机验收③：带群评论（口令追加、审=发）+ 拒绝路径抽查（壳行 empty_body/已评论 already_commented/未配口令 group_code_missing/评论行禁用）
