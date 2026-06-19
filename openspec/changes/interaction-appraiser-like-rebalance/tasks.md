## 1. 证伪/证实偏置（gating，先做）

- [x] 1.1 查 cloud 决策日志（`base-role.ts decide()` verdict）：统计 appraiser 被调用次数、like/collect/both/pass 分布与样本量 <!-- ECS journalctl 2026-06-19 查询（窗口 2700 行，至 2026-06-18T22:50:54）：40 次 appraiser 决策 → collect 22 / like 10 / pass 8 / both 0；实际执行 collect 22 / like 9 / follow 13 -->
- [x] 1.2 结论写入本 tasks 进度：**确认是真偏置，非样本噪声**。40 样本下 collect(22) ≈ 2.2× like(10)，且 both 从未被选(0/40)——与 soul `style:收藏比点赞更稀有`（like 应 > collect）**相反**。like 链路正常（9 次真实点赞），原会话「零点赞」只是单会话小样本切片。→ D1（prompt 重平衡）+ D2（收藏即点赞，根治 both=0）+ D3（soul 文案）全量推进 <!-- 2026-06-19 gating done -->

## 2. aidcp-cloud — prompt 重平衡与确定性兜底

- [ ] 2.1 `src/agents/interaction-appraiser-role.ts buildPrompt`（:132-136）：重写决策逻辑——like 写成低门槛/常见轻互动，collect 写成稀有/选择性，提示「值得收藏几乎也值得点赞 → 倾向 both」（D1）
- [ ] 2.2 `src/agents/interaction-appraiser-role.ts parseOutput`（:170-179）：`action==='collect'` 且 `budget.likes>0` 时 actions 同时 push `like` 与 `collect`；`budget.likes===0` 仅 collect（收藏即点赞、受配额约束）（D2）
- [ ] 2.3 `src/soul/soul.yaml`：`like_principle` 改为轻量高频门槛、`collection_principle` 保持选择性，与 D1 框定一致（D3）
- [ ] 2.4 确认 `like`/`both`/`pass` 既有映射与 edge 执行（`executeLikeOrCollect` 后置校验）未被改动

## 3. 验证与归档

- [ ] 3.1 cloud 单测：collect+like 配额>0 → actions=[like,collect]；collect+like 配额=0 → [collect]；pass → []；prompt 含重平衡框定；`npm run test:acceptance` → `npm test` → `npm run typecheck`
- [ ] 3.2 上线后用 `decide()` 日志对比改动前后 like/collect 比例，确认 D1/D2 实际生效（LLM 行为类改动须日志佐证）
- [ ] 3.3 部署前确认 ECS 实际 soul 的 `like_principle`/`interests` 与仓库一致（否则改了不生效）
- [ ] 3.4 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 3.5 `openspec validate interaction-appraiser-like-rebalance --strict` 通过
- [ ] 3.6 cloud 改动按 §5 安全序列部署 ECS（含 healthcheck/回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 3.7 `/opsx:archive` 归档（新建 `openspec/specs/interaction-appraisal`）
