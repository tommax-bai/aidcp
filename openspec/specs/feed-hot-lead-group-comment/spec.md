# feed-hot-lead-group-comment Specification

## Purpose
TBD - created by archiving change feed-hot-lead-group-comment. Update Purpose after archive.
## Requirements
### Requirement: 详情页诚实抽取原始发布时刻文本

边缘 SHALL 在浏览闭环打开笔记详情页时，从**正文列底部的日期容器**（真机校准的窄选择器）抽取笔记的**原始发布相对时刻文本** `publishedAtText`（如「3小时前」「昨天 14:30」「07-05」），并原样上报。该抽取作用域 MUST 与正文抽取器物理隔离、且该选择器 MUST 加入正文抽取排除清单，绝不把发布时刻文本混入正文。边缘 MUST 只回传原始文本、不解析成小时、不做热度判定（边轻云重）。feed 卡片层 MUST NOT 采集发布时间。

#### Scenario: 详情页有发布时刻文本

- **WHEN** 浏览闭环打开的笔记详情页底部展示「3小时前」
- **THEN** 边缘抽取该文本作为 `publishedAtText` 上报，且正文抽取结果不含该发布时刻文本

#### Scenario: 抽取不污染正文（f8712f5 回归）

- **WHEN** 对同一详情 DOM 分别跑正文抽取与发布时刻抽取
- **THEN** 正文输出逐字不含 `publishedAtText` 串，且开启发布时刻抽取前后正文输出不变

#### Scenario: 发布时刻文本缺失

- **WHEN** 详情页未渲染出可识别的发布时刻文本
- **THEN** `publishedAtText` 留空 / 不带该字段，边缘不臆造

#### Scenario: feed 卡片层不采集

- **WHEN** 边缘扫描 feed 瀑布流卡片
- **THEN** 卡片上报不含发布时间，且不为取发布时间而在卡片阶段逐张打开详情

### Requirement: note.detail 协议携带原始发布时刻文本单字段

系统 SHALL 在 `note.detail` 上报载荷新增**单个**可选字段 `publishedAtText`（不加解析后字段，云端自行派生小时与速率）。两份 `protocol.ts`（edge/cloud）MUST 逐字一致，`command-bridge` 映射 MUST 不漂移，`docs/protocol.md` 计数与表 MUST 同步。只加上报字段、不加消息类型、不加主动命令，主动命令白名单不动。`note.detail.arrived` 事件载荷 MUST 透传该字段供判定角色消费。

#### Scenario: 字段随详情上报并透传事件

- **WHEN** 边缘上报某笔记 `note.detail` 且携带 `publishedAtText`
- **THEN** 云端按同一契约读取，并经 `note.detail.arrived` 事件透传给判定角色

#### Scenario: 旧边缘不带字段向后兼容

- **WHEN** 未升级的边缘上报的 `note.detail` 不含 `publishedAtText`
- **THEN** 云端不报错，按发布时刻不可得处理（该帖不入候选队列）

### Requirement: 云端解析发布时刻为距今小时数

云端 SHALL 把 `publishedAtText` 解析为距今小时数 `hoursAgo`：「刚刚 / X分钟前」→ `0`；「X小时前」→ `X`；「昨天 HH:MM」按时刻算、「昨天」无时刻 → 常数（约 36 小时）；裸日期（`MM-DD` / `YYYY-MM-DD`）→ 记为**超帖龄上限的哨兵值**（判超龄丢弃）；剥离「编辑于」前缀与地区后缀后仍无法匹配任何形态 → `null`。云端 MUST NOT 把无法识别的文案臆造成具体小时数。

#### Scenario: 小时级文案

- **WHEN** `publishedAtText` 为「5小时前」
- **THEN** `hoursAgo` 解析为 `5`

#### Scenario: 分钟级 / 刚刚

- **WHEN** `publishedAtText` 为「刚刚」或「20分钟前」
- **THEN** `hoursAgo` 解析为 `0`

#### Scenario: 昨天无时刻

- **WHEN** `publishedAtText` 为「昨天」（无 HH:MM）
- **THEN** `hoursAgo` 取约 36 小时的常数

#### Scenario: 裸日期视为超窗

- **WHEN** `publishedAtText` 为「07-05」这类裸日期
- **THEN** `hoursAgo` 记为超帖龄上限的哨兵值，交由过滤闸判超龄丢弃，且不做臆造的精确小时

#### Scenario: 无法识别

- **WHEN** 剥离前后缀后 `publishedAtText` 不匹配任何已知形态
- **THEN** `hoursAgo` 为 `null`

### Requirement: 云端热度速率过滤闸

