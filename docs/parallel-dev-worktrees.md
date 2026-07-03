# 并行开发操作手册（多 Claude session / git worktree）

> 配套 `CLAUDE.md §7`。**§7 的不变量是 OVERRIDE 法条；本手册的命令序列 / 脚本为
> 操作细节，经实战跑通验证后方视为定稿**（下方每块标注状态）。未验证前，只把 §7
> 不变量当铁律，本手册命令按需人工确认。
>
> **状态图例**：`[稳]` 已实战验证 · `[草案]` 待跑通验证 · `[待建]` 脚本尚未落地。
>
> 仓库默认分支：本仓 `aidcp` = `main`；`aidcp-edge` / `aidcp-cloud` / `aidcp-console`
> = `master`。三 sub-repo 为同级目录（`../aidcp-edge` 等），可能未在本机 clone
> （先 `ls -d` 确认，见 CLAUDE.md §0）。

## 1. 心智模型：worktree 解决一半，集成串行是另一半

- worktree 给的是**开发期隔离**：N 个 session 各一个目录 + 各一条分支，互不污染工作区；
  目录名 = 分支名 = change 名，人在哪个目录就在改哪个 change，忘不掉。
- worktree **不消灭合并冲突**：文件重叠不可预测时，冲突从「开发时」挪到「集成时」。
  因此 **开发并行、集成串行**——合回默认分支一个一个来。
- **真正的瓶颈是评审 / 集成带宽，不是 git。** 5–8 个 agent = 5–8 份 diff 要 verify，
  这里是天然的序列化点，按此排期。

### 何时开 worktree、何时不开

| 场景 | 做法 |
| --- | --- |
| 控制仓 aidcp 的 change（propose / spec / tasks） | **不开 worktree**。change 是 additive 目录、近零冲突，主 checkout 各写各的 change 目录即可 |
| 两个 change 改的**文件不重叠** | 不开 worktree，串行提交到默认分支，commit 前缀带 change 名 |
| 两个 change 改的**文件重叠、且要同时推进**（尤其一条流交给 Claude、一条你自己写） | 每 change 一个 worktree 隔离 |
| 任务要动**热点文件**（见 §5） | **不并行**，单写者串行做 |

### 每仓并发软上限（避免全挤一个子系统）

- 控制仓 aidcp：不限（additive）。
- aidcp-cloud：并发 ≤ 2–3，且分散到不同子系统（publish / risk / config 别都挤 config/）。
- aidcp-edge：并发 ≤ 2。
- aidcp-console：并发 ≤ 2。

### 用手动 `git worktree add`，不用内置 EnterWorktree/ExitWorktree

本项目一律用**手动 `git worktree add` 到目标子仓**（`scripts/new-change` 封装），**不要**用 Claude Code 内置的 `EnterWorktree`/`ExitWorktree`。原因是内置工具只适配「单仓隔离分支」，不合本项目「中控仓驱动、代码落子仓」的多仓模型（已对照工具接口核实）：

- **只能操作当前仓**：内置 worktree 建在当前仓 `.claude/worktrees/`，`path` 进已有 worktree 也要求它属于当前仓。session 锚在中控仓 aidcp，就**开不出 / 进不了 aidcp-cloud 等子仓的 worktree**——而要隔离的正是子仓。
- **会切走 session cwd**：而本项目要 cwd 锚在中控仓（`openspec/` + `tasks.md` 在这），代码落子仓、来回走；切走反而别扭。
- **生命周期纳管不覆盖手动 worktree**：`ExitWorktree` 明确只管 `EnterWorktree` 建的，不碰 `git worktree add` 的——多仓场景连它的 keep/remove 便利都吃不到。

单仓（非本项目多仓编排）做隔离分支时，内置工具是好默认；本项目用手动。

## 2. 目录布局 `[稳]`

worktree 放到各仓的兄弟目录 `<repo>.wt/<change-name>`，保持主 checkout 干净、作为
集成与部署位：

