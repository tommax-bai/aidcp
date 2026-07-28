> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 表征当前退化（失败优先）

- [ ] 1.1 新建 `test/native-page-engine/xhs-behavior-parity.test.ts`，加一条失败用例：带联系方式串码的评论命令，断言提交进编辑器的文本同时含正文与串码（当前实现只含正文，必失败）（参照 src/browse/browse-session.ts:2543-2553；串码须单独整段插入绕开 @/# 补全 — 见 oracle.md ②）
- [ ] 1.2 加失败用例：开帖后页面处于「笔记暂时无法浏览」错误页且地址仍含笔记 id，断言返回非成功且不产出 `note_detail` 输出（参照 src/browse/browse-session.ts:1876-2036；缺错误页否决/正面详情证据/令牌门控 — 见 oracle.md ①）
- [ ] 1.3 加失败用例：详情容器存在但标题、正文、图片三项皆空，断言返回 ambiguous 而非确认详情（参照 src/browse/browse-session.ts:2067-2110 正文渲染门 + note-extractor.ts:283-292；缺渲染门与选择器排除 — 见 oracle.md ①）
- [ ] 1.4 加失败用例：看图命令断言输出为动作回执且回执带实际前进张数；无轮播时断言 `no_target` 回执（参照 src/browse/browse-session.ts:2797-2844；旧回执即 no_target / browsed=N — 见 oracle.md ⑤）
- [ ] 1.5 加失败用例：翻页控件在第一次前进后被替换，断言回执张数等于实际观察到的前进次数、不等于请求张数（参照 同上 2807-2844；旧实现循环内重解析控件、点不动即 break，但**无图序前进校验**需新写 — 见 oracle.md ⑤）
- [ ] 1.6 加失败用例：返回列表后落在非列表面，断言动作回执 `ok=false`（参照 src/browse/browse-session.ts:2735-2795；⚠ 旧回执 :2794 恒真、不可照抄 — 见 oracle.md ④）
- [ ] 1.7 加失败用例：页面同时存在互动条内具名点赞控件、聚合赞数控件、含「取消赞」文本的反向控件，断言只解析到互动条内的那一个；互动条缺失时断言 `control_not_found`（参照 src/browse/browse-session.ts:2298-2360 + flows/anchors.ts:46-64；互动栏无 aria/无文本，唯一锚点是语义 class — 见 oracle.md ⑥a/⑥b）
- [ ] 1.8 加失败用例：控件在首次采样之后、有界窗口之内才翻转，断言判成功；全程不翻转断言 ambiguous `state_unchanged`，且控件文本含「已」不得提成成功（参照 同上 2339-2341；真机翻转 300–600ms、上限 1500ms — 见 oracle.md ⑥a）
- [ ] 1.9 加失败用例：通知列表同时含头像行、裸列表项与真实通知行，断言只产出真实通知行；同一发送者的多条通知断言 itemKey 互不相同或为空；无正文容器时断言正文为空串且不回落整行文本（参照 src/browse/notification-monitor.ts:148/163-164/169；行容器两级、正文缺失发空串、itemKey 排除主页链 — 见 oracle.md 通知三条）
- [ ] 1.10 加失败用例：滚动评论区后评论区位置未变，断言动作回执 `ok=false`；另一例断言回执里的评论条数等于滚动后页面上实际可见的条数、不等于请求的步数（当前实现恒 `ok:true` 且直接回报请求值，两例必失败）（参照 src/browse/browse-session.ts:2797-2844 同族 scrolled=N / no_scroll 回执 — 见 oracle.md ⑤）
- [ ] 1.11 加失败用例：看图翻页过程中新加载出的图片，断言仍随本次命令到达云端（不因终局改成动作回执而丢掉图片证据）；同时断言本次命令只有一个终局（参照 src/browse/browse-session.ts:1284-1311 refreshOnly 快照；旧规则=抽不到图不发、失败不伪造快照 — 见 oracle.md ⑤）
- [ ] 1.12 修 `test/native-page-engine/router-contract.test.ts:37-39` 的夹具：不再在 `HTMLElement.prototype` 上全局钉死 `getBoundingClientRect`（当前返回固定 100×40，使 `xhs-command-router.js:7-12` 的宽高判定恒真），改为按用例给定几何，使可见性判断在测试里可真伪两态；修完重跑既有小红书路由用例并记录因此暴露的既有失败。**只改小红书那份契约测试，`facebook-router-contract.test.ts` 的同款夹具属 Facebook 平价 change，不动**（参照 oracle.md ⑥a 末条：router-contract.test.ts:34-36 钉死几何使 :84 那条互动用例无保护力）

