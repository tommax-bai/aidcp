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

## 2. 目录布局 `[草案]`

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

## 3. 开一条流 `new-change` `[草案]`

```bash
# repo ∈ {aidcp-edge, aidcp-cloud, aidcp-console}；name = openspec change 名
git -C ../<repo> fetch origin
git -C ../<repo> worktree add ../<repo>.wt/<name> -b <name> origin/master
# 之后：在 ../<repo>.wt/<name> 里启动该 session 的 Claude / 开发
```

控制仓 aidcp 侧无需 worktree：直接在主 checkout 用 openspec 流程建 change 目录
（`/opsx:propose` 等）。

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

## 6. 串行集成 `land-change` `[草案]`

一个一个来，这是整支 fleet 的节流阀：

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

## 7. fleet 状态一屏看 `fleet-status` `[待建]`

目标：一条命令对四仓所有 worktree 输出「分支 / 相对默认分支 ahead-behind / 是否 dirty
/ 对应 openspec change 状态」，让整支 fleet 一屏可见，孤儿 worktree 一眼可查。

参考实现骨架（`[待建]`，落地后改 `[稳]`）：

```bash
for repo in aidcp aidcp-edge aidcp-cloud aidcp-console; do
  d="../$repo"; [ -d "$d/.git" ] || { echo "$repo: NOT CLONED"; continue; }
  git -C "$d" worktree list --porcelain   # 解析 branch + path
  # TODO: 对每个 worktree 补 rev-list --left-right --count、status --porcelain 计数、
  #       与 `openspec list` 对账（worktree 名是否有对应活跃 change）
done
```

## 8. 部署边界（承 CLAUDE.md §5）

- cloud 只跑 ECS `121.89.85.150`，本地永不起 cloud；**只从主 checkout 默认分支部署**，
  绝不从任何 worktree。
- 多流并行期，一次只推一个已集成 + 验证过的 change 上线，别让半合并态堆到 ECS。
- 同机 isales 独立运行，任何 ECS 操作绝不碰它。

## 9. helper 脚本（`[待建]`，验证后提升为 `[稳]`）

计划落 `new-change` / `land-change` / `fleet-status` 三个薄封装（放本仓 `scripts/` 或
用户 shell 函数）。**在跑通 ≥1 轮真实并行开发前，本手册对应块保持 `[草案]` / `[待建]`，
不写入 CLAUDE.md 当法条。**

## 10. 常见故障与兜底

- **push non-ff**：远端有他人先推 → `fetch` + `rebase origin/<默认分支>` 后重推，绝不 force。
- **工作树脏 / 混入非本 change 文件**：多 session 共享工作树的迁移期常态；辨明归属，
  本 change 的提交、他人的留着或 stash，别误删。
- **孤儿 worktree**（无对应活跃 change）：`git worktree remove` + `branch -d` 清掉。
- **worktree remove 报 dirty**：先确认无未提交价值，再 `worktree remove --force`（谨慎）。
