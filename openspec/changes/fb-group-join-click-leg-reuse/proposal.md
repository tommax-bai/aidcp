## Why

Facebook 加群是**两段边缘调用**：① observe 腿（`click` 缺省）——边缘导航到群页、就绪轮询、回传观测、**不点**；② 云端裁判观测安全后下 `click=true`——边缘**再次导航到同一个群页**、重新就绪轮询、点「加入」。

两段是**对的**：云端在两段之间**故意释放边缘任务租约**（`facebook-group-join-scheduler.ts:326-327`「预判 LLM 已在租约外完成；真实点击重新申请任务租约，绝不长占浏览器」），不在等 LLM 的几秒里霸占浏览器。

**但边缘的 `joinGroup` 是一个 navigate→observe→click 的整体例程，开头的 `Page.navigate` 无条件执行**（`join-executor.ts:641`），排在「本次只观察」的守卫（`:673`）**之前**。于是 click 腿把一个**已经加载好、已经水合完毕**的页面**整页重新加载了一遍**。

真机可见（用户 2026-07-16 跑 `/comment <nick> --join --contact --force` 报告）：群页面区域被连续完整加载三次（群主页 ×2 同址 + 群内搜索页 ×1），主观即「页面跳两次、进群后又刷新一次」。

**代价**（非正确性 bug——群照样加上、评论照样发）：

1. **白等一整轮渲染**：FB 群页的加入按钮实测需数秒才渲染（本 capability 的就绪轮询即为此而生，上限 30s）。重新加载 = 丢掉 observe 腿已经等到的成熟 DOM，从头再等一轮。edge click 腿最坏预算 ≈ 30(ready)+2(settle)+1.5(afterClick)+45(post)=78.5s，云端 `group.join` 步骤超时 120s——白等的这一轮直接吃掉本就不宽的余量。
2. **反检测面**：对同一 URL 连续两次整页加载是机器行为特征。

## What Changes

- **click 腿复用已确立的目标页**：`click=true` 调用发现**当前页恰为目标群主页**时，SHALL 跳过 `Page.navigate`（及其后的 `settleMs`），直接进就绪轮询→点击。
- **observe 腿永远导航，绝不复用**（**承重不变量，见 design.md 的死锁论证**）：observe 腿是「确立页面」+「故障恢复」的**唯一**手段。若两腿都复用，页面一旦卡在目标 URL 上的坏状态，`not_ready` 重试将**永远不会重新加载**、死锁在坏页面上。observe 腿无条件导航 ⇒ 每次逻辑加群必有一次干净加载兜底，重试必定重开。
- **判据严格、失败即导航（fail-safe 方向）**：「在原地」判据 = 同 origin（必须 `https://www.facebook.com`——观察脚本按桌面 DOM 写，`m.facebook.com` 是另一套 DOM）+ pathname 恰为 `/groups/<id>`（容尾斜杠）。query/hash 不计（群主页带 `?ref=…` 仍是群主页）。`/groups/<id>/about`、`/groups/<id>/posts/…` 等子面**一律不算**。判据取不到 / 存疑 → 导航（退回今天行为，绝不因优化而少加载）。
- **就绪轮询照跑，不因跳过导航而跳过**：`observeUntilReady` 仍是就绪与否的唯一权威。已在原地且水合完毕 ⇒ 首轮即决定性、立即返回（这就是省下的那一轮）；页面若处于坏状态 ⇒ 照常轮询到底 → `not_ready` → 云端短退避重试 → 新 observe 腿重新导航 → 恢复。
- **不做（YAGNI）**：不跳过 `preClickSettleMs`（2s 水合等待，收益小于风险）；不跨调用缓存 DOM 句柄 / 坐标（`facebook-join-actuation-decouple` 已证跨导航句柄必失效——但本 change 让 click 腿**不再跨导航**，是那个 deferred change 的上游缓解，不替代它）；不动云端两段式设计（云端零改动）；不动协议（零字段变更）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `fb-group-join-wait-render` — 就绪轮询前的导航从「无条件」收窄为「observe 腿无条件 / click 腿按在位判据复用」。
