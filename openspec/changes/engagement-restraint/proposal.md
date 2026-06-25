## Why

自动浏览闭环当前的互动判定几乎全靠 LLM 的宽松判断、没有数值闸，且上游内容粗筛门是故意放宽的（「默认继续看、拿不准就过」）。真机实测一轮下来：点赞近乎逢篇必点、进作者主页逢赞必进、关注/收藏频繁、评论也能发出——按账号的每日安全配额会很快触顶，且互动节奏过密、不拟人、抬高封号风险。需要在不破坏「边轻云重 / 风控终态单写 / 诚实硬失败」红线的前提下，让账号更克制地互动：**提质量（筛选从严）+ 降数量（评论设硬门槛）+ 控节奏（每动作冷却）**。

## What Changes

- **收紧互动筛选标准（更挑剔，全程从严）**：
  - 上游内容粗筛门：从「宽松、默认继续看、拿不准就过」改为「话题强相关且真有信息/观点/经验才继续看，蹭热点/泛泛/擦边/纯情绪一律 close」。
  - 点赞口径：从「低门槛高频、多数都该至少点赞」改为「只在真有共鸣 / 学到具体东西 / 观点眼前一亮时才点」（**BREAKING**：翻转 `interaction-appraisal` 现有「点赞是低门槛高频互动」需求，并同步人设 `like_principle`）。
  - 进主页口径、关注口径：抬高 LLM 判定门槛（关注 MUST 仍只用平台真实信号、绝不碰作品数——`follow-decision` 契约不变）。
- **评论硬阈值**：仅当详情页 `likeCount > 1000` 且 `collectCount > 300`（严格大于）才允许评论；在评估阶段、调 LLM 之前先判定，不满足直接走「不评 → 进主页评估」。现有 LLM 精品判定 + 飞书人审仍叠加在上。
- **新增「每动作冷却」**（云端、内存、按账号、按动作类型）：like 2min / collect 5min / follow 10min / comment 30min。云端下发互动前查冷却闸，未到点则诚实跳过（不下发、不计数、不假成功）；`page.scroll` / `navigation.back` 等推进/返回指令 MUST NOT 受闸拦截；edge 零改动（冷却判定全在云端）。

## Capabilities

### New Capabilities
- `interaction-cooldown`: 云端按账号、按动作类型的最小间隔冷却闸（like/collect/follow/comment 各自冷却时长），在互动下发前查询、未到点诚实抑制、不阻塞推进指令、不写风控终态、为内存态。

### Modified Capabilities
- `interaction-appraisal`: 把「点赞是低门槛高频互动」翻转为「点赞是选择性互动」（并保持 collect 仍更稀有、不比 like 易命中）；新增「互动筛选全程从严」需求（上游粗筛门 + 进主页 + 关注口径更挑剔；关注仍只用平台真实信号）。
- `comment-interaction`: 把「精品门槛」细化为**可确定性判定的硬数值阈值**（`likeCount > 1000` 且 `collectCount > 300`），作为评估阶段必过前置（不达即 `comment.skipped`，不进撰写/人审）。

## Impact

- **代码（仅 `aidcp-cloud`）**：
  - prompt 收紧：`src/agents/content-curator-role.ts`、`src/agents/interaction-appraiser-role.ts`、`src/agents/author-evaluator.ts`、`src/agents/follow-agent.ts`；人设 `src/soul/soul.yaml` 的 `like_principle`。
  - 评论阈值：`src/agents/comment-appraiser.ts` 加确定性数值预闸 + 评论冷却早判。
  - 冷却闸：新增 `src/risk/action-cooldown.ts`（进程内 `Map<accountId, Map<action, lastTs>>`）+ 接入 `src/orchestrator/role-dispatcher.ts` 命令翻译统一闸；`src/server.ts` 装配处注入。
- **协议 / 迁移 / edge：一律不动**（冷却为内存态、判定全在云端，符合边轻云重；不新增 `MessageType`、不碰两份 `protocol.ts` / `command-bridge` / edge 白名单 / `docs/protocol.md`；无新迁移）。
- **风控**：冷却为附加只读闸——MUST NOT 写 `risk_state`、MUST NOT 调 `setQuotaLevel` / `applySignal`；账号风控终态仍仅由 `RiskController` 单写。
- **测试**：新增冷却闸单测（按账号按动作隔离、到点放行/未到点抑制、推进指令不被拦、被抑制=诚实跳过不计数）+ 评论阈值边界（1000/300 严格大于）；回归按 §4 纪律跑 `test:acceptance`（AC-RISK/PROTO/PUB 全过）→ 全量 `test` → `typecheck`。
- **行为副作用（预期目标）**：互动总量显著下降（冷却为主要约束）；整体浏览读得更少（粗筛收紧）；评论变得极稀（双重硬门槛 + 冷却 + 人审）。