```
../aidcp-cloud                       # 主 checkout = 集成 + 部署位（只从这里 rsync 上 ECS）
../aidcp-cloud.wt/<change-a>         # fleet 成员 A（只开发 + 提交，绝不部署）
../aidcp-cloud.wt/<change-b>         # fleet 成员 B
../aidcp-edge.wt/<change-c>
../aidcp-console.wt/<change-d>
```

**铁律**：worktree / 分支 / openspec change **三名合一**。这样 `openspec list` 与
`git worktree list` 永远 1:1 对得上——有 worktree 却无对应活跃 change = 孤儿、清掉。

## 3. 开一条流 `new-change` `[稳]`

```bash
scripts/new-change <aidcp-edge|aidcp-cloud|aidcp-console> <change-name>
# 等价于：fetch origin + git worktree add ../<repo>.wt/<name> -b <name> origin/<默认分支>
# 会拒绝覆盖已存在的分支/worktree；change 名不在控制仓时 WARN 提示（不阻断）
# 之后：cd ../<repo>.wt/<name> 里启动该 session 的开发
```

控制仓 aidcp 侧无需 worktree：直接在主 checkout 用 openspec 流程建 change 目录
（`/opsx:propose` 等）。

## 3b. 多终端模式（形态 A：每终端一条流）`[稳]`

用户自己开 N 个 claude CLI 终端并行开发时，每终端一条命令进车道：

```bash
cd ~/codes/aidcp && scripts/spawn-change <repo> <change-name> --launch
# = 确保隔离 worktree 存在（幂等，缺则创建）→ 生成任务简报 → 在中控仓启动 claude
#   （中控仓启动 = 自动读到 CLAUDE.md §7）；不带 --launch 只打印简报，可粘给任意 session
```

- session 拿到简报即自知身份（独占哪个 change、代码只写哪个 worktree、怎么集成），
  无需逐个口头交代。全新任务先在任一 session `/opsx:propose` 再 spawn。
- **用户在 fleet 层只管三件事**：① 挑互不重叠的任务（按子系统摊开，见并发软上限）；
  ② 碰热点文件（§5）的任务不同时派两个；③ 部署天然串行（部署前必探 ECS，见 §8）。
- 集成撞车由机制兜底：`land-change` ff-only + rebase 重试，绝不 force；中控仓 tasks.md
  各 change 各一份、互不冲突。
- 资源提醒：多条流同时跑全量测试很吃 CPU，集成（land-change 全量套件）尽量错峰；
  多 session 共享模型/API 限额。

## 4. 在 worktree 里干活的规矩

- 只在**本分支**提交；commit message 前缀带 change 名（如 `<name>: …`），末尾带
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- **在自己 worktree 里跑** `npm test` / `npm run typecheck`（sub-repo 内执行）。
- **绝不从 worktree 部署**（部署只从主 checkout 默认分支，见 §6 与 CLAUDE.md §5）。
- 勤 `git fetch && git rebase origin/master`，让冲突小而早暴露。
- 碰到**热点文件**（§5）先停手、标记为需串行。

## 5. 热点文件单写者清单（并行时绝不同时碰）

- 两份 `protocol.ts`（edge + cloud，须逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts`
  的动作↔消息映射（协议四处同步，CLAUDE.md §2）。
- 角色注册：`event-bus/types.ts` 的 `RoleName` 穷举 + `src/config/role-catalog.ts`。
- 风控状态机 `src/risk/risk-state-machine.ts`。
- 边缘主动命令路由白名单 `aidcp-edge/src/client/edge-client.ts` 的 onMessage（新增
  cloud→edge 主动命令时）。

任一任务需动上述文件 → 该 change 串行做，同一时刻只有一个 session 在碰。

## 6. 串行集成 `land-change` `[稳]`

一个一个来，这是整支 fleet 的节流阀。脚本封装：

```bash
scripts/land-change <repo> <name>          # 只做 prep：fetch+rebase+测试，然后停下打印命令
scripts/land-change <repo> <name> --yes    # prep 通过后自动 ff 推送+同步主 checkout+清理
```

`--yes` 用 `git push origin <name>:<默认分支>` 走 ff 推送（不切主 checkout 分支、
不碰其工作区），撞 non-ff 立即中止、**绝不 force**。下面是 `--yes` 自动化的等价手动步骤
（`--yes` 全流程已于 2026-07-03 随 dashboard-refresh-clarity 在 cloud+console 两仓实战跑通：rebase 到已前进的 master、全量绿、ff 推送、清理）：

```bash
# 1) 把本流 rebase 到最新默认分支，解冲突
git -C ../<repo> fetch origin
git -C ../<repo>.wt/<name> rebase origin/master        # 解冲突

