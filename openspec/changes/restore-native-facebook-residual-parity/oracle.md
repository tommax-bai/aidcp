# 退役实现参照（oracle）

> 用途：本 change 的多数条目属「以前能做、迁移后做不了」。退役的 TypeScript 实现仍在
> /Users/baitianxing/codes/aidcp-edge/src/ 下（被构建期剪枝挡在生产外、宿主装配被恒假条件短路），可直接当行为参照。
> **只当参照书，不得把退役实现搬回生产**——那会击穿本次迁移的动机，且宿主那段是死码不是开关。
> 迁移前版本用 `git -C /Users/baitianxing/codes/aidcp-edge show 317cd47^:<path>`（小红书）或 `4f04e9c^`（Facebook/微信）读。

## ⚠️ 不可照抄的条目（先看这段）

### ② 评论入口从不点击（折叠态必然失败）—— `also-wrong`
旧实现**同样从不点击**「评论」CTA，它只有有界滚动催拉（6 轮 × 700px）。照抄旧代码不会带来任何点击能力。
旧实现之所以不需要点：它的评论链路**先按 permalink 整页导航到帖子详情页**（`comment-executor.ts:633-679` 的 `openPost` → navigate），
详情页上评论框天生展开，**折叠态在旧架构里根本不出现**。新引擎的评论走的是「在列表 / 就地上下文里评论」，
折叠态是**迁移后新出现的形态**。
→ 可照抄的只有旧代码的两个**替代机制**（先导航到 permalink；有界催拉预算），
外加新引擎自己已经写好但没接上的点击闸（`runtime.rs:338-388`）。
**照抄的后果**：把 6 轮滚动照搬一遍，折叠态照样 100% 失败，且会误认为「已对齐旧行为」而收工。

### ⑥ 反应/评论控件标签的兼容形·分解形不识别 —— `also-wrong`（两代共有盲区）
两代都**没有**对控件标签做 Unicode 归一化。两代都只在「首页空态文案」这一处做了 NFD 去变音符
（旧 `feed-reader.ts:257` 的 `norm`、新 `20-feed.js:178` 的 `clean`），控件标签正则一律裸比。
旧实现对越南语的处理是**在词表里手工并列两个写法**（带变音符的 `Thích` 与 ASCII 折叠的 `Bay to cam xuc Thich`），
这是**穷举而非归一**：只覆盖了当初真机见过的那两种形态，NFD 分解形（`T-h-i-◌́-c-h`）两代都不认。
新引擎 `08-reaction-semantics.js:1` **逐字继承了这套并列写法**，因此**看起来**覆盖越南语、实际没有。
**照抄的后果**：把盲区原样搬过来，且被「词表里有越南语」这个表象掩盖。
**尤其注意连带效应**：修 ① 时新增的计数控件选择器**若照抄裸比就会带着同一个盲区上线**——
本 change 的 tasks 里没有任何一条要求新见证解析做归一化，见文末「覆盖漏洞」。

### ③ Cookie 同意策略与失败分档 —— `direct`，但**立论必须先修正**
change 正文 / tasks 完全没提这条，且外界常见的前提「新版只会点接受全部」在当前 HEAD **不成立**：
新引擎**已经**有策略枚举（`shared.rs:426-434` 读 `AIDCP_FB_COOKIE_CONSENT`，`necessary_only` 下取 necessary_only 点位）。
真正缺的是失败分档、探测失败降级，以及一处**新引入的作用域自伤**（详见「逐条参照 ③」）。
**照抄的后果**：按「补一个策略枚举」去做，等于做了一件已经存在的事，真正会把整台账号打死的那条自伤原封不动。

### ④ 小组页/搜索页滚到底 —— `direct`，但旧实现是「面无关」的
旧实现同一段滚动逻辑吃 `activeFeedUrl`，首页 / 搜索 / 群组一视同仁，所以它**天然没有这个 bug**、
也就没有可照抄的「解锁」代码。旧实现还**没有**显式「没有更多帖子」文案信号（`explicit_end` 是迁移时新加的能力）。
→ 正确做法不是照抄，而是把新引擎里已有的到底确认从 home-only 解锁到全部列表面。

### ⑤ 文本校验口径 —— `direct`，但这是**裁决题不是补缺题**
旧的两条链路口径**本来就不一样**，而且**评论侧比发布侧更宽**：评论只查子串包含、无长度上限、只查一次；
发布查包含 + 4 字符多余量上限。新引擎把评论侧收成「归一后逐字相等、提交前查三次」，把发布侧容差从 4 放到 10。
**照抄旧评论口径（纯包含、查一次）的后果**：会同时丢掉新引擎新加的 typeahead / @提及污染防护与提交窗口内的目标漂移检测。

### 行号勘误（本次实读核对）
- `comment-executor.ts` 的 `buildMarkerAcceptedJs`：参照数据写 `:1202-1208`，**实读在 `:1208-1215`**（注释 1208、函数体 1209-1215）。
- `comment-executor.ts` 的 `buildEditorContainsFragmentsJs`：参照数据写 `:1211-1219`，**实读在 `:1216-1224`**（函数签名 1217）。
- `cta-labels.ts` 写 `:100-155`，**该文件只有 139 行**；Node 侧正则从 `:100` 起、数字守卫注释在 `:124`，实际范围应为 `:100-139`。
- 其余抽查（`feed-reader.ts:203-206`/`:148`/`:519`、`consent.ts:16`/`:67-80`/`:141-148`/`:163-167`、`facebook-session.ts:186-198`、`publish-executor.ts:226-236`/`:692-703`、`cta-labels.ts:19-28`、`comment.rs:82-126`、`runtime.rs:338-388`）**逐条对得上**。

---

## 逐条参照

### ① 首页卡片互动热度恒为 0
- **对应任务**：1.1、1.2、1.4、1.5（边缘取数）；7.1、7.2、7.3、7.4（云端门槛）；9.4、9.4b（真机采样）
- **旧实现**：`aidcp-edge/src/facebook/feed-reader.ts:203-206`（抽数逻辑）、`:148`（计数解析器 `parseFacebookCount`）、`:519`（映射）；
  `aidcp-edge/src/facebook/cta-labels.ts:18-29`（控件语义源串）、`:100-139`（Node 侧正则与数字守卫，两代都靠它区分 toggle 与汇总）
  — 旧实现把「点赞 toggle」与「反应计数汇总控件」当成**两类东西**。抽热度时遍历卡内所有带 aria-label 的按钮，
  命中条件是两条 **AND**：标签以 赞/讚/Like/Me gusta/Thích 开头，**且**标签或渲染文案里至少有一个数字。
  没数字的纯 toggle 因此被**跳过、继续往下找**，直到找到真正带数字的那一个；取值优先用渲染文案、文案为空才退回标签。
  数字再交给专门的计数解析器（认千分位、K、M、万/萬/w），解析不出就落 0。
  同一份控件语义还被点赞执行器**反向复用**：那边用「有数字」当**排除**条件，防止把「任何已有反应的帖子」误判成已赞。
  收藏数是另一条独立决定：Facebook 没有收藏概念，一律诚实 0，明文禁止拿反应数冒充。
