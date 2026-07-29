> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 恢复小红书阻断监测与云端上报

- [x] 1.1 先加失败在先的聚焦测试：小红书 Native 会话在页面探针回 `pageKind='captcha'` 时必须发一次 `risk.captcha_detected{kind:'captcha'}`，回非阻断态后必须发一次配对 `risk.captcha_cleared`（当前两条断言应先红）（参照 src/browse/overlay-report-gate.ts:1-83；缺 detected/cleared 严格配对 + epoch 作废 — 见 oracle.md） <!-- aidcp-edge b57d619 判类/上报/清除三段从 Facebook 专属改为平台无关（observeProbe / reportBlocking）；用例断言 detected 恰 1 条（含完整载荷）、cleared 恰 1 条，重复观测同一 episode 不重复上报 -->
- [x] 1.2 把 `src/native-page-engine/browse-session.ts` 的周期探针启动条件与观测函数的平台判据改成按平台取分类适配，保留 Facebook 分支的判据、延后确认与词库语义逐位不变（参照 src/browse/background-watcher.ts:1-131；缺自走时钟骨架/sticky 容错/翻转一次/节拍可配 — 见 oracle.md） <!-- aidcp-edge b57d619 scheduleProbe/probeOnce/observeProbe 三处 platform!=='facebook' 早退全部移除，改为按平台取一份 BlockingPolicy（classify/reportsUnknownBucket/haltsLocalDispatch/emitsCompanionUi 四格）；既有 browse-session.test.ts 25 条不改一字仍全过 -->
  - 决策记录（2026-07-29）：Facebook 侧刻意**不**加宿主级停手（`haltsLocalDispatch=false`）——它的停手在执行体的逐动作 fail-closed 闸上，宿主再叠一道会改变 Facebook 既有的阻断语义。「按平台取分类适配」这层壳里因此仍有一处按平台分叉，但它是**具名策略字段**而不是散落的条件判断，且 Facebook 行为逐位不变，理由已写进策略常量注释。
- [x] 1.3 实现小红书分类适配：`pageKind='captcha'` → `kind:'captcha'` 即时 fail-closed；`pageKind='login'` → 本地停手等登录、不发账号级阻断上报；其余 → 非阻断（参照 src/browse/overlay-monitor.ts:1-231 的五类优先级 + login-modal-watcher.ts:52-58 的 5 条强短语；登录判据已在 xhs-page-probe.js:12-21，只需接线勿重写 — 见 oracle.md） <!-- aidcp-edge b57d619 登录判据不重写、直接消费 xhs-page-probe.js 已产出的 pageKind；用例断言登录墙路径 sent 为空数组且 observationStatus().blockingKind==='login' -->
- [x] 1.4 加断言：`pageKind='unknown'`（页面类型未识别）MUST NOT 产生任何阻断上报，也不得触发账号风控迁移（参照 oracle.md「不可照抄」第 2 条：旧 unknown 桶判据本身是误报源，声明缺席是正确处置） <!-- aidcp-edge b57d619 XIAOHONGSHU_BLOCKING_POLICY.classify 对 unknown 恒返 'none' 且 reportsUnknownBucket=false；用例断言零上报、blockingKind 仍 'none'、后续 page.scroll 正常派发 -->
- [x] 1.5 加断言：从未上报过的阻断态自愈时不得发孤儿 `cleared`；已上报过的阻断态自愈必须发一次 `cleared`（参照 src/browse/overlay-report-gate.ts:43-63；缺 episode 世代号令在途确认作废 — 见 oracle.md） <!-- aidcp-edge b57d619 上报闸补 blockingEpisode 世代号（离开云端上报态即自增、令在途延后确认作废），清除只在 reportedBlockingKind 存在时发出；login→none 断言零 cleared，captcha→none 断言恰 1 条 -->
- [ ] 1.6 小红书检出阻断后必须本地暂停普通浏览下发，并在清除后恢复；被暂停期间收到的浏览命令回诚实的未开始，不得静默丢弃（参照 src/browse/browse-session.ts:3391-3451；缺等待循环的三个出口，接管须抛出不可只 return，否则闭环死锁 — 见 oracle.md）
  - **偏离说明（2026-07-29）——实现里多一条任务正文没点名的正常路径，需人确认后再勾**：停手闸加了**有界等待预算**（`blockingWaitMs`，默认 15 000ms，可注入；轮询 250ms）。预算内清除就继续派发，等满仍阻断才回诚实未开始（`blocked_by_captcha` / `login_required`，沿用 Facebook 同名原因码）。**理由**：任务同时要求「阻断期间暂停」与「被暂停期间的命令回诚实未开始」，这两条只有加预算才同时成立——无预算则命令**无界挂在闸门里、云端等不到任何回执**，会被看门狗按空闲判死整场会话，那是另一种停摆。落点 `browse-session.ts:879-914`（`waitWhileBlocked`），常量 `DEFAULT_BLOCKING_WAIT_MS=15_000` / `DEFAULT_BLOCKING_POLL_MS=250`。若认为该档位应调整或去掉，只需改 `NativeBrowseSessionOptions.blockingWaitMs`。
  - 已落成部分：`onCloudCommand` 前置停手闸，阻断期间普通浏览命令**零派发**、回诚实未开始，清除后恢复下发；两条用例（captcha 与 login 各一）均断言 `executions.length === 0`。
- [x] 1.7 高危动作提交前补一道即席新鲜复检：小红书的点赞 / 收藏 / 关注 / 评论提交在派发前重探一次页面阻断态，命中验证码即**零派发**、回诚实原因 `blocked_by_captcha`（沿用 Facebook 同名原因码，不新造）；探测**本身失败**按「有挑战」保守拒绝。只读周期观测缓存不够——缓存可能过期约一个节拍，闸门放行到真正点击之间的拟人停顿里弹出的验证码必漏。桶的取舍（只认验证码 / 登录两桶，页面类型未识别 MUST NOT 拒绝）见 design.md D7。验收标准：搬旧测试「点赞命中验证码 → 放弃点击并诚实回执」（参照 native/page-engine/src/facebook/shared.rs:376-412 的动作前闸与 :404 的 fresh 探测；小红书执行入口 engine.rs:598 与 xhs-command-router.js:229/235 的互动分支目前无任何提交前闸 — 见 oracle.md 覆盖漏洞 1） <!-- aidcp-edge b57d619 Rust 侧新增 ensure_xhs_action_gate：四条动作在 evaluate_router 之前重探 probe_page；Captcha→blocked_by_captcha、Login→login_required、Unknown 绝不拒绝、探测失败保守拒绝，一律 EffectPhase::NotStarted 零派发。xhs_session_guard_write_protection.rs 四条用例均断言页面规则表达式一次都没被 evaluate -->
  - 归因损失登记（2026-07-29）：本条的两条要求合起来有**已知的归因精度损失**——「探测本身失败按有挑战保守拒绝」+「原因码沿用同名不新造」意味着「**读不到判定**」会被报成「**命中验证码**」，两态被压成一态。方向是保守的（不会误放行），但云端看到的 `blocked_by_captcha` 里混了一小部分「其实只是探测抖动」。已按指示照做（不新造原因码），取舍写在 `engine.rs` 的 `ensure_xhs_action_gate` 文档注释里，便于日后云端为它准备了归宿再拆开。
  - **残留缺口（2026-07-29）**：`interaction.like_comment`（**评论点赞**）同属高危写动作，但本条正文只点名了点赞 / 收藏 / 关注 / 评论提交四条，本轮按范围只接了这四条 —— **小红书的评论点赞目前仍无提交前阻断复检**。补法是机械动作：在引擎侧受闸动作名映射（`engine.rs` 的 `xhs_gated_action_name`）里补一条 `InteractionLikeComment → "comment_like"`。
