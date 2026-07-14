> 交织说明：本文件的「精品门槛…」条文**基于 `category-adaptive-images-and-judgment` 未归档 delta 的表述之上**只调默认地板值；本 change 归档 MUST 排在该 change 之后（见 proposal Impact）。

## MODIFIED Requirements

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。**通用默认地板** SHALL 为：`likeCount > 300` **且**（`collectCount > 100` **或** `likeCount > 10000` 超高热豁免），边界均为严格大于——把中腰部高收藏内容（教程 / 攻略 / 清单类）纳入候选，同时保留超高热爆帖对收藏绝对值的豁免。为控成本，该硬门槛 SHALL 尽量在**最便宜阶段（调 LLM 之前）**确定性判定，MUST NOT 退化为宽松纯 OR 让过多笔记落到昂贵 LLM 判定。任一不满足门槛 MUST 直接 `comment.skipped`、不进入撰写 / 去 AI 味 / 审批。硬门槛之上，现有 LLM 精品判定（高热度 + 高价值）与飞书人审继续叠加（门槛为必要非充分条件）。此外系统保留**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api` 下发）；**实际生效每日上限 = min(运营配置上限, 风控安全配额)**，"今日已评数" MUST 复用风控按账号按天计数。数量、门槛与阈值 MUST 在评估阶段就判定：超上限 / 不达门槛 / LLM 判不值得 MUST 直接走"不评论 → 进主页评估"分支，MUST NOT 进入撰写 / 去 AI 味 / 审批。

#### Scenario: 达到每日上限即停止评论

- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再评论，直接进"是否进主页评估"

#### Scenario: 运营配置不可越过风控安全线

- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达品类/账号硬门槛不评

- **WHEN** 笔记未达该品类 / 账号解析出的硬门槛（按详情页真实点赞 / 收藏量或其比例；通用默认地板为 赞 > 300 且（藏 > 100 或 赞 > 10000））
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过，不进入撰写

#### Scenario: 中腰部高收藏笔记按新默认地板可入候选

- **WHEN** 一篇笔记 `likeCount = 500`、`collectCount = 150`（旧默认地板 1000 赞下必被排除）
- **THEN** 该笔记通过通用默认地板进入 LLM 精品判定（是否真评论仍由 LLM + 人审决定）

#### Scenario: 高赞低藏爆帖不再被固定绝对值一律排除

- **WHEN** 一篇情感 / 颜值类高赞低藏笔记（如高点赞、收藏绝对值不高）进入评估
- **THEN** 硬门槛按其品类 / 账号口径判定（比例 / 品类默认 / 超高热豁免），MUST NOT 仅因「收藏绝对值未过固定线」就必然判未达门槛

#### Scenario: 门槛边界严格判定

- **WHEN** 笔记指标恰好等于解析出的阈值边界（如 `likeCount === 300` 或 `collectCount === 100`）
- **THEN** MUST 视为未达门槛、不评（「超过」语义为严格大于，等于不算达标）

#### Scenario: 达门槛仍需过 LLM 与人审

- **WHEN** 笔记通过品类 / 账号硬门槛
- **THEN** 该笔记仅**通过硬门槛**进入后续判定，是否真评论仍由 LLM 精品判定 + 飞书人审决定（门槛是必要非充分条件）

### Requirement: 评估→撰写→去AI味→审批四段单职责角色

系统 SHALL 以四个独立角色实现评论支线，**评估与撰写 MUST NOT 合并**：`CommentAppraiser`（只判定要不要评、产判定不产文本）→
`CommentComposer`（产评论文本）→ `CommentDeAiFlavor`（去 AI 味 + 合规声明判定：**检测步**确定性无 LLM；**改写步**在命中 AI 味信号或与参考语料撞车时按**该账号人设口吻**做至多一次 LLM 改写，改写失败 / 超时 MUST 回退原文、不抛异常）→
`CommentApprovalGate`（循环内飞书人审）。任一段失败 / 不通过 MUST emit `comment.skipped` 并带如实原因，MUST NOT 伪造文本或伪造通过。
`CommentComposer` 作为浏览闭环首个自由文本角色，MUST 自己保证：空 / 超长文本如实跳过、做跨笔记近似去重、撰写时避开裸 `@`（编辑器带 `data-tribute` 提及）；并 SHALL 提供**语义弃权出口**——对着笔记确实写不出有真实内容的话时，MUST 返回弃权（`nothing_genuine`）走 `comment.skipped` 分支，MUST NOT 硬凑客套话（客套敷衍正是评论体裁的 AI 味主形态）。

#### Scenario: 评估为是才进入撰写

- **WHEN** `CommentAppraiser` 判定该笔记值得评论且配额/门槛通过
- **THEN** emit `comment.appraised` 触发 `CommentComposer` 产文本 → `CommentDeAiFlavor` 去 AI 味 / 合规 → `CommentApprovalGate`；评估为否则 emit `comment.skipped`，不进入撰写（不付 LLM 撰写成本）

#### Scenario: 去AI味检测步确定性、改写步失败回退

- **WHEN** `CommentComposer` 产出草稿文本
- **THEN** `CommentDeAiFlavor` 的 AI 味检测 MUST 为确定性规则（无 LLM、可独立单测）；命中信号触发的人设口吻改写走 LLM，改写失败 / 超时 MUST 回退检测前原文并继续流程，MUST NOT 抛异常中断评论支线

#### Scenario: 撰写诚实弃权不硬凑

- **WHEN** `CommentComposer` 面对已判值得评的笔记仍写不出有真实内容的评论（LLM 返回弃权）
- **THEN** MUST emit `comment.skipped{reason:'nothing_genuine'}`，不进入去 AI 味与审批；评论支线照常收敛（下游进主页评估不受影响）

#### Scenario: 红线反例——撰写失败伪造文本（禁止）

- **WHEN** `CommentComposer` LLM 失败 / 产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST emit `comment.skipped{reason}`，绝不发出无法落地的伪造评论

## ADDED Requirements

### Requirement: 评论链人设注入对齐互动评估样板

评论支线的判定与产文角色（`CommentAppraiser` / `CommentComposer` / `CommentDeAiFlavor` 的两条改写路径）SHALL 注入账号人设的**性格字段**（`background` / `tone`，判定角色另注入 `like_principle` 类互动原则；对齐互动评估角色的注入水平），使不同人设账号在「是否开口」「怎么说话」上产生可区分差异；判定角色 SHALL 注入 `behavior_guidelines.style`（浏览风格）作为行为倾向背景。撞车改写路径（与参考语料雷同触发的重写）MUST 与主改写路径同源使用人设口吻行，MUST NOT 以无人设的通用口吻改写。无人设账号仍按 `mandatory-account-persona` 既有闸诚实拒绝，本要求不改变该行为。

#### Scenario: 判定与撰写 prompt 含性格字段

- **WHEN** 构造 `CommentAppraiser` / `CommentComposer` 的 prompt
- **THEN** prompt 含该账号 `background` / `tone`（判定另含互动原则与浏览风格），MUST NOT 仅注入「名字 + 职业 + 兴趣清单」

#### Scenario: 撞车改写带人设口吻

- **WHEN** 评论草稿与参考语料近似撞车、触发重写
- **THEN** 重写 prompt 含该账号人设口吻行（与主改写路径同源），产出保留该账号个人腔，MUST NOT 收敛为通用中庸腔

### Requirement: 撰写语境穿透与言语行为多样化

系统 SHALL 让评论撰写基于「刚发生的真实体验」而非孤立正文：`CommentAppraiser` 判定「值得评」的理由 SHALL 经 `comment.appraised` payload（可选字段）穿透到撰写 prompt；撰写 prompt SHALL 注入本次互动类型（like / collect）与作者名；会话内已采集到该笔记当页评论时 SHALL 注入头部摘要（限幅 3-5 条）以贴合现场话题、避免重复他人已说，未采集到时 MUST 诚实不注入、MUST NOT 为此改动事件时序或新增边缘采集。撰写的**切入角** SHALL 为可选面板（共鸣 / 真问题 / 自己的相关经历 / 纯情绪短评等）由人设与内容选择，MUST NOT 钉死单一「共鸣或提问」两模式；长度约束 SHALL 表述为「一般一两句，可以更短、更随口」（保留平台上限硬闸），MUST NOT 诱导恒定长度。

#### Scenario: 判定理由穿透进撰写

- **WHEN** `CommentAppraiser` 产出「值得评」判定且 payload 携带 reason
- **THEN** 撰写 prompt 含「你刚才觉得这篇值得评，因为…」语境；payload 无 reason 时省略该片段（可选字段向后兼容）

#### Scenario: 当页评论缺失不编造

- **WHEN** 会话内未采集到该笔记的当页评论
- **THEN** 撰写 prompt 省略现场评论片段，MUST NOT 编造「大家在聊…」占位语境

#### Scenario: 切入角与长度不钉死

- **WHEN** 同一账号在多篇不同笔记下撰写评论
- **THEN** 切入角随人设与内容在面板内变化、长度自然波动，MUST NOT 每条都呈「一句共鸣 / 一个提问 + 近似等长」的模板签名

### Requirement: 去 AI 味信号集覆盖评论体裁

`CommentDeAiFlavor` 的 AI 味检测 SHALL 使用**评论体裁专用信号集**（客套模板句如「感谢分享」「学到了」单句成评、空洞附和、和稀泥句式等，人工校准维护），命中 **1 条**即触发人设口吻改写；MUST NOT 仅复用发帖侧长文议论文连接词词表与其阈值（该词表对评论体裁近零召回、致改写路径长期空转）。改写指令 SHALL 允许「可以更短、更随口」，MUST NOT 强制等长。发帖侧既有词表与阈值不受本要求影响。

#### Scenario: 客套模板评论被检出并改写

- **WHEN** 评论草稿为「感谢分享，学到了！」类客套模板句（不含议论文连接词）
- **THEN** 评论体裁信号集命中、触发按账号人设口吻的改写；改写后保持贴题、允许比原文更短

#### Scenario: 发帖侧不受影响

- **WHEN** 发布正文走发帖侧去 AI 味
- **THEN** 发帖侧词表、阈值与行为与本 change 之前一致