- **旧代码记下的真机经验**：
  > 反应数取「赞」计数汇总按钮（带数字，非 toggle）。

  > Facebook 无「收藏」概念——collect 一律诚实缺省 0（design 决策），绝不用反应数冒充。

  > 解析 Facebook 反应计数文案："3,829" / "1.2K" / "3.4M" / "1.2万"。抓不到/空 → 0（绝不臆造）。

  > // 反应计数：帖级动作栏「赞」计数汇总按钮（aria-label 以 赞/Like 开头且带数字文案）。

  > if (!permalink) continue; // 无可开链接 → 不作候选（诚实）

  > *  - 帖级「点赞动作」按钮 = `[role=button][aria-label="留下心情"]` 或 `[aria-label="给<作者>的帖子留下心情"]`（zh-CN），**文案为空**；单击即「赞/Like」。它与「赞：N」反应【计数汇总】按钮、以及反应项「给<作者>的帖子留下心情：赞」不同——后两者不是 toggle。

  > * Facebook 的本地化 UI 有两种都真实存在的计数布局：汇总按钮自己显示数字，或真正的点赞动作按钮在同一按钮内显示数字。因此数字只能描述呈现，不能单独决定“动作/汇总”。Feed 身份与 like 执行器注入同一份 helper，避免扫描能认、执行器不能点（或反之）的漂移。

  > * 【数字守卫】反应【计数汇总】按钮 aria-label 亦是「赞/Like」但带**数字文案**（如「3,829」），它不是点赞 toggle（探针 §Action bar item①）；必须排除，否则会把「任何已有反应的帖子」误判为已赞（同 feed-reader 的 /\d/ 守卫）。
- **新引擎现状**：`native/page-engine/src/facebook-router/08-reaction-semantics.js:28-31`（`reactionButton`）；
  取数三处 `20-feed.js:12`（feed 卡）、`:117`（群首帖卡）、`:243`（详情页）；
  点赞侧 `10-feed-like.js:3-6, :20-35`（已把汇总 toolbar 排除掉）；计数解析器 `00-shared.js:23-29`
- **具体缺哪几样**：
  1. 缺「必须含数字才采信」这道筛：`reactionButton` 只做标签前缀匹配、取 DOM 序**第一个**命中项，没有 `/\d/` 条件。真机常见版式里第一个命中的就是无文案的纯 toggle（`aria-label=赞`，innerText 为空）。
  2. 缺「找不到就继续往下找」的循环语义：`find()` 一命中即返回，不会跨过 toggle 去找带数字的汇总控件。
  3. 缺计数控件的**独立选择器**：全局只有一个 `reactionButton`，同时被点赞分支（`90-dispatch.js`）与三处 `likeCount` 复用。它**必须继续返回 toggle** 才点得动赞——所以修法不能改 `reactionButton`，只能**新增**一个「计数承载控件」选择器（正是 task 1.1 的形状）。
  4. 缺汇总控件的**可达性**：`10-feed-like.js:3-6` 的 `insideReactionSummary` 把 `[role=toolbar]` 内的控件显式排除（点赞侧正确），而扫卡侧从不查 toolbar —— 数字所在的那个控件在新引擎里**两条路都到不了**。
  5. 取值口径 `text(reaction,96)||label(reaction,96)` 本身对（文案优先、空退标签），但因为选中的是无文案 toggle，text 为空 → 退回 label `'赞'` → `count('赞')=0`。三处同一个 0。
  6. **不是缺口、别改**：`collectCount:0` 与旧实现一致（旧是不产出该字段、云端补 0；新是显式 0）；计数解析器 `00-shared.js:23-29` 与旧 `parseFacebookCount` 同覆盖（千分位/k/m/万/萬/w）。
- **可 port 的旧测试**：
  - `test/facebook/feed-reader.test.ts`『parseFacebookCount: 千分位/K/M/万/空/非数字』——锁解析口径：`3,829→3829`、`1.2K→1200`、`3.4M→3400000`、`1.2万→12000`、空/null/`'赞'→0`。可直接对 `00-shared.js` 的 `count()` 建契约测试。
  - 同文件『fb-feed: 跳过未水合空壳 + 无 permalink 卡，映射字段，去重』——锁 `reactionText='3,829'→3829`、`reactionText=null→0`（诚实置 0 而非臆造）、无 permalink 卡不作候选；并断言卡上**没有** collect 字段。
  - 同文件『fb-feed[jsdom]: 真 feed 内轻量视频允许动作按钮内含数字，并排除越南语汇总 toolbar』——真机形态：动作栏 `aria-label="Thích"` 文案 `866` + toolbar 里 `aria-label="Thích: 825 người"`，期望 `reactionCount=866`。**这条是新引擎最直接的红灯用例。**
  - 同文件『fb-feed[jsdom]: 支持语言共用动作栏分类，数字汇总 toolbar 不成为第二个 react 控件』『fb-feed[jsdom]: 数字 reaction word 只有汇总结构时不证明视频卡动作边界』。
  - `test/facebook/cta-labels.test.ts`『反应【计数汇总】按钮（aria-label=赞 + 数字文案）绝不误判已赞（数字守卫）』——锁数字守卫的**反向**用法，保证新增计数选择器时不把点赞态判错（正对 task 1.1 的验收）。
  - 同文件『已反应态判定（正向信号才算，绝不「变了就算」）』——锁「不确定即判未反应」。

---

### ② 评论入口从不点击（折叠态必然失败）
> ⚠️ `also-wrong`，先读文首那段。旧代码没有可照抄的点击逻辑。

