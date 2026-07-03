# scripts/ — 并行开发 fleet 助手

配套 `CLAUDE.md §7` 与 `docs/parallel-dev-worktrees.md`。控制仓 aidcp 编排，脚本对
同级 sub-repo（`../aidcp-edge` / `../aidcp-cloud` / `../aidcp-console`）用相对路径操作。

约定：**worktree / 分支 / openspec change 三名合一**，worktree 落 `../<repo>.wt/<name>`。

| 脚本 | 作用 | 安全性 |
| --- | --- | --- |
| `fleet-status` | 四仓所有 worktree 一屏:分支 / ahead-behind / dirty / 孤儿标记 | 只读（仅 quiet fetch） |
| `new-change <repo> <name>` | 开一条流：建 `../<repo>.wt/<name>` 分支 `<name>` | 可逆（worktree remove + branch -d） |
| `land-change <repo> <name> [--yes]` | 集成：fetch+rebase+测试；`--yes` 才 ff 推送+同步主 checkout+清理 | 默认只 prep 不推；push 撞 non-ff 即中止，**绝不 force** |

```bash
scripts/fleet-status
scripts/new-change aidcp-cloud my-change-name
# … 在 ../aidcp-cloud.wt/my-change-name 里开发 …
scripts/land-change aidcp-cloud my-change-name          # 只 prep + 打印命令
scripts/land-change aidcp-cloud my-change-name --yes    # prep 通过后自动集成
```

**红线**：部署只从主 checkout 默认分支走、绝不从 worktree（CLAUDE.md §5/§7）；
`land-change` 永不 force-push；`new-change` 不会覆盖已存在的分支/worktree。

> 状态：三者均已实战跑通（2026-07-03 dashboard-refresh-clarity 经 new-change 开流、
> land-change --yes 在 cloud+console 两仓完成 rebase→全量绿→ff 推送→清理）。
