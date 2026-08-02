# 退役实现参照（oracle）

> 用途：本 change 的多数条目属「以前能做、迁移后做不了」。退役的 TypeScript 实现仍在
> /Users/baitianxing/codes/aidcp-edge/src/ 下（被构建期剪枝挡在生产外、宿主装配被恒假条件短路），可直接当行为参照。
> **只当参照书，不得把退役实现搬回生产**——那会击穿本次迁移的动机，且宿主那段是死码不是开关。
> 迁移前版本用 `git -C /Users/baitianxing/codes/aidcp-edge show 317cd47^:<path>`（小红书）或 `4f04e9c^`（Facebook/微信）读。

> 行号核对（2026-07-28，edge `master`）：抽查 `src/browse/browse-session.ts:2450`（executeComment doc）、`:2794`（back 恒真回执）、
> `src/browse/notification-monitor.ts:146/148`（cut / 行容器）、`:260-263`（nextEpoch）、`src/flows/publish-command-handlers.ts:1332`（runSubmit doc）、
> `src/main.ts:1043`（`if (false && …)`）、`src/flows/anchors.ts:34-37/46-64`、`native/page-engine/src/xhs-command-router.js:126-140/187-214/229-240/271-273`、
> `317cd47^:src/main.ts:1413-1426`（通知未读监测装配点），逐条对得上，未发现需要「行号待核」的条目。

## ⚠️ 不可照抄的条目（先看这段）

### ④ 返回列表（`oracleQuality: also-wrong`）
旧实现的**回执一样不诚实**：`src/browse/browse-session.ts:2794` 在所有分支收尾无条件
`reportActionCompleted({action:'back', ok:true})`——连 `ready===false`、走完最后一层 explore 安全网的情形也报成功，
真值 `ready` 算出来了却没进回执。**照抄会把「恒真」原样搬回来**，等于本 change 的 task 2.4 白做。
可照抄的只是它的**机制**：回源列表 URL、等可见卡片、二次导航、explore 安全网、严格 feed 正则、返回前关浮层、先上报卡再回执。
回执 `ok` 必须新写成「由列表面真可用（可见卡片确认）推导」。

### ⑥b 关注（`oracleQuality: also-wrong`）
旧实现的**后置校验本身就是缺的**：`src/browse/browse-session.ts:2724-2727` 点击后只 `sleep(1500)` 就无条件打「✓ 关注成功」并报
`ok:true`，无任何状态翻转确认（与同文件点赞/收藏的 1500ms 有界轮询形成对照）。**照抄会把「点完睡一觉就成功」搬回来。**
可照抄的是它的**定位与已关注前置判据**（七个具名候选选择器 + 文本「已关注」/「互关」 + `aria-pressed` + `already_followed` 的 reason 口径 +
只读探针逐字镜像同一套判定）；成功判据必须新写成「有界轮询到按钮状态真翻转」，可复用点赞侧的真机窗口（300–600ms / 上限 1500ms）作起点。

### ① 开帖（`direct`，但两点须现场复核）
- 真机结论取自 2026-06-27（`aidcp-edge/docs/xhs-layout-states.md` 头部自记来源），弹层容器选择器与「成功开一次 modal 后确认 detail 容器选择器」在该文档 §2.4 仍标 🔶 待确认。
- 「页内 `el.click()` 是否也能被单页应用接住」在 Native 路径上**从未复核**。故「改用可信指针输入」是安全方向，但**不能把「新引擎必然落 404」当既成事实**（task 5.1 正是为此设的真机项）。
- 可无条件照抄的只有三层：**必须有正面详情证据 + 错误页否决 + 访问令牌门控**。

### ⑤ 看图（`direct`，有一层旧实现里没有）
旧实现只到「点得动 / 点不动」，**不校验图序真前进**（不比对 swiper active index 或当前图 URL）。本 change 设计 D3 要求「每步重新解析控件并校验图序真前进」——
这一层**旧实现无对应物，需新写**。可直接照抄的是 `no_target` / `browsed=N` 两种诚实回执与「循环内重新解析控件」。

### 通知类三条选择器的时效（`direct`，选择器不可当已验证事实）
- 行容器 `div.tabs-content-container > div.container`、属性名 `note-id`、「评论行无 per-comment permalink」出自 **2026-06-24 活页面 dump**，距今一月余；task 5.5 要求重新 dump 后再定选择器。
- 赞/关注两栏的行容器与昵称选择器，**旧实现自己写明「未经活页面 dump、待真机校准」**——机制可抄，选择器不可当已验证事实。
- 入口角标探测判据是 2026-06-23 真机校准，仍可照抄，但**必须连同它依赖的「宽/窄双布局遍历、取可见那个」一起搬**：只搬结构判据不搬遍历，会在窄布局漏报（真机实测漏报 10 条未读）。

### epoch（`oracleQuality: none`）
Native 的 `epoch:Date.now()` 是**迁移新造的字段，旧实现里没有对应物**，不能照抄旧代码「改回去」。
正确做法是恢复「无→有 翻转」这个单一来源的单调序号，并让列表 / 首页上报**不自造 epoch**。

---

## 逐条参照

### ① 开帖：成功判据只看地址里有笔记 id + 页内程序化点击封面裸链

- **对应任务**：1.2、1.3、2.2、5.1
- **旧实现**：`src/browse/browse-session.ts:1475-1489`（note.open 分发）、`:1876-2036`（openAndReportNote 全流程）、`:1826-1845`（locateCardByNoteId）、`:1271-1277`（rememberCurrentSourceList）、`:2040-2060`（waitForEngageBar）、`:2067-2110`（waitForNoteBody）；`src/browse/feed-scroller.ts:214-228`（openCard）；`src/browse/cdp-util.ts:176-262`（dispatchHover / dispatchClick / commitLeftClick）；`src/browse/modal-controller.ts:39-96`（buildIsOpenJs / waitForModal）；`src/flows/anchors.ts:34-37`（弹层选择器）；`src/browse/note-extractor.ts:283-292`（正文选择器）、`:356-417`（extractNoteContent）；真机结论 `docs/xhs-layout-states.md:58-62`
  — 开帖是「六段有预算的证据链」，不是一次求值：① 按云端给的 noteId 在当前视口快照里找卡，找不到先判它是否还在 DOM、在就 scrollIntoView 拉回视口重扫，真被虚拟列表回收才重报当前卡片并诚实 card_not_found；② 记住来源列表 URL（供返回用）；③ 用 CDP 可信指针输入（贝塞尔轨迹逐帧 mouseMoved → mousePressed/mouseReleased 原子区）点卡片几何中心，而不是对锚点调页面内 click；④ 轮询等详情弹层容器真出现（可见性判据：有盒 + display/visibility 非隐藏），未出现则重点一次、再不出现诚实 modal_timeout；⑤ 分别等互动栏渲染（≤3s）与正文渲染门（图文 3.5s / 视频 2.5s，命中真正文即早退），超时还要再探一次「是布局变体未命中还是本就无正文」并分别打日志；⑥ 抽取后才上报，且上报的可点链接必须来自地址栏且确含访问令牌，否则整条 url 字段留空。全程带单命令预算（noteOpenTimeoutMs）与逐段耗时日志，预算耗尽诚实 open_timeout。
