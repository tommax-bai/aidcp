## Context

互动决策是事件驱动浏览闭环的一环：`reading.done`（由 `comment-reviewer.ts` 发出，互动阶段唯一入口）→ `InteractionAppraiserRole.onReadingDone` 一次 LLM 调用出 `{like|collect|both|pass}` → `parseOutput` 按配额映射成 `actions[]` → `interaction.completed{actions}` → `role-dispatcher` 逐个 `sendCommand` → bridge `like→interaction.like` / `collect→interaction.collect` → edge `executeLikeOrCollect`（like/collect 共用，仅 wrapper 选择器不同，后置校验 SVG href 翻转、如实报 ok）。

经核实：链路全通、like 非死代码（`like-command.ts` 是 v1 遗留、不在现役路径）。零点赞的唯一成因是 appraiser 那次 LLM 选了 collect/pass。两个真实缺口：
- `buildPrompt`（:132-136）：collect 条件具体易命中且标「更稀有更谨慎」，like 条件含糊门槛更高 → LLM 偏 collect。
- `soul.yaml:30` `style:收藏比点赞更稀有`（意图：like 应更频繁）**未注入** prompt；注入的 `like_principle`（:123「有实际共鸣」）反把 like 写成高门槛。
- `parseOutput`（:170-179）：collect 只映射 collect，无「收藏即点赞」兜底。

**关键不确定性**：该场仅 1 篇笔记真正互动，「零点赞」可能是样本噪声而非系统性压制。`base-role.ts decide()`（:63）已记原始 verdict。

## Goals / Non-Goals

**Goals:**
- 先**证伪/证实**偏置：从既有决策日志看 appraiser 动作分布与样本量，再定改动力度。
- 让 like 成为低门槛高频互动、collect 成为稀有选择性互动（与 budget likes:10 > collects:5 及 soul 意图一致）。
- 确定性兜底：收藏时在 like 配额允许下**同时点赞**，根除「collect 触发但 like 从不出现」。
- 改动后能用日志验证 like/collect 比例真的改善。

**Non-Goals:**
- 不改 like 的接线/执行（edge 已完整）、不动协议。
- 不引入 like/view 比例风控门（`risk.canDo/record` 为保留通道、未接线；CLAUDE.md）。若将来接线，收藏即点赞须先咨询该门。
- 不改 collect 既有行为本身（仍可独立 collect）。

## Decisions

### D0：先用日志证伪，再决定改动力度（gating）
第一步统计既有 `decide()` verdict 日志：appraiser 被调用次数、like/collect/both/pass 分布。
- 若样本足够且 like 明显偏低 → 执行 D1+D2+D3 全量。
- 若样本太小（如本场仅 1 篇）→ D2（收藏即点赞）与 D1（prompt 重平衡）仍**独立成立**（与人类行为一致），但按低优先推进，不做激进调参。
- **为何**：避免据单篇样本过度调参；`decide()` 已有日志，零成本可证。

### D1：prompt 决策逻辑重平衡（like 低门槛、collect 稀有）
改 `buildPrompt` 的「决策逻辑」块：like = 「有共鸣/学到东西/认同观点 → 点赞（常见的轻互动）」；collect = 「会反复查看、需落地复用才收藏（稀有）」；显式提示「值得收藏的内容几乎也值得点赞 → 优先 both」。
- **为何**：根因是 collect 条件易命中、like 门槛高且含糊。反过来框定即纠偏，且匹配 soul `style` 意图。
- **备选（否决）**：只调 confidence 阈值——治标不治本，LLM 仍按错误框架选 collect。

### D2：parseOutput「收藏即点赞」确定性兜底
`parseOutput` 中 `action==='collect'` 分支：若 `budget.likes>0`，`actions` 同时 push `like` 与 `collect`（受各自配额约束）。`both`/`like`/`pass` 行为不变。
- **为何**：真人收藏几乎都先点赞；这是不依赖 prompt 调参就能保证 like 至少随 collect 出现的确定性兜底，直接闭合观察到的缺口。
- **边界**：严格受 like 配额约束（`budget.likes>0` 才补），不绕过预算；like 配额耗尽时仅 collect。
- **备选（保留为可选）**：把 collect 视作隐式 both 除非模型显式 opt-out——与 D2 等价但更隐晦，采用显式 budget-gated push。

### D3：soul 文案对齐
`like_principle` 降为轻量高频门槛（如「只要有共鸣/认同/有用就点赞，点赞是轻量高频的」）；`collection_principle` 保持选择性。
- **为何**：注入 prompt 的恰是这两条；现状 `like_principle` 抬高了 like 门槛。
- **注**：`style`「收藏比点赞更稀有」当前不注入；本次不改注入集合（避免扩大面），靠 D1/D3 在已注入的两条里体现该意图。

### D4：观测复用既有日志
不新增日志；`base-role.ts decide()`（:63）已记 verdict。验收时断言能从日志读到 appraiser 的 action/reason，用于改动前后对比。
- **为何**：避免冗余日志；验证 D1/D2 真的改善 like/collect 比例。

## Risks / Trade-offs

- [据单篇样本过度调参] → D0 先证伪；D1/D3 为温和重框定、D2 为确定性兜底，均不依赖「确认大规模偏置」也成立。
- [收藏即点赞导致 like 过量/不自然] → 受 like 配额（freshBudget likes:10）硬约束；真人收藏即点赞本就常见；可按 D0 日志观察比例，必要时回退 D2 为「prompt 倾向 both」软策略。
- [LLM 行为不可确定性] → D2 是确定性代码兜底，不靠模型自觉；D1/D3 的效果用 D4 日志前后对比验证，不靠主观。
- [配额绕过红线] → D2 严格 `budget.likes>0` 门控，like 配额耗尽不补；acceptance 钉「like 配额为 0 时收藏不补点赞」。
- [部署 soul 与仓库不一致] → 上线前确认 ECS 实际 soul 的 `like_principle`/`interests` 与仓库一致（否则改了仓库不生效）。

## Migration Plan

1. D0：拉取/查看 cloud 决策日志，统计 appraiser 动作分布，结论写 tasks 进度（gating）。
2. D1+D3：改 `interaction-appraiser-role.ts buildPrompt` 与 `soul.yaml`；`npm run typecheck`。
3. D2：改 `parseOutput`（收藏即点赞，budget-gated）。
4. 回归：cloud `npm run test:acceptance` → `npm test`（含 appraiser 用例 + 配额门控）。
5. 部署：cloud 按 §5 安全序列上 ECS；上线后用 D4 日志对比 like/collect 比例。回滚：还原文案与 parseOutput 即可，无数据迁移。

## Open Questions

- D0 结论：本会话是 1 篇样本还是多篇？多篇里 like 真的为 0 吗？决定 D1 调参激进程度。
- 是否需要 like/view 比例风控门（当前 `risk.canDo/record` 未接线）？若将来接线，D2 须先咨询。
- ECS 实际 soul 是否与仓库一致？
