> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 固化现状的失败优先测试

- [ ] 1.1 为「时间指令被丢弃」写失败优先的测试，两个字段按各自实际转发面分开断言：携带动作前犹豫值的开帖 / 点赞 / 收藏 / 关注 / 评论命令在首条影响页面的输入前有可观测等待；携带离页停留值的关帖 / 返回命令在离开内容前补足停留（该字段转发面只有 feed 翻页、关帖、返回、看图、滚评论五条，返回类命令不携带犹豫值）；当前实现下必须失败 （参照 src/browse/browse-session.ts:504-556；缺犹豫/详情停留/feed 停留三段接线 — 见 oracle.md ⑩）
- [ ] 1.2 为「转发未消费」写一条对照测试：把 `src/native-page-engine/command-mapper.ts` 允许字段表里出现时间字段的命令集合，与 Native 侧消费点集合做集合相等断言；当前实现下必须失败并列出差集 （参照 src/native-page-engine/command-mapper.ts:53-69 转发面 vs Rust 侧零读取点 — 见 oracle.md ⑩）
- [x] 1.3 为「按下失败时抬起不发」写一条 Rust 假 CDP 测试：让按下事件返回错误，断言序列里仍出现抬起事件；当前实现下必须失败 （参照 src/browse/cdp-util.ts:242-260 commitLeftClick 的 try/finally 补发 — 见 oracle.md ②） <!-- aidcp-edge 3a1b2b3 新增 native/page-engine/tests/actuation_pointer.rs::a_failed_press_still_dispatches_its_release_and_never_reports_not_started：假 CDP 拒绝按下，断言抬起仍派发且紧随按下，并断言错误文案带「已派发、不得当未开始重投」 -->
- [x] 1.4 为「点击是坐标瞬移」写一条 Rust 假 CDP 测试：断言一次点击派发的移动事件数 > 1 且帧间延迟非恒定；当前实现下必须失败 （参照 src/humanize/mouse-path.ts:1-136 + cdp-util.ts:176-207；缺弧线/过冲/落点抖动/帧间抖动 — 见 oracle.md ①） <!-- aidcp-edge 3a1b2b3 actuation_pointer.rs::a_click_moves_frame_by_frame_instead_of_teleporting_to_the_target 断言移动帧 > 1 且移动全在按下之前 -->
  - 偏离说明（2026-07-29）：判据被**拆到两层**。假 CDP 层只断言「多帧且移动在按下之前」——CDP 记录里没有可靠的墙钟间隔可读，在假 CDP 上断言「帧间延迟非恒定」等于断言测试机的调度抖动。「帧间延迟非恒定」改由轨迹生成层的单测承担（`input.rs` 的 `pointer_frame_delays_are_not_constant`，64 个种子逐个断言同一条轨迹内至少两帧延迟不同且全部落在 [3, 26] ms）。两层合起来覆盖本条字面；单看假 CDP 那一条不足。
  - 另注（1.3 / 1.4 共同）：两条用例与实现落在**同一个提交**，未经历「先红后绿」的观察窗口。它们的判据是反证式的（多帧 / 抬起必发），把实现回退即会转红，但「失败优先」这一工序本身本轮**未走**。
- [ ] 1.5 为「对齐滚动是单帧精确位移 + 固定间隔」写一条 Rust 假 CDP 测试：断言首页点赞前的对齐滚动派发多帧滚轮且两轮之间的等待不相等；当前实现下必须失败 （参照 src/facebook/viewport-scroll.ts:50-107；现状 feed_like.rs:263-274 单帧精确位移 + 固定 250ms — 见 oracle.md ⑧）
  - 进度说明（2026-07-29）：**未做**。3.1 / 3.2 的实装已落（见那两条），但**点赞前的对齐滚动没有任何假 CDP 用例**——`fake_cdp.rs` 里唯一的多帧滚轮断言是 feed 翻页（`facebook_feed_scroll_dispatches_a_humanized_multi_frame_wheel_gesture`，本轮之前就有）与 Reels 兜底滚轮（本轮改的那两条）。对齐滚动这条路径目前**只有实现、没有回归保护**，实现被改回单帧固定间隔不会有任何测试变红。
- [ ] 1.6 为「单次尝试即报升级」写一条仓内合约测试（测试落本 change 的测试目录、不改被测文件）：断言生产步骤执行路径不存在「升级结论 + 尝试次数为 1」的组合；当前实现下必须失败（现状在 `native/page-engine/src/xhs-command-router.js:242`） （参照 src/locating/engine.ts:247-264：escalated 的前提是连续 maxAttempts=3 次校验失败 — 见 oracle.md ⑮）
- [ ] 1.7 为「云端已下发时长被二次乘档位」写一条测试：断言给定同一 dwell/think 值时，改变生效档位不改变等待中心值（防照搬退役 Facebook 会话的 double-count） （参照 browse-session.ts:514-535；反例 4f04e9c^:facebook-session.ts L722/L738 二次乘档位 — 见 oracle.md 开头补注二）

## 2. aidcp-edge — Native 指针原语与原子区

- [x] 2.1 在 `native/page-engine/src/input.rs` 新增指针原语：多帧轨迹（起点可由调用方指定）、帧间非恒定延迟、路径抖动、可选过冲回拉、落点停顿。只**新增**函数，不动既有文本 / 滚轮原语（该文件与 `harden-native-engine-runtime-contracts` 重叠） （参照 src/humanize/mouse-path.ts:1-136；缺法向弧线/过冲回拉/落点抖动/逐帧延迟四样 — 见 oracle.md ①③） <!-- aidcp-edge 3a1b2b3 新增 dispatch_pointer_click + PointerClickOptions/PointerPoint/PointerInputFailure/PointerRhythm 与三阶贝塞尔轨迹生成；四样齐备：法向偏移弧线（控制点 1/3、2/3 处 ± U(0.1,0.3)×距离）、15% 过冲回拉（5~15px，末帧恒为落点）、落点 ±3px 抖动、逐帧对数正态延迟（中心 8ms、裁进 [3,26]）；既有文本 / 滚轮原语未动，只新增函数与常量 -->
  - 偏离说明（2026-07-29）：另加两样不在字面里的——① 时间参数走 ease-in-out（起步慢 / 中段快 / 逼近再慢，配 Fitts 形态，有单测 `pointer_path_accelerates_then_decelerates`）；② 极近距离（≤2px）或帧预算只剩 1 时退化为单帧，不画无意义曲线。伪随机源是 xorshift + splitmix 混合，种子 = 墙钟毫秒 **异或** 一个进程内自增序号乘黄金比例常数——单靠墙钟会让同一毫秒内的多次调用完全相同（这正是 3.5 要拆掉的那种「假随机」）。
