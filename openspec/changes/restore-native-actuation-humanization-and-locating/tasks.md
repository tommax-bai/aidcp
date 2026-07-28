> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 固化现状的失败优先测试

- [ ] 1.1 为「时间指令被丢弃」写失败优先的测试，两个字段按各自实际转发面分开断言：携带动作前犹豫值的开帖 / 点赞 / 收藏 / 关注 / 评论命令在首条影响页面的输入前有可观测等待；携带离页停留值的关帖 / 返回命令在离开内容前补足停留（该字段转发面只有 feed 翻页、关帖、返回、看图、滚评论五条，返回类命令不携带犹豫值）；当前实现下必须失败 （参照 src/browse/browse-session.ts:504-556；缺犹豫/详情停留/feed 停留三段接线 — 见 oracle.md ⑩）
- [ ] 1.2 为「转发未消费」写一条对照测试：把 `src/native-page-engine/command-mapper.ts` 允许字段表里出现时间字段的命令集合，与 Native 侧消费点集合做集合相等断言；当前实现下必须失败并列出差集 （参照 src/native-page-engine/command-mapper.ts:53-69 转发面 vs Rust 侧零读取点 — 见 oracle.md ⑩）
- [ ] 1.3 为「按下失败时抬起不发」写一条 Rust 假 CDP 测试：让按下事件返回错误，断言序列里仍出现抬起事件；当前实现下必须失败 （参照 src/browse/cdp-util.ts:242-260 commitLeftClick 的 try/finally 补发 — 见 oracle.md ②）
- [ ] 1.4 为「点击是坐标瞬移」写一条 Rust 假 CDP 测试：断言一次点击派发的移动事件数 > 1 且帧间延迟非恒定；当前实现下必须失败 （参照 src/humanize/mouse-path.ts:1-136 + cdp-util.ts:176-207；缺弧线/过冲/落点抖动/帧间抖动 — 见 oracle.md ①）
- [ ] 1.5 为「对齐滚动是单帧精确位移 + 固定间隔」写一条 Rust 假 CDP 测试：断言首页点赞前的对齐滚动派发多帧滚轮且两轮之间的等待不相等；当前实现下必须失败 （参照 src/facebook/viewport-scroll.ts:50-107；现状 feed_like.rs:263-274 单帧精确位移 + 固定 250ms — 见 oracle.md ⑧）
- [ ] 1.6 为「单次尝试即报升级」写一条仓内合约测试（测试落本 change 的测试目录、不改被测文件）：断言生产步骤执行路径不存在「升级结论 + 尝试次数为 1」的组合；当前实现下必须失败（现状在 `native/page-engine/src/xhs-command-router.js:242`） （参照 src/locating/engine.ts:247-264：escalated 的前提是连续 maxAttempts=3 次校验失败 — 见 oracle.md ⑮）
- [ ] 1.7 为「云端已下发时长被二次乘档位」写一条测试：断言给定同一 dwell/think 值时，改变生效档位不改变等待中心值（防照搬退役 Facebook 会话的 double-count） （参照 browse-session.ts:514-535；反例 4f04e9c^:facebook-session.ts L722/L738 二次乘档位 — 见 oracle.md 开头补注二）

## 2. aidcp-edge — Native 指针原语与原子区

