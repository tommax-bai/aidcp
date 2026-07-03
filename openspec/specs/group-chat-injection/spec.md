# group-chat-injection Specification

## Purpose
TBD - created by archiving change account-group-chat-injection. Update Purpose after archive.
## Requirements
### Requirement: 每账号「关联群聊引流码」为原样存储的可选属性

系统 SHALL 为每个账号维护一份可选的「关联群聊引流码」自由文本（`group_chat_info`），经账号存储的一等单写方法读写。该值 MUST **原样存储**：MUST NOT `trim` 首尾空白、MUST NOT 设长度上限、MUST 保留 emoji 与换行（与既有分组标签写入的 `trim`+64 截断刻意相反）。空 / 空白输入 SHALL 归 NULL（清空该账号的码）。退役保留账号 `default` 的写 MUST 被拒。无覆盖行的账号读回 SHALL 为「无码」（null），MUST NOT 回落任何默认 / 打包码。

#### Scenario: 原样回读含 emoji 与换行的码
- **WHEN** 运营为某账号保存一串含 emoji、换行、首尾空白的群聊码
- **THEN** 该账号读回的码与保存的字节一致（emoji 完整、换行保留、首尾空白不被 trim、不被截断）

#### Scenario: 空输入清空
- **WHEN** 运营把某账号的群聊码保存为空 / 空白
- **THEN** 该账号的码归 NULL（无码），读回为 null

#### Scenario: 退役账号写被拒
- **WHEN** 对退役保留账号 `default` 写群聊码
- **THEN** 写被拒、不落库、与成功可区分地呈现

### Requirement: `/comment` 引流开关 `group:on/off` 逐次 opt-in

飞书 `/comment` 命令 SHALL 支持一个**尾部**引流开关 token `group:on`（开）/ `group:off`（关），大小写不敏感；命中即从 token 流剔除、其余 `join` 为目标昵称。开关 MUST 为**逐次 opt-in**：**不带**开关时命令行为 SHALL 与引入本能力之前**完全一致**（普通评论、零回归），系统 MUST NOT 因账号配了码就自动注入。解析 MUST 为 trailing-only（只认末尾开关），避免把中间 token 误当开关而错切昵称。

#### Scenario: 带 group:on 开启引流
- **WHEN** 运营发送 `/comment <昵称> group:on`
- **THEN** 该次评论任务标记为「需注入群聊码」，其余按 `/comment` 既有流程定位账号并执行

#### Scenario: 不带开关时零回归
- **WHEN** 运营发送 `/comment <昵称>`（无 group 开关）
- **THEN** 命令按引入本能力之前的行为执行普通评论，不注入任何码

#### Scenario: 含空格昵称 + 尾部开关正确切分
- **WHEN** 昵称含空格且命令以 `group:on` 结尾
- **THEN** 末尾开关被识别并剔除，其余部分完整还原为该昵称

### Requirement: 命中开关时在人审卡前 verbatim 注入并保证「审=发」

当该次任务标记为需注入且该账号有码时，系统 SHALL 把码 **verbatim 追加**到评论文本，且追加 MUST 发生在「去 AI 味 + 反照搬之后、飞书人审卡之前」。人审卡展示的文本 MUST 是含码的完整终稿（AC-PUB「审的就是发的」）。码 MUST NOT 参与反照搬（overlap）比对。既有正文长度闸只作用于**正文草稿**、在追加之前——追加后终稿可超该上限，此为有意（码本身长）、非缺陷。该次任务用于「缺码判定」与「实际注入」的码 MUST 为**同一次解析**的值（任务开始处解析一次），MUST NOT 在闸与注入之间二次读取（避免不一致）。

#### Scenario: 人审看到的即将发出的完整含码文本
- **WHEN** 一次需注入且有码的评论走到人审
- **THEN** 飞书人审卡上的文本已含 verbatim 群聊码，人审通过后边缘发出的正是这段文本

#### Scenario: 码不被去 AI 味改写、不进反照搬
- **WHEN** 注入发生
- **THEN** 码追加在去 AI 味与反照搬之后，未被重写 / 剥字符，且未作为正文参与 overlap 判定

### Requirement: 缺码时 fail-closed，绝不静默发无码评论

当该次任务标记为需注入、但该账号无码时，系统 SHALL fail-closed：回一张明确的告警回执「该账号未配置关联群聊信息」并**本次不发**。系统 MUST NOT 静默降级为发一条无码的普通评论。

#### Scenario: group:on 但账号未配码
- **WHEN** 运营对一个未配群聊码的账号发送 `/comment <昵称> group:on`
- **THEN** 系统回告警回执说明未配码、本次不发评论，不静默发无码评论

### Requirement: 边缘保真——人审文本可被边缘原样送达

系统 SHALL 保证人审通过的含码文本能被边缘**原样送达**为评论。鉴于边缘发评论会 `trim` 首尾空白、逐字符敲进带自动补全（`@` 提及等）的评论编辑器，系统 MUST 在码到达人审卡之前消除该发散：或在存储 / 注入前对码做校验 / 规整（拒绝或转义会触发编辑器补全的字符、约定换行策略、告知首尾空白将被 trim），或由边缘以不触发补全的整段插入方式送达。二者之一 MUST 成立，使「边缘将敲出的字节」等于「人审卡上的字节」。任一步为空 / 超时 / 被阻断 SHALL honest-fail，MUST NOT 静默假成功。

#### Scenario: 含编辑器触发字符的码不破坏「审=发」
- **WHEN** 群聊码含会触发评论编辑器自动补全的字符
- **THEN** 系统在人审前规整该码或以整段插入送达，使边缘发出的评论文本与人审通过的一致，而非被补全劫持 / 篡改

#### Scenario: 边缘无法送达时诚实失败
- **WHEN** 边缘发送该评论时目标缺失 / 未生效 / 遇验证码阻断
- **THEN** 边缘如实回报失败原因（no_target / state_unchanged / blocked_by_captcha 等），不谎报成功

### Requirement: 注入仅经命令式评论任务机器，自治浏览闭环永不自动引流

群聊码注入 SHALL 仅发生在命令式评论任务机器内——由飞书 `/comment group:on` 手动触发，或由内容排期调度器的群评动作触发（change `content-schedule-group-comments`）。**硬不变量保留**：系统 MUST NOT 在自治浏览闭环的评论撰写链注入任何群聊码——浏览闭环产出的评论永不携带引流码。排期触发的注入 MUST 经同一条命令式管线（缺码 fail-closed、人审卡前 verbatim 注入、人审内联），且 MUST 受排期侧刹车：每日自动尝试上限（持久、硬 ≤10）、按账号 × 动作错峰、一码一号硬阻断（开启即校验）、自动路径 `canDo('comment')` 配额。原「不做每账号引流频次上限」的留缝对**自动**情形由此正式补上；手动命令式仍无频次上限（人逐条掌控是刹车）。

#### Scenario: 浏览闭环评论不含码
- **WHEN** 自治浏览闭环自行对某笔记生成并发出评论
- **THEN** 该评论不含任何群聊引流码，无论相关账号是否配了码

#### Scenario: 排期群评经同一机器且带刹车
- **WHEN** 内容排期调度器触发某账号的群评动作
- **THEN** 走与 `/comment group:on` 完全相同的命令式任务机器（缺码 fail-closed、人审通过才发），且该次触发已过尝试型日上限、错峰与配额闸

#### Scenario: 无刹车的自动注入被判违背
- **WHEN** 任何路径试图在无人审或无日上限约束下自动注入群聊码
- **THEN** 判为违背本能力；注入必须同时具备人审与排期刹车

