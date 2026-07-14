# 交接文档 — lease-strict-preemption 第 4 节（取消点补齐）

> 写给下一个接手的 session。**读完这份 + `tasks.md` 就能开工，不必回读之前的对话。**
> 行号均已在分支 `lease-strict-preemption` 的 **`bd9ffc0`** 上实测核对（取证快照里的行号已漂移，以此为准）。

---

## 0. 你在哪、代码在哪

| 项 | 值 |
| --- | --- |
| 控制仓 | `/Users/baitianxing/codes/aidcp`，分支 `main`（台账 `20b4ed7`） |
| edge worktree | `/Users/baitianxing/codes/aidcp-edge.wt/lease-strict-preemption` |
| edge 分支 | `lease-strict-preemption`，已推 origin，**未合 master** |
| 已落提交 | `0ae90c8`（第 1 节）→ `c8e3202`（第 2 节）→ `bd9ffc0`（第 3 节） |
| 当前门禁 | typecheck 通过 / `test:acceptance` 19/19 / 全量 **1317/1317** |

**红线约束（本 change 全程有效）**：

- `aidcp-edge/src/main.ts` 的 **FB 租约闸节奏豁免段**用户并行占用中，**不碰**。main.ts 其余改动（第 5.3 / 8.1）先与用户协调。第 3 节我只在 main.ts 的两个会话注册处加了 `catch`（`:1069` / `:1133` 附近），没进那一段。
- 第 6 节要动**两份 `protocol.ts`**（热点文件）→ 不与他人并行。第 4 节**不需要动协议**。

---

## 1. 第 4 节要解决的问题（一句话）

**抢占的「等停」预算现在是空的。**

第 1–3 节把「纯等待」段做成了安全取消点（当场让路）、把让位探针做诚实了、把清场做出来了。但**真正在写页面的那一段仍然完全不可取消**——它只会自然跑完。于是「有界等停」这个数字就是纸面上的：

- 逐字输入一篇长正文，中途没有任何取消检查（除了 FB 发布一处）。
- 六个手写的轮询循环只认自己的死线，不认外部取消信号。
- 🔴 **云端选元素是一个 600 秒的黑洞**：单次等待上限 200 秒（`src/client/cloud-selector.ts:31` `SELECT_TIMEOUT_MS = 200_000`）× 定位引擎默认最多 3 轮（`src/locating/engine.ts:90` `maxAttempts ?? 3`）＝ **结构上界 600 秒，全程无取消点**。发布路径今天还吃的是这个默认值。

**不补第 4 节的后果**：第 5.5 的「等停到期 → 判控制面故障 → 整队回收」会天天触发——验证码人工协助会变成常态性拿不到锁。也就是说，**第 4 节不做完，第 5 节做出来是负收益**（把「偶尔死锁」换成「天天误判浏览器坏了」）。

---

## 2. 现成可复用的原语（第 1–2 节已经建好，别重新发明）

在 `src/browse/browse-session.ts`：

- `export class TaskTakeoverError`（`:317`）——命令在安全取消点被接管，**零页面副作用作废**。
- `export class BrowseQuiesceTimeoutError`（`:328`）——交接未在预算内收敛，**诚实抛出**。
- `export const DEFAULT_TASK_QUIESCE_MS`（`:339`，env `AIDCP_TASK_QUIESCE_MS`，默认 30s）。
- `sleepInterruptible(ms)`（`:617`）+ `wakeInterruptibleSleeps()`（`:647`）——可打断 sleep。
- `takeoverRequested()` / `throwIfTakeover()`（`:637` / `:642`）——**判据是「接管世代号」**。

在 `src/facebook/facebook-session.ts`（第 2 节新建，同形）：

- `activePageWriters`（在飞页面写者计数，**只在执行体真正 settle 时才减**）、`orphanWriters`（超时放行串行链后仍在写页面的孤儿）、`trackWriter()`、以及同样的 `sleepInterruptible` / `throwIfTakeover`。

在 `src/browse/cdp-util.ts`：

- `dispatchKeystrokes(cdp, text, { deadlineAt, clock, sleep, random })`（`:277`）+ `InputDispatchDeadlineError`（`:122`）+ 内部 `assertInputDeadline`。**它今天只认死线，不认取消信号**——这正是 4.1 要改的。

### ⚠️ 两个已经踩过的坑，别再踩

1. **取消令牌绝不能用「浏览已冻结」这类布尔标志。** 交接一开始就置冻结、只在恢复时才清，而**独占任务自己的命令就跑在冻结期内**。用标志当令牌，评论 / 巡视的每条命令要么当场自尽、要么跳过阻断浮层闸对着验证码墙点击。**只能用世代号**（交接时 +1，命令入口拍一份，两者不等 = 被接管）。第 1 节有一条专门的回归断言焊住这一点。
2. **让路时抛出，不要 return。** `return` 会让命令继续往下执行（对着验证码墙点击）。必须抛 `TaskTakeoverError`，由命令主循环捕获 → 诚实回执 → 不重放。

