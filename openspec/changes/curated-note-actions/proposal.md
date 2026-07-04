## Why

精选页目前只能「看和删」：收集下来的笔记（curated_content）只能被动地作为创作素材与搜索词来源被抽样消费，运营者无法对某一条具体的好笔记主动下达动作。实际运营需要两类定向动作：①看中某篇笔记，让账号**参照它洗稿创作**一篇自己的帖子；②对收藏的笔记**定向评论**做互动/引流（内容评论，或追加群聊口令的带群评论）。这两条链路（发布生成+人审+下发、搜索驱动评论+人审+发布）都已在生产运行，缺的只是「从精选页的一行触发、并把目标钉死在这一条笔记上」的接线。

## What Changes

> 范围 = aidcp-cloud（panel 新端点 + publish 参照注入 + comment-agent 定向任务）+ aidcp-console（精选页行内动作按钮）。**零 edge 改动、零协议改动**——定向评论复用既有 search.execute / note.open / interaction.comment 消息，参照创作复用既有 publish.command 序列。

- 精选页笔记行（content_type='note'）新增两个行内动作：「参照创作」「定向评论」；评论行（content_type='comment'）不提供动作（未存源笔记 noteId，无法定位）。执行账号固定为该行归属账号（row.accountId），不提供跨账号执行。
- **参照洗稿创作**：新端点 POST /api/curated/contents/:id/create-post（accountId 必带）。云端把该行的标题/正文/话题装配为「参照笔记」注入 TriggerInput，走完整既有发布链路（ContentScout→ContentCreator→配图→飞书人审→publish_takeover→边端发布）。创作 prompt 中参照笔记使用独立条件块（借选题/结构/要点、以人设口吻重写、**禁止逐句照抄**），不混入既有素材块（该块红线「严禁照抄或改写其句子」语义不同）。正文为空的壳行（bot_collect(content_missing)）诚实拒绝。
- **定向评论**：新端点 POST /api/curated/contents/:id/comment（accountId 必带，body.withGroup 区分两种类型）。云端复用 /comment 的受控独占任务骨架，但把「搜索词生成+强相关择优」替换为**定向定位**：以该笔记标题为搜索词、排序=综合、时间窗=不限（默认的「最多收藏+一天内」会筛掉老笔记），在搜索结果中按 noteId 精确匹配卡片→note.open→读现场→撰写→飞书人审→发布。有界重试后找不到目标即诚实失败（note_not_found）。**绝不导航存量 source_url**（xsec_token 过期→300031 风控误判红线）。
  - 内容评论：既有 CommentComposer 撰写链原样复用。
  - 带群评论：复用既有 injectGroup 机制——评论正文同样基于笔记信息自动生成，追加账号配置的群聊口令；账号未配群口令则 fail-closed 诚实拒绝。
- 已评论过的笔记（risk_interactions 去重命中）触发定向评论时诚实拒绝（already_commented），不重复评论。
- 两类动作的 API 返回都是**触发态回执**（triggered / 拒绝原因），不是成功态；终态结果沿既有渠道呈现（发布=飞书人审卡+内容页草稿，评论=飞书人审卡+终态结果卡）。回执三态诚实，绝不把未触发染成成功。

## Capabilities

### New Capabilities

- `curated-note-actions`: 精选页笔记行两类定向动作（参照洗稿创作、定向评论·内容/带群）的触发端点、账号隔离、目标定位方式（搜索驱动、禁存量 URL）、人审保留、单飞与让位、诚实回执契约。

### Modified Capabilities

- `curated-inspiration-corpus`: 「创作消费——精选语料为正向素材唯一来源，仅作灵感不照抄」需求扩展：在既有抽样灵感消费之外，新增**人工指定单条笔记作为洗稿参照**的消费模式（借选题/结构/要点重写，仍禁逐句照抄），参照模式不改变既有抽样素材块的规则。

<!-- panel-curated-content 不做 MODIFIED delta：其既有需求（只读检索/诚实置空/删除单条/清空壳行/降级）行为均不变，本变更的新增动作以新能力 curated-note-actions 承载。另：已部署的「全部账号」合并读视图与 panel-curated-content L6 的账号必带需求存在既有 spec-vs-code 漂移，属另一独立变更（全账号合并总览）的补账范围，本变更刻意不触碰——本变更的写侧动作一律按行归属账号隔离，与该漂移无涉。publish-pipeline 亦不做 MODIFIED delta（其 ADDED delta 仍散布在 3 个在途变更中，沿用 curated-inspiration-corpus 归档时的先例），参照注入的契约写入新能力。 -->

## Impact

- **aidcp-cloud**：
  - panel 层：`src/panel/panel-server.ts` 新增两条 POST 路由（注意手写 if-chain 的路由顺序，静态后缀在前）；`src/panel/types.ts` 新增 curatedActions 依赖接口（缺失→503 诚实降级）。
  - 存储：`src/cache/curated-content-store.ts` 新增按 id+account_id 读单行的只读方法（写侧红线不变，无新表无新列）。
  - 发布侧：`src/publish-agent/types.ts` TriggerInput 增加参照笔记字段；`src/publish-agent/publish-scheduler.ts` triggerManual 支持携带参照；`src/publish-agent/prompts.ts` buildScoutPrompt/buildCreatorPrompt 增加条件性【参照笔记】块。
  - 评论侧：`src/comment-agent/comment-scheduler.ts` 新增定向触发入口；`src/comment-agent/comment-task-runner.ts` 新增定向定位控制流（复用 edge-steps，覆盖 sort/timeWindow）；复用既有人审卡与终态结果卡。
  - 接线：`src/server.ts` 把 publishScheduler/commentScheduler 注入 panel deps。
- **aidcp-console**：`src/pages/CuratedContentPage.tsx` 行内动作按钮 + 页面本地 useMutation（遵循写操作页面本地约定；避开另一会话在 routes.tsx / api/queries.ts 的在途 WIP）。
- **aidcp-edge**：零改动。协议 v2 零改动。
- **数据库**：零 DDL。
- **红线**：AC-PUB 三重人审闸不短路；评论人审（AIDCP_COMMENT_APPROVAL）保留；绝不由裸 noteId 伪造可点链接、绝不导航存量笔记 URL；写侧动作 accountId 必带且入 WHERE（防跨账号越权）；发布全局串行/评论按账号单飞，占用中诚实返回；回执诚实三态。
