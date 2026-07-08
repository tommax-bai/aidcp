## Context

诉求：复用浏览闭环已有的 feed 发现能力，在它逐篇打开的详情上加一道「热度速率过滤」，把「涨得快」的热帖挑出来，走人审逐条发带群码引流评论。

现状事实（已 grounding，均带代码位置）：
- **发现面**：自治浏览闭环刷 feed → 选卡开笔记 → 深读，边缘上报 `note.detail`，云端转成 `note.detail.arrived` 事件（`role-dispatcher.ts:1514`），多个判定角色订阅它（如 `curated_note_evaluator` 读详情判要不要入精选，`content-curator-role.ts:47` / `curated-note-evaluator.ts:77`）。载荷带全文 + 赞藏数。
- **群码红线**：浏览闭环产出的评论下发结构上只带 `{noteId,text,thinkMs}`、无群码（`role-dispatcher.ts:1306`）；群码只经命令/排期两条受控通道汇入 `CommentScheduler.triggerManual({injectGroup})`；「浏览闭环永不自动注入群码」是硬不变量。
- **定向评论已存在**：`CommentScheduler.triggerTargeted(accountId,…)` → `runTargetedTask(…, groupChatCode, …)`（`comment-scheduler.ts:192/278`）已支持**按 noteId 定向评论并带群码**，自带去AI味→群码 verbatim 追加→飞书人审=发。
- **缺口**：全链未采集发布时间，算不出速率；带群码的选帖是搜索驱动（独占边端、结束浏览），覆盖「搜到的」不是「刷到的」。

约束：① 协议 v2 四处原子同步；② 红线「MUST NOT 静默假成功」（抽不到→null、不臆造）；③ 边轻云重、状态单写；④ 浏览闭环永不自动发群码。

## Goals / Non-Goals

**Goals:**
- 复用浏览闭环发现面：在它已打开的详情上做热度评估，零额外开销。
- 边缘只抽原始发布时刻文本；云端解析小时 + 算速率 + 过滤 + 入队（决策收云端、可只改云端调参）。
- 过滤出「涨得快」热帖入持久候选队列（只发现、不发布），入队去重。
- 人审逐条消费：复用既有按 noteId 定向评论 + 群码注入 + 人审=发。
- 红线不动：浏览闭环永不自动发群码。

**Non-Goals:**
- **不**在 feed 卡片层采集发布时间（无 DOM 源）。
- **不**新增任何自动发布 / 自动注群码路径；浏览闭环发布行为不变。
- **不**做「搜索驱动选帖排序」（前一版方案的错误接入点，已废弃）。
- **不**追求分钟级精度（日期形态天然 ±24h）。
- **不**改风控终态、人审闸、日上限、一码一号。

## Decisions