- [x] 1.8 把任务 1.6 的停手等待循环写成**三个显式出口**并各加一条回归断言：① 本地停止；② 队列里已到的**会话结束命令必须绕过闸门直接终止会话**（否则登录墙常驻时云端终止不了会话）；③ **任务接管信号到达必须抛出**，令该命令零副作用作废、当场让路，MUST NOT 只返回（只返回会让命令继续对着验证码墙点下去；旧注释点名后果是闭环死锁、整台机器停摆）。现状证据：Native 会话在 `blocked` 时对会话结束命令同样只回 `native_session_quiesced` 的未开始（src/native-page-engine/browse-session.ts:122-126），新增停手闸若沿用同一处理即复现该死锁（参照 src/browse/browse-session.ts:3403-3448 的三出口注释与两条死锁回归测试 — 见 oracle.md 覆盖漏洞 2） <!-- aidcp-edge b57d619 三出口逐条落地：① stopRequested → session_stopped；② session.end 在进闸门之前放行（:228）直接终止会话；③ 任务接管 throw {code:'preempted_by_task'}（:898-901），用例以 assert.rejects 断言抛出且 executions 与 actions 均为空 -->
  - **范围扩充登记（2026-07-29）**：闸门另放行了「**协调器授予的独占任务命令**」（带 `taskId` 的命令）。理由：停手闸若同样拦住独占任务命令，会造出一个**新的死锁**——解除验证码本来就是独占任务（远程协助）干的活，把它拦在「等阻断消失」的闸门里，等的是一个**只有它自己能促成的条件**。任务正文只点名了会话结束命令这一个绕过口，这是就地扩充。已加回归断言 `lets a coordinator-owned task command through`，理由写在 `browse-session.ts:222-228` 的注释里。
  - **残留缺口（2026-07-29）**：会话启动时的**首次扫描滚动不经停手闸**——它不走云端命令入口、也没有可回执的信封。后果是会话启动瞬间若正停在登录墙上会多滚一次 feed；**首个周期探针（默认 2s 后）之后的所有命令都受闸**。本轮未改（改它需要给启动路径造一个假信封或改回执面，收益不抵风险）。
- [ ] 1.9 把周期阻断观测做成有生命周期托管的观测体，而不是一个裸定时器。四项验收：① 执行器连接进入不可恢复终态即停掉全部周期观测、重连后整批重启且启动幂等；② 补「上次成功探测距今多久」的存活度量，使「持续探测失败」与「确实没情况」在外部可区分（MUST NOT 把探测不了当成没情况）；③ 探测节拍可注入 / 可配（现写死 2 秒，src/native-page-engine/browse-session.ts:459-464；旧骨架默认 1 秒且可注入），并显式选定探测失败的容错档（保持上一状态 / 回落初始态）写进断言；④ 待机或启动即暂停时「已装配但暂不启动」留一条可观测记录。现状证据：连接不可恢复只触发执行器隔离并请求冷待机（src/main.ts:1542-1548 → :1500-1511），而冷待机在复用外部浏览器或有活跃租约时直接拒绝（:1317-1323），此时探针不被停、继续对死连接空轮询并每拍打一行失败日志到进程退出（参照 src/browse/background-watcher.ts:34/38/56-58 与 src/browse/watcher-supervisor.ts — 见 oracle.md 覆盖漏洞 3）
  - **偏离说明（2026-07-29）——② ③ ④ 已落，① 只做了会话侧一半、宿主侧未接线**：
    - ② 已落：`observationStatus()` 暴露 `msSinceLastOkProbe`（从未成功过时为 `undefined`）与 `consecutiveProbeFailures`；用例 `liveness separates cannot-probe from nothing-to-see` 断言失败计数 > 0、`msSinceLastOkProbe === undefined`、`blockingKind` 仍为 `captcha`。
    - ③ 已落：节拍改为 `probeIntervalMs` 可注入 + `AIDCP_NATIVE_OBSERVATION_MS` 可配（默认仍 2 000ms，Facebook 行为不变）；容错档**显式选定为 sticky**（保持上一状态、绝不翻转），且只在进入失败态记一行。
    - ④ 已落：blocked / suspended 时留 `observation_deferred` 一条「已装配但暂不启动」记录，有独立用例。
    - ① **只有会话侧那一半**：`suspendObservation()` / `resumeObservation()` 已实现且**两端幂等**（重复调用各只 1 行诊断，有回归断言）。**订阅「执行器连接不可恢复 / 重连」的另一半在宿主装配文件 `src/main.ts`，本轮未接**——落点是 `src/main.ts:1542` 附近的连接不可恢复订阅处调 `browse.suspendObservation('cdp_unrecoverable')`、重连处调 `browse.resumeObservation()`。**未接线前，连接死掉后探针仍会按节拍空轮询**（失败只记一行、不再刷屏，但不会自己停）。

## 2. aidcp-edge — 恢复小红书不可逆写入的提交窗口

- [x] 2.1 加失败在先的测试：小红书评论提交、通知评论栏消费、通知点赞/关注栏消费、发布提交四处在写入派发前必须各请求一次提交窗口。标签与预算沿用迁前实测值（已在 `317cd47^` 逐处坐实，**不得照抄 Facebook 的值**）：`xhs_comment_submit` 4 000ms、`xhs_notification_comments` 20 000ms、`xhs_notification_likes` / `xhs_notification_follows` 20 000ms、`xhs_publish_submit` **15 000ms**（不是 20 000ms——20 000ms 是 Facebook 的 `fb_publish_submit`）。验收标准：四处各有一条断言比对标签字符串与预算数值（参照 src/execution/commit-window.ts:1-75 与四处开窗点 browse-session.ts:2583/3109/3163 + publish-command-handlers.ts:1372 与 :1388（发布是两条开窗点）— 见 oracle.md） <!-- aidcp-edge b57d619 native/page-engine/src/commit_window.rs 新增 xiaohongshu_commit_window() 契约表（读命令与可重放导航回 None）；Rust 用例五条各一对 label/budget 断言，另加 assert_ne!(publish.budget_ms, 20_000) 钉死「发布提交不得照抄 Facebook 的 20s」 -->
  - **跨提交依赖已解除（2026-07-29）**：宿主把提交窗口预算做成了「**按标签发放**」的单一事实源，**未列入的标签会被判契约违规并否决窗口**——若只落 b57d619，小红书的评论提交、三条通知分类栏、发布提交会**全部拒发**（诚实的未开始，但功能等于停摆）。五条标签已在同批的 `aidcp-edge 74eaf41` 加进宿主事实源 `src/native-page-engine/client.ts` 的 `NativeCommitWindowLabel` 与 `NATIVE_COMMIT_WINDOW_BUDGETS`（数值与本条完全一致），机械对账用例同批扩到**同时读两份引擎源**（`facebook/capability.rs` + `commit_window.rs`）。**这两个提交必须同批部署，单独回滚任一个都会让小红书写入停摆。**