- [x] 2.2 在指针原语内实现按下 / 抬起配平：按下之后无论成功失败都尝试抬起，抬起失败不覆盖原始错误，按下未完成不得返回已作用结果 （参照 cdp-util.ts:251-260：try/finally 补发，补发失败吞掉、原异常原样上抛 — 见 oracle.md ②） <!-- aidcp-edge 3a1b2b3 press 与 release 都先 await 拿到 Result，再判：pressed 出错就返回 SubmitDispatched(原错误)、release 的失败被丢弃不覆盖；pressed 成功才把 release 的失败上抛。假 CDP 用例 1.3 钉住「拒绝按下时抬起仍派发」 -->
- [x] 2.3 把取消与截止检查全部前置到按下之前；按下到抬起之间不留任何提前返回路径，取消只在抬起之后生效 （参照 cdp-util.ts:233-237；注意接管检查须排在死线之前，写反=接管被报成超预算 — 见 oracle.md ②） <!-- aidcp-edge 3a1b2b3 ensure_pointer_input_active() 先查取消再查死线（顺序与 oracle 一致），逐帧前、瞄准停顿后、按下前各调一次；press 到 release 之间无 `?`、无 return、无 await 于取消通道 -->
- [x] 2.4 让原语默认起点取会话内最近一次真实落点（无历史落点时才回落随机偏移），并把真实落点回报给调用方，使同一次互动内的连续点击形成连续光标轨迹 （参照 cdp-util.ts:186-192 默认起点 + :238 返回真实落点供下点继承 — 见 oracle.md ①③） <!-- aidcp-edge 3a1b2b3 LAST_POINTER_LANDING 记住上次真实落点，起点优先级为「调用方显式指定 → 上次落点 → 目标左上方 U(40,160)px 随机偏移」；dispatch_pointer_click 返回 PointerPoint 落点，dispatch_facebook_click_with 透传给调用方 -->
  - 偏离说明（2026-07-29）：落点记忆是**进程内的 `static Mutex<Option<PointerPoint>>`**，不是会话对象上的字段；依据是「引擎进程同一时刻只服务一个会话」，已写进代码注释。若将来一个进程同时服务多会话，这个静态会把 A 会话的光标位置泄漏给 B 会话（不是安全问题，是轨迹连续性会失真）。另：落点在**按下之前**就被记住，因此按下失败的那次也会留下落点——这是有意的（光标物理上确实到了那里）。
- [x] 2.5 把 `native/page-engine/src/facebook/shared.rs` 的点击出口改为调用该原语：原有两参调用形态对全部 11 处调用点行为等价（**新增可选的起点与禁过冲入参**，默认值等价于今天的调用），11 处的结果取值集合不变 （参照 cdp-util.ts:219-240 dispatchClick 的「逐帧移动 + 提交式左键」两段结构 — 见 oracle.md ①②） <!-- aidcp-edge 3a1b2b3 dispatch_facebook_click 两参形态签名不变、内部转调新增的 dispatch_facebook_click_with(…, PointerClickOptions::default())；新入口返回真实落点。逐处核对：comment.rs:123/176、feed.rs:367、feed_like.rs:131/185/201、publish.rs:396/549/880、reels.rs:123、runtime.rs:375、shared.rs:468 共 12 处两参调用全部原样保留、无一处改签名 -->
  - 实测订正（2026-07-29）：任务里写的「全部 **11** 处调用点」与代码对不上——改动前 `dispatch_facebook_click(session, …)` 实际有 **12** 处（清单见上一行）。本轮 `reels.rs` 里原本裸写三条鼠标事件的「下一个」按钮也改走了这个出口（见 3.5），故改动后为 **13** 处。
  - 偏离说明（2026-07-29）：结果取值集合的口径要说清——① 错误码集合不变：新增的两个失败态（取消 / 超死线）在 Facebook 调用点上**不可达**（`dispatch_facebook_click_with` 传的是 `None` 与 `u64::MAX`，见 2.6 / 3.3 的同一处缺口）；移动失败仍原样上抛原错误。② **有一处文案变了**：按下 / 抬起阶段的失败改带「已派发、不得当未开始重放」的措辞（这是 2.8 要的），错误码不变。③ 落点从「精确几何中心」变成「中心 ±3px」，已有一条既有夹具（`facebook_comment_entry.rs` 按 y 归属计数）因此加了 8px 容差——入口与编辑框相距 40px，仍分得开。
- [ ] 2.6 为需要保持指针走廊的两处反应浮层提交调用点（`facebook/feed_like.rs:123`、`:193`）显式传入帖级 react 控件坐标作为起点并禁用过冲，满足已归档 `facebook-note-scoped-targeting` 对该路径的要求；加事件序列断言，断言移动路径未越出走廊 （参照 like-executor.ts:360-387 与 reels-reader.ts:531-536：浮层项必须坐标点击、overshoot=false、定位限定浮层内 — 见 oracle.md ⑪）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；**走廊模式落在了第三处、任务点名的那两处没落，故不勾选**）：已落——① 走廊入参 `PointerClickOptions::from_corridor(起点)`（显式起点 + `allow_overshoot=false`）已实现；② `dispatch_facebook_picker_click`（`feed_like.rs:448`，唯一调用点在 `:358`，首页两步点赞的浮层提交）已改用它，起点取帖级 react 控件坐标；③ 事件序列断言已加——`actuation_pointer.rs::the_reaction_picker_commit_stays_inside_the_control_to_flyout_corridor` 断言移动多帧、全程落在「控件→浮层」两点外接框加一圈余量内、末帧不越过浮层项落点。
  - 未落的部分：任务点名的两处（改动前的 `feed_like.rs:123`、`:193`，现为 `:131`、`:201`）**仍是默认两参调用**——起点走「上次落点」的隐式回落而非显式传入，且**过冲仍然允许**。这两处都在 `execute_facebook_reel_like` 里（短视频点赞的浮层提交），而该路径的主控件提交走的是注入路由、不是 CDP 指针，所以浮层那次点击之前**根本没有留下落点**，起点会回落到「目标左上方随机偏移」，与帖级 react 控件坐标无关。过冲甩出浮层 hover 区致其收起，正是 7.4 真机项点名的那条唯一有理由怀疑会新增失败的路径。**收口前必须把这两处也改成 `from_corridor`。**
  - 实测订正（2026-07-29）：本条的调用点清单**既漏了一处也定位偏了一处**。① 任务点名的 `:123` / `:193` 都在 **`execute_facebook_reel_like`（短视频点赞）** 里，不在首页 feed 点赞路径上；② **首页 feed 点赞的浮层提交是第三处**，走的是 `dispatch_facebook_picker_click`（改动前 `feed_like.rs:333` 调用、`:421` 定义），它**本来就带 `from_x` / `from_y` 显式起点**，本轮改的正是它。所以现状是「首页那条已进走廊、短视频那两条还没进」，与任务字面正好相反。
