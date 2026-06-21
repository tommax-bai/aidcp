## Why

实测一场浏览全程零点赞（collect/follow/scroll 都正常）。经端到端核实：**like 链路完整接线、与 collect 完全对称、并非坏掉/遗留/保留通道**——既然 collect 成功执行，就证明决策点跑到了、LLM 跑了、配额够、bridge/edge 全通。like 与 collect 唯一的分叉点是 `InteractionAppraiserRole` 那**一次 LLM 决策**返回了 `collect`/`pass` 而非 `like`/`both`。

两个真实的设计缺口（经代码核实）：
1. **prompt 决策逻辑偏置 collect**：`buildPrompt`（`interaction-appraiser-role.ts:132-136`）把 collect 写成有具体可命中条件「有实操步骤、代码/配置、架构图…（更稀有更谨慎）」，like 却写成含糊的「有启发但不需反复参考」。对工程兴趣的人格，技术笔记天然命中 collect，like 反而门槛更高——与「点赞应高频、收藏应稀有」相反。
2. **soul 的真实意图没进 prompt**：`soul.yaml:30` `style: 收藏比点赞更稀有`（即点赞应**比收藏更频繁**）从未注入 prompt——`buildPrompt` 只注入 `collection_principle`/`like_principle`（:122-123），而注入的 `like_principle`「有实际共鸣」又把点赞写成更高的门槛，进一步压低 like。

重要不确定性（须先证伪再大改）：「系统性压制 like」目前是**推断而非证据**。该场实际只有**一篇笔记真正触发了互动**（且选了 collect），「零点赞」很可能是**单篇样本噪声**。`base-role.ts decide()`（:63）已记录每次 LLM 原始 verdict——本 change **第一步**就是从决策日志确认到底有几篇走到 `reading.done`、各自选了什么，再决定改动力度。

## What Changes

- **cloud（调查，gating）**：从既有 LLM 决策日志统计 appraiser 各动作（like/collect/both/pass）分布与样本量，确认是否真偏置（而非样本太小）。结论写入 tasks 进度。
- **cloud（prompt 重平衡）**：改 `buildPrompt` 决策逻辑——把 **like 写成低门槛、常见的轻互动**（有共鸣/学到东西/认同观点即可），**collect 写成稀有、选择性**的「会反复查看才收藏」；并提示「值得收藏的内容几乎也值得点赞 → 倾向 both」。
- **cloud（确定性兜底：收藏即点赞）**：`parseOutput`（:170-179）当 LLM 选 `collect` 且 `budget.likes>0` 时，**同时补 `like`**（真人收藏几乎都先点赞），受 like 配额约束。直接堵住「collect 触发了但 like 从不出现」。
- **cloud（soul 文案）**：把 `like_principle` 降为轻量高频门槛、`collection_principle` 保持选择性，使注入 prompt 的两条标准与 `style` 意图一致。
- **观测**：复用 `base-role.ts decide()` 既有 verdict 日志（无需新增日志），仅在验收时断言能从日志读到 appraiser 的 action/reason。

## Capabilities

### New Capabilities
- `interaction-appraisal`: 点赞/收藏的评估与下发——点赞为低门槛高频互动、收藏为稀有选择性互动；收藏即点赞（收藏时在配额允许下同时点赞）；决策动作可观测且受配额约束。

### Modified Capabilities
<!-- 无修改既有 spec -->

## Impact

- **cloud（aidcp-cloud）**：`src/agents/interaction-appraiser-role.ts`（`buildPrompt` 决策逻辑、`parseOutput` 收藏即点赞）；`src/soul/soul.yaml`（`like_principle`/`collection_principle` 文案）。
- **观测**：`src/agents/base-role.ts decide()` 既有 verdict 日志（仅读取/断言，不改）。
- **edge**：无改动（like 执行已完整：`browse-session.ts:448-460` / `executeLikeOrCollect`）。
- **协议 / docs**：无改动。
- **风险面**：纯云端决策/文案改动；「收藏即点赞」须受 like 配额约束、不得绕过；不改 edge 执行与红线（`executeLikeOrCollect` 仍后置校验 SVG href 翻转、如实报 ok）。LLM 行为类改动须以日志验证实际生效（A/B 或前后对比）。
