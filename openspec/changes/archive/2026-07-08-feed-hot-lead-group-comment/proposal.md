## Why

运营想对「小红书上正在被推流、涨得最快」的帖发带群码的引流评论。当前系统没有任何一条「刷 feed 刷到热帖就引流」的路径：① 自治浏览闭环里的被动评论只按**存量绝对量**（赞>300 且 藏>100 或 赞>10000）判要不要评、且**永不带群码**（硬不变量）；② 带群码的引流评论只有两条**受控通道**（飞书 `/comment group:on` 与排期自动群评），且都是**搜索驱动选帖**（人设关键词搜「最近一天最多收藏」），跑起来会**独占边端、结束自治浏览**——覆盖的是「搜到的帖」，不是「刷到的帖」。此外全链路**从未采集笔记发布时间**，算不出「每小时点赞」这类**速率**信号。

诉求本质：**复用浏览闭环已有的 feed 发现能力，在它逐篇打开的详情上增加一道「热度速率过滤」，把「涨得快」的热帖挑出来，再走受控通道（人审逐条）发带群码的引流评论**。红线不动：浏览闭环永不自动发群码，群码只经人审=发的受控通道。

## What Changes

- **【新增·边缘抽取】** 详情页新增抽取笔记的**原始发布相对时刻文本** `publishedAtText`（如「3小时前 / 昨天 14:30 / 07-05」），从**正文列底部的日期容器**取（真机校准的窄选择器），与正文抽取器物理隔离、加入正文排除清单，守 f8712f5 不污染正文。边缘只抽原始文本、**不解析、不判热度**（边轻云重）。feed 卡片层不采集（无 DOM 源）。
- **【新增·协议字段】** `note.detail` 上报增加**单个**可选字段 `publishedAtText`（云端自己派生小时数与速率，不占协议字段）。协议 v2 四处原子同步（两份 `protocol.ts` 逐字一致 + `command-bridge` 映射 + `docs/protocol.md` 计数与表；只加上报字段、无新消息类型、无新主动命令，白名单不动）。
- **【新增·云端判定角色】** 新增「引流线索评估」角色，**订阅浏览闭环的 `note.detail.arrived` 事件**（仿 `curated_note_evaluator` 的订阅接线，搭浏览闭环开详情的便车、fire-and-forget、零额外开销）：把 `publishedAtText` 解析成距今小时数（小时形态精确 / 「昨天」无时刻常数 ~36h / 裸日期视为超窗丢弃 / 无法识别→`null`，绝不臆造）→ 算**每小时点赞速率** `likeCount / max(hoursAgo, FLOOR)` → 过**过滤闸**（帖龄≤上限 且 速率≥阈值 且 赞≥最小绝对值；小时不可得则不判为热帖）→ 命中即入「引流待评候选队列」。判定是**纯确定性阈值闸、不调 LLM**（相关性交给消费时人审逐条判），因此 roleName 进 `RoleName` 穷举但**不登记 `role-catalog`**（对齐「role-catalog 仅列真调大模型角色」白名单）。
- **【新增·阈值后台可配】** 帖龄上限 / 速率阈值 / 最小赞做成**全局后台可配**，落「安全」页（`QuotasPage`）复用「互动质量阈值(全局)」机制（`session_config_global` 自愈加列 + facade + `/api/session-limits` 类端点 + 热加载 provider）；判定角色从 provider 现读，运营改完即时生效、不重发边缘。**不复用** `quota_config.per_hour[like]`（那是本账号限频、非帖子热度）。起步只全局（YAGNI）。
- **【新增·候选队列】** 新增持久「引流待评候选队列」（按账号存 `{noteId, 快照(标题/赞/速率/帖龄), status, discoveredAt}`，启动幂等自建表，无迁移器）；**入队即去重**（滤掉本账号已评过 `hasInteracted(noteId,'comment')` 与已在队列的）。**只发现、不发布。**
- **【新增·人审逐条消费】** 运营从候选队列逐条取用（飞书命令 / 面板），对选中那条帖发一条带群码的**定向引流评论**：复用现成的**按 noteId 定向评论**通道（`CommentScheduler.triggerTargeted` → `runTargetedTask`，已支持带群码），走**去AI味 → 群码 verbatim 追加 → 飞书人审=发**；发出后记账去重、该 lead 置 actioned。
- **【红线·发布路径不变】** 浏览闭环 **MUST NOT** 因本 change 产生任何自动发评论 / 自动注入群码；群码仍只经受控通道（人审=发 / 排期日上限+错峰+一码一号+canDo）。本 change 新增的是「发现+过滤+入队」和「人审逐条触发既有定向评论」，**不新增任何自动发布路径**。

