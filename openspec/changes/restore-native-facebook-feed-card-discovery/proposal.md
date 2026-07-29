## Why

2026-07-29 用 AdsPower 启动真实账号环境（`k1f4kcsv` / Xu Nu，越南语首页），挂 CDP 逐项实测，得到一组硬数字：

| 指标 | 实测 |
| --- | --- |
| `div[role="feed"]` | **0** |
| `[role="article"]`（Native 唯一的找卡依据） | **2**，且均为 286px 高的**空壳**（0 链接 / 0 文字） |
| `[aria-posinset]`（该版式的真实条目） | 11 |
| 退役 TS 回落路径（从帖子正文标记向上找带作者链接的祖先）找到的卡 | **5 张真卡**，作者 `NHÀ ĐẸP AN BÌNH` / `Đại Việt Kỳ Nhân` / `Liên Bỉnh Phát` 等，正文均为真实越南语内容 |
| 其中已带可接受 permalink（无需任何交互） | **2 张** |
| 页面滚动 | 正常（高度 2010 → 9407，懒加载在工作） |

即：**页面、登录、代理、滚动全都正常，卡是有的，只是 Native 找卡的那一条路在这个版式上恒定命中零。**

退役 TS 实现找卡是**三路并用**（`aidcp-edge/src/facebook/post-identity.ts:135-150` 的 `fbFeedTopCards`）：① 语义路 `div[role="feed"]` 内的 `[role="article"]`；② 视频路，从 `[data-video-id]` 反向上溯卡边界（`:107-125`）；③ **回落路**，从帖子正文标记 `[data-ad-comet-preview="message"]` 等向上走到第一个带作者链接 `h2/h3/h4 a[href]` 的祖先（`:87-106`），**完全不依赖语义 role**。三路结果再按包含关系去重合并（`:126-134`）。

Native 迁移只搬了 ①（`native/page-engine/src/facebook-router/00-shared.js:277-280` 的 `topArticles`）。②③ 全丢。这是**迁移回归，不是新提案**——③ 正是为「没有 `role="feed"` / `role="article"` 的版式」写的。

同批还丢了**水合过滤**：退役实现判「首页是否有卡」时要求该卡含作者链接或正文标记（`src/facebook/feed-reader.ts:264`），Native 的 `articleCount` 只数可见性（`20-feed.js:228`），于是那 2 个空壳被当成「有物理卡」。后果是 change `restore-native-facebook-feed-scroll-continuation` 的兜底会以**错误的理由**判成「有内容读不出来」——结论恰好正确，依据是假的。

## What Changes

- **补回回落找卡路径**：从帖子正文标记向上走到第一个带作者链接的祖先作为卡边界；跳过已在 `div[role="feed"]` 内的（那条走语义路）；按包含关系只保留最外层；按文档顺序排序。判据逐条照抄退役实现。
- **合并而非替换**：语义路结果与回落路结果按「互不包含」去重合并，语义路优先。已有版式行为逐位不变。
- **补回水合过滤**：判定「首页有物理卡」时只数**已水合**的卡（含作者链接或正文标记），空壳不再冒充物理卡。
- **不新增协议字段、不新增原因码、不改任何回执语义**。

**非目标（本 change 明确不做，已登记为后续）**：
- **视频路（②）**：其准入依赖「恰好 1 个视频 id + 1 个 video 元素 + 恰好 1 个点赞控件 + 1 个评论控件」，后两者的语义在 `08-reaction-semantics.js`（晚于 `00-shared.js` 加载），跨文件取用会引入隐式加载顺序耦合。实测该页面 `[data-video-id]` 仅 1 个、且其所属卡已被回落路覆盖，收益极低、风险不成比例。
- **时间戳诱饵链接**：实测该版式的时间戳 href 平时指向站点根路径，**鼠标真实悬停后**才换成 `/<主页>/posts/pfbid…` 或 `/permalink.php?story_fbid=…`（视口内 7/7 复现）。这是 Facebook 新加的反抓取、**退役实现同样没有**，属新能力而非回归，另起 change。本 change 落地后，5 张卡中已有 2 张无需悬停即可上报。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `native-facebook-behavior-parity`: 「Native Feed scanning preserves stateful continuation truth」当前只规定了卡的**状态**分类，未规定卡的**发现**必须覆盖非语义化版式。补上两条义务——找卡不得只依赖 `role="feed"` / `role="article"`，须含以帖子正文标记为种子的回落发现；「有物理卡」的判定须以水合证据为准，未水合的空壳不得计入。

## Impact

- **代码**：只改 `aidcp-edge/native/page-engine/src/facebook-router/00-shared.js`（找卡）与 `20-feed.js`（物理卡计数）。Rust 侧、协议侧、cloud 侧、console 侧零改动。
- **波及面**：`topArticles()` 有 9 处消费方（点赞定位、首帖定位、Reels、探测、诊断）。全部消费方都按 permalink 精确匹配再取唯一命中，放宽候选集不会让它们误选；合并去重保证同一帖不会同时以语义卡与回落卡出现两次。
- **验证条件优越**：本机有一个已登录该账号的真实浏览器在跑，可把改后的发现逻辑直接注入实页比对——不必只靠桩。
- **红线**：MUST NOT 静默假成功。回落路只在能找到作者链接的祖先时成卡；找不到就不成卡，绝不把整页或无关容器当成一张卡。