- [ ] 1.13 加失败用例：页面规则层的未读角标读数——宽 / 窄双布局 DOM 同时存在隐藏侧栏入口与可见底部入口时断言取可见那个；角标容器里只有常驻图标与空槽时断言「无未读」；数字角标断言「有未读」且计数带出；无数字红点断言「有未读」计数 0；读不到入口时断言返回「读不到」而非「无未读」（当前 Native 无任何未读读数，全部必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:17-91`；判据为 2026-06-23 真机校准、须按 5.8 复核 — 见 oracle.md 未读监测体条）
- [ ] 1.14 加失败用例：「赞和收藏」「新增关注」两类命令断言产出动作回执，动作名与云端角色等待的规范名一致（`browse_notification_likes` / `browse_notification_follows`，见 `aidcp-cloud/src/agents/notification-like-browser.ts:36`、`notification-follow-browser.ts:35`）；分类栏未命中时断言 `ok=false` + `no_target`；发送者抽取失败时断言清零回执仍产出（当前只上报 `notification.items`、不产回执，必失败）（参照 `317cd47^:src/browse/browse-session.ts:3161-3173/3195-3210` — 见 oracle.md「看一眼」条）
- [ ] 1.15 加失败用例：「评论和@」栏首屏 2 行、滚动后追加 2 行 → 断言上报 4 行；另一例断言云端下发的滚动上限真参与循环上限（当前点一次栏就抽取、`p.scrollMax` 全文零读取，两例必失败）（参照 `317cd47^:src/browse/browse-session.ts:3116-3133` 的行数不增判到底 + `max(scrollMax,12)` — 见 oracle.md 清零循环条）
- [ ] 1.16 加失败用例：通知首页三栏未读计数——页面正文里出现「赞 312」这类非分类栏计数时断言不被读成未读；分类栏角标文本为「1.2万」时断言不折算成条数；三栏均无数字角标时断言全 0（当前取整页前 5000 字做正则，三例必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:93-123` 的叶子 tab 作用域 + 1–3 位纯数字叶子守卫 — 见 oracle.md per-tab 计数条）
- [ ] 1.17 加失败用例：页面只存在含「赞」「关注」字样的非分类栏元素（笔记卡片 / 侧栏项 / 包裹容器）时，断言分类栏点击诚实回未命中，不得点到包裹容器、也不得按类名激活态猜成成功（参照 `317cd47^:src/browse/browse-session.ts:3112-3114/3166-3167` 的叶子 tab + 严格文本判据 — 见 oracle.md 分类栏点击条）
- [ ] 1.18 加失败用例：通知项正文第 200 个 code point 落在 emoji 上时，断言截断不劈裂代理对且补省略号（当前 `xhs-command-router.js:6` 按 UTF-16 `slice`，必失败）（参照 `317cd47^:src/browse/notification-monitor.ts:146` 的 `Array.from` 截断 — 见 oracle.md 截断条）
- [ ] 1.19 加失败用例：断言通知列表与通知首页上报里不含页面规则自造的墙钟批次序号（现为 `xhs-command-router.js:134/139` 的 `epoch:Date.now()`）；该字段在协议里是可选（`src/comm/protocol.ts:1782/1790`），去掉不动协议（参照 oracle.md epoch 条：批次序号唯一来源是未读「无→有」翻转，本 change 只禁自造）

## 2. aidcp-edge — 恢复动作诚实（两条 critical 优先）