- [x] 2.2 让 `native/page-engine/src/engine.rs` 的小红书执行入口接收提交窗口请求器，并在上述四处写入的正前方开窗、终态关窗（参照 engine.rs:598 缺 `commit_windows` 形参；真实点击在不许改的 xhs-command-router.js:224/236/272，故只能在 `evaluate_router` 之前开窗、预算须覆盖 router 内后置校验 — 见 oracle.md） <!-- aidcp-edge b57d619 execute_xhs_command_once 签名补 commit_windows: &CommitWindowRequester（engine.rs:567 调用处一并传下），在 evaluate_router 之前开窗、粒度为整条 router 调用、预算覆盖规则内部后置校验；关窗在终态由宿主传输层负责。用例断言收到的窗口请求恰为 ('xhs_comment_submit', 4000)、且窗口获准后才出现 interaction_comment 的页面规则调用 -->
- [x] 2.3 把 `src/native-page-engine/browse-session.ts:237-239` 的窗口处理器注入从「仅 Facebook」改为平台无关；确认发布侧 `src/native-page-engine/publish.ts` 的处理器注入被真正取用（参照 publish.ts:56-57 已无条件传入但 Rust `publish_submit` 走 evaluate_router、从不请求 ⇒ 处理器空转 — 见 oracle.md） <!-- aidcp-edge b57d619 窗口处理器注入去掉 platform==='facebook' 条件；publish.ts 补上「不得加平台条件」的约束注释，该处理器现因 Rust 侧 publish_submit 真发起请求而不再空转。两条用例：浏览写入 handler 非 undefined 且窗口内 coordinator 读到占用中 + 剩余 4000；发布 label=xhs_publish_submit、remaining=15000 -->
- [x] 2.4 加断言：窗口请求被拒或不可得时，写入 MUST NOT 派发，回执标未开始；协调器在窗口内对抢占回「窗口占用中 + 剩余预算」（参照 native/page-engine/src/commit_window.rs:107-112 的 `CommitWindowUnavailable`；小红书现为「无声照写」 — 见 oracle.md） <!-- aidcp-edge b57d619 Rust 用例 a_refused_commit_window_dispatches_nothing_and_terminates_as_not_started（error.code==CommitWindowUnavailable、phase==NotStarted、无任何 Input.* 且无 interaction_comment 页面规则调用）+ TS 用例「an unavailable commit window leaves the Xiaohongshu write not started」 -->
- [x] 2.5 加断言：窗口在终态（成功 / 失败 / 超预算）后必须关闭，不得泄漏成永久占用（参照 src/execution/commit-window.ts 两条安全设计：时基兜底自动过期 + 世代守卫防误关 — 见 oracle.md） <!-- aidcp-edge b57d619 用例「a stuck commit window expires on the clock and a late disposer never closes a newer one」覆盖两条安全设计；另在浏览/发布两条用例末尾各断言 guard.isOpen()===false -->

## 3. aidcp-edge — 验证码协助键入取证诚实化

- [ ] 3.1 加失败在先的测试：下发了文本但 Native 回执未携带任何键入取证时，宿主 MUST NOT 标 `inputMode:'click_type'`（当前实现按请求推断，此断言应先红）（参照 src/main.ts:1015 按 payload 推断 ↔ 云端探测器 aidcp-cloud/src/comm/captcha-assist.ts:255-262 — 见 oracle.md）
- [ ] 3.2 给 Native 验证码回执补结构化键入取证：焦点分级、清空三态、实际派发字符数、回读三态、是否已提交；失败路径按 `engine.rs` 既有结构化原因逐段映射（参照 src/browse/captcha-assist.ts:445-659；缺 focus/focusTag/cleared/typed/verified/submitted 六字段与「type→read→submit 顺序反了必假阴性」 — 见 oracle.md）
- [ ] 3.3 宿主把取证逐字段透传进 `captcha.assist.click_result` 的既有可选字段；`inputMode` 只在确有字符派发时为 `click_type`（参照 src/main.ts:1007-1015；`replayMode` 亦写死 synthetic，但轨迹回放不在本 change 范围 — 见 oracle.md 覆盖漏洞 4）
- [ ] 3.4 加边到边逐字段往返断言（边缘打包 → 云端解析 → panel HTTP 边界透传），确认没有字段在任一跳被丢（参照 oracle.md 的旧回执字段集；`typeReport` 绝不含答案本身）
- [ ] 3.5 加断言：中途被抢占或超预算时，取证的字符数为实际派发数、不得回退到请求文本长度，且不得执行提交（参照 src/browse/captcha-assist.ts:445-659；`typed` 须由闭包逐字更新——抛出时派发函数内部计数丢失，只有闭包值是真实数 — 见 oracle.md）
- [ ] 3.6 加断言：云端「下发了文本却未键入」的探测器在取证缺席时会触发，在取证齐备且确有派发时不触发（参照 aidcp-cloud/src/comm/captcha-assist.ts:255-262 的 textNotExecuted：textLen>0 且 inputMode≠click_type — 见 oracle.md）
  - **本轮未做（2026-07-29）**：整节主要落点是 `src/main.ts` 的回执打包与 `native/page-engine/src/engine.rs` 的验证码回执壳字段扩容，两处本轮均在其他并行流的单写区，未触碰。归后续波次；接手方需同时拿到这两个文件才能一次做完（只改宿主会把「取证缺席」当成「取证为零」）。

## 4. aidcp-edge — 排障证据平台对称

