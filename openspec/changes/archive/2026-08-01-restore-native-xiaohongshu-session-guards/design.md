## Context

### 现状（已在代码里坐实）

- **阻断监测只服务 Facebook**。Native 浏览会话的周期探针在 `aidcp-edge/src/native-page-engine/browse-session.ts:459-466` 一开头就判平台，非 Facebook 直接不启动；观测函数 `:491-492` 同样第一行返回。全仓 `src/` 里活着的阻断上报只有两处，都在这条 Facebook 通路上（`:538` 清除、`:555` 检出）。另一处 `src/main.ts:1089/1117` 位于恒假分支内，不执行。
- **退役监测体的引用状态并不一致，清理时必须分开对待**（实测于 HEAD `9cd7691`）。`IdentityWatcher`（`src/browse/identity-watcher.ts`）与 `CdpLoginModalWatcher`（`src/browse/login-modal-watcher.ts`）在 `src/` 里除自身源文件外零引用；`WatcherSupervisor` 与 `createOverlayReportGate` 只被恒假块及其影子声明（`src/main.ts:101` / `:103`）引用。但 **`OverlayMonitor` 不是孤儿**：它仍是活着的类型，`PlatformDriver` 接口至今声明 `createOverlayMonitor(cdp): OverlayMonitor`（`src/platform/driver.ts:57`），小红书 driver 仍返回真实实现 `new CdpOverlayMonitor(cdp)`（`src/xhs/driver.ts:25`），Facebook driver 返回 native-only 桩（`src/facebook/driver.ts:22` / `:58`），另有十余个 `src/facebook/*.ts` 以类型形式引用它。真正为零的是**调用**：全仓没有任何一处调用 `platformDriver.createOverlayMonitor(...)`，恒假块里的唯一构造点（`src/main.ts:1052`）用的还是 `new FacebookOverlayMonitor`。因此删除恒假块 MUST NOT 顺手删 `src/browse/overlay-monitor.ts`——那会连带打断活着的 driver 接口。迁前 `317cd47^:src/main.ts` 的小红书装配段同时建这三个看护体（`:1281` 浮层监测、`:1389` 上报闸、`:1406` 看护托管、`:1431` 登录墙、`:1435` 身份看护）。
- **Rust 侧仍在算阻断信号，但小红书无消费者**。`native/page-engine/src/probe.rs:150-156`（`classify_page`）依 `login_wall_count` / `captcha_signal_count` 判 `PageKind::Login` / `PageKind::Captcha`，小红书页面探针 `xhs-page-probe.js:12-21` 产出这两个计数。而带语义的 `blockingKind` / `blockingText` 只有 Facebook 路由产出（`facebook-router/90-dispatch.js:46`），`probe.rs:137-138` 对其它平台恒为 `None`。
- **提交窗口只有 Facebook 会请求**。Rust 侧真正开窗的唯一函数是 `facebook/shared.rs:352` 的 `enter_facebook_commit_window`（也是 `CommitWindowRequester::enter` 的唯一调用点），其调用方三处、全在 Facebook：`facebook/comment.rs:226`、`facebook/publish.rs:791`、`facebook/group_join.rs:179`；窗口契约同样是 Facebook 专属常量（`facebook/capability.rs:36-47`：`fb_join_click` 18.5s / `fb_comment_enter` 20s / `fb_publish_submit` 20s）。小红书执行入口 `execute_xhs_command_once`（`engine.rs:598`）的签名里根本没有 `commit_windows` 参数——对比同一 `match` 的 Facebook 分支在 `:590` 把它传了下去。宿主侧 `browse-session.ts:237-239` 只在平台是 Facebook 时传处理器；发布侧 `src/native-page-engine/publish.ts:56-57` 虽然平台无关地传了处理器，但小红书没有任何一条命令会发起请求，等于空接。迁前小红书有四处窗口，标签与预算已在 `317cd47^` 逐处坐实：`xhs_comment_submit` **4 000ms**（`317cd47^:src/browse/browse-session.ts:2578`）、`xhs_notification_comments` **20 000ms**（`:3104`）、`xhs_notification_likes` / `xhs_notification_follows` **20 000ms**（`:3158`），以及发布提交 `xhs_publish_submit` **15 000ms**（`317cd47^:src/flows/publish-command-handlers.ts:1372` 与 `:1388` 两处，窗口由 `317cd47^:src/main.ts:848` 注入的 `publishGuard` 提供）。发布这一处的预算是 15s 而非 20s——20s 是 Facebook 的 `fb_publish_submit`，两者不可混用。
- **协助键入取证按请求推断**。`src/main.ts:1015` 把 `inputMode` 写成「请求里带没带 text」，与是否真打字无关；协议里定义的 `typeReport`（`src/comm/protocol.ts:1264-1277`，注释明写「绝不写 `typed || text.length`」）在 Native 路径一次也不发。云端 `aidcp-cloud/src/comm/captcha-assist.ts:259` 的版本偏斜探测读的正是 `inputMode`，于是恒不触发。Rust 的打字实现本身诚实（`engine.rs:1318-1373` 逐段返回 `captcha_input_not_focused` / `captcha_input_not_clean` / `text_readback_mismatch` 等结构化原因），但回执壳 `engine.rs:1434-1450` 只带 `ok` + `reason`，取证字段无处可放。
- **排障证据不对称**。唯一一行逐命令回执诊断在 `browse-session.ts:349-357`，被平台判据包住；在场感事件的产出点（`:291`、`:321`、`:543`、`:572` 及 `emitFacebookAction` / `projectFacebookCardActivity` 全体）同样只在 Facebook 分支。
- **恒假短路**。`src/main.ts:1043` 起到 `:1213` 止约 171 行宿主装配位于 `if (false && platformDriver.runtimeKind === 'browser') {` 内（该条件由 `4f04e9c`、2026-07-23 引入，`git log -S` 唯一命中），文件头 `:88-105` 用 `type X = import(...)` + `declare const X: typeof import(...)` 造影子声明（注释 `:88-90` + 2 条 `type` + 11 条 `declare const`，末条 `captureBlockingOverlaySnapshot` 跨 `:104-105`），注释自称「Review-only declarations for the compile-time-unreachable legacy assembly」。块内含浮层监测、上报闸、看护托管与 CDP 生命周期挂钩、评论/加群执行器与处理器、Facebook 会话装配与页面命令处理器注册。

