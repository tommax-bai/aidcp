> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — 恢复小红书阻断监测与云端上报

- [ ] 1.1 先加失败在先的聚焦测试：小红书 Native 会话在页面探针回 `pageKind='captcha'` 时必须发一次 `risk.captcha_detected{kind:'captcha'}`，回非阻断态后必须发一次配对 `risk.captcha_cleared`（当前两条断言应先红）（参照 src/browse/overlay-report-gate.ts:1-83；缺 detected/cleared 严格配对 + epoch 作废 — 见 oracle.md）
- [ ] 1.2 把 `src/native-page-engine/browse-session.ts` 的周期探针启动条件与观测函数的平台判据改成按平台取分类适配，保留 Facebook 分支的判据、延后确认与词库语义逐位不变（参照 src/browse/background-watcher.ts:1-131；缺自走时钟骨架/sticky 容错/翻转一次/节拍可配 — 见 oracle.md）
- [ ] 1.3 实现小红书分类适配：`pageKind='captcha'` → `kind:'captcha'` 即时 fail-closed；`pageKind='login'` → 本地停手等登录、不发账号级阻断上报；其余 → 非阻断（参照 src/browse/overlay-monitor.ts:1-231 的五类优先级 + login-modal-watcher.ts:52-58 的 5 条强短语；登录判据已在 xhs-page-probe.js:12-21，只需接线勿重写 — 见 oracle.md）
- [ ] 1.4 加断言：`pageKind='unknown'`（页面类型未识别）MUST NOT 产生任何阻断上报，也不得触发账号风控迁移（参照 oracle.md「不可照抄」第 2 条：旧 unknown 桶判据本身是误报源，声明缺席是正确处置）
- [ ] 1.5 加断言：从未上报过的阻断态自愈时不得发孤儿 `cleared`；已上报过的阻断态自愈必须发一次 `cleared`（参照 src/browse/overlay-report-gate.ts:43-63；缺 episode 世代号令在途确认作废 — 见 oracle.md）
- [ ] 1.6 小红书检出阻断后必须本地暂停普通浏览下发，并在清除后恢复；被暂停期间收到的浏览命令回诚实的未开始，不得静默丢弃（参照 src/browse/browse-session.ts:3391-3451；缺等待循环的三个出口，接管须抛出不可只 return，否则闭环死锁 — 见 oracle.md）

- [ ] 1.7 高危动作提交前补一道即席新鲜复检：小红书的点赞 / 收藏 / 关注 / 评论提交在派发前重探一次页面阻断态，命中验证码即**零派发**、回诚实原因 `blocked_by_captcha`（沿用 Facebook 同名原因码，不新造）；探测**本身失败**按「有挑战」保守拒绝。只读周期观测缓存不够——缓存可能过期约一个节拍，闸门放行到真正点击之间的拟人停顿里弹出的验证码必漏。桶的取舍（只认验证码 / 登录两桶，页面类型未识别 MUST NOT 拒绝）见 design.md D7。验收标准：搬旧测试「点赞命中验证码 → 放弃点击并诚实回执」（参照 native/page-engine/src/facebook/shared.rs:376-412 的动作前闸与 :404 的 fresh 探测；小红书执行入口 engine.rs:598 与 xhs-command-router.js:229/235 的互动分支目前无任何提交前闸 — 见 oracle.md 覆盖漏洞 1）
- [ ] 1.8 把任务 1.6 的停手等待循环写成**三个显式出口**并各加一条回归断言：① 本地停止；② 队列里已到的**会话结束命令必须绕过闸门直接终止会话**（否则登录墙常驻时云端终止不了会话）；③ **任务接管信号到达必须抛出**，令该命令零副作用作废、当场让路，MUST NOT 只返回（只返回会让命令继续对着验证码墙点下去；旧注释点名后果是闭环死锁、整台机器停摆）。现状证据：Native 会话在 `blocked` 时对会话结束命令同样只回 `native_session_quiesced` 的未开始（src/native-page-engine/browse-session.ts:122-126），新增停手闸若沿用同一处理即复现该死锁（参照 src/browse/browse-session.ts:3403-3448 的三出口注释与两条死锁回归测试 — 见 oracle.md 覆盖漏洞 2）
- [ ] 1.9 把周期阻断观测做成有生命周期托管的观测体，而不是一个裸定时器。四项验收：① 执行器连接进入不可恢复终态即停掉全部周期观测、重连后整批重启且启动幂等；② 补「上次成功探测距今多久」的存活度量，使「持续探测失败」与「确实没情况」在外部可区分（MUST NOT 把探测不了当成没情况）；③ 探测节拍可注入 / 可配（现写死 2 秒，src/native-page-engine/browse-session.ts:459-464；旧骨架默认 1 秒且可注入），并显式选定探测失败的容错档（保持上一状态 / 回落初始态）写进断言；④ 待机或启动即暂停时「已装配但暂不启动」留一条可观测记录。现状证据：连接不可恢复只触发执行器隔离并请求冷待机（src/main.ts:1542-1548 → :1500-1511），而冷待机在复用外部浏览器或有活跃租约时直接拒绝（:1317-1323），此时探针不被停、继续对死连接空轮询并每拍打一行失败日志到进程退出（参照 src/browse/background-watcher.ts:34/38/56-58 与 src/browse/watcher-supervisor.ts — 见 oracle.md 覆盖漏洞 3）