- **对应任务**：2.1、2.2、2.3、2.6；9.7（真机确认点击后编辑框出现时延与重探轮次预算）
- **旧实现**：`aidcp-edge/src/facebook/comment-executor.ts:929-935`（`focusEditorWithScroll`，只滚不点）、
  `:633-679`（`openPost`：permalink 直驱导航 + 有界催拉）、`:11`（红线注释）、
  `:251-254`/`:270-274`（催拉轮数 6 / 距离 700px 及预算说明）、`:946-955`（`scrollViewport` 复用 FB 惯性手势）
  — 旧评论执行器的编辑框获取**只有一种手段**：有界滚动催拉。它把「按 permalink 整页导航到帖子详情页」当**前置条件**——
  导航完成后先等详情 article 水合，再按 canonical 帖身份把编辑框**收窄到目标帖**，收不到就滚一屏再探，
  最多 6 轮、每轮 700px 的惯性 wheel 手势。6 轮滚完仍探不到，诚实报 `editor_not_found`、绝不硬提交。
  作用域内 0 个编辑框时**明文禁止**回落到 document 第一个编辑框（防评错帖）。
  换句话说：**旧实现用「换页面」绕开了折叠态，而不是用「点开」解决折叠态。**
- **旧代码记下的真机经验**：
  > // - 懒加载评论框（F1 补丁①）：提交前有界滚动催出视口外的评论框，滚不出即 `editor_not_found`、不硬提交。

  > * 催拉 + 聚焦**目标帖作用域内**的评论框；返回 reason 表示失败（editor_not_found / permission_gated）。作用域内 0 个评论框 → editor_not_found，**绝不回落 document 第一个编辑框**（红线：不评错帖）。

  > * 按 permalink 直驱开帖 + 有界催拉懒加载评论框（F1 补丁①）。返回 editorReady=true 表示视口内已探到评论框（可进入提交）。

  > // - surfaceProbeRounds 的调用点（搜索候选 / 群首帖 / 评论框催拉）都跑在 editorScrollRounds=6 的循环**内**，

  > /** 视口滚动催拉懒加载：复用 FB 惯性手势，且不在 wheel 已生效后双滚。 */
- **新引擎现状**：`native/page-engine/src/facebook/comment.rs:82-126`（只滚不点的 6 轮循环）；
  **已写好但未被评论主路复用**的点击闸在 `native/page-engine/src/facebook/runtime.rs:338-388`（`wait_for_first_post_editor`），
  其唯一调用点 `runtime.rs:168`；页内探针 `facebook-router/50-comment.js:2-16`（`commentActionProbe`）与路由 `90-dispatch.js:20`
- **具体缺哪几样**：
  1. 缺「探不到编辑框时点一次评论 CTA」：`comment.rs:83-116` 的 6 轮循环里唯一动作是 `dispatch_wheel_humanized`，**没有任何 click**。
  2. 这个能力**新引擎里已经写好了、只是没接到评论主路**：`runtime.rs:338-388` 完整实现了「`editor_not_found` → 探 `comment_action_probe` → 点它 → 立刻重探」，且**只探一次**（`action_probed` 幂等标志）。`comment.rs` 从头到尾没调用 `probe_facebook_comment_action`。**task 2.1 的「镜像 runtime.rs」是照着这段抄，不是照旧 TS 抄。**
  3. 缺 permalink 前置导航：旧路径的折叠态豁免来自 `openPost` 的整页导航，`comment.rs` 直接在当前页探编辑框，既不导航也不点开。
  4. 缺「点开后按 ambiguous / pending_group_approval 分诊」：`runtime.rs:362-367` 已把探针的 `ambiguous_target` / `pending_group_approval` / `target_context_mismatch` 分开映射；`comment.rs:117-126` 的失败面只有 `editor_not_found` 一档（把 `editor.reason` 原样吐出）。这正是 task 2.2 要补的。
  5. **不是缺口**：滚动参数已对齐（新 6 轮 × 650px vs 旧 6 轮 × 700px；每轮 sleep 500ms 对旧 500ms）。
  6. **别误改的 legacy 死路**：`90-dispatch.js` 的 `interaction_comment` 分支（router 内联评论）也只找 `commentEditor`、不点 CTA；FB 的评论命令由 `comment.rs` 接管，该分支对 FB **已不可达**，改它不等于改好了。
- **可 port 的旧测试**：
  - `test/facebook/comment-executor.test.ts`『评论框在首屏下、滚动催拉后就绪（F1 补丁①）』——锁「首轮探不到、滚动后探到 → 继续提交」。
  - 同文件『评论框始终催不出 → ok:true 但 editorReady:false』——锁「催不出不谎报就绪」。
  - 同文件『评论框催不出 → editor_not_found，不提交』——可直接 port 成 `comment.rs` 的「未开始」契约（task 2.3）。
  - 同文件『群首页先停在封面时有界滚动催拉首帖，不改走搜索』——锁「有界催拉不越界改路线」。
  - 同文件『群问答门槛（permissionGated）→ 不提交』与『评论框标签识别覆盖真机变体与多语言（回归 发表公开评论 漏配 → 评论从未发出）』——后者是真机回归用例，覆盖 CTA 与编辑框两侧词表。
  - `test/facebook/editor-probe.test.ts` / `comment-executor.test.ts` 的 **fb-editor-scope 全组**（『多编辑框页面 → 只命中目标帖 article 内的编辑框（绝不回落 document 第一个）』『目标帖不在页面上 → 空』『排他区域里出现多个候选编辑框 → 空（诚实 editor_not_found，绝不取第一个）』『弹层里开目标帖、背后 feed 还有别人的帖 → 绝不把评论打进别人帖子的输入框（红线回归）』）——**点开 CTA 后新出现的编辑框必须仍受同一套作用域收窄，这组是必须一起 port 的护栏。**

---

### ③ Cookie 同意策略与失败分档
- **对应任务**：**本 change 无对应任务 —— 见文末覆盖漏洞（这是本参照书发现的最大漏洞）**
- **旧实现**：`aidcp-edge/src/facebook/consent.ts:16`（策略枚举）、`:67-80`（`present` 纯判定）、`:141-148`（env 读取）、
  `:163-167`（`pickButton`）、`:175-225`（accept 主循环，含 `:188-195` 探测失败降级 / `:200-206` no_target / `:223-224` 升级）
  — 旧实现把同意条处理拆成「采集信号 → 纯判定 → 按策略挑按钮 → 点 → 复探 → 有界升级」六段，
  回执是**四元组**：探到没探到（handled）、清没清掉（cleared）、点了几次（attempts）、失败原因（`no_target` 还是 `blocked_by_consent`）。
  存在性判定要求**四条同时成立**：有 cookie 政策文案、**至少有一个可点的接受按钮**、不在登录类 URL、页面无验证码特征；
  验证码与登录门优先级高于同意条，命中就一律判「不是同意条」交给既有闸。
  策略所需按钮缺失时返回空、上层报 `no_target`——明文禁止改点另一个按钮。
  探测本身抛错时**既不假设有同意条也不假成功**，当作「无同意条」让流程照常继续。
  点完必须复探确认横幅消失才算成功；到重试上限仍在，停手升级成 `blocked_by_consent`。
  按钮采集**在整个 document 上做**，取**首个命中**。