- **旧代码记下的真机经验**：
  > feed 封面是**裸链** `<a href="/explore/<id>">`（**无 xsec_token**）。**直接导航裸 URL → 404 `error_code=300031 当前笔记暂时无法浏览`**（XHS 反爬：开笔记须带 xsec_token）。

  > ✅ 正确路径：**真实点击**（CDP 鼠标事件，非 `el.click()` 裸 anchor 导航）触发 SPA 就地开 modal，URL 变 `/explore/<id>?xsec_token=...&xsec_source=pc_feed`（token 来自 feed 内存）。

  > 诚实置空：仅当地址栏链接确含 xsec_token 才作为真实可点链接上报；否则不带，绝不用裸 id 拼打不开的假链接。

  > 解析真实 noteId：优先 feed 卡片 → modal 内 explore 链接 → 当前页面 URL → 合成兜底。真实 noteId 是云端 visited 去重的主键，缺失会导致"反复打开同一张卡"的死循环。

  > 优先按 noteId 在「当前快照」里定位：云端决策与 edge 执行之间 feed 可能已滚动，纯 index/position 寻址会开成同序号上的"邻座"（云端判 LLM 卡 valuable，edge 却开了 NPD/C罗）。

  > 真被虚拟列表回收出 DOM（自主 feed 换页的常态）就**立即返回 undefined、绝不盲滚**——盲滚既救不回、还会把 feed 越滚越乱、每次白费数秒（真机黑匣子实证：自主浏览 note.open 级联里盲滚 5 下次次落空）。

  > 正文(#detail-desc)常比 engage-bar 晚渲染：先等正文出现再抽取，避免抽到空/「标题+刚刚」。按类型给正文门余量：文字/图文渲染实测 <1s，3.5s 已远超（body-less 时早停不空等满 5.5s）；video 主体是视频、正文多为空 → 2.5s 更短。命中真正文即提前返回，不影响抽取保真。

  > 背景（实测 6/16）：正文常比 engage-bar 晚一拍渲染，过早抽取会拿到空 body，进而回退到含"标题+发布时间"的容器、并让云端 curator 误判"空洞"。这里只盯正文容器 `#detail-desc`（评论区也用 `.note-text`，故不以它为准）；纯图文/视频笔记本就无正文 → 等到超时即放行（body 合法为空，不阻塞）。

  > 【刻意不含】裸 `.note-content` / `[class*="content"]`：它们会把"标题+发布时间(刚刚)"拼进正文（假阳性，f8712f5 实测根因）。变体一律下钻到 .note-text/.desc，既救回长文布局变体（治假阴性）又不泄漏标题。

  > 点赞/收藏/评论数限定到互动栏（engage-bar）作用域统计——否则在整个 modal 内扫会落到评论区每条评论自带的 like-wrapper（真机实测「卡片👍311 vs 详情👍1」：详情点赞被错成某条评论的赞数）。collect-wrapper 只在互动栏故收藏数本来就对。

  > 标题：收紧选择器——去掉贪婪的 [class*="title"] 与裸 h1（作用域降级到整页时它们会命中全局「猜你想搜」搜索推荐插页标题，真机实测污染源）
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:187-196`（note_open 分支）、`:45-51`（click 助手）、`:90`（detailRoot）、`:91-118`（detail 抽取）、`:141-144`（exactNote）、`:59-89`（cardNodes/cards）；`native/page-engine/src/engine.rs:610-619`（仅「命令带 url」时才走导航 + NoteDetail 轮询，现役云端不带 url）、`:708`（其余一律通配求值）；页型判据在 `native/page-engine/src/probe.rs:150-196`（含 `PageKind::Error`）
- **具体缺哪几样**：
  1. 把可信指针输入换成页内 `el.click()`（router:49 对 `a[href="/explore/<id>"]` 锚点调 `el.click()`），正是真机文档点名「非 `el.click()` 裸 anchor 导航」的那一种；缺 CDP mousePressed/mouseReleased 轨迹点击。
  2. 成功判据退成「详情容器存在 或 地址里解析出笔记 id」（router:194），而 300031 错误页地址恰好也是 `/explore/<id>` → 错误页判成功。
  3. 缺错误页否决：`probe.rs:158` 已有 `PageKind::Error` 机械判据、`src/browse/overlay-monitor.ts:100-104` 已有「当前笔记暂时无法浏览」词库，router 的 note_open 一条都没用。
  4. 缺访问令牌门控：router:116 无条件 `url:String(location.href)`，不再判 `xsec_token`；空壳/错误页的裸链会被当「真实可点链接」上报。
  5. 缺正面详情证据：detail() 直接抽取，无 engage-bar 渲染门、无正文渲染门；标题/正文/图片全空也照样返回 note_detail（云端收到详情即记一笔浏览）。
  6. 正文选择器把旧实现明令排除的 `[class*="content"]` 放了回来（router:95），标题选择器用回被点名的贪婪 `[class*="title"]` 与裸 `h1`（router:94）。
  7. 点赞/收藏数不再限定互动栏：router:105-106 在整个详情容器内取首个 `[class*="like"]` / `[class*="collect"]`，会落到评论区某条评论的赞数。
  8. 缺 noteId 找回：router:191 仅 `candidates.find(...)`，不在 DOM 就直接 `target_not_found`；无 scrollIntoView 拉回、无「重报当前卡片」兜底。
  9. 缺来源列表记忆（无 rememberCurrentSourceList 对应物），返回时无从回到搜索结果页（见 ④）。
  10. 缺重试与分段预算：一次点击 + 固定 sleep(900)，无二次点击、无逐段耗时、无 open_timeout 语义。
  11. 幂等早退也只看 URL：router:188 停在错误页时会直接把错误页当「已在目标笔记」返回详情。
- **可 port 的旧测试**：
  - `note.open surface=feed 小红书诚实拒 capability_unsupported`（锁「无 feed 就地读、绝不静默回落详情」；router:189 已有等价分支，可当契约回归钉住）
  - `详情页地址栏带 xsec_token → note.detail 带真实可点 url` / `无 xsec_token → url 诚实置空`（后者正是新引擎无条件上报 `location.href` 的表征测试）
  - `note.open 按 noteId 命中目标卡（index 已失效也开对）`、`目标已滚走时重报当前卡片（不开邻座）`、`目标滚出视口 → 有界滚动找回并打开`
  - `note.open 预算耗尽后如实失败，接管等待到安全边界才结束`（锁 open_timeout 不假成功）
  - `note.open 视频卡上报 note.detail.mediaType=video`（锁 mediaType 口径）
  - `启动停在笔记详情页(/explore/<id>) → ensureExplore 严格判定并导航回 feed`（锁「/explore/<id> 不是 feed」）

### ② 评论：只提交正文，云端下发的联系方式串码被丢弃

- **对应任务**：1.1、2.1、5.6、6.3
- **旧实现**：`src/browse/browse-session.ts:2450-2648`（executeComment 全流程，doc 2450-2459）、`:1518-1535`（interaction.comment 分发含就地 noteId 核对）；串码整段插入 `:2543-2553`；清场闸 `:2509-2536`；提交前验证码复检 `:2555-2562`；后置校验 `:2603-2626`；提交三态 `:2627-2637`；`src/browse/cdp-util.ts:294-299`（insertText）、`:218-262`（dispatchClick）
  — 评论是「六道闸 + 双通道输入」：① 折叠态入口 → 点击激活；② 定位真编辑器并点本体落 caret（contenteditable + 提及插件下 activeElement 不可信）；③ 清场闸——输入是在光标处追加，残文清不干净就诚实终止、绝不拼接发出；④ 正文走拟人逐字派发（可打断 + 取消点），联系方式串码另走一次整段 insertText（绕开逐字触发的 @/# 补全劫持），拼成「正文 + 换行 + 串码」，与云端人审卡上的合并终稿逐字一致；⑤ 提交前 fresh 复检验证码 + 最后一个安全取消点；⑥ 点提交后进入禁区，轮询「编辑器已清空 且 自己的评论作为顶部新行出现」≤2s，命中报 ok，未命中报可区分的「已提交、结果未知」而不是「未提交」。被接管时让位前必须清场。
- **旧代码记下的真机经验**：
  > 选择器与发布后校验信号由真机 CDP 探针坐实（scripts/comment-probe.ts）：
  >  *  - 折叠态入口 `.engage-bar .content-edit .not-active`（"说点什么"）→ 激活后 engage-bar 加 `.active`；
  >  *  - 真编辑器 `p#content-textarea`（contenteditable，data-tribute 提及）——必须点本体落 caret；
  >  *  - 提交键 `.engage-bar.active button.btn.submit`（"发送"）；
  >  *  - 发布后校验：编辑器清空 且 自己的评论作为顶部新 `[id^="comment-"]` 行出现（评论数文本不可靠，不依赖）。
  >  * 红线：找不到框/按钮 no_target、未生效 state_unchanged、验证码 blocked_by_captcha——绝不静默假成功。

  > 3b) 联系方式（change account-group-chat-injection）：串码部分**单次整段插入**（Input.insertText），绕过逐字输入会触发的 @/# 提及/主题补全劫持；verbatim，不 trim/不逐字敲。追加「换行 + 联系方式」，与云端人审卡展示的合并终稿一致（AC-PUB 审=发）。缺省则不插、行为与今天一致。

  > 2b) 清场前置（change lease-strict-preemption task 3.2）：输入是**在光标处追加**——上一次被抢占 / 失败留在编辑器里的半截评论不清掉，就会和这一条拼在一起发出去。清干净了才往下走；清不掉 = 真脏页，诚实终止（绝不带着残文提交）。

  > comment 编辑器清不干净（残留 …）→ 诚实终止，绝不拼接发出

  > 提交三态（change lease-strict-preemption task 3.2）：**提交动作已经派发出去了**。这一条评论可能真已发出（网络在途 / 页面渲染慢），也可能没发出——我们分不清。谎报「未提交」会让上游重试 ⇒ 重复评论。故 MUST 用可区分的「已提交、结果未知」，上游据此 MUST NOT 自动重试（去重账本 + 人工确认），见 cloud task 7.6。

  > 6) 后置校验：轮询「编辑器清空 且 自己的评论作为顶部新行出现」，命中即返回、上限 2000ms（取代固定 sleep(2000)；发评论生效多在 1s 内，快路径省 ~1s）。

  > 让位前 MUST 清场：半截评论留在编辑器里，下一条评论的清场闸会把它判成 editor_not_clean、白白毙掉一条有效评论（清不掉时更会真发出一条拼接的评论）。

  > 🔴 提交窗口开启（5.1）：点下即进入禁区，协调器此间不强杀（回 window_busy + 剩余预算）。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:235-237`（interaction_comment 整个分支，一行）、`:34-44`（dispatchInput）；参数确实到位：`native/page-engine/src/command.rs:288-303`（`CommentParams.group_chat_code`，camelCase 序列化）、`:696-702`（长度校验），命令 JSON 经 `native/page-engine/src/xhs.rs:33-42` 拼进注入表达式 → 页内 `p.groupChatCode` 可读但**全文零命中**；对照正确实现 `native/page-engine/src/facebook/comment.rs:72-80`
- **具体缺哪几样**：
  1. 丢串码：router:236 只读 `p.text`，`p.groupChatCode` 全文零引用 → 人审终稿与真实发出内容不一致（违「审=发」）。
  2. 回读校验只覆盖正文且只比前 100 字（router:236），即便串码补上也不会被回读覆盖。
  3. 缺清场闸：直接覆盖式写值，没有「先清空、清不掉则 editor_not_clean 诚实终止」；contenteditable 分支走 `el.textContent=value`（router:41），残文风险换成了「框架受控编辑器不认 textContent 直写」风险。
  4. 把两段输入合成一次程序化写值：无逐字拟人派发、无「串码单独整段 insertText 绕开 @/# 补全劫持」这一分工。
  5. 缺折叠态入口激活：旧实现先点 `.engage-bar .content-edit .not-active` 才出现真编辑器；router 直接 `first(['textarea','[contenteditable="true"]','input[placeholder*="评论"]'])`，折叠态下取不到真编辑器 → comment_editor_not_found。
  6. 提交键退成「文本含发送/发布/submit 的第一个元素」（findByWords），不再是标定过的 `.engage-bar.active button.btn.submit`。
  7. 后置校验退成「详情容器内任何 class 含 comment 的元素文本包含正文前 500 字」，一次固定 sleep(800)、无轮询；旧实现要求「编辑器已清空」+「自己的评论出现在顶部 3 行 `[id^="comment-"]` 内」双条件同时成立。
  8. 提交三态被压平：返回 `ambiguous` + `comment_submit_unconfirmed`，但没有「已提交、结果未知」与「未提交」的可区分标记，也没有提交窗口守卫。
  9. 缺提交前 fresh 验证码复检、缺最后一个安全取消点、缺被接管时的让位前清场。
  10. 缺 fastReturnToFeed（`/comment --feed`）语义：router 完全不读 `p.fastReturnToFeed`。
- **可 port 的旧测试**：
  - `executeComment: 编辑器清空且自己的评论行出现 → ok:true`（锁双条件正证据）
  - `executeComment: 找不到编辑器 → ok:false reason no_target`
  - `executeComment: 提交后未确认生效 → ok:false reason submitted_unconfirmed`（锁提交三态，绝不谎报未提交）
  - `executeComment 清场：编辑器里有残文且清不掉 → 诚实 editor_not_clean`
  - `executeComment --feed: 提交后等 500ms、跳过结果检测、直回首页并诚实 submitted_unconfirmed`
  - `interaction.comment: 当前详情 noteId 与目标不符 → note_page_mismatch`（新引擎有等价物 router:236 exactNote，可直接钉住）／`一致 → 正常发布`
  - `取消点: 评论逐字输入中途被接管 → 停手 + 清场 + preempted_by_task`
  - 🔴 `禁区: 提交键点下之后被接管 → 后置校验照跑完，回 ok / submitted_unconfirmed，绝不回 preempted、绝不重发`
  - `fb-handler: interaction.comment 带 groupChatCode → 透传给 executor contactInfo`（`test/facebook/comment-handler.test.ts:228`，现成的「串码必须到达提交层」表征测试，改平台即可 port）

### ③ 发布提交：整页前 3000 字做正则匹配当成功判据

- **对应任务**：3.2（成功判据与已派发位）；提交窗口那一半由同批 `restore-native-xiaohongshu-session-guards` task 2.1/2.2 承接（`xhs_publish_submit` 15 000ms）
- **旧实现**：`src/flows/publish-command-handlers.ts:1332-1432`（runSubmit，doc 1332-1335）、`:1092-1143`（findShadowButtonCenter：`DOM.getDocument{pierce:true}` 穿闭合 shadow + `DOM.getBoxModel` 取盒模型中心 + 禁用态诊断）、`:1303-1329`（logSubmitDiag）、`:1408-1412`（CHECK 正证据注释）；提交窗口 `:1372`/`:1388`（15s）
  — 提交是「穿透闭合 shadow 的坐标点击 + 只认正证据的 15s 有界轮询」：① 目标不靠文本搜索——发布栏是自定义元素 `<xhs-publish-btn>`，按钮在闭合 shadow 里，必须走 shadowRoots 递归找文本节点恰等于「发布」/「定时发布」的元素，再取真实盒模型中心，并把命中节点的 class / disabled / aria-disabled 打进诊断以区分「禁用按钮 no-op」；② 点击前有「通读全文确认」停留，且刻意关掉 overshoot 与落点抖动；③ 点击那一刻置 submitDispatched，press 已发而响应抛错也要如实带上「已点」；④ 点下即开 15s 提交窗口守卫（禁区，不可取消）；⑤ 后置校验只认页面成功文案（`发布成功|发布中|笔记已?发布|成功发布|稍后可在`），每 500ms 轮询、上限 15s，URL 判据被明令删除；⑥ 未确认返回 post_validate_failed 并再抓一次终态诊断。
- **旧代码记下的真机经验**：
  > 点「发布」提交：发布栏是自定义元素 <xhs-publish-btn>（闭合 shadow，文本搜不到）；「发布」为其右侧红色按钮、「暂存离开」在左。用坐标点击宿主右侧区域（安全避开左侧暂存），再后置校验发布成功。

  > 后置校验：**只认正证据**——页面成功文案（5.9 收紧）。原「离开发布编辑页(!href.includes('/publish/publish'))」判据是已上膛的假成功：抢占方 / 恢复导航会在这 15s 窗口内把发布页导走 → 一篇可能根本没发出去的稿被记成已发布。该假成功由 5.2/5.3（publishInFlight 闸封住恢复导航）从根上堵住，这里再去掉 URL 判据做纵深防御（URL 缺失单独不得判成功）。真机项 F/D 待核：若确有成功后跳转的落地帖 URL 正证据，可再补为「成功文案 OR 落地帖 URL」白名单。

  > 拟人：点「发布」前"通读全文确认"停留，再走贝塞尔轨迹点击。关键：发布按钮小而精确，**关掉 overshoot/落点抖动**（精确落点）确保点中——保留移动轨迹(反检测)，但不冒"点偏发不出"的险。

  > 🔴 MUST 带 submitDispatched：若 press 已派发（onPressDispatched 已置真）但 CDP 响应抛错，回执必须如实告知「已点」，否则云端按提交前失败重投 → 双发（复核 wf_1657e89b MEDIUM）。press 未发时它仍为 false（正确）。

  > 🔴 提交点已跨过：以下 MUST NOT 取消（全仓代价最高的禁区）。中止 = 一篇**可能已经发出去的帖子**被当成没发生 → 云端重投 → 发两遍。pollBounded 签名里没有取消入参，编译器焊死。

  > 诊断（change diagnose-publish-submit-failure，只观测不改行为）：记录命中按钮节点的属性，用于区分「按钮禁用 no-op」——禁用红按钮仍有文字与坐标、点上去无效。诊断失败不影响主路径。

  > 🔴 提交窗口开启（5.1）：越过此点即不可逆，协调器此间不强杀（回 window_busy + 剩余预算）。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:271-273`（publish_submit 整个分支）、`:145-152`（findByWords）、`:45-51`（click）；`engine.rs:653-707` 里有平台语义的发布原子只有 PublishUploadImage / PublishNavigateEntry / PublishCaptureScheduled，submit 落在 `:708` 通配求值