- [ ] 2.1 在 `native/page-engine/src/input.rs` 新增指针原语：多帧轨迹（起点可由调用方指定）、帧间非恒定延迟、路径抖动、可选过冲回拉、落点停顿。只**新增**函数，不动既有文本 / 滚轮原语（该文件与 `harden-native-engine-runtime-contracts` 重叠） （参照 src/humanize/mouse-path.ts:1-136；缺法向弧线/过冲回拉/落点抖动/逐帧延迟四样 — 见 oracle.md ①③）
- [ ] 2.2 在指针原语内实现按下 / 抬起配平：按下之后无论成功失败都尝试抬起，抬起失败不覆盖原始错误，按下未完成不得返回已作用结果 （参照 cdp-util.ts:251-260：try/finally 补发，补发失败吞掉、原异常原样上抛 — 见 oracle.md ②）
- [ ] 2.3 把取消与截止检查全部前置到按下之前；按下到抬起之间不留任何提前返回路径，取消只在抬起之后生效 （参照 cdp-util.ts:233-237；注意接管检查须排在死线之前，写反=接管被报成超预算 — 见 oracle.md ②）
- [ ] 2.4 让原语默认起点取会话内最近一次真实落点（无历史落点时才回落随机偏移），并把真实落点回报给调用方，使同一次互动内的连续点击形成连续光标轨迹 （参照 cdp-util.ts:186-192 默认起点 + :238 返回真实落点供下点继承 — 见 oracle.md ①③）
- [ ] 2.5 把 `native/page-engine/src/facebook/shared.rs` 的点击出口改为调用该原语：原有两参调用形态对全部 11 处调用点行为等价（**新增可选的起点与禁过冲入参**，默认值等价于今天的调用），11 处的结果取值集合不变 （参照 cdp-util.ts:219-240 dispatchClick 的「逐帧移动 + 提交式左键」两段结构 — 见 oracle.md ①②）
- [ ] 2.6 为需要保持指针走廊的两处反应浮层提交调用点（`facebook/feed_like.rs:123`、`:193`）显式传入帖级 react 控件坐标作为起点并禁用过冲，满足已归档 `facebook-note-scoped-targeting` 对该路径的要求；加事件序列断言，断言移动路径未越出走廊 （参照 like-executor.ts:360-387 与 reels-reader.ts:531-536：浮层项必须坐标点击、overshoot=false、定位限定浮层内 — 见 oracle.md ⑪）
- [ ] 2.7 核算指针帧预算与各命令现有截止预算的关系，超预算时缩减帧数而非跳过配平；记录取值依据 （参照 mouse-path.ts：点数=距离/8 裁进 [15,60]；缩帧不得跳过配平 — 见 oracle.md ①）
- [ ] 2.8 让「按下之后才置位的取消」回报为「已派发、结果待定」而非「未开始」，并加断言防止它被当成可安全重放的失败 （参照 cdp-util.ts:236 的「按下即将派发」诚实置真钩子，防云端按提交前失败重投致双发 — 见 oracle.md ②）
- [ ] 2.9 验证码协助的落点循环（现状 `native/page-engine/src/engine.rs:1283-1297`：一帧移动 + 按下 + 抬起 + 固定 80 毫秒）改为调用 2.1 的指针原语，并给该路径单列一档高审查节奏：移动到位后、按下之前插入瞄准停顿，点与点之间改用对数正态停顿，开启逐帧延迟抖动与落点抖动，上一点的真实落点作下一点起步点 （参照 captcha-assist.ts:73-79 专用档常量、:158-167、:320-341 合成注入循环 — 见 oracle.md ③）
- [ ] 2.10 为验证码协助回执的诚实性加一条仓内合约测试（测试落本 change 的测试目录、不改被测文件）：断言宿主向引擎投影验证码点击参数时不得静默丢弃云端携带的轨迹字段（丢弃必须留下可观测记录），且回执里的回放模式不得写成常量。实现点在 `src/main.ts:992-1001`（手工枚举转发、`payload.trajectory` 被丢且无日志）与 `:1014`（回放模式硬编码为合成），该文件归 `restore-native-xiaohongshu-session-guards`：**本 change 不改该文件**，只与其属主对齐落地方式，并把结论与对应 sha 写回本清单 （参照 captcha-assist.ts:300-318「轨迹无效即如实标注回落、绝不谎称用了轨迹」 — 见 oracle.md ④）

## 3. aidcp-edge — 拟人滚轮扩到写动作前置手势

