> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 表征当前退化（失败优先）

- [x] 1.1 新建 `test/native-page-engine/xhs-behavior-parity.test.ts`，加一条失败用例：带联系方式串码的评论命令，断言提交进编辑器的文本同时含正文与串码（当前实现只含正文，必失败）（参照 src/browse/browse-session.ts:2543-2553；串码须单独整段插入绕开 @/# 补全 — 见 oracle.md ②） <!-- aidcp-edge 552eda1 已由 2.1 转绿 -->
- [x] 1.2 加失败用例：开帖后页面处于「笔记暂时无法浏览」错误页且地址仍含笔记 id，断言返回非成功且不产出 `note_detail` 输出（参照 src/browse/browse-session.ts:1876-2036；缺错误页否决/正面详情证据/令牌门控 — 见 oracle.md ①） <!-- aidcp-edge 552eda1 幂等早退与点击后两条路径各一例；已由 2.2 转绿 -->
- [x] 1.3 加失败用例：详情容器存在但标题、正文、图片三项皆空，断言返回 ambiguous 而非确认详情（参照 src/browse/browse-session.ts:2067-2110 正文渲染门 + note-extractor.ts:283-292；缺渲染门与选择器排除 — 见 oracle.md ①） <!-- aidcp-edge 552eda1 已由 2.2 转绿 -->
- [x] 1.4 加失败用例：看图命令断言输出为动作回执且回执带实际前进张数；无轮播时断言 `no_target` 回执（参照 src/browse/browse-session.ts:2797-2844；旧回执即 no_target / browsed=N — 见 oracle.md ⑤） <!-- aidcp-edge 552eda1 两例仍红，待 2.3 -->
- [x] 1.5 加失败用例：翻页控件在第一次前进后被替换，断言回执张数等于实际观察到的前进次数、不等于请求张数（参照 同上 2807-2844；旧实现循环内重解析控件、点不动即 break，但**无图序前进校验**需新写 — 见 oracle.md ⑤） <!-- aidcp-edge 552eda1 仍红，待 2.3 -->
- [x] 1.6 加失败用例：返回列表后落在非列表面，断言动作回执 `ok=false`（参照 src/browse/browse-session.ts:2735-2795；⚠ 旧回执 :2794 恒真、不可照抄 — 见 oracle.md ④） <!-- aidcp-edge 552eda1 仍红，待 2.4 -->
- [x] 1.7 加失败用例：页面同时存在互动条内具名点赞控件、聚合赞数控件、含「取消赞」文本的反向控件，断言只解析到互动条内的那一个；互动条缺失时断言 `control_not_found`（参照 src/browse/browse-session.ts:2298-2360 + flows/anchors.ts:46-64；互动栏无 aria/无文本，唯一锚点是语义 class — 见 oracle.md ⑥a/⑥b） <!-- aidcp-edge 552eda1 两例仍红，待 2.5 -->
- [x] 1.8 加失败用例：控件在首次采样之后、有界窗口之内才翻转，断言判成功；全程不翻转断言 ambiguous `state_unchanged`，且控件文本含「已」不得提成成功（参照 同上 2339-2341；真机翻转 300–600ms、上限 1500ms — 见 oracle.md ⑥a） <!-- aidcp-edge 552eda1 三例仍红，待 2.6 -->
- [x] 1.9 加失败用例：通知列表同时含头像行、裸列表项与真实通知行，断言只产出真实通知行；同一发送者的多条通知断言 itemKey 互不相同或为空；无正文容器时断言正文为空串且不回落整行文本（参照 src/browse/notification-monitor.ts:148/163-164/169；行容器两级、正文缺失发空串、itemKey 排除主页链 — 见 oracle.md 通知三条） <!-- aidcp-edge 552eda1 三例仍红，待 2.7 -->
- [x] 1.10 加失败用例：滚动评论区后评论区位置未变，断言动作回执 `ok=false`；另一例断言回执里的评论条数等于滚动后页面上实际可见的条数、不等于请求的步数（当前实现恒 `ok:true` 且直接回报请求值，两例必失败）（参照 src/browse/browse-session.ts:2797-2844 同族 scrolled=N / no_scroll 回执 — 见 oracle.md ⑤） <!-- aidcp-edge 552eda1 两例仍红，待 2.4a -->
- [x] 1.11 加失败用例：看图翻页过程中新加载出的图片，断言仍随本次命令到达云端（不因终局改成动作回执而丢掉图片证据）；同时断言本次命令只有一个终局（参照 src/browse/browse-session.ts:1284-1311 refreshOnly 快照；旧规则=抽不到图不发、失败不伪造快照 — 见 oracle.md ⑤） <!-- aidcp-edge 552eda1 仍红，待 2.3a -->
- [x] 1.12 修 `test/native-page-engine/router-contract.test.ts:37-39` 的夹具：不再在 `HTMLElement.prototype` 上全局钉死 `getBoundingClientRect`（当前返回固定 100×40，使 `xhs-command-router.js:7-12` 的宽高判定恒真），改为按用例给定几何，使可见性判断在测试里可真伪两态；修完重跑既有小红书路由用例并记录因此暴露的既有失败。**只改小红书那份契约测试，`facebook-router-contract.test.ts` 的同款夹具属 Facebook 平价 change，不动**（参照 oracle.md ⑥a 末条：router-contract.test.ts:34-36 钉死几何使 :84 那条互动用例无保护力） <!-- aidcp-edge 552eda1 几何改按元素给定（新增 test/native-page-engine/xhs-dom-fixture.ts）；facebook-router-contract.test.ts 未动；重跑既有小红书路由用例 7/7 全过，夹具修正未暴露任何既有失败 -->

