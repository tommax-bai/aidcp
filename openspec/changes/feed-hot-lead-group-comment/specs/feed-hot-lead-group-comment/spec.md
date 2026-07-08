## ADDED Requirements

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

云端 SHALL 计算每小时点赞速率 `velocity = likeCount / max(hoursAgo, FLOOR_HOURS)`，并以布尔过滤闸判定是否「热帖线索」：当且仅当 `hoursAgo` 非 `null` 且三者皆满足——`ageHours ≤ MAX_AGE_HOURS`（帖龄上限，第一道闸）、`velocity ≥ VELOCITY_MIN`、`likeCount ≥ LIKES_MIN`——判为热帖线索。`hoursAgo` 为 `null` 或超帖龄上限时 MUST 判为**非热帖、不入队**，MUST NOT 臆造速率、MUST NOT 按绝对量硬塞。这是过滤不是排序，MUST 不引入跨候选比较。判定 MUST 为**纯确定性**（不调 LLM）。

#### Scenario: 涨得快且新鲜且够量 → 命中

- **WHEN** 某帖 `likeCount=5000`、`hoursAgo=2`、在上限内、超过速率与最小赞阈值
- **THEN** 判为热帖线索

#### Scenario: 帖龄超上限 → 淘汰

- **WHEN** 某帖 `hoursAgo` 超过 `MAX_AGE_HOURS`（或为裸日期哨兵值）
- **THEN** 判为非热帖、不入队，无论其绝对赞数多高

#### Scenario: 小基数假热 → 淘汰

- **WHEN** 某帖 `likeCount=20`、`hoursAgo=0`（速率被 FLOOR 兜底后仍可能很高）但 `likeCount < LIKES_MIN`
- **THEN** 判为非热帖、不入队

#### Scenario: 时刻不可得 → 不臆造

- **WHEN** 某帖 `hoursAgo` 为 `null`
- **THEN** 判为非热帖、不入队，不臆造速率

### Requirement: 引流待评候选队列（只发现不发布，入队去重）

云端 SHALL 新增「引流线索评估」角色，**接在稿件价值判定之后**：仅对通过质量闸（`quality.pass`）的笔记评估热度。角色 SHALL 订阅两个事件并按 `noteId` 对齐——`note.detail.arrived`（缓存当前笔记的 `noteId/likeCount/publishedAtText`）与 `quality.pass`（对放行 noteId 取缓存详情跑过滤闸）；被 `quality.reject`（含 LLM 出错/解析失败）的笔记 MUST NOT 入队。命中过滤闸的帖 SHALL 把 `{accountId, noteId, 快照(标题/赞数/速率/帖龄), status, discoveredAt}` 入持久「引流待评候选队列」。入队前 MUST 去重：滤掉本账号**已评过**（`hasInteracted(noteId,'comment')`）与**队列内已有 pending** 的同 `noteId`。队列 MUST 按账号隔离。入队 MUST NOT 触发任何发布或群码注入——**只发现、不发布**。该角色 roleName MUST 进 `RoleName` 穷举，但因判定为纯确定性、不调 LLM，MUST NOT 登记 `role-catalog`（对齐「role-catalog 仅列真调大模型角色」白名单）。回调 MUST fire-and-forget，不阻塞浏览主路径。

#### Scenario: 质量通过且命中即入队

- **WHEN** 笔记先经稿件价值判定发出 `quality.pass`，其缓存详情命中过滤闸、本账号未评过、队列无同 noteId pending
- **THEN** 该帖入引流待评候选队列，status=pending，只落记录不发布

#### Scenario: 质量未通过不入队

- **WHEN** 笔记被 `quality.reject`（或 LLM 出错/解析失败按 reject 处理）
- **THEN** 即使其热度命中过滤闸也 MUST NOT 入队（继承稿件价值判定的质量门槛）

#### Scenario: 已评过去重

- **WHEN** 命中过滤闸的帖本账号已评论过（`hasInteracted(noteId,'comment')`）
- **THEN** 不入队

#### Scenario: 队列内重复去重

- **WHEN** 命中过滤闸的帖在队列已有同 noteId 的 pending 记录
- **THEN** 不重复入队

#### Scenario: 入队不发布

- **WHEN** 任一帖入队
- **THEN** 系统不因入队向该帖发布评论或注入群码

### Requirement: 人审逐条消费引流候选发定向群评

运营 SHALL 能从引流待评候选队列**逐条**取用，对选中 `noteId` 发一条带群码的定向引流评论，复用既有按 noteId 定向评论通道（`triggerTargeted(accountId, noteId, {injectGroup:true})` → `runTargetedTask`）：打开该 noteId → 撰写 → 去AI味 → 群码 verbatim 追加 → **飞书人审=发** → 发出。发出真 `ok` 后 MUST `recordInteraction(noteId,'comment')` 且把该 lead 置 `actioned`；缺码 MUST fail-closed（本次不发）；人审拒/超时/边端离线 MUST honest-fail，lead 不置 actioned、绝不静默假成功。

#### Scenario: 逐条人审发出

- **WHEN** 运营从队列选一条 pending lead 触发发引流评论
- **THEN** 走既有定向评论通道打开该 noteId、撰写去AI味、追加群码、经飞书人审通过后发出，lead 置 actioned 并记去重

#### Scenario: 缺群码 fail-closed

- **WHEN** 触发发引流评论但该账号未配置群聊引流码
- **THEN** 本次不发（黄卡/明确失败），绝不静默降级成无码评论，lead 不置 actioned

#### Scenario: 人审拒/超时诚实失败

- **WHEN** 人审未通过或超时或边端离线
- **THEN** 不发出、lead 保持 pending 或置 dismissed，honest-fail 不静默假成功

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

### Requirement: 浏览闭环永不自动发群码红线保留

系统 MUST 保留「浏览闭环永不自动注入群码 / 永不自动发评论触达」硬不变量。本 change 在浏览闭环内仅可做「发现 + 度量 + 过滤 + 入队」，MUST NOT 由浏览闭环自动向任何帖发布评论或注入群码。带群码的引流评论 MUST 仅经受控通道：人审逐条定向评论（人审=发），或既有排期通道（日上限 + 错峰 + 一码一号 + canDo）。

#### Scenario: 浏览闭环只发现不发布

- **WHEN** 浏览闭环刷到并打开一篇命中过滤闸的热帖
- **THEN** 系统仅入候选队列，MUST NOT 自动向其发评论或注群码

#### Scenario: 群码仅经受控通道

- **WHEN** 对某热帖发带群码的引流评论
- **THEN** 必经人审=发（逐条定向）或排期风控闸，本 change 不新增任何绕过人审/风控的自动带码路径
