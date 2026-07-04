# Design — curated-note-actions

> file:line 证据以 2026-07-04 各仓 HEAD 为准（cloud d0e865e / console 04b53cf）。两条链路（发布、/comment）均已生产运行，本变更是「从精选页一行触发 + 目标钉死」的接线，不重建链路。

## Context

- 数据侧：`curated_content`（aidcp-cloud/src/cache/curated-content-store.ts，DDL 119-143）。**note 行**存 `source_id`=noteId、`source_url`=带 xsec_token 的详情链接、title/body/topics；**comment 行**的 source_id 是 DOM 锚点 `comment-<id>`，未存源笔记 noteId 与 URL——无法定位回源笔记。壳行（admit_reason `bot_collect(content_missing)`）body 为空。
- 发布链路：`publishScheduler.triggerManual(accountId)`（publish-scheduler.ts:227-241）→ TriggerInput（types.ts:82-123）→ blackboard 角色链 → `publish_log` pending_approval → 飞书人审卡 → publish_takeover 下发。创作 prompt 的素材块下有红线「严禁照抄或改写其句子」（prompts.ts:248）。
- 评论链路：/comment 命令（comment-scheduler.ts triggerManual 87-139 → comment-task-runner.ts runCommentTask 94-153 → edge-steps.ts）已具备全部边端原语：`search.execute`（支持 sort/timeWindow 覆盖，edge-steps.ts:171-172）→ `page.cards.arrived` → `note.open{noteId}`（按卡片点击定位，browse-session.ts:1069-1176）→ `note.scroll_comments` → compose-approve（飞书人审，AIDCP_COMMENT_APPROVAL）→ `interaction.comment{text, groupChatCode?}`。
- 边端红线：**没有按 URL 打开笔记的能力**；存量 note URL 的 xsec_token 会过期，打开触发 300031「当前笔记暂时无法浏览」且可能被 overlay 监控误判为风控（browse-session.ts:1633-1656）；edge 对 `interaction.comment` 的 noteId 只记日志不校验（835-841），跨笔记安全完全靠云端先 note.open 验证 + takeover 独占。
- 面板：panel-server.ts 手写 if-chain 路由（静态后缀须排在 :id 动态匹配前，:1305 注释）；写端点 accountId 必带且入 WHERE；console 写操作为页面本地 useMutation（queries.ts:1 约定）。

## Goals / Non-Goals

**Goals:**
- 精选页 note 行一键触发：①参照洗稿创作（既有发布链路+人审不变）；②定向评论（内容/带群两型，既有人审不变）。
- 目标定位可靠且守红线：搜索驱动 + noteId 精确匹配，绝不走存量 URL。
- 全链路诚实：触发态回执与终态结果分离，拒绝原因逐条透传（壳行/已评论/占用中/边端离线/未配群口令/未绑人设）。

**Non-Goals:**
- 跨账号执行（执行账号固定=行归属账号）；批量动作；动作排期化/自动化（仅手动触发）。
- comment 行的定向动作（未存源 noteId；将来若做，先在 curated-comment-evaluator.ts:116 处把在手的 p.noteId 持久化，属独立变更）。
- 边端新增「按 URL 开笔记」能力；协议新消息类型。
- 精选层治理类动作（置顶/压制/翻转标记）；「全部账号」读侧漂移的 spec 补账（另一变更范围）。

## Decisions

### D1 定向评论的目标定位 = 搜索驱动 + noteId 精确匹配（否决存量 URL 导航）

以该行 `title` 为搜索词发 `search.execute`，在返回的 `page.cards` 中查找 `source_id` 精确相等的卡片；命中→`note.open{noteId}`→等 `note.detail.arrived` 校验 noteId。否决方案：直接导航 `source_url`——token 过期→300031→风控误判，且需要新增边端导航能力，双重红线。
- **排序/时间窗覆盖**：sort=`comprehensive`、timeWindow=`all`（/comment 默认的「最多收藏+一天内」会把非当日笔记全部筛掉，定向场景必错）。buildEdgeCommentSteps 已参数化，仅传参不改边端。
- **搜索词**：title 截断到 ≤20 字（拟人逐字输入 ~110ms/字，控制在单步 28s 预算内；XHS 标题上限本就 20 字）。title 为空的行（理论上壳行伴随空 body）诚实拒绝。
- **有界重试 ≤2 次**：第 1 次全标题；未命中则第 2 次重发（可截前 12 字放宽）。两次都未命中→终态 `note_not_found`（黄）。重试同时缓解已知的 re-wake 首包错配（takeover 后 loop 重启会先报 feed 卡片，edge-steps.ts:125-127 匹配任意 page.cards）——定向流按 noteId 精确匹配，错配包无害，只消耗一次尝试。
- **去重前置**：触发前查 `risk_interactions.hasInteraction(noteId,'comment')`，命中→`already_commented` 拒绝；发布成功后 `recordInteraction`（与 /comment 一致，只记真实回执）。

