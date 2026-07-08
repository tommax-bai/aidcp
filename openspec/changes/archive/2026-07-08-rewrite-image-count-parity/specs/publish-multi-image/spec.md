## MODIFIED Requirements

### Requirement: 配图张数由正文决定并夹在安全范围

图集选题角色 `ImageSetPlanner` SHALL watch `createdContent`、读正文（并在洗稿场景读源参照笔记有效图数）决定本帖配图张数与每张主题，写键 `imageSetPlan`。张数 SHALL 经规则**夹取**到安全范围：默认上限 9（`AIDCP_PUBLISH_MAX_IMAGES` 未设时的代码默认；env 可覆盖）、下界 ≥1（`wantImage === true` 时图文帖不能 0 张）、硬上限 MUST NOT 超过 9（平台上界）。

张数决策 SHALL 按是否洗稿分流：

- **洗稿帖**——触发含源参照笔记（`trigger.generateInput.referenceNote`）且其**有效图** ≥1 张（有效 = `ossUrl ?? sourceUrl` 可用，口径与生图参考图一致 `referenceImagesForGeneration`）：`imageCount` SHALL = `clamp(有效源图数, 1, 上限)`（对齐源稿体量）。选题角色 SHALL 要求 LLM 产出等量主题；主题不足 SHALL 由系统补齐至该数（图 0 恒封面/钩子位）。
- **非洗稿 / 无有效源图**：`imageCount` SHALL 取 LLM 读正文的判断值并 `clamp(1, 上限)`（维持内容驱动）。

选题角色 MUST NOT 调用图源、MUST NOT 产出万相 prompt（纯内容决策）；读源参照笔记 SHALL 经管线上下文快照，MUST NOT 因此把 `trigger` 加进 watchKeys（`createdContent` 就绪时 trigger 必在快照内）。源参照笔记的图 SHALL 仅用于「决定张数 + 作生图参考」，MUST NOT 被直接搬运当配图。

#### Scenario: 洗稿按源稿有效图数出等量图

- **WHEN** 洗稿触发含源参照笔记、其有效图为 N 张（N ≤ 上限），`ImageSetPlanner` 激活
- **THEN** `imageCount === N`、`themes` 长度 === N（不足由系统补齐、图 0 为钩子/封面位），产图数对齐源稿体量

#### Scenario: 源图数超上限被夹回

- **WHEN** 洗稿源有效图 > 上限（如 12 张、上限 9）
- **THEN** `imageCount` SHALL 夹回 `上限`（9），绝不超过平台上界

#### Scenario: 非洗稿内容定张数、规则夹安全范围

- **WHEN** 非洗稿（无源参照笔记 / 源无有效图），`createdContent` 就绪、`ImageSetPlanner` 激活
- **THEN** 产出 `imageSetPlan`（含 `wantImage` / `imageCount` / `themes` / `styleHint`），`imageCount` 取 LLM 判断值并 `clamp(1, AIDCP_PUBLISH_MAX_IMAGES≤9，默认 9)`；`themes` 长度与 `imageCount` 一致

#### Scenario: 越界张数被夹回

- **WHEN** LLM 给出 0 或 > 上限的张数 / 主题数
- **THEN** 规则 SHALL 夹回 `[1, 上限]`；`wantImage:true` 下永不产出 0 张

#### Scenario: 选题角色不碰图源与话术

- **WHEN** 为 `ImageSetPlanner` 写单测
- **THEN** 只需桩内容决策 LLM 与快照里的源参照笔记、无需桩图源；其依赖中不含 `ImageProvider`