- **具体缺哪几样**：
  1. 目标定位从「CDP 穿透闭合 shadow」退成「页内 querySelectorAll 找文本含发布的第一个元素」——页内选择器进不了闭合 shadow root，真发布按钮结构上不可达。
  2. findByWords 依次扫 `button,[role="button"],a` → `span` → `div`，首个含「发布」的可见元素很可能是「定时发布」开关标签一类，点它等于误改定时模式而非提交。
  3. 缺「定时发布」与「发布」两种标签的区分（旧实现按 scheduleModeConfirmed 选目标文本），也缺「避开左侧暂存离开」的方位约束。
  4. 点击退成 `el.click()`，无精确落点坐标点击、无关闭 overshoot/抖动、无「通读全文确认」停留。
  5. 成功判据换成 `/success|published|发布成功/i.test(location.href+' '+text(document.body,3000))`：① 把旧实现**明令删除的 URL 判据**放了回来；② 中文正证据只剩「发布成功」，丢了「发布中 / 笔记已发布 / 成功发布 / 稍后可在」四项；③ 整页正文被截到 3000 字，成功浮层文案落在 3000 字之外就读不到。
  6. 校验窗口从「15s / 500ms 有界轮询」退成「一次 sleep(1200) 后单次读」。
  7. **submitDispatched 恒真**：router:272 两条出口都写 `submitDispatched:true`，而 `click()` 在元素不可见时直接返回 false、什么都没点——「压根没点」也报「已点」，云端据此不重投 → 稿子静默丢失（与旧实现「no_target 时保持假」正好相反）。
  8. 缺禁用态诊断快照（class/disabled/aria-disabled/center 三态日志）。
  9. 缺 15s 提交窗口守卫；缺点击前/超时后两次终态诊断快照。
- **可 port 的旧测试**：
  - 🔴 `5.9 收紧假成功 CHECK：后置校验只认成功文案，绝不含「离开发布页」URL 判据`（直接对着 router:272 的 `location.href` 参与匹配写表征测试）
  - 🔴 `6.2 已派发提交位：点击已发出但后置校验超时未确认 → ok:false/post_validate_failed 且 submitDispatched=true`
  - 🔴 `6.2 已派发提交位：发布按钮找不到（no_target）→ submitDispatched 保持假`（正是新引擎恒真的表征测试）
  - 🔴 `复核 wf_1657e89b MEDIUM：mousePressed 已发出但响应抛错 → engine_error 且 submitDispatched=true`
  - 🔴 `禁区：submit_publish 点击已发出后被接管 → 15s 后置校验照跑到底`／`取消点：通读停留期间被接管 → 零 mousePressed + preempted_by_task`
  - `AC-CMD fill_field 后置校验失败（点了没生效）→ ok:false`（同族「后置校验必须能否决」）
  - `XHS-SCHEDULE 缺「定时发布」提交按钮正证据时 fail closed`
  - `select_mode 红线：下发的点击 JS 含可见性判据（取可见非取首个）`（可 port 成对 router `first()`/`findByWords` 的可见性契约）

### ④ 返回列表：回执恒为成功

- **对应任务**：1.6、2.4
- **旧实现**：`src/browse/browse-session.ts:2735-2795`（navigateBack，doc/注释 2736-2739；**恒真回执在 2794**）、`:1251-1277`（isSearchListUrl / isTargetListUrl / rememberSourceListUrl）、`:1208-1229`（waitForVisibleCards）、`:298-307`（EXPLORE_FEED_RE / SEARCH_LIST_RE 及注释）、`:3380-3389`（safeCloseModal）
  — 返回不是「按浏览器后退键」，而是「回到来源列表并确认列表真可用」：① 先关掉笔记浮层；② 协议名保留但语义改成回源列表——默认 `Page.navigate` 直连记下来的 feed / 搜索结果 URL，只有搜索来源 URL 缺失且当前仍像笔记浮层时才允许 history.back 兜底；③ 落地后必须等到 scroller 真扫到可见卡片（与上报同口径、轮询而非固定 sleep），一次不成再导航一次，最后还有一层「回退 explore」安全网；④ feed 判据是严格正则 `/\/explore\/?(\?|#|$)/`，明确排除 `/explore/<noteId>`；⑤ 确认可用后先上报可见卡片、再发回执。
