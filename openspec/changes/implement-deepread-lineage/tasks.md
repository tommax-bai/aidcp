## 1. 协议层（aidcp-cloud + aidcp-edge 双侧 protocol 同步）

- [x] 1.1 cloud `src/comm/protocol.ts`：新增消息类型 `profile.open`（cloud→edge）+ `ProfileOpenPayload {authorId?, reason?, thinkMs?}`，登记到 `MessageType` 与 `PayloadMap` <!-- aidcp-cloud ab49d5c -->
- [x] 1.2 edge `src/comm/protocol.ts`：同步 `profile.open` 与 `ProfileOpenPayload`（与 cloud 字段一致） <!-- aidcp-edge 8b2b4b9 -->
- [x] 1.3 双侧确认 `ProfileDetailPayload` 含 `authorId/postsCount/followersCount`，并增加可选 `extracted?: boolean`（标记抽取是否成功） <!-- aidcp-cloud ab49d5c / aidcp-edge 8b2b4b9。另修复 cloud 侧 NoteBrowse/ScrollComments payload 缺 count 的两端漂移 -->
- [x] 1.4 决定是否给 `ActionCompletedPayload` 增加结构化回报（已浏览张数/滚屏数）——若 `reason` 字段够用则不扩；记录决定于 design Open Questions <!-- 决定：不扩协议，用 reason 承载 browsed=N / scrolled=N -->

## 2. aidcp-cloud — 多图浏览（DeepReader 真实化）

- [x] 2.1 `src/agents/deep-reader.ts`：去掉 `imagesBrowsed=0` 硬编码直通；改为消费 `quality.pass`，基于当前笔记（图数/正文长度）+ 人设决策是否看图、看几张（含概率门） <!-- aidcp-cloud ab49d5c。无 LLM 策略角色：概率门+正文长度启发，random 可注入 -->
- [x] 2.2 决策"看"时 emit 意图事件（如 `reading.browse_images_requested`），决策"不看"时直接 emit `reading.images_done` <!-- aidcp-cloud ab49d5c。事件名实现为 reading.browse_images / reading.images_done -->
- [x] 2.3 `src/orchestrator/role-dispatcher.ts`：`setupCommandTranslation` 新增接线——意图事件 → `sendCommand({action:'browse_images', params:{noteId, count, dwellMs}})` <!-- aidcp-cloud ab49d5c -->
- [x] 2.4 监听 `browse_images` 的 `action.completed`（含失败兜底 `recover_after_browse_images_failed`）→ emit `reading.images_done`，保证成败都推进 <!-- aidcp-cloud ab49d5c。DeepReader 自订阅 action.completed；dispatcher 把 browse_images 排除出 recovery-scroll -->
- [x] 2.5 `src/event-bus/types.ts`：补 `reading.images_done` / 意图事件的事件定义 <!-- aidcp-cloud ab49d5c -->

## 3. aidcp-cloud — 评论浏览（comment_reviewer 实体化）

- [x] 3.1 新增 `src/agents/comment-reviewer.ts`：`BaseRole` 子角色，`roleName='comment_reviewer'`，消费 `reading.images_done`，LLM 判定是否看评论/看多少（含概率门） <!-- aidcp-cloud ab49d5c -->
- [x] 3.2 `src/agents/index.ts` 导出 + `src/orchestrator/role-dispatcher.ts` 实例化注册 `comment_reviewer` <!-- aidcp-cloud ab49d5c -->
- [x] 3.3 决策"看"时 emit 意图事件 → role-dispatcher 接线 `sendCommand({action:'scroll_comments', params:{noteId, dwellMs}})`；"不看"直接 emit `reading.done` <!-- aidcp-cloud ab49d5c -->
- [x] 3.4 监听 `scroll_comments` 的 `action.completed`（含失败兜底）→ emit `reading.done`（进入互动阶段的唯一出口，下游不变） <!-- aidcp-cloud ab49d5c -->
- [x] 3.5 `src/event-bus/types.ts`：把 `comment_reviewer` 纳入活跃 `RoleName`，补相关事件定义 <!-- aidcp-cloud ab49d5c -->

## 4. aidcp-cloud — 进主页 + 作者资料接线

- [x] 4.1 `src/comm/command-bridge.ts`：新增 `profile_open → profile.open` 翻译映射 <!-- aidcp-cloud ab49d5c -->
- [x] 4.2 `src/orchestrator/role-dispatcher.ts`：把 `profile.entered` 翻译为 `sendCommand({action:'profile_open', params:{authorId, thinkMs}})`（替换原 `open_note{type:'profile'}`） <!-- aidcp-cloud ab49d5c -->
- [x] 4.3 `src/comm/handler.ts`：新增 `case 'profile.detail'` → `emit('profile.detail.arrived', {detail, ts})`（与 `note.detail.arrived` 同构） <!-- aidcp-cloud ab49d5c -->
- [x] 4.4 `src/orchestrator/role-dispatcher.ts`：订阅 `profile.detail.arrived` → `updateProfileData(detail)` <!-- aidcp-cloud ab49d5c。偏离：改由 ProfileBrowser 直接消费 profile.detail.arrived 产出 profile.browsed；dispatcher 不再中转存储，原 updateProfileData/profileData 死代码已移除 -->
- [x] 4.5 `src/agents/profile-browser.ts`：触发点从 `profile.entered` 改为 `profile.detail.arrived`，用真实 counts emit `profile.browsed`；缺省/null 不再静默填 0 <!-- aidcp-cloud ab49d5c。profile.entered 缓存 sourcePageType，detail.arrived 携真实 counts+extracted 产出 -->
- [x] 4.6 `src/agents/follow-agent.ts`：当资料标记不可用（`extracted=false`）时保守 skip，并在 prompt/逻辑上区分"数据缺失"与"真 0 粉丝" <!-- aidcp-cloud ab49d5c。extracted=false → 不调 LLM 直接 skip -->

