## Why

目前评论只在**自治浏览闭环**里被动发生：账号自己刷 feed、自己挑笔记、由 `CommentAppraiser` 的硬阈值（赞>1000 且 藏>300）+ LLM 判定决定要不要评。运营**无法主动指定**「按这个账号的人设、去搜一批最近一天最火的笔记、在其中挑一篇相关且没评过的、留一条贴合语境的评论」。

需要一个**按需、搜索驱动**的评论入口：飞书一句 `/comment <昵称>` 即触发，让账号用自己的人设 + 已沉淀的精选集生成搜索词、搜小红书、按「最近一天 + 最多收藏」筛、避开已评过的、挑最相关的一篇，读正文与现场评论后生成评论、经人工审核发出。这把「精选集 + 人设」从只喂发帖创作，扩展为也能驱动**主动的高质量评论触达**。

## What Changes

- **【新命令】** 新增飞书 `/comment <昵称>` 命令：仿 `/publish` 的解析 / 路由 / 回执 / 按昵称定位账号；两段式回执（先 ack「已触发」，人工审核通过发出后再补结果）。
- **【新编排】** 新增一条**按需、受控、独占边端**的一次性评论任务（仿发布任务形态）：命令触发 → 暂时结束该账号自动浏览会话以独占边端 → 跑有方向的步骤序列 → `finally` 恢复浏览；按账号串行，边端离线 honest-fail。
- **【当前笔记联系评论】** 对自治浏览中刚判定通过的热帖引流线索，自动联系评论必须复用当前 `note.detail` 上下文直接评论；不得再按标题搜索兜底，也不得评论相似笔记。触发只记联系尝试，只有最终真发出评论才消费共用 comment 配额。
- **【新角色 ①·搜索词生成】** 读账号人设兴趣 + 精选集（`curated_content`）高收藏笔记标题/主题 → 生成一小批搜索词；精选集稀疏时**退回人设种子词**兜底。
- **【新角色 ②·搜索笔记甄选】** 在「去重后」的候选里判断**人设强相关**（沾边/泛泛相关不算）并挑出**强相关且收藏最高的一篇**；当前搜索词无强相关候选时**换下一个搜索词重试**（有界、首中即止），词用尽仍无则诚实结束不评。
- **【搜索结果原生筛选】** 边端搜索后**驱动小红书搜索页原生「最多收藏」排序 +「一天内」时间筛选**再采卡片（现状只输入关键词+回车、不点排序/时间控件）；平台卡片真实暴露收藏数时回传 `collectCount`，不暴露时不伪造，云端以原生排序后的结果顺序为主。协议按 v2 四处同步扩展（搜索指令加排序/时间参数、结果卡片保留收藏数字段）。
- **【去重·未评论过】** 进入甄选前先滤掉本账号**已评论过**的笔记（复用每笔记已交互去重，`action='comment'`，按账号）。
- **【撰写接入现场评论】** 复用既有「撰写→去AI味→人工审核→发布」尾链；其中撰写角色**小改为同时读现场评论**（现状只看标题+正文+精选参考）。
- **【门槛取舍】** 命令路径**跳过**自动 `CommentAppraiser` 的硬数值阈值（用户已手动指定意图，改由角色②相关性把关），**保留**飞书人工审核闸；**不计入**风控按天评论配额、不经 `canDo('comment')` 门控（人工授权，与 `/publish` 越过风控同理——不消耗自治评论预算、不动风控态；仍记每笔记去重）。
- **【角色入目录】** 两个新角色登记进云端角色目录（判定类），后台「角色管理」数据驱动、自动出现、可配模型/温度（前端无需改）。

> 非 BREAKING：命令、角色、协议字段均为新增；自治浏览闭环的搜索/评论行为不变。每次只评一篇。

## Capabilities

### New Capabilities
- `comment-search-command`: 飞书 `/comment` 命令触发的按需、搜索驱动评论任务——含命令与受控编排、两个新角色（搜索词生成 / 搜索笔记甄选）、有界换词重试流程（角色①出有序多词 →〔逐词：原生「最近一天+最多收藏」筛选 → 去重 → 人设强相关择优；命中即止，不中换下一个词〕→ 读正文与现场评论 → 撰写 → 人工审核 → 发布 → 记账去重 → 恢复浏览；词用尽/达上限仍无强相关则诚实结束）、搜索结果原生筛选与收藏数采集的协议增量、以及门槛/审核/配额/账号隔离/诚实红线。