- [x] 2.7 核算指针帧预算与各命令现有截止预算的关系，超预算时缩减帧数而非跳过配平；记录取值依据 （参照 mouse-path.ts：点数=距离/8 裁进 [15,60]；缩帧不得跳过配平 — 见 oracle.md ①） <!-- aidcp-edge 3a1b2b3 拟人化只吃剩余预算的 1/4（POINTER_FRAME_BUDGET_SHARE=4），按帧间中心值折算成帧数上限；帧数 = 距离/8 裁进 [15,60] 再与预算取小，恒 ≥ 1；瞄准停顿也按「预算减去已花」裁剪。单测 pointer_frame_budget_shrinks_with_the_remaining_deadline + pointer_path_degenerates_… 钉住「预算耗尽也只缩到 1 帧，绝不跳过按下/抬起」 -->
  - 偏离说明（2026-07-29）：取值依据落在代码常量的文档注释里（1/4 份额、帧数 = 距离/8 裁进 [15,60]、帧延迟中心 8ms），**但「与各命令现有截止预算的关系」这一半是空的**——Facebook 的点击调用点目前传的死线是 `u64::MAX`（见 3.3 的同一处缺口），预算裁剪在生产上恒不生效，缩帧路径只有单测覆盖。等 3.3 / 4.x 把死线透传下来后须复核这条份额取值。
- [ ] 2.8 让「按下之后才置位的取消」回报为「已派发、结果待定」而非「未开始」，并加断言防止它被当成可安全重放的失败 （参照 cdp-util.ts:236 的「按下即将派发」诚实置真钩子，防云端按提交前失败重投致双发 — 见 oracle.md ②）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；**真相只到错误文案、没到阶段字段，故不勾选**）：已落——原语层区分出 `PointerInputFailure::SubmitDispatched`，其转成的引擎错误带显式文案「按下已派发、点击可能已生效、MUST NOT 被当成未开始重放」；假 CDP 用例 `a_failed_press_still_dispatches_its_release_and_never_reports_not_started` 断言这两句话都在。
  - 未落的部分：**命令层仍把任何带错误的写一律记成「未开始」**（该判定在引擎主干里，本轮未动那个文件）。所以「已派发」目前只由一句错误文案承载，**没有反映到回执的效果阶段字段上**——云端读到的仍是「未开始」，重投防线实际上还没建立。用例里已就地标注了这个缺口。另注：本原语把取消检查全部前置到按下之前，因此「按下之后才置位的取消」在结构上不会发生，本条的现实形态就是「按下 / 抬起阶段的 CDP 失败」。
- [ ] 2.9 【本轮未做，`engine.rs` 未在 `3a1b2b3` 的改动面内】验证码协助的落点循环（现状 `native/page-engine/src/engine.rs:1283-1297`：一帧移动 + 按下 + 抬起 + 固定 80 毫秒）改为调用 2.1 的指针原语，并给该路径单列一档高审查节奏：移动到位后、按下之前插入瞄准停顿，点与点之间改用对数正态停顿，开启逐帧延迟抖动与落点抖动，上一点的真实落点作下一点起步点 （参照 captcha-assist.ts:73-79 专用档常量、:158-167、:320-341 合成注入循环 — 见 oracle.md ③）
- [ ] 2.10 为验证码协助回执的诚实性加一条仓内合约测试（测试落本 change 的测试目录、不改被测文件）：断言宿主向引擎投影验证码点击参数时不得静默丢弃云端携带的轨迹字段（丢弃必须留下可观测记录），且回执里的回放模式不得写成常量。实现点在 `src/main.ts:992-1001`（手工枚举转发、`payload.trajectory` 被丢且无日志）与 `:1014`（回放模式硬编码为合成），该文件归 `restore-native-xiaohongshu-session-guards`：**本 change 不改该文件**，只与其属主对齐落地方式，并把结论与对应 sha 写回本清单 （参照 captcha-assist.ts:300-318「轨迹无效即如实标注回落、绝不谎称用了轨迹」 — 见 oracle.md ④）
  - 进度说明（2026-07-29）：**未做**，无结论也无 sha。第二波 `3a1b2b3` 只含 Rust 改动，**没有新增任何 TypeScript 用例**，本条要的仓内合约测试不存在；也未与 `restore-native-xiaohongshu-session-guards` 的属主就 `src/main.ts` 的落地方式对齐。两处实现点（轨迹字段被静默丢弃、回放模式硬编码为合成）现状未变。

## 3. aidcp-edge — 拟人滚轮扩到写动作前置手势

- [x] 3.1 把 `native/page-engine/src/facebook/feed_like.rs` 的对齐滚动改为共享拟人手势的有界步进：每轮一次手势、手势后重新解析目标与控件、达到可视带即停（轮次结构与每轮重解析**已存在**，只换手势） （参照 viewport-scroll.ts:50-107 + humanize/scroll-physics.ts:1-98：8~15 帧钟形包络、总位移 ±20% — 见 oracle.md ⑧） <!-- aidcp-edge 3a1b2b3 单帧 dispatch_wheel 换成共享的 dispatch_wheel_humanized（8~15 帧钟形包络、基线 ±20%、滚前先把光标移到落点）；基线位移仍按控件偏移算并保持 ±620 裁剪；轮次结构与每轮 probe_facebook_feed_like_target 重解析原样保留 -->
- [x] 3.2 用随机化的等待取代对齐滚动后的固定 250 毫秒重探间隔 （参照 scroll-physics.ts：帧间 16~60ms 不均匀延迟 — 见 oracle.md ⑧） <!-- aidcp-edge 3a1b2b3 新增 sample_pause_ms()（围绕中心值的对数正态采样，裁进中心值的 0.55~1.8 倍），重探间隔改为 sample_pause_ms(250.0)，中心值不变 -->
- [ ] 3.3 把取消信号与绝对截止透传进对齐循环（共享手势的入参要求），不得把一段不可打断的等待塞进本可让位的路径 （参照 viewport-scroll.ts:50-107「输入异常不中断 browse loop」：派发失败只中止本轮、绝不抛出 — 见 oracle.md ⑧）
  - 进度说明（2026-07-29）：**未做**。3.1 换手势时给对齐滚动传的是 `None` 与 `u64::MAX`（代码里已就地写明原因：取消信号与绝对截止止步于命令分发层，那几个文件不在本轮改动面内）。后果有两条：① 对齐循环里的等待仍不可打断，本可让位的路径继续占着；② 手势的取消 / 超死线两条失败分支在这里**恒不可达**，所以 3.4 说的「结果取值集合不变」是靠「新分支到不了」成立的，而不是靠语义等价。这与 2.5 / 2.7 记的是**同一处缺口**，提交信息也把它列为「Not yet wired」之一。
