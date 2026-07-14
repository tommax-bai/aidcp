# humanize-interaction-prompts — tasks

> 代码全部落 `../aidcp-cloud`；实装前先 `git fetch` + rebase 最新 master（comment 链文件被 `comment-search-command` 动过）。
> `event-bus/types.ts` 为 §7 热点文件（只加可选字段、不动 `RoleName` 枚举），集成时最后 rebase、提交显式列文件。
> 测试口径按克制原则：关键行为少数用例，LLM 输出观感登记真机 backlog。
>
> **实装收口（aidcp-cloud master `14eda68`，2026-07-07）**：全量 1406/1406、acceptance 44/44、typecheck 净。
> 新增两个共享 helper：`src/agents/persona-format.ts`（`tieredInterests` 兴趣分层，5 角色共用）、`src/agents/interaction-label.ts`（互动动作→中文）。
> **归档待办**：spec 交织，本 change 归档 MUST 排在 `category-adaptive-images-and-judgment` 之后（见 task 9.4）。

## 1. aidcp-cloud — 人设注入对齐（spec: comment-interaction「评论链人设注入」、comment-like-interaction）

- [x] 1.1 `src/agents/comment-appraiser.ts`：prompt 补注 `background` / `tone` / `like_principle` / `behavior_guidelines.style`（对齐 `interaction-appraiser-role.ts:144-149` 样板）；`personaSegments()` 同源更新。 <!-- aidcp-cloud 14eda68 抽 personaHeader()：注入 background/tone/兴趣/style；like_principle 由后续评论判据段承载 -->
- [x] 1.2 `src/agents/comment-like-appraiser.ts`：prompt 补注 `like_principle` / `tone`；三轴固定口径（:204-207）改人设派生（通用负面清单保留：广告 / 带货 / 与正文无关 / 像自己会写的不点）。 <!-- aidcp-cloud 14eda68 personaHeader 含 tone+点赞标准(like_principle)；三轴改「按你上面的点赞标准」，负面清单保留 -->
- [x] 1.3 `src/agents/comment-reviewer.ts`：prompt 补注 `background` / `tone` / `behavior_guidelines.style`。 <!-- aidcp-cloud 14eda68 personaHeader 同 comment-appraiser -->
- [x] 1.4 `src/agents/comment-composer.ts`：prompt 补注 `background`。 <!-- aidcp-cloud 14eda68 personaHeader 含 background/tone/兴趣 -->
- [x] 1.5 `src/agents/comment-de-ai-flavor.ts`：`rewriteAwayFrom` 复用 `personaVoiceLine()`。 <!-- aidcp-cloud 14eda68 撞车改写路径接 personaVoiceLine()，soul 缺失诚实降级 -->

## 2. aidcp-cloud — 评判模板去口味化（spec: interaction-appraisal「点赞是选择性互动…」MODIFIED）

- [x] 2.1 `src/agents/interaction-appraiser-role.ts`：「决策逻辑」段只留动作空间语义，口味判据引用人设原则；兜底 `likePrinciple`「轻量高频」改选择性表述。 <!-- aidcp-cloud 14eda68 like/collect 行改「按你上面的点赞/收藏标准」；LIKE_PRINCIPLE_FALLBACK 改选择性、去「轻量高频」 -->
- [x] 2.2 既有 `interaction-appraisal` 回归用例同步更新，硬闸行为用例保持原样通过。 <!-- aidcp-cloud 14eda68 藏赞比闸/0赞防线/both映射/预算过滤全绿、机制零改 -->

## 3. aidcp-cloud — 评论精品门槛默认地板（spec: comment-interaction「精品门槛…」MODIFIED；用户定案①）

- [x] 3.1 `COMMENT_MIN_LIKES` 1000→300、`COMMENT_MIN_COLLECTS` 300→100、`COMMENT_HIGH_LIKES` 10000 不动；头部注释同步。 <!-- aidcp-cloud 14eda68 comment-appraiser.ts:23-27；门槛单测重写(300/100 边界+中腰部500/150入选+10001豁免) -->

## 4. aidcp-cloud — 决策上下文注入（spec: interaction-appraisal「互动决策注入阅读体验与会话状态」ADDED）

- [x] 4.1 `onReadingDone` 注入阅读体验；缺失诚实不注。 <!-- aidcp-cloud 14eda68 **偏离**：keyPoints 全链路恒空(唯一发出者 comment-reviewer:102 硬编码 [])——改为主注入真实流动的 imagesBrowsed/commentsRead(「你刚读完这篇：翻了 N 张图」)，keyPoints 做「非空才注入」的休眠钩子(将来有深读角色填充即生效)，空则省略绝不编造 -->
- [x] 4.2 用起 `sessionContext` 死参，注入会话状态；不放温度。 <!-- aidcp-cloud 14eda68 interaction-appraiser + comment-reviewer 均存起 sessionContext(原死参)；会话状态=visitedCount(真实,新增 getter)+recentInteractions 有界环(互动后累积,新增 recordInteraction)；温度锁 0 不动(遵 role-llm-config「判定类不开温度」) -->
- [x] 4.3 删「剩余预算 like=N」裸数字行。 <!-- aidcp-cloud 14eda68 删除；buildPrompt 不再收 budget 参、预算过滤仍在解析层 -->