- [x] 1.13 加失败用例：页面规则层的未读角标读数——宽 / 窄双布局 DOM 同时存在隐藏侧栏入口与可见底部入口时断言取可见那个；角标容器里只有常驻图标与空槽时断言「无未读」；数字角标断言「有未读」且计数带出；无数字红点断言「有未读」计数 0；读不到入口时断言返回「读不到」而非「无未读」（当前 Native 无任何未读读数，全部必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:17-91`；判据为 2026-06-23 真机校准、须按 5.8 复核 — 见 oracle.md 未读监测体条） <!-- aidcp-edge a45fc81 三例落在 xhs-notification-parity.test.ts（双布局取可见入口 / 常驻图标+空槽=无未读 / 读不到≠无未读，无数字红点算未读并入第二例）；已由 2.9 转绿 -->
- [x] 1.14 加失败用例：「赞和收藏」「新增关注」两类命令断言产出动作回执，动作名与云端角色等待的规范名一致（`browse_notification_likes` / `browse_notification_follows`，见 `aidcp-cloud/src/agents/notification-like-browser.ts:36`、`notification-follow-browser.ts:35`）；分类栏未命中时断言 `ok=false` + `no_target`；发送者抽取失败时断言清零回执仍产出（当前只上报 `notification.items`、不产回执，必失败）（参照 `317cd47^:src/browse/browse-session.ts:3161-3173/3195-3210` — 见 oracle.md「看一眼」条） <!-- aidcp-edge a45fc81 三例（规范名回执 / 分类栏未命中 no_target 且不误触其他元素 / 抽取失败仍回清零回执）；已由 2.11 转绿 -->
- [x] 1.15 加失败用例：「评论和@」栏首屏 2 行、滚动后追加 2 行 → 断言上报 4 行；另一例断言云端下发的滚动上限真参与循环上限（当前点一次栏就抽取、`p.scrollMax` 全文零读取，两例必失败）（参照 `317cd47^:src/browse/browse-session.ts:3116-3133` 的行数不增判到底 + `max(scrollMax,12)` — 见 oracle.md 清零循环条） <!-- aidcp-edge a45fc81 两例（滚动后才加载的行仍被覆盖 / 下发的滚动预算真参与循环上限）；已由 2.10 转绿 -->
- [x] 1.16 加失败用例：通知首页三栏未读计数——页面正文里出现「赞 312」这类非分类栏计数时断言不被读成未读；分类栏角标文本为「1.2万」时断言不折算成条数；三栏均无数字角标时断言全 0（当前取整页前 5000 字做正则，三例必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:93-123` 的叶子 tab 作用域 + 1–3 位纯数字叶子守卫 — 见 oracle.md per-tab 计数条） <!-- aidcp-edge a45fc81 三例齐备；其中两例落笔时意外为绿，查出原任务把失效方向记反了（见 2.12 实测订正）；已由 2.12 转绿 -->
- [x] 1.17 加失败用例：页面只存在含「赞」「关注」字样的非分类栏元素（笔记卡片 / 侧栏项 / 包裹容器）时，断言分类栏点击诚实回未命中，不得点到包裹容器、也不得按类名激活态猜成成功（参照 `317cd47^:src/browse/browse-session.ts:3112-3114/3166-3167` 的叶子 tab + 严格文本判据 — 见 oracle.md 分类栏点击条） <!-- aidcp-edge a45fc81 一例：无叶子分类栏时诚实报未命中且全程不触发任何其他元素的点击；已由 2.13 转绿 -->
- [x] 1.18 加失败用例：通知项正文第 200 个 code point 落在 emoji 上时，断言截断不劈裂代理对且补省略号（当前 `xhs-command-router.js:6` 按 UTF-16 `slice`，必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:146` 的 `Array.from` 截断 — 见 oracle.md 截断条） <!-- aidcp-edge a45fc81 一例；已由 2.14 转绿 -->
- [x] 1.19 加失败用例：断言通知列表与通知首页上报里不含页面规则自造的墙钟批次序号（现为 `xhs-command-router.js:134/139` 的 `epoch:Date.now()`）；该字段在协议里是可选（`src/comm/protocol.ts:1782/1790`），去掉不动协议（参照 oracle.md epoch 条：批次序号唯一来源是未读「无→有」翻转，本 change 只禁自造） <!-- aidcp-edge a45fc81 一例，两处上报一并断言；已由 2.15 转绿 -->
  - 进度说明（2026-07-29，取代 07-28 那条）：1.13–1.19 的失败优先用例**已进提交** `a45fc81`（`test/native-page-engine/xhs-notification-parity.test.ts`，405 行 / 13 例，落笔时 11 红 2 绿）。07-28 记的「未追踪状态、未进任何提交、集成前须由属主提交」这一风险**已消解**，覆盖不会再随分支合并丢失。13 例与 1.13–1.19 逐条对得上（未读读数 3 / 两类回执 3 / 清零循环 2 / per-tab 计数 3 / 严格叶子分类栏 1 / code-point 截断 1 / 禁自造批次序号 1），故本轮据实勾选；13 例已全部由 2.9–2.15 的实装（`19d4872`）转绿。

## 2. aidcp-edge — 恢复动作诚实（两条 critical 优先）

- [x] 2.1 在小红书评论路径合成「正文 + 联系方式串码」的完整提交文本，提交前回读校验覆盖合成后的完整文本；回读不含串码即在提交前返回 not_started，不派发提交（参照 src/browse/browse-session.ts:2450-2648；缺清场闸/串码整段插入/提交三态 — 见 oracle.md ②） <!-- aidcp-edge 8b99183 只改 native/page-engine/src/xhs-command-router.js；加清场闸 editor_not_clean、正文空 comment_text_empty、串码缺失 comment_contact_code_missing、未派发 comment_submit_not_actuated 四个诚实终局 -->
  - 偏离说明（2026-07-28）：① 提交后未确认的 reason 由 `comment_submit_unconfirmed` 改回退役实现的 `submitted_unconfirmed` —— 云端 `aidcp-cloud/src/comment-agent/edge-steps.ts:357` **精确匹配**该串才归「已提交、结果未知」并写去重，串不上会归 `not_dispatched` 触发上游重投 ⇒ 重复评论。② **逐字输入原语未接线**：`native/page-engine/src/input.rs:67/76` 的 `type_text_humanized*` 是 CDP 层原语，只能从 Rust 平台语义臂调用，而 `interaction_comment` 落在 `engine.rs:708` 的 `_ => evaluate_router`（整条命令在注入的页面 JS 里跑完）。接线需把整条评论路径重写进 Rust，属拟人化 change 范围，且 `engine.rs` 与同批 `restore-native-xiaohongshu-session-guards` 共写（design D6）。本轮只在页面规则层做合成，段界（正文一段 / 串码一段）已保留，将来换成「正文逐字 + 串码整段插入」是 drop-in。附带结论：现整段写值**不触发** @/# 补全劫持（劫持只由逐字派发触发）。③ 折叠态入口激活（oracle ②-5）未做，不在 2.1 任务面内，真机确认后需单开。
- [x] 2.2 把开帖成功判据改为正面详情证据（详情容器 + 标题/正文/图片至少一项非空），错误页语义命中即诚实失败；未确认打开一律不产出 `note_detail` 输出。**两个判据点都要改**：点击后的那处（`xhs-command-router.js:194`）与「已在详情页」的快速返回处（`:188`，当前地址里有目标 id 就直接回详情、连点击都不发）（参照 src/browse/browse-session.ts:1876-2036 + probe.rs:158 的 PageKind::Error；⚠「必落 404」未在 Native 复核，见 oracle.md ①） <!-- aidcp-edge 8b99183 两个判据点都改；新增 confirmedDetail() / noteUnavailable()；按 oracle ① 第三层加令牌门控（地址无 xsec_token= 则详情 url 诚实置空） -->
  - 偏离说明（2026-07-28）：① 按 oracle ① 的 caveat **只实装可无条件成立的三层**（正面详情证据 / 错误页否决 / 令牌门控），开帖执行方式（页内点击 vs 可信指针输入）**刻意未动**，等真机项 5.1 结论。② 幂等早退触发条件收窄为「命令带 noteId 且地址 id 等于它」，行为差异只在「命令未带 noteId + 地址是某条笔记详情 + 页面无详情容器」这一种组合（原来直接回详情，现在落点击路径）—— 收窄是为避免「已在目标笔记但拿不到证据」时掉进点击路径点开邻座笔记；云端现役 open_note 恒带 noteId（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:3278-3288`），该组合在闭环上不出现。③ 令牌门控不在本行字面里，但在 oracle ① 的「可无条件实装的三层」内且退役实现有逐字对应物（`src/browse/browse-session.ts:1994`），它同时作用于 `note_open` 与 `note_browse_images` 的详情输出。④ 给 2.3a 的耦合提醒：`detail()` 的 `url` 现在无令牌时是 `undefined`，`NoteDetail.url` 是 `#[serde(default)] Option<String>`、Rust 解析无碍，但 2.3a 断言随行详情时**别把 url 当必填**。
- [x] 2.3 看图命令改为返回动作回执：每步重新解析翻页控件、校验图序真前进、按实际前进张数回报；无轮播回 `no_target`；不再以 `refreshOnly` 详情充当终局（参照 src/browse/browse-session.ts:2797-2844；缺 total 探测/viewed 计数/循环内重解析 — 见 oracle.md ⑤） <!-- aidcp-edge 19d4872 每步重解析 nextArrow()、按 swiper 激活片下标（读不到退到首张可见图地址）校验图序真前进、reason='browsed='+实测张数；无轮播且无翻页控件回 no_target/not_started；终局改为 action_receipt_with_observation -->
  - 偏离说明（2026-07-29）：① 真图张数按 `.swiper-slide:not(.swiper-slide-duplicate)` 统计并据此给目标张数封顶（n 张图最多前进 n-1 次），loop 复制片同时也从随行详情的图片数组里排除——否则同一张图会被重复灌进云端参考图；这一条在原任务字面之外，属实装时坐实的必要项。② 三种停手原因分开回报：控件消失 = `exhausted`（良性，如实回已前进张数）、点不动 = `no_target/not_started`、点得动但图序不前进 = `no_advance/ambiguous`。③ 「点得动 ≠ 翻得动」是本条的核心：只有图序标记真变化才计一张，`click()` 返回真不计数。
- [x] 2.3a 安排看图过程中新图片的去处（先定机制再改判据）：一条命令只能回一个输出（`evaluate_router` 返回单个 `(EffectPhase, CommandOutput)`，宿主按 `kind` 走互斥分支），而当前那条 `refreshOnly` 详情是云端参考图刷新（`aidcp-cloud/src/agents/curated-note-evaluator.ts:114-118`）与灵感 / 观测笔记 `referenceImages` 更新（`aidcp-cloud/src/server.ts:4914`）的唯一来源。二选一并在此记录所选：① 回执携带本次观察到的图片；② 宿主在收到回执后补一次详情读取。**验收判据：改完后跑一遍云端参考图刷新的既有用例仍绿，且新图片确实到达云端**；不得只改回执把图片证据静默丢掉（参照 src/browse/browse-session.ts:1284-1311：旧实现是回执与 refreshOnly 快照两条出口并存 — 见 oracle.md ⑤） <!-- aidcp-edge 19d4872 按决策记录落地：新增输出 kind action_receipt_with_observation（Rust model.rs 的 ObservedActionReceipt + engine.rs 的 CommandOutput 新臂 + xhs.rs 的 typed_output 分支，发布命令走 `_` 诚实报无效）；页面规则抽到 ≥1 张图才带 noteDetail；宿主 browse-session.ts 新增该 case 并与裸回执共用同一段 reportActionReceipt，顺序为「先 reportNoteDetail(refreshOnly 强制置真) → 再报回执」 -->
  - 偏离说明（2026-07-29）：验收判据的**边缘侧那一半**已坐实——`xhs-behavior-parity.test.ts` 的 1.11 用例断言翻页新图随本次命令的唯一终局到达，Rust `tests/xhs_observed_receipt.rs` 锁住线上 kind 与两段载荷字段名不漂、无观测时不造空壳字段、发布命令不得用该 kind。**云端那一半未跑**：判据里的「跑一遍云端参考图刷新的既有用例仍绿」需在 `aidcp-cloud` 仓执行，本轮**未碰云端仓、未跑云端测试**；因宿主强制 `refreshOnly:true`、云端读到的仍是既有的 refreshOnly 详情形状，判断为不影响，但**这一条属未验证、不得当已验证结案**。
  - 决策记录（2026-07-28，实读云端后定）：**选 ①「回执携带观测」**，但携带的是**完整详情快照**而非裸图片数组，且不加宽 `ActionReceipt`，改用新的单一输出 kind `action_receipt_with_observation`。
    · 为什么必须是完整快照：云端 refreshOnly 分支（`aidcp-cloud/src/comm/handler.ts:694-698`）emit 的 `note.image_snapshot.arrived` 有**两个**订阅方——`curated-note-evaluator.ts:115-118`（OCR 开启时 `:117` 转调 `evaluate()`，而 `:148` 要 likeCount/collectCount 做共鸣预筛、`:178` 正文空即 return）与 `server.ts:4948` 的 `rememberObservedNote`（`:4909-4945` 把 title/body/likeCount/referenceImages **整体覆盖**写进最近观测笔记）。只塞 images 的残缺详情会把最近观测笔记的标题正文清空 —— 用一个新的静默丢数据换掉旧的。
    · 为什么否决 ②（宿主补一次详情读取）：宿主再读只能再发一条命令，而现有能返回详情的命令是 `note_open`（`xhs-command-router.js:184-196`），其输出 `note_detail` **不带 refreshOnly** ⇒ 云端 `handler.ts:700+` 会当成一次新的详情上报并入队一笔 `view` 风控事实（浏览计数唯一入口），一次看图凭空多记一次浏览；要绕开就得新造一条只读详情命令 + 宿主调度，多一次往返、多一个命令面，且落进 session-guards 的宿主装配单写区。
    · 为什么否决「直接给 `ActionReceipt` 加字段」：该结构有 5 处穷举式字面量构造（`native/page-engine/src/facebook/shared.rs:284/310/828`、`engine.rs:1020/1441`），加字段必须改 `facebook/**` —— design D6 明令不碰；且宿主还得像今天删 `groupObservation` 那样再删一个字段才能不改 `action.completed` 协议载荷。
    · 下游接口形状：Rust `model.rs` 新增 `ObservedActionReceipt { receipt: ActionReceipt, #[serde(default, skip_serializing_if="Option::is_none")] note_detail: Option<NoteDetail>, #[serde(default, skip_serializing_if="Option::is_none")] notification_items: Option<NotificationItems> }`（`deny_unknown_fields` + camelCase，`bounded()` 逐段复用各自 `bounded()`）；`engine.rs` 的 `CommandOutput` 加一臂 `ActionReceiptWithObservation(Box<ObservedActionReceipt>)`（既有 `tag="kind", content="value"` ⇒ 线上 kind 即 `action_receipt_with_observation`）；`xhs.rs::typed_output` 加同名分支（置于 `publish_identity` 判定之外，发布命令 MUST NOT 用该 kind）。页面规则侧：`note_browse_images` 终局恒为该 kind，`receipt.action` MUST 为 `browse_images`（`aidcp-cloud/src/agents/deep-reader.ts:122` 精确匹配），成功时 `receipt.reason` MUST 为 `browsed=<N>`（`deep-reader.ts:39-45` 正则 `browsed=(\d+)`，N 为实测前进张数），无轮播则 `ok=false / reason=no_target / effectPhase=not_started` 且 MUST NOT 带 `noteDetail`；`noteDetail` 仅在「`exactNote()` 成立且本次抽到 ≥1 张图」时携带，形状 = 现 `detail()` 的完整 `NoteDetail`（含 title/content/likeCount/collectCount/images）且 `refreshOnly:true`。宿主 `src/native-page-engine/browse-session.ts` 新增该 kind 的 case，与既有 `action_receipt` 分支**共用同一段回执处理**（抽私有方法，勿复制 `ok: receipt.ok && effectPhase==='confirmed'` 那条口径）；顺序 MUST 为「先 `reportNoteDetail({...noteDetail, refreshOnly:true})`（宿主强制置真）→ 再报回执」，且 `action.completed` 载荷 MUST 只含 receipt 字段（协议不变）。