云端 SHALL 计算每小时点赞速率 `velocity = likeCount / max(hoursAgo, FLOOR_HOURS)`，并以布尔过滤闸判定是否「热帖线索」：当且仅当 `hoursAgo` 非 `null` 且三者皆满足——`ageHours ≤ MAX_AGE_HOURS`、`velocity ≥ VELOCITY_MIN`、`likeCount ≥ LIKES_MIN`——判为热帖线索。`hoursAgo` 为 `null` 或超帖龄上限时 MUST 判为**非线索、不触发**，MUST NOT 臆造速率、MUST NOT 按绝对量硬塞。这是过滤不是排序，MUST 不引入跨候选比较。判定 MUST 为**纯确定性**（不调 LLM）。判为「热帖线索」后是否发评论，另受「自动触发安全闸」需求约束。

#### Scenario: 涨得快且新鲜且够量 → 命中

- **WHEN** 某帖 `likeCount=5000`、`hoursAgo=2`、在上限内、超过速率与最小赞阈值
- **THEN** 判为热帖线索（是否发评论再过自动触发安全闸）

#### Scenario: 帖龄超上限 → 淘汰

- **WHEN** 某帖 `hoursAgo` 超过 `MAX_AGE_HOURS`（或为裸日期哨兵值）
- **THEN** 判为非线索、不触发，无论其绝对赞数多高

#### Scenario: 时刻不可得 → 不臆造

- **WHEN** 某帖 `hoursAgo` 为 `null`
- **THEN** 判为非线索、不触发，不臆造速率

### Requirement: 过滤阈值全局后台可配、热加载

过滤闸三参数（帖龄上限 / 每小时点赞速率阈值 / 最小绝对赞数）SHALL 由**全局配置面**提供，运营可在管理后台「安全」页编辑，改后**热加载即时生效**、无需重发边缘或重启。存储 SHALL 复用「全局质量阈值」机制（单行全局表 + 自愈加列 + facade 校验 + GET/PUT 端点 + 热加载 provider），判定角色现读该 provider。速率阈值 MUST NOT 复用账号自身的每小时限频配额（那是本账号动作限频、非候选帖热度）。起步 MUST 为全局（不做每账号）。

#### Scenario: 后台改阈值即时生效

- **WHEN** 运营在「安全」页改「内容热度过滤(全局)」的帖龄上限/速率阈值/最小赞并保存
- **THEN** 校验通过后热加载，后续 `note.detail.arrived` 判定即用新值，无需重发边缘/重启

#### Scenario: 非法值整块拒

- **WHEN** 提交的阈值非法（如负数/越界）
- **THEN** facade 校验 400 整块拒、不落库，沿用现有质量阈值的校验纪律

#### Scenario: 不接风控限频表

- **WHEN** 配置速率阈值
- **THEN** 其存储独立于账号限频配额表，二者语义不混用

### Requirement: 受闸自动评论触发 helper（回执 ok 才记账）

系统 SHALL 提供一个「受闸自动评论触发」helper（`triggerGatedAutoComment`），收口自动化联系评论的安全闸序与记账时机。闸序 MUST 为：`canDo('comment')`（共用评论安全配额，时/日）→ 子上限 `countContactAttemptsToday < contactCommentDailyCap`（与共用配额叠加即 min）→ 调触发闭包（浏览＝按 noteId `triggerTargeted({noteId,title},{injectContact})`）→ **仅当触发回执 `ok` 时**：`record('comment')`（消费共用评论安全配额）+ `recordContactCommentAttempt(accountId, {noteId, source, velocity, ageHours})`（子上限计数 + 审计）。任一闸不过 MUST 不触发、不记账。本 change 浏览路径经其触发；**排期评论/排期群评接入同一 helper（令其也 record 消费共用配额）为 follow-up**（本 change 未做，见 tasks/backlog）。

#### Scenario: 回执 ok 才记账（消费共用配额 + 子上限）

- **WHEN** 经 helper 触发一条联系评论且回执 `ok`
- **THEN** `record('comment')` 消费共用配额一次 + `contact_comment_attempts` 当日计数 +1（带 source/noteId 审计）

#### Scenario: 未真开跑不记账

- **WHEN** 触发被单飞/边端离线/缺联系方式等拒（回执非 ok）
- **THEN** MUST NOT 记账（不误占额度、不消耗配额）

#### Scenario: 子上限对浏览来源真生效

- **WHEN** cap=N，浏览路径经 helper 触发 N 次（均 ok）后第 N+1 次命中
- **THEN** 第 N+1 次因 `countContactAttemptsToday >= cap` 被拦、不触发

### Requirement: 引流线索命中即经 helper 自动触发群评

「引流线索评估」角色（`hot_lead_detector`，订阅 `quality.pass` + 缓存 `note.detail.arrived` 按 noteId 对齐）命中热度过滤闸后，SHALL 经「受闸群评触发 helper」（source='hot_lead'、target=noteId）自动触发带群码引流评论；不再持久化「引流待评候选队列」。被 `quality.reject`（含 LLM 出错/解析失败）的笔记 MUST NOT 触发。角色回调 MUST fire-and-forget、不阻塞浏览；roleName 在 `RoleName` 穷举内、纯确定性、MUST NOT 登记 `role-catalog`。系统 MUST NOT 设「每会话自动群评计数」这类随会话重置的装饰性节流；**权威节流 = 共用评论安全配额（时/日）+ 单场评论预算（场次）**，群评日上限为其下的子上限。账号联系评论模式为 `review` 时，撰写去 AI 味追加联系方式后推飞书人审卡；人点通过才真发。账号联系评论模式为 `auto_approve` 时，后台配置视为预授权，系统 SHALL 发送飞书免审通知并继续提交链路。账号联系评论模式为 `off` 或未配置时 MUST 不触发。