- [ ] 2.1 在小红书评论路径合成「正文 + 联系方式串码」的完整提交文本，提交前回读校验覆盖合成后的完整文本；回读不含串码即在提交前返回 not_started，不派发提交（参照 src/browse/browse-session.ts:2450-2648；缺清场闸/串码整段插入/提交三态 — 见 oracle.md ②）
- [ ] 2.2 把开帖成功判据改为正面详情证据（详情容器 + 标题/正文/图片至少一项非空），错误页语义命中即诚实失败；未确认打开一律不产出 `note_detail` 输出。**两个判据点都要改**：点击后的那处（`xhs-command-router.js:194`）与「已在详情页」的快速返回处（`:188`，当前地址里有目标 id 就直接回详情、连点击都不发）（参照 src/browse/browse-session.ts:1876-2036 + probe.rs:158 的 PageKind::Error；⚠「必落 404」未在 Native 复核，见 oracle.md ①）
- [ ] 2.3 看图命令改为返回动作回执：每步重新解析翻页控件、校验图序真前进、按实际前进张数回报；无轮播回 `no_target`；不再以 `refreshOnly` 详情充当终局（参照 src/browse/browse-session.ts:2797-2844；缺 total 探测/viewed 计数/循环内重解析 — 见 oracle.md ⑤）
- [ ] 2.3a 安排看图过程中新图片的去处（先定机制再改判据）：一条命令只能回一个输出（`evaluate_router` 返回单个 `(EffectPhase, CommandOutput)`，宿主按 `kind` 走互斥分支），而当前那条 `refreshOnly` 详情是云端参考图刷新（`aidcp-cloud/src/agents/curated-note-evaluator.ts:114-118`）与灵感 / 观测笔记 `referenceImages` 更新（`aidcp-cloud/src/server.ts:4914`）的唯一来源。二选一并在此记录所选：① 回执携带本次观察到的图片；② 宿主在收到回执后补一次详情读取。**验收判据：改完后跑一遍云端参考图刷新的既有用例仍绿，且新图片确实到达云端**；不得只改回执把图片证据静默丢掉（参照 src/browse/browse-session.ts:1284-1311：旧实现是回执与 refreshOnly 快照两条出口并存 — 见 oracle.md ⑤）
- [ ] 2.4 返回列表的回执 `ok` 改为由观察到的列表面推导，去掉硬编码为真（参照 src/browse/browse-session.ts:2735-2795 的机制；⚠ 回执 ok 必须新写，旧的 :2794 恒真 — 见 oracle.md ④）
- [ ] 2.4a 滚动评论区的回执改为实测：`ok` 由滚动前后位置差推导（未移动即诚实非成功），回报的评论条数改为滚动后页面上实际可见的条数，去掉「直接回报请求值」；对应云端 `comment-reviewer` 的「已读评论数」不再恒 1（云端侧不改，只验证输入变诚实后投影随之变真）（参照 oracle.md ⑤ 的 scroll_comments 同族测试：按实测位移与实测条数回报）
- [ ] 2.5 点赞 / 收藏 / 关注改为互动条内结构化定位（排除聚合计数与反向控件），去掉「按钮→行内→块」三级文本回落（参照 flows/anchors.ts:46-64 + browse-session.ts:2298-2360/2685-2732:349 七候选；缺互动栏作用域与具名控件 — 见 oracle.md ⑥a/⑥b）
- [ ] 2.6 点赞 / 收藏 / 关注的确认改为有界轮询状态翻转，去掉固定睡眠后单次采样，去掉「控件文本含『已』」这条兜底；未翻转回 ambiguous `state_unchanged`（参照 browse-session.ts:2339-2341 有界轮询；⚠ 关注侧旧实现无后验、不可照抄 — 见 oracle.md ⑥b）
- [ ] 2.7 通知抽取回到真机校准契约：行按已标定容器结构选取（去掉裸列表项与命中头像行的 class 猜测）、正文只取正文容器且缺失发空串、itemKey 逐条稳定且不得使用发送者主页链、无逐条身份时留空（参照 notification-monitor.ts:128-138/148/163-164/169/209；另注意 oracle.md 覆盖漏洞 4/6：per-tab 计数与 code-point 截断本清单未覆盖）
- [ ] 2.8 先确认云端与 CLI 已无 v1 有序步骤（`plan_execute`）的活跃产出方，确认后删除小红书路由里的该分支；若确认仍有活跃产出方，改为按实测位移回报滚动步骤。**判定依据必须实读后写在此处**，且已知两条反证据必须逐条回应：① 规则式规划器产的 `note.like_button` / `note.follow_button` 与路由映射表**是对得上的**（`aidcp-cloud/src/planner/simple-planner.ts:24-48`），只有收藏那条名字不同；② 规划器的 LLM 兜底分支（`:68-78`）允许模型自由产出 `actionId` 且 `op` 白名单含 `scroll`（`:16`），所以「`page.scroll` 步骤不可能被产出」在代码上证明不了。**判不清即默认走「补测量」，不删**

