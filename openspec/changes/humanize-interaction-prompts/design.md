# humanize-interaction-prompts — 设计

## Context

浏览闭环互动决策链的 8 个 LLM 角色（`aidcp-cloud/src/agents/`）经拟人化审计确认：架构层拟人化扎实（人设硬前置、fail-closed、随机性与节奏在代码层、格式污染隔离在幕后），短板集中在 prompt 层——人设只用兴趣一层、固定模板盖过人设口味、决策零随机零当下状态、评论链语境盲判、去 AI 味对评论体裁零召回。

已有的正确样板（改进对齐目标，勿破坏）：
- 人设注入样板：`interaction-appraiser-role.ts:144-149`（background / tone / 两条互动原则全注入且承重）。
- 随机性分层样板：`comment-like-appraiser.ts`（伯努利掷骰在代码层、random 可注入测试、LLM 只做价值判断不「假装随机」）。
- 诚实弃权样板：`comment_like_appraiser` 解析失败 / 选「都不点」= 弃权，绝不默认挑第一条。

用户定案边界（本设计的硬约束）：硬数值闸机制不动（仅评论门槛常量 1000→300 / 300→100）；`author_evaluator` 整文件不动（进主页放松必须与频率闸捆绑，整体推迟到下一 change）；好奇心出口是新增豁免层非改现有闸。

## Goals / Non-Goals

**Goals:**
- 把人设从「话题过滤器」升级为「性格来源」：性格字段（tone / background / 互动原则 / 浏览风格）进入所有判定与产文角色。
- 消除全 fleet 统一的口味模板：固定评判段只留动作空间语义，判据由人设派生——不同人设产生可区分的行为分布。
- 给决策引入当下状态：深读体验与会话进度进 prompt；选卡有受控的好奇出口。
- 评论链打通语境、放开言语行为分布、修复去 AI 味对评论体裁的零召回。
- 评论精品门槛默认地板降到 300 / 100（覆盖中腰部高收藏内容）。

**Non-Goals:**
- 不改任何硬数值闸的机制（藏赞比地板、评论点赞比率闸、滚动深度公式原样保留）。
- 不动 `author_evaluator`（进主页判定 + 频率闸留下一 change 捆绑做）。
- 不放开判定类角色温度（见 D3）。
- 不动发布侧同款问题（`publish-agent/post-processor` 无人设——属 `publish-trigger-and-apply` 地盘）。
- 不新增人设 schema 字段（「开口欲 / 评论区习惯」等行为字段留扩展缝，先用现有 `behavior_guidelines.style` 承载浏览风格）。
- 不追求「LLM 输出观感」的单测覆盖（真机项，登记 backlog）。

## Decisions

**D1 口味判据的分层：动作语义留模板、判据来自人设、负面清单留硬规则。**
固定「决策逻辑」段退化为纯动作空间说明（like / collect / both / pass 各自含义、收藏更稀有、多数 pass 的克制先验）；「什么内容值得点 / 藏 / 赞评论」全部由注入的 `like_principle` / `collection_principle` / tone 派生。广告 / 带货 / 与正文无关等通用负面清单保留为模板硬规则（这是所有真人共同的排除项，不是口味）。
*备选*：按 `behavior_guidelines` 参数化生成模板段——多一层模板引擎复杂度，人设原则字段已经是自由文本，直接引用即可，砍掉。

**D2 好奇心豁免的实现位置：`content_evaluator` 构造器注入 `random`，评估轮内掷骰、命中才追加 prompt 行。**
沿用 `comment_like_appraiser` 的分层惯例：概率在代码层（可注入 random、可单测边界）、LLM 只在被豁免的那一轮看到「本屏也可以纯粹因为标题有趣点开兴趣之外的内容」一句。未命中轮次 prompt 与现状逐字一致。诚实 skip 红线不变（好奇打开的也是真实评估过的卡、`content.no_valuable` 语义不变）；品牌安全禁区（category-adaptive delta 的全局兜底）不受豁免。概率默认 0.12，常量导出便于调。
*备选 A*：把好奇写进常驻 prompt 让 LLM 自己「偶尔」——LLM 不可靠地模拟低频事件，且温度 0 下近乎恒定，弃。
*备选 B*：放开温度制造随机——与 `role-llm-config` 冲突（见 D3），弃。

**D3 不放开判定类角色温度，用「状态注入」制造决策波动。**
`role-llm-config` 已合并条文：「温度 MUST 仅对生成 / 改写类角色开放」「判定类角色不开放温度」（该约束存在的理由：判定角色需要稳定可解析的 JSON 输出）。遵守之。决策层的波动来源改为三个确定输入的组合：会话状态注入（每场不同）、深读体验注入（每篇不同）、好奇掷骰（代码层真随机）——同一笔记在不同会话 / 不同阅读体验下自然得到不同判定，无需温度。
*备选*：给 `role-llm-config` 出 delta 允许判定角色调温——为拟人化去动模型配置治理的既有约束，影响 console 渲染与温度校验链，收益不成比例，弃。

**D4 payload 穿透用可选字段，向后兼容。**
`comment.appraised` 加可选 `reason?: string`（`event-bus/types.ts`——非 RoleName 枚举，但同文件属 §7 热点，实装标记串行注意、集成时最后 rebase）。composer 收到有 reason 就注入「你刚才觉得这篇值得评，因为…」，没有就跳过。同理：互动类型（like / collect）已在 `interaction.completed`→评论支线链路上可得，作者名在 NoteData 里现成；当页评论仅在会话内已采集到时注入头部 3-5 条摘要（`comment_like_appraiser` 的候选或 `scroll_comments` 上报），采不到诚实不注——不为注入语境去改事件时序或加边缘采集。

