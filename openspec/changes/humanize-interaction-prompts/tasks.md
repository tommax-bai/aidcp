# humanize-interaction-prompts — tasks

> 代码全部落 `../aidcp-cloud`；实装前先 `git fetch` + rebase 最新 master（comment 链文件被 `comment-search-command` 动过）。
> `event-bus/types.ts` 为 §7 热点文件（只加可选字段、不动 `RoleName` 枚举），集成时最后 rebase、提交显式列文件。
> 测试口径按克制原则：关键行为少数用例，LLM 输出观感登记真机 backlog。

## 1. aidcp-cloud — 人设注入对齐（spec: comment-interaction「评论链人设注入」、comment-like-interaction）

- [ ] 1.1 `src/agents/comment-appraiser.ts`：prompt 补注 `background` / `tone` / `like_principle` / `behavior_guidelines.style`（对齐 `interaction-appraiser-role.ts:144-149` 样板）；`personaSegments()` 同源更新。验证：单测断言 prompt 含性格字段。
- [ ] 1.2 `src/agents/comment-like-appraiser.ts`：prompt 补注 `like_principle` / `tone`；三轴固定口径（:204-207）改人设派生（通用负面清单保留：广告 / 带货 / 与正文无关 / 像自己会写的不点）。验证：单测断言判据段引用人设原则、不含钉死三轴措辞。
- [ ] 1.3 `src/agents/comment-reviewer.ts`：prompt 补注 `background` / `tone` / `behavior_guidelines.style`。验证：单测断言注入存在。
- [ ] 1.4 `src/agents/comment-composer.ts`：prompt 补注 `background`。验证：既有单测通过 + 注入断言。
- [ ] 1.5 `src/agents/comment-de-ai-flavor.ts`：`rewriteAwayFrom` 复用 `personaVoiceLine()`（一行改动，与主改写路径同源）。验证：单测断言撞车改写 prompt 含人设口吻行、soul 缺失时诚实降级不抛。

## 2. aidcp-cloud — 评判模板去口味化（spec: interaction-appraisal「点赞是选择性互动…」MODIFIED）

- [ ] 2.1 `src/agents/interaction-appraiser-role.ts`：「决策逻辑」段（:158-162）只留动作空间语义（like/collect/both/pass 含义、收藏更稀有、多数 pass、收藏倾向 both），口味判据改为引用上文人设原则；兜底 `likePrinciple` 文本（:141「轻量高频」）改为选择性表述，与框定一致。验证：单测断言模板段无内联口味判据、兜底文本无「轻量高频」。
- [ ] 2.2 既有 `interaction-appraisal` 回归用例同步更新（prompt 断言随新模板调整），收藏藏赞比闸 / 0 赞防线 / both 映射 / 预算过滤等行为用例全部保持原样通过（硬闸机制零改动）。

## 3. aidcp-cloud — 评论精品门槛默认地板（spec: comment-interaction「精品门槛…」MODIFIED；用户定案①）

- [ ] 3.1 `src/agents/comment-appraiser.ts:23-27`：`COMMENT_MIN_LIKES` 1000→300、`COMMENT_MIN_COLLECTS` 300→100、`COMMENT_HIGH_LIKES` 10000 不动；头部注释同步（默认地板语义 + 与 category-adaptive 可配表述的关系）。验证：门槛单测更新（边界严格大于：300/100 恰等于不达标；500 赞 150 藏达门槛；10001 赞低藏豁免达门槛）。

## 4. aidcp-cloud — 决策上下文注入（spec: interaction-appraisal「互动决策注入阅读体验与会话状态」ADDED）

- [ ] 4.1 `src/agents/interaction-appraiser-role.ts`：`onReadingDone` 保留 payload 的 `keyPoints` / `imagesBrowsed` 并注入 prompt（「你刚读完，印象最深的是…」，keyPoints 限幅前 2-3 条）；缺失诚实不注。验证：单测——有 keyPoints 时 prompt 含印象段、空时无该段且不编造。
- [ ] 4.2 `src/agents/interaction-appraiser-role.ts` + `src/agents/comment-reviewer.ts`：用起 `sessionContext` 死参，注入一两句会话状态（本次已刷 N 篇、刚点过什么；comment_reviewer 服务 detail-deep-read 既有「拟人化多样性」条文）。验证：单测断言状态行存在且随 ctx 变化；不放开温度（role-catalog 零改动）。
- [ ] 4.3 「剩余预算 like=N，collect=M」裸数字行（:156）删除（解析层预算过滤与调 LLM 前 skip 行为不变）。验证：既有预算行为用例通过、prompt 断言无台账行。

## 5. aidcp-cloud — 选卡受控好奇豁免（spec: interaction-appraisal「互动筛选全程从严」MODIFIED；用户定案③）