- [ ] 3.1 把 `native/page-engine/src/facebook/feed_like.rs` 的对齐滚动改为共享拟人手势的有界步进：每轮一次手势、手势后重新解析目标与控件、达到可视带即停（轮次结构与每轮重解析**已存在**，只换手势） （参照 viewport-scroll.ts:50-107 + humanize/scroll-physics.ts:1-98：8~15 帧钟形包络、总位移 ±20% — 见 oracle.md ⑧）
- [ ] 3.2 用随机化的等待取代对齐滚动后的固定 250 毫秒重探间隔 （参照 scroll-physics.ts：帧间 16~60ms 不均匀延迟 — 见 oracle.md ⑧）
- [ ] 3.3 把取消信号与绝对截止透传进对齐循环（共享手势的入参要求），不得把一段不可打断的等待塞进本可让位的路径 （参照 viewport-scroll.ts:50-107「输入异常不中断 browse loop」：派发失败只中止本轮、绝不抛出 — 见 oracle.md ⑧）
- [ ] 3.4 保留现有轮次上限与不可见时的诚实结论（`target_not_visible` + 未开始），确认改动后结果取值集合不变 （参照 like-executor.ts:346-356：滚够回合仍不可见即诚实报不可见，绝不改点当前居中卡 — 见 oracle.md ⑧）
- [ ] 3.5 把 `native/page-engine/src/facebook/reels.rs` 的兜底滚轮改为共享拟人手势（含滚前光标移动），距离改由手势自身在基线附近采样，去掉墙钟毫秒求余 （⚠️ 旧 Reels 实现本身也是单帧滚轮+裸事件，**不可照抄** reels-reader.ts:353-373；应改指 viewport-scroll.ts:50-107 — 见 oracle.md ⑨）
- [ ] 3.6 确认兜底滚轮改动后仍保留位移实测校验，未测到移动不得报成推进 （参照 viewport-scroll.ts「只在前后都量到位置且完全没动时才兜底一次」，避免部分滚轮已生效再补第二段 — 见 oracle.md ⑧）
- [ ] 3.7 Facebook 共享注入脚本的通用点击助手（现状 `native/page-engine/src/facebook-router/00-shared.js:34-38`：点击前先 `scrollIntoView({block:'center'})`）去掉这次瞬移——需要把目标带进视野时由 Rust 侧先走 3.1 的共享拟人手势，点击助手本身不得移动页面；并加一条对该脚本文本的静态契约检查，断言助手内不再出现瞬移滚动。消费面为 `facebook-router/90-dispatch.js` 的看图 / 点赞 / 关注 / 评论提交 / 评论点赞五个分支，改动后逐分支确认结果取值集合不变；对已被 Rust 侧截走、实际不可达的分支只记录不改 （参照 test/facebook/like-executor.test.ts:193-225『点击脚本里绝不能再有 scrollIntoView 瞬移』断言 — 见 oracle.md ⑪）

## 4. aidcp-edge — Native 消费云端时间指令