- [x] 4.1 把 `browse-session.ts:349-357` 的逐命令回执诊断改为平台中立，输出动作名、成功与否、效果相位、原因码，且原因码继续走既有的诊断 token 白名单收敛（参照旧全链诊断 src/browse/browse-session.ts:3088/3139/3170；缺「未命中 tab 诚实 no_target、绝不无条件报 viewed」这层证据 — 见 oracle.md） <!-- aidcp-edge b57d619 四元组（action/ok/effectPhase/reason）从 platform==='facebook' 判据里取出改为平台中立；另补 command_outcome 结构化行覆盖「终局不是动作回执」的命令（滚动、开帖）。用例逐字比对两条 action.completed 行并断言 command_outcome 依次为 page_scroll/note_open/interaction_like/navigation_back -->
- [x] 4.2 为每个 Native 浏览平台补会话级诊断：会话就绪、阻断检出 / 清除、为任务让位与恢复、终止原因（参照 src/browse/browse-session.ts:3444 与 :3438「出现/消失各只记一次」；MUST 走结构化行，壳侧兜底正则只认「弹窗/暂停操作」曾让 FB 阻断态恒绿 — 见 oracle.md） <!-- aidcp-edge b57d619 补平台中立结构化行 `[native-page] session.event event=… platform=… k=v`：session_ready / blocking_state / blocking_detected / blocking_cleared / blocking_halt_enter / blocking_halt_exit / task_yield / task_resume / session_stopped / command_outcome / command_failed / observation_*，全部字段过 token 白名单；用例断言六个生命周期事件存在且日志中不含「暂停操作」这类兜底正则依赖的措辞 -->
- [x] 4.3 加断言：一次小红书浏览闭环（滚动 → 开帖 → 互动 → 返回）在日志里逐命令留有回执证据；诊断不得携带页面正文、凭据或选择器（参照现成模板 test/native-page-engine/browse-session.test.ts:157，去掉平台条件即为小红书同款契约） <!-- aidcp-edge b57d619 故意把 '.like-wrapper missing at https://…?xsec_token=secret' 塞进原因码，验证被收敛成 non_token_reason；断言 logs 中不含 'https://'、'xsec_token'、'like-wrapper' -->
- [x] 4.4 明确不为小红书补在场感 / 陪伴界面事件（非本次回归）。验收标准：一条断言固定「小红书会话产出生命周期诊断但不产出陪伴界面事件」这一预期状态，断言注释里写明这是产品范围而非可观测性缺陷，防后续误当缺口重做（参照 oracle.md：旧实现两侧都靠日志措辞点亮运行态，故此处 MUST NOT 退回措辞匹配） <!-- aidcp-edge b57d619 emitsCompanionUi=false 在 BlockingPolicy 里具名；用例末段断言无任何 '[ui-event] ' 行，策略常量与断言两处各有注释说明「防后续误当缺口重做」 -->

## 5. aidcp-edge — 恢复运行期身份持续校验

- [ ] 5.1 加失败在先的测试：长跑会话在两次启动 / 唤醒之间发生换号或掉登录时，必须被周期校验发现并退回无身份态（参照 src/browse/identity-watcher.ts:1-162；缺 30s 节拍 + `AIDCP_IDENTITY_CHECK_MS`/`AIDCP_IDENTITY_FAIL_THRESHOLD` 两旋钮 + 连续 2 次防抖 — 见 oracle.md）
- [ ] 5.2 把身份重读挂到与阻断观测同一条周期通路上，沿用既有分域判据（消费端读稳定 id / 创作子域用登录门禁 / 其它域判无法确认）（参照 identity-watcher.ts 的分域四态与正向登出探针；缺「只读不导航」与登录浮层作第二判据的接线 — 见 oracle.md）
- [ ] 5.3 加断言：判「无法确认」的那一轮不计入失效防抖计数、不判失效也不判健康，且留下可观测日志（参照 identity-watcher.ts 的 unknown 跳过分支与「创作发布页穿插不得凑够阈值」的跨页计数污染用例 — 见 oracle.md）
- [ ] 5.4 加断言：判失效只 emit 一次转移，退回无身份态前先诚实回执在途发布（参照 `317cd47^:src/main.ts:1035-1102` 的重立链；在途发布须在关连接之前判失败，后半段 8 步本 change 未覆盖 — 见 oracle.md 覆盖漏洞 5）
- [ ] 5.5 补齐身份重立链的后半段（5.1–5.4 做完只能「发现」失效、不能「恢复」）：停全部周期观测 → 停浏览 → **在途发布诚实判失败（MUST 在关连接之前，否则失败回执发不出去）** → 断开云端 → **先导航回消费端首页再读身份** → 读不出即停在无身份态、**绝不回落默认账号（红线）** → 按新 id 换云端会话并重连 → 重设基线 → 重启周期观测与浏览。其中「重连后重注入连接级节奏快照」这一步归属未定，见任务 5.6，本任务先不实现该步、也不得静默跳过（参照 `317cd47^:src/main.ts:1035-1090` 的逐步顺序与红线注释；已合并要求「重新确立身份 MUST 先回到可读身份的页面再判定」与「退回无身份态断连前 MUST 先诚实回执在途发布」已在册，本任务是把它们在 Native 宿主上真正接线 — 见 oracle.md 覆盖漏洞 5）
  - **本轮未做（2026-07-29）**：5.1–5.5 的落点是 `src/main.ts` 的周期校验体与身份重立链，本轮该文件归另一条并行流（只做了第 6 节的死码清除），未触碰身份相关代码。归后续波次。注：会话侧已具备可挂载点——1.9 落成的 `suspendObservation()` / `resumeObservation()` 与 `observationStatus()` 可直接被身份重立链的「停全部周期观测 / 重启周期观测」两步复用。
- [ ] 5.6 **【阻塞 · 待人裁定】** 身份翻转 / 重连后「重注入连接级节奏快照」这一步在 Native 形态下的归属未定：Native 会话的同名接收点是空实现且注释写明节奏归云端（src/native-page-engine/browse-session.ts:213-218），会话对节奏更新命令直接返回（:121）。未裁定前任务 5.5 的该步既无法实现也无法声明不做。裁定项与两种走法各自的后果见 design.md「待裁定」§1
  - 本轮未开工（2026-07-29）：按「未裁定前既无法实现也无法声明不做」的约定，本轮不动。**需用户在走法甲（Native 会话恢复真接收点）与走法乙（正式声明不再需要）之间裁定。** 同一裁定项在第 6 节 6.1 的对账表第 14 行也被登记为唯一一处「连接级节奏快照注入无落点」的缺口。

## 6. aidcp-edge — 清除恒假短路的宿主装配

