# Design — facebook-note-scoped-targeting (C0)

> edge-only 纯 bug 修复，零协议 / 零云端。是 FB feed 就地互动（C2）与整个多平台浏览抽象（C1）的正确性地基。所有 `文件:行` 为 2026-07-14 HEAD 实核，随代码演进以行为为准。

## 1. 问题的根：帖子身份不是「某个链接的 URL」

今天三处独立地把「点哪张卡 / 评哪张卡」建立在脆弱的 URL 推断上：

| 位置 | 现状 | 缺陷 |
|---|---|---|
| `like-executor.ts:208 postKey` | 按 `new URL(href).pathname` 规范化当 key | 丢 `multi_permalinks` 查询参数；与 `page-structure.ts:111 sanitizeFacebookPermalinkHref`（保留 `multi_permalinks`）**语义不一致**；同群两个 `multi_permalinks` 帖撞成同 key |
| `like-executor.ts:225 searchRoots` | permalink URL 命中 article 则限定其中，否则回落 `document` | feed 态（URL=`origin+'/'`）无命中 → 取 DOM 序第一个反应按钮 = 点错卡 |
| `comment-executor.ts:623 fbEditors` + `:705/:717/:735 eds[0]` | document 级取第一个可见评论编辑框 | 多编辑框页面输入落到别人帖子下 |

**统一治法**：定义一个规范帖子身份 `fb:<container>:<postId>`，作为匹配 / 去重 / 定位 / 后置校验的唯一依据，替换发散的局部 `postKey`。

## 2. 规范帖子身份 `canonicalPostId(href)`

把 `page-structure.ts:111 sanitizeFacebookPermalinkHref` 升级为 `canonicalPostId(href): string | null`：

- container = 群 id（`/groups/<id>/...`）或主页 slug/id；缺省用空 container 但保留 postId。
- postId 取值优先级：`/posts/<id>` → `story_fbid=<id>` → `multi_permalinks=<id>`（群帖）→ 路径中的 `pfbid<...>` 段。
- **排除**：`comment_id` 参数、URL 落在嵌套 `[role=article]`（评论）子树内的链接、分享/附件子树内链接。
- **失败返回 `null`，不是 `''`**——空串对任何坏 href 都相等，会让「匹配不到」退化成「又点第一张」。

身份字符串 = `fb:${container}:${postId}`。这个身份**同时**用于：命令 payload 的 noteId 解析、feed 卡 → article 匹配、`liked_notes`/双证据 Set 的键（云端侧在 C1/C2 切齐，本 change 只保证 edge 派生一致）。

> ⚠️ 真机未定项（转 C2 的探针 P3）：`pfbid` 是否跨扫描/跨会话漂移、分享卡的首链接是否等于卡头 canonical 链接。本 change 的 fail-closed（派生失败或匹配不到即诚实拒）保证「不稳时不乱点」，不假设身份一定稳定。

## 3. 三段式目标解析（取代「全 document 扫 + 取第一个」）

任何 note-scoped 命令，边缘用命令携带的规范 postId 解析出**恰好一个**目标 article：

1. **作用域**：可见 `[role=dialog]`（取**最后打开的**，非 `querySelector` 第一个）优先，否则 `div[role=feed]`。
2. **顶层候选**：作用域内、祖先链上无其它 `[role=article]` 的节点（`a.parentElement.closest('[role=article]')===null`）——排除嵌套评论 article。
3. **身份匹配**：候选卡头 canonical 链接（`h2/h3/h4` 邻近的时间戳锚）派生的规范 postId 与命令 postId 相等。

解析结果：0 个 → `no_target`；同层 >1 个 → `ambiguous_target`；恰好 1 个 → 目标。**任何情况都不回落 DOM 序第一个。**

## 4. 边缘八处落点

| # | 位置 | 改法 |
|---|---|---|
| ① | `page-structure.ts:111 sanitizeFacebookPermalinkHref` | 升级 `canonicalPostId(href)`：加 container、保留四形态 postId、排 comment_id/嵌套/分享子树，**失败返 `null`** |
| ② | `like-executor.ts:208 postKey` / `:213 currentArticleRoot` | 参数化为 `articleRootFor(targetPostId)`；`targetPostId=canonicalPostId(payload.noteId)`；缺省回落 `location.href` 派生（老云端不带 noteId 时兼容） |
| ③ | `like-executor.ts:225 searchRoots` | **删 `document` 回落**；fail-closed（0 与 >1 皆拒）从 permalink 分支扩到 feed 态 |
| ④ | `like-executor.ts:238/248/254/263 findPostReactControl` + `:257 scrollIntoView` | LOCATE+CLICK+VERIFY **合成一次页内 eval**：定位目标 article、点击、采样，被点 article 打 `data-aidcp-target="<runId>"`；VERIFY **只看标记节点**、重新派生 postId==命令 postId；标记节点消失 → `verify_indeterminate`（不可重试） |
| ⑤ | `comment-executor.ts:623 fbEditors` + `:705/:717/:735 eds[0]` | 收窄到目标 article 子树（复用它 `:758/:794` 已有的 targetPath 模板）；作用域内 0 编辑框 → `editor_not_found`，**不回落 `eds[0]`** |
| ⑥ | `facebook-session.ts:563 likeCurrent(_payload)` | 真读 `payload.noteId`（不再 `_payload`） |
| ⑦ | `like-executor.ts:257 scrollIntoView({block:'center'})` | 换「按 postId 有界滚到目标 article 可见」显式循环（读目标 `boundingRect.top`、拟人步长增量滚、每步重扫、有界 N 轮/T 秒），先滚到可见再定位 |
| ⑧ | `like-executor.ts` `clusterHasComment` 帖级判定 | 结构化：react 控件须与「发表评论/分享」同一动作栏容器（同父/同 `role=group`）、且动作栏不在嵌套 `[role=article]` 内。**保留反应计数按钮数字守卫**（`赞：N位用户` 不当 toggle） |

## 5. 红线（本 change 兑现的）

- **不点错卡**：三段式 + fail-closed，绝不 DOM 序回落（§3）。
- **不评错帖**：编辑框收窄到目标 article，0 编辑框诚实拒（④⑤）。
- **不假成功**：`data-aidcp-target` 绑定同一张卡的后置校验；`verify_indeterminate` 不可重试；`no_target`/`ambiguous_target` 如实回执。
- **XHS 零影响**：全部改动在 `src/facebook/**`，小红书路径不触及。

## 6. 消歧点（真机实测坐实）

真机（Dennis 环境）观测到每张卡有 2 个「留下心情」类按钮：`给X的帖子留下心情：赞`（真触发，`text=赞`）与 `给X的帖子留下心情`（悬停展开更多表情容器，`text=空`）。§4-⑧ 取「文本=赞 / aria 以`：赞`结尾」那个；旁边 `赞：N位用户`/`大爱：N位用户` 是计数按钮，数字守卫排除。

## 7. 不做

- ❌ 不发新协议字段（observation / 派生 noteId 的回执 emission 在 C1b/C2）。
- ❌ 不改云端归账（C1b）。
- ❌ 不引入 feed 就地读/赞（C2）。
- ❌ 不动 `currentNote` 单槽 → Map（编排严格串行）。