### D1. 评估放云端新增判定角色，接在「稿件价值判定」之后（挂 `quality.pass`）
新增「引流线索评估」角色，放云端（热度判定是决策、阈值要随真机调参、云端可只改一处不必重发边缘）。**接入位置 = 稿件价值判定角色（`content-curator-role`）之后**：浏览闭环的事件链是 `note.detail.arrived → content-curator(质量判定) → quality.pass → deep-reader(深读) → 互动/评论`；`quality.pass`（`role-dispatcher`/`content-curator-role.ts:88`）是既有**硬价值闸**（深读与整条互动链都挂其后）。引流线索评估挂 `quality.pass` 后面 = **继承这道质量门槛**，不把「很火但很水」的帖放进引流队列。
- **两事件按 noteId 对齐**：`quality.pass` 载荷只带 `{noteId, sourcePageType, reason}`、不带赞数/发布时刻；故角色同时订阅 `note.detail.arrived`（缓存当前这篇的 `noteId/likeCount/publishedAtText`，浏览闭环一次只开一篇、缓存最近一篇即可）与 `quality.pass`（对放行 noteId 取缓存详情、跑热度闸、命中入队）。这是仓内既有「两事件按 noteId 关联」惯用法。
- 判定仍是**纯确定性**：LLM 质量判断在 content-curator 完成，本角色只在其放行后跑数值热度闸、自身不调 LLM（故不进 role-catalog，见 D1b）。fire-and-forget、不阻塞浏览。
- 注册点：`RoleDispatcher.setup()`，仿 `curated_note_evaluator` 的**条件注册**（依赖「引流待评候选队列」store，store 可用才注册；store 从 `RoleDispatcherOptions` 加字段、`server.ts` 接线）。roleName 进 `RoleName` 穷举（热点文件，串行）。
- 透传 `publishedAtText` 只改两处（协议 `NoteDetailPayload` + 事件 `NoteDetailData`）；`handler.ts` 整对象透传、不用改。
- 取舍：被 `quality.reject`（含 LLM 出错/解析失败按 reject 处理）的帖即使很火也不入队——绝大多数是要的（挡垃圾）；content-curator 判据是「策展质量」，与「好引流目标」高度相关但不完全等同，若要连它会拒的爆帖也捞，才改挂原始 `note.detail.arrived`。默认挂 `quality.pass`。
- 备选：边缘算热度 → 否决（违边轻云重、调参要重发边缘）。
- 备选：接进搜索选帖角色 `comment_target_picker` → **否决**（前一版致命缺陷：选帖发生在开详情之前，那时没有发布时刻；且发现面是「搜到的」不是「刷到的」）。
- 备选：挂更下游的 `interaction.completed`（账号真点赞/收藏过的帖）→ 漏斗更窄、门槛更高，但用户问的是「稿件价值判定之后」，故取 `quality.pass`。

### D1b. 判定做纯确定性阈值闸，不调 LLM、不进 role-catalog
判定 = `发布时刻在窗内 且 velocity≥阈值 且 likeCount≥下限 且 本账号未评过` —— 全客观可算，照 `comment-appraiser.ts:106-111` 的便宜数值闸模式，**不需要模型**。因此：
- 构造**不把 `llm` 当必需依赖**（不像 `curated-note-evaluator.ts:69` 那样 throw）。
- **不登记 `role-catalog`**：role-catalog 是「现役且真调大模型」的白名单（`role-catalog.ts:7-8` 明写纯规则角色 MUST NOT 出现）；纯确定性角色进去是死配置。大量非 LLM 角色（feed_scroller/note_opener 等）只在 `RoleName`、不在 role-catalog——本角色同理。
- 相关性（帖与引流主题搭不搭）交给**消费时的人审逐条**判，检测环节不做 LLM 相关性、保持轻。
- 备选（暂不做，YAGNI）：若日后要在检测就做主题相关性，可叠一段 LLM 二段（仿 comment-appraiser 数值闸→LLM），那时才进 role-catalog。

### D8. 阈值走全局配置面（安全页），不接风控限频表
三参数（帖龄上限 `post_age_max_hours` / 速率阈值 `velocity_min` / 最小赞 `min_like_floor`）做成**全局后台可配**，落「安全」页（`QuotasPage.tsx`），复用「互动质量阈值(全局)」那套：`session_config_global` 单行表用自愈 `ALTER ... ADD COLUMN IF NOT EXISTS` 加三列 + facade 校验 + `/api/session-limits`（或紧邻新端点）GET/PUT + 热加载 provider；「安全」页加一张「内容热度过滤(全局)」卡片。判定角色从该 provider 现读，运营改完即时生效、不重发边缘。
- **纠偏**：速率阈值 **不复用** `quota_config.per_hour[like]`——后者是「本账号每小时点赞几次」的风控限频，与「候选帖每小时被点多少赞」的帖子热度是两个概念，属新加列。
- 起步只做全局（YAGNI，同一质量红线对所有账号一致）；`curated-gate.ts` 的 `resolveCuratedGateConfig(accountId)` 占位为日后按账号 override 预留，需要时照抄排期页「全局默认 + 每账号侧表、effectiveX = override ?? global」。

