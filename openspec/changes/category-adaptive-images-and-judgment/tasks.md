# Tasks — category-adaptive-images-and-judgment

> 落地仓：全部在 **aidcp-cloud**（`../aidcp-cloud`）。本仓只回写进度。
> 排序铁律：动手前先做第 0 组前置（核实 Seedream 尺寸、避开并发方 WIP 文件、与 `split-topic-roles`/`persona-driven-content-pipeline` 协调）。
> 每组改完按 CLAUDE.md §4：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（AC-PROTO/AC-PUB/AC-RISK 必过）；按需走 §5 安全序列部署、绝不碰 isales。
> 分批独立可测可部署，组间无强依赖（第 4 组感叹号是唯一「生成+后处理」双侧同步点）。
>
> **进度（2026-07-02）**：
> - **第 1 组（配图风格档 + 品类判定角色）已实装 + 测试全绿 + 已推 master**（aidcp-cloud `2769a88`）。删全局 `IMAGE_STYLE_BASE` → `STYLE_PROFILES`(10 档：9 品类 + 兜底 general) + `resolveStyleProfile`；新增独立 flash 角色 `CategoryClassifier`（watch `createdContent` → 写 `PostCategory`，判不出恒回落 general 防 composer waitAll 挂死）；composer 改 `waitAll [imageSetPlan, postCategory]`、图0封面变体/图1..N内页 styleBase 逐字复用、主体保留中文、`imageStyle=null`；去 provider 第二风格源；preview 同源 + 新角色登记 role-catalog。
> - **偏离**：品类不挂 `ImageSetPlan.category`，改为独立 `PipelineFields.postCategory`（分类角色单独产出、下游复用），比挂选题对象更解耦。人物策略（2.1）直接写进各档 `styleBase` 串而非独立字段（YAGNI）。
> - **2.1 顺带完成**（人物三档已写进各档 styleBase）；**1.7/0.2 未完**：比例仅到 prompt 层（styleBase 含 `vertical 3:4`），provider `defaultSize`(2048 方图) 未改——待 0.2 核实线上 Seedream 合法竖版尺寸后再改像素。
> - **并发坑记录**：批中并发方又起 `edit-note-draft-before-publish` WIP 污染共享工作树（`feishu/*`/`panel/*`/`publish-dispatcher`/`server.ts`）。提交用精确逐文件 staging + `server.ts` 只挑含 `CategoryClassifier` 的 hunk（`git apply --cached`），未卷入其 WIP；全量 1 失败(`buildPublishApprovalCard`)为其 WIP、与本批无关。
> - **第 3 组（质量评审接人设 + 品类自适应）已实装 + 测试全绿 + 已推 master**（aidcp-cloud `86bb0e0`，叠在并发方已提交的 `8eb0664` edit-note-draft 之上、只含我 3 文件）。`buildAssemblerPrompt` 加 `soul` + 品类：「真实感」→「贴合人设声音」、「内容价值」维度按品类切子标准（`QUALITY_VALUE_HINTS`）、few-shot 去技术腔；`QualityScorer.extractInput` 取 `trigger.generateInput.soul` + `postCategory`；preview 同源。**未动**放行阈值/降级公式/getDefaultOutput=50（AC-PUB）。tests: 13/13 + acceptance 27/27。
> - **第 6 组（浏览去偏见 + 评论去 AI 味接人设）已实装 + 测试全绿 + 已推 master**（aidcp-cloud `f9f270c`）。`content-evaluator` 删「娱乐/明星=无关、与AI/技术相关」硬编码 → 从账号真实兴趣派生 + 诚实 skip + 全局品牌安全底线；`comment-de-ai-flavor` 去 AI 味按人设语气重写（`this.soul`，未注入诚实降级）、抽共享 `buildRewritePrompt` 让 rewrite/previewPrompt 同源，**4.4 顺带完成**（感叹号软化）。tests 46/46 + acceptance 27/27。
> - **第 4 组（感叹号双侧分档 + BANNED 校准）已实装 + 测试全绿 + 已推 master**（aidcp-cloud `ca415da`）。`buildCreatorPrompt` 感叹号改按语气克制；`post-processor` 加 `exclamationMaxForTone`(casual/narrative→3 否则1) + `detectBannedPhrases`/`process` 参数化，`ContentCleaner` 按 `created.tone` 传入（生成+后处理同一口径）；`BANNED_PHRASES` 移除「不得不说」。tests 20/20 + acceptance 27/27。
> - **第 5 组（互动/评论门禁品类自适应）已实装 + 测试全绿 + 已推 master**（aidcp-cloud `4a0f321`）。`interaction-appraiser` 收藏判据去技术示例 + 订正收藏率注释（审美类经既有 getMinSaveLikeRatio 钩子调低）；`comment-appraiser` 门槛从固定「赞>1000且藏>300」改「赞>1000 且（藏>300 或 赞>10000 高热爆帖豁免）」——治高赞低藏爆帖被固定藏300排除、主条件不放松、pre-LLM 便宜确定性、稀缺闸不动。对应 comment-interaction spec MODIFIED。tests 32/32 + acceptance 27/27。
> - **✅ 已部署上线（2026-07-03）**：5 批全部在 ECS 生产运行。探测发现并发方 07-03 00:14-00:21 一次整体升 HEAD 已把 batch 1/3/6 带上线；本次 scoped rsync 只补 batch 4（`ca415da`）+ batch 5（`4a0f321`）的 5 文件（prompts/post-processor/content-cleaner/interaction-appraiser/comment-appraiser）。安全序列：备份 `cloud.bak.20260703-095110.tar.gz` + `.env` → rsync → `systemctl restart` → healthcheck 全绿（active / 8787 / PG select 1 / 存储就绪 / PublishOrchestrator 25 角色含 `CategoryClassifier` / 飞书 onReady / 零启动错误）→ isales 未碰。<!-- aidcp-cloud 4a0f321 2026-07-03 deployed（batch1/3/6 由并发方整体升 HEAD 带上、batch4/5 scoped rsync 补齐）-->
> - **剩余（均有外部依赖/开放子决策，待用户）**：**2.2/2.4 配图产后校验**（需定「乱码/肖像」视觉核验机制——轻规则 or 二次视觉模型，涉成本/延迟/新能力）；**1.7/0.2 出图竖版像素**（需连 ECS 探线上 Seedream 版本+合法尺寸，风格档文本已写 vertical 3:4）。已完成 6 个代码批中的 5 个（1/3/4/5/6 + 2.1/4.4），**全部已上线**。