- **旧代码记下的真机经验**：
  > navigation.back 的协议名保留，但边缘语义改为「回到来源列表」：默认用 Page.navigate 直连 feed/search 来源页，避免 history.back 回踩过期详情路由并触发小红书 access-limit-app 弹窗；只有搜索来源 URL 缺失且当前仍像笔记浮层时，才允许历史兜底。

  > explore feed 页 URL 判定：匹配 /explore（feed 列表），【排除 /explore/<noteId>（笔记详情页）】。用于 ensureExplore（启动）与 navigateBack（back_to_feed）统一判定是否真在 feed——历史上松判断 `url.includes('/explore')` 会把详情页误当 feed，导致扫不到卡 → 静默 → 边-云互等死锁。

  > 轮询直到 scroller 真正检测到可见卡片（与 reportVisibleCards 同口径），超时返回 false。history.back 后 feed 重渲染有延迟，固定 sleep 后瞬时判断会误判为空 → 误报"无可见卡片"。

  > 健康校验安全网：search 来源不可达或历史兜底落到坏页时，最终回退 explore，保证闭环继续上报。

  > 熟悉度提速：返回到刚看过的 feed（back_to_feed）时，离页停留已由 ensureDetailDwell 治理，返回手势不必再全量犹豫 → 用更轻的手势停顿（scroll 档，中位 ~0.8s ≈ action 的 1/3，仍带抖动、非零、不秒退）。注：此处原误取 cardGapTiming（中位 5s，比 action 还重一倍，与注释本意相反）——快速返回反成最慢档，已修正为 scroll 档。

  > 记录来源列表是返回路径优化，失败不应阻断 note.open；后续会走诚实降级。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:203-205`（navigation_back 整个分支）；对照 note_close 分支 `:197-202`（它反而有真判据：关后仍在则 ambiguous）
- **具体缺哪几样**：
  1. 回到用 `history.back()`（router:204），正是旧实现明令弃用的那一种（回踩过期详情路由、触发小红书访问限制弹窗）。
  2. 缺来源列表 URL：无 rememberSourceListUrl / sourceListUrl，搜索来源无从回到搜索结果页；`p.targetPage` 全文未读。
  3. 回执 `ok` 硬编码为 true；effectPhase 虽按路径分 confirmed/ambiguous，但云端读的是回执 `ok`。
  4. effectPhase 的路径判据是松正则 `/\/(explore|search|search_result)/.test(location.pathname)`——`/explore/<noteId>` 同样命中，正是旧注释点名的「边-云互等死锁」那个坑。
  5. 缺列表可用性确认：只 sleep(800)，不轮询等可见卡片、不做二次导航、无「最终回退 explore」安全网。
  6. 返回前不关笔记浮层；返回后不上报列表卡片。
  7. 缺返回手势停顿分档（back_to_feed 用轻档 scroll 停顿），返回是零停顿的程序化跳转；也完全不读 `dwellMs`。
- **可 port 的旧测试**：
  - `navigateBack: 看笔记→开通知→返回（无浮层整页离页）→ 不 history.back，直接 Page.navigate 回 feed`（事故回归，正对 router:204）
  - `navigateBack: 笔记浮层盖在列表上返回 → 直接 Page.navigate 回 feed`
  - `navigateBack: 搜索来源记录 URL → 直接 Page.navigate 回搜索结果，不拽回 explore`
  - `navigateBack: 搜索来源 URL 缺失时 history.back 落坏页 → 兜底 Page.navigate 回 feed 并上报 page.cards`
  - `navigation.back 无 targetPage（back_to_feed 生产路径）轮询等水合再上报，不静默死锁`
  - `启动停在笔记详情页(/explore/<id>) → ensureExplore 严格判定并导航回 feed`（可直接钉住新引擎的松正则）
  - `pacing: navigation.back 带 dwellMs 且停留不足 → 兜底停留（治秒退）` / `真实阅读已超过 dwellMs → 不叠加等待`

### ⑤ 看图：翻页控件循环外取一次、零计数、不发动作回执

- **对应任务**：1.4、1.5、1.11、2.3、2.3a、5.2；同族的评论区滚动见 1.10、2.4a
- **旧实现**：`src/browse/browse-session.ts:2797-2844`（browseNoteImages，doc 2798-2803，轮播探测注释 2807-2809）、`:1284-1311`（reportCurrentNoteImageSnapshot，refreshOnly 快照）、`:1663-1669`（note.browse_images 分发）；图片抽取 `src/browse/note-extractor.ts:203-247`（含 isNonNoteImage `:192-198`）
  — 看图是「先数总数、逐张前进、最后如实报数」：① 探测轮播返回 {total,hasNext}——真图数量用 `.swiper-slide:not(.swiper-slide-duplicate)` 数（swiper loop 会复制首尾），退路是 `.note-slider-img / [class*="media"] img`；② total<=0 就诚实 `no_target` 且**不发任何图片快照**；③ 目标张数 = min(云端 count, total)，逐次循环内**重新查询**右箭头（`.arrow-controller.right / .swiper-button-next`，带 forbidden/disabled 排除）再点，点不动就 break，只把真点动的次数计进 viewed，每步之间有拟人停顿 + 800ms 稳定等待；④ 结束后刷新一次 refreshOnly 的参考图快照（抽不到图就不发）；⑤ 回执 `ok:true reason:'browsed=N'`，N 是实测张数，明确不再用 `count||1` 兜底。
- **旧代码记下的真机经验**：
  > 浏览笔记图片。count 由 Cloud 指定。
  >  * 如实回报（不再用 `count||1` 兜底假报成功）：找不到图片轮播 → ok:false reason:'no_target'；
  >  * 命中 → ok:true reason:'browsed=N'（N 为实际浏览张数）。选择器对照真实小红书详情页 DOM，
  >  * 需本地核对校准（见 tasks 5.4）。

  > 探测图片轮播：返回 {total, hasNext}。真实小红书：真图用 .swiper-slide:not(.swiper-slide-duplicate) 计数（swiper loop 会复制首尾），翻页箭头为 .arrow-controller.right（首图时左箭头带 .forbidden）。

  > note.browse_images: 图片快照抽取失败：…（抽取失败直接 return，不发快照）

  > note.browse_images: 已刷新参考图快照 noteId=… images=…
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:206-210`（note_browse_images 整个分支）、`:91-118`（detail，图片抽取在 98-104）、`:55`（done 的 effectPhase 默认 confirmed）
- **具体缺哪几样**：
  1. 翻页控件在循环外只解析一次（router:208），循环体只 `click(next)`；翻页后引用失效/被移出可见区，`click()` 的可见性判据（router:46）会静默拒绝，实际前进张数恒为 0 而调用方无从知晓。
  2. 零计数：没有 viewed 计数器，也没有 total 探测——不数 `.swiper-slide:not(.swiper-slide-duplicate)`，直接把云端 `p.count` 夹到 1..20 当迭代次数。
  3. 无「点不动就停」：`click()` 返回值被丢弃，不 break。
  4. 不发动作回执：返回 `note_detail` + `refreshOnly=true`（router:209），云端深读角色只在收到动作名为 browse_images 的动作完成时才清等待表 → 永久挂起（旧实现两种出口都是 action.completed）。
  5. 无 no_target 语义：找不到翻页控件时循环直接不执行，仍返回详情且 effectPhase=confirmed（假成功）。
  6. 缺前进后的稳定等待与拟人停顿：每步固定 sleep(250)，无 800ms 落定等待、无 cardGap 档停顿。
  7. 图片抽取口径退化：取详情容器内所有可见 `img`（上限 20），丢掉 `.swiper-slide-duplicate` 去重、头像/emoji 过滤、srcset/data-src 回退与 `//` 协议补全。
  8. 失败时仍可能发图片快照（旧实现明确「失败翻图不应伪造图片快照」）。
- **可 port 的旧测试**：
  - `note.browse_images 命中轮播 → 如实回报 browsed=N`（并断言成功后刷新 refreshOnly 快照、图片 URL 有序）
  - `note.browse_images 无轮播 → no_target 不假报成功`（并断言 `reportedDetails.length===0`，失败不伪造快照；正对新引擎「无控件仍 confirmed」）
  - `note.scroll_comments 命中但不可滚/已到底（scrollTop 无位移）→ no_scroll`（可 port 去钉 router:213——它把是否位移塞进观测字符串里，`ok` 恒真）
  - `note.scroll_comments 命中评论区 → 如实回报 scrolled=N`

### ⑥a 点赞/收藏：文本三级回落 + 睡 450ms 单次采样 + 「已」字兜底

- **对应任务**：1.7、1.8、2.5、2.6、5.3；夹具修正见 1.12
- **旧实现**：`src/browse/browse-session.ts:2298-2360`（executeLikeOrCollect，轮询注释 2339-2341）、`:2303-2306`（互动栏渲染门注释）、`:2040-2060`（waitForEngageBar）、`:2372-2447`（executeLikeComment：按锚点复读 + 赞数 +1 双判据，doc 2364-2371）；结构锚点与真机 DOM 路径 `src/flows/anchors.ts:46-64`
  — 点赞/收藏是「结构锚点 + 图标状态位翻转的有界轮询」：① 先有界等互动栏渲染（≤3s，超时不抛、走诚实 no-bar）；② 定位限定在 `.interactions.engage-bar`（退 `.engage-bar`）内的 `.like-wrapper` / `.collect-wrapper`，读其 `svg use` 的 `xlink:href`/`href`：已是 `#liked`/`#collected` 就报 `already_liked`/`already_collectd`、不重复点，找不到栏/找不到控件分别报 `btn_no-bar`/`btn_no-btn`；③ 取控件盒模型中心，提交前 fresh 复检验证码（命中即 blocked_by_captcha 放弃点击）；④ CDP 拟人坐标点击；⑤ 后置校验轮询同一个 `svg use` 是否翻成 `#liked`/`#collected`，命中即返回、上限 1500ms，未翻转诚实 `state_unchanged`。评论点赞另有更严的一条：按云端给的稳定锚点 `getElementById` 复读，判据是「use 翻成 #liked 或 赞数较点前 +1」，锚点没了就 no_target。
- **旧代码记下的真机经验**：
  > 验证：轮询 SVG href 是否翻成 #liked / #collected（多在 300–600ms 翻转），命中即返回、上限 1500ms —— 取代原固定 sleep(1500) 后单次读，快路径省 ~1s，仍带上限不会过早误报。

  > 互动栏常比笔记打开晚一拍渲染（AI 总结流式重排 / 卡片回收）：定位前有界等待，避免在渲染完成前误报 btn_no-bar。超时不抛、仍走下方诚实 no-bar。

  > 小红书互动栏不暴露任何无障碍语义（无 aria-label / 无 role=button / 无"点赞"文本，图标是纯 SVG，计数是裸数字），唯一稳定可读的锚点是手写语义 class `like-wrapper`。它属于 extractor 反混淆白名单，可作为稳定属性参与匹配。

  > 实际 DOM 结构（语义 class 路径）：
  >  *   section.note-item > div.footer > div.author-wrapper > span.like-wrapper
  >  *                                                          └─ <svg heart/> + 计数数字

  > 点赞作用域：把定位限制在「当前打开的笔记详情容器」内。用 CSS 选择器锁定弹层，消除 explore 瀑布流里其余卡片 like-wrapper 的干扰。

  > 给详情页内「某一条评论」点赞。靠云端给的稳定锚点 commentAnchorId 经 getElementById 重新定位，在该评论行内点 `.interactions .like .like-wrapper`，点后按锚点复读校验 svg use #like→#liked（或赞数+1）。红线（绝不静默假成功）：
  >    *   - 锚点已不在（评论被滚走/重渲染）→ no_target，【绝不退化成「点现在在那个位置的那条」】；
  >    *   - 该评论已是已赞 → already_liked，不重复点；
  >    *   - 点击后状态未翻转 → state_unchanged；验证码弹窗 → blocked_by_captcha。

  > 点击前 fresh 复检验证码（fail-CLOSED）：引导性停顿已上移到命令入口 gateBeforeAction（最小间隔 + 云端犹豫，取 max 不累加），此处不再叠一段停顿——避免「操作后兜底累加」（设计 §3.3）。

  > ⚠ … 点击后状态未变化 (href=…)，可能未生效

  > 笔记内点赞：`span.like-wrapper` + `svg.reds-icon.like-icon`(use `#like`)，**须限定在 modal 容器内**（feed 卡同款类名）。（docs/xhs-layout-states.md:61）
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:229-234`（interaction_like / collect / follow 合并分支）、`:145-152`（findByWords 三级回落）、`:52`（active 判据）、`:45-51`（click）、`:238-240`（interaction_like_comment）
- **具体缺哪几样**：
  1. 定位退成「文本含该词的第一个可见元素」（findByWords(['点赞','赞','like']) / (['收藏','collect','save'])，`button,[role="button"],a` → `span` → `div` 三级回落取首个）。而真机结论是小红书互动栏**没有** aria-label、没有 role=button、没有「点赞」文本，图标是纯 SVG、计数是裸数字 → 该判据在互动栏上**结构性不可命中**；能命中的只会是评论区/其它含「赞」「收藏」字样的元素。
  2. 丢掉结构锚点：不用 `.interactions.engage-bar` 作用域、不用 `.like-wrapper`/`.collect-wrapper` 具名控件、不排除评论区与 feed 卡同名控件。
  3. 丢掉图标状态位：改用通用 `active()`（看 aria-pressed / data-active / className 匹配 `/(active|selected|liked|collected|followed)/i`），不读 `svg use` 的 `#liked`/`#collected`——`like-wrapper` / `collect-wrapper` 这两个类名都不含 `liked`/`collected`，该判据在小红书上**永远不成立**。
  4. 后置校验退成「sleep(450) 后单次采样」，没有有界轮询；旧实现记录真机翻转多在 300–600ms、上限 1500ms —— **450ms 单次采样落在翻转窗口正中间**。
  5. 新增「已」字兜底：`text(control,100).includes('已')` 也判成功。这是唯一还能返回成功的路径，且在定位已退化到可能命中大容器的前提下，任何含「已」字的文案（已关注、已收藏、已读…）都会把没生效的动作报成成功。
  6. 缺互动栏渲染门（无 waitForEngageBar 对应物），笔记刚开时定位就会落空。
  7. 缺提交前 fresh 验证码复检（blocked_by_captcha 语义在小红书分支完全没有）。
  8. 失败终局压平：只有 control_not_found / postcondition_unconfirmed 两种，丢了 btn_no-bar / btn_no-btn / state_unchanged 的可区分性。
  9. 评论点赞（router:238-240）另有两处退化：控件用 findByWords(['赞','like']) 而非 `.interactions .like .like-wrapper`；判据只看 active()，丢了「赞数较点前 +1」这条第二正证据。
  10. 点击是 `el.click()` 而非 CDP 坐标点击。