- [x] 2.4 返回列表的回执 `ok` 改为由观察到的列表面推导，去掉硬编码为真（参照 src/browse/browse-session.ts:2735-2795 的机制；⚠ 回执 ok 必须新写，旧的 :2794 恒真 — 见 oracle.md ④） <!-- aidcp-edge 19d4872 ok 由 listReady()（在列表地址上且真扫到可见卡片）推导；未确认回 ambiguous list_not_confirmed -->
  - 偏离说明（2026-07-29）：① 顺带改了两处原任务字面之外、但不改就等于没修好的东西——(a) 动作名从 `navigation_back` 归一到云端角色关联键 `back`（名字对不上，云端把它当未知失败动作，诚实回执照样落空）；(b) 执行方式从 `history.back()` 改为「先关浮层 → 等重绘 → 仍不在列表才 `location.assign('/explore')`」（浏览器后退会回踩过期详情路由并触发平台访问限制弹窗）。② feed 判据收严为 `/explore` 本身或搜索页，`/explore/<笔记 id>` **不算**列表——松判据会把详情页认成 feed，随后扫不到卡、边云互等。
- [x] 2.4a 滚动评论区的回执改为实测：`ok` 由滚动前后位置差推导（未移动即诚实非成功），回报的评论条数改为滚动后页面上实际可见的条数，去掉「直接回报请求值」；对应云端 `comment-reviewer` 的「已读评论数」不再恒 1（云端侧不改，只验证输入变诚实后投影随之变真）（参照 oracle.md ⑤ 的 scroll_comments 同族测试：按实测位移与实测条数回报） <!-- aidcp-edge 19d4872 逐步滚动并按位置差判定，全程未位移回 ambiguous no_scroll；条数取滚动后页面上真数出的评论行、reason='scrolled='+条数 -->
  - 偏离说明（2026-07-29）：① 条数用「逐个选择器试、取第一个真数出条目的那个」而非几个选择器求并集——求并集会把「评论行」与「评论行里的正文块」各计一次，条数凭空翻倍。② 云端侧未改也未跑：本条只坐实边缘输入变诚实（`xhs-behavior-parity.test.ts` 1.10 两例），「云端投影随之变真」需真机或云端仓验证，未做。
- [x] 2.5 点赞 / 收藏 / 关注改为互动条内结构化定位（排除聚合计数与反向控件），去掉「按钮→行内→块」三级文本回落（参照 flows/anchors.ts:46-64 + browse-session.ts:2298-2360/2685-2732:349 七候选；缺互动栏作用域与具名控件 — 见 oracle.md ⑥a/⑥b） <!-- aidcp-edge 19d4872 赞/收藏作用域限定在互动栏（.interactions.engage-bar 具名候选，带有界等待应对晚渲染）内的 .like-wrapper / .collect-wrapper；关注改具名 FOLLOW_SELECTORS 七候选；findByWords 文本回落在这三条路径上全部移除 -->
  - 偏离说明（2026-07-29）：详情读数里的 `authorFollowed` 一并改成与关注动作**逐字镜像同一套候选与判定**（原为 `active(first(['[class*="follow"]','button'],root))`，会把任意按钮当关注态）；读不到按钮回 false，让云端回退主页评估流程。这一条不在任务字面里，但两处不镜像就会出现「读数说已关注、动作却去点关注」的自相矛盾。
- [x] 2.6 点赞 / 收藏 / 关注的确认改为有界轮询状态翻转，去掉固定睡眠后单次采样，去掉「控件文本含『已』」这条兜底；未翻转回 ambiguous `state_unchanged`（参照 browse-session.ts:2339-2341 有界轮询；⚠ 关注侧旧实现无后验、不可照抄 — 见 oracle.md ⑥b） <!-- aidcp-edge 19d4872 新增 waitFor 有界轮询（1500ms / 60ms 步进），赞与收藏读图标状态位（svg use 的 #like→#liked / #collect→#collected）、关注读 aria-pressed 或已关注/互相关注文案；「文本含『已』」兜底删除；未翻转一律 ambiguous state_unchanged -->
  - 偏离说明（2026-07-29）：① 关注侧的后置校验按 oracle 的告警**新写**（旧实现点完只睡一觉就无条件报成功，等于没有后验），且每轮重新解析控件而非复查旧引用。② 新增两个良性 no-op 终局 `already_liked` / `already_collected` / `already_followed`（目标状态本就达成），云端据 reason 区分真实互动与 no-op；这是把原来的 `already_active` 拆细，不是新放宽。③ 控件点不动回 `control_not_actuated` + `not_started`，与「找不到控件」分开。
- [x] 2.7 通知抽取回到真机校准契约：行按已标定容器结构选取（去掉裸列表项与命中头像行的 class 猜测）、正文只取正文容器且缺失发空串、itemKey 逐条稳定且不得使用发送者主页链、无逐条身份时留空（参照 notification-monitor.ts:128-138/148/163-164/169/209；另注意 oracle.md 覆盖漏洞 4/6：per-tab 计数与 code-point 截断本清单未覆盖） <!-- aidcp-edge 19d4872 行改 .tabs-content-container > .container 两级容器（裸 li 与模糊 class 猜测全删）；正文只取 .interaction-content，缺失即空串；itemKey 取 note-id/data-note-id/data-id/笔记链里的 id，取不到留空，主页链彻底不进 itemKey -->
  - 偏离说明（2026-07-29）：另加两条不在字面里、但不加就仍在造假的约束——① 「赞和收藏」是同一栏两类，按行内动作文案区分 collect / like，不再一栏之内全标成赞；② 互动行拿不到昵称也拿不到主页 ID 时**整行跳过**，不再用 `'unknown'` 占位（占位昵称会被云端当真实身份写进联系人名册、还参与去重键）。