---

## 3. 逐项任务（tasks.md 第 4 节的展开）

### 4.1 逐字输入：守卫从「只认死线」扩成「死线 or 取消信号」

`dispatchKeystrokes` 的守卫（`cdp-util.ts:277-292`）目前只在 `deadlineAt` 到期时抛 `InputDispatchDeadlineError`。要加一个可选的取消回调（形如 `shouldCancel?: () => boolean`），命中即抛**可区分**的被抢占异常（复用 `TaskTakeoverError` 或新建同族类型）。

**语义必须保持**：只在下一个字符尚未发出时检查，**绝不取消已经发出的 CDP 命令**；已输入的部分留在编辑器里，由调用方负责**清场**（第 3 节已经把清场建好了，直接调用）。

**五个调用点，今天只有一个有守卫**（已实测）：

| 调用点 | 现状 |
| --- | --- |
| `src/facebook/publish-executor.ts:433` | ✅ **唯一**传了 `deadlineAt` 的 |
| `src/facebook/comment-executor.ts:483` | ❌ 裸跑（正文） |
| `src/facebook/comment-executor.ts:494` | ❌ 裸跑（联系方式整段） |
| `src/browse/search-handler.ts:586` | ❌ 裸跑（搜索词） |
| `src/browse/browse-session.ts:2448` | ❌ 裸跑（XHS 评论正文） |

**第六处（取证没点出来，我核代码时发现的）**：XHS 发布的 `typeHumanized`（`src/flows/publish-command-handlers.ts:547` 附近）**根本不走 `dispatchKeystrokes`**，它有自己的分块 `insertText` 循环 + `this.sleep`。它同样必须接取消信号，别只改 `dispatchKeystrokes` 就以为覆盖全了。

### 4.2 抽一个「有界 + 可取消」的轮询原语，替换 6 个手写循环

全在 `src/flows/publish-command-handlers.ts`（当前行号）：`:363`、`:509`、`:700`、`:848`、`:902`、`:919`。它们都是 `for (;;) { …evaluate…; if (clock() >= deadline) …; await new Promise(r => setTimeout(r, N)); }`。

注意 memory `edge-poll-helpers-iteration-bounded` 的教训：**按迭代次数限界，别只靠墙钟**——注入的 sleep 桩可能立即 resolve，恒定 now 会把循环变成死循环。第 2 节的 `waitDrained` 里我用的是「墙钟 + 最大迭代次数」双保险，照抄那个形状。

### 4.3 🔴 云端选元素的 600 秒黑洞（本节最重要的一条）

- 上限来源：`src/client/cloud-selector.ts:31`（200s，注释说明它必须 > 云端单次模型调用天花板 180s）× `src/locating/engine.ts:90`（默认 3 轮）。
- 要做两件事：
  1. `CloudElementSelector.select()` 接受取消信号，**抢占时就地作废在飞请求**（不要傻等 `client.request` 的计时器）。定位引擎已有「升级上报（escalated）」分支，作废走那条路**不会假成功**。
  2. **发布路径显式传入引擎参数，不再吃 `maxAttempts ?? 3` 的默认值**——今天发布是靠默认值撞上 600s 的。

### 4.4 图片上传：下载段可取消，塞文件之后不可取消

- 下载段的取消句柄提出来接受外部信号（真可取消，能省 ~15s）。
- **塞文件进上传控件之后不可取消**——文件已交给页面脚本，只能承认。这一条直接连着**真机项 A**（缩略图指向本机还是平台服务器？指向平台 ⇒ 抢占「已传图未提交」的发布会在小红书留**孤儿图且无回收手段**，必须写进 spec 显式承认）。真机项 A 是个 10 秒的检查，见 tasks.md 12.1。

---

## 4. 验收（本节做完的判据）

- [ ] `typecheck` + `test:acceptance` + 全量 `npm test` 全绿（当前基线 1317）。
- [ ] 新增断言：一个正在逐字输入的执行体，收到取消信号后**在下一个字符发出之前**停手；已输入部分被清场；回执诚实（复用第 3 节的清场三态）。
- [ ] 新增断言：定位引擎在等云端选元素时收到取消信号 → **不等满 200s**，就地作废并走升级上报，**绝不假成功**。
- [ ] 台账回写 `tasks.md` 第 4 节，格式 `<!-- aidcp-edge <sha> 分支 lease-strict-preemption -->`，sha **必须取自已推送的提交**（memory `tasks-md-sha-must-be-pushed`）。

---

## 5. 做完第 4 节之后

第 5 节（提交窗口标志 + 页面写者注册表 + 真抢占）才是抢占本体。**它依赖第 4 节**：没有取消点，第 5.5 的「等停到期 → 判控制面故障」会天天误触发。

另有一件**已经拍板、第 7 节要用**的口径（tasks.md §9，用户 2026-07-14 定）：**一切发布一律自动档**，不论触发路径；人工档只留「运营在线等回执」的动作（手动评论 / 手动加群 / 客户端内即时审批）。