- **旧代码记下的真机经验**：
  > *  - 只对被识别为同意条的浮层动手：命中 cookie 政策文案 + cookie 接受按钮 + 非登录/验证 URL + 非验证码。

  > *    真登录门（有「登录 Facebook」字样但无 cookie 接受按钮）、验证码天然被排除，绝不误点。

  > *  - 后置校验：点完复探确认横幅消失方判成功；找不到按钮 → no_target，绝不乱点其他按钮。

  > *  - 有界重试：到上限仍在 → blocked_by_consent 停手升级，绝不静默假成功。

  > * 优先级铁律：验证码 / 登录门优先——onLoginUrl 或 captchaLike 时一律 present=false（让既有闸处置）。

  > * present 需同时满足：有 cookie 政策文案 + 至少一个 cookie 接受按钮 + 非登录 URL + 非验证码。

  > /** 读 env 决定接受策略（默认 accept_all）。necessary_only 只在显式配置时启用。 */

  > /** 按策略挑接受按钮：策略要求的按钮缺失 → null（诚实 no_target，绝不改点另一个）。 */

  > // 探测失败：不假设有同意条、也不假成功——当作无同意条让既有闸继续处置。

  > // 认出同意条但策略所需按钮定位失败（文案/布局漂移）——诚实 no_target，绝不乱点。

  > // 到上限仍在——停手升级，绝不静默假成功。
- **新引擎现状**：`facebook-router/05-session.js:10-29`（`consentProbe`，含 `:18` 的作用域、`:22` 的 present 门、`:25-28` 的唯一性/歧义）；
  `native/page-engine/src/facebook/shared.rs:399-465`（`ensure_facebook_action_gate_inner`：`:418-424` present、`:426-444` 策略选点、`:445-452` 与 `:455-462` 的失败出口）；
  仅报不点的两处 `10-feed-like.js:122, :165`
- **具体缺哪几样**：
  1. **新引入的作用域自伤（最严重）**：`05-session.js:18` 把按钮采集框到 `first(['[role="dialog"]','[aria-modal="true"]'])||document` —— 取的是**首个可见 dialog，不校验它是否含 cookie 文案**。FB 同意条常是**非 dialog 的底部横幅**，而 FB 首页常年挂良性 dialog（聊天弹窗 / 加载浮层，旧 `feed-reader.ts:349-354` 记录过同一现象）；scope 一落到那个良性 dialog，同意按钮就永远采不到 → `present=true` 且两个点位都是 `null` → **每个受闸动作（评论 / 点赞 / 发帖 / 加群 / 滚动 / 刷新）都变成 `blocked_by_consent`**。旧实现在整个 document 上采集，没有这个失效模式。
  2. 缺 present 门里的「**至少一个按钮**」条件：`05-session.js:22` 的 present 只要 `cookieCopy && !captcha && !loginPath`。后果是 cookie 文案在页但按钮词表全 miss 时，旧实现返回 `handled=false` 让流程照常继续，新实现把**所有**受闸动作一律判 `blocked_by_consent`。
  3. 缺 `no_target` / `blocked_by_consent` 分档：`shared.rs:445-452` 把「策略所需按钮定位不到」与「点了三次清不掉」折叠成同一个 `blocked_by_consent`。旧实现明文把前者做成 `no_target`（布局 / 文案漂移，可诊断），后者做成 `blocked_by_consent`（升级停手）。
  4. 缺探测失败的降级：旧实现 detect 抛错 → 当无同意条继续；新实现 `probe_facebook_consent` 的错误直接经 `?` 上抛（`shared.rs:419-421, :455-458`），整条命令变成引擎错误。
  5. 缺「取首个命中」的宽容：`05-session.js:25-26` 要求命中数**恰好 1**，`>1` 只置 ambiguous 标志且不给点位（`shared.rs:435-443` 据此放弃点击）。旧实现取首个命中即用。FB 同意横幅在多语言并存 / 多容器渲染时出现两个同文案按钮就直接卡死。
  6. 缺回执可观测性：旧实现返回 handled / cleared / attempts / reason；新实现只有 present + 两个点位 + 两个歧义标志，尝试次数与「探到了但没清掉」在回执里不可分。
  7. **不是缺口、别重做**：策略枚举与 env 键名已对齐（`accept_all` 默认，`necessary_only`/`necessary`/`essential` 三别名）；验证码优先、登录门优先、点后复探、有界三次重试也都在。
- **可 port 的旧测试**：
  - `test/facebook/consent.test.ts`『accept: required button missing for policy is honest no_target, never clicks the other』——**本条最核心的可 port 用例**。
  - 同文件『accept: detect failure is treated as no consent (never fake success)』——锁探测失败降级，而不是把整条命令炸掉。
  - 同文件『accept: banner that never clears escalates blocked_by_consent within bounded attempts』——锁有界重试与升级语义。
  - 同文件『accept: necessary_only policy clicks the essential-only button』『accept: accept_all clicks the allow-all button and confirms cleared』。
  - 同文件『consent classify: no accept button means not present (never mis-click)』——**直接锁 present 门必须含「至少一个按钮」，是 `05-session.js:22` 的红灯用例。**
  - 同文件『banner text mentioning 登录 Facebook is still consent, not login』『real login/checkpoint url is never consent even with cookie copy』『captcha-like page is never consent』——锁优先级铁律三态，**修 scope 时不能把登录门 / 验证码放进来**。
  - 同文件『policy from env: defaults to accept_all』『necessary_only variants』——锁 env 键名与别名集合。
  - `test/facebook/comment-executor.test.ts`『cookie 同意浮层清不掉 → blocked_by_consent（先于阻断判定）』——锁同意闸在阻断判定之前跑。

---

### ④ 小组页/搜索页滚到底被上报成「找不到目标」
> `direct`，但旧实现「面无关」、没有可照抄的解锁代码；也**没有** `explicit_end` 文案信号（那是迁移时新加的）。