- [x] 2.8 先确认云端与 CLI 已无 v1 有序步骤（`plan_execute`）的活跃产出方，确认后删除小红书路由里的该分支；若确认仍有活跃产出方，改为按实测位移回报滚动步骤。**判定依据必须实读后写在此处**，且已知两条反证据必须逐条回应：① 规则式规划器产的 `note.like_button` / `note.follow_button` 与路由映射表**是对得上的**（`aidcp-cloud/src/planner/simple-planner.ts:24-48`），只有收藏那条名字不同；② 规划器的 LLM 兜底分支（`:68-78`）允许模型自由产出 `actionId` 且 `op` 白名单含 `scroll`（`:16`），所以「`page.scroll` 步骤不可能被产出」在代码上证明不了。**判不清即默认走「补测量」，不删** <!-- aidcp-edge 19d4872 按决策记录走「补测量、不删」：plan_execute 的 page.scroll 分支改按实测位移回报（scrolled=Npx / no_scroll），outcome 仍限协议四取值、无 Rust 改动；新增 test/native-page-engine/xhs-plan-compat.test.ts 三例（滚得动 / 滚不动 / 找不到目标仍回 no_target） -->
  - 偏离说明（2026-07-29）：本条只改滚动那一支。click / input 两支按任务范围**未动**，其 `outcome:'escalated', attempts:1` 的形态原样保留 —— 这正是并行 change `restore-native-actuation-humanization-and-locating` 的 1.6 / 5.3 盯的那个点（「升级结论 + 尝试次数为 1」在本文件里仍然存在），本 change 作为该文件的单写区属主**未在本轮修正升级语义**，两侧对账见该 change 的 5.3。
  - 决策记录（2026-07-28，实读云端 + CLI + 边缘路由后定）：**走「补测量」，不删**。判定依据（活跃产出方存在且现成可跑）：① 云端 CLI `aidcp-cloud/src/cli/trigger-like.ts:44` 发 `plan.request{context.dispatch:'edge'}`，且 `aidcp-cloud/package.json:23` 有 `npm run trigger:like` 入口；② 云端 `src/comm/handler.ts:487` → `onPlan`（`:1369-1385`）用 `SimplePlanner` 规划后 `pusher.pushToEdges(plan.response)`，未指定 edgeId 即**广播给全部在线边缘**，而该 planner 在 `src/server.ts:2465` 实例化并注入 ⇒ 生产进程里就带着；③ 边缘 `src/client/edge-client.ts:756-765` 放行 `plan.response`，`src/native-page-engine/command-mapper.ts:5` 映射 `plan.response → plan_execute` ⇒ Native 路径接得住。故「无活跃产出方」不成立。
    · 反证据①回应：`note.like_button` / `note.follow_button`（`simple-planner.ts:26-32`）与 `xhs-command-router.js:241` 的映射表确实对得上；只有 `note.favorite_button`（`:34`）不在表里 —— 它落 `no_target`，那是**诚实失败**，不构成「整条路径不可达」的证明。
    · 反证据②回应：LLM 兜底（`simple-planner.ts:69-77`）把模型自由产出的 `actionId` 直接放行，`VALID_OPS`（`:16`）含 `'scroll'` ⇒ `page.scroll` 步骤在代码上可被产出，删除即删活路径。
    · 下游接口形状（只改滚动步骤那一支，不动 Rust）：`xhs-command-router.js` 的 `plan_execute` 里 `step.actionId==='page.scroll'` 分支 MUST 改为实测位移 —— 滚前取 `before = document.scrollingElement.scrollTop || window.scrollY`，`window.scrollBy(0, Math.max(200, Number(step.value)||500))`，等落定后取 `after`，`moved = after !== before`；结果条为 `{actionId, ok: moved, outcome: moved ? 'success' : 'escalated', attempts: 1, reason: moved ? ('scrolled=' + Math.abs(after-before) + 'px') : 'no_scroll'}`。`outcome` 取值 MUST 限于 `src/comm/protocol.ts:818` 的 `'success' | 'escalated' | 'no_target' | 'guard_blocked'`，MUST NOT 新造取值；`PlanActionResult`（`native/page-engine/src/model.rs:474-480`）字段不变、无 Rust 改动；click / input 两支不在本任务范围，且 MUST NOT 顺手把「找不到目标」从 `no_target` 改掉。

- [x] 2.9 在小红书页面规则层恢复未读角标的结构化读数：宽 / 窄双布局都遍历、取可见那个入口；未读 = 入口角标容器里图标之外的可见真实角标（空槽 = 无未读），红点无数字也算未读、计数仅附带；读不到入口或读取出错 MUST 回「读不到」，MUST NOT 回「无未读」。落点二选一并在此记录所选：① 扩 `native/page-engine/src/xhs-page-probe.js` 的返回结构（**须同步 `native/page-engine/src/probe.rs` 的 `RawPageSignals` 与 `StructuralSignals`，后者带 `deny_unknown_fields`，漏改即整条探针解析失败**）；② 在 `xhs-command-router.js` 加一条只读命令。**周期调用与未读信号的发送方不在本 change**（见 design.md「覆盖漏洞的范围外交接」与任务 4.5 / 4.6）（参照 `317cd47^:src/browse/notification-monitor.ts:17-91`；判据 2026-06-23 校准、须按 5.8 复核 — 见 oracle.md 未读监测体条） <!-- aidcp-edge 19d4872 按决策记录选 ①：xhs-page-probe.js 顶层新增 notificationUnread（遍历双布局入口取可见那个、图标之外的可见元素才算角标、整段 try/catch 回 unreadable）；probe.rs 新增 NotificationUnreadState/Signal + RawNotificationUnread + build_result 严格映射（非 unread/clear 一律 unreadable）；client.ts 只加类型与 parseNotificationUnread（缺失/非法一律 unreadable），未加调用点 -->
  - 偏离说明（2026-07-29）：① 与决策记录一致，`StructuralSignals` 未动，读数落 `ProbeResult` 顶层。② `ProbeResult` 的该字段序列化时对 `unreadable` 做 `skip_serializing_if` —— 「不带该字段」与「带一个 unreadable」在宿主侧等价（`parseNotificationUnread` 两种都回 unreadable），既有探针契约无需变形。③ Rust 侧一并加了单测 `keeps_unread_read_failures_distinguishable_from_no_unread`，钉住「取值漂移 / 字段缺失 ⇒ unreadable，绝不回落 clear」。④ 周期调用仍归承接方，本轮**未接线**，故未读信号在运行路径上仍无发送方（见 4.6）。
  - 决策记录（2026-07-28，实读 Rust 探针链路后定）：**选 ①（扩 `xhs-page-probe.js`）**，但读数落在 `ProbeResult` **顶层新字段**，**不塞进 `StructuralSignals`**。
    · 为什么 ①：`page_probe` 命令对小红书**已经接线**（`native/page-engine/src/engine.rs:378-380` → `execute_page_probe`；另有 `cdp.rs:126` 的页型轮询走同一段 JS），宿主也已有现成调用面（`src/native-page-engine/browse-session.ts:477-484` 的 `runtime.execute`、`src/native-page-engine/client.ts:597-606` 的 `probePage`）⇒ 承接方（session-guards 1.2）只需把现有周期探针按平台放开，不必新造命令面。② 新增只读命令则要动 `native/page-engine/src/command.rs` 的 `NativeCommand` 穷举 + `command-mapper.ts` + 云端下发面，多一条命令面，且「未读怎么读」根本不该由云端下发触发。
    · 为什么不塞 `StructuralSignals`：该结构是 `classify_page`（`probe.rs:146-193`）的输入、字段语义全是 u32 计数，未读是**三态读数**（有 / 无 / 读不到）；塞进去要么退化成计数（丢掉「读不到」这一态，正是本任务禁止的），要么污染页型分类输入。故 `StructuralSignals` 本次不动 —— 若后续有人改主意要塞进 `signals`，MUST 同时改 `StructuralSignals`（`deny_unknown_fields`）**与** `client.ts:1090-1101` 的 `signalNames` 白名单，漏一处即解析失败或字段被静默吞掉。
    · 下游接口形状：页面规则 `xhs-page-probe.js` 的返回对象与既有字段同级新增 `notificationUnread: { state: 'unread' | 'clear' | 'unreadable', count: 0..999 }` —— 遍历**全部** `a[href*="/notification"], a[href*="/notice"]` 入口（宽 / 窄双布局 DOM 同时存在），取第一个 `visible()` 为真的；命中后在其角标容器内找「图标（svg / i / img / `[class*="icon"]`）之外的可见元素」：有则 `state='unread'`、`count` 取该元素文本里的 1–3 位纯数字（无数字的红点 ⇒ `count=0` 但仍 `unread`），只有常驻图标 / 空注释槽 ⇒ `state='clear'`；无可见入口或读取抛错 ⇒ `state='unreadable'`（整段包 try/catch，**MUST NOT** 回 `'clear'`）。Rust `probe.rs` 新增 `pub enum NotificationUnreadState { Unread, Clear, Unreadable }`（serde `snake_case`）与 `pub struct NotificationUnreadSignal { state, count: u32 }`（`deny_unknown_fields` + camelCase，`Default` = `{ Unreadable, 0 }`）；`RawPageSignals` 加 `#[serde(default)] notification_unread: Option<RawNotificationUnread>`（`RawNotificationUnread { state: String, #[serde(default)] count: u32 }`，Raw 侧保持无 `deny_unknown_fields` 的宽松解析）；`ProbeResult` 加 `#[serde(default)] pub notification_unread: NotificationUnreadSignal`（该结构带 `deny_unknown_fields`，故字段与 default MUST 同时加）；`build_result`（`probe.rs:107-144`）里 state 字符串**只有**恰为 `"unread"` / `"clear"` 才映射、其余一律 `Unreadable`，`count` 取 `.min(999)` 且非 `Unread` 时归 0。宿主 `src/native-page-engine/client.ts` **只加类型与解析、不加调用点**（周期调用归承接方）：`NativePageProbeResult` 加 `notificationUnread: { state: 'unread'|'clear'|'unreadable'; count: number }`，`parseProbeResult`（`:1073-1113`）对缺失 / 非法值一律回 `{ state: 'unreadable', count: 0 }`，MUST NOT 回落 `'clear'`。
