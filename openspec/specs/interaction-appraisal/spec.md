# interaction-appraisal Specification

## Purpose
TBD - created by archiving change interaction-appraiser-like-rebalance. Update Purpose after archive.
## Requirements
### Requirement: 点赞是低门槛高频互动、收藏是稀有选择性互动

互动评估 prompt SHALL 把**点赞（like）框定为低门槛、常见的轻互动**（内容有共鸣 / 学到东西 / 认同
观点即可点赞），把**收藏（collect）框定为稀有、选择性互动**（需要反复查看 / 落地复用才收藏）。
该框定 MUST 与 soul 注入的 `like_principle` / `collection_principle` 一致，且 MUST NOT 让 collect
的触发条件比 like 更易命中（避免系统性偏向 collect）。prompt SHALL 提示「值得收藏的内容几乎也
值得点赞」，倾向 `both`。

#### Scenario: prompt 把 like 框定为低门槛、collect 为稀有

- **WHEN** 构造互动评估 prompt 的决策逻辑
- **THEN** like 的标准为低门槛/常见（有共鸣/学到东西/认同即可），collect 的标准为稀有/选择性（反复查看才收藏），且 collect 的条件不比 like 更易命中

#### Scenario: 注入的 soul 标准与框定一致

- **WHEN** prompt 注入 `like_principle` / `collection_principle`
- **THEN** `like_principle` 表达低门槛高频点赞、`collection_principle` 表达选择性收藏，两者不互相矛盾

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

