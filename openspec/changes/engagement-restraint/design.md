## Context

云端是事件驱动多 Agent 浏览闭环：笔记详情上报后，`content_curator`（粗筛）→ `interaction_appraiser`（like/collect）→ 评论支线（`comment_appraiser`→…）→ `author_evaluator`（进主页）→ `follow_agent`（关注）逐角色接力，各角色产出意图事件，由 `RoleDispatcher` 的命令翻译（`setupCommandTranslation`）翻成边缘命令；该翻译处是**风控/配额/软暂停的统一闸**（`canInteract` + `RiskController.canDo` + budget）。

当前所有互动判定几乎只靠各角色 prompt 的 LLM 宽松判断，无数值/时间闸：粗筛门「默认继续看」、点赞「多数都该点」、进主页逐篇触发、关注偏宽。配额层（`quotas.ts` 三档 + `effectiveQuotas()`）与每会话预算（`freshBudget`）是仅有的两道数量天花板，但都偏高，真机一轮即大量消耗。

**红线约束（贯穿设计）**：① 边轻云重——edge 不做任何策略，冷却判定全在云端；② 风控终态单写——冷却是附加只读闸，绝不写 `risk_state` / 不调 `setQuotaLevel`·`applySignal`；③ 诚实硬失败——被冷却抑制 = 诚实跳过（不下发、不计数、不假成功）；④ 不碰协议——无新 `MessageType`，两份 `protocol.ts`/`command-bridge`/edge 白名单/`docs/protocol.md` 不动。

## Goals / Non-Goals

**Goals:**
- 互动筛选全程更挑剔（粗筛门 + 点赞 + 进主页 + 关注口径收紧），少读垃圾、少做无谓互动。
- 评论加可确定性判定的硬数值门槛（likeCount>1000 且 collectCount>300），叠加在现有 LLM 精品判定 + 人审之上。
- 每动作类型按账号设最小间隔冷却（like 2m/collect 5m/follow 10m/comment 30m），把动作节奏压稀、更拟人、延缓配额触顶。

**Non-Goals:**
- 不改协议、不改 edge、不加迁移、不动风控状态机与配额数字。
- 不给 profile.open 加冷却/预算（本次冷却只覆盖 like/collect/follow/comment 四个真实互动；profile.open 仅 prompt 抬门槛）。
- 不把冷却时长做成后台可配（本次写死常量；如需可配后续单独走 change，留干净缝）。
- 不持久化冷却（内存态；云端重启后短暂放宽可接受）。

## Decisions

### D1：冷却为独立云端模块 `ActionCooldownGate`（内存、按账号、按动作类型）
新增 `src/risk/action-cooldown.ts`：内部 `Map<accountId, Map<action, lastTsMs>>` + 写死常量 `COOLDOWN_MS = {like:120000, collect:300000, follow:600000, comment:1800000}`。接口：
- `canAct(accountId, action, nowMs): boolean` —— `nowMs - (last ?? -∞) >= COOLDOWN_MS[action]`（缺记录/未配置动作 → 放行）。
- `markActed(accountId, action, nowMs): void` —— 记录时间戳。

**为何独立模块而非塞进 `RiskController`**：风控终态单写是核心不变量，冷却是「节奏闸」而非「风控状态」，混入会模糊「谁单写终态」；独立模块只读判定、可脱离风控单测，也不进 `risk_state` 持久化路径。`nowMs` 由调用方注入（`Date.now`），便于单测注入假时钟。

### D2：like/collect/follow 在统一命令翻译闸处查冷却；comment 前置到评估阶段
- **like/collect/follow**：在 `RoleDispatcher` 命令翻译（现有 `canInteract`+`canDo` 那道闸）里，下发前加 `cooldown.canAct(accountId, action)`；未到点 → 与「被风控拒」同构地诚实跳过（不下发、不扣预算、记可观测原因 `cooldown`），到点 → 下发。
- **comment**：冷却前置到 `CommentAppraiser`（与「数量闸/阈值」同处早判），未到点 emit `comment.skipped{reason:'cooldown'}` → 直接进「是否进主页评估」。**理由**：评论要走撰写+去AI味+飞书人审（页面久留 + 占用人工），若拖到最终下发才被冷却拦截，会白白走完整条昂贵链路、还可能让人审通过后却被抑制——必须最早拦。