- [x] 2.10 通知「评论和@」栏恢复滚到底清零循环：每轮先数行数、连续 2 轮行数不增即判到底、硬上限取 `max(云端滚动上限, 12)`、每轮滚约 0.8 个视口高并留加载等待；使云端下发的滚动预算真参与上限，不再是「声明并校验却无人读取」的悬空参数（`src/native-page-engine/command-mapper.ts:61-63` 与 `native/page-engine/src/command.rs:651-662` 已在传与校验）（参照 `317cd47^:src/browse/browse-session.ts:3116-3133` — 见 oracle.md 清零循环条） <!-- aidcp-edge 19d4872 新增 sweepNotificationList()：连续 2 轮行数不增即判到底、每轮滚 0.8 视口高、每轮有界等新行（一出新行立刻进下一轮，不做固定睡眠空等）、上限真读 p.scrollMax -->
  - 偏离说明（2026-07-29）：上限实装为 `min(100, max(12, p.scrollMax))`，比任务字面的 `max(scrollMax, 12)` 多一道 **100 轮的绝对天花板**——防云端下发一个异常大的预算把单条命令拖过看门狗。云端现役预算远小于 100，行为等价；若将来真需要超过 100 轮，此处要一并放开。
- [x] 2.11 「赞和收藏」「新增关注」两类改为以动作回执终局：动作名用云端角色等待的规范名；分类栏未命中回 `no_target`；发送者抽取失败只记日志、绝不阻断清零回执。**与 2.3a 同一个机械约束（一条命令只能回一个输出）**：现 `ActionReceipt`（`native/page-engine/src/model.rs:301-313`）无通知项字段，二选一并在此记录所选——① 给回执加通知项字段并同步 `native/page-engine/src/xhs.rs` 的输出解析；② 宿主在 `notification_items` 输出上补发回执（`src/native-page-engine/browse-session.ts:340-342`，属宿主装配面，按 6.5 与 session-guards 对账）。**验收判据：改完后通知联系人名册仍收到 items（`aidcp-cloud/src/server.ts:6440`），且云端两个分类浏览角色能凭回执结案**；不得只加回执把 items 静默丢掉（参照 `317cd47^:src/browse/browse-session.ts:3161-3210` — 见 oracle.md「看一眼」条） <!-- aidcp-edge 19d4872 按决策记录选 ①：两类终局改 action_receipt_with_observation，规范名 browse_notification_likes / _follows，未命中分类栏回 ok=false/no_target/not_started 且不带 notificationItems，抽取失败（try/catch）仍回 ok=true 的清零回执；「评论和@」保持 notification_items 终局、只在失败时给诚实失败终局；宿主顺序为「先 send notification.items → 再报回执」 -->
  - 偏离说明（2026-07-29）：验收判据的**云端那一半未跑**（未碰 `aidcp-cloud` 仓）。边缘侧已坐实：`xhs-notification-parity.test.ts` 断言规范名回执、未命中回 no_target 且全程不触发其他元素、抽取失败仍出清零回执；宿主侧 items 与回执的先后顺序在 `browse-session.ts` 的同一个 case 里写死。「云端两个分类浏览角色能凭回执结案」仍属未验证。
  - 决策记录（2026-07-28，与 2.3a 同一决定、同一载体）：**选 ①（回执携带通知项）**，复用 2.3a 定下的 `action_receipt_with_observation` 输出 kind，**不加宽 `ActionReceipt`**（理由同 2.3a：`facebook/shared.rs` 三处字面量属 design D6 不碰区）。
    · 为什么否决 ②（宿主在 `notification_items` 输出上补发回执）：会把终局判定劈成两层 —— 失败路径的回执由页面规则的 `ambiguous()` 造（而且现在造出来的动作名是 `notification_browse_likes`，**不是**云端等的规范名），成功路径的回执由宿主造，宿主还得自己维护一张「命令 kind → 规范动作名」映射表。这正是 CLAUDE.md §2 第 5 处同步点记载的「两端各一张映射表、typecheck 抓不到」的漂移形态。① 让规范名只在页面规则里出现一次。
    · 下游接口形状（赞和收藏 / 新增关注两类）：终局输出 kind = `action_receipt_with_observation`；`receipt.action` MUST 为 `browse_notification_likes` / `browse_notification_follows`（`aidcp-cloud/src/agents/notification-like-browser.ts:36`、`notification-follow-browser.ts:35` 精确匹配、且都要求 `ok===true` 才 emit `category_handled`）；看完回 `ok=true, reason='viewed'`；分类栏未命中回 `ok=false, reason='no_target', effectPhase='not_started'` 且 MUST NOT 带 `notificationItems`；发送者抽取失败仍回 `ok=true` 的清零回执、`notificationItems` 字段缺省（抽取 MUST NOT 阻断清零）。`notificationItems` 形状 = 现有 `NotificationItems`（`native/page-engine/src/model.rs:239-243`）**去掉自造 epoch**（见 2.15）。宿主同一个 case 里顺序 MUST 为「先 `client.send('notification.items', value.notificationItems)` → 再报回执」，以保云端通知联系人名册（`aidcp-cloud/src/server.ts:6440`）在结案前先收到 items。
    · **「评论和@」这一类保持现状、MUST NOT 造回执**：其终局仍是 `notification_items` 输出。依据：云端该类的结案在 `aidcp-cloud/src/agents/notification-deduper.ts:76` 与 `notification-notifier.ts:61`，凭 items 到达即 emit `category_handled{comments}`，**没有任何角色等它的回执**；而发一个云端不认识的动作名会被调度器当未知失败动作处理（CLAUDE.md §2 第 5 处同步点的已知事故形态）。旧实现同样只对 likes / follows 发回执（`317cd47^:src/browse/browse-session.ts:3131` 只发 items，vs `:3168/3204/3210` 三处回执）。
- [x] 2.12 通知首页三栏未读计数改为在真实叶子分类栏作用域内读纯数字叶子角标（1–3 位），排除同样带 tab 字样的包裹容器（防跨类泄漏），读不到即 0；去掉整页正文正则，禁止「解析不出就当 1」，也不得把「1.2万」这类单位文本折算成条数（下游是云端清零判据 `aidcp-cloud/src/agents/notification-triage.ts:55-77`）（参照 `317cd47^:src/browse/notification-monitor.ts:93-123` — 见 oracle.md per-tab 计数条） <!-- aidcp-edge 19d4872 整页正文正则删除；改 leafTabs()（class 含 tab-item 且内部不再含叶子）+ tabBadgeCount()（作用域内无子元素的可见叶子、文本恰为 1–3 位纯数字才计），带单位文本不折算、读不到即 0 -->
  - 偏离说明（2026-07-29）：新增的验收判据两条都已实装——① 中英文两套界面文案：`TAB_MATCHERS` 三类各带一条英文分支（`comments?/mentions?`、`likes?/collect…`、`follow(s|ers|ing)?/new followers?`），中文分支不再依赖任何捕获组，运算符优先级击穿的根因随整段重写消失；② 「三栏全 0」与「读不到」可区分**落在命令层而非计数层**：`notification_open` 先有界等叶子分类栏出现，一个都没有就回 `ambiguous / notification_tabs_not_found`，绝不回一份全 0 的读数；`notificationHome()` 本身仍只回计数（它被调用时已保证分类栏存在）。
  - **实测订正（2026-07-28，1.16 的两条用例意外为绿时查出，主 session 已独立复核）**：本行原写的失效方向「计数永不归零 → 每趟巡视跑到尝试上限」**记反了**。真实机制是运算符优先级击穿：`xhs-command-router.js:164` 的 `named('赞|like')` 拼出的正则是 `赞|like[^0-9]{0,8}([0-9万w千k.]+)`，两个分支为 `赞` 与 `like[^0-9]{0,8}(...)`，**中文分支不带捕获组**。实测 `"赞 312".match(re)` → `["赞", null]`，`"like 312"` → 捕获到 `312`。故中文界面下三栏计数**恒 0**，与页面上有没有角标无关。下游后果因此相反且更重：`notification-triage.ts:65` 是 `if (counts[cat] <= 0) continue; // 已清零，跳过`，三栏恒 0 ⇒ **每一类都被当成已清零跳过，整条通知巡视静默什么都不做**，真实的评论与 @ 永远不被处理。这是「静默假成功」的一种形态，不是空转。
  - 修复方向不变（叶子分类栏作用域 + 1–3 位纯数字叶子角标 + 读不到即 0 + 不折算单位），但**验收判据要加一条**：中文与英文两种界面文案下都必须读出真实计数；且「三栏全 0」必须能与「读不到」区分，不得让读不到静默变成已清零。
- [x] 2.13 分类栏点击改为在叶子分类栏集合内按严格文本判据挑选（评论类整串等于「评论和@」或以「评论」开头且含 @；赞 / 关注类限制文本长度以容纳角标数字），去掉「按钮→行内→块」三级全页文本回落；是否命中由点击结果推导，不用类名激活态猜测（参照 `317cd47^:src/browse/browse-session.ts:3112-3114/3166-3167` — 见 oracle.md 分类栏点击条） <!-- aidcp-edge 19d4872 findByWords 全页回落删除，改 notificationTab(category) 在 leafTabs() 内按 TAB_MATCHERS 严格文本判据挑；未命中回 no_target，点不动回 tab_not_actuated，selected(tab) 类名激活态判据删除 -->
- [x] 2.14 通知项各字段改 code-point 安全截断并在超长时补省略号，长度上限回到字段级（正文 200 / 昵称 40 / 笔记标题 80 量级），不再统一走整行 blob 量级的 UTF-16 切片（参照 `317cd47^:src/browse/notification-monitor.ts:139/146` — 见 oracle.md 截断条） <!-- aidcp-edge 19d4872 新增 clip()（Array.from 按 code point 切）与 cut()（超长补省略号）；norm() 一并改走 clip；昵称 40 / 正文 200 / 笔记标题 80 三个字段级上限落位 -->
- [x] 2.15 通知列表与通知首页上报去掉页面规则自造的墙钟批次序号；批次序号只应有一个来源——未读「无→有」翻转时取的单调序号，该来源随未读监测体归承接方（见 4.5）。**实读记录**：当前云端下游取的是会话内巡视序号（`aidcp-cloud/src/agents/notification-triage.ts:57`、`notification-classifier.ts:41`），故去掉自造值不需要云端配套改动，但该结论须在实装时复读一次再确认（参照 oracle.md epoch 条：迁移新造字段，不可照抄旧代码「改回去」） <!-- aidcp-edge 19d4872 notificationItems() 与 notificationHome() 两处 epoch:Date.now() 删除，协议侧该字段本就可选、未动协议 -->
  - 偏离说明（2026-07-29）：任务要求的「实装时复读一次云端下游再确认」**本轮未做**（未碰 `aidcp-cloud` 仓，07-28 的实读结论未复核）。判断为不阻断：该字段在协议里是可选，去掉后云端读到 `undefined`，与它原本就取会话内巡视序号的路径不冲突；但这一条属未复核，收口前应补一次。