### 机械约束

- 页面规则必须留在编码后的 Native 产物内（防反编译是这次迁移的动机），因此**不能**把退役的 TypeScript 浮层监测原样搬回宿主：那需要在 TypeScript 里重新持有原始 CDP 句柄并写回可读的页面判据。
- 提交窗口的开窗时刻在写入动作的正前方，而写入动作现在整段发生在 Native 引擎内部，宿主无从知道那一刻——窗口请求只能由执行体发起。
- 协议的 `MessageType` 穷举守卫只护消息类型不护字段；本 change 只填既有可选字段，因此**没有任何机械闸**会替我们发现字段没接上，必须靠逐字段往返断言。

## Goals / Non-Goals

**Goals**

- 小红书恢复「检出阻断 → 本地停手 → 上报云端 → 自愈后配对上报清除」的既有语义，并保持 `detected` / `cleared` 严格配对。
- 小红书四处不可逆写入恢复提交窗口保护，窗口请求由执行体发起；拿不到窗口即诚实判未开始。
- 运行期身份校验恢复成「真的在跑的周期校验体」，而不是启动与唤醒各读一次。
- 验证码协助回执的键入取证来自真实执行体，`inputMode` 只反映实际动作。
- 逐命令回执诊断与会话生命周期诊断平台中立。
- 恒假短路的宿主装配被清除，且清除动作逐条对账、有机械闸防复发。

**Non-Goals**

- 不给小红书补在场感 / 陪伴界面事件。迁移前小红书也没有，这不是本次回归；本 change 只要求排障级诊断对称，不要求产品级在场感对称。
- 不重建退役的 TypeScript 浮层监测体（`overlay-monitor.ts` / `login-modal-watcher.ts` / `identity-watcher.ts`）的实现形态；只恢复其对外行为义务。
- 不改 Facebook 的阻断分类、限流词库与告警语义。
- 不改协议消息类型、云端风控状态机与配额。
- 不含部署、出安装包、真机写动作。

**分派简报里明确不由本 change 承接的条目（逐条具名去处，不留静默漏项）**