## 0. 前置与排序（务必先做）

- [x] 0.1 `openspec list` + `git -C ../aidcp-cloud status` 确认并发方 WIP 占用文件（`prompts.ts`/`role-catalog.ts`/`server.ts`/`panel`/`config`）当前状态；本 change 改 `prompts.ts` 须与 `persona-driven-content-pipeline`/`split-topic-roles` 协调、避免同文件互吞。
- [ ] 0.2 核实 ECS 线上实跑 Seedream 版本（代码默认 `doubao-seedream-4-5-251128` vs 台账 `5-0-260128`）及其同步 `/images/generations` 允许的合法 size 串与推荐 3:4 尺寸；万相对应竖版尺寸。据此决定第 1 组比例改动同批做还是拆后（尺寸不确定则先只上风格档、比例拆到后续）。
- [x] 0.3 新增品类判定角色须动【角色目录 / 角色索引 / 装配】——正是并发方 WIP 占用文件（`role-catalog.ts` / `server.ts` / `roles/index.ts`）。此步排在这几文件稳定或与并发方协调后做，避免同文件互吞（搭车加字段本可绕开、独立角色绕不开）。

## 1. 配图风格档 + 中文主体 + 去第二风格源（aidcp-cloud）

- [x] 1.1 `src/publish-agent/types.ts`：新增 `Category` 字面枚举（干货/知识、美妆护肤、美食、穿搭、旅行、家居、情感/治愈、职场/成长、技术示意图 + 兜底档）与 `StyleProfile` 类型；`ImageSetPlan` 增 `category: Category`。
- [x] 1.2 `src/publish-agent/prompts.ts`：删 `IMAGE_STYLE_BASE`（:361），新增 `STYLE_PROFILES: Record<Category, StyleProfile>`（每档 styleBase/palette/人物策略/比例/封面变体/品类 few-shot，取自 design 附的 9 档）+ `resolveStyleProfile(category, {cover})`。
- [x] 1.3 `src/publish-agent/prompts.ts`：新增 `buildCategoryClassifierPrompt`（输入品类枚举 + 正文、只输出单个 category）；`buildImagePromptComposerPrompt` 停止「翻成英文主体」（主体保留中文、只补动作/场景、不写风格词），few-shot 换成按 category 注入的对应示例（去 isometric 分布式系统例）。`buildImageSetPlanPrompt` 不再承担分类（分类归品类判定角色）。
- [x] 1.4 新增【品类判定角色】（发布侧，`src/publish-agent/roles/` + 装配）：flash 模型、输入品类枚举 + 正文、schema 约束输出单个 `category` + 校验重试；判不出/枚举外回落安全兜底档、绝不 brick；**一帖判一次**写入管线状态供配图选题与质量评审消费；登记角色目录（`role-catalog.ts` displayName + `role-llm-config`）供后台配模型。⚠️ 触 `role-catalog.ts` / `server.ts` / `roles/index.ts` 装配——见 0.3 排期。
- [x] 1.5 `src/publish-agent/roles/image-prompt-composer.ts`：把 :86 的 `${desc}. ${IMAGE_STYLE_BASE}` 改为 `resolveStyleProfile(category)`（category 来自品类判定角色、经管线状态传入）取一次——图 0 用 `coverStyleBase`、图 1..N 用 `styleBase` 逐字复用；保留现有去重护栏与「永远保住第 0 张」。
- [x] 1.6 `src/publish-agent/roles/image-generator.ts` + `seedream-client.ts` + `wanxiang-client.ts`：ImageGenerator 生成时不再把 `imageStyle` 枚举传给 provider（消除 `seedream-client.ts:81` 的「，风格：<enum>」第二风格源）。
- [ ] 1.7 （依赖 0.2）比例竖版化：`SeedreamClient`/`WanxiangClient` 的 `defaultSize` 由方图改合法竖版 3:4（或经 env 在 `server.ts` 注入）；全帖同比例。尺寸未核实则本任务拆到后续、不乱填。
- [x] 1.8 `src/publish-agent/prompts-preview.ts`：图像示例（EXAMPLE_IMAGE_SUBJECT/科技扁平）随真源改为按品类示例，保预览与线上同源（真源先改、再同步预览）。
- [x] 1.9 回归：不同品类帖得到不同风格档、同帖内一致（对应 spec「配图风格按内容品类自适应」两 Scenario）；未知品类回落不阻断；无第二风格源；typecheck。