#### Scenario: 命中且过闸 → review 模式经 helper 触发飞书审批

- **WHEN** 笔记经 `quality.pass`、缓存详情命中过滤闸、本账号未评过/未在近期尝试过、联系评论模式为 `review`、且过全部安全闸
- **THEN** 经 helper 调 `triggerTargeted(injectContact:true)`，撰写去AI味追加联系方式后推飞书人审卡；人点通过才真发

#### Scenario: 命中且过闸 → auto_approve 模式经 helper 触发免审通知

- **WHEN** 笔记经 `quality.pass`、缓存详情命中过滤闸、本账号联系评论模式为 `auto_approve`、且过全部安全闸
- **THEN** 经 helper 调 `triggerTargeted(injectContact:true, approvalMode:'auto_approve')`，撰写后发飞书免审通知并继续提交链路

#### Scenario: 质量未通过不触发

- **WHEN** 笔记被 `quality.reject`（或 LLM 出错/解析失败按 reject 处理）
- **THEN** 即使热度命中也 MUST NOT 触发

#### Scenario: 不落队列

- **WHEN** 命中热帖但任一安全闸不过
- **THEN** 诚实略过、不发、**不入任何持久队列**（不再有 `hot_lead_queue`）

### Requirement: 浏览自动联系评论共用评论安全上限

浏览触发的自动联系评论 SHALL **与普通评论共用同一套评论安全上限**：**时/日**——helper 于触发回执 ok 后 `record('comment')` 消费同一 `RiskController` 评论配额（与自治浏览评论同池）；**场次**——detector 于触发前 gate 单场会话评论预算 `comments`、成功后扣减。自动化配置量 `contactCommentDailyCap` MUST 为**子上限**，与共用配额叠加即 min（`canDo` 先拦即等价 min），配置 MUST NOT 实际越过安全额。账号 `contactCommentMode` 为 `review` 或 `auto_approve`（默认 `off`）方触发；`review` 走人审，`auto_approve` 走后台预授权通知。缺联系方式 MUST fail-closed（本次不发、绝不降级无码评论）；账号未开时 MUST 等价现状（命中仅可记日志、不发），零回归。人工 `/comment` 命令 MUST 仍不占配额（人是刹车，不变）。

> 说明：本 change 未改 takeover 的 `skipRiskRecord` 语义，而由 helper 在浏览路径**显式 `record('comment')`** 达成共用配额消费；排期评论/排期群评纳入同一账本为 follow-up。

#### Scenario: 账号未开自动联系评论 → 不发（零回归）

- **WHEN** 命中热帖但账号 `contactCommentMode='off'`
- **THEN** MUST NOT 自动触发

#### Scenario: 浏览自动联系评论消费共用评论配额

- **WHEN** 某账号浏览触发发出一条联系评论成功
- **THEN** MUST `record('comment')` 消费共用评论配额且扣单场评论预算；后续该账号普通评论与联系评论共见余额减少

#### Scenario: 共用配额/单场预算耗尽 → 拦

- **WHEN** 账号已开自动联系评论但 `canDo('comment')` 被拒（时/日共用配额耗尽或风控态收紧）或单场评论预算已耗尽
- **THEN** MUST NOT 触发

#### Scenario: 缺联系方式 fail-closed

- **WHEN** 账号开了自动联系评论但未配置联系方式
- **THEN** 本次不发（明确失败），绝不降级为无联系方式评论

### Requirement: 去重覆盖未发出终态 + 尝试台账兼审计

系统 SHALL 对浏览触发去重覆盖三层：① `hasInteracted(noteId,'comment')`（已发出，risk_interactions）；② **短时 per-account「本 note 已尝试过（任意终态：发出/拒/超时/离线）」标记**，防人审拒或失败后重刷时反复推同一帖；③ `triggerTargeted` 单飞。`contact_comment_attempts` 台账 SHALL 加 `note_id / source / velocity / age_hours`（可空）列，令其兼作「系统自动给哪些帖、因多热发了联系评论」审计（零新表）。

#### Scenario: 人审拒后不立即重触发

- **WHEN** 某热帖触发后人审拒/超时，账号稍后重刷到同一 noteId（仍在短时标记窗口内）
- **THEN** MUST NOT 立即再触发同一帖

#### Scenario: 台账带审计维度

- **WHEN** 浏览路径记一条群评尝试
- **THEN** 该行带 `source='hot_lead'` + `note_id` + 速率/帖龄快照，可回查系统自动触达了哪些帖

