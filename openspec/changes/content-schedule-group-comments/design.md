## Context

内容排期 Phase 1/2 已部署开闸：三态周历（自动 ⊆ 活跃云端强制）、每分钟心跳 `ContentScheduler`（动作循环 post+comment、每动作幂等键、错峰、fire-and-forget、风控 normal 闸）、每账号开关 / 日上限（发帖=已发+在途原子；评论=持久互动计数+单飞）。评论动作三件套为**可选 deps**（未注入整体跳过）——本变更按同构再加群评三件套。

群评底座（`account-group-chat-injection`，2026-07-03 归档）：每账号群码 `accounts.group_chat_info`（verbatim 存储）；`/comment group:on` 逐次 opt-in；注入在人审卡前 verbatim（审=发）；**缺码 fail-closed**（`comment-scheduler.ts:100-104`）；边端保真定案 split-typing（正文逐字敲 + 群码整段原子插入，edge `d714b9f`；真机探针 `1385fef`）。触发入口 `triggerManual(accountId,{injectGroup:true})` 现成——**本变更对 comment-agent/* 零改动**（那是活跃 change `comment-search-command` 的地盘）。

其 spec「仅命令式路径注入」（`openspec/specs/group-chat-injection/spec.md:58`）当年是硬 Non-Goal，理由「同码被一批账号高频发 = 最强封号指纹」，且刻意不做频次上限（唯一刹车 = 人逐条 opt-in）。放宽的正当性：当年缺的刹车本变更全部补上（见 D2/D3/D4），且「一码一号硬阻断」直接消灭「同码多账号」这个最强指纹本身。

约束：无迁移器（DDL 幂等自愈）；退役 `default` 拒；MUST NOT 静默假成功；评论人审铁红线；风控最终态单写（只读 `canDo` / 计数）；协议 v2 不动。

## Goals / Non-Goals

**Goals:**
- 排期时段内按账号错峰自动发起群评任务（评论机器 + `injectGroup:true`），每条人审、结果卡如实。
- 每账号「自动群评」开关 + 每日**尝试**上限（持久、保守方向、硬 ≤10）。
- 一码一号从软告警升级为**开启硬阻断**。
- 正式 MODIFIED 放宽「仅命令式」spec，浏览闭环永不注入保留为硬不变量。

**Non-Goals:**
- 不做评论搜索翻页（归 `comment-search-command` 家族 / 评论自动发布线）。
- 不碰 `comment-agent/*`、协议 v2、边端、浏览闭环、三态周历。
- 不做聚合层专门人审卡节流器（结构性受限论证见 D5）。
- 不做多群码 / 按群码轮换（一码一号是本设计的支柱，多码留待将来独立评估）。

## Decisions

### D1. 第三动作沿用评论机器，单飞与评论共用

动作循环扩为 `['post','comment','group_comment']`。群评与评论共用 `isCommentBusy`（同一台评论任务机器，isRunning 按账号）——同账号「评论任务在跑时群评不触发、反之亦然」天然成立，无需新互斥。错峰分钟按 `action='group_comment'` 独立哈希（与 comment 大概率岔开）；幂等键 `(账号|group_comment|小时格)`；每账号每 tick 至多一动作不变（顺序 post → comment → group_comment，前者命中则后者顺延到自己的分钟 / 下一活跃小时）。

- **为何群评排 comment 之后**：两者共用边端与评论机器，先后无本质差；固定顺序保证确定性。

### D2. 群评日上限 = 每日自动**尝试**上限（持久 attempts 表，方向保守）

新极薄表 `group_comment_attempts (id BIGSERIAL, account_id TEXT, attempted_at TIMESTAMPTZ DEFAULT now())`，由 `ContentScheduleStore.init()` 幂等自建；`countGroupAttemptsToday(accountId)` 按服务器本地日历日计数；**触发回执 ok（任务真开跑）即记**。

- **为何按「尝试」不按「发出」**：群评发出与普通评论共用互动记录（`action='comment'`），区分「带码/不带码」需改动评论链记账（comment-agent 地盘，撞活跃 change）或加带外归因（脆弱）。按尝试计数则完全在排期侧闭环：被人审拒 / 无强相关目标也占额度——对协同 spam 敏感动作这是**保守方向**（宁可少试，绝不多发），且重启不清零、无 TOCTOU。UI 文案明写「每日自动尝试上限」。
- **为何不复用 Phase 2 的互动计数**：那会让普通评论吃掉群评额度、且无法单独限制群评——两个动作的风险面不同，必须独立计数。
- **硬上限 0..10**：store 校验层与发帖/评论的 0..50 刻意分开（`GROUP_COMMENT_DAILY_CAP_MAX = 10`），越界整块拒；UI 建议 ≤3。

### D3. 一码一号硬阻断，落在「开启」写路径

`store.setAccount` 收到 `groupCommentEnabled: true` 时（且仅在从关到开的写入时）校验：

1. 该账号 `accounts.group_chat_info` 为 NULL → 拒 `no_group_code`（没码开开关无意义，提前拦比触发时黄卡友好；触发时缺码 fail-closed 仍在，纵深）。
2. 存在**其它**账号的 `group_chat_info` 与该账号 **verbatim 相等** → 拒 `shared_group_code`。

- **为何硬阻断而非沿用软告警**：手动路径人逐条掌控，软告警够；自动化无人在场、暴露随时间累积,「同码多账号」是当年 Non-Goal 的核心理由——把它做成结构上不可能，放宽才站得住。
- **已开启后改码的绕道**：运营先开群评、再把码改成与他号相同——录入路径（`setGroupChatInfo`）不在本 store、不加跨店联动校验（YAGNI + 避免撞 accounts 拥有者）；兜底：调度器触发前不重查同码（成本高），接受此窄缝并在设计与 console 文案声明「改码后请自查一码一号」；`shared_group_code` 校验在**每次** `groupCommentEnabled:true` 的写入时都会重跑（重新保存开关即重查）。

### D4. server 包装 `triggerGroupComment`（与 Phase 2 评论包装同构）

`canDo('comment')` 拒 → 黄卡「配额拒绝、本槽未触发」；过 → `triggerManual(accountId,{injectGroup:true})`；触发回执非 ok（**缺码 fail-closed** / 离线 / 未绑人设 / 在跑）→ 黄/红卡透传回执文案；**回执 ok → 记一条 attempt**（先记后返回，绝不静默）；终态结果卡由评论链自补，包装层不重复发。卡片 command 名「排期群评（自动）」。

### D5. 人审卡量结构性受限（不造节流器）

群评卡量上界 = Σ各账号 cap（硬 ≤10、UI 建议 ≤3）×（每动作每活跃小时至多一次错峰）×（评论机器按账号单飞串行）。多账号一码一号后无同码聚合风险，卡量与普通评论同数量级——专门聚合节流器 YAGNI，不做；若将来账号数量级变化再议（留缝：调度器闸序处加全局尝试闸即可）。

### D6. spec 放宽的写法

`group-chat-injection`「仅命令式路径注入」条款 MODIFIED 重写为两层：(a) **硬不变量保留**——自治浏览闭环评论撰写链 MUST NOT 注入任何群聊码（原 scenario 原样保留）；(b) **放行排期**——注入 MAY 由内容排期调度器触发，但 MUST 经同一命令式评论任务机器（人审内联、缺码 fail-closed）且 MUST 受排期刹车（尝试型日上限 + 错峰 + 一码一号硬阻断 + 自动路径配额）。当年 proposal「不做频次上限（留缝）」的缺口由本变更对 AUTO 情形正式补上；手动命令式仍无上限（人是刹车）。

## Risks / Trade-offs

- **[行为面残余指纹]** 一码一号消灭了跨账号同码，但「多账号各自的码在同段时间高频出现」仍是可聚合信号 → **Mitigation**：小日上限（硬 ≤10、建议 ≤3）+ 错峰 + 人审逐条；设计诚实声明非零风险，运营按账号价值自行权衡开几个。
- **[尝试型上限偏保守 → 空槽占额度]** 无强相关目标的尝试也烧额度，命中率低时（翻页未做）群评可能一天只发出 0–1 条 → **Mitigation**：这正是保守方向的代价，文案讲清；翻页增强落地后命中率自然抬升。
- **[改码绕过一码一号的窄缝]**（见 D3）→ **Mitigation**：重新保存开关即重查 + console 文案提醒；不做跨店联动（避免撞 accounts 拥有者与活跃 change）。
- **[与活跃 change 交织]** `comment-search-command`（28/34）活跃且占 comment-agent/*；本变更零改动该目录，`server.ts`/`panel/*` 走 worktree 车道 → **Mitigation**：land 前 rebase + 全量绿；worktree 提交显式列文件。
- **[真机端到端尚未以生产链路发过一条群评]** 保真已探针定案，但完整「/comment group:on → 人审 → 边端原样送达」的生产真机一条尚待运营执行 → **Mitigation**：登记真机 backlog；console 文案建议先手动跑一条再开自动；代码上线 ≠ 行为开启（开关默认关）。

## Migration Plan

- DDL：两列自愈补列 + `group_comment_attempts` 幂等建表；文档 `0030_content_schedule_group_comments.sql`。无回填（默认关 / 0 = 不自动 = 零回归）。
- 回滚：纯新增、默认关——撤代码即回 Phase 2 行为；表 / 列留空无副作用。
- 部署：cloud 测试全绿后按安全序列（脏则 `git archive`）；console build 后 rsync（不 `--delete`）。部署后无需动 env——`AIDCP_CONTENT_SCHEDULE_AUTO` 已开，群评是否自动完全由每账号开关（默认关 + 开启硬校验）决定。
- 归档顺序：本变更的 MODIFIED base（`content-schedule` / `group-chat-injection` / `console-write-operations`）均已在 `openspec/specs/`，无顺序约束。

## Open Questions

- 群评错峰是否要求与评论强制隔开最小间距？（默认不做——哈希天然岔开 + 单飞串行 + 各自小上限，YAGNI。）
- attempts 表是否需要定期清理？（默认不做——每天每账号 ≤10 行，年量级千行/账号，无清理必要；留缝后续按需加保留期。）
