## ADDED Requirements

### Requirement: 已关注作者不进主页子链

当笔记详情页显示作者**已被关注**时，系统 SHALL 跳过作者主页子链——MUST NOT 下发 `profile.open`、MUST NOT 浏览主页、MUST NOT 发起关注。`note.detail`（edge → cloud）SHALL 携带可选 `authorFollowed: boolean`，由边缘在 `note.open` 时读取笔记 modal 作者区关注按钮状态（文案 `已关注/互关` 或等价状态标记，复用关注执行的检测口径）得出；该状态是平台**当下真实**信号，边缘只读取上报、MUST NOT 臆造。`AuthorEvaluator` 在互动后触发评估时，SHALL 在调用 LLM 之前判定：若 `authorFollowed` 为真，直接产出 `profile.skipped`（reason 表明已关注），不进入主页评估。

当 `note.detail` 未提供 `authorFollowed`（缺省/读取失败）时，系统 SHALL 回退到原有主页子链流程（不因缺该信号而中断）；此时末端 `interaction.follow` 的 `already_followed` 良性 no-op 作为兜底。该要求 MUST NOT 改变「仅在互动后才评估进主页」的既有触发语义（本闸位于该触发之后）。

#### Scenario: 详情页已关注 → 跳过主页与关注

- **WHEN** 笔记详情页作者区关注按钮显示「已关注/互关」，边缘据此在 `note.detail` 置 `authorFollowed=true`，且该笔记被互动（`interaction.completed`）
- **THEN** `AuthorEvaluator` 不调用 LLM、直接 `profile.skipped`（reason 表明已关注），系统不下发 `profile.open`、不浏览主页、不发起关注

#### Scenario: 详情页未关注 → 正常评估是否进主页

- **WHEN** 关注按钮显示「关注」（未关注），`authorFollowed` 为 false/缺省
- **THEN** `AuthorEvaluator` 照常评估，符合条件则进入主页子链

#### Scenario: 缺 authorFollowed 信号时回退原流程

- **WHEN** `note.detail` 未携带 `authorFollowed`（旧边缘 / modal 无按钮 / 读取失败）
- **THEN** 系统按原有主页子链流程运行（行为不劣化），并由末端 `interaction.follow` 的 `already_followed` no-op 兜底，不重复关注
