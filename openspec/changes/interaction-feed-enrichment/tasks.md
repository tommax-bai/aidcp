# Tasks — interaction-feed-enrichment

> 实装前先做 CLAUDE.md §0 前置检查（`ls -d ../aidcp-edge ../aidcp-cloud ../aidcp-console`；部署涉及私钥再查）。代码落 sub-repo，进度回写本节，标 `[x]` 时附 `<!-- <repo> <sha> 备注 -->`。
> 顺序：云端先行（可独立部署、对旧边缘向后兼容；上线即让评论 / 关注进流、标题来自既有上报）→ 边缘（真实链接 + 昵称）→ 前端（标题链接 + 配色）。

## 1. aidcp-cloud — 存储 + 记录 + 面板读侧（先行，向后兼容）
<!-- aidcp-cloud e91c33c 全绿(739/739 + acc 26/26, typecheck 仅余并发 publish-multi-image WIP 报错非本变更)。
     1.3 偏离: currentAuthorId 加在 EdgeSession(src/comm/ws-server.ts) 而非 SessionContext —— handler 的 session 即 EdgeSession(currentNoteId/accountId 同处)。
     1.8 panel-server.ts 未改: 端点透传 store 结果, 形状随 store 自动更新。 -->

- [x] 1.1 迁移 `migrations/0019_interaction_feed.sql`（`IF NOT EXISTS` 幂等）：建 `interaction_feed(account_id, action CHECK in like/collect/comment/follow, target_id, occurred_at, PK(account_id,action,target_id))` + 索引 `(account_id, occurred_at DESC)`；建 `interaction_target_meta(account_id, target_id, title, url, updated_at, PK(account_id,target_id))`
- [x] 1.2 `src/comm/protocol.ts`（cloud 份）：`NoteDetailPayload` +`url?: string`；`ProfileDetailPayload` +`nickname?: string` +`url?: string`（与 edge 份逐字一致，见 2.1）
- [x] 1.3 `src/agents/session-context.ts`：新增 `currentAuthorId`（getter/setter），仅此一个字段
- [x] 1.4 `src/comm/handler.ts`：`profile.detail` 时存 `session.currentAuthorId`；`note.detail` 到达时 upsert 笔记元数据（noteId→title,url）+ 作者元数据（authorId→nickname）；`profile.detail` 时 upsert 作者元数据（authorId→nickname,url）；emit `interaction.occurred` 时带 `targetId`（笔记动作=currentNoteId，关注=currentAuthorId）；移除对评论 / 关注进流的排除
- [x] 1.5 新增互动流存储方法（如 `src/cache/interaction-feed-store.ts` 或并入现有 store）：`recordFeedEvent(account, action, targetId, ts)` 用 `ON CONFLICT DO NOTHING`（保留首次时间）；`upsertTargetMeta(account, targetId, {title?,url?})` 用 `ON CONFLICT DO UPDATE` + `COALESCE`（互不抹除、刷新最新 token）；`listInteractions` 读 feed `LEFT JOIN` meta
- [x] 1.6 `src/server.ts`：`interaction.occurred` 订阅写 `interaction_feed`（四类动作均写），近旁加注释「observability ledger; 不碰 RiskController 终态」；`risk_interactions` 既有写入**保持不动**
- [x] 1.7 `src/panel/panel-store.ts` + `src/panel/types.ts`：`listInteractions` 改读 `interaction_feed LEFT JOIN interaction_target_meta`；`PanelInteraction` 形状改为 `{accountId, action(4 值), targetId, title?, url?, occurredAt}`（缺失字段诚实 NULL→undefined）
- [x] 1.8 `src/panel/panel-server.ts`：`/api/monitor/interactions` 路径不变，返回新形状
- [x] 1.9 更新 `panel-store.test.ts`（旧 `{noteId,action,interactedAt}` 期望→新形状）；新增 AC-PANEL 验收：笔记动作→标题+详情 url、关注→昵称+主页 url、缺失→NULL 绝不造假
- [x] 1.10 cloud 回归：先 `npm run test:acceptance`（AC-PROTO/RISK 必过）再全量 `npm test` 再 `npm run typecheck` 全绿

## 2. aidcp-edge — 诚实抓取真实链接与作者昵称
<!-- aidcp-edge 0eb3d26 全绿(362+2 / acc 11/11 / typecheck 0)。两份 protocol.ts: NoteDetailPayload 逐字一致; ProfileDetailPayload 新增字段一致(仅历史注释差异)。 -->