**D5 composer 的 decline 出口是「诚实弃权」不是「静默不发」。**
输出格式扩为 `{"text":"..."}` 或 `{"decline":"nothing_genuine"}`；解析到 decline 走既有 `comment.skipped` 分支（reason=nothing_genuine），下游进主页评估不受影响（评论支线本就是直通）。与「红线反例——撰写失败伪造文本（禁止）」一致：写不出真话时的正确行为是弃权，不是硬凑客套话（客套话正是评论体裁的 AI 味主形态）。

**D6 去 AI 味评论路径：独立的评论场景词表 + 阈值 1，不动发帖侧。**
`comment_de_ai_flavor` 当前复用发帖侧词表（议论文连接词、阈值 2 按长文调）。为评论体裁增设独立信号集：客套模板句（「感谢分享」「学到了」单句成评、「说得太对了」类空洞附和、和稀泥句式）、命中 1 即触发人设化改写。发帖侧词表与阈值不动。等长约束改「保持原意、可以更短更随口」。撞车改写路径（`rewriteAwayFrom`）复用主路径 `personaVoiceLine()`（一行）。
*已知 spec 滞后*：`comment-interaction` 条文仍描述去 AI 味为「确定性、无 LLM」，代码早已有 LLM 改写路径（历史 change 未更新条文）。本 change 的 delta 顺带把该句修正为如实描述（检测确定性、改写走 LLM、失败回退原文不抛），不扩大行为面。

**D7 卫生清理的兼容性**：删 confidence 只删 prompt 输出示例中的字段与示例锚点值；解析器本就不读该字段，无需改（旧 prompt 缓存期模型仍可能输出它，解析器容忍）。「剩余预算」裸数字行直接删除（代码闸已在解析层兜底，模型无需知道台账）。

**D8 门槛常量与 spec 交织的处理**：`comment-interaction` 的门槛条文已被 `category-adaptive-images-and-judgment` 未归档 delta 改写为「按品类 / 账号可配 + 合理默认、MUST NOT 全体写死同组绝对值」。本 change 不实现可配机制（那是该 change 的地盘），只把**代码默认地板**从 1000 / 300 调到 300 / 100（10000 豁免不动），delta 写成「默认地板值」的修改、明确叠加在其表述之上。**归档顺序 MUST 在 category-adaptive-images-and-judgment 之后**；若其先行归档有出入，归档期按 memory `concurrent-session-shares-subrepo-worktree` 的重归档流程处理。

## Risks / Trade-offs

- [人设派生判据后，LLM 判定分布漂移不可控（互动率骤升 / 骤降）] → 克制先验仍在模板硬规则里（「多数 pass」「收藏更稀有」）；硬数值闸与预算 / 配额 / 冷却全部原样；上线后用 `interaction-appraisal`「互动决策可观测」的既有日志对比动作分布，异常可只回滚 prompt 文本（无 schema / 协议变更，回滚即 revert + redeploy）。
- [门槛降到 300 / 100 后评论候选量放大，人审与配额压力上升] → 每日上限 min(运营配置, 风控配额)、会话预算、冷却、飞书人审四道闸全部原样；量只影响进入 LLM 评估的候选数，实际发出量仍被闸住。真机观察一周再决定是否回调常量。
- [向 prompt 注入更多上下文（keyPoints / 会话状态 / 现场评论）拉长 prompt、增加 token 成本与跑偏面] → 每类注入都限幅（keyPoints 取前 2-3 条、会话状态一两句、现场评论头部 3-5 条截断）；缺数据诚实不注、不编造占位。
- [event-bus/types.ts 是热点文件，与并行 change 撞] → 只加可选字段不动枚举；实装时最后 rebase、显式列文件提交（memory：worktree-symlink-gitadd-trap）。
- [好奇豁免被误读为「放宽诚实 skip 红线」] → proposal / spec delta 里已写明：未命中轮 prompt 逐字不变；命中轮打开的也是真实评估过的卡；品牌安全禁区不豁免。
- [comment 链文件与 comment-search-command 已合并改动交叠] → 该 change 云端代码已入 master（剩余任务在 edge / 真机 / console），实装前 fetch + rebase 最新 master 即可，无语义冲突面。

## Migration Plan

无数据迁移、无协议变更、无 schema 变更。部署 = cloud 常规安全序列（备份 → rsync → restart → healthcheck）。回滚 = revert 提交重部署。上线后观察项（登记真机 backlog）：动作分布对比（like / collect / pass 比例、评论候选量）、多账号判定差异抽查（同一笔记不同人设是否产生不同判定）、评论文本观感（去 AI 味触发率从近 0 恢复到有效区间）。

## Open Questions

- 评论场景 AI 味词表的初版条目（客套 / 附和 / 和稀泥各几条）在实装时人工校准，参照既有词表的校准纪律（「不得不说」因真人常用被移出的先例）。
- 现场评论注入的取数源（`comment_like_appraiser` 候选缓存 vs `scroll_comments` 上报缓存）以实装时核实的事件时序为准，两者都取不到就不注入。