- **可 port 的旧测试**：
  - `interaction.like 命令执行点赞并上报结果`（桩里 like-wrapper 第一次返回坐标 + href='#like'、第二次返回 '#liked'；锁「结构锚点 + 图标状态位翻转」）
  - `interaction.like 已点赞时上报 already_liked`（锁「已达成不重复点」）
  - `overlayMonitor 提交前复检: like 命中 captcha → 放弃点击并上报 blocked_by_captcha`
  - `让路 / 取消点系列中的 like 断言（命令停在阻断浮层闸时被接管 → 零页面写 + 诚实失败回执）`
  - `feed.refresh: 点后首卡为空（仅回到顶部、内容未换）→ not_reloaded`（同族「后置校验必须能否决 + 有界轮询」，可 port 成对 450ms 单次采样的表征测试）
  - ⚠️ 现有唯一的新引擎互动测试 `binds an interaction to the current note and verifies the changed state`（`test/native-page-engine/router-contract.test.ts:84`）**目前没有保护力**：夹具在 `HTMLElement.prototype` 上钉死 getBoundingClientRect（同文件 `:34-36`），可见性判断恒真，且用的是能被 `active()` 命中的人造 DOM——须先修夹具（task 1.12）。

### ⑥b 关注：点完睡一觉就报成功（后置校验缺失）

- **对应任务**：1.7、1.8、2.5、2.6、5.3
- **旧实现**：`src/browse/browse-session.ts:2685-2732`（executeFollow；**恒真回执在 2724-2727**）、`:2653-2682`（probeAuthorFollowed，doc 2653-2659）、`:349`（FOLLOW_BUTTON_SELECTORS 七个候选）
  — 关注的**定位与前置判据**是结构化的：按七个候选选择器依序取元素（笔记浮层作者区 `.author-wrapper .follow-button`、作者主页 `.user-info .follow-button` / `.user-page .follow-button`，再裸 `.follow-button` 等兜底），对命中元素读文本含「已关注」/「互关」或 `aria-pressed==='true'` 判已关注 → 报 `ok:true reason:'already_followed'`（良性 no-op 成功，云端据 reason 区分真实新关注与 no-op）；未关注且有非零盒才取中心点；一个都不命中报 `btn_no-btn`；点击前 fresh 复检验证码。开笔记时另有一条只读探针 probeAuthorFollowed 逐字镜像同一套选择器与判定，读不到就返回 false 让云端回退主页评估流程。
- **旧代码记下的真机经验**：
  > 关注按钮两种上下文：笔记 modal 内 .author-wrapper .follow-button；作者主页 .user-info .follow-button（真实小红书主页按钮为 button.reds-button-new.follow-button）。bare .follow-button 兜底两者。

  > 已关注：目标状态（已关注）本就达成 —— 良性 no-op 成功，而非失败。以 ok:true + reason:'already_followed' 上报；云端据 reason 区分"真实新关注"（不带 reason）与"已关注 no-op"。

  > note.open 时探测笔记 modal 作者区关注按钮当下真实态（change skip-profile-visit-if-followed）。复用 executeFollow 的选择器与「已关注/互关/aria-pressed」判定，逐字镜像其扫描顺序：对 executeFollow 会判「已关注」的同一元素返回 true，会去点击（未关注）的返回 false。无按钮 / 读取失败 / 异常 → false（falsy），云端据此回退原主页评估流程。边缘只读取平台当下信号上报、不臆造（红线：MUST NOT 静默假成功）。

  > 点击前 fresh 复检验证码（fail-CLOSED）：引导性停顿已上移到命令入口 gateBeforeAction（max 非累加），此处不再叠停顿。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:229-234`（follow 与 like/collect 同一分支）、`:231`（作者身份核对）、`:232`（words=['关注','follow']）、`:52`（active）；作者已关注态上报在 `:115`（`authorFollowed:active(first(['[class*="follow"]','button'],root))`）
- **具体缺哪几样**：
  1. 定位退成 findByWords(['关注','follow']) 三级回落取首个可见元素，丢掉七个具名候选与「笔记浮层作者区 vs 作者主页」两种上下文的区分；页面上「关注」二字还出现在关注数标签、导航项等处 → 可能点到非按钮元素。
  2. 已关注判据退成通用 `active()`：不读文本「已关注」/「互关」；而 `.follow-button` 的 className 不含 `followed`，`active()` 在小红书上基本恒假 → **已关注也会被再点一次**。
  3. 已关注的终局语义变了：命中 `active()` 时返回 `ok:true reason:'already_active'`，与云端约定的 `already_followed` 不一致（云端靠 reason 区分真实新关注与 no-op）。
  4. 后置校验：sleep(450) 后单次 `active()` 采样 + 「已」字兜底（同 ⑥a）；关注按钮点后文案会变成「已关注」，所以「已」字兜底恰好是**唯一生效路径**，但它同时会被任何含「已」字的邻近文案骗到。
  5. note_detail 的 authorFollowed **事实上恒假**（router:115 对首个 class 含 `follow` 的元素调 `active()`）→ 云端「已关注则短路整条主页子链」的优化永久失效。
  6. 缺提交前 fresh 验证码复检；缺 btn_no-btn 与 no-bar 的可区分失败原因。
  7. 作者身份核对判据不同：router:231 只在 `p.authorId` 存在时从首个 `a[href*="/user/profile/"]` 抽 id 比对，取的是「详情容器里第一个用户链接」，与要关注的那个按钮不是同一个元素，绑定关系松。
- **可 port 的旧测试**：
  - `interaction.follow 已关注 → 良性 no-op 成功 ok:true + already_followed`（锁 reason 口径，正对新引擎的 `already_active`）
  - `interaction.follow 找不到按钮 → ok:false + btn_no-btn`
  - `note.open 探测到已关注 → note.detail 带 authorFollowed=true`（正对新引擎恒假）／`未关注/读不到 → authorFollowed=false`

### 未读监测体整块失活：巡视触发源消失

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`src/browse/notification-monitor.ts:1-12`（语义）、`:17-91`（入口角标探测 JS）、`:227-264`（CdpNotificationMonitor 类，sticky/epoch）；装配点在迁移前 `git show 317cd47^:src/main.ts` 的 `1413-1426`（已核对：`② 通知未读监测：无→有 上报 notification.detected`）
  — 旧实现有一个后台监测体，按固定周期在页面上探一次「消息」入口的未读角标，状态是布尔（有/无未读），计数只作附带；探测失败按 sticky 保持上一次状态、绝不把「有」清成「无」；只在无→有翻转时取一个单调递增的 epoch 并向云端发一次未读信号，云端据此启动巡视。整条巡视链路的**唯一触发源**就是这个信号。
- **旧代码记下的真机经验**：
  > 软中断 + fail-open：漏一条评论代价小，误触发巡视会打断浏览；故探测失败按 sticky 保持上次，且 MUST NOT 把未读重置为 false（那会静默丢失真通知）——sticky 正好满足"保持上次"。

  > 状态 = 是否有未读（boolean）。未读计数仅作信号附带参考，不参与翻转判定（count 3→5 仍是"有"，不重复触发）。

  > epoch：每次"无→有"翻转单调 +1，作云端去重键（不随计数变）。由上层在 onTransition(false→true) 时取 nextEpoch()。

  > 真机校准（2026-06-23）：通知入口真实结构为 <a href="/notification"><div class="badge-container"><svg class="reds-icon">…</svg><!----></div><span>通知</span></a> 其中 `badge-container` 与 `reds-icon` 图标**常驻**；未读角标是 Vue 条件渲染进 `badge-container` 的子元素（无未读时是空注释槽 `<!---->`）。旧版用 `[class*="badge"]`/`[class*="red"]` 宽选择器会命中常驻的 `badge-container`/`reds-icon`（小红书品牌即 RED，设计系统类名前缀 `reds-`），故几乎永远判「有未读」→ 没通知也反复跳通知页。

  > 新判据（结构化、类名无关）：未读 = 通知入口的角标容器里，存在**图标 svg 之外的、可见的真实角标元素**。空槽（仅图标）= 无未读。既消除假阳性，又不漏真角标（红点无数字也算未读，count 仅附带）。

  > 小红书 web 双布局（宽=左侧栏 / 窄=底部图标栏，见 docs/xhs-layout-states.md）：DOM 常【同时存在】隐藏的侧栏通知入口 + 可见的底部通知入口；旧码 querySelector 取首个 → 可能命中【隐藏】那个 → .count 不可见 → 窄布局恒判无未读（真机实测漏报 10 条未读）。

  > ② 通知未读监测：无→有 上报 notification.detected（云端协调器据此巡视「评论和@」）。
- **新引擎现状**：`src/main.ts:1043`（`if (false && platformDriver.runtimeKind === 'browser')` 把整个浏览器态监测装配段短路，段内原有的通知未读监测注册在当前树里已不复存在——`grep -n "notification" src/main.ts` 只命中 1043 这一行）；Native 侧唯一周期探针 `src/native-page-engine/browse-session.ts:460`（`if (this.options.platform !== 'facebook' … ) return;`）只服务 Facebook
- **具体缺哪几样**：
  1. 缺整个未读探测循环：Native 运行时没有任何代码探测通知入口角标。
  2. 缺 `notification.detected` 的发送方：全仓仅协议定义与退役类里出现该消息名，运行路径上无人发送 → 云端巡视链（分诊/清零/飞书）在小红书上**永不启动**。
  3. 缺 sticky 语义：无探测即无「失败保持上次」这一层。
  4. 缺单调 epoch：翻转 epoch 生成器随监测体一起退役（Native 侧改用 `Date.now()` 当 epoch，见最后一条）。
  5. 把「常驻图标 vs 条件渲染角标」的结构判据换成了页面分类用的计数：`native/page-engine/src/xhs-page-probe.js:31` 只统计 `a[href*="/notification"],[class*="notification"],[class*="notice"]` 的元素个数，供 `probe.rs:165-166` 判断「当前是不是通知页」，与「有没有未读」无关。
- **可 port 的旧测试**：
  - `buildNotificationBadgeJs: 真实无未读结构 → unread:false`（锁「常驻 badge-container + reds-icon + 空注释槽」不得判有未读）
  - `buildNotificationBadgeJs: 数字角标 → unread:true 且 count 取数字`／`红点(无数字)角标 → unread:true count:0`／`无通知入口 → unread:false`
  - `NotificationMonitor.tick: 无→有 触发一次；计数变化(仍有)不重复触发`
  - `NotificationMonitor.tick: 探测失败保持上次未读（sticky，绝不重置为 false）`
  - `NotificationMonitor.nextEpoch: 单调递增`

### 「评论和@」滚到底清零循环整块消失，scrollMax 变悬空参数

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`src/browse/browse-session.ts:3097-3147`（尤其 `:3116-3133` 的滚到底循环、`:3117` 的行计数 JS、`:3119-3120` 的 HARD_CAP / STABLE_ROUNDS）
  — 进入「评论和@」后不是固定滚几屏，而是「滚到底」：每轮先数一次列表行数，行数比上轮多就重置稳定计数，连续两轮不增即判到底停止；另设硬上限（max(云端下发上限,12) 轮）作有界兜底，每轮滚 0.8 个视口高、等 600ms 让新项加载。云端下发的 scrollMax 只当硬上限的下限参考。
- **旧代码记下的真机经验**：
  > 滚动策略（change notification-clear-to-zero）：滚到底 / 直到不再有新项（连续 STABLE_ROUNDS 次评论行数不增），有界兜底 HARD_CAP——替代旧的「固定 scrollMax 屏」：未读条数多于一屏时固定屏数会遗留未清，破坏「清零」前提。

  > scrollMax 由云端下发，此处当作硬上限的下限参考（实际上限取 max(scrollMax, HARD_CAP_FLOOR)）。

  > 滚到底：连续 STABLE_ROUNDS 次评论行数不增即判到底；HARD_CAP 防异常无限滚（诚实有界）。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:223-225`（点一次 tab、`await sleep(500)`、直接返回 notificationItems，**全程无滚动**）；参数通道 `src/native-page-engine/command-mapper.ts:61-63` 与 `native/page-engine/src/command.rs:651-662` 仍在传并校验 scrollMax，但 router 全文没有任何 `p.scrollMax` 读取