## 3. aidcp-edge — 发布原子回到既有契约

- [ ] 3.1 依据 `openspec/specs/publish-pipeline/spec.md`「边缘指令运行时逐条执行并每条后置校验如实回报」，在 Native 小红书正文填写上恢复逐字增量输入、每个换行独立派发真实 Enter、有界确认段落数/已写前缀/光标归尾、语义相似度 ≥ 0.90 放行、失败清场
  - 部分完成（2026-07-29，`aidcp-edge 19d4872`；**五项里四项已落，「逐字」那一项未落，故不勾选**）：已落——① 增量写入（按 24 个 code point 分块追加、块间留 20ms，取代一次性整段赋值）；② 每个换行独立派发一次回车键事件，派发后立刻复读、换行没落进内容就补写一个（宁可段落结构不理想也不丢正文）；③ 有界确认（2000ms / 80ms 步进）三条判据齐备——已写内容以目标开头、受控框语义下段落数达标、相似度（字符二元组 Dice）≥ 0.90；④ 确认不过即**清场**并回 `ambiguous / publish_field_readback_mismatch`，确认通过后光标归尾。新增 `test/native-page-engine/xhs-publish-atoms.test.ts` 三例覆盖（多段各一次回车 + 增量事件数、编辑器吞写入时清场失败、无害标点改写不误杀）。
  - 未落的那一项：**真正的逐字输入**。原因与 2.1 偏离说明②同源——逐字输入原语（`native/page-engine/src/input.rs`）是 CDP 层原语，只能从 Rust 平台语义臂调用，而 `publish_fill_field` 落在 `engine.rs` 的通配分支、整条命令在注入的页面 JS 里跑完。当前是「分块增量 + 合成 KeyboardEvent 回车」，不是硬件级按键。接线归并行 change `restore-native-actuation-humanization-and-locating` 的 8.1 / 8.3（其 8.3 对回车与归尾确认的要求比本条更严：连续两次命中才算稳定、超时清空正文）。**本条在那条接线落地前不得勾选**。
- [x] 3.2 依据 `openspec/specs/publish-submit-integrity/spec.md`「成功判定锚定真实成功信号」，把提交成功判据从全页文本/地址正则改为绑定本次草稿的真实成功信号；已派发未确认回 ambiguous 并记录已派发（参照 flows/publish-command-handlers.ts:1332-1432；穿闭合 shadow 定位 + 只认成功文案 + no_target 时 submitDispatched 保持假 — 见 oracle.md ③） <!-- aidcp-edge 19d4872 地址判据删除；只认成功文案且先记点击前的同款文案基线（陈旧文案不算本次证据）；15s 有界轮询；找不到/禁用/点不动三态 submitDispatched 保持假 + not_started，已派发未确认回 ambiguous 且 submitDispatched=true -->
  - 偏离说明（2026-07-29）：① **穿闭合 shadow 定位未做**（oracle ③ 里的那一条）：目标改为「文案恰为『发布』或『定时发布』、排除暂存/离开/草稿、只取叶子、同时命中多个取最靠右」，未做 shadow 穿透。若真机上发布按钮落在闭合 shadow 里会退化为 `publish_submit_not_found`（诚实未命中、`submitDispatched` 保持假，不会假成功），需真机复核后再决定是否补。② 成功文案词库为 `发布成功|发布中|笔记已发布|笔记发布成功|成功发布|稍后可在`，中文单语；未确认的错误码用 `post_validate_failed`。
- [ ] 3.3 更新 `docs/real-machine-acceptance-backlog.md` 中「小红书逐字输入辅助未受影响」这条已失效的记述所在条目（70.6），改为指向本 change 的真机验收项；不改动该文件其他簇 <!-- 2026-07-31 指针订正：本 change 的真机验收项已按用户裁定移出本 tasks.md，现落在同一文件的**簇 125**（小红书 Native 切换）。本条要改的 70.6 指向应写簇 125，不再写本清单的 5.x 编号 -->
  - 进度说明（2026-07-29）：本轮**未做**。该文件在控制仓、不在本轮 edge 提交面内；且 3.1 的「逐字」那一半尚未落地，条目 70.6 的记述要指向的真机项此刻还不完整，宜与 3.1 一并收口。

## 4. aidcp-edge — 验证（代码级）

- [ ] 4.1 运行 `npm run test:acceptance`，记录安全红线用例（协议不漂移 / 未授权不发布 / 风控不自残）全过
  - 阶段性记录（2026-07-28，2.1 / 2.2 落地后跑；本条为 change 收口门，余下 slice 落地后须重跑，故不勾选）：`npm run test:acceptance` **30 / 30 全过、0 失败**（1 条 gated 跳过 = AC-E2E 真机联调，需 `AIDCP_E2E=1`）。安全红线三族全过：AC-PROTO-01～20b（协议版本 2、消息类型 94、两端不漂移）、AC-PUB-01～07（未授权绝不静默发布）、风控不自残族在 edge 侧无用例（属 cloud）。
  - 阶段性记录（2026-07-29，第二波 `19d4872` + 并行 change 的 `3a1b2b3` 落地后重跑；3.1 / 3.3 / 4.5 / 4.6 未收口，故仍不勾选）：`npm run test:acceptance` **30 / 30 全过、0 失败**（1 条 gated 跳过 = 需真机的 E2E）。本轮新增的输出 kind `action_receipt_with_observation` 未触发任何协议红线失败——它是引擎内部的命令输出形状，不进 `src/comm/protocol.ts`，`action.completed` 载荷不变。
- [ ] 4.2 运行全量 `npm test` 与 `npm run typecheck`，记录通过数与因夹具修正（1.12）新暴露的既有失败
  - 阶段性记录（2026-07-28，同上不勾选）：`npm test` **2583 例 / 2556 绿 / 26 红 / 1 跳过**；`npm run typecheck` **通过**。26 条红**全部**是失败优先的表征用例、按设计留红等后续 slice：`xhs-behavior-parity.test.ts` 15 条（1.4→2.3、1.5→2.3、1.6→2.4、1.7→2.5、1.8→2.6、1.9→2.7、1.10→2.4a、1.11→2.3a）+ `xhs-notification-parity.test.ts` 11 条（1.13–1.19，并行 session 的未追踪文件）。**本轮零新增失败**：上一阶段基线 30 红 → 现 26 红，净转绿 4 条正是 1.1 + 1.2（两条）+ 1.3。**夹具修正（1.12）未暴露任何既有失败**：`router-contract.test.ts` 单跑 7 / 7 全过。
  - 阶段性记录（2026-07-29，同上不勾选）：`npm test` **2630 例 / 2629 绿 / 0 红 / 1 跳过**；`npm run typecheck` **通过**。**表征用例全部转绿**：上一阶段的 26 红（`xhs-behavior-parity` 15 + `xhs-notification-parity` 11）已由 2.3–2.15 的实装清零，本轮零遗留红。例数从 2583 涨到 2630，增量来自本 change 新增的 `xhs-plan-compat.test.ts`（3 例）、`xhs-publish-atoms.test.ts`（5 例）与并行 change 的用例。
- [ ] 4.3 运行 Rust 侧 `cargo test` 与 `cargo fmt --check`，记录通过数
  - 阶段性记录（2026-07-28，同上不勾选）：`cargo test` **138 通过 / 0 失败**（单元 100 + 集成 34 + 2 + 1 + 1，doc-test 0）；`cargo fmt --check` **干净、退出码 0**。本轮 **Rust 零改动**，仅 `build.rs` 重新嵌入改后的页面规则 JS。⚠ 上一阶段首跑时 `facebook::publish::tests::submit_does_not_confirm_when_the_submitted_probe_crosses_the_deadline` 红过一次、单跑与复跑全绿，判为并发负载下的 deadline 计时 flaky，与本 change 无关；本轮复跑未复现。
  - 阶段性记录（2026-07-29，同上不勾选）：Rust 门禁 `npm run gate:native` **通过**（toolchain `1.97.1-aarch64-apple-darwin`，steps = fmt, clippy, test）——本条要求的 `cargo test` 与 `cargo fmt --check` 都被该门禁涵盖并通过，另多跑一道 clippy。**本轮 Rust 有改动**（与上一阶段不同）：`model.rs` 新增 `ObservedActionReceipt`、`engine.rs` 新增 `CommandOutput` 一臂、`xhs.rs` 新增 typed_output 分支、`probe.rs` 新增未读三态与严格映射；新增集成测试 `tests/xhs_observed_receipt.rs`（3 例）与 `probe.rs` 单测 1 例。逐项通过数未单独记录（门禁只报总体通过），收口时若需精确计数须单跑 `cargo test`。