- **对应任务**：4.1、4.1b、4.2、4.3、4.4、4.5；4B.1、4B.2、4B.3、4B.4；9.9
- **旧实现**：`aidcp-edge/src/facebook/facebook-session.ts:1008-1098`（`scrollFeed` 全段）、阈值常量 `:186-198`；
  面白名单 `aidcp-edge/src/facebook/feed-reader.ts:106-109`（`isFacebookListSurface = home | search | group`）
  — 旧滚动循环每轮先量一次滚动位置 / 内容总高 / 视口高，滚一屏，判稳扫卡，再量一次。有新卡就上报走人。
  0 新卡时分两种：内容总高还在长（**超过阈值增量**）或还没接近底部 → 判「懒加载还在长 / 没到底」，继续下滚，**绝不当到底**；
  高度稳定 + 接近底部 + 0 新卡 → 只算一次「到底候选」，要**连续两轮**都满足、且这次命令里**至少见过一张卡**，
  才诚实报 `feed_exhausted`（云端据此换批 / 刷新）。
  轮数耗尽时再分：整段从没见过任何卡 → 报判稳给出的真实原因、兜底 `no_target`；见过卡但没确认到底 → **仍报 `feed_exhausted` 换批**。
  而「严格确认首页空态」这一路**明文只对 canonical 首页开放**——也就是说旧实现把 home-only 的限制
  **只**加在「空态确认」上，**从不**加在「到底判定」上。（这正是 task 4.5 保留首页空态确认的立论来源。）
- **旧代码记下的真机经验**：
  > * page.scroll 单条命令内有界续滚上限：本次 0 新卡时最多再滚几次找下沉的新卡（FB 懒加载 + 虚拟化需要时间渲染下一批）。

  > * 从旧值 2 提到 8——给懒加载足够时间把下一批渲染出来，避免「滚两下没冒新卡就误判到底、立刻刷新回顶」的换批抖动。

  > * 单条命令兜底超时 90s、每轮 ~5s，8 轮 ≤ ~45s 安全在预算内。

  > /** 判「真到底」需连续满足「高度稳定 + 接近底部 + 0 新卡」的轮数（连续确认防抖，绝不单轮误判到底）。 */

  > /** scrollHeight 视为「FB 懒加载又长出内容」的最小增量（像素）——只要页面在长就继续下滚、绝不判到底。 */

  > /** 距内容底部小于此值（像素）视为「接近底部」——FB 通常在触底前就懒加载，故留约一屏余量提前判定。 */

  > * 现在：本轮 0 新卡时，只有「页面高度不再增长（懒加载没在长）**且**已接近底部**且**连续确认」才诚实 `feed_exhausted`（云端映射为 refresh）；只要页面还在长或还没到底就继续下滚找下沉的新卡。让 60 篇深度阈值（云端 FeedScroller）成为换批主路。绝不把回收重现当新内容重复上报，绝不在还有内容时假判到底。

  > // 页面在长（FB 懒加载中）或还没滚到底 → 继续下滚找下沉的新卡，绝不当到底。

  > // 高度稳定 + 接近底部 + 0 新卡 → 真到底候选，连续确认防抖后才诚实 feed_exhausted。

  > // 仅 canonical 首页可达，搜索/群组/unknown 绝不套用。
- **新引擎现状**：`native/page-engine/src/facebook/feed.rs:169-230`（`execute_facebook_feed_scroll`）；
  home-only 三处硬闸 `:203`、`:425-426`、`:475-486`；到底确认 `:444-473` 与 `:416-442`；
  阈值 `:409-414`（高度增长）与 `:618-622`（接近底部）；
  入口 `native/page-engine/src/facebook/reels.rs:175-185`（非 Reels 面一律转 `execute_facebook_feed_scroll`，群 / 搜索都走这里）
- **具体缺哪几样**：
  1. 缺「到底确认对搜索 / 群组开放」：`feed.rs:203` 的分支条件里带 `|| after.surface != "home"` —— 非首页面永远 `continue`，一次都进不了 `confirm_facebook_feed_bottom`。（task 4.1）
  2. 缺「到底态分类对搜索 / 群组开放」：`feed.rs:425-426` 的 invalidated 要求 initial 与 current 的 surface **都**是 home，否则直接判 `Invalidated` → 永远拿不到 `ExplicitEnd`（`feed_exhausted`）或 `WindowStable`（`feed_continuation_unconfirmed`）。（task 4.1b —— **只改 4.1 是空动作**）
  3. 缺「轮次耗尽时的诚实原因」：`feed.rs:475-486` 的 `facebook_unconfirmed_scroll_reason` 只在 `saw_any_card` **且** `surface=="home"` 时给 `feed_continuation_unconfirmed`，其余一律 `no_target`。搜索 / 群组滚满 8 轮后即使全程有卡也报 `no_target`。（task 4.2）
  4. 后果具体化：云端把 `feed_exhausted` 映射为换批 / 刷新、`feed_continuation_unconfirmed` 映射为再滚一次（`../aidcp-cloud/src/orchestrator/role-dispatcher.ts:3624-3646`），而 `no_target` 是**死胡同**——搜索 / 群组滚到底后调度器拿不到任何可执行语义。
  5. **把「高度增长阈值 100px」换成了 1px**：`feed.rs:409-414` 判 `after.scroll_height > before.scroll_height + 1.0`。旧实现明文取 **100px**，理由是「只要页面在长就继续下滚」需要一个**抗噪阈值**；1px 会让任何 reflow 都算「还在长」，**即便首页也难走到到底确认**。→ tasks 里无人认领，见文末覆盖漏洞。
  6. 把「连续两轮确认」换成「时间窗 + 连续两次显式文案样本」：`feed.rs:435` 要求 `explicit_end_samples>=2` 才给 `feed_exhausted`，否则窗口到点给 `feed_continuation_unconfirmed`（`:377-387`）。语义不同但可接受；关键是这两档在非首页面上都拿不到。
  7. **新增能力，别当缺口**：显式「没有更多帖子」文案信号 `explicit_end`（`20-feed.js:179-181` 只判 title，`explicit_empty` 才要 title && hint）。旧实现只有 `explicitEmpty`、没有 `explicitEnd`。解锁 home-only 时**这条文案信号对群 / 搜索面是否有对应文案需真机坐实**（task 9.9 附近）。
