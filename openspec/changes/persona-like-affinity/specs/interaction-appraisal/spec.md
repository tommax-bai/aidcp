## MODIFIED Requirements

### Requirement: 点赞是按人设倾向分档的选择性互动、收藏是更稀有的选择性互动

互动评估 prompt SHALL 把**点赞（like）框定为仍可跳过的选择性互动**、**收藏（collect）框定为更稀有的选择性互动**，并按账号 `behavior_guidelines.like_affinity` 注入单调分档的软偏好：`normal` 保持当前克制先验（多数普通笔记落 pass）；`like_more` 对兴趣明确相关且带来真实正向感受的内容适度降低点赞阈值；`like_most` 对兴趣相关、安全、非低质内容明显偏向点赞但仍允许 pass。档位越高 SHALL 越倾向输出含 `like` 的普通互动决定，但任何档位 MUST NOT 直接产生动作、跳过 LLM 普通判定、绕过预算/冷却/RiskController，或进入 `mandatory_interactions` 确定性旁路。

模板固定段 MUST 只承载**动作空间语义**（like / collect / both / pass 各自含义、稀有度层级以及按档位变化的克制程度），MUST NOT 对全部账号硬编码具体口味判据（如“学到具体东西”“可落地复用的硬核知识”这类单一人设的知识型标准）——具体判据 SHALL 由该账号人设注入的 `like_principle` / `collection_principle` 与 interests 派生，使不同人设产生可区分的互动口味。代码兜底在缺 `like_affinity` 时 MUST 等价 `normal`；缺 `behavior_guidelines` 时的原则文本 MUST 与正常档选择性框定一致。

#### Scenario: 正常档保持现有克制

- **WHEN** 账号 `like_affinity=normal` 或字段缺省
- **THEN** prompt 保持“点赞选择性、多数普通内容 pass”的现有口径，既有账号行为不因升级突变

#### Scenario: 高档位单调提高普通点赞倾向

- **WHEN** 同一账号兴趣与同一合格内容分别以 `normal`、`like_more`、`like_most` 构造互动 prompt
- **THEN** prompt 的点赞软偏好逐档增强，同时每档都保留 pass 与低质/不相关内容不点赞的出口

#### Scenario: 模板固定段只含动作与档位语义、不含统一口味

- **WHEN** 构造互动评估 prompt 的决策逻辑段
- **THEN** 该段只描述动作空间、稀有度与档位倾向，具体“什么内容值得点/藏”引用人设兴趣与原则，MUST NOT 覆写成全账号同一口味

#### Scenario: 人设原则真实承重

- **WHEN** 两个同档位账号的 `like_principle` / interests 表达不同口味
- **THEN** 两账号的互动评估 prompt 判据随人设不同而不同，MUST NOT 因档位相同而坍缩成同一套口味

#### Scenario: 点赞倾向不进入强制点赞旁路

- **WHEN** `like_affinity=like_most` 但当前内容被普通判定为 pass、软预算为 0、处于冷却或 RiskController 拒绝
- **THEN** 系统不产生或不执行点赞，MUST NOT 把“更喜欢”当 mandatory like 绕过任一闸

#### Scenario: 兜底原则与正常档一致

- **WHEN** 账号人设缺 `behavior_guidelines` 或缺 `like_affinity`
- **THEN** 兜底文本与行为按 `normal` 的选择性点赞处理，不出现隐式高频或强制点赞