| 简报条目 | 去处 | 为什么不在这里 |
| --- | --- | --- |
| 小红书开帖是否真落 404（需真机看地址是否带令牌、详情正文是否为空） | `restore-native-xiaohongshu-action-honesty` | 属「开帖判据 / 动作回执诚实」，落点在 `xhs-command-router.js`——本 change 的显式禁改区 |
| 看图命令导致深读永久挂起、直到会话看门狗杀场 | `restore-native-xiaohongshu-action-honesty` | 同上，属看图命令的回执与超时口径；本 change 不改任何命令的执行语义 |
| 小红书通知去重键折叠 / 行选择器退化的后果规模 | `restore-native-xiaohongshu-action-honesty` | 属未读的抽取与去重口径；本 change 在通知巡视上只管「那段消费不可被抢占」 |
| Facebook 热度恒 0（中性按钮正则） | `restore-native-facebook-residual-parity` 等 Facebook parity 系列 | Facebook 页面规则与读数判据由那批 change 独占；本 change 对 Facebook 判据逐位不变 |
| 四处「找不到就退回文档主体」的空根塌陷 | `harden-native-engine-runtime-contracts` | 属引擎运行时契约的定位根收窄，与会话看护 / 写入保护不同层 |
| CI 上实际生效的 Rust 编译器版本无法事后对账 | `enforce-native-engine-artifact-gates` | 该 change 的范围已含「把 Rust 格式化 / 静态检查 / 测试做成解析钉死工具链的仓内脚本并纳入集成闸」，正是这条的归口；与本 change 四个能力零交集 |
| 跨环境错投（重连复用旧 CDP 端点） | 已有记忆条目 `captcha-assist-base-url-cross-env` 所述问题域；本 change 不认领 | 根因在端点解析与重连，不在会话看护；本 change 不动端点获取 |
| 七个簇里「维持原判」的条目只有编号没有正文（F-IPC-*/INJ-*/TXT-*/PACE-*/GEST-*/TIME-*/RETRY-*/PLAT-OBS-*/BUILD-*/DRIFT-*） | 不认领；须由发起分派的一方先补齐正文再并案 | 无正文即无法判定归属，凭编号推断会制造错标与重复劳动。本 change 不据这些编号做任何推断 |

**合并退役实现参照书时查出、明确不由本 change 承接的覆盖漏洞（逐条具名，不留静默漏项）**

| 漏洞是什么 | 为什么不在本 change 做 | 建议由谁承接 | 不做的后果 |
| --- | --- | --- | --- |
| 验证码协助除「键入取证」外的其余 9 项全无覆盖：回放模式写死合成、轨迹回放整体缺席、点击拟人节奏退化成固定 80ms 等距（无抖动 / 无过冲 / 无落点前读图停顿 / 无点间对数正态停顿 / 无光标连续性 / 无每机偏置）、带文本时「落点必须恰好一个」的注入前预检缺席、回放前的陈旧状态复检缺席、抓帧前的阻断前置复检缺席、快照裁剪恒为整视口且类型恒标验证码、实时抓帧从不发「验证码已清除」且无「连续 3 次无遮罩才判清除」、点击期间与抓帧无互斥、提交后从「4 次有界复检」退成单次探测 | 本 change 在协助链路上只认领一件事：让键入取证由真正派发字符的执行体产出（D4），宿主逐字段透传。上列 9 项横跨注入拟人化、轨迹回放、抓帧循环与清除判定四个子系统，面积远大于取证透传，且多数要改 Rust 注入层与抓帧循环——与本 change「宿主装配 + 执行入口签名 + 回执字段」的改动面不同层。它们也不是新能力，而是**已上线要求在 Native 路径上的整体回归**（`captcha-incident-handling` 已合并的「验证码可交互态必须近实时回传现场帧」「远程协助可复刻运营真实鼠标轨迹」「协助注入点击必须达到不低于日常点击的合成拟人度」三条） | 需新立 change（建议名 `restore-native-captcha-assist-humanization`）。**不**由 `restore-native-actuation-humanization-and-locating` 顺手带：那个 change 的面是浏览动作的手势与定位，不含协助链路的抓帧循环与清除判定 | ① 协助注入退回全 fleet 逐字相同的固定节奏（80ms 等距、无轨迹、无过冲），这恰恰是反爬审查最严、专门拿鼠标轨迹熵做指纹的场景；② 实时抓帧永不发清除信号，账号停在受限档等人工；③ 快照不裁剪且类型恒标验证码，运营看整视口图、非验证码类阻断被误标；④ 提交后单次探测撞上回车触发的导航会被算成「仍被阻断」。四条都是真机上可观察的坏结果，不是理论风险 |