### D2 复用 /comment 任务骨架，砍掉两个 LLM 角色（零新角色）

在 comment-agent 新增定向控制流 `runTargetedCommentTask`（与 runCommentTask 并列，复用同一 `CommentTaskSteps` 的 searchAndHarvest/readNote/post/recordCommented 与 compose-approve）：**不需要** CommentSearchTermGenerator 与 CommentTargetPicker（目标已知）→ 零 role-catalog 新条目，规避「角色漏登记→误用全局默认模型」的历史坑。CommentScheduler 新增 `triggerTargeted(accountId, {noteId, searchTitle, injectGroup})`，守卫与 triggerManual 同构：账号有效、人设已绑、group 口令 fail-closed、按账号单飞（running set）、边端在线；takeover 复用 comment_takeover 钩子（占位让位+quota-skip+finally 恢复）。人工触发语义与 /comment 手动一致：跳过风控配额 canDo（人是刹车），但保留人审与去重记账。

### D3 带群评论 = 既有 injectGroup 机制原样映射

用户已确认：带群评论正文与内容评论一样基于笔记信息自动生成。既有机制恰好如此——CommentComposer 撰写正文（≤50 字、人设口吻），`groupChatCode` 由 accountStore.getGroupChatInfo 解析、在审核卡合并展示（审=发）、边端以单次 Input.insertText 追加（绕 @/# 自动补全）。故 `withGroup=true` ⇔ injectGroup=true，未配群口令→触发即拒（`group_code_missing`，黄）。不新增撰写角色、不改 prompt。

### D4 参照洗稿 = TriggerInput 新增 referenceNote + 独立条件 prompt 块

- 数据流：panel 端点读行 → `publishScheduler.triggerManual(accountId, {referenceNote:{sourceId,title,body,topics,author?}})` → doTrigger → TriggerInput.generateInput.referenceNote（types.ts:88-113，与 materials 并列）。正文截断（如 ≤800 字）控 prompt 规模。
- Prompt：buildCreatorPrompt 新增条件块【参照笔记——洗稿参照】：借其选题/结构/要点，以账号人设口吻**重新创作**，禁止逐句照抄或简单同义替换，须与参照有可辨识的表达差异。**独立于素材块**——素材块红线「严禁照抄或改写其句子」（prompts.ts:248）语义是「素材只当灵感」，与「参照洗稿」互斥，混入会让 LLM 收到自相矛盾指令。buildScoutPrompt 的 forced 块同步注入参照标题/要点，把 publishDirection 钉在参照选题上（forced=true 时 Scout 不能否决，但方向仍由 prompt 引导）。
- 下游零改动：Title/Topic/配图/质量/人审/下发各角色只消费成品正文，参照自动流经。AC-PUB 三重人审闸（executor 只落 pending_approval / dispatcher 复核签名 / sequencer 无授权不 submit）原样生效。
- 占用语义与 /publish 持平：发布全局串行，运行中触发→`skipped`（黄）诚实返回；同账号可叠多份待审草稿（与 /publish 一致，人审是闸）。

### D5 Panel 端点与依赖注入