# 2) 在 worktree 里跑安全红线 + 全量
cd ../<repo>.wt/<name> && npm run test:acceptance && npm test && npm run typecheck

# 3) ff 合并回默认分支 + push（撞 non-ff 就回到步 1 重来，绝不 force）
git -C ../<repo> checkout master
git -C ../<repo> merge --ff-only <name>
git -C ../<repo> push origin master

# 4) 按需部署（只从主 checkout，严格走 CLAUDE.md §5 安全序列）

# 5) 收口：archive openspec change → 删 worktree/分支
git -C ../<repo> worktree remove ../<repo>.wt/<name>
git -C ../<repo> branch -d <name>
```

- **push 遇 non-ff**：一律 rebase 后重来，**绝不 force**；空 diff = 已在远端、可弃
  （见 memory `concurrent-session-shares-subrepo-worktree`）。
- 集成顺序：先落**不碰热点、改动小**的流，热点流留到最后单独处理。

## 7. fleet 状态一屏看 `fleet-status` `[稳]`

一条命令对四仓所有 worktree 输出「分支 / 相对默认分支 ahead-behind / dirty 计数 /
是否孤儿」，整支 fleet 一屏可见，孤儿 worktree（无对应活跃 change）一眼可查。只读
（仅 quiet fetch）。

```bash
scripts/fleet-status
# 每个 worktree 一行：路径 · branch · ahead/behind(vs origin/<默认分支>) · dirty 数 · 标签
#   标签：(main checkout · 集成+部署位) / change:active / !! ORPHAN(该清)
```

## 8. 部署边界（承 CLAUDE.md §5）

- cloud 只跑 ECS `121.89.85.150`，本地永不起 cloud；**只从主 checkout 默认分支部署**，
  绝不从任何 worktree。
- 多流并行期，一次只推一个已集成 + 验证过的 change 上线，别让半合并态堆到 ECS。
- 同机 isales 独立运行，任何 ECS 操作绝不碰它。

## 9. helper 脚本

三个薄封装已落 `scripts/`（共享 `scripts/lib.sh`），见 `scripts/README.md`：

- `scripts/new-change <repo> <name>` — `[稳]`（pilot 跑通：建 worktree/分支、拒绝覆盖、change 缺失 WARN）
- `scripts/fleet-status` — `[稳]`（pilot 跑通：四仓扫描 + ahead/behind + dirty + 孤儿标记，只读）
- `scripts/land-change <repo> <name> [--yes]` — `[稳]`（2026-07-03 随 dashboard-refresh-clarity
  在 cloud+console 两仓实战跑通全流程；test:acceptance 仅在该仓定义时跑）

**红线**：`land-change` 永不 force-push；`new-change` 不覆盖已存在分支/worktree；
部署只从主 checkout（§8）。

## 10. 常见故障与兜底

- **push non-ff**：远端有他人先推 → `fetch` + `rebase origin/<默认分支>` 后重推，绝不 force。
- **工作树脏 / 混入非本 change 文件**：多 session 共享工作树的迁移期常态；辨明归属，
  本 change 的提交、他人的留着或 stash，别误删。
- **孤儿 worktree**（无对应活跃 change）：`git worktree remove` + `branch -d` 清掉。
- **worktree remove 报 dirty**：先确认无未提交价值，再 `worktree remove --force`（谨慎）。