### D2. 边缘只抽原始文本，云端解析
边缘 `note.detail` 只回传 `publishedAtText`（原始 DOM 串）。解析成小时、算速率全在云端。协议因此只加**一个**字段（不加 `publishedHoursAgo`），更薄、更好调，也少一处字段漂移面。

### D3. 发布时刻解析规则（帖龄上限把裸日期挡在窗外，解析只需处理小时级形态）
关键洞见：帖龄上限（D4 的 `MAX_AGE_HOURS`，默认小，1–2 天）与小红书的展示粒度天然咬合——平台按 `刚刚 / X分钟前 / X小时前 / 昨天` 展示新鲜帖，**再老才跳成裸日期 `MM-DD`（基本 ≥2 天前）**。所以只要上限取小：
- 窗内形态只有 `刚刚/分钟/小时/昨天`，全是小时精度，速率算得准。
- 一旦是**裸日期 `MM-DD` / `YYYY-MM-DD`**，基本已超窗 → **直接判超龄丢弃、不入队**，无需按当前日期换算小时。
解析规则（不臆造）：
- 「刚刚 / X分钟前」→ `0`（不足 1 小时，速率用 FLOOR 分母）。
- 「X小时前」→ `X`（小时精度，速率最准）。
- 「昨天 HH:MM」→ 有时刻按时刻算；「昨天」无时刻 → 常数 `~36h`（24–48 中点）。
- 「MM-DD / YYYY-MM-DD」等裸日期 → 视为**超窗**（`ageHours` 记为大于上限的哨兵值）→ 过滤闸直接判超龄丢弃。
- 剥离「编辑于」前缀 / 地区后缀；**无法匹配任何形态 → `null`**（不臆造、不入队）。
> 这样「>24h 一律 48h 常数 vs 按日期真算」这个纠结从根上消失：超窗的帖压根不参与，不需要给它算速率。既否决了「一律 48h」的失真（常数把 2 天和 30 天前的帖当成一样，老帖假冒涨得快），也省掉了「日期真算」的代码——因为窗一小，裸日期即超窗。若日后把上限调大到需要区分裸日期年龄，再补「按当前时钟真算天数→小时」（云端有时钟、可加），当前 YAGNI 不做。

### D4. 速率过滤闸（帖龄上限 + 速率阈值 + 最小赞），不做排序
`velocity = likeCount / max(hoursAgo, FLOOR_HOURS)`。**是布尔过滤闸不是排序**——因此前一版方案的「null 回退混合比较非传递」问题从根上消失。入队条件三者皆满足：
- `ageHours ≤ MAX_AGE_HOURS`（**帖龄上限，第一道闸**，默认小 1–2 天；裸日期/超龄直接淘汰，见 D3）；
- `velocity ≥ VELOCITY_MIN`（涨得快）；
- `likeCount ≥ LIKES_MIN`（最小绝对赞数，防「0.5h 20 赞=40/hr」小基数假热）。
- `hoursAgo === null`（时刻不可得/无法识别）→ **不判为热帖、不入队**（诚实回退，不臆造速率、不按绝对量硬塞）。
阈值/FLOOR/上限均为云端可配常量（先给保守默认，真机看分布再调，见 Open Questions）。帖龄上限做第一道闸的好处：把「涨得快」限定在平台推流新鲜窗内，且让解析器只需处理小时级形态（D3）。

### D5. 持久候选队列 + 入队去重
新表 `hot_lead_queue`（`account_id, note_id, snapshot_json, velocity, age_hours, status('pending'|'actioned'|'dismissed'), discovered_at`），启动幂等自建、无迁移器（仿 `group_comment_attempts`）。入队前去重：滤掉本账号**已评过**（`hasInteracted(noteId,'comment')`）与**已在队列 pending**的同 noteId。按账号隔离（不跨账号）。只落发现，不触发任何发布。