- [ ] 4.4 明确记录本次**未做**的门：未打安装包、未部署、未替换运行中的桌面客户端、未做任何真机写动作
  - 阶段性记录（2026-07-28，change 未收口故不勾选）：本轮**未打安装包、未部署（dev / ol 都没碰）、未替换运行中的桌面客户端、未做任何真机写动作**。另未碰：Rust 源码（无新输出 kind）、宿主 `src/native-page-engine/browse-session.ts`（属 session-guards 单写区）、云端仓、协议四处同步文件、`openspec/specs/`。分支 `native-migration-repair` 已推 origin（`552eda1` / `8b99183`），**未合入 master**。
  - 阶段性记录（2026-07-29，change 未收口故不勾选）：第二波同样**未打安装包、未部署（dev / ol 都没碰）、未替换运行中的桌面客户端、未做任何真机写动作**。与上一阶段的差别：本轮**碰了 Rust 源码**（新输出 kind + 未读三态，见 4.3）与**宿主 `src/native-page-engine/browse-session.ts` / `client.ts`**——前者只加了一个 case 并把既有回执处理抽成私有方法（口径一字未改），后者只加类型与解析、**未加任何调用点**；两处都在 `restore-native-xiaohongshu-session-guards` 的单写区边缘，集成前须按 6.5 对账。仍未碰：云端仓、协议四处同步文件、`openspec/specs/`、`docs/real-machine-acceptance-backlog.md`。分支 `native-migration-repair` 本波提交为 `a45fc81`（1.13–1.19 用例）与 `19d4872`（2.3–2.15 / 3.2 实装）。

- [ ] 4.5 登记「未读监测体的宿主周期装配与未读信号发送方（含单调翻转批次序号的持有位置）」为本 change 范围外项，已在 design.md「覆盖漏洞的范围外交接」具名交接给 `restore-native-xiaohongshu-session-guards`（其 1.2 周期探针按平台分类适配、6.1 恒假装配块逐条对账、6.4 退役监测体去留结论）。登记时须写明：`src/browse/notification-monitor.ts` 在 `src/` 里只被恒假块引用，按 6.4 的三分类会落进「仅恒假块引用」，**若按孤儿删除则本 change 的通知类修复永久不通电**——该项要的是恢复而不是清理
- [ ] 4.6 通电对账（承接方不落地即不算修好）：确认小红书未读信号在运行路径上确有发送方——当前边缘全仓仅协议定义（`src/comm/protocol.ts:110/1965`）与验收测试出现 `notification.detected`，而云端整条巡视链的唯一触发源就是它（`aidcp-cloud/src/agents/notification-gatekeeper.ts:48`、`src/orchestrator/role-dispatcher.ts:2062`）。未落地则在此记录为阻断依赖，并明确写下「通知抽取 / 清零 / 计数类修复已实装但生产未通电」，**不得按已生效结案**
  - 进度说明（2026-07-29）：本条**仍未达成，且现在有了确切的阻断形状**。2.9 落地后，未读读数在页面规则与 Rust 探针与宿主解析三层都已具备（`19d4872`），但宿主 `client.ts` **只加了类型与解析、没有任何调用点**，周期探针的平台化放开归承接方 `restore-native-xiaohongshu-session-guards`（其 1.2）。因此：**「通知抽取 / 清零 / 计数 / 未读读数」四类修复均已实装，但生产未通电**——边缘全仓仍无 `notification.detected` 的发送方，云端整条巡视链的唯一触发源仍悬空。本条按阻断依赖登记，**不得按已生效结案**。

## 5. 真机验收项 —— **已移出本清单（2026-07-31 用户裁定）**

> 原 5.1–5.10 共 10 条已统一收拢到 `docs/real-machine-acceptance-backlog.md` **簇 125**
> （小红书 Native 切换：只读矩阵与写动作验收），不再计入本 change 的任务数、不再阻塞归档。
> 簇 125 与已有的**簇 122 / 123 是同一台机器、同一个分身**，三簇应在一次真机 session 里连着验。
>
> **原 5.1 里夹带的实装分支已随条目一并搬走**（簇 125.3）：若真机确认开帖落错误页，
> 须追加「开帖改用可信指针输入触发就地弹层」的实装任务——这条不因本节移出而消失。
>
> **口径不变**：登记 ≠ 已验证。小红书侧自 Native 迁移以来**真机零覆盖**，
> MUST NOT 因本 change 归档而读成「验过了」。

## 6. 控制仓收口

- [ ] 6.1 运行 `openspec validate restore-native-xiaohongshu-action-honesty --strict`，记录输出
  - 阶段性记录（2026-07-28，change 未收口故不勾选）：输出 `Change 'restore-native-xiaohongshu-action-honesty' is valid`，退出码 0。
- [ ] 6.2 运行 `openspec show restore-native-xiaohongshu-action-honesty` 自查能力与要求条数
- [ ] 6.3 与同批 `restore-native-xiaohongshu-session-guards` 对账集成顺序：两者共写 `native/page-engine/src/engine.rs` 的小红书执行入口与 `test/native-page-engine/` 目录。集成前 `git fetch` + rebase 到最新 `master`，跑 `cargo test` 与 `npm test` 后再合；并核对该 change 的「小红书评论提交须开提交窗口」与本 change 的「评论提交合成完整文本」两条同时生效（窗口在外、写入在内），后落地的一方在此记录核对结果（参照 oracle.md 提交窗口条：xhs 四处窗口预算在 317cd47^ 已逐处坐实，勿照抄 Facebook 值）
- [ ] 6.4 在本清单回写 Edge 与控制仓的 commit sha、偏离说明，以及与并行 change 的重叠文件（Facebook 路由 / 微信适配器 / 协议四处同步文件本 change 不碰）
  - 进度说明（2026-07-29，**分波回写中，change 未收口故不勾选**）：Edge 侧 sha 已逐条落在各任务行尾。截至第二波，本 change 在 `native-migration-repair` 上的提交为 —— 第一波 `552eda1`（1.1–1.3 / 1.12 用例与夹具）、`8b99183`（2.1 / 2.2）；第二波 `a45fc81`（1.13–1.19 用例）、`19d4872`（2.3–2.15 / 3.2）。**控制仓 sha 待本文件提交后补**。重叠文件实测：本 change 碰了 `native/page-engine/src/{engine.rs,model.rs,probe.rs,xhs.rs}` 与宿主 `src/native-page-engine/{browse-session.ts,client.ts}`，前四者中 `engine.rs` 与 `restore-native-xiaohongshu-session-guards` 共写、后两者是该 change 的单写区边缘（见 6.5）；`input.rs` / `facebook/**` 与并行 change `restore-native-actuation-humanization-and-locating` 的改动面在本波**零交叉**（该 change 的 `3a1b2b3` 只动 Rust 的 input/locating/facebook 三处，与本 change 的 xhs 路由与 probe 不相交）；协议四处同步文件、Facebook 路由、微信适配器**全程未碰**。
- [ ] 6.5 与 `restore-native-xiaohongshu-session-guards` 再对两处集成边界（本次覆盖漏洞收口新增）：① 2.9 若落在 `xhs-page-probe.js` / `probe.rs`，与该 change 的 1.2 / 1.3（周期探针平台化、按页面类型分类）读同一份探针输出，字段增删须同时过它们的判据；② 2.11 若走宿主补发回执，与该 change 的 4.1（`src/native-page-engine/browse-session.ts` 逐命令诊断改平台中立）同文件。集成前 `git fetch` + rebase，跑 `cargo test` 与 `npm test` 后再合，在此记录对账结果
- [ ] 6.6 在本清单记录本次「参照书覆盖漏洞」收口的处置结论：就地补任务 = 1.13–1.19 / 2.9–2.15 与新增真机项 5.8–5.10；范围外具名交接 = 4.5（承接方 `restore-native-xiaohongshu-session-guards`）；通电对账 = 4.6。三类都必须有结论，不得留空 <!-- 2026-07-31 指针订正：文中的「新增真机项 5.8–5.10」已移出本 tasks.md，现落在 `docs/real-machine-acceptance-backlog.md` **簇 125.9 / 125.10**（原 5.10 是登记动作、随移出一并关闭）。记处置结论时按簇号写 -->

## 边缘诚实性缺口清单（2026-07-30 用户裁定「要做」，本 change 是主要属主）

> 全文见控制仓 `docs/edge-honesty-gap-inventory.md`（12 条经对抗复验确认成立，带 `文件:行`、
> 今天回报什么、为什么错、真机最坏后果）。**12 条里有 9 条落在本 change 的单写区
> `native/page-engine/src/xhs-command-router.js`**，因此归属本 change，不由他流代改。

- [ ] H.1 按清单逐条判「修 / 显式弃守」，结论回写清单与本节（**MUST NOT 静默跳过**）
      - 进度（2026-07-31）：清单已加「处置状态」表，12 条**首次逐条过了一遍**。
        **已修 4 条**（E6 评论点赞 / E8 共享判据扇出 7 处 / E10 设为封面 / E11 兼容步骤两处，均 edge `52a2110`）。
        **余 8 条仍是「未判」而非「不做」**：E2 / E7 / E9 属主已明列本轮范围外；E12 落点不在本清单主属主
        （归拟人化流的 H.2）；E1 / E3 / E4 / E5 至今无人正式判过。**本条因此不勾**——
        H.1 要的是逐条给出「修 / 显式弃守」结论，「本轮没做」不等于「判过了」。