- [ ] 5.1 `src/agents/content-evaluator.ts`：构造器注入可选 `random`（默认 `Math.random`，测试可注入）；每评估轮掷骰（导出常量 `CURIOSITY_EXEMPTION_PROBABILITY = 0.12`），命中才在 prompt 追加好奇许可一句；未命中轮 prompt 与现状逐字一致；品牌安全禁区与诚实 skip（`content.no_valuable`）语义不变。验证：单测——random 注入 1.0 时 prompt 无好奇行、注入 0.0 时含好奇行；skip 路径不受影响。

## 6. aidcp-cloud — 评论链语境穿透与言语行为多样化（spec: comment-interaction「撰写语境穿透…」ADDED +「四段单职责」MODIFIED）

- [ ] 6.1 `src/event-bus/types.ts`：`comment.appraised` payload 加可选 `reason?: string`（不动 `RoleName`；热点文件——集成时最后 rebase、提交显式列文件）。`comment-appraiser.ts` 判「评」时带上 reason。验证：typecheck + 单测断言 payload 穿透。
- [ ] 6.2 `src/agents/comment-composer.ts`：prompt 注入（有则注、无则省）——appraiser reason（「你刚才觉得这篇值得评，因为…」）、本次互动类型（like/collect）、作者名；当页评论头部摘要（3-5 条限幅）——实装时先核实取数源（`comment_like_appraiser` 候选缓存 vs `scroll_comments` 上报缓存）的事件时序，两者都取不到诚实不注（design D4/Open Questions）。验证：单测——各注入项有/无两态；缺数据不编造占位。
- [ ] 6.3 `src/agents/comment-composer.ts`：切入角改可选面板（共鸣 / 真问题 / 自己的相关经历 / 纯情绪短评）；长度表述改「一般一两句，可以更短、更随口」（平台上限硬闸保留）；补语义弃权出口——输出格式扩为 `{"text":...}` 或 `{"decline":"nothing_genuine"}`，解析到 decline 走 `comment.skipped{reason:'nothing_genuine'}`（评论支线直通、下游进主页评估不受影响）。验证：单测——decline 输出走 skip 不进去 AI 味；空文本既有跳过行为不回归。

## 7. aidcp-cloud — 去 AI 味评论体裁召回修复（spec: comment-interaction「去 AI 味信号集覆盖评论体裁」ADDED +「四段单职责」MODIFIED）

- [ ] 7.1 `src/agents/comment-de-ai-flavor.ts`：增设评论体裁专用信号集（客套模板句「感谢分享」「学到了」单句成评、空洞附和、和稀泥句式——初版人工校准，参照「不得不说」移出先例），命中 1 条即触发人设口吻改写；发帖侧词表 / 阈值零改动。验证：单测——「感谢分享，学到了！」被检出触发改写、正常人话不触发；发帖侧用例不动。
- [ ] 7.2 改写指令等长约束改「保持原意、可以更短更随口」（`buildRewritePrompt` 与 `previewPrompt` 同源，守 prompt-preview 同源红线）。验证：preview 单测同步。

## 8. aidcp-cloud — 卫生清理（spec: interaction-appraisal「判定 prompt 去评分器姿态」ADDED）

- [ ] 8.1 删全家族输出示例的死 `confidence` 字段（interaction_appraiser / content_evaluator / comment_appraiser / comment_reviewer / search_evaluator 等六处；解析器本就不读、容忍旧输出，零解析改动）。验证：grep 无 confidence 示例残留、既有解析用例通过。
- [ ] 8.2 `comment_reviewer` / `content_evaluator` 判定段公文语域改第一人称口语（「评估维度」「候选」→使用者视角）；兴趣主 / 次分层表述（「主要兴趣…也关注…」三个角色通用一行）。验证：prompt 断言更新；previewPrompt / personaSegments 同源不漂移。

## 9. 回归、集成与部署（控制仓编排）

- [ ] 9.1 全量回归：`cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`（安全红线 AC-* 全过；协议 / 风控 / 发布零改动，预期无相关面波动）。
- [ ] 9.2 集成：rebase 最新 master → 提交推送（显式列文件，勿 `git add -A`）→ 按 §5 安全序列部署 dev → healthcheck + 观察互动决策日志（「互动决策可观测」既有日志对比 like/collect/pass 分布与评论候选量）。
- [ ] 9.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：多账号判定差异抽查（同笔记不同人设不同判定）、评论文本观感与去 AI 味触发率（从近 0 恢复到有效区间）、门槛 300/100 后评论候选量与人审压力、好奇豁免命中轮的选卡观感。
- [ ] 9.4 `openspec validate humanize-interaction-prompts --strict` → 确认 `category-adaptive-images-and-judgment` 已先归档（spec 交织按序）→ archive 本 change。
