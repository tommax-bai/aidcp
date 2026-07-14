## Why

Facebook 的点赞与评论执行器不按命令携带的目标帖定位，而是靠「当前页面」的隐式假设，今天就会作用到错误的帖子——这是一个与后续 feed 就地互动无关、**当前已在生产上的正确性缺陷**：

- 点赞执行器忽略命令 payload 里的目标帖 id（`aidcp-edge/src/facebook/facebook-session.ts` 的 `likeCurrent(_payload)`），只对「当前页」操作；在信息流（非固定链接页）上下文里，目标查找会回落到整个 `document` 取 DOM 序第一个反应按钮（`src/facebook/like-executor.ts` 的 `searchRoots`）。当前仅靠云端「先导航进详情页」把页面变成单帖态兜住，一旦命令在信息流态到达就会点错卡。
- 帖子身份被定义成「卡内某个链接的 URL 规范化结果」。这个 key 既不唯一（一卡多链接）、不稳定（一帖多形态）、也不排他（别人的卡里也有你的链接）。`like-executor.ts` 内部的局部 `postKey` 按 URL pathname 计算、**丢弃 `multi_permalinks`**，而 `src/facebook/probes/page-structure.ts` 的 `sanitizeFacebookPermalinkHref` **保留** `multi_permalinks`——两者语义不一致，同群两个 `multi_permalinks` 形态的帖会撞成同一个 key，**即使在详情页上也会锁错卡**。
- 评论执行器的编辑框查找是 document 级（`src/facebook/comment-executor.ts` 的 `fbEditors()` + 取 `eds[0]`），多编辑框页面会把评论输入到错误的帖子下——一次真实的对外写入落在别人帖子里。

修好这条正确性地基，是后续任何 Facebook 浏览机制调整（feed 就地读/赞）能安全展开的前提。

## What Changes

- 新增一个跨执行器共用的**规范帖子身份**推导：从卡头 canonical 链接派生 `fb:<container>:<postId>`（container=群/主页 id，postId 取 `posts/<id>` / `story_fbid` / `multi_permalinks` / `pfbid` 段），**显式排除** `comment_id`、嵌套 article 内链接、分享/附件子树内链接；推导失败返回 `null`（不是空串，避免任何坏 href 都相等而又回落第一张卡）。匹配、去重、点赞/评论定位一律改用这一个身份，替换 `like-executor.ts` 内那个发散的局部 `postKey`。
- 点赞/评论/任何 note-scoped 命令改为**按命令携带的规范 postId 在当前 document 里解析出恰好一个目标 article**（三段式：作用域 → 顶层非嵌套候选 → 身份匹配）。解析 0 个回 `no_target`，同层 >1 个回 `ambiguous_target`，**绝不回落 DOM 序第一个**。
- 点赞把定位、点击、后置校验合成一次页内求值，给被点 article 打临时标记（`data-aidcp-target`），后置校验**只看该标记节点**并重新派生 postId 与命令一致；标记节点在校验前消失回 `verify_indeterminate`（不可重试）。保留既有反应计数按钮数字守卫与帖级/评论级消歧（并结构化）。
- 评论编辑框查找收窄到目标 article 子树，作用域内 0 编辑框回 `editor_not_found`，**不回落 `eds[0]`**。
- 点赞前按目标 postId 有界滚动把该 article 滚进视口再定位（拟人步进、有界轮次），替换无条件 `scrollIntoView({block:'center'})` 的瞬移。

本变更**edge-only、零协议改动、零云端改动**；小红书路径完全不受影响；Facebook 侧行为只在「不再点错卡/评错帖」这一维度改变，不引入任何 feed 就地互动。

## Capabilities

### New Capabilities

- `facebook-note-scoped-targeting`: Facebook note-scoped actions (like / comment) resolve exactly one target post from a canonical post identity carried by the command, and never fall back to DOM order.

## Impact

- Edge Facebook executors: `aidcp-edge/src/facebook/like-executor.ts`（`postKey`/`currentArticleRoot`/`searchRoots`/`findPostReactControl` 定位与后置校验合流）、`aidcp-edge/src/facebook/comment-executor.ts`（`fbEditors` 收窄）、`aidcp-edge/src/facebook/facebook-session.ts`（`likeCurrent` 真读 payload）、`aidcp-edge/src/facebook/probes/page-structure.ts`（`sanitizeFacebookPermalinkHref` 升级为 `canonicalPostId`）。
- Edge Facebook tests: `aidcp-edge/test/**` 的 like/comment 执行器测试扩多卡定位、fail-closed、歧义、撞键反例、编辑框收窄、`verify_indeterminate` 用例。
- 协议、`command-bridge`、`edge-client` 白名单、云端、console、数据库、`ol` 部署均**不受影响**（无新增消息类型、无新增主动命令）。