- [x] 3.4 保留现有轮次上限与不可见时的诚实结论（`target_not_visible` + 未开始），确认改动后结果取值集合不变 （参照 like-executor.ts:346-356：滚够回合仍不可见即诚实报不可见，绝不改点当前居中卡 — 见 oracle.md ⑧） <!-- aidcp-edge 3a1b2b3 逐处核对：FACEBOOK_FEED_SCROLL_ROUNDS 轮次上限未动、滚够回合仍不可见仍回 target_not_visible + 未开始、未新增任何「改点居中卡」的兜底 -->
  - 偏离说明（2026-07-29）：结果取值集合「不变」的前提是 3.3 那两条新失败分支不可达（见上条）。等取消 / 死线真透传下来，对齐循环就会多出两种终局，本条须重新核对。
- [x] 3.5 把 `native/page-engine/src/facebook/reels.rs` 的兜底滚轮改为共享拟人手势（含滚前光标移动），距离改由手势自身在基线附近采样，去掉墙钟毫秒求余 （⚠️ 旧 Reels 实现本身也是单帧滚轮+裸事件，**不可照抄** reels-reader.ts:353-373；应改指 viewport-scroll.ts:50-107 — 见 oracle.md ⑨） <!-- aidcp-edge 3a1b2b3 `70.0 + (unix_time_ms() % 31)` 删除，改基线常量 85px 交给 dispatch_wheel_humanized 采样（±20% 落回原 70~100 区间）；滚前光标移动由手势自带；这一处**真把 cancellation 与 deadline 传了下去**（与 3.3 的对齐循环不同）。夹具 fake_cdp.rs 三处随之改判据：单帧改 8~15 帧、单帧位移改总位移区间、并新增「首个移动事件必须早于首个滚轮事件」断言 -->
  - 偏离说明（2026-07-29）：同一函数里「下一个」按钮那三条裸鼠标事件也一并改走了共享指针出口 `dispatch_facebook_click`（原来按下失败就早返回、抬起永不发出）。这条不在 3.5 字面里，属 2.2 配平红线的同一类缺口，故就地一并修，它也是 2.5 调用点从 12 增到 13 的那一处。另：假 CDP 的应答脚本因多帧手势改成了「输入事件透明放行、脚本只对下一条非输入请求生效」（新增 `respond_to_call_capture_all`）——**这是夹具编码了旧的单帧行为**，不是放松断言：帧数改成区间判据、并补了新的顺序断言。
- [x] 3.6 确认兜底滚轮改动后仍保留位移实测校验，未测到移动不得报成推进 （参照 viewport-scroll.ts「只在前后都量到位置且完全没动时才兜底一次」，避免部分滚轮已生效再补第二段 — 见 oracle.md ⑧） <!-- aidcp-edge 3a1b2b3 手势之后仍走 wait_for_facebook_reel_movement 实测位移，未测到移动才继续往下一档兜底；no_target 分支与「测不到移动不得报推进」的口径原样保留 -->
- [ ] 3.7 【本轮未做，`facebook-router/00-shared.js` 未在 `3a1b2b3` 的改动面内】Facebook 共享注入脚本的通用点击助手（现状 `native/page-engine/src/facebook-router/00-shared.js:34-38`：点击前先 `scrollIntoView({block:'center'})`）去掉这次瞬移——需要把目标带进视野时由 Rust 侧先走 3.1 的共享拟人手势，点击助手本身不得移动页面；并加一条对该脚本文本的静态契约检查，断言助手内不再出现瞬移滚动。消费面为 `facebook-router/90-dispatch.js` 的看图 / 点赞 / 关注 / 评论提交 / 评论点赞五个分支，改动后逐分支确认结果取值集合不变；对已被 Rust 侧截走、实际不可达的分支只记录不改 （参照 test/facebook/like-executor.test.ts:193-225『点击脚本里绝不能再有 scrollIntoView 瞬移』断言 — 见 oracle.md ⑪）

## 4. aidcp-edge — Native 消费云端时间指令

> 进度说明（2026-07-29）：本节 **4.1–4.7 全部未开工**。第二波提交 `3a1b2b3` 只动了 Rust 的 `input.rs` / `locating.rs` / `facebook/{shared,feed_like,reels}.rs` 与四个测试文件，**未碰** `command.rs`、`runtime.rs`、`engine.rs` 的命令执行路径，也未碰宿主 `src/native-page-engine/browse-session.ts`。云端下发的动作前犹豫值与离页停留值在 Native 侧仍是零消费点。

- [ ] 4.1 在 Rust 命令执行路径上为携带动作前犹豫值的命令加入消费点：在该命令第一条影响页面的输入之前等待抖动后的时长 （参照 browse-session.ts:504-512 thinkBefore + :599-614 动作前统一闸 — 见 oracle.md ⑩）
- [ ] 4.2 在 Rust 命令执行路径上为携带离页停留值的命令加入消费点：以内容开始展示的时刻为锚点补足抖动后的停留，已达标不再叠加 （参照 browse-session.ts:514-535/:537-556：以详情打开或本批卡到达时刻起算、只补差额 — 见 oracle.md ⑩）
- [ ] 4.3 明确不对云端已下发的值二次乘以风控档位；只在本地采样兜底时按档位放大（依据：`command-pacing`「云端已下发 dwellMs 不再叠 tempo」；**不得**照搬退役 Facebook 会话 `4f04e9c^:src/facebook/facebook-session.ts` L722/L738 的二次放大） （参照 browse-session.ts:527 注释；反例 4f04e9c^:facebook-session.ts L722/L738 — 见 oracle.md 开头补注二）
- [ ] 4.4 恢复 `src/native-page-engine/browse-session.ts` 的节奏接线：`:121` 改为在本地应用节奏更新而非直接 return，`:213` 的空方法体改为真的保存并应用档位与每类操作 floor 区间。**不改 `src/main.ts`**——其三处快照注入点（`:588`/`:732`/`:1422`）已存在，且该文件归 `restore-native-xiaohongshu-session-guards` （参照 browse-session.ts:470-502：重连重注入清间隔锚点 vs 中途升档只改档位不清锚点 — 见 oracle.md ⑩）
- [ ] 4.5 把 1.2 的集合相等对照做成常驻门禁，新增命令时缺消费点即失败 （参照 command-mapper.ts:53-69 转发白名单：16 条带犹豫、5 条带停留 — 见 oracle.md ⑩）
- [ ] 4.6 逐条列出仍无消费点的命令与理由（若有），写进本清单而不是留空 （对照 oracle.md ⑩ 列出的「14 个命令的犹豫值一路解析进结构体后无人使用」清单）
- [ ] 4.7 登记本 change **不覆盖**的两条 `command-pacing` 已生效义务作为残留缺口（最小间隔 gating 的单调锚点与「与犹豫取 max 不相加」、兜底采样用反射而非硬裁），写清现状为零实现、并在 `docs/real-machine-acceptance-backlog.md` 或后继 change 提案里留名，不得因本 change 落地而被当成已覆盖 （参照 browse-session.ts:568-597 + humanize/timing.ts:113-126：反射采样消竖直左壁尖峰、间隔与犹豫取 max 不相加 — 见 oracle.md ⑩）

