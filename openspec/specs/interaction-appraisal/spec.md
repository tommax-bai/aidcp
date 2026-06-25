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

互动评估 prompt SHALL 把**点赞（like）框定为选择性互动**——仅在内容**真有共鸣 / 学到具体东西 / 观点令你眼前一亮**时才点赞；普通的、只是泛泛认同的、刷过即忘的笔记 MUST NOT 默认点赞。把**收藏（collect）框定为更稀有的选择性互动**（需要反复查看 / 落地复用的硬核可复用知识才收藏）。该框定 MUST 与 soul 注入的 `like_principle` / `collection_principle` 一致（`like_principle` 表达选择性点赞而非「轻量高频」）；MUST NOT 让 collect 的触发条件比 like 更易命中。prompt SHALL 提示「值得收藏的内容几乎也值得点赞」，收藏时倾向 `both`。

#### Scenario: prompt 把 like 框定为选择性、collect 为更稀有

- **WHEN** 构造互动评估 prompt 的决策逻辑
- **THEN** like 的标准为选择性（真有共鸣 / 学到具体东西 / 观点眼前一亮才点；普通/泛泛认同不点），collect 的标准为更稀有/选择性（反复查看才收藏），且 collect 的条件不比 like 更易命中

#### Scenario: 注入的 soul 标准与框定一致

- **WHEN** prompt 注入 `like_principle` / `collection_principle`
- **THEN** `like_principle` 表达**选择性**点赞（非「轻量高频」「多数都该点」）、`collection_principle` 表达更稀有的选择性收藏，两者不互相矛盾

### Requirement: 互动筛选全程从严

系统 SHALL 在互动漏斗的各阶段都采取**更挑剔**的筛选口径，使账号只在真正相关且有价值的内容/作者上互动：
- **上游内容粗筛门**（决定一篇笔记是否继续看）MUST 偏挑剔——仅当话题与人格兴趣**明显相关且笔记真有信息 / 观点 / 经验**时才通过；蹭热点 / 通篇泛泛 / 仅擦边 / 纯情绪的笔记 MUST 倾向不通过；MUST NOT 维持「默认继续看、拿不准一律通过」的宽松口径。
- **进作者主页判定**的门槛 MUST 抬高——仅当作者明显展现专业深度、方向与兴趣高度吻合、且确有长期关注价值时才判定进入。
- **关注判定**的门槛 MUST 抬高至「主题强相关 + 至少一个真实质量信号（粉丝数 / 获赞与收藏）」；但 MUST 继续遵守 `follow-decision`：只用平台真实提供的信号、MUST NOT 摆出或依赖「作品数」、MUST NOT 以「作品数未知」为由 skip（收紧 MUST NOT 重新引入作品数依赖，相关健康创作者仍应被关注）。

#### Scenario: 粗筛门拒掉低相关 / 低信息笔记

- **WHEN** 一篇笔记仅与兴趣擦边、或通篇泛泛无实质信息 / 纯情绪
- **THEN** 内容粗筛门 MUST 倾向不通过（不进入下游互动阶段），而非「拿不准一律通过」

#### Scenario: 进主页 / 关注口径更挑剔

- **WHEN** 对一篇已互动笔记评估是否进主页、或在主页评估是否关注
- **THEN** 仅在作者专业深度 + 主题高度吻合（关注另需至少一个真实质量信号）时才判定进入 / 关注，普通作者倾向不进 / 不关注

#### Scenario: 收紧关注不重犯作品数旧 bug

- **WHEN** 作者粉丝数与获赞收藏健康（如 130 粉 / 6707 获赞）、内容与兴趣相关，而作品数不可得
- **THEN** 关注判定仍依据粉丝 + 获赞收藏 + 相关性判定关注，MUST NOT 因「作品数未知」或收紧口径而 skip 该相关创作者

