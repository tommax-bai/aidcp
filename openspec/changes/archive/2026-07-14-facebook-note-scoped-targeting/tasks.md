## 1. aidcp-edge — Canonical post identity

- [x] 1.1 Upgrade `src/facebook/probes/page-structure.ts` `sanitizeFacebookPermalinkHref` into `canonicalPostId(href): string | null` — derive `fb:<container>:<postId>` from `posts/<id>` / `story_fbid` / `multi_permalinks` / `pfbid`, add container, exclude `comment_id` / nested-article / share-subtree links, and return `null` (not `''`) on failure.
<!-- aidcp-edge cf8cb4c 偏离①：canonicalPostId 落在**新模块** src/facebook/post-identity.ts（非原地改 page-structure.ts）——sanitizeFacebookPermalinkHref 产出的是**可导航的规范化 href**（feed 卡 noteId、note.open{url} 要用它导航），不能被身份字符串取代；page-structure 保留 href 规范化，只把**去重键**换成身份。偏离②（对抗性评审后）：身份是 `fb:<postId>`、**不含 container**。原设计的 `fb:<container>:<postId>` 会让同一帖两身份（`/Meta/posts/X` 的 container=主页 slug vs `/permalink.php?story_fbid=X&id=<数字id>` 的 container=数字 id）→ 确定性 no_target；FB 的 post fbid/pfbid/视频 id 本就全局唯一，container 对唯一性零贡献。偏离③：加**形状白名单**——只有帖子 permalink 形状才派生身份，否则 FB 卡头的作者主页链接 `/people/<slug>/pfbid…/`（DOM 序在时间戳 permalink 之前）会把卡身份变成「作者身份」→ 该作者每张卡永久 no_target（评审在真实注入产物上复现）。扩展：postId 来源在四种之外补 `/videos` `/reel` `/watch?v=`（视频帖也是 feed 卡，不派生=砍点赞能力）。comment_id/reply_comment_id → null。 -->
- [x] 1.2 Replace the divergent local `postKey` in `src/facebook/like-executor.ts` with the shared `canonicalPostId` derivation so like matching, comment matching, and dedup all key off one identity.
<!-- aidcp-edge cf8cb4c 局部 postKey 已删；like/comment/feed 候选去重（normalizeFacebookPermalinks 的 seen 键）统一走 canonicalPostId。**单一实现**：页内 JS 不是第二份拷贝，而是 canonicalPostId 本体经 Function.prototype.toString 注入（POST_IDENTITY_JS），并有对拍用例守（页内引用了模块作用域标识符就当场炸，不会静默退化成 no_target）。 -->

## 2. aidcp-edge — Three-stage target resolution (never DOM-order)

- [x] 2.1 Parameterize `like-executor.ts` `currentArticleRoot` into `articleRootFor(targetPostId)` fed by `canonicalPostId(payload.noteId)`, falling back to `location.href` derivation only when the command carries no noteId (old-cloud compatibility).
<!-- aidcp-edge cf8cb4c 实现为页内 fbTgtResolve(targetId)；noteId 缺省时页内回落 fbCanonicalPostId(location.href)。noteId 存在但派生不出身份（坏链接）→ 当场 no_target，连页面都不碰。 -->
- [x] 2.2 Implement three-stage resolution (scope: last-opened visible dialog > `div[role=feed]`; top-level non-nested candidate; identity match on the card-header canonical link) and **delete the `document` fallback** in `searchRoots`; extend fail-closed (0 → `no_target`, >1 same-level → `ambiguous_target`) from the permalink branch to the feed context.
<!-- aidcp-edge cf8cb4c searchRoots 已删。偏离①：document 仍作为**最后一级作用域**（permalink 全页态既无 dialog 也无 role=feed），但被删掉的「无匹配即取 DOM 序第一个」不复存在——任何作用域内都必须身份匹配唯一命中才动手。偏离②（评审后）：作用域根只认「真的含帖」的 dialog/feed——聊天/同意条/发帖 composer 这类**无帖弹层**不得劫持作用域（否则目标永远解析不到→点赞与评论双双永久失败）。偏离③：卡身份取「DOM 序首个可派生 id 的 own-level 锚」（与 feed-reader 产 noteId 同源），配合 1.1 的形状白名单，作者链接抢不到身份。偏离④：新增「URL 佐证的单帖态」兜底（作用域内恰好一张顶层 article、派生不出身份、且 location.href 身份==命令身份）——非 DOM 序回落，为不把「详情页卡内无自链接」变成永久 no_target。 -->
- [x] 2.3 Make `facebook-session.ts` `likeCurrent` read `payload.noteId` (drop the `_payload` discard).
<!-- aidcp-edge cf8cb4c -->