## 5. aidcp-edge — Native 定位三道闸

- [ ] 5.1 在 Native 侧建立共享的解析—执行—后置校验编排：写动作后按同一绑定目标读回业务结果，无证据只报诚实的未开始 / 不确定 （参照 src/locating/engine.ts:213-235 执行后重取根再校验；判据分家见 flows/like-post.ts:27-75、publish-post.ts:203-251 — 见 oracle.md ⑫⑬）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；**模块已建但零接线，故不勾选**）：新增 `native/page-engine/src/locating.rs`（348 行）与 `tests/locating_gates.rs`（12 例）。已落——① `LocatingSteps` 三段接口（解析 / 执行 / 后置校验）重建了「可换的页面来源与执行层」这条缝，使判据能脱离浏览器被断言（这正是 7.17 里「在 Native 侧重建可替换缝」那个选项）；② `run_locating_gates` 每一轮**重新解析**、不复用上一轮活引用；③ 终局四态 `Confirmed / NoTarget / Ambiguous / Escalated`，无证据只回诚实的未开始或不确定，绝不回落成已确认。
  - 未落的部分：**该模块没有被任何平台命令调用**（提交信息自己写明「Not yet wired」）。所以现役的写动作一条也没有因此获得后置校验，本条要的「在 Native 侧建立编排」目前只是「有了一个可用的编排原语」。收口前须至少接一条真实命令，否则这三道闸在生产上等于不存在。
- [ ] 5.2 实现有界重试与升级：可重放的写在未达上限时继续尝试；不可重放的写一经派发即停手报不确定、绝不重放；升级结论只在上限耗尽时给出 （参照 engine.ts:137-264：3 轮重试 + no_target / systemic_revision / llm_unavailable 三态终局 — 见 oracle.md ⑮）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；同 5.1，**逻辑齐备但零接线，故不勾选**）：`locating.rs` 里三条判据都在且都有用例——上限默认 3 轮（与退役实现同）、只有上限耗尽才给升级结论、且升级分「一次都没写下去（`NoTarget`）」与「写下去了但结果始终没发生（`SystemicRevision`）」；解析来源本身不可用（`SourceUnavailable`）**立刻升级、不再重试**，与「平台改版」分开；不可重放的写一经派发即停手回 `Ambiguous`，绝不重放（用例 `a_dispatched_non_replayable_write_is_never_retried`）。未落的仍是接线。
- [ ] 5.3 升级语义与尝试计数的实现点在 `native/page-engine/src/xhs-command-router.js`，该文件是并行 change `restore-native-xiaohongshu-action-honesty` 的单写区：**本 change 不改该文件**，只与其属主对齐落地方式（在文件内修正、或以删除该 v1 分支达成），并把结论与对应 sha 写回本清单；1.6 的合约测试按属主落地后的形态转绿 （参照 locating/types.ts:138-148 的升级三态枚举；旧口径下 escalated 须连续 3 次校验失败 — 见 oracle.md ⑮）
  - 对账结果（2026-07-29，属主已落地，**但两个选项都没选，故本条不勾选**）：属主 `restore-native-xiaohongshu-action-honesty` 在 `aidcp-edge 19d4872` 里就其 2.8 做了决策——**保留 v1 分支、走「补测量」**（实读云端 CLI 与规划器后确认该路径仍有活跃产出方，删除即删活路径）。属主只改了 `page.scroll` 那一支（改按实测位移回报），**click / input 两支的 `outcome:'escalated', attempts:1` 原样保留**。因此：本条要的「在文件内修正升级语义」与「删除该 v1 分支」两个选项**都未发生**，`xhs-command-router.js` 里「升级结论 + 尝试次数为 1」的组合**依然存在**，1.6 的合约测试按现状仍会红（1.6 本身也还没写）。下一步须与属主重新对齐：要么把这两支的 `escalated` 降级为 `ambiguous`/`no_target` 之类如实取值，要么给 v1 兼容路径真做有界重试。
- [ ] 5.4 实现锚点暂存区与晋升阈值：非确定性来源得到的新锚点先暂存，连续确认成功达阈值才进主缓存 （参照 cache.ts:89-116 暂存/阈值 2/晋升；⚠️ 旧缓存纯进程内、snapshot 零调用方，持久化须重新设计 — 见 oracle.md ⑯⑲）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；**7.16 明令「裁定前不得按已实现勾掉」，故不勾选**）：`locating.rs` 的 `AnchorCache` 实现了主缓存 + 暂存区两层、可配置的连续确认阈值、三种运行模式（读写 / 只读 / 只写）、快照进出（畸形快照整体拒绝、绝不半载入），并明确「只有**非确定性**来源的锚点才进暂存区」。用例覆盖晋升、阈值、锚点变更即重置确认计数、确定性锚点永不进暂存。**但暂存区在当前引擎里恒为空**——每个定位器都是编译进二进制的固定选择器，没有任何非确定性来源，`stage_non_deterministic` 在生产上不会被调用。实装方就此加了一条测试把「空转」这件事钉死，以免被读成「定位自愈已恢复」。裁定见 7.16。
- [ ] 5.5 实现反污染丢弃：任一次后置校验失败即把相关暂存锚点丢弃，且不得被后续解析当作已确认复用 （参照 cache.ts:119-121 dropStaged + engine.ts:238-243「校验失败即丢弃且强制换路径」 — 见 oracle.md ⑯）
  - 部分完成（2026-07-29，`aidcp-edge 3a1b2b3`；同 5.4，受 7.16 阻断故不勾选）：`record_failure` 当场 `staged.remove(key)` 并给主缓存记一次失败；用例 `a_failed_validation_drops_the_staged_anchor_for_good` 断言丢弃后不再被当已确认复用。同样受「暂存区恒为空」这个前提影响：逻辑正确，但在生产上无事可做。