- [x] 6.1 逐条对账 `src/main.ts:1043-1213` 块内的每项能力（浮层监测、上报闸、看护托管与 CDP 生命周期挂钩、评论 / 加群执行器与处理器、Facebook 会话装配、页面命令处理器注册），每条给出「已有 Native 归属（落点）」或「已登记缺口（去处）」结论，写进本清单（参照 oracle.md 末条：已列出 6 项「无对应物」+ 6 项「已有 Native 归属」，可直接当对账底稿） <!-- aidcp-edge 813ff7c 逐条复读块内 18 项能力完成对账；oracle 末条 6+6 底稿在代码里全部坐实，另补出底稿未单列的 4 项 -->

  **删除对象**：`src/main.ts` 原 1041–1213（自述注释 2 行 + `if (false && platformDriver.runtimeKind === 'browser')` 起至块尾，共 173 行）与原 88–105 的 18 行影子声明。

  **对账表（18 项；结论只有两类：已有 Native 归属＝写落点，已登记缺口＝写去处）**

  | # | 块内能力 | 结论 | 落点 / 去处 |
  |---|---|---|---|
  | 1 | 平台分叉闸 + 重复的「不支持 browse」告警 | 已有 Native 归属 | `main.ts` 的 Native 会话装配按 `platform === 'facebook' ? 'facebook' : 'xiaohongshu'` 取值；告警只保留 Native 那一条（删块后重复告警一并消失） |
  | 2 | 浮层监测体创建 | 已有 Native 归属 | native-page-engine 浏览会话的周期页面探针 |
  | 3 | 确认窗环境变量 + 默认 2000ms | 已有 Native 归属 | 同上会话的 `overlayConfirmMs`（同一环境变量、同一默认值） |
  | 4 | 结构化现场快照 | **已登记缺口** | 见 6.6 的三栏登记；本 change 不承接 |
  | 5 | 同源证据文本回填 | 已有 Native 归属 | FB 路由的阻断探针直出阻断文案，无需宿主回填 |
  | 6 | 阻断检出上报 | 已有 Native 归属（原仅 Facebook） | 同上会话的上报路径；小红书侧已由本 change §1.1/1.3 承接 |
  | 7 | 阻断清除上报 | 已有 Native 归属（原仅 Facebook） | 同上；小红书侧已由本 change §1.5 承接 |
  | 8 | 结构化「需要处理 / 已恢复」客户端事件 | 已有 Native 归属（仅 Facebook） | 同上会话的两处 UI 事件；小红书侧是**产品范围内的有意缺席**（本文件 4.4 已定，MUST NOT 当缺口重做） |
  | 9 | 上报闸：unknown 延后确认 + detected/cleared 严格配对 | 部分归属 + 缺口已消除 | 延后确认与配对已在 Native 会话的等价物里；**episode 世代号**（离开阻断态即作废在途确认）起草期无对应物，已由本 change 1.5 补上 |
  | 10 | 看护托管 + 连接不可恢复/重连联动 + 冷待机/暂停启动闸 | **部分归属 + 已登记缺口** | 会话侧的停 / 重启 / 存活度量 / 待机记录已由 1.9 的 ②③④ 落成；**订阅连接不可恢复 / 重连的宿主侧那一半仍未接线**，去处 = 本文件 1.9 ①（落点 `src/main.ts:1542` 附近） |
  | 11 | 评论执行器的提交窗口 | 已有 Native 归属 | Rust `facebook/capability.rs` 的 `fb_comment_enter` = 20 000ms |
  | 12 | 加群执行器的提交窗口 | 已有 Native 归属 | Rust `facebook/capability.rs` 的 `fb_join_click` = 18 500ms |
  | 13 | 评论 / 加群处理器装配 | 已有 Native 归属 | Native 会话内的 Facebook 命令分支（含各自超时预算） |
  | 14 | 会话装配的三个参数：起始地址 / 启动号 / 降速档 | 两项归属 + **一项已登记缺口** | 启动号仍由 `main.ts` 传给 Native 会话；起始地址由 `main.ts` 的浏览器启动参数承接（同一环境变量）；**连接级节奏快照注入无落点**（Native 的接收点是空实现），去处 = design.md「待裁定」§1，须由人先裁定走法甲 / 乙（即本文件 5.6） |
  | 15 | 命令路由 + 任务租约准入与续租 | 已有 Native 归属 | `main.ts` 的 Native 命令路由（逐字同款闸，另多一条 pacing 命令豁免） |
  | 16 | 注册时的交接收敛 | 已有 Native 归属 | `main.ts` 同段，语义一致（有界、诚实抛出、catch 只为不炸装配） |
  | 17 | 启动闸（冷待机 / 暂停）+ 注册日志 | 已有 Native 归属 | `main.ts` 同段 |
  | 18 | 上报时的地址兜底读取 | 已有 Native 归属 | 页面探针回传来源与路径，宿主不再自行读页面 |

  **底稿差异登记（2026-07-29）**：`oracle.md` 末条把恒假块概括为 6 项无对应物 + 6 项已有归属（共 12 项），实测块内可分出的能力条目是 **18 项**。底稿本身没有错（它列的 12 条逐条成立），但**直接照抄会漏掉 4 项**未被列举的：平台分叉闸、评论 / 加群处理器装配、起始地址注入、阻断上报时的地址兜底读取。这四项复读后都归到「已有 Native 归属」，无新增缺口。

  **机制性结论（本节存在的理由）**：这 173 行 + 18 行影子声明构成「编译期不可达 + 影子声明」的保留形态——类型穷举看不见、生产剪枝挡在产物外、单测不覆盖，于是能力整批静默消失且无一道闸报警。同一机制已付过一次代价（块内的 Facebook 软限流上报直到 07-26 才在 Native 会话补回）；本次又抓到第二次代价，见 6.3 下方的夹具订正②。

- [x] 6.2 删除该恒假块与 `src/main.ts:88-105` 的类型影子声明（含末条跨行的 `captureBlockingOverlaySnapshot`）；确认删除后 typecheck、剪枝与全量测试仍通过（参照 src/main.ts:88-103 实测 16 行影子声明，块首 :1043 `if (false && …)`、块尾 :1213 — 见 oracle.md） <!-- aidcp-edge 813ff7c 删恒假块（原 1041-1213 共 173 行）与文件头 18 行影子声明（原 88-105，含跨 104-105 两行的 captureBlockingOverlaySnapshot），连带删只为该块存在的 import type { BlockingOverlaySnapshot }（原 77）与 let overlayMonitor（原 495），并改写 main.ts:462 那条描述旧平台分叉的过期注释 -->
  - 验证（2026-07-29）：`npm run typecheck` 通过（0 error）；`npm run build:dist` 成功（`reachable=77 removed=68 legacy_page_rules=absent page_rule_fragments_guarded=11 source_maps=absent`）；`npm test` 全量 2676 例 / 2675 绿 / 0 红 / 1 跳过。删除后全仓 grep 无 `if (false`、无 `declare ` 于 `src/main.ts`、无 `createOverlayMonitor`。
  - **夹具订正①（2026-07-29）**：`test/platform/driver.test.ts:140` 曾断言「小红书驱动必须**引用**退役的浮层监测体模块」（`assert.match(driverSource, /..\/browse\/overlay-monitor/)`）——**那是切换前的接线**。阻断观测已移到执行体侧的页面探针上，工厂成员随 6.5 从平台接口删除；照这条断言去改实现会把退役模块**重新挂回来、并顺带把它拖进生产产物**。已按事实改为 `assert.doesNotMatch`（同用例其余两条仍有效的断言保留）。在注释里塞一段模块路径去骗过正则是**假绿**，明确不做。
