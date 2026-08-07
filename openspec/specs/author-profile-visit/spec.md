# author-profile-visit Specification

## Purpose
TBD - created by archiving change implement-deepread-lineage. Update Purpose after archive.
## Requirements
### Requirement: 专用进作者主页指令

系统 SHALL 通过专用指令 `xiaohongshu.profile.open`（cloud → edge）让边缘进入作者主页，MUST NOT 复用 `xiaohongshu.note.open` 携带非协议字段（如 `type:'profile'`）。`RoleDispatcher` MUST 将 `profile.entered` 翻译为 `xiaohongshu.profile.open` 指令（payload 含 `authorId?`、`reason?`、`thinkMs?`），`command-bridge` MUST 提供 `profile_open → xiaohongshu.profile.open` 映射。边缘 `dispatchCommand` MUST 新增处理：导航进入该作者主页（点击作者头像或跳转主页）并等待主页渲染就绪。

#### Scenario: 评估值得进主页后真正进入
- **WHEN** `AuthorEvaluator` 判定 visit、`ProfileOpener` emit `profile.entered`
- **THEN** 系统下发 `xiaohongshu.profile.open` 指令，边缘导航到作者主页并等待渲染，而非打开信息流中的某条笔记

#### Scenario: 不再因缺字段开错笔记
- **WHEN** 需要进入作者主页
- **THEN** 系统下发的是 `xiaohongshu.profile.open` 而非 `xiaohongshu.note.open`，边缘不会因 `type` 字段被丢弃而按 `index=0` 打开错误笔记

### Requirement: 进主页评估触发维持互动后

系统 SHALL 维持"仅在对笔记完成点赞/收藏（`interaction.completed`）后才评估是否进入作者主页"的触发语义；`AuthorEvaluator` MUST 继续以 `interaction.completed` 为触发源，未产生互动的笔记不启动主页子链。

#### Scenario: 未互动的笔记不进主页
- **WHEN** 一篇笔记通过深读但未被点赞或收藏
- **THEN** 系统不触发 `AuthorEvaluator`，不进入作者主页子链

### Requirement: 作者资料采集与上报

边缘进入作者主页成功后 SHALL 抽取作者 `postsCount`（作品数）与 `followersCount`（粉丝数）并调用 `reportProfileDetail` 经 `profile.detail`（edge → cloud）上报。抽取 MUST 使用真实小红书作者主页选择器；抽取失败或超时时 MUST 仍回报并标记数据不可用，而非静默不报。

#### Scenario: 成功采集并上报作者资料
- **WHEN** 边缘进入作者主页且主页渲染含作品数/粉丝数
- **THEN** 边缘上报 `profile.detail`，payload 含真实 `authorId`/`postsCount`/`followersCount`

#### Scenario: 采集失败也回报
- **WHEN** 边缘进入主页但抽取作品数/粉丝数失败
- **THEN** 边缘仍上报 `profile.detail` 并标记数据不可用（不静默丢弃）

### Requirement: 云端接收作者资料并喂入关注决策

云端 `handler.ts` SHALL 处理 `profile.detail`（emit `profile.detail.arrived`，与 `note.detail.arrived` 同构），`RoleDispatcher` MUST 订阅该事件调用 `updateProfileData`。`ProfileBrowser` MUST 在作者资料就绪（`profile.detail.arrived`）后产出 `profile.browsed`（携带真实 counts），使 `FollowAgent` 基于真实粉丝/作品数判定，MUST NOT 再因数据链路断裂而恒得 0/0。

#### Scenario: 关注判定收到真实资料
- **WHEN** 边缘上报含非 0 作品数/粉丝数的 `profile.detail`
- **THEN** 云端不再返回 `unsupported_type`，`ProfileBrowser` 产出携带真实 counts 的 `profile.browsed`，`FollowAgent` 在真实数据上判定

#### Scenario: 数据不可用时关注保守处理
- **WHEN** `profile.detail` 标记作者资料不可用
- **THEN** `FollowAgent` 按数据缺失保守处理（倾向 skip），而非把"缺失"误判为"0 粉丝低质量"

### Requirement: 已关注作者不进主页子链

当笔记详情页显示作者**已被关注**时，系统 SHALL 跳过作者主页子链——MUST NOT 下发 `xiaohongshu.profile.open`、MUST NOT 浏览主页、MUST NOT 发起关注。`note.detail`（edge → cloud）SHALL 携带可选 `authorFollowed: boolean`，由边缘在 `xiaohongshu.note.open` 时读取笔记 modal 作者区关注按钮状态（文案 `已关注/互关` 或等价状态标记，复用关注执行的检测口径）得出；该状态是平台**当下真实**信号，边缘只读取上报、MUST NOT 臆造。`AuthorEvaluator` 在互动后触发评估时，SHALL 在调用 LLM 之前判定：若 `authorFollowed` 为真，直接产出 `profile.skipped`（reason 表明已关注），不进入主页评估。

当 `note.detail` 未提供 `authorFollowed`（缺省/读取失败）时，系统 SHALL 回退到原有主页子链流程（不因缺该信号而中断）；此时末端 `xiaohongshu.user.follow` 的 `already_followed` 良性 no-op 作为兜底。该要求 MUST NOT 改变「仅在互动后才评估进主页」的既有触发语义（本闸位于该触发之后）。

#### Scenario: 详情页已关注 → 跳过主页与关注

- **WHEN** 笔记详情页作者区关注按钮显示「已关注/互关」，边缘据此在 `note.detail` 置 `authorFollowed=true`，且该笔记被互动（`interaction.completed`）
- **THEN** `AuthorEvaluator` 不调用 LLM、直接 `profile.skipped`（reason 表明已关注），系统不下发 `xiaohongshu.profile.open`、不浏览主页、不发起关注

#### Scenario: 详情页未关注 → 正常评估是否进主页

- **WHEN** 关注按钮显示「关注」（未关注），`authorFollowed` 为 false/缺省
- **THEN** `AuthorEvaluator` 照常评估，符合条件则进入主页子链

#### Scenario: 缺 authorFollowed 信号时回退原流程

- **WHEN** `note.detail` 未携带 `authorFollowed`（旧边缘 / modal 无按钮 / 读取失败）
- **THEN** 系统按原有主页子链流程运行（行为不劣化），并由末端 `xiaohongshu.user.follow` 的 `already_followed` no-op 兜底，不重复关注