- [ ] 5.6 逐条盘点当前 Native 命令面，标出哪些已具备后置校验、哪些暂不具备并注明原因；不具备的不得默认返回成功 （参照 engine.ts:39-41 校验器是接口式强制、缺判据即编译不过；判据强度反例见 oracle.md ⑬⑭）
- [ ] 5.7 **只读**确认 `scripts/prune-production-dist.mjs` 的禁入表未被放宽（该文件归 `enforce-native-engine-artifact-gates`，本 change 不改一行），退役的 TypeScript 定位层与锚点缓存仍不进生产产物
  - 进度说明（2026-07-29）：**未做**，且现在更该做了。属主 change `enforce-native-engine-artifact-gates` 已在同一分支的 `aidcp-edge be0a8be` 落地，**把该脚本整体重写**（242 行改动，同批还新增了 `scripts/gate-native.mjs`、`scripts/native-engine-inventory.cjs` 与 `test/native-page-engine/artifact-gates.test.ts`）。本条的只读确认必须**以 `be0a8be` 之后的脚本为准**重做一次：禁入表在重写中是否仍覆盖退役的 TypeScript 定位层与锚点缓存，尚无人核对。本 change 不改该文件一行的纪律不变。
- [ ] 5.8 记录本 change 对迁移主 change 3.2 的承接边界：只承接三道闸，可见性 / 几何 / 歧义拒绝仍归各平台目标解析能力；3.3 的文件输入那一半也不在本 change 内 —— 两条都不得因本 change 落地而被整条勾掉 （本 change 未承接的参照条目：匹配唯一性闸 / 守卫层 / 模型兜底 / 语义 class 白名单 / 可换接口 — 见 oracle.md 覆盖漏洞）
- [ ] 5.9 给后置校验判据立**强度下限**（5.1 只要求「有校验环节」，一条宽松子串正则即可满足其字面）：状态翻转只认属性白名单等于真值（可访问按下态 / 选中态 / 站点稳定的已点赞与已选中属性），类名只认词边界匹配出来的语义片段（片段须是整个 class token，或被连字符 / 下划线包裹），并沿祖先做有限层级回溯（翻转可能落在包裹容器上）；**MUST NOT** 用宽松子串正则判「已生效」，也不得用单个汉字（如「已」）作文本兜底。没有实测锚点的判据一律 fail-closed 诚实失败 （参照 flows/like-post.ts:27-60 属性白名单 + 3 层回溯、publish-command-handlers.ts:346-360 封面判据 fail-closed；现状反例 `xhs-command-router.js:52`、`:233`、`:287` — 见 oracle.md ⑬⑳）
- [ ] 5.10 禁止**自证循环**：后置校验读回的证据不得是本命令自己刚写进页面的那段文本。文本类结果的校验须走结构信号 + 精确相等（去前导标记、去空白、大小写归一，并剔除隐藏后缀），不得对整段编辑器文本做包含判断 （参照 publish-post.ts:255-294 真话题标记判据：只认带话题属性的真标记、精确相等；现状反例 `xhs-command-router.js:256` 读回的正是自己刚写入的文本 — 见 oracle.md ⑭）
- [ ] 5.11 按 5.9 / 5.10 逐条盘点现存后置判据（小红书注入路由 8 处、Facebook 加群的有界轮询复查、其余靠一次 sleep 后复读的分支），标出达标 / 不达标；不达标且实现点落在他人单写区（`xhs-command-router.js` 归 `restore-native-xiaohongshu-action-honesty`）的，只与属主对齐落地方式并回写 sha，本 change 不代改 （参照 engine.ts:39-41「校验器是接口式强制、缺判据即编译不过」 — 见 oracle.md ⑫）
  - 进度说明（2026-07-29）：**盘点本身未做**（无逐条清单产出），但**盘点的基线已经变了**，重做时须以属主的第二波提交 `aidcp-edge 19d4872` 为准，不要照着旧行号盘。该提交在小红书注入路由里改掉的后置判据至少有六处：赞 / 收藏改读图标状态位（`svg use` 的 `#like→#liked`）并做 1500ms 有界轮询、关注**新写**了后置校验（旧实现点完只睡一觉就无条件报成功）、「控件文本含『已』」这条 5.9 点名的宽松兜底**已删除**、返回列表的 `ok` 改由列表面推导、滚评论的 `ok` 改由位移推导、发布提交改绑本次草稿的成功文案。**仍不达标且属主未动的**：5.10 点名的自证循环（评论提交读回的正是自己刚写进编辑器的文本）与 v1 兼容路径 click / input 两支的升级语义（见 5.3）。

## 6. aidcp-edge — 仓内验证

- [ ] 6.1 运行 Rust 单测与假 CDP 测试（`cargo test --locked`），记录通过数
  - 阶段性记录（2026-07-29，change 未收口故不勾选）：Rust 门禁 `npm run gate:native` **通过**（toolchain `1.97.1-aarch64-apple-darwin`，steps = fmt, clippy, test），本条要的 `cargo test` 被它涵盖。本波新增 Rust 用例：`tests/actuation_pointer.rs` 3 例（假 CDP：按下失败仍补发抬起 / 点击非瞬移 / 浮层提交不越出走廊）、`tests/locating_gates.rs` 12 例、`input.rs` 单测 7 例。**逐项通过数未单独记录**（门禁只报总体通过），收口时须单跑 `cargo test --locked` 补上精确计数。
- [ ] 6.2 运行 `cargo fmt --check` 与 `cargo clippy -- -D warnings`
  - 阶段性记录（2026-07-29，同上不勾选）：两者都被 `npm run gate:native` 的 steps 涵盖并**通过**。注：本轮按并行纪律**禁止单独跑 `cargo fmt`**（会重写全部 Rust 文件、砸掉并行流），故只经门禁校验、未单独执行。
