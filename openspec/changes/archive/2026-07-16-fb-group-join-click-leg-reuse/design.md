## Context

**现状（坐实，2026-07-16）**：

- 云端 `facebook-group-join-scheduler.ts:303` 起 `group_join` 租约 → `observeGroup(groupUrl)` → 下发 `group.join{click:false}`。
- 租约**释放**，`evaluatePreClick` 跑 LLM 预判（`:320`）。
- 云端 `:329` **重新申请** `group_join` 租约 → `clickJoin(groupUrl)` → 下发 `group.join{click:true}`，**URL 逐字相同**。
- 两条命令由同一个 `facebook-group-join-edge-steps.ts:92` 构造，只有 `click` 不同。
- 边缘 `join-executor.ts:641` `Page.navigate` **无条件**在例程开头执行，`:673` 的 `if (!options.click) return {reason:'observation_only'}` 在其**之后** ⇒ **两腿各加载一次同一页**。

五路独立代码追踪（workflow `wf_e09a80d0-096`，含三视角对抗复核）一致收敛于此，并**排除**了以下常被误指的成因：

| 排除项 | 排除理由 |
| --- | --- |
| `ensureFeed` 守卫整页重载（历史「一直刷新」元凶） | 该守卫只在浏览闭环；`/comment` 全程委派 `FacebookCommentHandler`，**根本不经过它**。且 `fb8c5b3` / `adf10f8` / `678bdc6` 均已在 edge master |
| 断连恢复重导航（`main.ts:607`） | 触发条件仅为 WebSocket 重连，非本流程 |
| 身份监测误判重导航（`main.ts:912`） | 触发条件仅为身份失效 |
| 群内搜索页导航（`comment-executor.ts:378`） | **不同 URL**、找帖子必需，非冗余 |
| `canonicalGroupUrl` 归一导致 FB 重定向 | 判据取消 canonical 化 current URL 即绕开（见下） |

## Goals / Non-Goals

- **Goal**：每次逻辑加群，目标群主页只被完整加载**一次**（今天两次）。
- **Goal**：省下一整轮就绪轮询（实测群页加入按钮需数秒渲染）。
- **Non-Goal**：不动云端两段式 / 租约释放设计——那是对的。
- **Non-Goal**：不追求「零加载」——observe 腿的加载是承重的（下节）。

## Decisions

### D1（承重）：只有 click 腿复用；observe 腿永远导航

**为什么不能两腿都复用** —— 反例即死锁：

1. 页面因任何原因卡在目标 URL 上的坏状态（半渲染、被别的任务开到一半、DOM 被弹层污染但 URL 未变）。
2. click 腿：URL 匹配 → 跳过导航 → 观察坏页 → `not_ready`。
3. 云端 `markEdgeFailure('not_ready')` → 短退避 → 心跳重新捞起 → **新一轮 observe 腿**。
4. **若 observe 腿也复用**：URL 仍匹配 → 仍跳过导航 → 仍观察同一个坏页 → 仍 `not_ready` → **永远出不去**，直到 attempts 撞上限被永久标 `failed`。

⇒ **observe 腿的无条件导航是唯一的故障恢复手段**，必须保留。保留后：click 腿即便复用到坏页，`not_ready` → 重试 → observe 腿重新导航 → **恢复**。死锁不可能成立。

这也让「复用」的语义变得干净：**observe 腿确立页面，click 腿延续自己刚确立的那个页面**。

### D2：在位判据严格，且失败方向 = 导航

判据**故意不复用** `canonicalGroupUrl(current)`：它会把 `m.facebook.com/groups/<id>`、`/groups/<id>/about` 统统归一成 `https://www.facebook.com/groups/<id>`，从而误判「在原地」——

- `m.facebook.com`：**另一套移动 DOM**，观察脚本按桌面 DOM 写 ⇒ 跳过导航 = 在错 DOM 上观察。
- `/about` 等子面：加入按钮未必在、或在不同位置 ⇒ 可能落 `no_button`（云端判**永久 failed、不进重试池**——这正是 `facebook-join-candidate-scope-guard` 拼命避免的后果）。

故新写独立谓词，**只认「导航本会把我们放到的那个位置」**：同 origin + pathname 恰为 `/groups/<id>`（容尾斜杠）。query/hash 不计（`?ref=share` 仍是群主页）。取不到 URL / 解析失败 / 任何存疑 ⇒ **返回 false ⇒ 导航**（退回今日行为）。优化只在确定安全时生效。

### D3：就绪轮询不跳过

`observeUntilReady` 保持为就绪唯一权威。跳过导航**只省加载**，不省判断：

- 页面真的好 ⇒ 首轮 `isDecisiveObservation` 命中（加入按钮已渲染 + `documentReady !== 'loading'`）⇒ 立即返回 = **省下的那一轮**。
- 页面不好 ⇒ 照常轮询到上限 ⇒ `not_ready` ⇒ D1 的恢复路径接管。

⇒ 本 change **不引入任何新的假成功面**：所有既有闸（同意浮层、登录、验证码、问卷、待审、作用域、矛盾守卫）位置不变、语义不变。

### D4：不跳过 `preClickSettleMs`

复用页面时 React 早已水合（页面挺过了一整个 LLM 调用），2s 理论上可省。**不省**：收益 2s，风险是「点了不生效」这个已被真机咬过的老伤（`fb-group-join-timeouts`）。YAGNI。

## Risks / Trade-offs

| 风险 | 缓解 |
| --- | --- |
| click 腿复用到一个 URL 对但状态坏的页 | D1：`not_ready` → 重试 → observe 腿重新导航恢复。**不可能死锁** |
| 判据过松误判在位 | D2：不 canonical 化 current；origin + 精确 pathname；存疑即导航 |
| observe 与 click 之间别的任务把页面开走 | URL 判据不匹配 → 导航（今日行为）。**判据自我保护**：任何冷调用 `clickJoin`（浏览器在别处）也天然走导航 |
| 与 deferred `facebook-join-actuation-decouple` 冲突 | 正交且**上游缓解**：该 change 的立论前提是「click 腿在新页重定位候选」；本 change 让 click 腿**不再换页**，候选身份天然保真。该 change 仍可独立实装（其回落路径不变），本 change **不替代**它、也不依赖它 |
| 热点文件并发 | `join-executor.ts` 不在 §7 热点清单；实测无其他活跃 change 触及（`grep` 全 `tasks.md` 零命中） |

## Migration / Rollback

- **零协议变更、零云端变更、零 DB 变更**。纯边缘单文件行为收窄。
- 回滚 = 让在位谓词恒返回 `false` ⇒ 逐字退回今日「无条件导航」行为。
- 无需 feature flag：优化路径的失败方向就是今日行为，flag 是纯冗余（YAGNI）。