## 2. aidcp-edge — 恢复小红书不可逆写入的提交窗口

- [ ] 2.1 加失败在先的测试：小红书评论提交、通知评论栏消费、通知点赞/关注栏消费、发布提交四处在写入派发前必须各请求一次提交窗口。标签与预算沿用迁前实测值（已在 `317cd47^` 逐处坐实，**不得照抄 Facebook 的值**）：`xhs_comment_submit` 4 000ms、`xhs_notification_comments` 20 000ms、`xhs_notification_likes` / `xhs_notification_follows` 20 000ms、`xhs_publish_submit` **15 000ms**（不是 20 000ms——20 000ms 是 Facebook 的 `fb_publish_submit`）。验收标准：四处各有一条断言比对标签字符串与预算数值（参照 src/execution/commit-window.ts:1-75 与四处开窗点 browse-session.ts:2583/3109/3163 + publish-command-handlers.ts:1372 与 :1388（发布是两条开窗点）— 见 oracle.md）
- [ ] 2.2 让 `native/page-engine/src/engine.rs` 的小红书执行入口接收提交窗口请求器，并在上述四处写入的正前方开窗、终态关窗（参照 engine.rs:598 缺 `commit_windows` 形参；真实点击在不许改的 xhs-command-router.js:224/236/272，故只能在 `evaluate_router` 之前开窗、预算须覆盖 router 内后置校验 — 见 oracle.md）
- [ ] 2.3 把 `src/native-page-engine/browse-session.ts:237-239` 的窗口处理器注入从「仅 Facebook」改为平台无关；确认发布侧 `src/native-page-engine/publish.ts` 的处理器注入被真正取用（参照 publish.ts:56-57 已无条件传入但 Rust `publish_submit` 走 evaluate_router、从不请求 ⇒ 处理器空转 — 见 oracle.md）
- [ ] 2.4 加断言：窗口请求被拒或不可得时，写入 MUST NOT 派发，回执标未开始；协调器在窗口内对抢占回「窗口占用中 + 剩余预算」（参照 native/page-engine/src/commit_window.rs:107-112 的 `CommitWindowUnavailable`；小红书现为「无声照写」 — 见 oracle.md）
- [ ] 2.5 加断言：窗口在终态（成功 / 失败 / 超预算）后必须关闭，不得泄漏成永久占用（参照 src/execution/commit-window.ts 两条安全设计：时基兜底自动过期 + 世代守卫防误关 — 见 oracle.md）

## 3. aidcp-edge — 验证码协助键入取证诚实化

