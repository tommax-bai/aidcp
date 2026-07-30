## MODIFIED Requirements

### Requirement: 评论链人设注入对齐互动评估样板

评论支线的判定与产文角色（`CommentAppraiser` / `CommentComposer` / `CommentDeAiFlavor` 的两条改写路径）SHALL 注入账号人设的**性格字段**（`background` / `tone`，判定角色另注入 `like_principle` 类互动原则；对齐互动评估角色的注入水平），使不同人设账号在「是否开口」「怎么说话」上产生可区分差异；判定角色 SHALL 注入 `behavior_guidelines.style`（浏览风格）作为行为倾向背景。撞车改写路径（与参考语料雷同触发的重写）MUST 与主改写路径同源使用人设口吻行，MUST NOT 以无人设的通用口吻改写。

本要求只约束**生成式**正文链路。模板正文链路 MUST NOT 读取人设、MUST NOT 经过人设口吻改写，也 MUST NOT 因账号无人设而被拒绝——Facebook 规则批次的模板评论即走这条链路。无人设账号在生成式链路上仍按 `mandatory-account-persona` 既有闸诚实拒绝，本要求不改变该行为。

#### Scenario: 判定与撰写 prompt 含性格字段

- **WHEN** 构造 `CommentAppraiser` / `CommentComposer` 的 prompt
- **THEN** prompt 含该账号 `background` / `tone`（判定另含互动原则与浏览风格），MUST NOT 仅注入「名字 + 职业 + 兴趣清单」

#### Scenario: 撞车改写带人设口吻

- **WHEN** 评论草稿与参考语料近似撞车、触发重写
- **THEN** 重写 prompt 含该账号人设口吻行（与主改写路径同源），产出保留该账号个人腔，MUST NOT 收敛为通用中庸腔

#### Scenario: 模板正文不进入人设注入链路

- **WHEN** 有效正文方案为模板，正文取自账号模板或区域通用模板
- **THEN** 该正文直接进入既有校验与提交链，不构造撰写 prompt、不做人设口吻改写，也不因账号无人设被拒绝