## 关键决策

### D1. 小红书阻断观测复用 Native 周期探针，按平台装配，而不是搬回旧监测体

把 `browse-session.ts` 的周期探针与观测函数从「平台等于 Facebook 才跑」改成「按平台取一份分类适配」，小红书用 Native 页面探针已产出的页面类型（`captcha` / `login`）驱动上报与本地停手。

- **被否方案 A：把 `platformDriver.createOverlayMonitor` + `createOverlayReportGate` + `WatcherSupervisor` 那套原样接回宿主。** 否决理由：它要在 TypeScript 里持原始 CDP 句柄并注入可读页面判据，与迁移的防反编译动机直接冲突；且这批模块正是本 change 要清除的恒假块的居民，接回去等于把刚要拆的东西重新钉牢。
- **被否方案 B：让 Rust 侧自主向云端推阻断事件。** 否决理由：上报闸的语义（低置信延后确认、`detected`/`cleared` 严格配对、与云端暂停的互动）是宿主与协议层的事，宿主已实现过一次；在 Rust 里再实现一份，等于把「诚实」这件事的面积翻倍，两份还会各自漂移。

### D2. 小红书低置信「未知阻断」桶：声明缺席，不用「页面类型识别不出」冒充

Facebook 的 `unknown` 阻断来自专门的阻断分类器（含尺寸 / iframe / 文案启发式）。小红书目前没有对应分类器；页面探针的 `PageKind::Unknown` 含义是「这是一个我没认出来的页面」，与「这是一堵我认出来但归不了类的阻断墙」完全不同。

因此本 change 只恢复 `captcha` 与 `login` 两桶，并把「不得由 `PageKind::Unknown` 生成阻断上报」写成 MUST NOT。低置信桶留作后续 change（需要在小红书页面规则里新增阻断分类器 + 有界证据文案），在那之前边缘对该桶的能力是**已声明的缺席**。

- **被否方案：把 `PageKind::Unknown` 直接映射成 `kind:'unknown'` 上报。** 否决理由：这会把每一次页面识别失败都变成一次账号降级（云端 `unknown → light → warned`），是一台误报机；误报代价是账号被限速直到人工恢复。

### D3. 提交窗口由执行体请求，宿主只做仲裁

小红书执行入口接收提交窗口请求器，在四处不可逆写入的正前方开窗（沿用迁前的标签与预算量级），窗口关闭在终态。宿主侧把窗口处理器的注入从「仅 Facebook」改为平台无关。

- **被否方案 A：宿主在下发命令前后包一层窗口。** 否决理由：命令粒度远大于写入粒度，包整条命令会把导航、定位、等待都算进不可抢占段，等于把「不可逆写入保护」偷换成「命令期间禁抢占」，抢占能力事实上失效。
- **被否方案 B：不做，理由是「写命令不做飞行中取消，所以现在也撕不裂」。** 否决理由：这是运气不是设计。当前后果已经是可观察的坏结果（抢占方在提交进行中发起接管、等不到原子边界后抛错）；且一旦给写命令加协作取消，同一处立刻变成真撕裂。
- **窗口不可得时的行为**：与 Facebook 侧已确立的口径一致——写入 MUST NOT 开始，回执诚实标未开始，而不是「先写了再说」。

### D4. 键入取证由 Native 执行体产出，宿主逐字段透传，`inputMode` 只反映实际动作

Native 验证码回执补上焦点分级、清空三态、实际派发字符数、回读三态、是否已提交这五类事实；宿主把它们原样填进回执的既有可选字段，并只在**确有字符被派发**时才标 `click_type`。

- **被否方案 A：维持按请求推断（现状）。** 否决理由：这正是缺陷本身——云端那道「下发了文本却只点了击」的探测器被永久关掉。
- **被否方案 B：宿主在动作后回读字段自证。** 否决理由：提交后页面常已导航，回读必然假阴性（这正是既有要求「提交后判据不可得不得报成失败」所治的病）；且回读需要在 TypeScript 里写页面判据，与 D1 同一约束冲突。
- **取证缺席时怎么办**：宿主 MUST NOT 用 `click_type` 顶上。让云端探测器如实报「键入未执行」比伪造一次成功好——这正是那道闸存在的意义。