> 非 BREAKING：新增上报字段 + 新判定角色 + 新队列表 + 复用既有定向评论通道；自治浏览闭环的评论/发布行为、风控终态、群码红线均不变。发布时刻不可得时该帖不入队（等价于现状不覆盖）。

## Capabilities

### New Capabilities
- `feed-hot-lead-group-comment`: 浏览闭环 feed 发现 + 热度速率过滤 + 引流待评候选队列 + 人审逐条定向群评。含边缘原始发布时刻抽取（隔离正文）、协议单字段上报、云端「引流线索评估」角色（订阅 `note.detail.arrived`，解析小时→算速率→过滤闸→入队）、持久候选队列与去重、人审逐条消费复用既有按 noteId 定向评论 + 群码注入 + 人审闸，以及「浏览闭环永不自动发群码」红线的原样保留与诚实回退（时刻不可得→不入队、不臆造）。

### Modified Capabilities
<!-- 无。消费复用既有 comment-interaction（撰写/去AI味/人审/发布动作）与 group-chat-injection（群码 verbatim 注入/缺码 fail-closed/一码一号/人审=发）能力但不改其 spec 级行为（定向评论 triggerTargeted 已存在，本 change 只新增「由候选队列 lead 触发」这一入口）；详情抽取新增的是全新字段，不改 note-extraction-fidelity 既有正文抽取行为。以上均作为新 capability 的 ADDED 需求收口，归档不与既有 spec 冲突。 -->

## Impact

- **aidcp-edge**
  - `src/browse/note-extractor.ts`：新增发布时刻文本抽取（正文列底部日期容器的窄选择器，真机校准 ⚠️）；把该选择器加入正文抽取排除清单，与 `NOTE_BODY_SELECTORS` 隔离；只回传原始文本、不解析。
  - `src/comm/protocol.ts`：`NoteDetailPayload` 加 `publishedAtText?`（与 cloud 逐字一致）。
  - `src/browse/browse-session.ts`：`note.detail` 组装带上原始文本。
- **aidcp-cloud**
  - `src/comm/protocol.ts` + `src/comm/command-bridge.ts`：`NoteDetailPayload` 同步加字段、映射不漂移。
  - `note.detail.arrived` 事件载荷透传 `publishedAtText`。
  - 新增发布时刻解析 + 速率工具（解析规则见 design；`likeCount` 复用既有 `parseCount`）。
  - 新增「引流线索评估」角色（订阅 `note.detail.arrived`，仿 `curated_note_evaluator` 订阅接线）：**纯确定性阈值闸、不调 LLM**；只登记 `event-bus/types.ts` 的 `RoleName`，**不进 `role-catalog`**；在 `RoleDispatcher.setup()` 条件注册（依赖队列 store）。
  - 阈值配置面：`session-config-store` 自愈加三列（帖龄上限/速率阈值/最小赞）+ facade 校验 + panel `/api/session-limits` 类 GET/PUT + 热加载 provider；判定角色现读。
  - 新增候选队列存储（新表 `hot_lead_queue`，启动幂等自建；入队去重）。
  - 人审逐条入口：飞书命令 / 面板列队列 + 触发 `triggerTargeted(accountId, noteId, {injectGroup:true})`；发出后 lead 置 actioned + `recordInteraction`。
- **aidcp-console**：① 「安全」页（`QuotasPage`）新增「内容热度过滤(全局)」卡片配三阈值；② （可选）「引流待评候选队列」只读列表 + 「发引流评论」按钮（走 `/api` 触发定向评论），不做也可用飞书命令消费。
- **DB**：新增 `hot_lead_queue` 表（启动自建、无迁移器，仿 `group_comment_attempts`）。
- **协议 v2**：四处原子同步；只加字段、消息类型计数不变，`AC-PROTO-*` 断言随字段更新。
- **热点文件串行**：两份 `protocol.ts` + `command-bridge.ts` + 角色注册（`RoleName`/`role-catalog`）为热点；须与活跃 change `comment-search-command` 等**串行**、单写。
- **红线**：浏览闭环不自动发群码、群码只经受控通道、人审=发、缺码 fail-closed、一码一号、发布时刻不可得诚实回退（不入队、不臆造）——全部不变。