- `POST /api/curated/contents/:id/create-post`，body `{accountId}`；`POST /api/curated/contents/:id/comment`，body `{accountId, withGroup:boolean}`。路由插在既有 if-chain 中静态后缀区（clear-empty 旁），先于 DELETE 的 :id 前缀匹配解析。
- 行加载：store 新增只读 `getOneForAccount(id, accountId)`（WHERE id AND account_id，防越权同 deleteOne:500）。行不存在→404；非 note 行→400 `note_only`；壳行/空正文（create-post）→200 `{triggered:false, reason:'empty_body'}`。
- 依赖：PanelDeps 新增 `curatedActions?: { createPostFromNote(...), commentOnNote(...) }`，server.ts 接线时闭包 publishScheduler/commentScheduler；缺失→503（同 curated_unavailable 模式）。
- 回执契约：HTTP 200 + `{triggered:boolean, reason?:string}`＝**触发态**（等价飞书触发回执的绿/黄）；域内拒绝一律 200+false+机器原因码，由前端映射中文；仅结构性错误用 4xx/503。终态结果沿既有渠道：评论→飞书终态结果卡（outcomeToReceipt 三态复用，卡面标注定向来源）；发布→内容页待审草稿+飞书人审卡。

### D6 Console 行内动作（只动 CuratedContentPage.tsx）

- 操作列（既有 stopPropagation 容器内，:222-236）新增：「参照创作」Popconfirm（说明：以此笔记为参照生成草稿并送飞书人审；正文为空或 comment 行禁用）；「定向评论」小 Modal（Radio 选内容评论/带群评论，默认内容评论；说明：占用该账号边端、评论文案送飞书人审后发布；comment 行禁用）。
- 写 mutation 页面本地（apiPost，非乐观，`invalidateQueries(['curated'])`），回执诚实分支：`triggered===true`→message.success（提示到飞书审核）；false→message.info(原因中文映射)；异常→message.error。原因码→中文映射表随页维护（empty_body/note_only/already_commented/busy/edge_offline/needs_persona/group_code_missing/publish_busy…）。
- 不触碰 routes.tsx / api/queries.ts / types 之外的在途 WIP 文件；若需 DTO 类型，加在 types/api.ts 精选区块并保持与 cloud panel/types.ts 手工镜像同步。

## Risks / Trade-offs

- [XHS 搜索未收录/降权该笔记→搜不到] → 有界重试后诚实 `note_not_found`（黄），不无限重试不换目标；真机标定项。
- [re-wake 首个 page.cards 是 feed 错配包] → noteId 精确匹配使错配无害，只消耗一次尝试；第 2 次重试兜底；不新增协议级配对（与 /comment 同等级容忍）。
- [搜索词=标题截断后歧义、结果第一页无目标] → 仅在返回卡片内精确匹配 noteId，绝不「差不多就评」；宁可 not_found 不误评他帖。
- [参照块与素材块指令冲突] → 参照独立块+明确优先级措辞；素材块规则原样保留。
- [洗稿与参照过近（无程序化查重）] → 现状发布链本就无文本相似度闸；prompt 红线（禁逐句照抄+可辨识差异）+ 飞书人审兜底；程序化相似度闸列为将来项，不在本变更。
- [评论正文长度撑爆 28s 单步] → 既有 MAX_COMMENT_LEN=50 已兜住；群口令经单次 insertText 不占逐字预算。
- [panel-server.ts 与在途变更 retire-default-account 同文件] → 不同分支互不重叠；提交用显式 pathspec；部署 targeted-scp。
- [console 工作树他会话 WIP] → 只改 CuratedContentPage.tsx（+必要时 types/api.ts），显式 pathspec 提交。

## Migration Plan

1. cloud：store 只读方法+panel 路由+deps → publish 参照注入 → comment 定向任务；单测（store/panel/prompts/targeted-runner）+typecheck；显式 pathspec 提交。
2. console：CuratedContentPage.tsx 行内动作；vitest+typecheck+build。
3. 部署：cloud targeted-scp+重启 aidcp-cloud.service+healthcheck；console build+tar-over-ssh 覆盖 /opt/aidcp/console（备份+验活，无需重启）。零 DDL、零 edge——**无需用户更新本地 edge**。
4. 回滚：cloud 备份回滚+重启；console console.bak 目录回滚。
5. 真机验收【用户侧】：①对一条精选笔记触发参照创作→飞书出人审卡→通过→发布成功；②定向内容评论全链路（搜索定位命中率标定）；③带群评论（口令追加+审=发）；④拒绝路径抽查（壳行/已评论/未配口令）。

## Open Questions

- 无阻塞项。真机标定项集中在 D1（搜索命中率、截断策略是否需要调整）——按现有「有界重试+诚实失败」设计，标定只调参不改结构。