- **具体缺哪几样**：
  1. 缺滚动本身：Native 只点一次分类 tab 就抽取，抽到的永远只是首屏 DOM 里已渲染的那些行。
  2. 缺「行数不增连续 N 轮判到底」的收敛判据。
  3. 缺有界硬上限（旧为 max(scrollMax,12) 轮）——Native 无循环故也无上限，但代价是永远不覆盖首屏之外。
  4. 缺每轮的加载等待（旧 600ms/轮）。
  5. 云端下发的 scrollMax 成了悬空参数：映射层与 Rust 校验都保留它，注入脚本不读 → **云端调节滚动预算完全无效且不报错**。
- **可 port 的旧测试**：
  - `notification.browse_comments → 抽取评论/@ 原始项并上报 notification.items`（现有断言只到条数与字段，port 时应扩为「首屏 2 行 + 滚动后追加 2 行 → 上报 4 行」以锁滚到底）
  - `CDP-NOTIF-1: 通知 browse_comments 断连 → 绝不假报空 items`

### 去重键改用用户主页链（旧实现明确排除）

- **对应任务**：1.9、2.7、5.4、5.5
- **旧实现**：`src/browse/notification-monitor.ts:140-142`（规则注释）、`:158-160`（fromUserId 与 itemKey 刻意分离的注释）、`:163-164`（实现：先 `note-id` 属性、否则取第一条非 profile 链、都没有留空）；云端配套 `aidcp-cloud/src/agents/notification-deduper.ts:34-43`
  — 逐条去重键有严格优先级：① 行上的 `note-id` 属性；② 行内第一条**不是**用户主页链的链接；③ 两者都没有就留空，交给云端回退到「用户名|剥掉尾部时间的正文」。主页链被显式排除，因为它是按发送者折叠的：同一个人的多条评论会撞成同一个键，第二条起被当成「已通知」静默丢弃。行内的主页链另有用途——解析出发送者的稳定主页 ID 填 fromUserId 这个独立身份字段，与去重键互不影响。
- **旧代码记下的真机经验**：
  > **itemKey 取 note-id 属性 或 非 profile 链**：profile 链 per-user 会把同人多评论去重键撞成一个 → 折叠丢失；都没有则留空（评论类即如此），交云端回退到 用户名|正文 去重键（正文已不含时间、跨巡视稳定）。

  > 主页ID（稳定身份，change notification-contact-registry）：从行内头像/昵称的 /user/profile/<id> 解析。

  > 注意：itemKey 仍刻意排除 profile 链（评论去重需保各评论独立）；fromUserId 是独立的身份字段，互不影响。

  > 行内**只有 profile 链、无 per-comment permalink**（赞类行带 `note-id` 属性、评论类无）。

  > 去重主键：优先用边缘给的**稳定且 per-comment 的** itemKey；缺失（或仅 per-user profile 链——会把同人多条评论撞成一个键、静默折叠丢失，故排除）则退化为 用户名|剥时间后的正文。

  > 回退去重键含正文，而平台把时间戳渲染在评论行**末尾**；跨巡视时间会漂移（「3分钟前」→「8分钟前」）→ 同一条评论键变化 → 重复打扰（NCQ-3）。剥掉尾部时间戳后键跨巡视稳定。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:132`（`itemKey:norm(root.getAttribute('data-id')||href||raw,256)`，其中 `href` 取自 `:129-130` 的 `a[href*="/user/profile/"]`）
- **具体缺哪几样**：
  1. 把主页链放进 itemKey 的第二优先级，正是旧实现点名排除的那一类键。
  2. 属性名从真机标定的 `note-id` 换成 `data-id`（真机 dump 记录的属性是 `note-id`，且只有赞类行有、评论类行没有）→ 唯一逐条稳定的键源永远取不到。
  3. 第三顺位从「留空」换成「整行文本」：`raw` 含时间（「3分钟前」），而云端 stripRelativeTime 只剥**尾部**时间、这里时间在中段 → 同一条评论每趟都换键 → 重复推飞书。
  4. 丢掉「itemKey 留空 → 云端回退键」这条协作路径：Native 恒有非空 itemKey，回退键永不启用。
  5. fromUserId 与 itemKey 的职责分离形式仍在，但 itemKey 也吃了主页链，分离已失去意义。
  6. 云端两条消费路径受影响不同：`aidcp-cloud/src/agents/notification-deduper.ts:41` 对含 `/user/profile/` 的 itemKey 有防御性排除（撞不成一个键，但会掉进含时间的正文回退键 → 重复打扰）；`aidcp-cloud/src/cache/notification-contact-store.ts:113-115` 无此排除，直接把主页链当笔记锚点写进联系人事件去重键 → **同人多条评论在名册侧真折叠**。
- **可 port 的旧测试**：
  - `buildNotificationItemsJs(NB-5): itemKey 取 note-id 属性 / 非 profile 链；仅 profile 链则留空`（三段断言；可直接 port 成 Rust 引擎契约：同一发送者两行 → itemKey 互不相同或均为空）

### 正文直接取整行文本（含昵称、动作标签、时间）

- **对应任务**：1.9、2.7
- **旧实现**：`src/browse/notification-monitor.ts:132-135`（行结构：时间是独立元素、不在正文里；回复型的被引原评论不取）、`:140`（缺失发空串的规则）、`:157`（`userEl` 只取 `.user-info a`）、`:169`（`content: cut(contentEl && contentEl.textContent || '', 200)`）
  — 只从行内的正文容器取正文，别的元素一概不进：昵称在另一个容器、动作标签是独立 span、时间也是独立元素（「2天前」或「05-15」），回复型通知里还有一块被引用的原评论也刻意不取。正文容器不存在时发空串，绝不回退成整行文本——空串会被云端非空过滤丢弃，等于诚实地说「这条没有正文」；回退整行则会把昵称+动作+时间糊成一团发到飞书。
- **旧代码记下的真机经验**：
  > **正文缺失发空串**：绝不回退整行 textContent（避免飞书 blob）；空串由云端非空过滤丢弃 = 诚实无正文。

  > `span.interaction-time`（时间：「2天前」或日期「05-15」，**独立元素、不在正文里**）

  > `div.interaction-content`（**正文**；回复型另有 `div.quote-info`=被引原评论，不取）

  > 昵称（避开空文本的 a.user-avatar）

  > 正文（不含时间、不取 quote-info）
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:128`（`const raw=text(root,2200); if(!raw)return null;`）、`:132`（`content:raw`）
- **具体缺哪几样**：
  1. 缺正文容器定位：Native 直接把整行 innerText 当正文。
  2. 正文里混入昵称、动作标签（评论了你的笔记）、时间（「2天前」）以及回复型的被引原评论。
  3. 缺「正文缺失发空串」这条诚实回落：Native 恒非空（`if(!raw)return null` 只在整行都空时丢弃整行）。
  4. 正文长度上限从 200 放到 2200，且是整行文本 → 飞书侧回到 blob。
  5. 副作用打到去重：含时间的正文进了云端回退去重键，使键跨巡视漂移（见上一条）。
  6. 副作用打到云端非空过滤：无正文的行现在也带着「昵称+动作+时间」通过过滤 → 被当成有内容的评论进入分类与推送。
- **可 port 的旧测试**：
  - `buildNotificationItemsJs: 真实行结构 → 昵称取 .user-info a、正文取 .interaction-content`（断言 content 等于纯正文且不含时间）
  - `buildNotificationItemsJs(NCQ-1): 无 .interaction-content → content 空串`（绝不回退整行成 blob；可直接 port 成 Rust 引擎契约测试）

### 行选择器从真机 dump 结构退回模糊 class 猜测 + 裸列表项

