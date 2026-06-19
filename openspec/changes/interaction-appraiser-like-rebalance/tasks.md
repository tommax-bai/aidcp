## 1. 证伪/证实偏置（gating，先做）

- [ ] 1.1 查 cloud 决策日志（`base-role.ts decide()` verdict）：统计 appraiser 被调用次数、like/collect/both/pass 分布与样本量
- [ ] 1.2 结论写入本 tasks 进度：是真偏置（like 明显偏低、样本足够）还是单篇样本噪声——据此定 D1 调参激进度（D2 收藏即点赞独立成立，照常做）

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
