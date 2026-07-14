# interaction-appraisal Specification

## Purpose
TBD - created by archiving change interaction-appraiser-like-rebalance. Update Purpose after archive.
## Requirements
### Requirement: 收藏即点赞（配额允许时收藏同时点赞）

当评估结论为 `collect` 且**点赞配额可用**（`budget.likes > 0`）时，系统 SHALL 在下发 collect 的
同时**也下发 like**（收藏即点赞）。该行为 MUST 受点赞配额约束——`budget.likes === 0` 时 MUST NOT
补发 like（仅 collect）。`like` / `both` / `pass` 的既有映射行为不变。

#### Scenario: 收藏时配额允许则同时点赞

- **WHEN** LLM 返回 `action: collect` 且 `budget.likes > 0`
- **THEN** 映射出的 actions 同时包含 `like` 与 `collect`

#### Scenario: 点赞配额耗尽时收藏不补点赞

- **WHEN** LLM 返回 `action: collect` 且 `budget.likes === 0`
- **THEN** 映射出的 actions 仅含 `collect`，MUST NOT 含 `like`（不绕过配额）

#### Scenario: pass 不产生任何互动

- **WHEN** LLM 返回 `action: pass`
- **THEN** 映射出的 actions 为空（既不点赞也不收藏）

### Requirement: 互动决策可观测

互动评估每次产出 SHALL 在服务日志中可观测——记录该笔记被选择的动作（like/collect/both/pass）
与简短原因，以便事后核实「是 LLM 选择问题还是链路问题」并对比改动前后的 like/collect 比例。

#### Scenario: 决策动作进入日志

- **WHEN** 互动评估对某笔记产出决策
- **THEN** 服务日志包含该次决策的原始动作与原因，可据以统计动作分布

### Requirement: 点赞是选择性互动、收藏是更稀有的选择性互动

互动评估 prompt SHALL 把**点赞（like）框定为选择性互动**、**收藏（collect）框定为更稀有的选择性互动**，并保留克制先验（多数普通笔记落 pass、收藏时倾向 `both`、MUST NOT 让 collect 的触发条件比 like 更易命中）。但模板固定段 MUST 只承载**动作空间语义**（like / collect / both / pass 各自含义、稀有度层级、多数 pass），MUST NOT 对全部账号硬编码具体口味判据（如「学到具体东西」「可落地复用的硬核知识」这类单一人设的知识型标准）——具体判据 SHALL 由该账号人设注入的 `like_principle` / `collection_principle` 派生，使不同人设产生可区分的互动口味。代码兜底原则文本（soul 缺 `behavior_guidelines` 时的 fallback）MUST 与选择性框定一致，MUST NOT 出现「轻量高频」等与模板框定矛盾的表述。

#### Scenario: 模板固定段只含动作语义、不含口味判据

- **WHEN** 构造互动评估 prompt 的决策逻辑段
- **THEN** 该段仅描述动作空间与稀有度层级（点赞选择性、收藏更稀有、多数 pass、收藏倾向 both），具体「什么内容值得点 / 藏」的判据引用上文注入的人设原则，MUST NOT 内联对全账号一致的口味标准

#### Scenario: 人设原则真实承重（不同人设不同口味）

- **WHEN** 两个账号的 `like_principle` / `collection_principle` 表达不同口味（如知识型「学到东西才点」 vs 审美型「好看戳心就点」）
- **THEN** 两账号的互动评估 prompt 判据段随人设不同而不同，MUST NOT 被模板固定段覆写回同一套标准

#### Scenario: 兜底原则与选择性框定一致

- **WHEN** 账号人设缺 `behavior_guidelines` 字段、代码使用兜底原则文本
- **THEN** 兜底文本表达**选择性**点赞与**更稀有**收藏，与模板框定不矛盾（不出现「轻量高频」「多数都该点」类表述）

### Requirement: 互动筛选全程从严