- [x] 6.3 加源码级检查：禁止「静态恒假的装配入口」与「为已剪枝模块造的 `declare const` 影子声明」这一组合再次出现，检查失败必须明确指出文件与行（参照 oracle.md「机制性问题」：typecheck 穷举不到、剪枝挡在产物外、单测不覆盖 ⇒ 能力整批静默消失，已付过一次代价 `54ae5b2`） <!-- aidcp-edge 813ff7c 新建常驻闸 test/native-page-engine/host-assembly-guard.test.ts：扫 src/ 全部 .ts，报两类违规（①条件首操作数为假值字面量或与假值字面量做合取，覆盖 if/while/else if、false/0/!true/!1；②declare const/let/var/function/class 且类型取自仓内相对路径 import()，支持跨行、向后有界并行 6 行），违规带 file+line+snippet。13/13 通过 -->
  - 可证伪验证（2026-07-29）：按 `artifact-gates.test.ts` 的纪律做了**植入验证**——临时目录植入恒假块 → 点名 `nested/assembly.ts:2`；植入单行与跨行影子声明 → 点名 `main.ts:1`（跨行时点 `declare` 那一行而非续行）；另有反向断言证明注释里的历史形状、`declare global`、`if (a===0)` / `if (a && arr[0])` 不误报。
  - **夹具订正②（2026-07-29）——本节复盘机制的第二实例，方向更坏**：`test/electron/control-plane-slot-decoupling.test.ts:69` 数 `src/main.ts` 里浏览器缺席入口守卫的出现次数并要求**等于 2**，失败文案自称「发布与浏览共用两条 Native-only 入口；被移除的 JavaScript 页面路由不得再出现」。实测这个前提是反的：HEAD 上那 2 次里**有 1 次就落在恒假块内的 JavaScript Facebook 路由里**（原 `main.ts:1184`），另 1 次是 Native 路由（原 `:1230`）；发布链路根本不走这个闸。**一条本意是「被移除的路由不得再出现」的否定式闸，被它要禁止的那段死码喂成了绿。** 若照它的期望值去「修实现」，等于把死码再种回去。已按事实改期望值为 1、并改写失败文案为「唯一活入口是 Native 页面命令路由；出现第二次即退役路由复活」。
- [x] 6.4 确认删除后仓内不再有仅被恒假块引用的孤儿模块；对确已无人引用的退役监测体给出保留或删除的结论并写明理由。**分类先做实，别按「都是孤儿」一刀切**（HEAD `9cd7691` 实测）：`IdentityWatcher` / `CdpLoginModalWatcher` 在 `src/` 里除自身外零引用；`WatcherSupervisor` / `createOverlayReportGate` 只被恒假块与影子声明引用；而 `src/browse/overlay-monitor.ts` 的 `OverlayMonitor` **仍被活着的代码引用**——`PlatformDriver` 接口声明 `createOverlayMonitor`（`src/platform/driver.ts:57`）、`src/xhs/driver.ts:25` 仍 `new CdpOverlayMonitor(cdp)`、十余个 `src/facebook/*.ts` 以类型形式依赖它，MUST NOT 顺手删除。验收标准：逐模块给出「零引用 / 仅恒假块引用 / 仍被活代码引用」三分类结论 <!-- aidcp-edge 813ff7c 符号级普查（grep 全 src/ + test/ + scripts/）完成三分类；两条测试把「本轮不删退役监测体」的决定钉住 -->

  **三分类结论（本轮只登记、一律不删除）**：
  - **零引用**（`src/` 内除自身源文件外）：`IdentityWatcher`（`src/browse/identity-watcher.ts`）、`CdpLoginModalWatcher`（`src/browse/login-modal-watcher.ts` 的类）。两者都只被 `src/browse/index.ts` 桶转出 + 自有测试引用。**注意一处细节**：login-modal-watcher 的**接口**仍被退役的 `src/browse/browse-session.ts` 以类型引用，**删类不等于删文件**。
  - **仅被恒假块与影子声明引用**：`WatcherSupervisor`（`src/browse/watcher-supervisor.ts`）、`createOverlayReportGate`（`src/browse/overlay-report-gate.ts`）。删块后二者在 `src/` 内只剩桶转出（overlay-report-gate 另有自有测试）。
  - **仍被活代码引用（MUST NOT 顺手删）**：`src/browse/overlay-monitor.ts`（`OverlayMonitor` / `OverlayKind` / `BlockingOverlaySnapshot` 被十余个 `src/facebook/*.ts` + `src/browse/browse-session.ts` + `src/browse/captcha-assist.ts` 以类型依赖）、`src/browse/notification-monitor.ts`（`src/browse/browse-session.ts` 取三段未读读取 JS，另有 `scripts/notification-clear-probe.ts`）、`src/browse/background-watcher.ts`（被 overlay-monitor 与 notification-monitor 继承）、`src/browse/captcha-assist.ts`（协助链路的参照书，本文件 §3 正据其复原取证字段）。

  **保留决定与理由**：本轮六个模块（`overlay-report-gate.ts`、`background-watcher.ts`、`watcher-supervisor.ts`、`identity-watcher.ts`、`notification-monitor.ts`、`captcha-assist.ts`，外加必须保留的 `overlay-monitor.ts`）**一律不删**——并行流与后续波次正拿它们当参照书逐条复原行为（本文件 §1 的自走时钟骨架 / sticky 容错 / 世代号、§3 的取证六字段、§5 的分域身份判据都直接引它们的行号）；`notification-monitor.ts` 已被另一个 change 具名标为「**要的是恢复而不是清理**，按孤儿删除则通知类修复永久不通电」。删除时机应等这批 change 落完，且要单独裁定，不能作为本节的顺手动作。已用两条测试钉住（六个文件仍在 + overlay-monitor 仍有活引用），避免后续清理波次把它们静默扫掉。