### D5. 运行期身份校验复用同一条周期观测通路

当前身份只在启动（`src/main.ts:350`）与浏览器唤醒（`:1389`）各读一次，两次之间换号或掉登录不会被发现。恢复方案是把身份重读挂到与阻断观测同一条周期通路上：按既有分域判据判「健康 / 换号 / 登出 / 无法确认」，连续达阈值才判失效。

- **被否方案 A：接回退役的 `IdentityWatcher` 实现。** 否决理由：它按注入的原始 CDP 句柄工作，与 D1 同一约束冲突；且其读身份函数在小红书侧是 TypeScript 页面判据。
- **被否方案 B：不做，靠每次唤醒重读兜底。** 否决理由：长跑会话可以几小时不唤醒，「持续校验」在那段时间事实上不存在；而换号会让两个账号的上下文串味，这是既有要求明令禁止的。

### D6. 恒假装配一律清除，并加机械闸防复发

删掉 `src/main.ts:1043-1213` 与 `:88-105` 的影子声明；删之前逐条对账块内每项能力，落成两栏结论：**已有 Native 归属**（写清落点）或**已登记缺口**（进本 change 的 tasks 或真机验收 backlog）。同时加一道源码级检查，禁止再次出现「静态恒假的装配入口 + 为已剪枝模块造的 `declare const` 影子声明」这种组合。

已有的第二道闸可以直接复用作背靠：`scripts/prune-production-dist.mjs` 的 forbidden 清单已含 `facebook/overlay.js` / `facebook/facebook-session.js` / `facebook/comment-executor.js` / `facebook/comment-handler.js` / `facebook/join-executor.js`——正是恒假块引用的那批模块。因此「把块改成运行期旗标从而使入口不再静态恒假」这条路会在打包时被这道 pruner 当场拦下并点名文件；缺的只是**源码级**那一道（恒假条件与影子声明本身，pruner 看不见，因为它们从不进 dist 的导入图）。注意 pruner 的 forbidden 清单里**没有** `browse/overlay-monitor.js` / `browse/watcher-supervisor.js` / `browse/overlay-report-gate.js` / `browse/identity-watcher.js` / `browse/login-modal-watcher.js`，所以「把旧监测体接回宿主」不会被 pruner 拦——否决方案 A 的理由是防反编译动机与 CDP 句柄约束，不要误记成「打包闸会拦」。

- **被否方案 A：留着当参考（现状）。** 否决理由：它提供的不是参考而是错觉——块内每一条能力是否还有人承接，只能靠人肉比对，且没有任何一道闸会提示。代价已付过一次：块内的 Facebook 软限流上报直到 `54ae5b2`（07-26）才在 Native 会话补回。
- **被否方案 B：改成环境变量开关，保留可回退路径。** 否决理由：那会造出真正的 JavaScript 回退路径，与「不双跑、不比对、不回退」的既定口径冲突，也会把页面规则重新塞回安装包。
- **被否方案 C：只删恒假条件、把块内代码搬进注释。** 否决理由：注释同样无信号，且会随时间腐烂成误导。对账结论进 tasks 与 git 历史即可，代码不留尸体。

### D7. 小红书的动作前闸只认两桶；探测失败才保守拒绝

（任务 1.7）Facebook 的动作前闸把 `login` / `captcha` / `unknown` 三桶都判成拒绝（`facebook/shared.rs:407-411`）。小红书 MUST 只认 `captcha` 与 `login` 两桶：页面类型未识别（`PageKind::Unknown`）MUST NOT 拒绝动作——理由与 D2 同源，那不是「我看见一堵墙」，而小红书的页面识别失败在看图态、AI 搜索结果页、详情弹层上都会发生，照抄三桶等于把「没认出来」变成「所有互动都不做了」。

探测**本身失败**（拿不到判定）是另一回事：MUST 保守当成有挑战、放弃这次派发。错过一次点赞很便宜，点进风控墙很贵。