- [x] H.2 优先处置**会错报成功**的那几条（自证循环、判据过宽里判正证据的那些）；
      只会**错报失败**的可降级排期 —— 红线针对的是静默假成功，方向诚实的悲观回执危害小得多
      <!-- aidcp-edge 52a2110 三条最狠的已修：① 发布布尔选项期望「关」时「读不到 = 达成」、连点都不点（删掉 `||row` 兜底，找不到真开关改诚实失败）；② 设封面往上找容器停在轮播「当前显示」层、连按钮都不点（去掉任意 div 兜底、改有界回溯只认图片项容器，证据必须封面专属，删掉「已…封面」文本兜底）；③ 搜索筛选误判后既不点也进不了未确认分支、把未筛选结果当筛过的返回（改成只有明确「是」才跳过点击、点后有界轮询每轮重解析、确认不上即 unconfirmed 且不返回卡片）。另修一条清单外的：兼容路径的评论输入框此前判据里硬写 `|| 是评论框` = 无条件回成功，改读焦点落位 -->
- [x] H.3 清单里标注「今天不可达、通电即生效」的潜伏项（评论点赞、通知分栏、设为封面），
      处置时 MUST NOT 因「现在跑不到」就当已解决；入口白名单已放行，生产者一补就生效
      <!-- aidcp-edge 52a2110 评论点赞与设为封面均按「通电即生效」处置、未因当前不可达跳过：评论点赞改读图标状态位 + 有界轮询等翻转（不再看类名、不再 already_active 早退），设封面改 fail-closed。**单侧依赖已坐实并登记，见下方「H 收口记录」**：云端 publish-dispatcher 硬写 cover=undefined 且 set_cover 不在 bestEffort 白名单内 = fail-fast，接回封面时云端须同批改，否则「封面选错」会升级成「稿子发不出去」 -->
- [x] H.4 共享判据 `active()` / `selected()` 的裸子串匹配是**扇出点**（8 个决策点据此回 ok=true），
      修它的收益最大；但要先确认各消费点的正确判据各是什么，不能一刀切
      <!-- aidcp-edge 52a2110 两个判据合并成一个三态 `stateOf`（'on' / 'off' / '' = 读不到），读不到**绝不塌成 off**；类名支改整词匹配（token 按 -/_ 分段）+ 否定形拒绝（分隔式 not-selected / 粘连式 unliked 均判 off）+ 计数容器（liked-count）判读不到；真表单控件 checked 位 > 属性白名单 > 类名逐层短路。**扇出点实测是 7 个不是 8 个**（穷举核对，本文件之外零扇出），逐点改法见 H 收口记录 -->
- [ ] H.5 复验只覆盖了 69 条候选里的 16 条，**余下 53 条未复验**。收口前补跑一轮，
      或显式记录「不再扩大清单」并说明理由


### H 收口记录（2026-07-31 · aidcp-edge `52a2110`）

**7 个决策点逐条改法**（穷举核对，本文件之外零扇出；原清单写「8 个」是多数了一个）：

| 决策点 | 改前 | 改后 |
| --- | --- | --- |
| 搜索筛选确认 | 判据假阳性 → 连筛选项都不点，复判也过 → 返回未筛选卡片当已筛过 | 只有明确「已生效」才跳过点击；点后 1200ms 有界轮询、每轮重解析；不确认即 `search_filter_unconfirmed` 且**不返回卡片列表** |
| 详情页评论点赞 | 类名含 active/selected/liked 即 `already_active` 早退、零点击；点后单次采样；点击返回值丢弃 | 控件优先取行内点赞容器；状态读**图标状态位**（不看类名）；点击返回假即 `control_not_actuated`；1500ms 有界轮询等翻转 |
| 兼容步骤点击确认 | `selected(el) \|\| 是评论输入框`（评论框**无条件**回成功）；`attempts:1` 却报 `escalated` | 换主路径同源硬判据（赞/收藏读图标位、关注读关注态、评论框读**焦点落位**）；有界重试上限 3、`attempts` 如实回报；从未点着回 `no_target`。另加自证闸：对非可编辑元素的输入步直接拒绝 |
| 发布地点/合集候选 | 往上找容器到任意 `div`，常把候选列表本身圈进来 → 行文本恒含目标值 = 自证 | 有界行回溯 + 排除候选子树；文本证据挡否定形；点击返回值不再丢；1000ms 有界轮询 |
| 发布选项（布尔支） | `first([...],row) \|\| row` 兜底 + `selected(control)===desired`：期望「关」时 `false===false` → 回 `already_active`、**连点都不点** | **删掉 `\|\| row` 兜底**（行本身就是开关时仍接受）；找不到开关即 `publish_option_not_found`；只有**读到明确状态**且等于期望才早退，读不到一律去点 |
| 发布选项（枚举支） | `selected(target) \|\| text(row,500).includes(value)`：行含候选层即自证，且「不公开」含「公开」 | 行包含目标时不采信行文本；文本证据挡否定形；有界轮询 |
| 设为封面 | 往上找容器到任意 `div` → 停在轮播「当前显示」层 → 判据恒真 → **连「设为封面」都不点**；另有「已…封面」文本兜底 | 有界回溯只认真正的图片项容器（**无 div 兜底**）；证据必须**封面专属**；「设为封面」必须找到且点着，否则诚实失败；文本兜底删除 |

**测试**：新增 `test/native-page-engine/xhs-state-evidence.test.ts` 14 例（这 7 个点此前**零覆盖**）。
**归因已独立复现**（不只是「改完全绿」）：把被测分片还原成改动前版本后 **14 例里 11 例转红**，
红的正是针对各缺陷的那些；余 3 例绿是如实情况——1 例的旧码在该夹具下本就诚实（说谎只发生在判据**假阳性**时，
那一面由另一例覆盖），2 例是**保留行为**的护栏、本就该两边都绿。
另改 1 个既有用例：`router-contract.test.ts` 的设封面夹具原本把「点图块 → 图块变激活」当封面证据，
那正是自证形态，改成「点『设为封面』→ 图块拿到封面标记」。

**验证实测**：`test:acceptance` 31/31（安全红线全过）· 全量 `npm test` 2882 tests / 2881 pass / 0 fail / 1 skip（gated 真机）·
`typecheck` 通过 · `gate:native` OK（fmt + clippy -D warnings + cargo test）。

**三处具名折中（不是遗漏）**：

1. **兼容步骤的 `escalated` 语义只做诚实化、未新增档位**：协议的动作结果枚举只有
   `success / escalated / no_target / guard_blocked`，**没有「本次未确认」这一档**，加一档要走协议四处同步 + 动热点文件，
   超出本轮边界。改法是**把 `escalated` 变诚实**——真做有界重试、`attempts` 回报实测次数、只在打满仍未确认时才报升级。
   **同块内 `page.scroll` 那支仍是 `attempts:1` + `escalated`，有意未动**：滚不动是**结构性到底**、不是「重试到顶」的结论，
   且是已落地行为、有既有用例钉着。
2. **两处失败复用了粗粒度原因码**（找不到开关 vs 找不到标签共用一个；封面的三种失败共用一个），
   诊断粒度因此变粗。原因是本仓纪律「MUST NOT 新增云端没有归宿的原因码」——要加精确码须先在云端接线。
3. **搜索筛选回执带不上「实际筛过什么」**：那条成功终局走的是卡片列表输出、不是动作回执，
   加字段要改引擎数据模型 + 云端得有消费方。按同一条纪律未硬加。

**两处只改善未根治（如实登记）**：
① 评论点赞的**控件定位**仍保留行内文本兜底（可能命中「赞 12」这类计数标签）——判据已是硬的，定位仍偏松；
② 类名支的中文否定（`未点赞` 之类）成立机制是「读不到」而非「判 off」——正向片段全是 ASCII，
中文 class token 产生不了正命中，结果安全但机制与英文那支不同。中文否定词用在**文本回显证据**上（「不公开」不再证明「公开」）。

**范围外未碰**：话题/提及候选那一支（另有自证形态、不在这 7 点内）、已发布笔记身份抓取、配图上传后置校验。

### ⚠️ 单侧依赖：设为封面 MUST NOT 只改边缘（本轮已坐实，交接给发布链属主）

云端 `aidcp-cloud/src/publish-agent/publish-dispatcher.ts` 硬写 `cover: undefined`，
且 `command-sequencer.ts` 的 `bestEffort` 白名单只含 `add_with_candidate` / `set_option`
—— **`set_cover` 是 fail-fast**。因此：

- **今天零影响**：云端从不下发该指令，这段边缘代码在生产上不可达。
- **一旦封面被重新接上而云端不动**：边缘现在会诚实回未确认，fail-fast 会让**整帖在提交前中止**——
  危害从「封面选错」升级成「稿子发不出去」。云端那行注释自己就写着「强发 set_cover 会踩 edge fail-closed……
  非 best-effort 整帖 failed」。
- **接回封面时云端必须同批做**：要么把 `set_cover` 放进 best-effort，要么先在真机上标定出封面锚点
  （真机项见 `docs/real-machine-acceptance-backlog.md` 簇 125）。

### 生产上会看到的变化（预期内，MUST NOT 当成回归）

- 搜索筛选确认不上时开始如实回未确认，**评论支线短期失败率会上升**——今天它在拿未筛选结果冒充筛过的。
- 发布的选项与候选会开始出现诚实的未确认；这两类在云端都是**尽力而为、不阻断发布**，
  **稿子照发、不丢稿**，只是台账不再把没设上的合规声明记成已设置。