- **可 port 的旧测试**：
  - `test/facebook/facebook-session.test.ts`『page.scroll 高度稳定且接近底部、连续无新卡 → 诚实 feed_exhausted 换批（真到底才刷新）』——用例 metrics 为 `scrollY=5000 / scrollHeight=5900 / innerHeight=900`（remaining=0）。**把桩换成 surface=group/search 就是新引擎的红灯用例**（正对 task 4.4）。
  - 同文件『懒加载还在长内容 / 未到底时绝不提前判到底：续滚到出新卡才上报（不刷新回顶）』——锁「还在长 / 没到底时绝不报 feed_exhausted」，同时是 **1px 阈值的反例来源**。
  - 同文件『首页从未出现真卡时 page.scroll 不得误报 feed_exhausted，并可严格复确认空态』——锁「从未见卡不能声称刷到底」这条补集判据，**解锁 home-only 时不能顺手放宽它**（正对 task 4.5）。
  - 同文件『FB scroll 在搜索详情页时回到原搜索结果，不误跳首页』『navigation.back 从搜索结果开帖后回落搜索页而非会话初始首页（修 split-brain）』——锁「活跃列表面不恒等于首页」，**正是 home-only 硬闸的立论错误所在**。
  - 同文件『普通浏览 search.execute 搜索页无卡 → no_results 成功终态』——锁搜索面 0 卡的终态口径（`no_results`，不是 `no_target`）。
  - `test/facebook/feed-reader.test.ts`『ensureFeed 幂等：搜索页放行搜索、不被带回首页』——锁 home/search/group 三面都是合法可滚列表面。
  - 同文件 settleCards 四条（『集合连续两轮相等且无 loading 才上报（loading 是单向继续等否决票）』『触达 wall-clock 仍 loading 但有真卡 → 照实上报 + degraded（非假成功）』『触达上限 0 卡 + 仍 loading → feed_still_loading 可重试（不报空批）』『触达上限 0 真卡（只有空壳）+ 无 loading → no_feed（空壳绝不当卡）』）——**`feed_still_loading` / `no_feed` / `no_target` 分档的契约来源**，4B.4 的覆盖式断言可拿它当清单。

---

### ⑤ 文本校验口径：评论逐字相等 vs 发布包含+容差
> `direct`，但这是**裁决题**：旧评论侧比旧发布侧更宽，照抄旧评论口径会丢掉新引擎新加的污染防护。

- **对应任务**：2.4、2.5、2.6；9.8（真机采样编辑器补入的不可见字符量，据此定容差）
- **旧实现**：评论侧 `aidcp-edge/src/facebook/comment-executor.ts:1208-1215`（`buildMarkerAcceptedJs`，子串包含 —— **行号已勘误**）、
  `:1216-1224`（`buildEditorContainsFragmentsJs`，片段包含 —— **行号已勘误**）、`:304-310`（`textFragment` 取前 60 字）、
  `:778-799`（输入 → 验收 → 追加联系方式 → 再验收）；
  发布侧 `aidcp-edge/src/facebook/publish-executor.ts:226-236`（归一函数 + 容差常量 **4**）、`:692-703`（回读 + 包含 + 容差判定）
  — **评论侧**：逐字符拟人输入正文后，在目标帖作用域内的编辑器里读**一次**全文，判它**包含**提交正文（trim 后）即验收通过；
  不做长度上限、不做归一后相等、不重复查。若带联系方式，再**逐字符**追加换行 + 联系方式，
  然后按「正文前 60 字片段 + 联系方式前 60 字片段」**两个片段都包含**来验收。
  之后是一次新鲜的验证码 / 登录复检，再是最后一个取消点，然后回车；**回车前不再重读编辑器全文**。
  **发布侧**：归一（折叠空白、去首尾）后要求编辑器全文**包含**期望正文，且多出来的字符数**不得超过 4**；
  超过就判正文被污染、清场、绝不发出去。发布侧还明文承认「编辑器已找到但焦点未落在其上，继续输入，**以全文回读为准**」——
  即**以回读为唯一权威、不靠焦点断言**。
- **旧代码记下的真机经验**：
  > /** 受控输入后校验 marker 已被编辑器接受（**目标帖作用域内**的编辑器文本含该片段）。 */

  > // 真机探针实证：正文逐字输入后，再用单次 Input.insertText 灌入 "\n+联系方式" 会被 FB/React

  > // 编辑器吞掉整段；换行和联系方式逐字符输入可稳定进入编辑器。

  > /** 与页面侧 fbPublishText 同口径归一（折叠空白、去首尾），供全文比对。 */

  > * 允许的「多出来的字符数」。编辑器可能带入零宽字符/不间断空格之类的无害残留；

  > * 超出这个容差就是真被塞了东西（如打字途中被 typeahead 劫持插入了 @提及），

  > * 那样的正文 MUST NOT 发出去。

  > this.log('[facebook-publish] 编辑器已找到但焦点未落在其上，继续输入，以全文回读为准');

  > // 状态判别前要剥掉的**完整**正文（非 60 字片段）——评论行 innerText 含我们自己的正文，不剥就会把「正文里含『已拒绝』的正常评论」误判成被拒 → 成功报失败 → 不打去重 → 下轮同帖**再发一条真评论**（平台可见重复），正是本 change 要堵的洞，绝不能自己造一个。
- **新引擎现状**：评论侧 `native/page-engine/src/facebook/comment.rs:199-220`（打字后回读，3s 预算轮询）、
  `:245-259`（提交窗口内二次比对 → `target_moved_before_commit`）、`:275-292`（回车前三次比对 → `comment_editor_focus_failed`）、
  `:405-427`（`facebook_comment_editor_matches`）；归一函数 `native/page-engine/src/facebook/shared.rs:270-272`；
  发布侧 `native/page-engine/src/facebook/publish.rs:19`（容差 **10**）、`:700-736`（包含 + 容差）；
  legacy 死路 `facebook-router/90-dispatch.js:139`