- **被否方案：照抄 Facebook 三桶。** 否决理由见上——那是一台把识别失败当阻断的误报机，且这一次误报的表现是互动整体停摆。
- **注意一处方向相反、且有意为之的既有口径**：验证码协助的清除判定至今把 `Unknown` 计入「仍被阻断」（`engine.rs:1422-1425`）。那是同向诚实（宁可不宣布清除），与本条（宁可不拒绝正常动作）不冲突，详见 Open Questions 末条。

## 风险与回滚

- **小红书阻断误报**：`captcha` 桶用的是厂商指纹类选择器（`xhs-page-probe.js:21`），历史上召回高误报低；但周期探针一旦开在小红书上，任何误判都会直接暂停该 edge。缓解：只放开 `captcha` / `login` 两桶（D2），并保留既有的严格配对语义使误报可自愈。真实误报率需真机观察，已列为验收项。
- **提交窗口令抢占变难**：小红书四处开窗后，高档位任务在这些窗口内会拿到「窗口占用中 + 剩余预算」而非立即接管。这是既定设计（保护不可逆写入），但会抬高一次抢占的等待上界至窗口预算量级。缓解：沿用迁前的预算量级，不新增更长的窗口。
- **取证字段两侧漂移**：只填既有可选字段，`MessageType` 穷举守卫抓不到漏接。缓解：逐字段往返断言（既有要求「扩载荷字段不漂移」已有此约束，本 change 只是把它落到这条链路上）。
- **删除恒假块误伤**：块内可能有尚未发现的、仍被别处依赖的副作用（如 CDP 生命周期挂钩）。缓解：删除前先逐条对账并跑全量 + typecheck；块内代码本就不执行，删除不改变运行时行为——真正的风险在对账遗漏，而对账结论必须逐条落进 tasks。
- **回滚**：本 change 只落 edge 源码，回滚即回退对应提交；无数据迁移、无协议迁移。

## 与其他并行 change 的边界

- **不碰** `aidcp-edge/native/page-engine/src/xhs-command-router.js`（另一 change 的单写区）。本 change 对小红书页面规则零改动；阻断分类沿用页面探针已有产出。
- **不碰** `native/page-engine/src/facebook/**` 与 `native/page-engine/src/facebook-router/**`——Facebook 能力边界由 `preserve-native-facebook-capability-boundaries` 与几个 `restore-native-facebook-*` change 独占。本 change 对 Facebook 行为的唯一影响是「把只判平台的那层壳改成按平台装配」，Facebook 分支的判据与语义逐位不变。
- **`native/page-engine/src/engine.rs` 是热点文件**（多个 Facebook parity change 也在改）。本 change 只动两处：小红书执行入口的签名与窗口请求、验证码回执的取证字段。集成时须先 rebase 到最新默认分支再跑聚焦测试。
- **`edge-task-execution-coordination` 能力另有五个活跃 change 触碰**（实测 `ls */specs/edge-task-execution-coordination`：`browser-slot-cloud-presence`、`browser-slot-scheduling`、`separate-client-data-plane-automation-engine`、`native-page-engine-platform-cutover`、`native-page-engine-production-cutover`）。本 change 在该能力下只新增一条要求（小红书不可逆写入开窗）、只重述一条既有要求（通知巡视窗口），与槽位调度 / 数据面拆分 / 切换叙事的要求标题零重叠。
- **`captcha-incident-handling` 能力另有 `captcha-assist-base-url-self-proof` 触碰**。已逐条比对标题：它 ADDED 两条（协助链接外部基址自证、判死只停按钮）、MODIFIED 两条（飞书告警的云端处理入口、告警创建可远程协助 incident），与本 change 的两条 ADDED 与一条 MODIFIED（`协助键入的证据必须分级诚实`）标题零重叠。语义上互补而非冲突：它管协助链接能不能签发，本 change 管协助执行完之后回执说不说实话。
- **`account-identity-resolution` 另有 `platform-specific-identity-commands` 触碰**，但那个 change 只改两条昵称采集要求（`昵称采集只在完整浏览器启动后的首个 feed 卡片触发`、`Facebook 启动握手昵称刷新不依赖 feed 卡片产出`），与本 change 重述的「身份可翻转，须持续校验」不重叠。
- **`restore-native-xiaohongshu-action-honesty`（并行 change）独占小红书页面规则与动作诚实**（评论合成文本、开帖判据、看图回执、通知去重键与行选择器等），它的能力是 `native-xiaohongshu-behavior-parity` 与 `notification-monitoring`。本 change 与它零文件重叠：它改页面规则里「动作怎么做、回执怎么说」，本 change 改宿主与执行入口的「会话怎么被看护、写入期间怎么被保护」。通知巡视是两者最近的接触面——它管未读的抽取与去重口径，本 change 只管那段消费不可被抢占，互不改对方的判据。
- **`restore-native-actuation-humanization-and-locating` / `harden-native-engine-runtime-contracts` / `restore-native-facebook-residual-parity`（并行 change）** 的能力与本 change 四个能力全不相交；三者都会动 `engine.rs`，集成时按热点文件串行。
- **`native-page-engine-production-cutover`（迁移主 change，42/51 仍活跃）** 拥有整体切换叙事。本 change 是它遗留缺口的定点修复，不改它的 `native-page-engine-production` 能力 delta；`openspec/specs/native-page-engine/` 是可行性验证阶段的只读探针规格，本 change 不往里塞生产行为要求。