- [x] 2.1 `src/comm/protocol.ts`（edge 份）：与 cloud 份逐字一致追加 `NoteDetailPayload.url?`、`ProfileDetailPayload.nickname?/url?`；两份 diff 核对（payload 字段漂移 typecheck 抓不到）
- [x] 2.2 `src/browse/browse-session.ts`：进笔记详情时读 `location.href`，仅当含 `xsec_token` 才作为 `url` 上报；`evalUrl()` 空串归一为 `undefined`（诚实置空，绝不用裸 id 拼链）
- [x] 2.3 `src/browse/browse-session.ts` + `src/browse/note-extractor.ts`：进作者主页时读 `location.href`（主页 url）并从主页 DOM 抓作者真实昵称（抓不到则诚实置空）
- [x] 2.4 edge 验收用例：无 token → `url` 为 `undefined`（断言绝不出现裸 id 拼链）；无昵称 → `nickname` `undefined`；AC-PROTO 不漂移
- [x] 2.5 edge 回归：`npm run test:acceptance` + `npm test` + `npm run typecheck` 全绿

## 3. aidcp-console — 标题链接 + 动作配色
<!-- aidcp-console 05b4c92 (tsc + build 绿, 枚举漂移测试绿)。 -->

- [x] 3.1 `src/types/api.ts`：`PanelInteraction` +`title?: string` +`url?: string` +`targetId`；动作 union 加 `follow`
- [x] 3.2 `src/types/aidcp-enums.ts`：新增 `RISK_ACTION_COLOR`（like/collect/comment/follow 各异色；未知回落默认）
- [x] 3.3 `src/pages/MonitorPage.tsx`：动作列改 `<Tag color={RISK_ACTION_COLOR[..]}>`；目标列 `url` 非空渲染 `<a href={url} target="_blank" rel="noreferrer">{title}</a>`，否则纯 `{title}`，否则回落裸 id；加「链接含时效令牌、较旧的可能失效」提示（tooltip / 列说明）
- [x] 3.4 console：`tsc`（typecheck）+ `build` 全绿

## 4. 协议文档 / 双端同步
<!-- 本仓 docs/protocol.md 改既有 note.detail / profile.detail 上报行(计数不变); 双端 protocol.ts 新增字段已 diff 核对一致。 -->

- [x] 4.1 `docs/protocol.md`：修改 `NoteDetailPayload`、`ProfileDetailPayload` 既有上报行说明（追加可选字段），消息类型计数**不变**
- [x] 4.2 核对两份 `protocol.ts` 就新增字段逐字一致；两仓各跑 `typecheck`

## 5. 校验 / 部署 / 真机 / 归档

- [x] 5.1 `openspec validate interaction-feed-enrichment --strict` 通过
- [x] 5.2 提交：仅暂存本变更涉及文件（并发会话纪律，绝不 `git add -A`）；cloud/edge/console 推各自 `master`、本仓推 `main`
- [x] 5.3 部署 cloud 到 ECS（§5 安全序列：dry-run 看带出范围 → 备份 → rsync → restart → healthcheck 含 grep 新码实测生效 → 失败回滚）；console 重新构建 serve 于 8088；确认 isales 未被触碰 <!-- 2026-06-26 deployed: git-archive 干净 master rsync(无 --delete, 仅本变更 10 文件); 备份 cloud.bak.20260626-110204; restart 后 healthcheck 全绿(active + 8787/8090/8088 + 飞书长连 + InteractionFeedStore/RiskController 已就绪日志 + interaction_feed/interaction_target_meta 表自建确认 + 无 error); console index-B-Ai_v1i.js 已 serve(8088=200, index.html 引新 hash); isales 4 服务全 active 未碰 -->

- [ ] 5.4 真机 E2E（gated）：点赞 / 收藏 / 评论 / 关注各产出一条流记录；笔记标题链接可开；作者主页链接可开；无 token 时诚实置空（不可点、无死链）
- [ ] 5.5 真机校验 Open Questions：裸 `/user/profile/<id>` 是否无 token 可开（不可靠则昵称改不可点）；explore 整页与 discovery 弹层两形态 `location.href` 是否都带 token
- [ ] 5.6 tasks 回写实测 + `openspec archive`（delta 合并进 `openspec/specs/`）