- [ ] 3.1 加失败在先的测试：下发了文本但 Native 回执未携带任何键入取证时，宿主 MUST NOT 标 `inputMode:'click_type'`（当前实现按请求推断，此断言应先红）（参照 src/main.ts:1015 按 payload 推断 ↔ 云端探测器 aidcp-cloud/src/comm/captcha-assist.ts:255-262 — 见 oracle.md）
- [ ] 3.2 给 Native 验证码回执补结构化键入取证：焦点分级、清空三态、实际派发字符数、回读三态、是否已提交；失败路径按 `engine.rs` 既有结构化原因逐段映射（参照 src/browse/captcha-assist.ts:445-659；缺 focus/focusTag/cleared/typed/verified/submitted 六字段与「type→read→submit 顺序反了必假阴性」 — 见 oracle.md）
- [ ] 3.3 宿主把取证逐字段透传进 `captcha.assist.click_result` 的既有可选字段；`inputMode` 只在确有字符派发时为 `click_type`（参照 src/main.ts:1007-1015；`replayMode` 亦写死 synthetic，但轨迹回放不在本 change 范围 — 见 oracle.md 覆盖漏洞 4）
- [ ] 3.4 加边到边逐字段往返断言（边缘打包 → 云端解析 → panel HTTP 边界透传），确认没有字段在任一跳被丢（参照 oracle.md 的旧回执字段集；`typeReport` 绝不含答案本身）
- [ ] 3.5 加断言：中途被抢占或超预算时，取证的字符数为实际派发数、不得回退到请求文本长度，且不得执行提交（参照 src/browse/captcha-assist.ts:445-659；`typed` 须由闭包逐字更新——抛出时派发函数内部计数丢失，只有闭包值是真实数 — 见 oracle.md）
- [ ] 3.6 加断言：云端「下发了文本却未键入」的探测器在取证缺席时会触发，在取证齐备且确有派发时不触发（参照 aidcp-cloud/src/comm/captcha-assist.ts:255-262 的 textNotExecuted：textLen>0 且 inputMode≠click_type — 见 oracle.md）

## 4. aidcp-edge — 排障证据平台对称

- [ ] 4.1 把 `browse-session.ts:349-357` 的逐命令回执诊断改为平台中立，输出动作名、成功与否、效果相位、原因码，且原因码继续走既有的诊断 token 白名单收敛（参照旧全链诊断 src/browse/browse-session.ts:3088/3139/3170；缺「未命中 tab 诚实 no_target、绝不无条件报 viewed」这层证据 — 见 oracle.md）
- [ ] 4.2 为每个 Native 浏览平台补会话级诊断：会话就绪、阻断检出 / 清除、为任务让位与恢复、终止原因（参照 src/browse/browse-session.ts:3444 与 :3438「出现/消失各只记一次」；MUST 走结构化行，壳侧兜底正则只认「弹窗/暂停操作」曾让 FB 阻断态恒绿 — 见 oracle.md）
- [ ] 4.3 加断言：一次小红书浏览闭环（滚动 → 开帖 → 互动 → 返回）在日志里逐命令留有回执证据；诊断不得携带页面正文、凭据或选择器（参照现成模板 test/native-page-engine/browse-session.test.ts:157，去掉平台条件即为小红书同款契约）
- [ ] 4.4 明确不为小红书补在场感 / 陪伴界面事件（非本次回归）。验收标准：一条断言固定「小红书会话产出生命周期诊断但不产出陪伴界面事件」这一预期状态，断言注释里写明这是产品范围而非可观测性缺陷，防后续误当缺口重做（参照 oracle.md：旧实现两侧都靠日志措辞点亮运行态，故此处 MUST NOT 退回措辞匹配）

## 5. aidcp-edge — 恢复运行期身份持续校验

- [ ] 5.1 加失败在先的测试：长跑会话在两次启动 / 唤醒之间发生换号或掉登录时，必须被周期校验发现并退回无身份态（参照 src/browse/identity-watcher.ts:1-162；缺 30s 节拍 + `AIDCP_IDENTITY_CHECK_MS`/`AIDCP_IDENTITY_FAIL_THRESHOLD` 两旋钮 + 连续 2 次防抖 — 见 oracle.md）
- [ ] 5.2 把身份重读挂到与阻断观测同一条周期通路上，沿用既有分域判据（消费端读稳定 id / 创作子域用登录门禁 / 其它域判无法确认）（参照 identity-watcher.ts 的分域四态与正向登出探针；缺「只读不导航」与登录浮层作第二判据的接线 — 见 oracle.md）
- [ ] 5.3 加断言：判「无法确认」的那一轮不计入失效防抖计数、不判失效也不判健康，且留下可观测日志（参照 identity-watcher.ts 的 unknown 跳过分支与「创作发布页穿插不得凑够阈值」的跨页计数污染用例 — 见 oracle.md）
- [ ] 5.4 加断言：判失效只 emit 一次转移，退回无身份态前先诚实回执在途发布（参照 `317cd47^:src/main.ts:1035-1102` 的重立链；在途发布须在关连接之前判失败，后半段 8 步本 change 未覆盖 — 见 oracle.md 覆盖漏洞 5）

