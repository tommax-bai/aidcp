# humanize-interaction-prompts — 互动决策链 prompt 拟人化精修

## Why

对小红书浏览闭环 8 个互动决策角色（选卡 / 点赞收藏 / 翻评论区 / 是否评论 / 评论点赞 / 评论撰写 / 去 AI 味 / 进主页）做了多 agent 对抗核验的拟人化审计，结论：**单个动作像人，但长期行为序列与多账号群体形态不像**。具体病灶（均有 文件:行 实证）：

- **人设「半注入」**：多数判定角色只注入「名字 + 职业 + 兴趣」，语气 / 背景 / 点赞收藏原则等性格字段缺席；`behavior_guidelines.style`（浏览风格）全仓零消费方，是纯死配置；去 AI 味的撞车改写路径完全零人设（`comment-de-ai-flavor.ts:96`）。两个兴趣相同、性格迥异的账号会做出逐条一致的判定——多账号同质化正是平台侧最易聚类的形态。
- **固定评判模板盖过人设口味**：`interaction-appraiser-role.ts:158-162` 的「决策逻辑」段对所有账号一字不差，与默认技术人设的点赞原则近乎逐字相同，且与本文件兜底 `likePrinciple`（「轻量高频」）直接矛盾；`comment-like-appraiser.ts:204-207` 三轴口径全 fleet 共用。
- **决策层零随机、零当下状态**：`sessionContext` 在多个角色构造器里收了不存不读（死参）；深读产出的阅读体验（`keyPoints` / `imagesBrowsed`）在点赞判定处全部丢弃；选卡「不匹配必须 skip」无任何好奇 / 猎奇出口——与人设文件自己「兴趣不用于硬匹配」的声明相悖（`soul.yaml:14` 注释）。
- **评论链语境盲判 + 言语行为单一**：撰写端看不到评论区已有内容、不知道刚才是赞还是藏、上游「为何值得评」的理由算完即弃；每条评论钉死「一句共鸣或一个真问题 + 恒定 50 字内」，长期积累可检测的模板签名。
- **去 AI 味防线失配**：触发闸是「书面连接词计数 ≥2」，词表全是议论文连接词，评论体裁的典型 AI 腔（客套 / 敷衍 / 和稀泥）零命中——该角色核心能力大多数时候空转。

## What Changes

> **用户定案边界（MUST 遵守）**：
> ① **现有硬数值闸机制与数值一律不动**（收藏藏赞比 1/3 地板、评论点赞比率闸与早场归零、滚动深度公式全部保持原样）。唯一例外是评论精品门槛**常量默认值**：`COMMENT_MIN_LIKES` 1000→300、`COMMENT_MIN_COLLECTS` 300→100（等比口径，用户批准区间 100-150），`COMMENT_HIGH_LIKES` 10000 豁免线不动（`comment-appraiser.ts:23-27`）——只挪数值，合取结构与「必要非充分」语义不变。
> ② **`author_evaluator`（进主页判定）本轮完全不动**——不放松、不加频率闸、数据缺失护栏也推迟。已核实进主页当前无任何专属频率闸（配额表无 profile 项），放松口味必须与频率闸捆绑落地，整体留待下一个 change。
> ③ **选卡好奇心出口是「新增」豁免层，不是改现有闸**：代码层小概率掷骰（10-15%，random 可注入）命中时才在 prompt 追加「本屏也可以纯粹因为标题有趣点开兴趣之外的内容」一句；未命中时行为与现状完全一致。品牌安全禁区兜底不受豁免。

具体改动（全部落 `aidcp-cloud`，按优先级）：