### Modified Capabilities
<!-- 无：本 change 复用既有 comment-interaction（撰写/去AI味/人工审核/发布动作/风控配额）与 concept-pool-search（搜索下发/限频）能力但不改其 spec 级行为——自治浏览闭环不变。命令路径的差异（替代触发、跳过硬阈值、撰写读现场评论、搜索原生筛选与收藏数协议增量）作为 ADDED 需求收在新 capability 内，归档时不与既有 spec 冲突。 -->

## Impact

- **aidcp-cloud（主体工作量）**
  - 飞书命令：`src/feishu/commands.ts` 加 `comment` 动作（`parseCommand` + `CommandRouter.runComment` + `CommandActions.comment`）+ HELP；`src/server.ts` 接 `actions.comment`（仿 `actions.publish`：按昵称定位账号 → 触发评论任务）。
  - 新模块 `src/comment-agent/`（仿 `src/publish-agent/`）：`CommentScheduler.triggerManual(accountId)` 一次性触发 + 一个有方向的步骤编排（搜索词 → 搜索 → 采列表 → 去重 → 甄选 → 开笔记 → 翻评论 → 撰写 → 审核 → 发布 → 恢复），独占边端走接管/恢复钩子（仿 `onPublishTakeoverStart/End` 新增 `onCommentTakeoverStart/End`，reason `comment_takeover`），按账号串行 + 边端离线 honest-fail。
  - 新角色 ①：`src/agents/comment-search-term-generator.ts`（读 `getSoul` + `curatedStore.selectForCreation` → 搜索词集）。
  - 新角色 ②：`src/agents/comment-target-picker.ts`（读候选卡片 + 人设 → 相关性 + 最多收藏择一）。
  - `src/event-bus/types.ts`：`RoleName` 加两角色；如需新事件载荷则加 `RoleEventMap`。
  - `src/config/role-catalog.ts`：两角色登记进 `ROLE_CATALOG`（判定类 `browse_judge`），否则运行时回落全局默认模型（见 `curated-admission-eval-roles` 6.1 真机教训）。
  - 撰写小改：`src/agents/comment-composer.ts` `buildPrompt` 增加可选「现场评论」输入。
  - 去重：评论发布前调每笔记去重（`risk_interactions`，`hasInteracted(noteId,'comment')`），发布成功后 `recordInteraction(noteId,'comment')`。
  - 协议（cloud 侧）：`src/comm/protocol.ts` 搜索指令加排序/时间参数、结果卡片加收藏数；`src/comm/command-bridge.ts` 映射不漂移。
- **aidcp-edge（新活，主要不确定性）**
  - `src/browse/search-handler.ts`：搜索后**驱动原生「最多收藏」排序标签 +「一天内」时间筛选**控件。
  - `src/browse/feed-scroller.ts` 卡片扫描 + `browse-session.ts` `reportVisibleCards`：平台卡片真实暴露收藏数时采集；不暴露时不伪造，依赖原生「最多收藏」排序后的顺序。
  - `src/comm/protocol.ts`（与 cloud 逐字一致）+ `src/client/edge-client.ts` 主动命令路由白名单（若新增主动下发命令）。
  - ⚠️ 原生筛选控件选择器随搜索页宽窄屏布局变，**需真机标定**（参 [[xhs-responsive-nav-layout]]）。
- **aidcp-console**：几乎不动——新角色经角色目录自动出现在「角色管理」；可选给两角色补中文用量标签（`src/types/usageLabels.ts`，仅影响用量页显示）。
- **DB**：无新表 / 无新列（复用 `curated_content`、`risk_interactions`）。
- **协议 v2**：四处原子同步（两份 `protocol.ts` 逐字一致 + `command-bridge` 映射 + `docs/protocol.md` 计数与表 + edge `edge-client` 主动命令白名单）；`AC-PROTO-*` 计数断言随之更新。
- **红线**：保留人工审核（`AC-PUB`：未授权绝不发）；按账号隔离（精选/去重/落评论不跨账号，PII 红线）；边端离线/撞验证码/筛选未生效一律 honest-fail，绝不静默假成功；不改风控终态单写、不改自治浏览闭环。