## 5. aidcp-cloud — 选卡受控好奇豁免（spec: interaction-appraisal「互动筛选全程从严」MODIFIED；用户定案③）

- [x] 5.1 `content-evaluator.ts`：注入可选 `random`，掷骰命中才追加好奇许可；诚实 skip / 品牌安全不变。 <!-- aidcp-cloud 14eda68 CURIOSITY_EXEMPTION_PROBABILITY=0.12；构造器第3参 random(默认 Math.random)；命中追加「兴趣之外」许可行，未命中逐字不变；单测 random=0/0.99 两态 -->

## 6. aidcp-cloud — 评论链语境穿透与言语行为多样化（spec: comment-interaction「撰写语境穿透…」ADDED +「四段单职责」MODIFIED）

- [x] 6.1 `comment.appraised` payload 加可选 `reason?`；appraiser 判「评」带上。 <!-- aidcp-cloud 14eda68 event-bus/types.ts 加可选 reason(不动 RoleName)；单测断言穿透 -->
- [x] 6.2 撰写 prompt 注入语境。 <!-- aidcp-cloud 14eda68 **偏离**：注入 reason/互动类型(interactionLabel)/作者名三个真实信号；当页评论**自主浏览路径无来源**(未新增跨角色管线,遵 design D4「不改事件时序」)——onPageComments 仍只由命令路径(composeDraft, /comment)注入,自主路径诚实不注 -->
- [x] 6.3 切入角可选面板 + 长度放松 + `nothing_genuine` 弃权出口。 <!-- aidcp-cloud 14eda68 输出扩 {text}|{decline:nothing_genuine}→comment.skipped；切入面板(共鸣/真问题/经历/纯情绪)；长度「一般一两句可以更短」平台上限硬闸保留；parseOutput 统一处理 -->

## 7. aidcp-cloud — 去 AI 味评论体裁召回修复（spec: comment-interaction「去 AI 味信号集覆盖评论体裁」ADDED +「四段单职责」MODIFIED）

- [x] 7.1 评论体裁客套句集，命中 1 触发改写；发帖侧零改。 <!-- aidcp-cloud 14eda68 COMMENT_AI_PHRASES(14 条高精度客套句)；PostProcessor 加可选 extraPhrases+rewriteThreshold=1(加性,发帖侧默认 2/无 extra 不变)；感叹号上限放宽到 3(评论活泼调性)；单测客套触发/口语不触发 -->
- [x] 7.2 改写指令等长约束改「可以更短更随口」。 <!-- aidcp-cloud 14eda68 buildRewritePrompt 与 previewPrompt 同源改 -->

## 8. aidcp-cloud — 卫生清理（spec: interaction-appraisal「判定 prompt 去评分器姿态」ADDED）

- [x] 8.1 删死 `confidence` 输出示例字段。 <!-- aidcp-cloud 14eda68 interaction_appraiser/content_evaluator/comment_reviewer 输出示例去 confidence；解析器容忍旧输出(content_evaluator 仍默认 0.7、无消费方) -->
- [x] 8.2 判定段第一人称口语 + 兴趣主/次分层。 <!-- aidcp-cloud 14eda68 comment_reviewer/content_evaluator 公文→口语；tieredInterests 共享 helper(persona-format.ts)「主要关注…；也会看…」 5 角色共用 -->

## 9. 回归、集成与部署（控制仓编排）

- [x] 9.1 全量回归：`test:acceptance` + `test` + `typecheck`。 <!-- aidcp-cloud 14eda68 acceptance 44/44、full 1406/1406、typecheck 净 -->
- [x] 9.2 集成：rebase → 推送 → 部署 dev → healthcheck + 观察互动决策日志。 <!-- aidcp-cloud 14eda68 已 land 到 master(ff 155ce52..14eda68)；dev 部署 origin/master@5a5a556 快照(含 sibling remote-captcha-assist)，backup cloud.bak.20260707-122617.tar.gz+.env，healthcheck 全绿(active/8787/PG/飞书长连/markers 300-100+budget行删) --> <!-- 2026-07-07 dev deployed -->
- [x] 9.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（簇 13）。 <!-- 控制仓 defd4ee 簇13 五项 -->
- [x] 9.4 `openspec validate --strict` → **确认 `category-adaptive-images-and-judgment` 已先归档（spec 交织按序）** → archive 本 change。<!-- 2026-07-15：category-adaptive 已先归档（其无-固定数值门槛版先写入主 spec）；本 change 归档 MODIFIED「精品门槛」超集（通用默认地板 赞>300 且（藏>100 或 赞>10000））覆盖之 = 与 cloud 代码 COMMENT_MIN_LIKES=300/COMMENT_MIN_COLLECTS=100 对齐。归档后核实主 spec 含「通用默认地板」+ 500赞/150藏 scenario。 -->