1. **人设注入对齐样板**（样板 = `interaction-appraiser-role.ts:144-149`）：`comment_appraiser` / `comment_like_appraiser` / `comment_reviewer` 补注 `background` / `tone` / `like_principle`；`comment_composer` 补 `background`；`comment_de_ai_flavor` 撞车改写路径（`rewriteAwayFrom`）复用主路径 `personaVoiceLine`（一行改动）；`behavior_guidelines.style` 接上消费方（判定角色注入浏览风格一行）。
2. **固定评判模板去口味化**：`interaction_appraiser`「决策逻辑」段只保留动作空间语义（like / collect / both / pass 各是什么、收藏更稀有、多数 pass），具体口味判据交人设 `like_principle` / `collection_principle` 派生；`comment_like_appraiser` 三轴口径同理改人设派生（通用负面清单如广告 / 带货不点保留为硬规则）。
3. **评论精品门槛默认值调整**（见定案①）。联动语义：改后 300-10000 赞段的实际卡点是收藏线，故收藏线同步 300→100。
4. **决策上下文注入**：深读 `ReadingDonePayload` 的 `keyPoints` / `imagesBrowsed` 注入点赞收藏判定 prompt（「你刚读完，印象最深的是…」，数据现成）；用起 `interaction_appraiser` / `comment_reviewer` 的 `sessionContext` 死参，注入一两句会话状态（本次已刷 N 篇、刚点过什么）。**不放开判定角色温度**——`role-llm-config` 已合并条文明确「判定类角色 MUST NOT 开放温度”，决策波动改由会话状态注入 + 人设派生判据实现（见 design）。
5. **评论链语境穿透与言语行为多样化**：`comment_appraiser` 的 reason 穿透进 `comment.appraised` payload 并注入撰写 prompt；撰写注入互动类型（like / collect）与作者名；已采集到当页评论时注入头部摘要（无则诚实不注，不强推翻事件时序）；切入角从钉死「共鸣 / 提问」改为可选面板（共鸣 / 真问题 / 自己经历 / 纯情绪短评）由人设选择；长度约束改「一般一两句，可以更短、更随口」；补语义 decline 出口（写不出真话返回 `nothing_genuine`，宁可不发——诚实弃权，不伪造文本）。
6. **去 AI 味召回修复（评论路径）**：改写触发阈值降为 1 + 补评论场景 AI 味信号词表（「感谢分享」「学到了」滥用、和稀泥句式等，人工校准）；等长约束改「可以更短」（删减是最自然的去书面腔动作）。
7. **卫生清理（一次做完）**：删全家族死 `confidence` 字段（六角色，解析端本就不读，解析器容忍旧字段）；「剩余预算 like=N」裸数字行删除或译成状态语言；兴趣主 / 次分层表述（「主要兴趣…也关注…」）；`comment_reviewer` / `content_evaluator` 公文语域改第一人称口语。

## Capabilities

### New Capabilities

（无——全部为既有能力的需求修改。）

### Modified Capabilities

- `interaction-appraisal`：① 点赞 / 收藏 prompt 判据从固定知识型措辞改为**人设原则派生**（保留「点赞选择性、收藏更稀有、多数 pass」的层级语义不变）；② 「互动筛选全程从严」的上游粗筛门条款增加**受控好奇心豁免**（代码层有界概率，非 LLM 自由放宽；品牌安全禁区与诚实 skip 红线不变）；③ 新增「决策上下文注入」要求（深读体验字段 + 会话状态进 prompt）。**注意**：本 capability 有 `category-adaptive-images-and-judgment` 的未归档 delta（去题材硬编码 / 收藏地板可配），本 change 的 delta 与其正交（它管判据来源与地板可配，我们管判据人设派生的扩面、好奇豁免与上下文注入），归档时按序合并。
- `comment-interaction`：① 精品门槛**默认地板值**调整（赞线 1000→300、收藏线 300→100、10000 豁免不动）——**基于 `category-adaptive-images-and-judgment` 未归档 delta 的「按品类 / 账号可配 + 合理默认」表述之上只调默认值**，归档 MUST 排在该 change 之后；② 撰写角色语境穿透（appraiser reason / 互动类型 / 作者 / 已采集的当页评论）与言语行为多样化 + `nothing_genuine` 诚实弃权出口；③ 评论链人设注入补齐 + 去 AI 味评论路径召回修复。
- `comment-like-interaction`：择选判据从钉死的「interest / knowledge-depth / resonance」三轴改为人设派生（价值判断 + 单条上限 + 多数弃权语义全部不变）；prompt 补注 `like_principle` / `tone`。

## Impact

- **仓库**：仅 `aidcp-cloud`（edge 不动、console 不动、协议四处同步不涉及——无新消息类型）。
- **代码**：`src/agents/` 下 7 个角色文件（`author-evaluator.ts` 整文件不动）；`src/event-bus/types.ts`（`comment.appraised` payload 加可选 reason 字段——**非 RoleName 枚举**，但同文件是 §7 热点，标串行注意）；对应单测按测试克制原则少数关键用例（人设字段注入有无、payload 穿透、掷骰边界可注入 random、门槛常量断言更新）。
- **不碰**：风控 `RISK_ACTIONS` / `quotas.ts` / `risk-state-machine.ts`；`role-catalog.ts`（不改温度可调性）；发布侧 `publish-agent/`（同款无人设问题属 `publish-trigger-and-apply` 地盘）。
- **串行 / 撞车**：① 归档顺序 MUST 在 `category-adaptive-images-and-judgment` 之后（`comment-interaction` / `interaction-appraisal` 两处 delta 交织）；② comment 链文件被 `comment-search-command`（29/35，剩余任务在 edge / 真机 / console）动过，实装前先 fetch rebase 最新 master；③ LLM 实际输出观感属真机项，登记 `docs/real-machine-acceptance-backlog.md`，不写死单测。