### D3：冷却时间戳在「真实发生」时落，而非下发时
`markActed` 挂在与配额计数同一时机——边缘真回执 `action.completed{ok:true}` 驱动 `RiskController.record(action)` 那条路径上同步落冷却时间戳（comment 同理 `ok:true` 才落）。**为何不在下发时落**：下发未必成功（找不到目标/验证码），按真实发生计时与「计数挂真回执」红线一致，避免一次失败动作白占一个冷却窗。对 follow 还需排除 `already_followed` no-op（与 follow 配额扣减口径一致：no-op 不算一次真关注，不重置冷却）。

### D4：冷却 MUST NOT 拦推进/返回指令
只对 `interaction.like`/`interaction.collect`/`interaction.follow`/`interaction.comment` 生效；`page.scroll`/`navigation.back`/`note.open`/`profile.open` 等推进/导航指令一律放行——与 `interaction-risk-gating` 既有「推进指令不被风控闸拦」同口径，杜绝浏览循环死锁。

### D5：评论硬阈值放在最便宜阶段、确定性判定
在 `CommentAppraiser.onInteractionCompleted` 现有「会话预算/每日上限」闸之后、取 `noteData` 之后、调 LLM 之前，加：`if (!(note.likeCount > 1000 && note.collectCount > 300)) skip('below_comment_threshold')`。严格大于（「超过」语义）。阈值写死常量（与冷却常量同处或就近），不做后台可配（YAGNI）。现有 LLM 精品判定 + 飞书人审保持不变，叠加在阈值之上（阈值是必要非充分条件）。

### D6：四道 prompt 收紧 = 改判定口径文字 + 同步人设
- 粗筛门（`content-curator-role.ts`）、点赞口径（`interaction-appraiser-role.ts` 决策逻辑 + `soul.yaml` 的 `like_principle`）、进主页（`author-evaluator.ts`）、关注（`follow-agent.ts`）。
- **点赞翻转需 spec delta**：现 `interaction-appraisal` 明文「点赞是低门槛高频」，收紧与之冲突——本 change 翻转该需求。`like_principle` 与 prompt 框定 MUST 保持一致（spec 既有约束）。
- **关注防回归（硬约束）**：`follow-decision` 规定只用平台真实信号、MUST NOT 摆「作品数」项、MUST NOT 以「作品数未知」skip。收紧只能抬「主题强相关 + 至少一个真实质量信号（粉丝/获赞）」的门，**绝不重新引入作品数依赖**，且 130 粉/6707 赞的相关创作者仍应被关注（该 spec 场景必须仍通过）。

## Risks / Trade-offs

- **[内存冷却跨重启清零]** → 云端重启/部署后冷却记录丢失，账号短时间内可连续动作。可接受（重启不频繁；真实发生计时 + 配额层仍兜底）。如需跨重启延续，后续单独加持久化（留模块接口缝）。
- **[冷却 + 四道收紧叠加，互动可能过稀]** → 冷却已是主要数量约束（赞最多 ~30/h、关注 ~6/h、评论 ~2/h）；若粗筛/点赞口径再大幅抬高可能压得过狠。缓解：prompt 收紧以「提质量」为主、措辞避免一刀切；上线后按真机观察再微调措辞（prompt/人设可热改，无需重发）。
- **[关注收紧重犯旧 bug]** → 抬关注门时误把相关健康新人 skip。缓解：D6 硬约束 + `follow-decision` 既有场景作回归断言（130 粉创作者仍关注）。
- **[评论阈值口径]** → 详情页 `likeCount`/`collectCount` 抽取若失真会误判；现状抽取已校准（note.detail 真实计数），阈值用严格大于，边界用单测固定。
- **[“被冷却跳过”被误读为故障]** → 必须如实记可观测原因 `cooldown`（区别于 `no_target`/风控拒），日志为「按冷却跳过」一类中性表述，不报失败、不假成功。

## Migration Plan

- 纯云端逻辑改动，无迁移、无协议、无 edge。部署随 `aidcp-cloud` 常规序列（备份→rsync→restart→healthcheck）。
- 回滚：还原 prompt 与新模块即可；冷却内存态，回滚后自然消失，无残留状态。
- 验证：本地 `npm run test:acceptance`（AC-RISK/PROTO/PUB 全过）→ 全量 `npm test` → `npm run typecheck`；新增冷却闸 + 评论阈值单测必绿。

## Open Questions

- 冷却时长是否最终需要后台可配 / 按账号差异化？本次写死；若运营要调，再单独走 change（模块已留常量集中点）。
- 冷却与 `command-pacing` 的 `tempo` 是否需联动（如 warned 态下冷却也拉长）？本次不联动，保持冷却为固定间隔；后续可评估。