- [ ] 5.5 补齐身份重立链的后半段（5.1–5.4 做完只能「发现」失效、不能「恢复」）：停全部周期观测 → 停浏览 → **在途发布诚实判失败（MUST 在关连接之前，否则失败回执发不出去）** → 断开云端 → **先导航回消费端首页再读身份** → 读不出即停在无身份态、**绝不回落默认账号（红线）** → 按新 id 换云端会话并重连 → 重设基线 → 重启周期观测与浏览。其中「重连后重注入连接级节奏快照」这一步归属未定，见任务 5.6，本任务先不实现该步、也不得静默跳过（参照 `317cd47^:src/main.ts:1035-1090` 的逐步顺序与红线注释；已合并要求「重新确立身份 MUST 先回到可读身份的页面再判定」与「退回无身份态断连前 MUST 先诚实回执在途发布」已在册，本任务是把它们在 Native 宿主上真正接线 — 见 oracle.md 覆盖漏洞 5）
- [ ] 5.6 **【阻塞 · 待人裁定】** 身份翻转 / 重连后「重注入连接级节奏快照」这一步在 Native 形态下的归属未定：Native 会话的同名接收点是空实现且注释写明节奏归云端（src/native-page-engine/browse-session.ts:213-218），会话对节奏更新命令直接返回（:121）。未裁定前任务 5.5 的该步既无法实现也无法声明不做。裁定项与两种走法各自的后果见 design.md「待裁定」§1

## 6. aidcp-edge — 清除恒假短路的宿主装配

- [ ] 6.1 逐条对账 `src/main.ts:1043-1213` 块内的每项能力（浮层监测、上报闸、看护托管与 CDP 生命周期挂钩、评论 / 加群执行器与处理器、Facebook 会话装配、页面命令处理器注册），每条给出「已有 Native 归属（落点）」或「已登记缺口（去处）」结论，写进本清单（参照 oracle.md 末条：已列出 6 项「无对应物」+ 6 项「已有 Native 归属」，可直接当对账底稿）
- [ ] 6.2 删除该恒假块与 `src/main.ts:88-105` 的类型影子声明（含末条跨行的 `captureBlockingOverlaySnapshot`）；确认删除后 typecheck、剪枝与全量测试仍通过（参照 src/main.ts:88-103 实测 16 行影子声明，块首 :1043 `if (false && …)`、块尾 :1213 — 见 oracle.md）
- [ ] 6.3 加源码级检查：禁止「静态恒假的装配入口」与「为已剪枝模块造的 `declare const` 影子声明」这一组合再次出现，检查失败必须明确指出文件与行（参照 oracle.md「机制性问题」：typecheck 穷举不到、剪枝挡在产物外、单测不覆盖 ⇒ 能力整批静默消失，已付过一次代价 `54ae5b2`）
- [ ] 6.4 确认删除后仓内不再有仅被恒假块引用的孤儿模块；对确已无人引用的退役监测体给出保留或删除的结论并写明理由。**分类先做实，别按「都是孤儿」一刀切**（HEAD `9cd7691` 实测）：`IdentityWatcher` / `CdpLoginModalWatcher` 在 `src/` 里除自身外零引用；`WatcherSupervisor` / `createOverlayReportGate` 只被恒假块与影子声明引用；而 `src/browse/overlay-monitor.ts` 的 `OverlayMonitor` **仍被活着的代码引用**——`PlatformDriver` 接口声明 `createOverlayMonitor`（`src/platform/driver.ts:57`）、`src/xhs/driver.ts:25` 仍 `new CdpOverlayMonitor(cdp)`、十余个 `src/facebook/*.ts` 以类型形式依赖它，MUST NOT 顺手删除。验收标准：逐模块给出「零引用 / 仅恒假块引用 / 仍被活代码引用」三分类结论
- [ ] 6.5 单独裁定 `PlatformDriver.createOverlayMonitor` 这个**无调用点的工厂成员**（全仓无 `platformDriver.createOverlayMonitor(...)` 调用）：或接进本 change 恢复的小红书阻断观测通路、或从接口上删除并同步两个 driver 实现，MUST NOT 原样留成「接口上有、没人调」的第二种无信号保留。验收标准：接口与两处实现的最终形态在测试里被断言（参照 src/browse/overlay-monitor.ts:472-498 的 `CdpOverlayMonitor`；旧 `probeNow()` 是高危动作提交前 fail-closed 用的即席复检句柄，Native 把它内化进 Rust 动作闸后宿主侧再无可调句柄 — 见 oracle.md）