- **具体缺哪几样**：
  1. 评论侧把「包含」换成「**归一后逐字相等**」：`comment.rs:405-427` 用 `normalize_facebook_text(value) == expected`；而 `shared.rs:270-272` 的归一**只做 `split_whitespace` + `join(" ")`，不去零宽字符、不做 Unicode 归一化**。FB 的 Lexical 编辑器带入的零宽字符 / 不间断空格会直接让相等判定失败 → `marker_not_accepted`。**这是评论侧失败的直接机制。**
  2. 评论侧把「查一次」换成「提交前查三次」：打字后（`:199-205`，3s 轮询）、进提交窗口后（`:245-249`）、回车前聚焦时（`:275-282`）。三次全用同一条相等判据，任一次不等就清场 + 诚实非成功，原因分别是 `marker_not_accepted` / `target_moved_before_commit` / `comment_editor_focus_failed`。**task 2.4 要求三处收成同一个共享谓词——三次检查本身是新引擎的增益，别在收谓词时把它砍掉。**
  3. 评论侧缺「**多余字符容差**」这一维度：相等判据下「多了 1 个零宽字符」和「被 typeahead 插了一整个 @提及」得到**同一个结果**，运营看到的失败原因分不出「无害残留」与「正文被污染」。旧发布侧那条注释正是为区分这两者写的。
  4. 评论侧缺「联系方式**分两段追加 + 片段包含验收**」：新版把正文与群号在 Rust 侧拼成一个字符串（`comment.rs:72-80` 的 `format!("{body}\n{code}")`）一次性打完。旧实现的真机经验「换行 + 联系方式必须逐字符输入」被新版的 `type_text_humanized` 满足了；**但「分两段各自验收」这层分诊没了**——吞掉整段时新版只会报一个笼统的 `marker_not_accepted`。
  5. 评论侧缺「取前 60 字片段」的宽容：旧实现对联系方式段用 `textFragment`（前 60 字）做包含判定，新版对全串做相等判定。
  6. 发布侧容差 **4 → 10**：`publish.rs:19` 的 `FACEBOOK_PUBLISH_FILL_EXTRA_CHAR_TOLERANCE = 10`，旧 `publish-executor.ts:236` 是 4。**旧值有明确立论**（零宽 / 不间断空格是无害残留，超出即被 typeahead 塞了 @提及），**10 这个值没有对应记录**，等于把 @提及污染的检出门抬高了 6 个字符。task 2.4 说「取同一常量或显式声明差异理由」——**裁决时应知道只有 4 有立论**。
  7. **不是缺口**：发布侧「包含 + 容差」的结构与归一口径已对齐（`publish.rs:727-736` vs `publish-executor.ts:698-703`）。
  8. **别误改的 legacy 死路**：`90-dispatch.js:139` 的 router 内联评论用 `norm(read)!==norm(value)` 相等判据 + `editor_readback_mismatch`。FB 评论由 `comment.rs` 接管，该分支不可达。
- **可 port 的旧测试**：
  - `test/facebook/comment-executor.test.ts`『受控输入未被接受 → marker_not_accepted，不提交』——**三次比对全部要保住的底线**。
  - 同文件『联系方式逐字符追加并验收，避免换行+联系方式整段 bulk 被 FB 吞掉』——锁真机经验，可 port 成新引擎的输入方式契约。
  - 同文件『联系方式追加后未被编辑器验收 → 不提交，避免裸发正文』——锁「只有正文进去、联系方式没进去时绝不发」这一档**独立失败面，新版目前没有对应分档**。
  - 同文件『提交前验证码 fresh 复检命中 → blocked_by_captcha，不提交』——锁提交前复检与文本校验的先后顺序。
  - 同文件『本人 id 未知 → identity_unknown，绝不提交（不点击）』——锁「宁可不发也不发了无法确认」，与三次比对同属提交前闸序。
  - `test/facebook/publish-executor.test.ts`『云端下发的预算够用时，长正文能完整打完并通过全文回读』——可作 **4 vs 10 容差裁决的基准用例**（现有测试里**没有**直接锁 `content_polluted` 的用例，要固化容差值需新写，正对 task 2.6）。
  - 同文件『opens composer, fills content, uploads image, submits, and captures post id』——发布链路端到端口径基准。

---

### ⑥ 反应/评论控件标签的兼容形·分解形不识别（两代共有盲区）
> ⚠️ `also-wrong`，先读文首那段。**本 change 只登记不修（task 9.10）**，但修 ① 时必须避免把盲区带进新代码。

- **对应任务**：9.10（**只登记、不修**）；对 ① 的新增见证解析有**约束性影响**，但 tasks 1.1 未写入 —— 见文末覆盖漏洞
- **旧实现**：`aidcp-edge/src/facebook/cta-labels.ts:18-29`（五条标签正则源串，含**手工并列**的 ASCII 折叠写法）、
  `:96-98`（`norm` 只折叠空白、不做 Unicode 归一）；对比 `aidcp-edge/src/facebook/feed-reader.ts:257`（**唯一**做 NFD 的地方，只用于空态文案）
  — 旧实现把五类反应控件语义（中性点赞、帖级评论、已反应词、撤销反应、反应选择器）各做成一条正则源串，
  同一份源串既喂给页内脚本也喂给可单测的 Node 侧断言，避免两份漂移。归一**只做一件事**：折叠连续空白、去首尾。
  多语言覆盖靠在词表里**逐条并列写法**——越南语并列了 `Thích` / `Bày tỏ cảm xúc Thích` 与 ASCII 折叠的 `Bay to cam xuc Thich` 两套；
  西语并列了 `Me gusta` / `Me encanta`。**没有任何 `normalize('NFD')` 或 NFC 归一，也没有去变音符后再比。**
- **旧代码记下的真机经验**：
  > * aria-label 是主锚点，绝不用自由文本命中（避免 feed 正文里的「Like」误配，见 comment-executor 的 CHROME 噪声）。多语言覆盖 zh-CN / zh-TW / en / es（本项目现役界面语言）。

  > * 红线：不确定即判「未反应」——绝不把「不确定」当「已赞」冒充成功（MUST NOT 静默假成功）。

  > * 已赞态确切串真机未拿到（留待 shadow task 8.2 收紧）；已知：react 后该按钮的**空文案会变成反应词**（中文实测变「赞」蓝字），或 aria-label 变「取消赞 / Remove Like」类「撤销」串。
- **新引擎现状**：`facebook-router/08-reaction-semantics.js:1-7`（七条标签正则，**逐字继承旧词表含 ASCII 折叠写法**）、`:28-31`（`reactionButton` 裸比）；
  归一入口 `facebook-router/00-shared.js:6`（`norm` 只折叠空白）、`:21-22`（`text`/`label`）；
  对比唯一做 NFD 的 `facebook-router/20-feed.js:178`
