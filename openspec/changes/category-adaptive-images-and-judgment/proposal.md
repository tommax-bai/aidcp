## Why

系统定位是**通用全品类、人设（persona）驱动**的小红书自动内容号，但多处 prompt 与判定把「本该随账号人设 / 内容品类 / 话题变化的东西」写死成**技术域**——配图被一段全局固定风格常量锁成「科技蓝扁平 isometric 技术图」（`IMAGE_STYLE_BASE`），质量评审只按「干货/信息密度」打分，收藏与评论门槛以「代码/架构图才配收藏」「固定收藏绝对值」为准。结果是所有账号配图雷同、非技术内容被系统性压低。文本生成侧的「技术帖/小林」硬编码已由活跃 change `persona-driven-content-pipeline`（`aecc1ce` 已部署）修掉；本 change 收口**其余同型缺陷**：把「品类 + 人设自适应」从配图链路一路贯穿到评审、互动与评论门禁。

## What Changes

- **配图链路：全局固定风格 → 品类风格档**。删除无差别拼接的全局常量 `IMAGE_STYLE_BASE`，改为「内容品类 → 风格档」注册表：每帖由配图选题环节判出品类、选定一档风格，逐字复用于本帖全部图（**保「图集帧内一致」不变量**），不同帖因品类不同而不同。同时：主体描述保留中文喂原生 Seedream（停止先翻英文）、去掉 provider 侧与风格档冲突的第二风格源、出图比例由方图改竖版 3:4（先核实线上 Seedream 合法尺寸）。
- **配图真人 / 封面文字分级**（保守口径，用户已定）。取代一刀切「无真人 / 无文字」：默认无脸 / 局部 / 背影，需正脸用「明确非写实虚拟人物」、**绝不写实真人正脸**；封面默认留白由后期程序化叠字。含真人或封面出字的图必过**产后校验**（乱码字 / 是否像可识别真人·名人），命中即丢弃重生成（守「无声假成功」红线）。
- **质量评审：品类自适应 + 接人设**。评审的「内容价值」维度不再单按干货信息密度，改为随品类切子标准（干货看信息量、情感/审美看共鸣与画面感与真实体验）；「真实感」判据改为「是否贴合该账号人设声音」，并把账号人设作为一等入参接进评审。**只改打分口味，不动发布放行阈值 / 降级公式**（AC-PUB）。
- **互动 / 评论门禁：品类自适应**。收藏判定去掉「代码/架构图才配收藏」的技术锁死、收藏率地板按人设/品类可配；评论精品门槛的**固定绝对值**（`likeCount>1000 且 collectCount>300`）改为品类自适应 / 比例 / 按账号可配（保留「宁缺毋滥」稀缺闸与硬数值闸的**存在性**）。**BREAKING**（spec 级）：`comment-interaction` 的硬数值门槛需求被改写。
- **浏览相关性去领域偏见**。卡片点击评估删除「AI/技术=默认兴趣、娱乐/明星=无关」硬编码，改从账号真实兴趣派生相关性；保留「无匹配诚实 skip、不编造相关理由」（不假成功），并保留一个「无论人设都不碰」的全局品牌安全禁区兜底。
- **表达约束按品类分档**。正文感叹号上限由「整篇最多 1 个」一刀切改为按品类/人设分档（生活·情感放宽、干货·克制保持严），且**生成 prompt 与后处理检测口径两侧同步**放宽（否则放宽后的正文仍被判「过量感叹号」推向 rewrite/人审）；评论去 AI 味复用发帖侧检测的部分按短评软化。
- **评论去 AI 味接人设**。评论去 AI 味重写注入该账号人设语气，只去 AI 腔、不把人设声音抹平成通用中庸腔。
- **禁用词校准**。把「不得不说」移出后处理硬检测/扣分（真人常见口头开头、误判为 AI 味）；真正的 AI 结构套话保留。

## Capabilities

### New Capabilities
<!-- 无新增独立能力：所有改动都是对既有能力的需求修正，按 YAGNI 不新造能力/抽象。 -->

