# Design — facebook-feed-inline-browse (C2)

> edge，旗标 + 真机探针 gated。前置 C0 + C1b land + P0/P1/P2/P3。旗标全关时逐位等于今天。所有 `文件:行` 为 2026-07-14 HEAD 实核。

## 1. 真机实测地基（Dennis 环境 `k1ej3o8f`）

| 探针 | 结论 |
|---|---|
| P0 | feed 逐卡有帖级 `留下心情：赞`（无 aria-pressed）+ `评论` 同栏兄弟 ✅ |
| P1/P2 | 点「展开」原地补全（48→124 字）、`location.href`/弹层数(0)/卡索引全不变、卡仍在 DOM ✅ |
| P3 | pfbid 形态 feed 内一一对应无重复、`matchedArticles:1` ✅（跨扫描漂移/multi_permalinks/分享卡待补）|
| P5 | 点「评论」= 导航到 permalink + 弹层，评论框在弹层内、卡内联无编辑框、静态 feed textbox=0 ✅ |
| P4/P7 | 待跑：`el.click()` 是否直接提交 Like + 已赞态串（真点一次赞，已授权 dev+测试号）；虚拟化留壳/回收 |

## 2. feed 连续性（无旗标 bug 修复，先单验一轮）

- **`ensureFeed` 三判守卫**（`feed-reader.ts` 的 `ensureFeed` 首行无条件 `Page.navigate`）：改「`URL==activeFeedUrl && 已水合 && 无阻断浮层` 才跳过导航」。**关键红线**：跳过的只有 `Page.navigate`，`blockingReason()`（cookie 同意 / 登录+验证码复检）**仍每次跑**——否则把三道安全门从每次 scroll 降成每会话一次。
- **postId 集合游标**（非 DOM 序水位——回收态会失效）：`scanCards` 只上报本次新出现的**顶层非嵌套**水合卡（`FEED_SCAN_JS vis()` 现只判宽高，补顶层非嵌套 + noteId 取卡头时间戳链接非 `perms[0]`）。本批零新卡 ⇒ 有界续滚（防「回收后同一批头部卡重现→误判新卡→空转」）；仍零 ⇒ 诚实回 `feed_exhausted`。
- **FB `feed.refresh` 实现**：受控重新导航 feed URL + 清游标 + 回顶（对应 C1a 声明的 `feed_refresh.supported=true`）。`feed_exhausted` 回执由云端映射为 refresh（C1b）。

## 3. inline-reader（新 `src/facebook/inline-reader.ts`，旗标 gated）

`note.open{surface:'feed'}` 处理：

1. 按命令 postId 唯一锁顶层 article（复用 C0 `canonicalPostId` + 三段式）。
2. **捷径**：先比目标 message 容器 `textContent.length` vs `innerText.length`；前者远大 ⇒ 全文已在 DOM（CSS line-clamp 折叠），直接读 textContent、**根本不点**（P1 裁决，两种结果 inline-reader 都成立）。
3. 否则点该 article message 容器内**锚定**展开控件：正则 `/^(查看更多|展开|See more|View more|More)\s*$/i`、排 `<a href>`、页内 `el.click()`。**不复用** `page-structure.ts:192 expandControlCount`（非锚定、计祖先、零消费者）。
4. **展开前后校验** `location.href` + `document.querySelectorAll('[role=dialog]').length` + 目标卡索引，任一变 ⇒ 中止就地展开、回落详情导航、`note.detail{surface:'detail'}` 如实（P2 已证不变，但守卫必须在，防个别帖 See more 开 dialog/导航）。
5. 点后重测同一 article `innerText.length`，没变 ⇒ `expand_no_effect`（不当成功）；无展开控件短帖 ⇒ 正常成功（不是 no_target）。
6. 上报 `note.detail{noteId=页面派生, content=完整正文, ...}`。

## 4. note.open surface/purpose 分流 + 独立见证

- `facebook-session.ts` note.open 处按 `surface`/`purpose` 分流：`surface:'feed'` ⇒ inline-reader；`purpose:'navigate'` ⇒ 现役 `onOpen` 但 **MUST 跳过 `reportNoteDetail`**（否则拿 likeCount:0 覆盖真实反应数），只回 `action.completed{observation, 派生 noteId}`。
- `action.completed.observation` 由**实测**注入：`author/textPreviewHead/reactionText/articleIndex/listKey/surface` + 页面派生规范 postId。listKey=当前 feed URL 规范化（列表身份，防「别的 feed 也是 feed」）。

## 5. 目标易失性无回滚（N2）+ 内联读停留

- 目标已从 DOM 消失 ⇒ 直接 `no_target(stale)` **不回滚寻卡**（回滚污染游标 + 是可辨识模式）；只有仍在 DOM 只是离屏才拟人滚进视口。
- 内联读停留 = 边缘本地 read floor（正文长度本地已知 × 已下发 tempo，锚点 `inlineReadStartedAt`，与 feed 翻页停留取 max、MUST NOT 相加，对应 C1b 的 command-pacing MODIFIED）+ 断连兜底。

## 6. XHS 诚实拒 + 幽灵注释修复

- `browse-session.ts` 收 `note.open{surface:'feed'}` ⇒ 回 `capability_unsupported`，MUST NOT 静默回落 detail。
- 探针 P0–P7 产物落进本 change 目录，修 `cta-labels.ts`/`feed-reader.ts`/`post-reader.ts` 三处引用幽灵 `a9df78d` 的注释——**先真机重采、再落文档**。

## 7. 不做

- ❌ FB feed 内联评论（P5 已证「点评论=导航」；评论走 C1b 的迁移，只审批通过时付一次导航）。
- ❌ `AIDCP_FB_INLINE_DETAIL_RATE` 反指纹随机分支（系统无通道验证有效性）。
- ❌ 选择器/点击策略配置化（那是 driver 代码）。
- ❌ 在真机 P0/P1/P2/P3 过之前 land 任何 surface 翻转分支（旗标默认全关；`like.surface`/`read.surface` 留 detail）。