## 3. aidcp-edge — Bound the like to one card

- [x] 3.1 Merge LOCATE + CLICK + VERIFY into a single in-page eval that tags the clicked article with `data-aidcp-target="<runId>"`; VERIFY reads only the tagged node and re-derives its postId == command postId; tagged node missing before verify → `verify_indeterminate` (not retriable).
<!-- aidcp-edge cf8cb4c 偏离：不是字面「一次 eval」——后置校验本就是有界轮询（2s/300ms）塞不进点击那次 eval。落法：RESOLVE 一次 eval 内「解析唯一目标+打标」，其后 LOCATE/CLICK/VERIFY **只按标记选节点**、绝不重新解析——三阶段绑定同一张卡。标记消失/身份变了 → verify_indeterminate（executed=true，不重试）。标记 finally 里清，每轮 RESOLVE 先清 stale。附带：CDP/eval 异常从 no_target 改成诚实 nav_error。 -->
- [x] 3.2 Replace the unconditional `scrollIntoView({block:'center'})` with a bounded, humanized scroll that brings the target article into view before locating.
<!-- aidcp-edge cf8cb4c 读标记节点 rect → 按差值增量滚（拟人 wheel，复用 scrollFacebookViewport）→ 复读，有界 6 轮，落进 [5%,70%) 带即停。顺带修 viewport-scroll.ts：位移改**带符号**（旧 Math.max(1,…) 把负位移夹成 +1px、只能向下滚、够不着视口上方目标）。滚不出 → target_not_visible，绝不对当前居中的卡下手。 -->
- [x] 3.3 Structure `clusterHasComment` so a post-level react must share the action bar with a "comment/share" sibling and must not live inside a nested `[role=article]`; keep the reaction-count numeric guard (`赞：N位用户` is not a toggle).
<!-- aidcp-edge cf8cb4c fbSharesActionBarWithComment：有界上溯 5 层找共同动作栏，且上溯不得越出目标卡、动作栏与评论按钮都必须 own-level（closest article===目标）——评论条目里的「回复/评论」按钮不再能把评论级 react 抬成帖级。数字守卫原样保留 + 回归用例。 -->

## 4. aidcp-edge — Scope the comment editor

- [x] 4.1 Narrow `comment-executor.ts` `fbEditors()` and every `eds[0]` consumer to the target article subtree (reuse the existing `targetPath` template); 0 editors in scope → `editor_not_found`, never fall back to `eds[0]`.
<!-- aidcp-edge cf8cb4c(初版)+3a4aeec(评审加固) fbEditors() 收窄为「目标帖作用域内」：① 目标 article 子树内评论框优先；② 子树内没有 → 退到目标帖**排他区域**（从目标卡向上爬、不混进任何别的顶层帖 article 的最大祖先），只取该区域内**不属于任何 article** 且**恰好唯一**的评论框（>1 也诚实拒，不取第一个）。加②的理由：真机 FB 常把评论框渲染成主帖 article 的**兄弟**，严格只认子树会让 /comment（已在真机发评论的生产链路）永久 editor_not_found。四个消费者（focus/marker 验收/联系方式验收/清空）全改带目标身份的 builder。**评审复现并修的两条评错帖/假成功**：(a) 排他区域过去无钳制、污染源只按作用域内算 → 弹层里开目标帖时区域爬到 <body> → 评论打进背后 feed 里别人帖子的框；3a4aeec 改为污染源含**全文档所有** article（含 0 尺寸/隐藏）+ 上爬钳制在作用域根 + 区域退化成 body 且文档有别的帖→null。(b) 两个「服务器确认」脚本（就地 ack/刷新兜底）去掉 articles[0]/pathname 子串兜底与「退化成整帖 article」——后者会把编辑器里还没发出去的正文 + 帖级动作栏判成「服务器已点头」（假成功）；现均诚实拒。openPost 的 editorReady 仍用 document 级计数（只是「能否进提交」的提示，权威闸在 submit 的作用域聚焦上）。 -->