### Modified Capabilities
- `publish-multi-image`：配图风格从**全局固定**改为**按内容品类自适应**（帖内一致、帖间有别）；主体语言、比例、真人与封面文字策略随之修订；新增「含真人/封面文字的图须过产后肖像·乱码校验、命中重生成」的诚实性要求。
- `publish-pipeline`：内容质量评审的价值维度与真实感判据**随品类/人设自适应**（不再单一干货口味）；正文标点（感叹号）约束按品类分档，且与后处理检测口径同步；禁用词表校准（移出误判词）。**不改**发布放行阈值 / 降级公式 / forced 必发语义。
- `interaction-appraisal`：收藏判定与浏览相关性评估**去技术域锁死、随账号人设兴趣**；收藏率数值地板由固定值改为按人设/品类可配（保留地板存在性与「0 赞不收藏」防线）。
- `comment-interaction`：评论精品门槛的**固定绝对数值阈值**改为**品类自适应/比例/按账号可配**（保留「必要非充分」的硬闸存在性与每日上限、风控取小、多道稀缺闸）；评论去 AI 味重写**人设感知**。

## Impact

- **aidcp-cloud（`src/publish-agent/`）**：`prompts.ts`（删 `IMAGE_STYLE_BASE`、加 `STYLE_PROFILES` 注册表 + `resolveStyleProfile`、`buildImageSetPlanPrompt`/`buildImagePromptComposerPrompt` 接品类与中文主体、`buildAssemblerPrompt` 接 soul + 品类维度、`buildCreatorPrompt` 感叹号分档、`BANNED_PHRASES` 校准）、`roles/image-set-planner.ts`（分类出 category 写入 `ImageSetPlan`）、`roles/image-prompt-composer.ts`（取档逐字注入、图0封面变体）、`roles/quality-scorer.ts`（extractInput 取 soul）、`seedream-client.ts` + `wanxiang-client.ts`（去第二风格源、竖版尺寸）、`post-processor.ts`（感叹号/禁用词检测接品类参数）、`types.ts`（`ImageSetPlan.category`、`StyleProfile`）、`prompts-preview.ts`（改签名处补 `EXAMPLE_SOUL`/style，保与线上同源）。
- **aidcp-cloud（`src/agents/`）**：`interaction-appraiser-role.ts`（收藏判据去技术示例、收藏率地板可配）、`comment-appraiser.ts`（评论门槛品类自适应/比例）、`content-evaluator.ts`（点击相关性去领域偏见 + 全局品牌安全兜底）、`comment-de-ai-flavor.ts`（去 AI 味接人设 + 短评软化，同步 previewPrompt）。
- **协议 / DB**：不改协议（AC-PROTO 无关）、不改 DB 结构（品类为每帖运行时派生，不落库）。
- **管理后台（aidcp-console）**：**本 change 前端不入范围**。后台「角色 prompt 预览」由 cloud 侧 `prompts-preview.ts` 同源保证自动正确；「让运营在界面手调每账号门禁阈值」列为**后续可选 console follow-up**（本 change 用自动分类 + 代码级品类默认 + 既有 `category_config` 面即可运行）。
- **不在本 change（DO NOT TOUCH）**：残留技术 few-shot（`ENCOURAGED_STYLE`/`FEW_SHOT_EXAMPLES`/scout·title·topic 示例）归 `persona-driven-content-pipeline` 待办 4.6，用「多品类真人范文库按人设匹配」策略落地（用户已定），本 change 只引用不改；`buildDeAiRewritePrompt` 的「逐字冻结」本轮不动；gatekeeper 放行阈值 / `QualityScorer` 降级公式；forced 必发语义；两份 `protocol.ts`；`RiskController` 单写；各判定角色 JSON 契约；已废弃 v1 路径。
- **排期约束**：aidcp-cloud 工作树当前有并发方 WIP（`account-store`/`role-catalog`/`server.ts`/`panel`/`config`），实装须避开其占用文件、与 `split-topic-roles`/`persona-driven-content-pipeline` 协调；每批改后 `test:acceptance` → `test` → `typecheck` 全绿（AC-PROTO/AC-PUB/AC-RISK 必过）；部署走安全序列、绝不碰同机 isales。