- [ ] 6.3 运行 `npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）
  - 阶段性记录（2026-07-29，同上不勾选）：**30 / 30 全过、0 失败**（1 条 gated 跳过 = 需真机的 E2E）。
- [ ] 6.4 运行 `npm test` 全量与 `npm run typecheck`
  - 阶段性记录（2026-07-29，同上不勾选）：`npm test` **2630 例 / 2629 绿 / 0 红 / 1 跳过**；`npm run typecheck` **通过**。本波改了三个既有 Rust 夹具（`fake_cdp.rs` 的两条 Reels 滚轮用例、`facebook_comment_entry.rs` 的按点位计数助手），**均为夹具编码了旧的缺陷形态**（「鼠标事件恰好三条」「兜底滚轮恰好一帧」「落点必须精确等于几何中心」），改法是把常量判据换成不变量判据（按下/抬起各一次且成对、帧数落在分布区间、落点带容差）并**新增**顺序断言，**没有放松任何安全断言**。
- [ ] 6.5 运行 `npm run build:dist` 并确认生产产物剪枝检查通过、禁入表未放宽
  - 进度说明（2026-07-29）：**本轮未跑**。
- [ ] 6.6 记录 Edge 与控制仓的提交 sha、偏离说明、与并行 change 的重叠文件（sha 必须取自已推送的提交）
  - 进度说明（2026-07-29，**分波回写中，change 未收口故不勾选**）：Edge 侧本波 sha = `3a1b2b3`（分支 `native-migration-repair`），已逐条落在各任务行尾；**控制仓 sha 待本文件提交后补**。重叠文件实测：本波碰的是 `native/page-engine/src/{input.rs,locating.rs,lib.rs,facebook/{shared,feed_like,reels}.rs}` 与四个 Rust 测试文件；design 重叠表点名的五处里，`input.rs` **碰了**（只新增函数与常量，未动既有文本 / 滚轮原语），`browse-session.ts` / `command.rs` / `runtime.rs` / `engine.rs` **一处都没碰**。与并行 change `restore-native-xiaohongshu-action-honesty`（本波 `a45fc81` / `19d4872`）在本波**零文件交叉**——它动的是 xhs 路由、probe 与宿主两个 TS 文件。
- [ ] 6.7 集成前按 design 的重叠文件表逐行核对：`input.rs` / `browse-session.ts` / `command.rs` / `runtime.rs` / `engine.rs` 五处属多流共写，先 fetch + rebase 到各属主最新提交再跑 6.1–6.5；push 遇 non-ff 一律 rebase 重来，绝不 force
  - 进度说明（2026-07-29）：**未做**（两波都还在同一条 `native-migration-repair` 分支上串行落地，尚未做跨属主的 fetch + rebase 核对）。

## 7. 验证与验收

- [ ] 7.1 运行 `openspec validate restore-native-actuation-humanization-and-locating --strict`
- [ ] 7.2 【真机验收项】在 dev 真机上用测试分组账号确认：恢复时间指令消费后，一次浏览闭环不会因单命令墙钟变长触发会话看门狗；记录实际的单命令耗时分布与看门狗阈值余量
- [ ] 7.3 【真机验收项】在 dev 真机上确认：改为有界步进后，首页点赞的对齐滚动仍能在现有轮次上限内把控件带进可视带；若不足，记录实测轮次并单独调整上限 （参照 like-executor.ts:346-356 的有界滚动与诚实不可见结论 — 见 oracle.md ⑧）
- [ ] 7.4 【真机验收项】在 dev 真机上确认：指针原语改为多帧轨迹后，Facebook 首页点赞、评论提交、加群按钮三条路径的成功率不低于改动前；两步点赞的第二步（反应浮层「赞」项）仍能提交 —— 重点看多帧轨迹是否会在移动途中划出浮层 hover 区致其收起，这是本改动唯一有理由怀疑会新增失败的路径 （参照 like-executor.ts:360-387：浮层「赞」项 in-page click 会返回已点却不生效，真机 A/B 实证 — 见 oracle.md ⑪）
- [ ] 7.5 【真机验收项】在 dev 真机上确认：短视频兜底滚轮改用共享手势后，推进仍可用且未出现"测不到移动却报推进" （⚠️ 旧 Reels 也无位移实测，此条无参照物、须新建 — 见 oracle.md ⑨）
- [ ] 7.6 【真机验收项 / 未坐实】"当前节奏与手势特征已被平台判别"这一因果无法在代码里坐实，只能通过真机上的限流信号频次做前后对照观察；本 change 只按已归档的节奏与反检测规格恢复应有行为，不主张判别因果
- [ ] 7.7 【真机验收项 / 未坐实】锚点暂存与晋升在 Native 侧恢复后，实际能带来多少定位命中率提升无线上数据支撑；上线后按定位失败原因分布做一次前后对照
- [ ] 7.8 记录本 change 明确未做的事：未打安装包、未部署 dev/ol、未改云端节奏中心值、未代改迁移主 change 的 tasks.md
  - 阶段性记录（2026-07-29，change 未收口故不勾选）：本波**未打安装包、未部署（dev / ol 都没碰）、未替换运行中的桌面客户端、未做任何真机动作、未改云端节奏中心值（未碰 `aidcp-cloud` 仓）、未代改任何他人 change 的 tasks.md**。另未碰：`openspec/specs/`、`docs/real-machine-acceptance-backlog.md`、`design.md`、协议四处同步文件、`facebook-router/**` 注入脚本、宿主 TS 全部文件。分支 `native-migration-repair` 本波提交为 `3a1b2b3`，**未合入 master**。
- [ ] 7.9 把 7.2–7.7 的真机项登记进 `docs/real-machine-acceptance-backlog.md` 的对应簇
- [ ] 7.10 登记 **运营真机鼠标轨迹回放通道** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**（本 change 只做 2.10 的「丢弃可观测 + 回放模式不得硬编码」那一半）
- [ ] 7.11 登记 **小红书注入路由的通用点击助手（瞬移滚动 + 伪造指针移动）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **restore-native-xiaohongshu-action-honesty**（该文件的单写区属主；本 change 只在规格层立跨平台要求并改 Facebook 那一半）
- [ ] 7.12 登记 **话题标记后置判据（真标记 + 精确相等 + 剔隐藏后缀）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **restore-native-xiaohongshu-action-honesty**（本 change 只在 5.10 立「禁自证循环」的跨平台判据要求）
- [ ] 7.13 登记 **动作前守卫层（干扰扫描 + 多轮清障 + 停手终局）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**
- [ ] 7.14 登记 **语义类名白名单的词边界匹配与匹配唯一性闸** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**（与匹配唯一性闸同批）
- [ ] 7.15 登记 **按边缘标识派生的每机节奏偏置** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **harden-native-engine-runtime-contracts**（会话身份入参的属主）
- [ ] 7.16 【阻塞：待裁定 P1】锚点暂存区的前提在新引擎里不成立（无任何非确定性锚点来源），裁定「保留空结构 / 改判据 / 暂不做」之前，5.4 / 5.5 与 `native-locating-gates` 的锚点要求不得开工，也不得按「已实现」勾掉；裁定结论写回 design.md「待裁定」小节
  - 实装侧的处置（2026-07-29，`aidcp-edge 3a1b2b3`；**这是实现选择，不是裁定，故本条仍不勾选**）：`3a1b2b3` 事实上走了「**保留空结构**」这一支——`locating.rs` 把暂存区与晋升阈值整套实现出来，同时明确写下「暂存区在当前引擎里恒为空（每个定位器都是编译进二进制的固定选择器，`stage_non_deterministic` 生产上不会被调用）」，并**专门立了一条测试把这件事钉死**，以免被读成「定位自愈已恢复」；模块头注释也直接指回本条「待裁定 P1」。
  - 为什么仍不算裁定：① 本条要求的「裁定结论写回 design.md『待裁定』小节」**未发生**——`design.md` 本波一字未改；② 三个选项里「改判据 / 暂不做」是否更划算，取决于要不要在 Native 侧重新引入非确定性锚点来源（那是产品与架构取舍，不是实现细节），**裁定权仍在人**。实装选择只是把「暂不做」的成本降到最低（结构在、空转可证、被误读的风险已被测试封住），**并没有替代那次裁定**。下一步：由人在 design.md 里落一句结论，然后 5.4 / 5.5 才可按结论收口。
- [ ] 7.17 【阻塞：待裁定 P2】可换的页面来源与执行层两个接口在迁移中消失，1.3 / 1.4 / 1.5 与 5.1–5.5 的断言方式取决于裁定结果（在 Native 侧重建可替换缝 / 接受退化为真机验收）；裁定前不得把这些任务的验证方式定稿，也不得默认它们能脱机跑；裁定结论写回 design.md「待裁定」小节
  - 实装侧的处置（2026-07-29，`aidcp-edge 3a1b2b3`；同 7.16，**未写回 design.md，故不勾选**）：事实上走了「**在 Native 侧重建可替换缝**」这一支，且两条缝各自落地形态不同——① 定位层用 `LocatingSteps` 三段接口（解析 / 执行 / 后置校验）重建可替换缝，`tests/locating_gates.rs` 的 12 例全部脱机跑、不起浏览器；② 指针 / 输入层**没有**新建接口，改用假 CDP 服务端（`tests/actuation_pointer.rs`、`fake_cdp.rs`）在协议层替换，1.3 / 1.4 就是这么断言的。所以「能不能脱机跑」这个问题现在有了肯定答案，但**验证方式尚未定稿**：1.5（对齐滚动）至今没有任何用例（见 1.5 进度说明），而 5.1–5.5 的接线一条都没做，脱机断言目前只覆盖原语本身、不覆盖任何真实命令路径。裁定结论仍须由人写回 design.md。
- [ ] 7.18 把 8.6 的真机复核项与 7.16 / 7.17 裁定后新增的真机项一并登记进 `docs/real-machine-acceptance-backlog.md`

## 8. aidcp-edge — 小红书写动作接上已有的 Native 拟人原语

> 本节只做**原语接线**：Rust 侧已有与退役实现参数逐项一致的逐字输入原语（`native/page-engine/src/input.rs:93-137`）与惯性滚轮原语（`:43-65`、`:269-310`），小红书路径完全没有接线到它们。接线方式为在 `native/page-engine/src/engine.rs` 的小红书分发里**新增命令特化分支**（该函数末尾的通配分支才落到注入路由），**不改 `native/page-engine/src/xhs-command-router.js`**——引擎侧特化截走命令后其对应分支不可达，删除由单写区属主 `restore-native-xiaohongshu-action-honesty` 处置。本节**不动**小红书的回执口径与后置判据（属该 change）。`engine.rs` 的小红书执行入口为三流共写，集成须串行。

- [ ] 8.1 小红书全线文本输入改走硬件级逐字输入原语：评论提交、发布填写、话题 / 提及候选、定时设置、遗留步骤路径的输入步，全部不再用「属性描述符 setter 一次性写 value / 对可编辑元素整段赋 textContent + 手动派发合成事件」 （参照 humanize/keyboard-rhythm.ts:22-81 + cdp-util.ts:310-340；现状 `xhs-command-router.js:34-44` 的输入助手及其 5 个消费点 — 见 oracle.md ⑤）
- [ ] 8.2 长正文加往返与停顿双封顶（写入次数上限、总停顿预算），红线是**所有字符都必须写入**——封顶只缩时间与往返、不得丢内容；核算封顶值与云端单步超时的余量并记录依据 （参照 publish-command-handlers.ts:758-791 的分块突发式输入与「不逐字到底」的理由 — 见 oracle.md ⑤）
- [ ] 8.3 正文换行拆成两类原语：文本写入一律不携带回车符，换行改为独立的裸回车按键（让编辑器自己执行段落拆分，带回车字符的形态只用于搜索框）；每次回车后做有界归尾确认——已写前缀仍在 + 换行数达标 + 光标位于末端，且须连续两次命中才算稳定，探针发现选区偏移时就地折叠到末尾再确认下一轮；上限与轮询间隔取有界值，超时即清空正文并诚实失败，不留下逐渐积累的文末尾字 （参照 publish-command-handlers.ts:793-816/:818-864/:866-892 与 dev record #153 的段落重排抢跑 — 见 oracle.md ⑥）
- [ ] 8.4 逐字输入的取消缝落在「这一字符的等待已结束、它的写入尚未发出」那一瞬；已写入的部分留在编辑器里并由调用方负责清场，接管异常须原样穿出、不得被吞成普通失败 （参照 cdp-util.ts:310-340 的取消缝位置与「接管优先于死线」的顺序 — 见 oracle.md ⑤②）
- [ ] 8.5 小红书滚动改走共享惯性滚轮手势（含滚前把光标移到可滚区中心）：feed 翻页与详情页评论滚动都不再用页面内平滑滚动，帧间延迟与总位移由手势自身采样；派发失败只中止本轮滚动、绝不抛出（一次瞬时超时不得终结整个浏览循环） （参照 humanize/scroll-physics.ts:1-98 + feed-scroller.ts:176-212；现状 `xhs-command-router.js:158`、`:213` — 见 oracle.md ⑦）
- [ ] 8.6 【真机验收项】feed 单次位移口径改回「约半屏、保留相邻两次扫描的可见卡片重叠」，并真机复核旧注释的两条结论在当前布局上是否仍成立：宽 / 窄两套布局的可滚元素不同、页面内滚动在窄布局上是空操作；**未复核前不得把「小红书 feed 已因此永不推进」当作既成事实** （参照 feed-scroller.ts:177-184/:191-194 的三重理由与 500px 口径 — 见 oracle.md ⑦）
- [ ] 8.7 记录本节与 `restore-native-xiaohongshu-action-honesty` 的分工结论与对应 sha：本节只接线原语，其回执口径、后置判据、去重键、遗留分支删除均归该 change；两侧对 `engine.rs` 小红书分发的改动按 6.7 的串行集成纪律处理