- **对应任务**：1.9、2.7、5.5
- **旧实现**：`src/browse/notification-monitor.ts:128-138`（真机 dump 的行结构与「据此换掉旧猜测选择器」的原因）、`:148`（`document.querySelectorAll('.tabs-content-container > .container')`）、`:151-155`（动作标签 span 判类 + 非评论/@/提及的结构异常行跳过）
  — 行容器是 2026-06-24 活页面 dump 校准出来的两级结构（列表容器 > 直接子行），并明确记下这是为了替换掉此前的模糊 class 猜测。选出行以后还按行内动作标签的文字判类（评论/回复/提到），文字对不上的结构异常行直接跳过，不猜。
- **旧代码记下的真机经验**：
  > 真机校准（2026-06-24，活页面 CDP dump）——真实行结构：`div.tabs-content-container > div.container`（每条一行，共 ~20 条）

  > 据此换掉旧猜测选择器（旧 `[class*="item"]` 命中 23 个 `avatar-item` 头像→垃圾行；旧 `[class*="user"]` 先命中空文本的 `a.user-avatar`→昵称抽空）。

  > if(!isMention && !isComment) continue; // 非评论/@/提及（结构异常行）跳过
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:126`（`all('[class*="notification-item"],[class*="notice-item"],[class*="message-item"],li')`）、`:131`（kind 用 expected 或整行文本猜）
- **具体缺哪几样**：
  1. 行容器换成三个 class 模糊匹配——真机 dump 记录的行 class 是 `container`、父容器是 `tabs-content-container`，这三个模糊 pattern **一个都不命中**。
  2. 额外加了裸 `li` 兜底：页面侧栏导航、菜单、任何列表项都会被当成通知行。
  3. 缺「列表容器 > 直接子行」的两级约束 → 无法排除嵌套的头像/子块。
  4. 缺「动作标签文字对不上就跳过」的结构异常过滤：Native 在 expected 已给定时把任何命中行都归成该类 → 垃圾行原样变成通知项。
  5. 赞/收藏行的类别区分丢失：赞和收藏 tab 下所有行一律标 like，永远不产 collect。
- **可 port 的旧测试**：
  - `buildNotificationItemsJs: 真实行结构 → 只抽 1 行（不被 a.user-avatar/avatar-item 头像污染成多行）`
  - `buildNotificationItemsJs(NB-5) 的三段夹具`（真实 container 行 + 头像链接 + 额外链接）可直接复用为「头像行 / 裸 li / 真实通知行混排 → 只产出真实行」的契约夹具

### 赞/收藏、新增关注两类「看一眼」不再产动作回执，未命中也不 no_target

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`src/browse/browse-session.ts:3149-3213`（尤其 `:3161-3173` 的点击命中布尔 → no_target，`:3204-3205` 的 viewed 回执，`:3206-3210` 的失败如实回执，`:3195-3203` 的发送者抽取失败不阻断清零回执）
  — 旧实现把「赞和收藏」「新增关注」两类当成动作：点分类栏目时捕获点击是否真命中，没命中就如实回 no_target（暴露选择器漂移），命中并看完回 viewed 成功回执，抽发送者失败只记日志、绝不阻断清零回执，整体失败按真实原因回 ok:false。这两个回执是云端分诊闭环的接力点。
- **旧代码记下的真机经验**：
  > 捕获点击命中布尔：未命中分类 tab（选择器漂移/页面未渲染/单合并 tab）→ 诚实 no_target，**绝不**像旧码那样丢弃返回值、无条件报 viewed（那是静默假成功，且掩盖了 6.5.4 本要暴露的选择器漂移）。

  > 清零仍是首要目的（保 notification-clear-to-zero 语义）；发送者抽取是清零旁路只读输出，抽取失败绝不阻断下方清零回执。

  > 抽取发送者（点赞/收藏 或 关注）→ notification.items（云端沉淀进通知联系人名册）。best-effort、待真机校准；抽取失败只记日志、绝不阻断下方清零回执（清零是首要目的）。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:223-225`（三类通知浏览命令一律返回 notification_items 输出）；上报侧 `src/native-page-engine/browse-session.ts:340-342`（notification_items 只 `send('notification.items')`，不产 action.completed）
- **具体缺哪几样**：
  1. 缺 action.completed 回执：Native 对赞/关注两类只上报 notification.items，云端 `aidcp-cloud/src/agents/notification-follow-browser.ts:35-38` 那类角色等的回执永不到 → 该类永不 category_handled → 分诊循环卡住直到巡视总超时。
  2. 缺 no_target：tab 没点到时走 ambiguous(notification_tab_unconfirmed)，语义不是「没这个目标」而是「不确定」，且同样不带 action.completed。
  3. 缺「抽取失败不阻断清零回执」的分层：Native 抽取与回执是同一条返回值，抽取一旦落空就什么都没确认。
  4. 缺提交窗口保护（见下一条）。
- **可 port 的旧测试**：
  - `notification.browse_likes → 看一眼清未读 + 如实 action.completed 回执`
  - `NM-C-1: 看一眼未命中分类 tab → ok:false reason:no_target`
  - `失败不静默吞：cdp 抛错 → items 上报空 + likes 回执 ok:false`

### 通知首页 per-tab 未读计数退成整页正文正则

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`src/browse/notification-monitor.ts:93-123`（尤其 `:96-98` 点名不许用宽 class + isNaN→1，`:100-105` 真机 dump 的 tab 结构与收窄到叶子 tab 的理由，`:110-120` 只在真实 tab 内认纯数字叶子角标）、共享判据 `:43-69`（numericOnly 分支的 1-3 位数字 + 叶子节点守卫）
  — 只在真实的三个叶子分类 tab 内部找角标，且只认纯数字、只认叶子节点、只认 1-3 位（排除时间戳/子计数/包裹容器），找不到就诚实回 0；tab 范围刻意收到叶子 class，把同样带 tab 字样的包裹容器排除掉，因为包裹容器的拼接文本会把一类的角标数字泄漏给另一类。它明确禁止两种做法：宽 class 猜角标、以及「解析不出数字就当 1」。
- **旧代码记下的真机经验**：
  > **绝不**沿用旧 `[class*="badge"]/[class*="red"]` 宽选择器 + `isNaN→1`——那正是 6.5.3 在入口探测点名删掉的假阳性源（命中常驻 reds-icon/badge-container），会让没未读也每类报「1」→ 无谓进各子分类、优先级失真。

  > **tab 范围收到 `[class*="tab-item"]`**：只命中三个真实叶子 tab，排除同样含 `[class*="tab"]` 的包裹容器（`reds-tabs-list` / `sticky-tab` / `tabs-content-container`，其拼接文本会把一类角标泄漏给另一类 = 复审 NM-2）。

  > 角标只可能是 1-3 位数字（≤999；「99+」含 + 不匹配，自然落到无数字红点→0）且为叶子节点。排除多位时间戳 / 子计数 / 含数字子文本的包裹被误当角标（NM-3 部分硬化）。

  > 真机双向验证：赞和收藏有真实未读→likes:1，看一眼清除后→0，清空账号三类全 0（无 phantom）。

  > 仅在该 tab 内见到纯数字角标才计数；否则保守 0
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:136-140`（`const body=text(document.body,5000)` + `new RegExp(word+'[^0-9]{0,8}([0-9万w千k.]+)')`）
- **具体缺哪几样**：
  1. 缺 tab 作用域：拿整页正文（前 5000 字）做正则，页面上任何「赞」后面 8 字符内的数字都会被当成未读计数（笔记赞数、粉丝数、页面 chrome 里的计数）。
  2. 缺「只认纯数字叶子角标」与「1-3 位」守卫 → 会吃到万/千单位与多位时间戳（`count()` 还会把「1.2万」折算成 12000 条未读）。
  3. 缺包裹容器排除（NM-2 跨类泄漏）：整页文本本身就是最大的一次泄漏。
  4. 缺「找不到就 0」的保守：正则命中即产计数。
  5. **⚠️ 第 5 条原写「方向反转成宁可虚报 → 云端跑到尝试上限空转」，实测订正为相反且更重（2026-07-28，1.16 用例意外为绿时查出，主 session 独立复核）**：`:164` 的 `named('赞|like')` 拼出 `赞|like[^0-9]{0,8}([0-9万w千k.]+)`，`|` 的优先级使其分为 `赞` 与 `like[^0-9]{0,8}(...)` 两支，**中文支不带捕获组**。实测 `"赞 312".match(re)` → `["赞", null]`；`"like 312"` → 捕获 `312`。**中文界面下三栏计数恒 0**，与页面上有无角标无关。云端 `notification-triage.ts:65` 是 `if (counts[cat] <= 0) continue; // 已清零，跳过` ⇒ 三栏恒 0 使**每一类都被当成已清零跳过，整条通知巡视静默什么都不做**，真实评论与 @ 永不被处理。这是静默假成功，不是空转。上面 2/3 条描述的「万/千折算」「多位数字」在中文界面上因此实际不可达（英文界面仍可达）。
  6. 由 5 推出的额外验收要求：修复后必须在中文与英文两种界面文案下都读出真实计数，且「三栏全 0」与「读不到」必须可区分。
- **可 port 的旧测试**：
  - `buildNotificationHomeJs: 全已读（无数字角标）→ 三类全 0`／`赞和收藏有真实数字角标 1 → likes:1，其余 0`
  - `buildNotificationHomeJs: 角标位仅常驻 reds-icon → 全 0`（回归 6.5.3 假阳性，绝不再 isNaN→1）
  - `buildNotificationHomeJs(NM-3): tab 内多位数字子文本(时间戳/子计数)不被当角标 → 0`
  - `buildNotificationHomeJs(NM-2): 真实包裹容器 reds-tabs-list 不被当 tab → 角标不跨类泄漏`
  - `buildNotificationHomeJs: 页面 chrome 里的「赞」按钮(非 tab)带数字 → 不被误读`（正是 Native 整页正则必然失败的用例）

### 分类 tab 点击从叶子结构选择退成全页文本模糊查找

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`src/browse/browse-session.ts:3112-3114`（评论 tab：遍历叶子 tab、文本严格等于「评论和@」或以评论开头且含 @）、`:3166-3167`（赞/关注 tab：叶子 tab + 文本长度 ≤8 放宽给角标数字）
  — 点分类栏目时只在真机标定的叶子 tab 集合里挑，且用文本严格匹配，明确避免全页文本匹配点到包裹容器。