- [ ] 2.9 在小红书页面规则层恢复未读角标的结构化读数：宽 / 窄双布局都遍历、取可见那个入口；未读 = 入口角标容器里图标之外的可见真实角标（空槽 = 无未读），红点无数字也算未读、计数仅附带；读不到入口或读取出错 MUST 回「读不到」，MUST NOT 回「无未读」。落点二选一并在此记录所选：① 扩 `native/page-engine/src/xhs-page-probe.js` 的返回结构（**须同步 `native/page-engine/src/probe.rs` 的 `RawPageSignals` 与 `StructuralSignals`，后者带 `deny_unknown_fields`，漏改即整条探针解析失败**）；② 在 `xhs-command-router.js` 加一条只读命令。**周期调用与未读信号的发送方不在本 change**（见 design.md「覆盖漏洞的范围外交接」与任务 4.5 / 4.6）（参照 `317cd47^:src/browse/notification-monitor.ts:17-91`；判据 2026-06-23 校准、须按 5.8 复核 — 见 oracle.md 未读监测体条）
- [ ] 2.10 通知「评论和@」栏恢复滚到底清零循环：每轮先数行数、连续 2 轮行数不增即判到底、硬上限取 `max(云端滚动上限, 12)`、每轮滚约 0.8 个视口高并留加载等待；使云端下发的滚动预算真参与上限，不再是「声明并校验却无人读取」的悬空参数（`src/native-page-engine/command-mapper.ts:61-63` 与 `native/page-engine/src/command.rs:651-662` 已在传与校验）（参照 `317cd47^:src/browse/browse-session.ts:3116-3133` — 见 oracle.md 清零循环条）
- [ ] 2.11 「赞和收藏」「新增关注」两类改为以动作回执终局：动作名用云端角色等待的规范名；分类栏未命中回 `no_target`；发送者抽取失败只记日志、绝不阻断清零回执。**与 2.3a 同一个机械约束（一条命令只能回一个输出）**：现 `ActionReceipt`（`native/page-engine/src/model.rs:301-313`）无通知项字段，二选一并在此记录所选——① 给回执加通知项字段并同步 `native/page-engine/src/xhs.rs` 的输出解析；② 宿主在 `notification_items` 输出上补发回执（`src/native-page-engine/browse-session.ts:340-342`，属宿主装配面，按 6.5 与 session-guards 对账）。**验收判据：改完后通知联系人名册仍收到 items（`aidcp-cloud/src/server.ts:6440`），且云端两个分类浏览角色能凭回执结案**；不得只加回执把 items 静默丢掉（参照 `317cd47^:src/browse/browse-session.ts:3161-3210` — 见 oracle.md「看一眼」条）
- [ ] 2.12 通知首页三栏未读计数改为在真实叶子分类栏作用域内读纯数字叶子角标（1–3 位），排除同样带 tab 字样的包裹容器（防跨类泄漏），读不到即 0；去掉整页正文正则，禁止「解析不出就当 1」，也不得把「1.2万」这类单位文本折算成条数（下游是云端清零判据 `aidcp-cloud/src/agents/notification-triage.ts:55-77`：计数永不归零会让每趟巡视跑到尝试上限）（参照 `317cd47^:src/browse/notification-monitor.ts:93-123` — 见 oracle.md per-tab 计数条）
- [ ] 2.13 分类栏点击改为在叶子分类栏集合内按严格文本判据挑选（评论类整串等于「评论和@」或以「评论」开头且含 @；赞 / 关注类限制文本长度以容纳角标数字），去掉「按钮→行内→块」三级全页文本回落；是否命中由点击结果推导，不用类名激活态猜测（参照 `317cd47^:src/browse/browse-session.ts:3112-3114/3166-3167` — 见 oracle.md 分类栏点击条）
- [ ] 2.14 通知项各字段改 code-point 安全截断并在超长时补省略号，长度上限回到字段级（正文 200 / 昵称 40 / 笔记标题 80 量级），不再统一走整行 blob 量级的 UTF-16 切片（参照 `317cd47^:src/browse/notification-monitor.ts:139/146` — 见 oracle.md 截断条）
- [ ] 2.15 通知列表与通知首页上报去掉页面规则自造的墙钟批次序号；批次序号只应有一个来源——未读「无→有」翻转时取的单调序号，该来源随未读监测体归承接方（见 4.5）。**实读记录**：当前云端下游取的是会话内巡视序号（`aidcp-cloud/src/agents/notification-triage.ts:57`、`notification-classifier.ts:41`），故去掉自造值不需要云端配套改动，但该结论须在实装时复读一次再确认（参照 oracle.md epoch 条：迁移新造字段，不可照抄旧代码「改回去」）