- [ ] 4.1 在 Rust 命令执行路径上为携带动作前犹豫值的命令加入消费点：在该命令第一条影响页面的输入之前等待抖动后的时长 （参照 browse-session.ts:504-512 thinkBefore + :599-614 动作前统一闸 — 见 oracle.md ⑩）
- [ ] 4.2 在 Rust 命令执行路径上为携带离页停留值的命令加入消费点：以内容开始展示的时刻为锚点补足抖动后的停留，已达标不再叠加 （参照 browse-session.ts:514-535/:537-556：以详情打开或本批卡到达时刻起算、只补差额 — 见 oracle.md ⑩）
- [ ] 4.3 明确不对云端已下发的值二次乘以风控档位；只在本地采样兜底时按档位放大（依据：`command-pacing`「云端已下发 dwellMs 不再叠 tempo」；**不得**照搬退役 Facebook 会话 `4f04e9c^:src/facebook/facebook-session.ts` L722/L738 的二次放大） （参照 browse-session.ts:527 注释；反例 4f04e9c^:facebook-session.ts L722/L738 — 见 oracle.md 开头补注二）
- [ ] 4.4 恢复 `src/native-page-engine/browse-session.ts` 的节奏接线：`:121` 改为在本地应用节奏更新而非直接 return，`:213` 的空方法体改为真的保存并应用档位与每类操作 floor 区间。**不改 `src/main.ts`**——其三处快照注入点（`:588`/`:732`/`:1422`）已存在，且该文件归 `restore-native-xiaohongshu-session-guards` （参照 browse-session.ts:470-502：重连重注入清间隔锚点 vs 中途升档只改档位不清锚点 — 见 oracle.md ⑩）
- [ ] 4.5 把 1.2 的集合相等对照做成常驻门禁，新增命令时缺消费点即失败 （参照 command-mapper.ts:53-69 转发白名单：16 条带犹豫、5 条带停留 — 见 oracle.md ⑩）
- [ ] 4.6 逐条列出仍无消费点的命令与理由（若有），写进本清单而不是留空 （对照 oracle.md ⑩ 列出的「14 个命令的犹豫值一路解析进结构体后无人使用」清单）
- [ ] 4.7 登记本 change **不覆盖**的两条 `command-pacing` 已生效义务作为残留缺口（最小间隔 gating 的单调锚点与「与犹豫取 max 不相加」、兜底采样用反射而非硬裁），写清现状为零实现、并在 `docs/real-machine-acceptance-backlog.md` 或后继 change 提案里留名，不得因本 change 落地而被当成已覆盖 （参照 browse-session.ts:568-597 + humanize/timing.ts:113-126：反射采样消竖直左壁尖峰、间隔与犹豫取 max 不相加 — 见 oracle.md ⑩）

## 5. aidcp-edge — Native 定位三道闸