- [x] 6.5 单独裁定 `PlatformDriver.createOverlayMonitor` 这个**无调用点的工厂成员**（全仓无 `platformDriver.createOverlayMonitor(...)` 调用）：或接进本 change 恢复的小红书阻断观测通路、或从接口上删除并同步两个 driver 实现，MUST NOT 原样留成「接口上有、没人调」的第二种无信号保留。验收标准：接口与两处实现的最终形态在测试里被断言（参照 src/browse/overlay-monitor.ts:472-498 的 `CdpOverlayMonitor`；旧 `probeNow()` 是高危动作提交前 fail-closed 用的即席复检句柄，Native 把它内化进 Rust 动作闸后宿主侧再无可调句柄 — 见 oracle.md） <!-- aidcp-edge 813ff7c 裁定＝从契约上删除：platform/driver.ts 删成员与类型导入（补写删除依据注释）、xhs/driver.ts 删工厂与值导入、facebook/driver.ts 删 native-only 桩；三条断言钉最终形态（源码级 + 运行时 'createOverlayMonitor' in driver === false + 全仓无复活） -->
  - 裁定依据逐条坐实（2026-07-29）：① 全仓**零调用点**（唯一构造点在已删的恒假块里，且用的是直接构造而非工厂）；② 「接进小红书阻断观测通路」一路**不成立**——小红书阻断观测已由本 change §1 在执行体侧走页面探针重建，**页面判据必须留在编码后的 Native 产物内**（design.md D1 已明否），「接进去」会把可读判据搬回宿主 TypeScript、与防反编译迁移动机直接冲突；③ 原样保留即任务点名禁止的第二种无信号保留。
  - **附带收益（实打实、已用 HEAD 快照对照实测）**：因为 `src/xhs/driver.ts` 用的是**值导入**，四个已退役的宿主侧监测体模块一直落在**生产产物的可达图**里 —— 生产可达模块 **81 → 77**，差集恰为 `browse/overlay-monitor.js`、`browse/login-modal-watcher.js`、`browse/background-watcher.js`、`flows/anchors.js`，新增为空。**这类模块正是防反编译迁移要从明文产物里清走的东西**——留着等于把可读的页面判据继续随安装包发给运营机。
  - 顺带删除的第二个无信号哨兵：`src/facebook/driver.ts` 里那个 native-only 的浮层监测体桩，注释自称是防止「未来某个泛化调用悄悄恢复 JS CDP 逻辑」的哨兵，但**全仓从来没有调用点**——一个永不被调用的哨兵不产生任何信号，只会让读代码的人误以为这里有防线。已连同接口成员一并删除，删除依据写进 `src/platform/driver.ts` 的接口注释，避免下一个人「恢复」它。
  - **同族无信号声明，超出本节范围、需另立 change 裁定（2026-07-29 登记）**：平台能力位 `overlay` 在边缘仓内**没有任何消费方**——`src/xhs/driver.ts:16`、`src/facebook/driver.ts:33`、`src/wechat-channels/driver.ts:26,35` 三个驱动都声明它，但全仓**没有一处判据读它**（无 `capabilities.includes('overlay')` 之类）。它与本条删掉的工厂成员是同一族的无信号声明，**但它会进云端注册与握手载荷，改动有协议侧外溢，不能顺手删**。需由做**能力位对账**的 change 单独裁定：要么接上判据，要么连同两侧一起下线。
- [x] 6.6 结构化现场快照的登记条目 MUST 写明下游影响，不得只记一句「缺快照」：Native 阻断上报把候选证据写死为空数组、只带一段截断到 1000 字的文本（src/native-page-engine/browse-session.ts:558-567 与 :506），下游后果是云端与运营分诊只能靠这一段文本给阻断命名——没有主候选的 DOM 特征 / 选择器路径 / 位置尺寸 / 层级与透明度 / 内嵌页地址 / 有无关闭控件 / 命中理由，也没有备选候选可看；且已合并要求「判为阻断态的遮罩上报必须携带非空证据文案」在文本为空时会让真限流只到降速档而非刹车档。验收标准：6.1 的对账表里这条落成「已登记缺口 + 下游影响 + 去处」三栏，MUST NOT 写成「已由 Native 承接」（参照 oracle.md 覆盖漏洞 6 与末条「无对应物 1」） <!-- aidcp-edge 813ff7c 三栏登记如下；已在 browse-session.ts 坐实 candidates 恒为 []、blockingText 截断到 1000 字 -->

  **三栏登记（MUST NOT 写成「已由 Native 承接」）**：
  - **已登记缺口**：结构化现场快照的**字段集**。旧实现采集主候选的 DOM 特征（标签 / id / class / role / aria-modal / 选择器路径 / 位置尺寸 / position+zIndex+opacity / 内嵌页地址 / 有无关闭控件 / 命中理由）加最多 3 个备选候选；Native 侧的阻断上报把**候选证据写死为空数组**，只带一段**截断到 1000 字**的阻断文案。
  - **下游影响**：云端与运营分诊只能靠这一段文本给阻断命名——没有主候选的 DOM 特征、没有选择器路径、没有位置尺寸、没有层级与透明度、没有内嵌页地址、没有关闭控件有无、没有命中理由，也没有任何备选候选可看；且已合并要求「判为阻断态的遮罩上报必须携带非空证据文案」在文本为空时会让**真限流只到降速档而非刹车档**（即一次真实限流被降格处理）。
  - **去处**：**不由本 change 承接**（oracle.md 覆盖漏洞 6 明示「按 6.1 登记即可，不扩范围」）。需**新立 change** 把字段集补回执行体侧的阻断探针；现成的字段级契约是 `test/browse/overlay-monitor.test.ts` 里快照采集与快照 JS 构造那两条，可直接作为验收依据。

## 7. 验证与验收

- [ ] 7.1 运行聚焦测试：小红书阻断上报、提交窗口、键入取证、诊断对称、身份校验五组
  - 阶段性记录（2026-07-29）：**五组里三组已有并全绿**——阻断上报 + 诊断对称（`test/native-page-engine/xhs-session-guard-blocking.test.ts`，14 条）、提交窗口（`xhs-session-guard-commit-window.test.ts` 4 条 + Rust `xhs_session_guard_write_protection.rs` 7 条）；第 6 节另有 `host-assembly-guard.test.ts` 13 条全过。**键入取证（§3）与身份校验（§5）两组本轮未实现，故无测试可跑**。本条待那两节落地后再勾。
- [ ] 7.2 运行 `cd ../aidcp-edge && npm run test:acceptance`，确认 `AC-PROTO-*` / `AC-RISK-*` 全过，两份 `protocol.ts` 消息总数不变
  - 阶段性记录（2026-07-29，worktree `native-migration-repair` @ `74eaf41`）：**30/30 全过**（1 条 gated 跳过 = 需真机的 E2E），`AC-PROTO-*` 全过、两份 `protocol.ts` 消息总数不变（本轮零协议改动）。change 未收口，本条不勾。
- [ ] 7.3 运行 `cd ../aidcp-edge && npm test` 与 `npm run typecheck`
  - 阶段性记录（2026-07-29）：`npm test` **2676 例 / 2675 绿 / 0 红 / 1 跳过**；`npm run typecheck` **通过**；另 `npm run build:dist` **通过**（`reachable=77 removed=68 legacy_page_rules=absent page_rule_fragments_guarded=11 source_maps=absent`）。change 未收口，本条不勾。
- [ ] 7.4 运行 Rust 侧 `cargo fmt --check`、`cargo clippy -- -D warnings`、`cargo test`
  - 阶段性记录（2026-07-29）：`npm run gate:native` **通过**（fmt + clippy `-D warnings` + test），toolchain `1.97.1-aarch64-apple-darwin`。change 未收口，本条不勾。