## Open Questions

- 小红书低置信 `unknown` 阻断桶的分类器（对应 Facebook 侧的形状 / iframe / 文案启发式）需要一次单独设计，落在页面规则侧；本 change 只把它的缺席声明清楚。
- 小红书运行期身份看护的轮询周期与防抖阈值是否沿用迁前默认（30s / 连续 2 次），需真机观察一次误退率后再定档。
- **`PageKind::Unknown` 在两处的口径故意不同，需人确认这个不对称是有意的**：D2 规定「未识别的页面类型 MUST NOT 生成阻断上报」，但验证码协助的清除判定至今把 `Unknown` 当成「仍被阻断」（`native/page-engine/src/engine.rs:1422-1425`：`Captcha | Unknown | Login` 皆判 `still_blocked`）。两者其实同向诚实——**上报侧宁可不报（否则误报一次就降一次账号）、协助判定侧宁可不宣布清除（否则一次识别失败就冒充解除成功）**，各自都朝保守方向倾斜。本 change 不改协助侧那一行；若后续有人为了统一而把协助侧的 `Unknown` 剔出 blocked 集合，那会让「页面没认出来」变成「验证码已清除」，属静默假成功，MUST NOT 这么统一。

## 待裁定（实装前必须有人决定，否则对应任务无法验收）

### 1. 身份翻转 / 重连后「重注入连接级节奏快照」这一步在 Native 形态下归谁（阻塞任务 5.5 的该步；标记任务 5.6）

**要决定什么**：退役实现的身份重立链在重连之后、重启浏览之前，把新的连接级节奏快照（各操作的时长下限与降速档）重新灌进浏览会话（`317cd47^:src/main.ts:1078-1081`，旧注释称这是「设计 §4.3 最严重缺口」的修复）。Native 浏览会话的同名接收点是空实现，注释写明「节奏归云端所有，每条 Native 命令自带已授权的时长字段」（`src/native-page-engine/browse-session.ts:213-218`），且会话对云端下发的节奏更新命令直接返回、不做任何事（`:121`）。因此这一步在 Native 形态下**既没有落点，也没有「不需要落点」的书面依据**。

- **走法甲：在 Native 会话恢复一个真的接收点。** 后果：宿主重新持有一份节奏状态，与「节奏系数收口云端、边缘只叠抖动」的现行归属直接接触，必须同时定清楚谁是中心值权威、以及边缘那份快照与命令自带字段冲突时谁赢；否则同一档位会被算两次（退役的 Facebook 会话就犯过这个重复计数）。
- **走法乙：正式声明该步骤在 Native 形态下不再需要**，依据是每条命令自带已授权时长字段。后果：必须先坐实「风控档位在会话中途升级后，其后每条命令携带的时长字段确实取的是新档位」——本 change 未在代码里坐实这一点，属需核对项（**不得当成既成事实**）。若并非每条命令都带最新档位，则连接级快照在这条唯一的原地重连路径上退化成进程级，风控升级到不了边缘节奏层。

**不裁定会怎样**：任务 5.5 的重立链缺一步且无法验收——既不能实现（没有落点），也不能声明不做（没有依据）。唯一的绕过办法是「悄悄跳过这一步」，而那正是本轮清账要消灭的静默漏项。