- [ ] 5.1 在 Native 侧建立共享的解析—执行—后置校验编排：写动作后按同一绑定目标读回业务结果，无证据只报诚实的未开始 / 不确定 （参照 src/locating/engine.ts:213-235 执行后重取根再校验；判据分家见 flows/like-post.ts:27-75、publish-post.ts:203-251 — 见 oracle.md ⑫⑬）
- [ ] 5.2 实现有界重试与升级：可重放的写在未达上限时继续尝试；不可重放的写一经派发即停手报不确定、绝不重放；升级结论只在上限耗尽时给出 （参照 engine.ts:137-264：3 轮重试 + no_target / systemic_revision / llm_unavailable 三态终局 — 见 oracle.md ⑮）
- [ ] 5.3 升级语义与尝试计数的实现点在 `native/page-engine/src/xhs-command-router.js`，该文件是并行 change `restore-native-xiaohongshu-action-honesty` 的单写区：**本 change 不改该文件**，只与其属主对齐落地方式（在文件内修正、或以删除该 v1 分支达成），并把结论与对应 sha 写回本清单；1.6 的合约测试按属主落地后的形态转绿 （参照 locating/types.ts:138-148 的升级三态枚举；旧口径下 escalated 须连续 3 次校验失败 — 见 oracle.md ⑮）
- [ ] 5.4 实现锚点暂存区与晋升阈值：非确定性来源得到的新锚点先暂存，连续确认成功达阈值才进主缓存 （参照 cache.ts:89-116 暂存/阈值 2/晋升；⚠️ 旧缓存纯进程内、snapshot 零调用方，持久化须重新设计 — 见 oracle.md ⑯⑲）
- [ ] 5.5 实现反污染丢弃：任一次后置校验失败即把相关暂存锚点丢弃，且不得被后续解析当作已确认复用 （参照 cache.ts:119-121 dropStaged + engine.ts:238-243「校验失败即丢弃且强制换路径」 — 见 oracle.md ⑯）
- [ ] 5.6 逐条盘点当前 Native 命令面，标出哪些已具备后置校验、哪些暂不具备并注明原因；不具备的不得默认返回成功 （参照 engine.ts:39-41 校验器是接口式强制、缺判据即编译不过；判据强度反例见 oracle.md ⑬⑭）
- [ ] 5.7 **只读**确认 `scripts/prune-production-dist.mjs` 的禁入表未被放宽（该文件归 `enforce-native-engine-artifact-gates`，本 change 不改一行），退役的 TypeScript 定位层与锚点缓存仍不进生产产物
- [ ] 5.8 记录本 change 对迁移主 change 3.2 的承接边界：只承接三道闸，可见性 / 几何 / 歧义拒绝仍归各平台目标解析能力；3.3 的文件输入那一半也不在本 change 内 —— 两条都不得因本 change 落地而被整条勾掉 （本 change 未承接的参照条目：匹配唯一性闸 / 守卫层 / 模型兜底 / 语义 class 白名单 / 可换接口 — 见 oracle.md 覆盖漏洞）
- [ ] 5.9 给后置校验判据立**强度下限**（5.1 只要求「有校验环节」，一条宽松子串正则即可满足其字面）：状态翻转只认属性白名单等于真值（可访问按下态 / 选中态 / 站点稳定的已点赞与已选中属性），类名只认词边界匹配出来的语义片段（片段须是整个 class token，或被连字符 / 下划线包裹），并沿祖先做有限层级回溯（翻转可能落在包裹容器上）；**MUST NOT** 用宽松子串正则判「已生效」，也不得用单个汉字（如「已」）作文本兜底。没有实测锚点的判据一律 fail-closed 诚实失败 （参照 flows/like-post.ts:27-60 属性白名单 + 3 层回溯、publish-command-handlers.ts:346-360 封面判据 fail-closed；现状反例 `xhs-command-router.js:52`、`:233`、`:287` — 见 oracle.md ⑬⑳）
- [ ] 5.10 禁止**自证循环**：后置校验读回的证据不得是本命令自己刚写进页面的那段文本。文本类结果的校验须走结构信号 + 精确相等（去前导标记、去空白、大小写归一，并剔除隐藏后缀），不得对整段编辑器文本做包含判断 （参照 publish-post.ts:255-294 真话题标记判据：只认带话题属性的真标记、精确相等；现状反例 `xhs-command-router.js:256` 读回的正是自己刚写入的文本 — 见 oracle.md ⑭）
- [ ] 5.11 按 5.9 / 5.10 逐条盘点现存后置判据（小红书注入路由 8 处、Facebook 加群的有界轮询复查、其余靠一次 sleep 后复读的分支），标出达标 / 不达标；不达标且实现点落在他人单写区（`xhs-command-router.js` 归 `restore-native-xiaohongshu-action-honesty`）的，只与属主对齐落地方式并回写 sha，本 change 不代改 （参照 engine.ts:39-41「校验器是接口式强制、缺判据即编译不过」 — 见 oracle.md ⑫）

## 6. aidcp-edge — 仓内验证