系统 SHALL 在互动漏斗的各阶段都采取**更挑剔**的筛选口径，使账号只在真正相关且有价值的内容/作者上互动：
- **上游内容粗筛门**（决定一篇笔记是否继续看）MUST 偏挑剔——仅当话题与人格兴趣**明显相关且笔记真有信息 / 观点 / 经验**时才通过；蹭热点 / 通篇泛泛 / 仅擦边 / 纯情绪的笔记 MUST 倾向不通过；MUST NOT 维持「默认继续看、拿不准一律通过」的宽松口径。**唯一例外是受控好奇心豁免**：系统 MAY 以**代码层有界概率**（掷骰在代码层、随机源可注入测试；MUST NOT 交由 LLM 自行「偶尔」）在个别评估轮次于 prompt 追加「本屏也可以纯粹因为标题有趣点开兴趣之外的内容」的许可；未命中豁免的轮次 prompt 与从严口径逐字一致。好奇豁免轮打开的仍是本屏真实评估过的卡片（诚实 skip / `content.no_valuable` 语义不变），且**全局品牌安全禁区 MUST NOT 被豁免**。
- **进作者主页判定**的门槛 MUST 抬高——仅当作者明显展现专业深度、方向与兴趣高度吻合、且确有长期关注价值时才判定进入。
- **关注判定**的门槛 MUST 抬高至「主题强相关 + 至少一个真实质量信号（粉丝数 / 获赞与收藏）」；但 MUST 继续遵守 `follow-decision`：只用平台真实提供的信号、MUST NOT 摆出或依赖「作品数」、MUST NOT 以「作品数未知」为由 skip（收紧 MUST NOT 重新引入作品数依赖，相关健康创作者仍应被关注）。

#### Scenario: 粗筛门拒掉低相关 / 低信息笔记（未命中好奇豁免）

- **WHEN** 好奇豁免未命中的评估轮次里，一篇笔记仅与兴趣擦边、或通篇泛泛无实质信息 / 纯情绪
- **THEN** 内容粗筛门 MUST 倾向不通过（不进入下游互动阶段），而非「拿不准一律通过」

#### Scenario: 好奇豁免命中时允许兴趣外的真实好奇

- **WHEN** 代码层掷骰命中好奇豁免（有界概率、随机源可注入）
- **THEN** 该轮 prompt 追加好奇许可一句，LLM MAY 因标题 / 内容确实有趣选择一张兴趣之外的卡片；若本屏确无有趣内容仍诚实 `content.no_valuable`，MUST NOT 为豁免而硬凑选择

#### Scenario: 好奇豁免不放宽品牌安全与诚实红线

- **WHEN** 好奇豁免命中、且本屏卡片命中全局品牌安全禁区题材
- **THEN** 禁区卡片 MUST NOT 被选择；豁免只作用于「兴趣匹配」维度，MUST NOT 弱化诚实 skip 与禁区兜底

#### Scenario: 进主页 / 关注口径更挑剔

- **WHEN** 对一篇已互动笔记评估是否进主页、或在主页评估是否关注
- **THEN** 仅在作者专业深度 + 主题高度吻合（关注另需至少一个真实质量信号）时才判定进入 / 关注，普通作者倾向不进 / 不关注

#### Scenario: 收紧关注不重犯作品数旧 bug

- **WHEN** 作者粉丝数与获赞收藏健康（如 130 粉 / 6707 获赞）、内容与兴趣相关，而作品数不可得
- **THEN** 关注判定仍依据粉丝 + 获赞收藏 + 相关性判定关注，MUST NOT 因「作品数未知」或收紧口径而 skip 该相关创作者

### Requirement: 相关性与收藏判定去题材硬编码、随账号人设兴趣

浏览内容相关性判定与收藏（collect）判定 SHALL 从账号**真实人设兴趣**派生，MUST NOT 在 prompt 里硬编码固定题材白 / 黑名单（如把「AI / 技术」当默认兴趣、把「娱乐 / 八卦 / 明星」钉死为无关），也 MUST NOT 用「代码 / 架构图」这类技术专属可复用性示例定义「值得收藏」。相关性判定 SHALL 保留「与账号兴趣无明显匹配即诚实 skip、MUST NOT 为无关内容编造相关理由」（对应 `content.no_valuable` 诚实回报，不静默假成功）。系统 SHALL 另保留一个**与人设无关的全局品牌安全禁区兜底**（无论人设都不碰的题材）。

#### Scenario: 娱乐 / 明星人设不再被判无关
- **WHEN** 一个兴趣含娱乐 / 明星的账号浏览到相关卡片
- **THEN** 相关性判定按其人设兴趣判为相关，MUST NOT 因硬编码「娱乐 / 明星 = 无关」而误 skip

#### Scenario: 无匹配仍诚实 skip 不编造
- **WHEN** 当前卡片均与账号兴趣无明显匹配
- **THEN** MUST 诚实 skip、MUST NOT 为凑互动编造相关理由