## 5. Verification

- [x] 5.1 Edge unit tests (jsdom / FakeCdp): multi-article feed with target = Nth card ⇒ only the Nth react button flips, cards 1..N-1 untouched; postId not present ⇒ `no_target` and the DOM-first card is untouched; same-group two `multi_permalinks` posts ⇒ distinct postIds (collide today); garbage/`javascript:` href ⇒ `no_target` (canonicalPostId returns null); three-stage ambiguity ⇒ dialog main post + per-comment article + background feed card sharing a key resolves to the main post only, real same-level >1 ⇒ `ambiguous_target`; multi-editor page ⇒ focus the target article editor, 0-in-scope ⇒ `editor_not_found`; `verify_indeterminate` when the tagged node disappears; numeric guard non-regression.
<!-- aidcp-edge cf8cb4c+3a4aeec 全覆盖：post-identity.test.ts（身份表 + 作者链接抢身份回归 + vanity vs permalink.php 收敛 + 页内/Node 同一实现对拍）、like-executor.test.ts（含「点第 N 张卡前面的不动」「同键→ambiguous」「详情弹层+嵌套评论+背景同键卡→只锁主帖」「作者头像 pfbid 链接仍锁目标卡」「无帖弹层不劫持作用域」「标记消失→verify_indeterminate 不重试」「拟人滚动无 scrollIntoView」「滚不出→target_not_visible」「CDP 异常→nav_error」「URL 佐证单帖兜底 + 不越界」）、comment-executor.test.ts（fb-editor-scope 7 例：多编辑框只命中目标 / 目标不在页面→空 / article 外由排他区域命中且回复框不算 / 混进别的帖→空 / 弹层+背后 feed 别人帖→绝不打进别人框 / 区域内>1→空 / 0 尺寸旁帖不纳入；fb-ack 2 例：没发出去绝不 ackConfirmed + 真评论行 ackConfirmed）、viewport-scroll.test.ts（负位移向上滚）。 -->
- [x] 5.2 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck`; AC-PROTO stays green (no protocol change).
<!-- aidcp-edge 3a4aeec test:acceptance 19/19（AC-PROTO/AC-PUB 全绿，零协议改动）；npm test 1210/1210（land 时全仓 1259/1259）；typecheck 干净。 -->
- [x] 5.3 Rebase on `origin/master`, integrate, push edge to `master`; record real-machine acceptance under cluster 64 in `docs/real-machine-acceptance-backlog.md` (feed like hits only the Nth card, no DOM-first fallback, multi_permalinks no collision, three-stage locks main post only, comment does not misfire, humanized scroll without teleport).
<!-- aidcp-edge cf8cb4c+3a4aeec rebase 到 origin/master(ede64c4) 后 ff 推送到 master（3a4aeec）。edge-only、无 ECS 部署，需运营/客户机 pull master + 重建安装包后生效。真机项登记 backlog 簇 64（新增 change 段）。 -->

## 6. Change Record

- [x] 6.1 Update this task record with commits and validation; `openspec validate facebook-note-scoped-targeting --strict`.
<!-- openspec validate --strict 通过。两轮多智能体对抗性评审（28+11 agent，真实注入产物 jsdom 复现）：第一轮 3 条真问题（排他区域爬 body 评错帖 / 作者链接抢身份整类卡失败 / 无帖弹层劫持作用域）修于 cf8cb4c，第二轮 1 条残余（0 尺寸旁帖漏算污染源）修于 3a4aeec，各带回归用例。 -->