- [ ] 6.6 结构化现场快照的登记条目 MUST 写明下游影响，不得只记一句「缺快照」：Native 阻断上报把候选证据写死为空数组、只带一段截断到 1000 字的文本（src/native-page-engine/browse-session.ts:558-567 与 :506），下游后果是云端与运营分诊只能靠这一段文本给阻断命名——没有主候选的 DOM 特征 / 选择器路径 / 位置尺寸 / 层级与透明度 / 内嵌页地址 / 有无关闭控件 / 命中理由，也没有备选候选可看；且已合并要求「判为阻断态的遮罩上报必须携带非空证据文案」在文本为空时会让真限流只到降速档而非刹车档。验收标准：6.1 的对账表里这条落成「已登记缺口 + 下游影响 + 去处」三栏，MUST NOT 写成「已由 Native 承接」（参照 oracle.md 覆盖漏洞 6 与末条「无对应物 1」）

## 7. 验证与验收

- [ ] 7.1 运行聚焦测试：小红书阻断上报、提交窗口、键入取证、诊断对称、身份校验五组
- [ ] 7.2 运行 `cd ../aidcp-edge && npm run test:acceptance`，确认 `AC-PROTO-*` / `AC-RISK-*` 全过，两份 `protocol.ts` 消息总数不变
- [ ] 7.3 运行 `cd ../aidcp-edge && npm test` 与 `npm run typecheck`
- [ ] 7.4 运行 Rust 侧 `cargo fmt --check`、`cargo clippy -- -D warnings`、`cargo test`
- [ ] 7.5 运行 `openspec validate restore-native-xiaohongshu-session-guards --strict`
- [ ] 7.6 记录 edge 与控制仓的提交 sha、验证证据、偏离说明与热点文件重叠情况；明确写下未执行的动作（未出安装包、未部署、未做真机写动作）

- [ ] 7.14 登记「验证码协助除键入取证外的其余 9 项（回放模式、轨迹回放、点击拟人节奏、落点数预检、回放前陈旧复检、抓帧前阻断复检、快照裁剪与类型、实时抓帧的连续确认清除、点击期间抓帧互斥、提交后有界复检）」为本 change 范围外项，已在 design.md Non-Goals 具名交接给「需新立 change（建议名 `restore-native-captcha-assist-humanization`）」

### 真机验收项（桩验不了，须在真机上定论；不得当成已确认事实）

- [ ] 7.7 【真机】小红书环境真触发一次验证码：确认边缘发出 `risk.captcha_detected`、云端唤起远程协助、账号风控态迁移，清除后收到配对 `cleared`
- [ ] 7.8 【真机】小红书 `captcha` 桶的误报率：连续观察若干场浏览，确认正常页面（含笔记详情弹层、看图态、AI 搜索结果页）不被判成阻断（参照 xhs-page-probe.js:22；`captchaSignalCount` 与 `dialogCount` 均不排除笔记详情容器、且已退化成子串计数，是误报的已知根因 — 见 oracle.md）
- [ ] 7.9 【真机】远程协助键入一次真实验证码，确认回执里的实际派发字符数、回读三态与是否提交与现场一致，且答案明文未出现在任何日志 / 落库 / URL 中
- [ ] 7.10 【真机】小红书提交窗口的实际效果：在评论提交进行中发起一次高档位抢占，确认协调器回「窗口占用中 + 剩余预算」而非在提交中途接管
- [ ] 7.11 【真机 · 推断未坐实】简报判定「提交窗口缺失目前只表现为接管失败、不撕裂写入」依赖「写命令不做飞行中取消」这一当前实现，未真机复现；须在真机上确认修复前后是否真出现过重复提交
- [ ] 7.12 【真机 · 推断未坐实】小红书运行期换号 / 掉登录的真实发生形态与频率没有线上数据支撑，只有代码与旧注释对照；周期与防抖阈值须按一次真机观察定档
- [ ] 7.13 【真机】小红书低置信 `unknown` 阻断桶的缺席影响面：观察是否存在「真阻断但既非验证码指纹也非登录墙」的实际形态，据此决定是否值得为它单起一个 change（参照 src/browse/overlay-monitor.ts:1-231 的旧五类分法与 `access-limit-app` 归「可关」；旧 unknown 判据本身是误报源，勿照抄 — 见 oracle.md）