- [ ] 7.5 运行 `openspec validate restore-native-xiaohongshu-session-guards --strict`
  - 阶段性记录（2026-07-29）：已运行，输出 `Change 'restore-native-xiaohongshu-session-guards' is valid`。change 未收口（§3、§5 未做，1.6 / 1.9 有偏离），本条留到收口时勾。
- [x] 7.6 记录 edge 与控制仓的提交 sha、验证证据、偏离说明与热点文件重叠情况；明确写下未执行的动作（未出安装包、未部署、未做真机写动作） <!-- aidcp-edge 813ff7c/b57d619 + aidcp-edge 74eaf41（跨 change 依赖）2026-07-29 记录如下 -->

  **提交 sha（`aidcp-edge` 分支 `native-migration-repair`，均已推送）**：
  - `813ff7c` — 第 6 节全节（清除恒假短路的宿主装配）。改动面：`src/main.ts`、`src/platform/driver.ts`、`src/xhs/driver.ts`、`src/facebook/driver.ts`、新增 `test/native-page-engine/host-assembly-guard.test.ts`，另订正两条既有夹具（`test/platform/driver.test.ts`、`test/electron/control-plane-slot-decoupling.test.ts`）。
  - `b57d619` — 第 1、2、4 节（阻断监测与上报 / 提交窗口 / 排障证据平台对称）。改动面：`src/native-page-engine/browse-session.ts`、`src/native-page-engine/publish.ts`、`native/page-engine/src/engine.rs`、`native/page-engine/src/commit_window.rs`，新增 `test/native-page-engine/xhs-session-guard-blocking.test.ts`、`xhs-session-guard-commit-window.test.ts`、`native/page-engine/tests/xhs_session_guard_write_protection.rs`。
  - **跨 change 依赖**：`74eaf41`（属 `harden-native-engine-runtime-contracts`）把第 2 节需要的五条小红书提交窗口标签加进宿主事实源。**b57d619 与 74eaf41 必须同批部署**，理由见 2.1。
  - 控制仓 `aidcp`：本次台账回写（本文件 + `harden-native-engine-runtime-contracts/tasks.md`），sha 由主控提交时补记。

  **验证证据**：见 7.2–7.5 各条的阶段性记录。另有两处非空转验证：第 6 节的源码级闸做了**植入违规验证**（见 6.3）；剪枝收益用 `git archive HEAD` 快照另建一棵树编译对照（见 6.5）。

  **偏离说明汇总**：1.6（停手闸多一条有界预算出口）、1.9 ①（宿主侧订阅未接线）、§3 与 §5 整节未做、5.6 待人裁定；另有两条残留缺口（评论点赞未纳入提交前闸、会话启动首次扫描不经闸）与两条夹具订正（见 6.2 / 6.3）。

  **热点文件重叠情况**：本轮三条流在同一 worktree 内**文件级零重叠**——第 6 节只动 `src/main.ts` + 三个 driver + 新增测试，`src/native-page-engine/browse-session.ts` / `publish.ts` / `client.ts` 与 `native/page-engine/**` 全程只读；§1/§2/§4 只动 `browse-session.ts` / `publish.ts` / `engine.rs` / `commit_window.rs`。CLAUDE.md §7 点名的四类热点文件（两份 `protocol.ts`、`command-bridge.ts` 动作映射、`RoleName` + `role-catalog`、`risk-state-machine.ts`）**本轮一处未碰**。

  **明确未执行的动作**：未出安装包（未跑 `electron:build` / 签名公证）、未部署（dev / ol 均未做）、**未做任何真机读写动作**、未改 Cloud↔Edge 协议 v2、未改 `openspec/specs/` 下任何文件、未碰 `aidcp-cloud` 仓。

- [x] 7.14 登记「验证码协助除键入取证外的其余 9 项（回放模式、轨迹回放、点击拟人节奏、落点数预检、回放前陈旧复检、抓帧前阻断复检、快照裁剪与类型、实时抓帧的连续确认清除、点击期间抓帧互斥、提交后有界复检）」为本 change 范围外项，已在 design.md Non-Goals 具名交接给「需新立 change（建议名 `restore-native-captcha-assist-humanization`）」 <!-- aidcp 2026-07-29 登记核对：design.md「Goals / Non-Goals」表内该行具名交接仍在，明确「不由 restore-native-actuation-humanization-and-locating 顺手带」，并列出四条真机可观察坏结果 -->
  - 补充（2026-07-29）：本轮 §3（键入取证本体）亦未做，见 §3 下方的未做说明。该 9 项的范围外结论不受影响，仍需新立 change 承接。

### 真机验收项（桩验不了，须在真机上定论；不得当成已确认事实）

> 本轮（2026-07-29）**零真机动作**：未打安装包、未部署、未在真机上做任何读写。7.7–7.13 全部原样保留。

- [ ] 7.7 【真机】小红书环境真触发一次验证码：确认边缘发出 `risk.captcha_detected`、云端唤起远程协助、账号风控态迁移，清除后收到配对 `cleared`
- [ ] 7.8 【真机】小红书 `captcha` 桶的误报率：连续观察若干场浏览，确认正常页面（含笔记详情弹层、看图态、AI 搜索结果页）不被判成阻断（参照 xhs-page-probe.js:22；`captchaSignalCount` 与 `dialogCount` 均不排除笔记详情容器、且已退化成子串计数，是误报的已知根因 — 见 oracle.md）
- [ ] 7.9 【真机】远程协助键入一次真实验证码，确认回执里的实际派发字符数、回读三态与是否提交与现场一致，且答案明文未出现在任何日志 / 落库 / URL 中
- [ ] 7.10 【真机】小红书提交窗口的实际效果：在评论提交进行中发起一次高档位抢占，确认协调器回「窗口占用中 + 剩余预算」而非在提交中途接管
- [ ] 7.11 【真机 · 推断未坐实】简报判定「提交窗口缺失目前只表现为接管失败、不撕裂写入」依赖「写命令不做飞行中取消」这一当前实现，未真机复现；须在真机上确认修复前后是否真出现过重复提交
- [ ] 7.12 【真机 · 推断未坐实】小红书运行期换号 / 掉登录的真实发生形态与频率没有线上数据支撑，只有代码与旧注释对照；周期与防抖阈值须按一次真机观察定档
- [ ] 7.13 【真机】小红书低置信 `unknown` 阻断桶的缺席影响面：观察是否存在「真阻断但既非验证码指纹也非登录墙」的实际形态，据此决定是否值得为它单起一个 change（参照 src/browse/overlay-monitor.ts:1-231 的旧五类分法与 `access-limit-app` 归「可关」；旧 unknown 判据本身是误报源，勿照抄 — 见 oracle.md）