- **旧代码记下的真机经验**：
  > 真机校准（2026-06-24）：真实分类 tab = [class*="tab-item"]（叶子），点它而非全页文本匹配（避免点到包裹容器）。

  > 真机校准（2026-06-24）：分类 tab = [class*="tab-item"]（叶子，文本如「赞和收藏1」含角标数字故放宽到 <=8）。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:224`（`findByWords(['赞和收藏','赞','like'] …)`）、判据实现 `:145-152`、确认用 `:53` 的 `selected()`
- **具体缺哪几样**：
  1. 缺叶子 tab 作用域：在整页按 button/a → span → div 三级找「文本含赞/关注/评论」的第一个可见元素，页面上任何带这些字的按钮、笔记卡片、侧栏项都可能被点。
  2. 缺严格文本判据：从「整串相等 / 长度上限」退成 includes 子串包含。
  3. 缺包裹容器排除：三级回落里的 div 一层最容易命中 tab 列表包裹容器 → 点到容器等于没切 tab。
  4. 确认改用通用 `selected()` 猜激活态，旧实现是用点击命中布尔 + 后续行为，未命中即 no_target。
- **可 port 的旧测试**：
  - `NM-C-1: 看一眼未命中分类 tab → ok:false reason:no_target`（夹具即「tab 点击 JS 返回 false」，port 后可锁「页面只有含赞字的非 tab 元素时不得判成功」）

### 无身份行不再跳过，昵称回落成 unknown

- **对应任务**：2.7（「无逐条身份时留空」那一半）、5.5
- **旧实现**：`src/browse/notification-monitor.ts:184`（注释：诚实——无身份的行跳过）、`:209`（`if(!fromUser && !fromUserId) continue;`）
  — 在赞/关注两类抽发送者时，昵称与主页 ID 都为空的行直接跳过，不把空联系人写进名册——注释把这条明确叫「诚实」。
- **旧代码记下的真机经验**：
  > **best-effort，待真机校准**：这两栏的真实行 DOM 未经活页面 dump，此处沿用评论栏的 `.tabs-content-container > .container` 行容器 + `.user-info a` 昵称 + 头像 `/user/profile/` 主页ID 假定；上线前须按真机结构校准（tasks 8.3），校准前宁可少抽不可瞎报。诚实：无身份(昵称且主页ID皆空)的行跳过。

  > 复用 code-point 安全截断；正文恒空（互动型无正文），noteTitle 仅点赞/收藏型尝试。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:132`（`fromUser:text(author,200)||'unknown'`，无身份不跳过）
- **具体缺哪几样**：
  1. 把「无身份 → 跳过」换成「无身份 → 昵称填字符串 unknown」，等于凭空造一个联系人身份。
  2. 叠加行选择器退化后果更重：被 `li` 兜底捞进来的页面 chrome 行也会带着 unknown 身份进云端联系人名册。
  3. 云端 `aidcp-cloud/src/cache/notification-contact-store.ts:113-115` 的身份取值是 主页ID > 昵称 > 空，`unknown` 会被当成一个真实昵称参与去重键。

### 截断从 code-point 安全退回 UTF-16 slice

- **对应任务**：本 change 无对应任务（2.7 只提行/正文/itemKey/身份，未含截断）—— 见文末覆盖漏洞
- **旧实现**：`src/browse/notification-monitor.ts:139`（规则注释）、`:146`（`function cut(s,n){ … var a=Array.from(s); return a.length>n ? a.slice(0,n).join('')+'…' : s; }`）、`:189`（分类抽取复用同一 cut）
  — 按 code point 数组切，超长补省略号，绝不在 emoji 的代理对中间劈开。
- **旧代码记下的真机经验**：
  > **code-point 安全截断**：绝不按 UTF-16 劈裂 emoji 代理对（否则飞书尾部乱码 U+FFFD）；超长补省略号。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:6`（`const norm=(v,n=2000)=>String(v??'').replace(/\s+/g,' ').trim().slice(0,n);`，通知项各字段经 `:21` 的 `text()` 与 `:132` 统一走这条 slice）
- **具体缺哪几样**：
  1. 截断实现从 code-point 数组切换成 UTF-16 `String.slice` → 边界落在代理对中间时产生半个字符（U+FFFD 乱码）。
  2. 缺超长补省略号的可见标记。
  3. 上限也从 200（正文）/40（昵称）/80（笔记标题）统一放成 2200/200 量级，配合整行文本一起变成 blob。
- **可 port 的旧测试**：
  - `buildNotificationItemsJs(NCQ-2): 超长正文按 code-point 截断 + 省略号，绝不劈裂 emoji 代理对`（用例已把第 200 个 code point 造成 emoji，可原样 port）

### 分类栏目点击丢失提交窗口保护（小红书侧未接线）

- **对应任务**：本 change 明示不做（design.md:59），由同批 `restore-native-xiaohongshu-session-guards` task 2.1/2.2 承接（`xhs_notification_comments` / `xhs_notification_likes` / `xhs_notification_follows` 各 20 000ms）；本 change 侧只在 6.3 做集成对账
- **旧实现**：`src/browse/browse-session.ts:3105-3109`（评论栏）、`:3156-3163`（赞/关注栏）
  — 把分类栏目的点击包在一个 20 秒提交窗口里，理由是这一次点击会**消费平台未读且不可回滚**，所以窗口必须覆盖点击那一刻；点击之后的确认与滚动是只读的，窗口过期也安全。早退（no_target）和正常结束都由 finally 关窗。
- **旧代码记下的真机经验**：
  > 提交窗口守卫（5.1）：分类栏目点击**消费未读、无回滚** ⇒ 窗口 MUST 覆盖点击那一刻；确认/滚动尾段只读，超预算自动过期也安全。

  > 提交窗口守卫（5.1）：分类栏目点击消费未读、无回滚 ⇒ 窗口 MUST 覆盖点击；早退(no_target)/尾段都由 finally 关窗。
- **新引擎现状**：`src/native-page-engine/browse-session.ts:236-238`（`this.options.platform === 'facebook' && this.options.commitWindow ? … : undefined` —— 提交窗口只对 Facebook 生效，小红书命令一律传 undefined）
- **具体缺哪几样**：
  1. 小红书的通知命令完全不进提交窗口：点击已消费未读、随后断连或被抢占时，系统会把这次已既成的动作当成「未开始」。
  2. Native 侧提交窗口的接线条件写死为 `platform==='facebook'`，不是按命令是否有不可回滚副作用判断。

### epoch 语义从单调翻转序号改成墙钟时间戳

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞（且 `oracleQuality: none`，无对照物可抄）
- **旧实现**：`src/browse/notification-monitor.ts:9`（epoch 语义）、`:260-263`（nextEpoch 单调 +1）；旧上报侧 `src/browse/browse-session.ts:3138` 与 `:3087` 都**不带** epoch（epoch 只在 notification.detected 上出现，由监测体翻转时生成）
  — 旧设计里 epoch 只有一个来源：未读监测体在无→有翻转时取的单调序号，一波未读一个稳定值，用于云端关联与观测。列表/首页上报本身不带 epoch。
- **旧代码记下的真机经验**：
  > epoch：每次"无→有"翻转单调 +1，作云端去重键（不随计数变）。由上层在 onTransition(false→true) 时取 nextEpoch()。
- **新引擎现状**：`native/page-engine/src/xhs-command-router.js:134`（`{items,epoch:Date.now()}`）、`:139`（notification_home 同样带 `epoch:Date.now()`）；透传到云端 `aidcp-cloud/src/comm/handler.ts:741-758`
- **具体缺哪几样**：
  1. 注入脚本自己造了 epoch，值是墙钟毫秒，每条上报都不同 → 同一波未读的多次上报不再共享同一个 epoch，云端按 epoch 的关联/日志失去意义。
  2. 与真正的翻转 epoch 失去任何对应关系（且翻转源已随监测体失活，见上文第一条通知项）。

---

## 覆盖漏洞

参照书里有、但本 change 的 tasks 里找不到对应任务的条目（按后果排序）。共同点：这批全在**通知巡视**上，而本 change 的通知任务（1.9 / 2.7）只覆盖了「抽取三处退化」（行选择器 / 正文 / 去重键），把巡视链路的**触发、覆盖面、回执、计数、tab 命中**五处漏在外面。

1. **未读监测体整块失活（巡视触发源消失）** — 最重。`notification.detected` 在运行路径上无人发送，云端整条巡视链在小红书上**永不启动**；也就是说 1.9 / 2.7 修好的抽取契约在生产里根本跑不到。
   建议：本 change 只做页面规则、不碰宿主装配（design D6），故此条应落到同批 `restore-native-xiaohongshu-session-guards`（它已在 task 6.1/6.4 逐条对账那段恒假装配块，通知未读监测正是块内被删掉的第②项，天然是它的归属）；若该 change 也不收，须单起一个 change 并在本 change tasks 6.4 登记依赖，否则本 change 的通知部分是「修了但不通电」。
2. **赞/收藏、新增关注两类不产 action.completed 回执** — 云端两个分类浏览角色永远等不到回执 → 该类永不 category_handled → 分诊循环卡到巡视总超时。与本 change 已在做的「看图不产回执」（2.3）是同一种病、同一处修法。
   建议：加进本 change 第 2 节（回执诚实），并补一条失败在先的测试（未命中 tab → `no_target` + `ok=false` 回执）。
3. **「评论和@」滚到底清零循环整块消失，scrollMax 成悬空参数** — 只抽首屏，未读多于一屏时永远清不零；云端调滚动预算完全无效且不报错（映射层与 Rust 校验都还在传）。
   建议：加进本 change 第 2 节。至少要做到「不读的参数不许留在契约上」——要么恢复滚到底循环，要么显式拒绝该参数，不能继续静默丢。
4. **通知首页 per-tab 未读计数退成整页正文正则** — 计数永不归零 + 「1.2万」被折算成 12000 条未读，云端「循环到三栏清零」的判据被喂假值。方向从「宁可漏报」反转成「宁可虚报」，属本 change 反的同一类退化。
   建议：加进 2.7（把它从「行/正文/去重键三处」扩成「抽取四处」），旧测试六条可整组 port。
5. **分类 tab 点击退成全页三级文本模糊查找** — 与 2.5 反的「点赞控件文本三级回落」是同一个 `findByWords` 判据、同一种失败模式（点到包裹容器等于没切 tab，且用 `selected()` 猜激活态）。
   建议：并进 2.5 的「结构化定位」要求，把作用域约束写成「叶子 tab + 严格文本」，别只覆盖互动控件。
6. **通知项截断从 code-point 安全退回 UTF-16 slice** — 后果小但确定发生（飞书尾部 U+FFFD 乱码），且旧测试 NCQ-2 可原样 port。
   建议：并进 2.7 的正文抽取要求，一句话即可（「截断按 code point、超长补省略号」）。
7. **epoch 语义从单调翻转序号改成墙钟时间戳** — 依附于第 1 条：翻转源不恢复，epoch 无从谈起。
   建议：与第 1 条同处落地，并同时要求「列表/首页上报不自造 epoch」。

另有一条**不是漏洞、已具名转交**：分类栏目点击的提交窗口保护，本 change design.md:59 明写「不做，归 `restore-native-xiaohongshu-session-guards`」，该 change task 2.1 已逐处标定预算（20 000ms）。本 change 只需在 tasks 6.3 的集成对账里核对它已生效。