#### Scenario: 全局品牌安全禁区兜底
- **WHEN** 内容命中全局品牌安全禁区题材
- **THEN** 无论账号人设如何 MUST NOT 互动

### Requirement: 收藏率数值地板随人设/品类可配且保留存在性

收藏判定的**数值地板**（如收藏 / 点赞比例下限）SHALL 可按人设 / 品类配置（审美 / 灵感 / 心情板类等「高赞低藏」口味的账号 MAY 放宽或旁路），MUST NOT 用单一固定比例误挡这类账号。但该地板的**存在性**与「点赞数 = 0 时保守不收藏」的防线 MUST 保留，MUST NOT 使收藏无条件化；LLM 收藏判定 SHALL 继续叠加在数值地板之上。

#### Scenario: 审美类账号放宽收藏率地板
- **WHEN** 一个声明为审美 / 灵感类口味的账号遇到高赞低藏的好看内容
- **THEN** 其收藏率地板按人设放宽 / 旁路，使该内容可被收藏，MUST NOT 被通用固定地板一律挡掉

#### Scenario: 地板存在性与 0 赞防线不移除
- **WHEN** 某内容点赞数为 0，或审视收藏闸整体
- **THEN** 仍保守不收藏；数值地板作为「必要非充分」条件仍存在、LLM 判定叠加其上，收藏 MUST NOT 变为无条件

### Requirement: 互动决策注入阅读体验与会话状态

互动评估 prompt SHALL 注入该笔记深读产出的**阅读体验**（`reading.done` 携带的关键印象 `keyPoints`、看图数量 `imagesBrowsed`，以「你刚读完，印象最深的是…」的第一人称体验形式），并 SHALL 注入**轻量会话状态**（如本次会话已刷多少篇、刚点过什么），使同一内容在不同会话 / 不同阅读体验下产生自然的判定波动。翻评论区判定（`comment_reviewer`）SHALL 同样注入会话状态（服务 `detail-deep-read` 既有「深读取舍的拟人化多样性」要求）。注入 MUST 限幅（keyPoints 取前 2-3 条、会话状态一两句）；任一数据缺失时 MUST 诚实不注入该项，MUST NOT 编造占位内容。

#### Scenario: 深读体验进入互动评估

- **WHEN** 某笔记深读完成且 `reading.done` 携带非空 `keyPoints`
- **THEN** 互动评估 prompt 含该笔记的阅读印象（限幅后），判定基于「刚读完的体验」而非仅标题 + 正文 + 计数

#### Scenario: 数据缺失诚实不注入

- **WHEN** `keyPoints` 为空或会话状态不可得
- **THEN** prompt 省略对应片段，MUST NOT 以编造的「印象」「状态」占位

#### Scenario: 会话状态使判定具有序列依赖

- **WHEN** 同一账号在一场会话的第 2 篇与第 15 篇遇到相近质量的内容
- **THEN** prompt 中的会话状态（已刷篇数、近期互动）不同，允许 LLM 产生「刷久了兴致变化」类的自然差异；该差异 MUST 仅通过 prompt 状态注入实现，MUST NOT 依赖放开判定角色温度（遵守 `role-llm-config`「判定类角色不开放温度」）

### Requirement: 判定 prompt 去评分器姿态

互动链判定角色的 prompt 与输出格式 MUST NOT 要求无消费方的自评置信字段（如 `confidence` 小数）；MUST NOT 向人设视角暴露配额台账语言（如「剩余预算：like=N」裸数字——预算与配额约束由代码层在解析 / 下发阶段兜底）。判定段表述 SHALL 采用第一人称使用者口吻，避免「评估维度」「候选」等评审文书语域。解析器对旧格式输出中的多余字段 MUST 容忍（不因模型仍输出 `confidence` 而解析失败）。

#### Scenario: 输出格式不含死置信字段

- **WHEN** 构造互动评估 / 选卡等判定角色的输出格式示例
- **THEN** 示例仅含被消费的字段（如 action / reason），不含 `confidence`；模型若仍输出多余字段，解析 MUST 正常成功

#### Scenario: prompt 不暴露配额台账

- **WHEN** 构造互动评估 prompt
- **THEN** 不含「剩余预算 like=N，collect=M」类裸配额数字；预算耗尽的拦截行为（调 LLM 前 skip、解析层过滤越额动作）保持不变

