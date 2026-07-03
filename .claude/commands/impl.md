---
description: 实装一个 openspec change(并行 fleet 全流程:worktree→开发→集成→回写→归档)
---

你被指派实装 openspec change「$ARGUMENTS」。你是并行 fleet 中独占本 change 的 session,按 CLAUDE.md §7 自主走全流程、无需逐步征询:

1. **定位任务**:读 `openspec/changes/$ARGUMENTS/` 下的 proposal.md / design.md(若有)/ tasks.md,判断涉及哪些子仓(可多仓)与待做 task;再读 `docs/parallel-dev-worktrees.md` §4。若该 change 目录不存在,停下向用户确认名字(勿猜)。
2. **开隔离车道**:对每个涉及代码的子仓跑 `scripts/new-change <repo> $ARGUMENTS`(worktree 已存在且分支同名则直接复用 `../<repo>.wt/$ARGUMENTS`)。**代码只改 worktree,绝不动子仓主 checkout**。控制仓改动(tasks.md 等)在主 checkout 直接做。
3. **热点红线**(CLAUDE.md §7):两份 protocol.ts、command-bridge.ts 动作映射、event-bus/types.ts 的 RoleName 穷举 + role-catalog 注册、risk-state-machine.ts、edge-client.ts onMessage 白名单——需要动就**停手上报**,不并行。
4. **质量闸**:在 worktree 内跑 test(有 test:acceptance 先跑)+ typecheck,全绿才算完;提交到本分支,message 前缀「$ARGUMENTS: 」,绝不静默假成功。
5. **串行集成**:`scripts/land-change <repo> $ARGUMENTS --yes`(fetch+rebase→全量绿→ff 推送→自动清理 worktree;撞 non-ff 重跑,绝不 force)。多仓时逐仓 land;接口形状有联动的仓必须同批。
6. **收口**:回写 `openspec/changes/$ARGUMENTS/tasks.md`(commit sha + 偏离说明);真机验收类项登记 `docs/real-machine-acceptance-backlog.md` 对应簇(归档与真机解耦);如需部署,先探 ECS 现状(近 1h 文件 mtime + md5 对 master,防撞并发部署)再走 §5 安全序列;代码完成+部署后 `openspec archive $ARGUMENTS -y`,控制仓提交推送。
7. 结束时按 CLAUDE.md §6 给一段「说人话」总结。