## 3. aidcp-edge — 发布原子回到既有契约

- [ ] 3.1 依据 `openspec/specs/publish-pipeline/spec.md`「边缘指令运行时逐条执行并每条后置校验如实回报」，在 Native 小红书正文填写上恢复逐字增量输入、每个换行独立派发真实 Enter、有界确认段落数/已写前缀/光标归尾、语义相似度 ≥ 0.90 放行、失败清场
- [ ] 3.2 依据 `openspec/specs/publish-submit-integrity/spec.md`「成功判定锚定真实成功信号」，把提交成功判据从全页文本/地址正则改为绑定本次草稿的真实成功信号；已派发未确认回 ambiguous 并记录已派发（参照 flows/publish-command-handlers.ts:1332-1432；穿闭合 shadow 定位 + 只认成功文案 + no_target 时 submitDispatched 保持假 — 见 oracle.md ③）
- [ ] 3.3 更新 `docs/real-machine-acceptance-backlog.md` 中「小红书逐字输入辅助未受影响」这条已失效的记述所在条目（70.6），改为指向本 change 的真机验收项；不改动该文件其他簇

## 4. aidcp-edge — 验证（代码级）

- [ ] 4.1 运行 `npm run test:acceptance`，记录安全红线用例（协议不漂移 / 未授权不发布 / 风控不自残）全过
- [ ] 4.2 运行全量 `npm test` 与 `npm run typecheck`，记录通过数与因夹具修正（1.12）新暴露的既有失败
- [ ] 4.3 运行 Rust 侧 `cargo test` 与 `cargo fmt --check`，记录通过数
- [ ] 4.4 明确记录本次**未做**的门：未打安装包、未部署、未替换运行中的桌面客户端、未做任何真机写动作

- [ ] 4.5 登记「未读监测体的宿主周期装配与未读信号发送方（含单调翻转批次序号的持有位置）」为本 change 范围外项，已在 design.md「覆盖漏洞的范围外交接」具名交接给 `restore-native-xiaohongshu-session-guards`（其 1.2 周期探针按平台分类适配、6.1 恒假装配块逐条对账、6.4 退役监测体去留结论）。登记时须写明：`src/browse/notification-monitor.ts` 在 `src/` 里只被恒假块引用，按 6.4 的三分类会落进「仅恒假块引用」，**若按孤儿删除则本 change 的通知类修复永久不通电**——该项要的是恢复而不是清理
- [ ] 4.6 通电对账（承接方不落地即不算修好）：确认小红书未读信号在运行路径上确有发送方——当前边缘全仓仅协议定义（`src/comm/protocol.ts:110/1965`）与验收测试出现 `notification.detected`，而云端整条巡视链的唯一触发源就是它（`aidcp-cloud/src/agents/notification-gatekeeper.ts:48`、`src/orchestrator/role-dispatcher.ts:2062`）。未落地则在此记录为阻断依赖，并明确写下「通知抽取 / 清零 / 计数类修复已实装但生产未通电」，**不得按已生效结案**

## 5. 真机验收项（必须真机才能定论，不得当成已确认事实）

- [ ] 5.1 **开帖是否真的落到错误页**：在 dev、tom 分组账号上从首页封面开一篇笔记，记录开帖后地址是否带访问令牌、返回详情正文是否为空。若单页应用拦截了程序化点击、导航仍走内部路由，则本条降级为指纹问题，2.2 的证据要求不变；若确认落错误页，追加实装任务：开帖改用可信指针输入触发就地弹层（参照 docs/xhs-layout-states.md:58-62 与 oracle.md ①：裸链 300031 结论出自 2026-06-27，Native 路径未复核）
- [ ] 5.2 **看图挂起是否复现**：真机跑一次详情深读，确认是否出现「看图这一步一直挂着直到会话看门狗杀场」的实例。复现则登记独立跟进项：云端深读等待表加有界超时（`aidcp-cloud/src/agents/deep-reader.ts`）；未复现则记录为未复现，不做云端改动（参照 oracle.md ⑤：旧实现两种出口都是 action.completed，深读挂起源于回执缺失）
- [ ] 5.3 **点赞类翻转窗口**：真机测量点赞 / 收藏 / 关注的状态翻转耗时分布，确认 2.6 的有界窗口上限足够；记录实测值，不写进 spec（参照 oracle.md ⑥a：旧注释实测翻转 300–600ms、上限 1500ms，可作窗口起点）
- [ ] 5.4 **通知去重折叠的真实规模**：真机跑一次含同一发送者多条通知的巡视，确认修复前后处理条数差异；当前只有代码与旧注释对照，无线上数据（参照 oracle.md 去重键条：主页链 per-user 折叠 + 云端两条消费路径受影响不同）
- [ ] 5.5 **通知行选择器**：在真机上 dump 一次通知页结构，确认 2.7 采用的容器结构与当前平台一致；结构若已变，以本次 dump 为准并记录（参照 oracle.md 行选择器条：`.tabs-content-container > .container` 与 `note-id` 属性出自 2026-06-24 dump，须重测）
- [ ] 5.6 **评论合成文本的编辑器行为**：真机发一条含联系方式串码的评论，确认合成后的完整文本被平台原样接受（不被自动补全劫持、不被截断）（参照 oracle.md ②：串码 verbatim 整段插入、不 trim、避开 @/# 补全劫持）
- [ ] 5.7 把 5.1–5.6 按共享真机环境聚成簇，登记进 `docs/real-machine-acceptance-backlog.md`，并在登记时标注与 `native-page-engine-production-cutover` 真机验收项 9.4 / 9.5 的依赖关系（该 change 的 `tasks.md` 由其属主更新，本 change 不改）

