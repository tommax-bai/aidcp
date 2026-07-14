## Why

真机实测（Dennis 环境）坐实：Facebook 与小红书页面模型不同——**首页信息流点「查看更多」原地补全完整正文、不离开信息流**（正文 48→124 字，URL/弹层/卡索引全不变），**逐卡有帖级点赞按钮**（`留下心情：赞`，与评论按钮同栏），**只有评论需要进详情页**（点评论=导航到固定链接 + 弹层，评论框在弹层内、卡内联无编辑框）。而今天的实现有三个结构性浪费/缺陷：

- **为读正文/点赞而无谓进详情页**：每篇 ≈3 次整页导航；且长帖正文无论走信息流还是详情页**都被截断**（`feed-reader.ts:141` 180 字 / `post-reader.ts:224` 2000 字 / 折叠态 innerText 只有可见部分），洗稿/评论一直在吃残缺正文。
- **信息流不连续**：`facebook-session.ts` 的 `scrollFeed` → `feed-reader.ts` 的 `ensureFeed` 第一行无条件 `Page.navigate` 重载回顶，就地展开/点赞的成果下一秒被冲掉，账号其实在反复看同一批帖。
- **信息流到底无自愈**：滚不出新卡时无诚实终止信号，会转 idle。

本变更让 Facebook 在信息流就地读全文、就地点赞（由云端 surface 旗标 + 真机探针 gated），只在决定要评论时才迁移进详情页。**前置 = C0（目标锁定）+ C1b（协议 surface/purpose + 归账）已 land + 真机探针 P0/P1/P2/P3 过。** feed 连续性（无旗标 bug 修复）先单独验一轮。

## What Changes

- **feed 连续性（无旗标，先单验）**：`ensureFeed` 幂等守卫改「`URL==activeFeedUrl && 已水合 && 无阻断浮层` 才跳过 `Page.navigate`」——**跳过的只有导航，`blockingReason()` 仍每次跑**（cookie 同意 / 登录+验证码复检不能从每次 scroll 降成每会话一次）；`scanCards` 只上报本次新出现的**顶层非嵌套**水合卡（排嵌套评论 article、noteId 取卡头时间戳链接非首个 permalink）；持会话级 postId 集合游标（非 DOM 序水位，回收态会失效）；本批零新卡 ⇒ 有界续滚，仍零 ⇒ 诚实回 `feed_exhausted`；FB `feed.refresh` 实现 = 受控重新导航 feed URL + 清游标 + 回顶。
- **inline-reader（新 `src/facebook/inline-reader.ts`，旗标 gated）**：`note.open{surface:'feed'}` ⇒ 按命令 postId 唯一锁顶层 article（复用 C0 的 `canonicalPostId` + 三段式）→ 先比 `textContent.length` vs `innerText.length`，前者远大 ⇒ 全文已在 DOM 直接读、根本不点 → 否则点该 article message 容器内锚定展开控件（锚定正则、排 `<a href>`、页内 `el.click()`）→ **展开前后校验 `location.href`/弹层数/卡索引不变**，任一变 ⇒ 中止、回落详情导航、`note.detail{surface:'detail'}` 如实 → 点后重测长度未变 ⇒ `expand_no_effect`（不当成功）。
- **note.open surface/purpose 分流**（`facebook-session.ts` note.open 处）：`purpose:'navigate'` 的 onOpen **MUST 跳过 `reportNoteDetail`**，只回 `action.completed{observation, 派生 noteId}`。
- **独立见证注入**：`action.completed.observation` 由**实测**注入（author/textPreviewHead/reactionText/articleIndex/listKey/surface）+ 页面派生规范 postId。
- **目标易失性无回滚**：目标已从 DOM 消失 ⇒ 直接 `no_target(stale)` 不回滚寻卡；只有仍在 DOM 只是离屏才拟人滚进视口。
- **内联读停留**：边缘本地 read floor（正文长度本地已知 × 已下发 tempo，锚点 `inlineReadStartedAt`，与 feed 翻页停留取 max）+ 断连兜底。
- **feed 卡 best-effort 抓可见评论** → `note.detail.comments[]`（协议已有字段）。
- **XHS 诚实拒**：`browse-session.ts` 收到 `surface:'feed'` ⇒ 回 `capability_unsupported`，**MUST NOT 静默回落 detail**。
- **探针产物入库**：P0–P7 结果落进本 change 目录，并修 `cta-labels.ts`/`feed-reader.ts`/`post-reader.ts` 三处引用不存在探针文档（幽灵 `a9df78d`）的注释。

## Capabilities

### New Capabilities

- `facebook-feed-browse`: Facebook reads full post text and likes in place on the home feed (behind a cloud surface flag), keeps the feed continuous instead of reloading to top, self-heals an exhausted feed, and honestly reports when in-place expansion would leave the feed.

## Impact

- Edge Facebook browse: `aidcp-edge/src/facebook/facebook-session.ts`（note.open surface/purpose 分流、scrollFeed）、`aidcp-edge/src/facebook/feed-reader.ts`（`ensureFeed` 三判守卫、postId 游标、`feed_exhausted`、FB refresh）、`aidcp-edge/src/facebook/inline-reader.ts`（新）、`aidcp-edge/src/facebook/post-reader.ts`（回落详情兼容）、`aidcp-edge/src/facebook/probes/page-structure.ts`（顶层非嵌套卡、卡头链接）。
- Edge XHS honest refusal: `aidcp-edge/src/browse/browse-session.ts`（收 `surface:'feed'` 回 capability_unsupported）。
- 幽灵探针注释修复：`aidcp-edge/src/facebook/cta-labels.ts`、`feed-reader.ts`、`post-reader.ts` 头部注释。
- 前置：C0（`facebook-note-scoped-targeting`）land + C1b（`platform-browse-protocol`）land + 真机 P0/P1/P2/P3；与 `facebook-dev-autobrowse-enable` 的 `browse-loop-resilience` delta 语义重叠（列表上下文校验 vs feed 游标/守卫）⇒ 协调、不并行。
- 协议不新增（surface/purpose/observation 在 C1b 已落）；云端、console、数据库、`ol` 不受影响；旗标全关时逐位等于今天。