- [ ] 6.1 运行 Rust 单测与假 CDP 测试（`cargo test --locked`），记录通过数
- [ ] 6.2 运行 `cargo fmt --check` 与 `cargo clippy -- -D warnings`
- [ ] 6.3 运行 `npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）
- [ ] 6.4 运行 `npm test` 全量与 `npm run typecheck`
- [ ] 6.5 运行 `npm run build:dist` 并确认生产产物剪枝检查通过、禁入表未放宽
- [ ] 6.6 记录 Edge 与控制仓的提交 sha、偏离说明、与并行 change 的重叠文件（sha 必须取自已推送的提交）
- [ ] 6.7 集成前按 design 的重叠文件表逐行核对：`input.rs` / `browse-session.ts` / `command.rs` / `runtime.rs` / `engine.rs` 五处属多流共写，先 fetch + rebase 到各属主最新提交再跑 6.1–6.5；push 遇 non-ff 一律 rebase 重来，绝不 force

## 7. 验证与验收

- [ ] 7.1 运行 `openspec validate restore-native-actuation-humanization-and-locating --strict`
- [ ] 7.2 【真机验收项】在 dev 真机上用测试分组账号确认：恢复时间指令消费后，一次浏览闭环不会因单命令墙钟变长触发会话看门狗；记录实际的单命令耗时分布与看门狗阈值余量
- [ ] 7.3 【真机验收项】在 dev 真机上确认：改为有界步进后，首页点赞的对齐滚动仍能在现有轮次上限内把控件带进可视带；若不足，记录实测轮次并单独调整上限 （参照 like-executor.ts:346-356 的有界滚动与诚实不可见结论 — 见 oracle.md ⑧）
- [ ] 7.4 【真机验收项】在 dev 真机上确认：指针原语改为多帧轨迹后，Facebook 首页点赞、评论提交、加群按钮三条路径的成功率不低于改动前；两步点赞的第二步（反应浮层「赞」项）仍能提交 —— 重点看多帧轨迹是否会在移动途中划出浮层 hover 区致其收起，这是本改动唯一有理由怀疑会新增失败的路径 （参照 like-executor.ts:360-387：浮层「赞」项 in-page click 会返回已点却不生效，真机 A/B 实证 — 见 oracle.md ⑪）
- [ ] 7.5 【真机验收项】在 dev 真机上确认：短视频兜底滚轮改用共享手势后，推进仍可用且未出现"测不到移动却报推进" （⚠️ 旧 Reels 也无位移实测，此条无参照物、须新建 — 见 oracle.md ⑨）
- [ ] 7.6 【真机验收项 / 未坐实】"当前节奏与手势特征已被平台判别"这一因果无法在代码里坐实，只能通过真机上的限流信号频次做前后对照观察；本 change 只按已归档的节奏与反检测规格恢复应有行为，不主张判别因果
- [ ] 7.7 【真机验收项 / 未坐实】锚点暂存与晋升在 Native 侧恢复后，实际能带来多少定位命中率提升无线上数据支撑；上线后按定位失败原因分布做一次前后对照
- [ ] 7.8 记录本 change 明确未做的事：未打安装包、未部署 dev/ol、未改云端节奏中心值、未代改迁移主 change 的 tasks.md
- [ ] 7.9 把 7.2–7.7 的真机项登记进 `docs/real-machine-acceptance-backlog.md` 的对应簇
- [ ] 7.10 登记 **运营真机鼠标轨迹回放通道** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**（本 change 只做 2.10 的「丢弃可观测 + 回放模式不得硬编码」那一半）
- [ ] 7.11 登记 **小红书注入路由的通用点击助手（瞬移滚动 + 伪造指针移动）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **restore-native-xiaohongshu-action-honesty**（该文件的单写区属主；本 change 只在规格层立跨平台要求并改 Facebook 那一半）
- [ ] 7.12 登记 **话题标记后置判据（真标记 + 精确相等 + 剔隐藏后缀）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **restore-native-xiaohongshu-action-honesty**（本 change 只在 5.10 立「禁自证循环」的跨平台判据要求）
- [ ] 7.13 登记 **动作前守卫层（干扰扫描 + 多轮清障 + 停手终局）** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**
- [ ] 7.14 登记 **语义类名白名单的词边界匹配与匹配唯一性闸** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **需新立 change**（与匹配唯一性闸同批）
- [ ] 7.15 登记 **按边缘标识派生的每机节奏偏置** 为本 change 范围外项，已在 design.md Non-Goals 具名交接给 **harden-native-engine-runtime-contracts**（会话身份入参的属主）
- [ ] 7.16 【阻塞：待裁定 P1】锚点暂存区的前提在新引擎里不成立（无任何非确定性锚点来源），裁定「保留空结构 / 改判据 / 暂不做」之前，5.4 / 5.5 与 `native-locating-gates` 的锚点要求不得开工，也不得按「已实现」勾掉；裁定结论写回 design.md「待裁定」小节
- [ ] 7.17 【阻塞：待裁定 P2】可换的页面来源与执行层两个接口在迁移中消失，1.3 / 1.4 / 1.5 与 5.1–5.5 的断言方式取决于裁定结果（在 Native 侧重建可替换缝 / 接受退化为真机验收）；裁定前不得把这些任务的验证方式定稿，也不得默认它们能脱机跑；裁定结论写回 design.md「待裁定」小节
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