- [ ] 5.8 **未读角标判据是否仍成立**：在宽（左侧栏）与窄（底部图标栏）两种布局各测一次，确认取到的是可见入口、无未读时不误报、数字角标与无数字红点都认出。判据出自 2026-06-23 校准、窄布局曾真机实测漏报 10 条未读，距今一月余，**不得当成已验证事实**（参照 oracle.md 未读监测体条的双布局遍历告警）
- [ ] 5.9 **清零是否真收敛**：在真机上制造多于一屏的未读，确认 2.10 的滚到底循环 + 2.12 的真实角标计数合起来能让该栏计数真归零、三栏清零循环能正常结束；桩验不了平台的真实加载与角标更新（参照 `openspec/specs/notification-monitoring/spec.md`「循环直到三栏清零」）
- [ ] 5.10 把 5.8–5.9 一并纳入 5.7 的簇登记（5.7 按原文只涵盖 5.1–5.6，本条补齐本次新增的两项，避免漏登）

## 6. 控制仓收口

- [ ] 6.1 运行 `openspec validate restore-native-xiaohongshu-action-honesty --strict`，记录输出
- [ ] 6.2 运行 `openspec show restore-native-xiaohongshu-action-honesty` 自查能力与要求条数
- [ ] 6.3 与同批 `restore-native-xiaohongshu-session-guards` 对账集成顺序：两者共写 `native/page-engine/src/engine.rs` 的小红书执行入口与 `test/native-page-engine/` 目录。集成前 `git fetch` + rebase 到最新 `master`，跑 `cargo test` 与 `npm test` 后再合；并核对该 change 的「小红书评论提交须开提交窗口」与本 change 的「评论提交合成完整文本」两条同时生效（窗口在外、写入在内），后落地的一方在此记录核对结果（参照 oracle.md 提交窗口条：xhs 四处窗口预算在 317cd47^ 已逐处坐实，勿照抄 Facebook 值）
- [ ] 6.4 在本清单回写 Edge 与控制仓的 commit sha、偏离说明，以及与并行 change 的重叠文件（Facebook 路由 / 微信适配器 / 协议四处同步文件本 change 不碰）
- [ ] 6.5 与 `restore-native-xiaohongshu-session-guards` 再对两处集成边界（本次覆盖漏洞收口新增）：① 2.9 若落在 `xhs-page-probe.js` / `probe.rs`，与该 change 的 1.2 / 1.3（周期探针平台化、按页面类型分类）读同一份探针输出，字段增删须同时过它们的判据；② 2.11 若走宿主补发回执，与该 change 的 4.1（`src/native-page-engine/browse-session.ts` 逐命令诊断改平台中立）同文件。集成前 `git fetch` + rebase，跑 `cargo test` 与 `npm test` 后再合，在此记录对账结果
- [ ] 6.6 在本清单记录本次「参照书覆盖漏洞」收口的处置结论：就地补任务 = 1.13–1.19 / 2.9–2.15 与新增真机项 5.8–5.10；范围外具名交接 = 4.5（承接方 `restore-native-xiaohongshu-session-guards`）；通电对账 = 4.6。三类都必须有结论，不得留空