## 2. 配图真人/封面文字分级 + 高风险图产后校验（aidcp-cloud）

- [x] 2.1 在各品类 `StyleProfile` 落人物三档（默认无人 / 无脸匿名 / 需正脸用明确非写实虚拟人物，绝不写实真脸）与封面文字策略（默认留白 + 后期叠字）。
- [ ] 2.2 新增产后校验：仅对「含真人或封面出字」的图做（乱码字 / 是否像可识别真人·名人），命中丢弃该张重生成；无则靠内页 no-text + faceless 默认兜底。实现为轻量规则 + 可选二次模型判定（首版覆盖子集即可）。
- [ ] 2.3 合规 AI 标识确认走既有 `ComplianceDecision.ai/aiEnforced` + 发布声明/元数据，MUST NOT 让模型画面内画水印。
- [ ] 2.4 回归：需人物时不出写实真脸；高风险图未过校验即重生成（对应 spec「配图真人与封面文字分级并对高风险图产后校验」两 Scenario）。

## 3. 质量评审接人设 + 品类自适应维度（aidcp-cloud）

- [x] 3.1 `src/publish-agent/prompts.ts` `buildAssemblerPrompt`：加 `soul` 入参，注入 identity.role/tone/interests + 本帖 `style.type`/品类；「内容价值」维度改品类自适应（干货看信息量 / 情感·审美看共鸣·画面感·真实体验）、「真实感」改「贴合人设声音」；:468 技术 few-shot 换品类中性。
- [x] 3.2 `src/publish-agent/roles/quality-scorer.ts`：`extractInput` 从 `snapshot.trigger.generateInput.soul` 取 soul，更新调用点。
- [x] 3.3 `src/publish-agent/prompts-preview.ts:97`：补 `EXAMPLE_SOUL`/style 入参（改签名后 typecheck 会红——同源守卫）。
- [x] 3.4 核对不动放行闸：`gatekeeper` 阈值（auto≥75/manual/retry/abort）、`QualityScorer` 降级公式 `round((1-aiScore)*70)`、`getDefaultOutput=50` 一律未改（AC-PUB）。
- [x] 3.5 回归：情感类不因缺硬信息被压低、评审 prompt 含人设声音、降级公式与放行分支不变（对应 spec「内容质量评审随品类与人设自适应」三 Scenario）。

## 4. 感叹号按品类分档 + 后处理口径同步（aidcp-cloud，唯一双侧 sync）