- **具体缺哪几样**：
  1. 缺**标签侧**的 Unicode 归一：`00-shared.js:6` 的 `norm` 只做 `replace(/\s+/g,' ').trim().slice()`，`label()`/`text()` 都经它，之后直接喂 `08-reaction-semantics.js` 的正则。**NFD 分解形的 `Thích` 不匹配 NFC 词表项。**
  2. 缺「去变音符后再比」这条兜底：新引擎在同一个文件里**已经会写这个变换**（`20-feed.js:178` 的 `normalize('NFD').replace(/[̀-ͯ]/g,'')`），但只用在空态文案上，标签侧没有。
  3. 手工并列写法被逐字继承（`08-reaction-semantics.js:1` 里同时有 `thích` 与 `bay to cam xuc thich`）——**看起来**覆盖了越南语，实际只覆盖当初真机见过的两种形态。
  4. **影响面不止反应按钮**：`postComment`（`08-reaction-semantics.js:7`）、`pickerReaction`/`pickerLike`（`:5-6`）、`unlike`（`:2`）、`feedLikePickerProbe` 的 `reactionish`/`likeOnly`（`10-feed-like.js:172-173`）、评论框标签（`05-session.js:1-4`、`50-comment.js:22-23`）、加群与发布词表，**全部同一条盲区**。
  5. **连带效应（实装时最要紧的一条）**：这条盲区一旦命中，①（热度恒 0）与②（评论入口找不到）都会以「像是选择器写错了」的形式表现出来，排查时**互相掩盖**；而修 ① 时新增的计数控件选择器**若照抄裸比就会带着同一个盲区上线**。
- **可 port 的旧测试**：
  - `test/facebook/cta-labels.test.ts`『中性点赞按钮 aria-label 多语言命中』——锁现有词表语种覆盖面（含越南语两种写法）。port 时应在此基础上**新增 NFD 分解形用例，把两代共有的盲区固化成红灯**。
  - 同文件『帖级「评论」按钮标签命中（排除评论级 react 用）』——锁评论 CTA 词表，②的点击闸依赖它。
  - `test/facebook/feed-reader.test.ts`『支持语言共用动作栏分类，数字汇总 toolbar 不成为第二个 react 控件』——用例已在四语种上循环，**加一轮 NFD 形态即成归一化的契约测试**。
  - 同文件『Re Su 越南语完整动作标签仍绑定同一卡的视频身份、作者与摘要』『越南语媒体-only 视频首卡跳过；exact-card watch 视频卡诚实上报』——真机越南语形态用例，**NFD 变体最可能出现的场景**。
  - `test/facebook/comment-executor.test.ts`『评论框标签识别覆盖真机变体与多语言（回归 发表公开评论 漏配 → 评论从未发出）』——**一次「词表穷举漏配导致评论从未发出」的真机事故回归，是本盲区最有说服力的历史证据。**

---

## 覆盖漏洞

以下条目在参照书里有、在本 change 的 tasks 里**找不到对应任务**。

### A. ③ Cookie 同意策略与失败分档 —— 整条无任何任务（最严重）
`grep -i "consent|同意|cookie"` 在 proposal / design / tasks / 四份 spec delta 上**零命中**。
其中至少两条是「今天就能把整台账号打死」的活缺陷：
1. **作用域自伤**（`05-session.js:18` 取首个可见 dialog 且不校验它含 cookie 文案）——FB 首页常年挂良性 dialog，
   一旦命中，评论 / 点赞 / 发帖 / 加群 / 滚动 / 刷新**全部**返回 `blocked_by_consent`。这是 Native 迁移**新引入**的失效模式，旧实现在 document 上采集、没有它。
2. **present 门缺「至少一个按钮」**（`05-session.js:22`）——cookie 文案在页但按钮词表 miss 时，
   旧实现放行流程，新实现把所有受闸动作判 `blocked_by_consent`。
   
**建议怎么补**：这两条与本 change 的主张（读数假 / 动作缺 / 语义标错）同类，且同属「静默假失败」，
应作为 §2 之外的新一节（如「§2C aidcp-edge — 同意闸作用域与失败分档」）加进本 change；
若判定超出本 change 范围，**必须另起 change 并在本 change 的 proposal 里点名交接**，不能只留在参照书里。
另两条（`no_target` / `blocked_by_consent` 分档、探测失败降级）与「唯一性恰好 1」的宽容度可一并处理，
可 port 的用例在 `test/facebook/consent.test.ts` 里现成一整组。

### B. ④ 的高度增长阈值 1px vs 旧 100px —— 无任务，且被 4.5 明令禁止改
`feed.rs:409-414` 判 `after.scroll_height > before.scroll_height + 1.0`，旧实现明文取 **100px** 抗噪。
1px 会让任何 reflow 都算「懒加载还在长」→ 继续下滚 → **连首页都难走到到底确认**，
这会**削弱 4.1 / 4.1b 的实际效果**（把守卫放开了，证据链却仍然走不到）。
而 task 4.5 把「无增高」列进「MUST NOT 改」的证据链清单，等于把这条锁死。
**建议怎么补**：在 4.5 里为「高度增长阈值取值」开一条显式例外（或新增 4.6），
按旧实现的 100px 立论重新取值，并用旧用例『懒加载还在长内容 / 未到底时绝不提前判到底』作反例回归；
若判定该阈值属 `repair-facebook-feed-exhaustion-continuation` 的资产，需与该 change 串行并写明交接。

### C. ⑥ 的盲区约束未写进 1.1 —— 修 ① 时会把盲区带进新代码
task 9.10 把 ⑥ 记为「两代共有、本 change 不修、只登记」，这个定性是对的；
但 task 1.1 新增的**计数见证解析**是**新写的标签匹配代码**，tasks 里没有任何一条要求它做 Unicode 归一，
也没有要求它复用 `20-feed.js:178` 已有的去变音符变换。照现状实装 = 新代码原样继承盲区。
**建议怎么补**：在 1.1 的验收里加一句「见证解析的标签匹配 MUST 经去变音符归一（复用 `20-feed.js:178` 的变换），
并在 1.5 的语料里加一条 NFD 分解形的越南语用例」——这不扩大 ⑥ 的修复范围（不动既有七条词表），
只保证**新增**的那段不带盲区上线。

### D. ⑤ 的「联系方式分两段验收」分诊 —— 无任务承接
旧实现对「正文进去了但联系方式没进去」有**独立失败面**（可 port 用例：『联系方式追加后未被编辑器验收 → 不提交，避免裸发联系方式缺失的正文』）。
新引擎把正文与群号拼成一串一次打完，这一档合并进了笼统的 `marker_not_accepted`。
task 2.4 只要求「三处收成同一个谓词」，没有要求恢复这层分诊。
**建议怎么补**：若不打算恢复分两段输入，至少在 2.5 的行为台账里显式记一条
「Facebook 评论的正文与联系方式不分段验收，失败原因合并为 marker_not_accepted」并写明理由，
使这个差异成文而不是静默丢失。