## 5. aidcp-edge — 多图与评论执行（选择器校准 + 如实回报）

- [x] 5.1 `src/browse/browse-session.ts` `browseNoteImages`：对照真实小红书详情页 DOM 校准图片轮播/翻页选择器；去掉 `count||1` 恒成功兜底 <!-- aidcp-edge 8b2b4b9。选择器为最佳推断，需 5.4 实机校准 -->
- [x] 5.2 `browse_images` 的 `action.completed` 如实回报（翻图张数；未命中→`ok=false, reason='no_target'`） <!-- aidcp-edge 8b2b4b9。reason='browsed=N' / 'no_target' -->
- [x] 5.3 `scrollNoteComments`：校准评论区选择器；`scroll_comments` 的 `action.completed` 如实回报（滚屏数/无评论/未命中） <!-- aidcp-edge 8b2b4b9。reason='scrolled=N' / 'no_target' -->
- [ ] 5.4 本地在真实页面核对选择器命中（开一篇多图笔记 + 一篇有评论笔记验证） <!-- 需本地登录小红书 + 跑 edge 实机核对，留待用户 -->

## 6. aidcp-edge — 进主页执行 + 作者资料抽取上报

- [x] 6.1 `src/browse/browse-session.ts` `dispatchCommand`：新增 `case 'profile.open'`——导航进入作者主页（点头像或跳转 `/user/profile/<authorId>`，按本地核对结果定）并等主页渲染就绪 <!-- aidcp-edge 8b2b4b9。实现为点详情页作者入口 + waitForProfile 轮询 -->
- [x] 6.2 新增作者主页 profile 抽取（`postsCount`/`followersCount` 的真实小红书选择器），复用 `parseCount` 数字解析 <!-- aidcp-edge 8b2b4b9。extractAuthorProfile；选择器需 6.5 实机校准 -->
- [x] 6.3 进主页成功后调用 `client.reportProfileDetail({authorId, postsCount, followersCount, extracted:true})`（落实当前的死代码调用点） <!-- aidcp-edge 8b2b4b9 -->
- [x] 6.4 抽取失败/超时仍上报 `profile.detail`（`extracted:false`），并兜底返回信息流不卡死 <!-- aidcp-edge 8b2b4b9。reportProfileFallback -->
- [ ] 6.5 本地在真实页面核对：能进主页、能抽到非 0 粉丝/作品数 <!-- 需本地实机核对，留待用户 -->

## 7. 测试与验收

- [x] 7.1 cloud 单测：DeepReader（看/不看/失败三分支推进）、comment_reviewer（三分支）、profile.detail.arrived→updateProfileData→profile.browsed 真实 counts、follow 在 extracted=false 时保守 skip <!-- aidcp-cloud ab49d5c -->
- [x] 7.2 cloud 集成测：`quality.pass → DeepReader → reading.images_done → comment_reviewer → reading.done → InteractionAppraiser` 整链跑通；`profile.entered → profile.open → profile.detail.arrived → profile.browsed → FollowAgent` 跑通 <!-- aidcp-cloud ab49d5c。路径 D/E/F 适配新链路（假边缘回执 browse_images/scroll_comments/profile_open） -->
- [x] 7.3 edge 单测：browse_images/scroll_comments 未命中→`no_target` 不假报成功；profile 抽取夹具解析 postsCount/followersCount <!-- aidcp-edge 8b2b4b9 -->
- [x] 7.4 双仓 `npm test` + `npm run typecheck` + `npm run test:acceptance` 通过 <!-- cloud 162+11 / edge 212+11，typecheck 均过 -->
- [ ] 7.5 本地 edge 连 ECS `ws://121.89.85.150:8787` 跑一轮：人工观测看图/翻评论/进主页/`FollowAgent` 收到非 0 数据 <!-- 需本地实机联调，留待用户 -->

## 8. 文档与部署

- [x] 8.1 ai-dcp `docs/protocol.md`：增补 `profile.open` 指令与（如有）回报字段说明，更新 action→message 映射表 <!-- ai-dcp（本提交） -->
- [x] 8.2 回写本 change `tasks.md` 进度（HTML 注释标 PR#/commit-sha/偏离说明） <!-- ai-dcp（本提交） -->
- [x] 8.3 `openspec validate implement-deepread-lineage --strict` 通过 <!-- 见提交前校验 -->
- [x] 8.4 cloud 按 ECS 安全序列部署（备份→rsync→restart→healthcheck→失败回滚），edge 本地发布；部署后追加 `<!-- <date> deployed -->` <!-- aidcp-cloud ab49d5c 2026-06-17 deployed：备份 /opt/aidcp/cloud.bak.20260617-141701.tar.gz + .env.bak.20260617，rsync src/（10 文件），restart aidcp-cloud.service active/NRestarts=0，healthcheck 全过（8787 监听 / 飞书长连接 / PG select 1 / isales 未触碰）。edge 本地发布待用户重启本机 edge（连 ws://121.89.85.150:8787），随 5.4/6.5/7.5 实机核对一并完成 -->
