# scripts/ — 并行开发 fleet 助手

配套 `CLAUDE.md §7` 与 `docs/parallel-dev-worktrees.md`。控制仓 aidcp 编排，脚本对
同级 sub-repo（`../aidcp-edge` / `../aidcp-cloud` / `../aidcp-console`）用相对路径操作。

约定：**worktree / 分支 / openspec change 三名合一**，worktree 落 `../<repo>.wt/<name>`。

| 脚本 | 作用 | 安全性 |
| --- | --- | --- |
| `task-preflight` | 任务准入硬门禁：检查本机存在的 canonical checkout 是否都在默认分支 | 只读；失败即阻止任务，不切分支、不修复状态 |
| `fleet-status` | 四仓所有 worktree 一屏:分支 / ahead-behind / dirty / 孤儿标记 | 只读（仅 quiet fetch） |
| `new-change <repo> <name>` | 开一条流：建 `../<repo>.wt/<name>` 分支 `<name>` | 可逆（worktree remove + branch -d） |
| `spawn-change <repo> <name> [--launch]` | 多终端模式：确保 worktree（幂等）+ 生成任务简报；`--launch` 直接在中控仓启动 claude | 同 new-change；`--launch` 只是启动 CLI |
| `land-change <repo> <name> [--yes]` | 集成：fetch+rebase+测试；`--yes` 才 ff 推送+同步主 checkout+清理 | 默认只 prep 不推；push 撞 non-ff 即中止，**绝不 force** |
| `deploy-target <dev\|ol> [--check\|--shell]` | 打印/校验 ECS 目标元数据：host、key、runtime 目录、cloud URL | 只读；`--check` 仅查本机 key 是否存在且权限安全 |
| `release-desktop-macos <version> [--target dev\|ol] [--expect-env ol] [--yes]` | 桌面签名包**出包后交付**编排：下载 CI prerelease 的 dmg → 静态校验（spctl/codesign/stapler/asar/烘焙环境/运行时）→ 改 console `downloads.ts` → 构建 console；`--yes` 才传包+部署 console+验活+提交 | 默认只做本地只读段（下载+校验+改配置+构建）并打印剩余命令；`--yes` 才做 3 个对外动作。构建/签名/公证仍是 CI 专属、脚本不碰。push 撞 non-ff 软失败不 force |

```bash
scripts/fleet-status
scripts/task-preflight
scripts/new-change aidcp-cloud my-change-name
# … 在 ../aidcp-cloud.wt/my-change-name 里开发 …
scripts/land-change aidcp-cloud my-change-name          # 只 prep + 打印命令
scripts/land-change aidcp-cloud my-change-name --yes    # prep 通过后自动集成
scripts/deploy-target dev --check                       # 部署前校验目标 key
scripts/deploy-target ol --check

# 桌面签名包出包后交付（先 CI 出包：gh workflow run build-desktop.yml --ref master -f cloud_default_env=ol）
scripts/release-desktop-macos 0.3.19                    # prep：下载+校验+改配置+构建，打印剩余命令
scripts/release-desktop-macos 0.3.19 --yes              # prep 全绿后传包+部署 console+验活+提交
```

Windows PowerShell must use the `.ps1` wrapper instead of opening the
extensionless Bash script directly:

```powershell
& .\scripts\task-preflight.ps1
```

**红线**：部署只从主 checkout 的 eligible ref 走、绝不从 worktree；部署前必须明确
`dev` 或 `ol` 并跑 `scripts/deploy-target <target> --check`。未指定目标的开发完成部署默认走
`dev`；`ol` 只有用户明确要求线上部署时才走，且必须创建或选定 release 分支并按分支部署。
`land-change` 永不 force-push；`new-change` 不会覆盖已存在的分支/worktree。`new-change` 和
`spawn-change` 会在任何 worktree 操作前执行 `task-preflight`；门禁失败即停止，不能绕过，缺少的
sibling clone 才会跳过。

> 状态：三者均已实战跑通（2026-07-03 dashboard-refresh-clarity 经 new-change 开流、
> land-change --yes 在 cloud+console 两仓完成 rebase→全量绿→ff 推送→清理）。