- [x] 4.1 `src/publish-agent/prompts.ts` `buildCreatorPrompt`（:217）：感叹号上限**主要按人设分档**（活泼/生活人设放宽、克制人设保持严），保留排比套话禁令。注：正文创作发生在品类判定之前、此时无内容品类，故以人设为主轴、不依赖内容品类。
- [x] 4.2 `src/publish-agent/post-processor.ts`：`EXCLAMATION_RE`（:16）与 `detectBannedPhrases` 的「过量感叹号」虚拟命中（:37-40）接受同一品类/人设参数，避免放宽后仍被判过量推向 rewrite/manual。
- [x] 4.3 `src/publish-agent/prompts.ts` `BANNED_PHRASES`（:30）校准：把「不得不说」移出后处理硬检测/扣分（保留真正 AI 套话如首先/其次/综上所述/众所周知）；若一并动「各有千秋/各有优劣」须同步清 `ENCOURAGED_STYLE:40`/`NEGATIVE_EXAMPLES:66` 的引用以免生成/检测口径自相矛盾（本轮可暂不动这两词）。
- [x] 4.4 `src/agents/comment-de-ai-flavor.ts`（:23 复用发帖 `PostProcessor`）：仅微调 rewrite 措辞「保留自然口语感叹、只在明显模板套话时收敛」并同步 `previewPrompt`（避免过度设计，不注入独立配置）。
- [x] 4.5 回归：生活类放宽感叹号且检测同步不被判过量、干货类仍克制（对应 spec「正文标点表达按品类分档且生成与后处理检测口径同步」两 Scenario）。

## 5. 互动/评论门禁品类自适应（aidcp-cloud）

- [x] 5.1 `src/agents/interaction-appraiser-role.ts`（:160）：删「代码/架构图才配收藏」技术示例，改品类中立可复用性、具体类型交上文已注入的收藏原则；（:26）`COLLECT_MIN_SAVE_LIKE_RATIO` 默认随人设/品类可配（审美/灵感类放宽/旁路），订正注释去「硬核=唯一收藏标准」假定；保留地板存在性与「0 赞不收藏」防线。
- [x] 5.2 `src/agents/comment-appraiser.ts`（:98）：把评论精品门槛的固定绝对值（`likeCount>1000 且 collectCount>300`）改为品类自适应/比例/按账号可配（默认按品类给合理值）；**勿用宽松纯 OR**（成本）；保留「必要非充分」硬门槛存在性、每日上限、风控取小、LLM 精品 + 飞书人审多道稀缺闸；门槛在调 LLM 前确定性判定。
- [x] 5.3 回归：高赞低藏爆帖不再被固定绝对值一律排除、审美类账号收藏率放宽、稀缺闸/每日上限/风控取小不移除（对应 `comment-interaction` MODIFIED 与 `interaction-appraisal` ADDED 的 Scenario）。

## 6. 浏览相关性去偏见 + 评论去 AI 味接人设（aidcp-cloud）

- [x] 6.1 `src/agents/content-evaluator.ts`（:179）：删「AI/技术=默认兴趣、娱乐/八卦/明星=无关」硬编码，改从已注入 `interestsStr` 派生相关性；保留「无匹配诚实 skip、不编造相关理由」；加一个「无论人设都不碰」的全局品牌安全禁区兜底。
- [x] 6.2 `src/agents/comment-de-ai-flavor.ts` `rewrite`（:116）/`rewriteAwayFrom`（:96）：拼入与 `CommentComposer` 同源的人设片段（`this.soul` 已可达），「改成更像真人随手留言」改为「用该人设语气重写、只去 AI 腔」，保留原有约束；同步 `previewPrompt`（:108）。
- [x] 6.3 回归：娱乐/明星人设不再被判无关、无匹配诚实 skip、全局禁区兜底生效（对应 `interaction-appraisal`「相关性与收藏判定去题材硬编码」三 Scenario）；评论去 AI 味体现人设语气。

## 7. 测试与部署

- [x] 7.1 每组改完：`cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；AC-PROTO/AC-PUB/AC-RISK 必过；preview 同源 typecheck 守卫过。
- [x] 7.2 绿后按批 commit（末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context)`），进度回写本 tasks.md（`<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`）。
- [x] 7.3 按需部署走 §5 安全序列（ECS 先备份 → rsync `--exclude .env --exclude node_modules --exclude .git` → `systemctl restart aidcp-cloud.service` → healthcheck active/8787/8090/飞书 onReady/PG select 1 → 失败回滚），避开并发方 WIP、绝不碰同机 isales。