### D6. 人审逐条消费，复用既有定向评论
运营从队列逐条取用（飞书命令列队列+选一条 / console 面板按钮），对选中 lead 调既有 `triggerTargeted(accountId, noteId, {injectGroup:true})` → `runTargetedTask`：接管边端 → 打开**那一条** noteId → 读正文+现场评论 → 撰写 → 去AI味 → 群码 verbatim 追加 → **飞书人审=发** → 发出 → 恢复浏览。发出真 ok 后 `recordInteraction(noteId,'comment')` + lead 置 `actioned`；缺码 fail-closed、被拒/超时→lead 回 `pending` 或 `dismissed`（不静默假成功）。红线：发布只此受控通道，浏览闭环不碰。

### D7. 抽取作用域 = 正文列底部日期容器，隔离正文
发布时刻在 XHS 详情**正文列底部的日期节点**（真机校准的窄选择器，如 `.bottom-container .date` / 专门 date span / `time` 元素），**不在详情头部、不在互动栏**（互动栏只有赞藏评计数、无日期）。把该选择器加入正文抽取排除清单、与 `NOTE_BODY_SELECTORS` 隔离，jsdom 桩双向断言「日期不进正文、正文变更不吞日期」，守 f8712f5 污染回归。⚠️选择器需真机标定。

## Risks / Trade-offs

- **[裸日期无小时精度]** → 裸日期形态（`MM-DD`）已超帖龄上限、直接丢弃，不参与速率，故其精度缺失落在「本就不入队」的区间，无影响。仅当日后把上限调大到需区分裸日期年龄，才需补日期真算（云端有时钟）。
- **[发现面受限于「浏览闭环选择打开的帖」]** → 浏览闭环只对它决定开的帖 emit 详情事件，刷过没开的帖拿不到发布时刻、不参与。这是「零额外开销复用发现面」的必然代价；可接受（要覆盖全部得逐卡开详情，成本不划算）。
- **[速率与阈值需真机标定]** → 阈值拍太低→队列灌水，太高→常年空队列。默认给保守值 + 真机看速率分布再调；阈值收云端可热调。
- **[抽取污染正文回归 f8712f5]** → 窄选择器 + 排除清单 + 双向桩断言；⚠️真机标定标记。
- **[队列积压 / lead 过期]** → lead 带 `discovered_at`，消费时提示时效（速率是发现时快照，隔太久失真）；可选加过期清理，先不做（YAGNI）。
- **[热点文件并行撞车]** → 协议三处 + 角色注册为热点，与 `comment-search-command` 等**串行**、单写。

## Migration Plan

- 分两段落地，天然规避前一版的接入点难题：
  - **段一（发现+度量，可独立上线观测）**：edge 抽 `publishedAtText` + 协议字段 + 云端解析/速率 + 「引流线索评估」角色**只打日志/落队列 pending**，不接消费。真机看速率分布、校准阈值与选择器。
  - **段二（消费）**：接人审逐条触发既有定向评论。
- 纯增量、向后兼容：旧边缘不带 `publishedAtText` → 云端 hoursAgo=null → 不入队（等价现状不覆盖）。
- 部署：cloud 走标准 dev 安全序列（备份→rsync→restart→healthcheck）；edge 运营机 pull+重启。表启动自建。
- 回滚：cloud 单服务回滚；字段可选、边缘旧版自动 null 回退，前后兼容。

## Open Questions

- `VELOCITY_MIN` / `LIKES_MIN` / `MAX_AGE_HOURS` / `FLOOR_HOURS` 默认值——先给保守常量，段一真机看分布再定档。
- 消费入口先做飞书命令还是 console 面板——飞书更快落地（无前端改动），面板更顺手；建议段二先飞书、面板可选后补。
- 「昨天」无时刻用 36h 常数是否够——真机看「昨天」帖占比与其对入队的影响再定。
- 是否给 lead 加过期/清理——先不做，看队列实际积压再评估。
