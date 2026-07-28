# 退役实现参照（oracle）

> 用途：本 change 的多数条目属「以前能做、迁移后做不了」。退役的 TypeScript 实现仍在
> /Users/baitianxing/codes/aidcp-edge/src/ 下（被构建期剪枝挡在生产外、宿主装配被恒假条件短路），可直接当行为参照。
> **只当参照书，不得把退役实现搬回生产**——那会击穿本次迁移的动机，且宿主那段是死码不是开关。
> 迁移前版本用 `git -C /Users/baitianxing/codes/aidcp-edge show 317cd47^:<path>`（小红书）或 `4f04e9c^`（Facebook/微信）读。

> 行号核对：本参照书的行号按 aidcp-edge `3207561`（2026-07-28）实测抽查过
> `src/main.ts:1043` / `:88-103` / `:1213`、`src/native-page-engine/browse-session.ts:237-239` / `:349-357` / `:459-466` / `:491`、
> `src/browse/browse-session.ts:2583` / `:3109` / `:3163`、`src/flows/publish-command-handlers.ts:1372` / `:1388`、
> `src/browse/login-modal-watcher.ts:39-65`、`native/page-engine/src/engine.rs:598` / `:563-566`、`native/page-engine/src/probe.rs:130-141`、
> `native/page-engine/src/xhs-page-probe.js:12-22`，均对得上（各退役文件总行数也与引用的区间上界一致：
> overlay-monitor 498 / overlay-report-gate 83 / login-modal-watcher 119 / identity-watcher 162 / background-watcher 131 / commit-window 75）。

## ⚠️ 不可照抄的条目（先看这段）

**oracleQuality 为 `stale` / `also-wrong` 的条目：无**（8 条全为 `direct`）。

但「direct」只保证**机制层**可照搬，下面 7 处即便在 direct 条目里也不得照抄，照抄的后果已写明：

1. **小红书阻断判定的选择器 / class 正则**（`src/browse/overlay-monitor.ts` 内的指纹表）是 2026-06 前的小红书 DOM。
   照抄的后果：判据静默失效（选择器漂移不报错，只是恒不命中）⇒ 恢复出来的监测体看着在跑、实际永不检出。必须真机复核。
2. **`unknown` 桶的判据 `hasIframe || (big && fixed && !hasClose)`** 本身就是误报源。
   照抄的后果：造出一台误报机——正常的笔记详情弹层 / 看图态 / AI 搜索结果页会被判成阻断，触发保守暂停并向云端上报，
   进而把账号推向 `restricted`（自残）。本 change 已裁定：在缺真正的阻断分类器前小红书要**声明缺席**（task 1.4），
   不得拿「页面类型识别不出」冒充阻断。
3. **登录墙判据不要重写第二份**。旧判据（5 条强短语 + 笔记详情容器排除 + 可见性三判）已被逐字搬进注入 JS
   `native/page-engine/src/xhs-page-probe.js:12-21`，只是没有消费者。照抄成第二份的后果：两处判据独立漂移，
   以后改一处另一处静默不同步。task 1.3 要做的是**接线**，不是重写判据。
4. **四处提交窗口不能照抄「在点击那一刻 `enter`」这个位置**。旧实现的四处 `enter` 紧贴 `dispatchClick`；
   而 Native 下这四次点击发生在注入 JS `native/page-engine/src/xhs-command-router.js:224 / 236 / 272` 里，
   proposal 明确**不碰该文件**（另一 change 的单写区）。所以开窗只能落在 Rust 侧 `evaluate_router` 调用之前，
   粒度是「整条 router 调用」而非「点击那一刻」，预算必须覆盖 router 内部的后置校验停顿（评论路径有 `sleep(800)`）。
   照抄旧位置的后果：改到别人的单写区，或窗口关得比真实写入还早。
5. **「重连后重注入节奏快照」这一步不能直接搬回**。Native 的 `applyPacingSnapshot` 是空实现且注释写明
   `Pacing stays Cloud-owned`（`src/native-page-engine/browse-session.ts:213-218`）。照抄旧代码的后果：
   与 Native 现行的节奏归属冲突。要先裁定归属，再决定落点。
6. **现场快照的候选筛选口径不能不加确认地照抄**。旧注释已记下：该筛选对 Facebook 标准限流弹窗**必然落空**
   （无 iframe / 未达尺寸阈 / 有关闭控件）⇒ 证据文本为空 ⇒ 云端「无文案不臆断限流」返否定。
   照抄到小红书前必须先确认小红书阻断弹窗的实际形态，否则同样落空，补了快照却仍是空证据。
7. **不得把退役实现整体搬回生产**（本文件顶部的红线）：`src/main.ts:1043-1213` 那段是**编译期不可达的死码**，
   不是一个可以打开的开关；剪枝脚本会拒绝它的选择器与模块，它也不可能成为打包后的回落路径。

## 逐条参照

### 小红书阻断浮层监测体与云端上报整体缺席

- **对应任务**：1.1、1.2、1.3、1.5（云端上报与配对）；6.5（`PlatformDriver.createOverlayMonitor` 的最终形态）。**注**：结构化现场快照（`candidates` 字段集）只被 6.1 要求「对账登记」，没有任何任务要求补回 —— 见文末覆盖漏洞。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/overlay-monitor.ts:1-231（分类口径 + sticky 容错 + 五类判定优先级）、:233-381（结构化现场快照 JS）、:472-498（CdpOverlayMonitor 基于 BackgroundWatcher）；/Users/baitianxing/codes/aidcp-edge/src/browse/overlay-report-gate.ts:1-83（上报闸纯状态机）；装配段 317cd47^:src/main.ts:1281（创建监测体）、:1336-1338（confirmMs / isCloudBlockingOverlay）、:1339-1355（快照 prime/reset）、:1356-1388（sendOverlayDetected）、:1389-1405（createOverlayReportGate）、:1406-1412（注册进 supervisor 并接上报闸）`
  - 机制：旧实现是一条独立的后台监测线：以 1 秒为默认节拍持续对页面判类，把「阻断」分成五类并各配一套相反的应对——登录墙只本地暂停、验证码即刻停手并升级、运营弹窗归为可关、可见但归不出类的大遮罩保守暂停并交云端命名、无遮罩放行。判定按危险度排序（验证码 > 登录 > 可关 > 未知 > 无），且只认人类可读、跨改版稳定的语义片段（验证码厂商 iframe 域名、挑战文案、稳定语义 class），不锁混淆 class。检测失败时后台节拍保持上一状态、绝不翻转（避免正常导航期的瞬时求值失败被当成验证码刷假告警），而供高危动作提交前用的即席探测则原样抛错、由调用方按「宁可信其有」处理。翻转出去的类别交给一个独立的上报闸做云端记账：低置信「未知」必须延后一轮确认仍在才上报（滤掉离页返回途中 token 失效详情墙这种一闪即自愈的坏页），真验证码指纹即时上报不经确认窗，且检出与清除严格配对——从未上报过的瞬时未知消失不得发孤儿清除，离开阻断态时自增 episode 号让在途的延后确认作废。上报时还会先抓一张只读的现场快照：主候选元素的标签/id/class/role/aria-modal/选择器路径/矩形/定位与层级/是否含 iframe 及其 src/是否有关闭控件/命中原因清单，加最多 3 个备选候选，供云端命名与运营分诊。另外小红书笔记级访问限制弹窗被专门归为「可关」而非账号级阻断，因为它能靠退回列表自行恢复。
- **旧代码记下的真机经验**：

> 把「检测节奏」与「执行节奏」解耦——后台 loop 按自己的节奏(默认 1s)持续判类，状态独立于命令到达保持新鲜，闸门只读缓存(零 CDP)；

> login    → 暂停等登录（沿用现状）

> captcha  → 暂停 + 停手 + 升级（漏一次=可能封号，故 fail-CLOSED）

> dismissible(运营活动) → 可关（本 PR 仅分类，关闭交后续 NuisanceDismisser）

> unknown  → 可见阻断遮罩但本地未能归类 → 保守暂停 + 上报云端命名(fail-CLOSED)

> none     → 放行

> 后台 tick()：探测失败按「保持上一状态」(sticky)，不翻转——否则页面正常导航期间 Runtime.evaluate 瞬时失败会被误判为验证码，刷假告警；

> probeNow()：原样抛出，交由调用方（高风险动作提交前复检）按 fail-CLOSED 处理。

> 检测口径沿用项目反混淆理念：只认人类可读、跨改版稳定的语义片段（厂商 iframe host、挑战文案、稳定语义 class），不锁混淆 class。验证码组件(数美/极验/网易易盾…)的 DOM 指纹极稳定，故本地确定性探测召回高、误报低，无需云端 LLM 介入热路径。

> 判定优先级（高危先判）：captcha > login > dismissible > unknown > none。

> // ⑤ unknown：可见、较大且 fixed/absolute 的阻断遮罩(非笔记详情)，分不出类且没有明显关闭键，
>     //    或内含未识别 iframe → 保守上报，交云端命名。口径偏保守以抑制误暂停。

> 小红书笔记级访问限制弹窗：不是账号级验证码/登录墙，应允许返回列表恢复。

> 低置信 `unknown` 遮罩 MUST 经一轮持续性确认（延后 confirmMs 复核仍为 unknown）才上报——滤掉离页返回途中 token 失效详情的 300031 墙这类一闪即自愈的瞬时坏页误报。

> 真验证码指纹 `captcha` MUST 即时 fail-CLOSED、不经确认窗（绝不弱化真验证码）。

> `detected` / `cleared` 必须配对：只有真发过 `detected` 的 episode，其自愈才发 `cleared`；被确认窗抑制、从未上报的瞬时 `unknown` 消失 MUST NOT 发孤儿 `cleared`，也 MUST NOT 遗留已发未清的 `detected`。

> login / dismissible 不入本闸（login 只本地暂停、不打扰云端；dismissible 自动关）——调用方传入的 from/to 是完整 OverlayKind，本闸只对 captcha/unknown 这两类「阻断-云端」态记账。

> episode 代号：离开阻断态 / 新 episode 即自增，令在途的延后确认失效（自愈后不再补发）。

> // 启动旁路监测：类别翻转进 captcha/unknown 时上报云端（人工升级）；离开时上报已清除。
>     // 仅 captcha/unknown 上报（login 只本地暂停、沿用现状不打扰云端）。

> 旁路弹窗监测体：后台持续判类（登录/验证码/运营/未知），闸门读其缓存状态停手。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:459-466（scheduleProbe 首行 `platform !== 'facebook'` 即 return，小红书从不起周期探针）、:475-489（probeFacebook 同样平台闸）、:491-550（observeFacebookProbe 首行 `platform !== 'facebook'` return，上报/清除全在其内）、:552-578（reportFacebookBlocking）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/probe.rs:130-141（小红书 build_result 恒置 `blocking_kind: None` / `blocking_text: None`）、:150-196（classify_page 只产 PageKind，无阻断分类）、/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-page-probe.js:22（captchaSignalCount 只数 class/iframe 子串命中数）`
- **具体缺哪几样**：
  1. 缺「小红书周期性阻断观测」这条线本身：`scheduleProbe` / `probeFacebook` / `observeFacebookProbe` 三处首行都是 `platform !== 'facebook'` 直接 return（browse-session.ts:460 / 476 / 492），小红书连 2 秒探针都不起
  2. 缺阻断分类：Rust 侧小红书探针恒返 `blocking_kind: None`（probe.rs:137），只有一个 `PageKind`；把「五类（none/login/captcha/dismissible/unknown）」压成了「PageKind::Login / PageKind::Captcha」两格，`dismissible` 与 `unknown` 两个桶整体没有对应物
  3. 把验证码指纹从「厂商 iframe host 正则 + 13 条挑战文案 + 稳定语义 class 正则」换成了一个 class/iframe-src 子串计数（xhs-page-probe.js:22 的 `[class*="captcha"],[class*="Captcha"],[class*="geetest"],iframe[src*="captcha"],iframe[src*="verify"]`），13 条中文挑战文案（安全验证/滑动验证/拖动滑块/依次点击…）全部丢失
  4. 缺笔记详情容器排除：新探针只在 `loginWallCount` 分支里做 `closest(noteSelector)` 排除（xhs-page-probe.js:16），`captchaSignalCount` 与 `dialogCount` 两个计数完全不排除笔记详情容器
  5. 缺小红书笔记级访问限制的专门归类（「当前笔记暂时无法浏览」「请打开小红书App扫码查看」「小红书如何扫码」+ `access-limit-app` class）→ 新实现里它要么不命中、要么落进 Login/Unknown，失去「可退回列表自愈、不算账号级阻断」这条语义
  6. 缺上报闸：没有 detected/cleared 严格配对与 epoch 作废机制的通用实现；Facebook 侧是手搓的近似物（browse-session.ts:512-549，只有一个 `facebookReportedBlockingKind` + 一个 timer），小红书连这个近似物都没有
  7. 缺现场快照：`captureBlockingOverlaySnapshot` 的候选筛选、主候选 DOM 特征（selector 路径 / rect / position+zIndex+opacity / iframeSrcs / hasClose / matchReasons）与最多 3 个备选全没了；Native 上报里 `candidates: []` 写死（browse-session.ts:566），只带一段 `blockingText`
  8. 缺 sticky 语义：新探针失败只在宿主打一行日志（browse-session.ts:487），没有「保持上一状态、不翻转」的状态缓存，也没有 `msSinceLastOkTick()` 这类「已看不见多久」的度量
  9. 后果链：全仓唯一活着的 `risk.captcha_detected` / `risk.captcha_cleared` 发送点在 browse-session.ts:538 与 :555，两处都在 Facebook 判据之内 ⇒ 小红书遇验证码零上报 ⇒ 云端不建 incident ⇒ 远程协助不被唤起、账号风控态不迁移
- **可 port 的旧测试**：
  - overlay-report-gate: 一闪而过的 unknown（确认前自愈）不上报、不发孤儿 cleared —— 锁「低置信桶必须经确认窗，且未上报过就不得发清除」
  - overlay-report-gate: 持续 unknown 经确认后上报一次，自愈发配对 cleared —— 锁「确认后只报一次 + 检出/清除严格配对」
  - overlay-report-gate: 确认到点但已自愈成非 unknown（isStillUnknown=false）不上报 —— 锁「确认窗到点要复核当前状态，不凭旧翻转补发」
  - overlay-report-gate: captcha 指纹即时上报、不经确认窗（不弱化真验证码） —— 锁「验证码不进确认窗」
  - overlay-report-gate: unknown→captcha 升级即时报 captcha，且不因在途确认双报 —— 锁「同一 episode 内升级不双报」
  - overlay-report-gate: login/dismissible 之间的切换不产生任何云端上报 —— 锁「登录墙只本地停手、不打扰云端」
  - CdpOverlayMonitor.tick: 探测失败保持上一状态（sticky，不刷假翻转） —— 锁 sticky 容错
  - CdpOverlayMonitor.probeNow: fresh 探测；CDP 失败原样抛出 —— 锁「即席复检失败必须外抛给调用方 fail-closed」
  - CdpOverlayMonitor.tick: 状态翻转触发一次 onTransition；同状态不重复触发 —— 锁翻转去抖
  - isBlockingKind: login/captcha/unknown 阻断；none/dismissible 不阻断 —— 锁五类到「是否停手」的映射
  - buildClassifyOverlayJs: 小红书 access-limit-app 归为可恢复非阻断弹窗 —— 锁笔记级访问限制不当账号级阻断
  - buildClassifyOverlayJs: 生成的 JS 含各类指纹与返回分支 —— 锁判定优先级与五个返回分支都在
  - captureBlockingOverlaySnapshot: normalizes text, DOM features, and first URL —— 锁快照字段归一（可移植为 Rust 上报体契约测试）
  - buildBlockingOverlaySnapshotJs: generated JS captures first URL and DOM feature fields —— 锁快照 JS 采集哪些 DOM 特征
- **caveat**：机制层（五类分法、优先级、sticky、确认窗、配对 epoch、快照字段集）可直接照搬；但两处不可照抄：① 具体选择器/class 正则是 2026-06 前的小红书 DOM，需真机复核；② `unknown` 桶的判据（`hasIframe || (big && fixed && !hasClose)`）本身就是误报源，change 已明确裁定在缺真正阻断分类器前小红书要「声明缺席」而不是拿「页面类型识别不出」冒充 —— 照抄这一条会造出一台误报机。

### 登录墙看护与本地停手闸缺席

- **对应任务**：1.3（登录墙 → 本地停手、不发账号级上报）、1.6（暂停下发 + 清除后恢复 + 诚实未开始）。**未覆盖**：高危动作提交前的即席 fresh 复检、停手等待循环的三个出口 —— 见文末覆盖漏洞。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/login-modal-watcher.ts:1-119（判据 + 防误报 + 失败按未弹出）、:39-45（候选容器）、:52-58（5 条强短语）、:60-65（排除笔记详情容器）；/Users/baitianxing/codes/aidcp-edge/src/browse/browse-session.ts:3391-3451（waitWhileBlocked 停手闸）、:3453-3469（captchaPresentFresh 提交前 fresh 复检）、:994（离页/返回后的 overlayStillBlocked 判据）；装配 317cd47^:src/main.ts:1431（CdpLoginModalWatcher 实例化）、:1432-1434（confirmLoggedOut 按平台分派）`
  - 机制：旧实现有两层：一层是判「登录浮层是否可见」的检测角色，在遮罩/对话框/含 login 的候选容器里找可见元素、文本命中 5 条长且特异的登录页签短语；为避免看笔记时被误暂停，凡落在笔记详情容器内（含自身）的候选一律跳过，短语也刻意不含「登录后」这种内联 CTA 与评论里都有的弱串；探测失败按「未弹出」处理、不误暂停。第二层是浏览会话里的停手闸：每条命令进来先读监测体的缓存类别（零 CDP），凡属阻断类（登录/验证码/未知）就暂停并轮询等其消失，出现与消失各只记一次日志不刷屏，等待期间同时响应本地停止、队列里已到的会话结束命令、以及任务接管信号（接管到达即抛出、命令零副作用作废，绝不只 return——否则命令会继续对着验证码墙点下去）。闸门只管停手，云端通知由上报闸负责，两者解耦。第三层是高危动作（点赞/收藏/关注）提交前的即席复检：缓存可能过期约一个节拍，闸门放行后到真正点击之间的拟人停顿里若弹出验证码，只靠缓存会漏，故在派发点击前就地再探一次，探测失败保守当成有挑战。
- **旧代码记下的真机经验**：

> 小红书在登录态缺失 / 过期 / 触发风控时会弹出登录浮层（扫码登录 / 手机号登录…）。一旦弹出，继续滚动 feed、点开卡片等操作既无意义又徒增风控特征，应当**暂停**，直到用户完成登录、弹窗消失再恢复

> 关键防误报（避免看笔记时被误暂停）：
>  *  - 排除「笔记详情容器」(XHS_NOTE_MODAL_SELECTOR)——它的 class 含 mask/modal 片段会被候选选择器
>  *    命中，而其 textContent 含正文+评论，评论里出现"登录"等字样会造成误判；
>  *  - 短语只用长且特异的登录页签文案，**不含** "登录后"（"登录后查看更多"等内联 CTA 与评论都含它）。

> 这样既不依赖 cookie（web_session 是 httpOnly，页面读不到），也不会误命中笔记详情/评论。

> 只用长且特异的登录页签文案：避免命中导航栏里恒存在的单字"登录"按钮，也避免命中评论 / 内联 CTA 里的"登录后…"（故不含"登录后"）。

> 探测失败不应误暂停浏览；交给调用方记录后按"未弹出"处理。

> captcha/unknown 的**云端上报**不在此处——由 overlayMonitor 的 onTransition 回调负责（见 main.ts），闸门只管「停手」，与「通知」解耦。

> 第三个出口 = 任务接管（change lease-strict-preemption，治硬死锁）：本闸门是 executeCommand 的第一句、排在任何页面写之前——停在这里的命令**一个字节都没写过页面**。但交接（quiesceForTask）等的是「命令处理函数还没返回」，于是它无界地等一条正在等验证码的命令，而那个验证码只有这次交接要授予的 system_recovery 协助任务才能点掉 → 闭环死锁，整台机器停摆。故：接管信号到达即抛出，命令零副作用作废、当场让路。**绝不能只 return**——那会让命令继续往下对着验证码墙点击。

> 旁路缓存可能过期约一个 poll 周期：闸门放行后、真正点击前的 humanPause 窗口里若弹出验证码，仅靠缓存会漏过。故在 dispatchClick 前就地再探一次：命中 captcha/unknown 即放弃点击。复检的 CDP 失败按"有挑战"保守处理（fail-CLOSED）——错过一次点赞很便宜，点进风控墙很贵。

> 出现 / 消失各只记一次日志（blockingOverlayActive 状态翻转才打），不刷屏。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-page-probe.js:12-21（登录判据被复制进注入 JS：5 条短语 + 笔记容器排除，只产一个 0/1 计数）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/probe.rs:151-153（login_wall_count>0 → PageKind::Login）；无消费者——/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts 全文无「阻断则等待/停手」的闸门，`page_probe` 对小红书只在 engine.rs:378 被显式命令触发时才跑`
- **具体缺哪几样**：
  1. 登录判据本身被搬进了注入 JS 且逐字保留（5 条短语 + 笔记容器排除 + 可见性三判），但**没有任何消费者**：Native 小红书路径没有「阻断则暂停」的闸门，`PageKind::Login` 只被用作导航后置校验（engine.rs 的 `wait_for_page_kind`），不会让浏览停手
  2. 缺「等待其消失后恢复」的轮询循环，连同它的三个出口（本地停止 / 队列里已到的会话结束 / 任务接管即抛出）一并消失 ⇒ 登录墙常驻时小红书侧既不暂停也不上报，命令继续往墙上打
  3. 缺「出现/消失各记一次」的日志去抖，改成每条命令各自静默失败
  4. 缺高危动作提交前的 fresh 复检：Rust 侧小红书没有任何 `ensure_*_action_gate`（对照 Facebook 的 `ensure_facebook_action_gate`，shared.rs:376），点赞/收藏/关注/评论都不做提交前阻断复检，也就没有 `blocked_by_captcha` 这个诚实回执理由
  5. 缺「探测失败保守当成有挑战」这条 fail-closed：新探针失败整条命令报错，方向相反（不是保守停手而是命令失败）
  6. 缺登录墙作为「正向登出探针」被身份看护复用的那条接线（见下一条缺口）
- **可 port 的旧测试**：
  - 判定JS: 候选落在笔记详情容器内（closest 命中排除选择器）→ false（防评论误判） —— 锁笔记详情排除，可直接对注入 JS 的 loginWallCount 跑
  - 默认短语只用多字强短语，不含裸"登录"与过松的"登录后" —— 锁短语表强度（防以后有人加回弱串）
  - 判定JS: 命中短语但容器不可见（display:none）→ false / 零尺寸 → false / opacity≈0（淡入淡出）→ false —— 锁三条可见性判据
  - isOpen: 探测异常按未弹出处理且触发 onError —— 锁「检测失败不误暂停」
  - 登录闸门: loop 启动时检测到弹窗则暂停，弹窗消失后恢复并上报卡片 —— 锁停手闸的暂停/恢复语义
  - 登录闸门: session.end 不被弹窗阻塞（终止命令绕过闸门） / 弹窗常驻时 cloud session.end 仍能终止会话（治死锁，回归） —— 锁闸门的终止出口
  - overlayMonitor 闸门: state=captcha 时暂停 browse.next，翻回 none 后才滚动 —— 锁缓存态驱动停手
  - overlayMonitor 闸门: session.end 不被 captcha 阻塞（绕过闸门，治死锁） —— 同上的终止出口
  - overlayMonitor 提交前复检: like 命中 captcha → 放弃点击并上报 blocked_by_captcha —— 锁提交前 fresh 复检 + 诚实回执理由

### 运行期身份看护与身份重立链缺席

- **对应任务**：5.1、5.2、5.3、5.4。**未覆盖**：身份重立链的后半段（断连换号重连 / 先回消费端首页 / halt 不回落默认账号 / 重注入节奏快照 / rebaseline / 重启监测体）—— 见文末覆盖漏洞。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/identity-watcher.ts:1-162（周期校验 + 分域 + 防抖 + 正向登出探针 + rebaseline）；装配与消费 317cd47^:src/main.ts:1427-1445（loginWall 作正向登出探针、IdentityWatcher 实例化与注册）、:1035-1102（reestablishIdentity 全链）`
  - 机制：旧实现把身份当成「持续校验的状态」而不是握手时定死一次：默认每 30 秒就地（不导航）重读本节点的稳定账号 id，与已确立基线比对——一致即健康清零计数、不一致判换号并带出新 id、读不出判登出/过期；连续达到阈值（默认 2）才判失效，滤掉瞬时读失败。判定前先按页面上下文分域：停在创作平台真实页说明还登着、直接判健康；创作子域被弹到登录页判真登出；页面无法判定（空白页/非本站/导航中途）本轮跳过——既不计失效也不判健康。消费页读不出本人锚点时，用登录浮层是否可见做正向登出探针区分「真登出」与「停在无侧栏页/弹层态」，不可见则本轮无法确认、跳过；缺省不注入探针时按登出计，保守不漏判。判失效只发一次转移，由宿主接一条完整的身份重立链：停掉全部后台监测体 → 停浏览 → 把在途发布诚实判失败（必须在关连接之前发，否则失败回执发不出去）→ 断开云端 → 先导航回消费端首页再读身份（触发失效时可能停在创作发布页/弹层态而无锚点）→ 读不出就停在无身份态、绝不回落默认账号 → 用新 id 换云端会话并重连 → 把新的节奏快照重新灌进浏览会话 → 重设基线、重启监测体与浏览。
- **旧代码记下的真机经验**：

> 身份是「持续校验的状态」，不是握手时定死一次（design D4）。本监测体周期性【就地、不跳转】重读自己的稳定 id，与已确立基线比对：
>  *   - 读出 == 基线 → 健康，清零计数；
>  *   - 读出 != 基线 → 换号（changed，带 newId）；
>  *   - 读不出      → 登出/过期（lost）。

> 防抖：连续达到阈值次数（默认 2）才判失效（healthy→invalid），避免瞬时读失败误退（design 开放问题 3）。

> 判失效后【只 emit 一次】转移，由调用方退回无身份态、断连重连重建身份（不重跑节点初始化）。

> 只读 + 不导航（readSelfIdentity allowNavigate:false）——绝不每轮把页面拽走。

> 正向登出探针：消费页读不出本人锚点时，用它区分「真登出」与「停在无侧栏页/弹层态」——登录浮层可见=真登出（判 lost），不可见=无法确认（本轮跳过）。缺省不注入时按登出计（保守、维持旧行为，不因引入分域判据而漏判真登出）。

> 先按页面上下文分域，绝不不看页面就一律用消费端锚点判定（否则发布把标签页带到创作子域时会误判登出）。

> 创作平台真实页（登录门禁）：能停在这=已登录 → 健康、清零。

> about:blank / 非小红书 / 导航中途：本轮跳过——既不计失效也不判健康（不误杀、不假愈）。

> 消费页无本人锚点但无登录浮层 → 无法确认（疑似无侧栏页/弹层态），本轮跳过

> 读取异常按登出计一次（防抖阈值兜住瞬时）

> 身份失效 → 退回无身份态、重新确立、按新 id 重连（account-identity-from-login 1.3/1.4）。复用同一 session.cdp（浏览器不重启、端口/目录不重分 = 节点初始化不动），只重跑「身份确立」。

> 断连前先把在途发布诚实判失败（须在关 WS 之前，失败回执才发得出去），云端不被无限期挂起等结果。

> 先回到消费端首页再判身份：触发失效时可能停在创作发布页/弹层态（无「我」锚点），直接原地读会无谓停摆。readSelfIdentity 的 hydrate 有界重试会等锚点渲染出来；导航失败则退回原地读（与旧行为同、不更坏）。

> 留在无身份态，不静默以默认账号开跑（红线）

> 重连重注入节奏快照（pacing-floor-config-min-interval 设计 §4.3 最严重缺口）：BrowseSession 只构造一次，identity 翻转复用同一对象；须在 connect()（新 welcome 已到）之后、start() 之前把新 floors/tempo 灌进去，否则连接级快照在唯一原地重连路径上退化成进程级、风控升级到不了边缘节奏层。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/main.ts —— 全文已无 `IdentityWatcher` / `reestablishIdentity` / `watcherSupervisor` 实体（只剩 :101 的影子声明 `declare const WatcherSupervisor`）；身份只在两点各读一次：:351-353（启动确立）与 :1388-1393（冷待机唤醒后重读）；:1419 的注释「恢复自动化：监测体重挂」已成孤证——没有任何监测体被重挂`
- **具体缺哪几样**：
  1. 缺周期校验体本身：无 30 秒节拍、无 `AIDCP_IDENTITY_CHECK_MS` / `AIDCP_IDENTITY_FAIL_THRESHOLD` 两个旋钮、无连续 2 次防抖计数；现在身份只在启动（main.ts:351）与冷待机唤醒（main.ts:1388）各读一次
  2. 缺四态分域判定：`creator-app` 判健康清零 / `creator-login` 判真登出 / `unknown` 本轮跳过 / 消费页就地读 —— 这四条一条都没有对应物
  3. 缺正向登出探针接线：登录浮层判据虽还在注入 JS 里（xhs-page-probe.js:12-21），但没有任何代码把它当作「消费页读不出锚点时区分真登出与弹层态」的第二判据
  4. 缺「只 emit 一次转移」的语义与 `lastReason`（换号带新 id / 登出）区分
  5. 缺整条身份重立链的 12 步：停监测体 / 停浏览 / 在途发布诚实判失败 / 断连 / 先回消费端首页 / 就地重读 / halt 时停在无身份态不回落默认账号 / 换 accountId / 重连 / 重注入节奏快照 / rebaseline / 重启监测体与浏览 —— 现在只有「唤醒后账号变了就重建云端会话」这一条近似物（main.ts:1403-1415），且它只在冷待机唤醒路径上跑，不在运行期
  6. `applyPacingSnapshot` 在 Native 会话里是空实现（browse-session.ts:213-218，注释「Pacing stays Cloud-owned」）⇒ 即便将来接回身份翻转，「重连重注入节奏快照」这一步也没有落点
- **可 port 的旧测试**：
  - IdentityWatcher: 读出基线 id → 健康，不转移 —— 锁健康路径不误报
  - IdentityWatcher: 换号需连续达阈值才判失效（防抖） —— 锁阈值防抖
  - IdentityWatcher: 中途恢复基线 → 计数清零、不误触发 —— 锁计数清零
  - IdentityWatcher: 读不出 id（登出/过期）连续达阈值 → lost —— 锁 lost 判据
  - IdentityWatcher: 判失效后不再重复转移 —— 锁「只 emit 一次」
  - IdentityWatcher: rebaseline 复位为健康、换新基线 —— 锁身份重立后的复位
  - IdentityWatcher: 停在创作发布页（creator-app）→ 判健康、绝不误杀（即便无消费端锚点） —— 锁分域第一格
  - IdentityWatcher: 创作子域被弹到登录页（creator-login）→ 判 lost —— 锁分域第二格
  - IdentityWatcher: 无法判定页（unknown，about:blank/非小红书）→ 本轮跳过，不计失效 —— 锁分域第三格「不误杀不假愈」
  - IdentityWatcher: 消费页无本人锚点但无登录浮层 → 无法确认、跳过（不误杀 AI 搜索/看图态） —— 锁正向登出探针的否定分支
  - IdentityWatcher: 消费页无本人锚点且有登录浮层 → 真登出判 lost（分域闸不漏判） —— 锁正向登出探针的肯定分支
  - IdentityWatcher: 创作发布页穿插在消费页失效计数间 → 清零，防止跨页凑够阈值 —— 锁跨页计数污染
  - IdentityWatcher: inconclusive 跳过后回消费页仍能正常判定（换号达阈值） —— 锁跳过不破坏后续判定
  - IdentityWatcher: 可注入平台身份读取器（FB 不复用小红书 readSelfIdentity） —— 锁读取器可注入（Native 侧对应「按平台选身份命令」）

### 监测体生命周期托管与 CDP 健康联动缺席

- **对应任务**：**本 change 无对应任务** —— 1.2 只改「周期探针的启动条件」，不含托管、CDP 健康联动、存活度量与节拍可配。见文末覆盖漏洞。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/background-watcher.ts:1-131（自走时钟 + 状态缓存 + 翻转一次 + 启停幂等 + 存活度量，:34 pollMs 默认 1000，:38 onProbeError 默认 sticky，:56-58 msSinceLastOkTick）；/Users/baitianxing/codes/aidcp-edge/src/browse/watcher-supervisor.ts（统一 register/startAll/stopAll）；装配 317cd47^:src/main.ts:1406（new WatcherSupervisor）、:1446-1457（cdp.unrecoverable / cdp.reconnected 联动）、:1458-1463（待机/暂停时装配但不启动）`
  - 机制：旧实现把所有「只看不动」的监测体收在一个共同骨架下：自走时钟轮询、状态缓存、只在翻转时回调一次、启停幂等，并记录「上次成功探测时刻」供上层判断是否已经看不见——明确拒绝把「探测不了」当成「没情况」。上层再用一个统一管家托管全部监测体的生命周期：CDP 重连进入不可恢复终态时停掉全部监测体（否则它们继续对已死的连接空轮询、每个节拍刷一行「探测失败(保持上一状态)」的僵尸日志直到进程退出），重连成功则整批重启（启动幂等，未停是空操作、曾停则干净恢复）。冷待机或启动即暂停时，监测体照样装配好但不启动，并明确打日志说明「已装配但暂不启动」。
- **旧代码记下的真机经验**：

> 职责：自走时钟轮询 + 状态缓存 + 仅在状态翻转时回调一次 + 启停幂等 + 自身存活（心跳）。子类只实现 probe()（一次检测，CDP/读取失败可抛）与可选的 equals()/状态类型；检测什么、怎么归类是子类的事，循环 / 容错 / 翻转 / 启停由基类统一负责。

> 存活：记录"上次成功探测时刻"，msSinceLastOkTick() 供上层判断"是否已看不见"——绝不把"探测不了"当成"没情况"（那是传感层的假成功）。基类只暴露该度量，是否升级为告警由上层决定。

> CDP 重连联动：不可恢复（重连耗尽、终态）→ 停掉全部后台监测体。否则它们继续对已死的 client 空轮询、每 pollMs 刷一行「探测失败(保持上一状态)」僵尸日志直到进程退出（旧码只有 SIGINT 才 stopAll）。重连成功 → 重启（start() 幂等：未停则 no-op；曾停则干净恢复，避免恢复的 session 后台盲跑/停摆）。

> 控制面待机：自动浏览与后台监测体已装配但暂不启动

> 用 WatcherSupervisor 托管 overlayMonitor 生命周期（CDP 不可恢复→停避免僵尸轮询；重连→重启），取代裸 overlayMonitor.start()（否则会话失联后监测体空轮询到进程退出）

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:459-473（scheduleProbe / stopProbe，唯一的长跑定时器，2 秒固定节拍、Facebook 专属）、:486-488（探针失败只打一行日志）；宿主 /Users/baitianxing/codes/aidcp-edge/src/main.ts 已无 `session.cdp.on('cdp.unrecoverable' → 停监测体)` 这条接线（只在 :1754 有与执行器隔离相关的另一处订阅）`
- **具体缺哪几样**：
  1. 缺统一托管：Native 会话只有一个 Facebook 专属的 `probeTimer`，没有可注册多个监测体的管家，也就没有 startAll/stopAll 这对整批操作
  2. 缺 CDP 健康联动：`cdp.unrecoverable` / `cdp.reconnected` 不再停/重启探针；连接死掉后 `scheduleProbe` 的 2 秒循环会一直靠 `probeFacebook` 的 catch 打日志（browse-session.ts:487）跑到进程退出——正是旧注释点名要治的僵尸轮询
  3. 缺存活度量：没有「上次成功探测距今多久」的读数，上层无从判断「已经看不见了」，探测持续失败与「确实没情况」在外部看来完全一样
  4. 把可配节拍换成写死 2 秒（browse-session.ts:464 的 `2_000`），旧骨架的 `pollMs` 默认 1000 且可注入
  5. 缺 sticky/reset 两档容错策略的选择位（旧骨架 onProbeError），Native 探针失败既不保持上一状态也不回落初始态，只是丢弃这一拍
  6. 「装配但暂不启动」这条待机语义在 Native 侧靠 `blocked` / `closed` 与 `start()` 隐式覆盖，没有对应日志，运维看不出监测体是「没装」还是「装了没开」
- **可 port 的旧测试**：
  - CdpOverlayMonitor.stop: 停止后即便定时器回调触发也不再 tick —— 锁启停幂等与停止后不再探测（可直接移植为 Native 探针的停止契约）
  - CdpOverlayMonitor.tick: 状态翻转触发一次 onTransition；同状态不重复触发 —— 锁翻转唯一性（骨架级）

### 小红书四处提交窗口整体消失

- **对应任务**：2.1（四条标签与预算）、2.2（Rust 执行入口接窗口请求器 + 开窗/关窗位置）、2.3（宿主注入去平台闸）、2.4（拿不到窗口即诚实未开始 + 抢占回「窗口占用中 + 剩余预算」）、2.5（终态必关窗）。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/execution/commit-window.ts:1-75（守卫语义：时基兜底自动过期 + 世代守卫防误关 + 预算<=0 不开假窗 + combineCommitWindows 聚合）；四处开窗点：/Users/baitianxing/codes/aidcp-edge/src/browse/browse-session.ts:2583（`enter(4000,'xhs_comment_submit')`，迁前 317cd47^ 同文件:2578）、:3109（`enter(20000,'xhs_notification_comments')`，迁前:3104）、:3163（`enter(20000, likes?'xhs_notification_likes':'xhs_notification_follows')`，迁前:3158）、/Users/baitianxing/codes/aidcp-edge/src/flows/publish-command-handlers.ts:1372 与 :1388（`publishGuard.enter(15_000,'xhs_publish_submit')`）；注入点 317cd47^:src/main.ts:1292（`commitWindow: browseGuard, // 5.1：XHS 评论提交 + 通知分类栏目点击窗口`）`
  - 机制：旧实现在每个不可逆写入动作真正点下去之前开一个有界窗口，协调器抢占前先读窗口是否开着：窗口内绝不强杀已提交动作（回一个「窗口忙」加剩余预算），窗口外才可抢占。守卫本身有两条安全设计——时基兜底（按当前时间是否小于窗口截止判定，即使关窗回调因异常或崩溃从未被调用，窗口也会在预算耗尽后自动过期，一个卡死的窗口绝不永久挡住抢占）和世代守卫（每次开窗递增世代号，关窗回调只关自己那一代，迟到的旧回调绝不误关新开的窗口）；预算不为正视为不开窗，绝不开一个已经过期的假窗口。四处开窗各有各的理由与预算：评论提交点下去就进入「已提交、结果未知」区，此后取消等于把一条可能已经发出去的评论当成没发生、上游重试就是重复评论，故 4 秒窗口覆盖点击那一刻，其后的后置校验属禁区不许取消；两处通知分类栏目点击「消费未读、无回滚」，窗口必须覆盖点击瞬间，确认与滚动尾段只读、即使超预算自动过期也安全，故给 20 秒并由 finally 关窗（含 no_target 早退路径）；发布提交给 15 秒。多个写者的窗口再经聚合器合成协调器要的两个读法（任一开着 / 开着那个的剩余预算）。
- **旧代码记下的真机经验**：

> 页面写者在进入**不可逆提交动作**（发布提交点击 / 评论回车 / 加群点击 / 通知分类栏目点击）之前 `enter(budgetMs)` 开一个有界窗口，拿到确认 / 预算耗尽后 `dispose()` 关闭。协调器抢占前读 `isOpen()`：窗口内**绝不强杀已提交动作**（回 window_busy + `remainingMs()` 剩余预算），窗口外才可抢占。

> ① **时基兜底自动过期**：`isOpen()` 按 `now < openUntil` 判定，即使 dispose 因异常/崩溃从未被调用，窗口也会在 `budgetMs` 后自动过期——一个卡死的窗口绝不永久挡住抢占。

> ② **世代守卫防误关**：`enter` 递增世代号，`dispose()` 只关闭自己那一代的窗口；一个迟到的旧 disposer 绝不误关一个新开的窗口（重叠/连续提交下不串味）。

> `budgetMs<=0` 视为不开窗（返回 no-op disposer）——绝不开一个已过期的假窗口。

> 把多个写者各自的提交窗口聚合成协调器 `writers` 探针要的两个读法。系统中同一时刻至多一个独占任务在跑 ⇒ 至多一个窗口开着，取「任一开着」/「开着那个的剩余」即可。

> // 4b) 整条评论流的**最后一个安全取消点**：点下去就进入「已提交、结果未知」窗口，
>       //     此后取消 = 把一条**可能已经发出去**的评论当成没发生 ⇒ 上游重试 ⇒ 重复评论。

> // 🔴 提交窗口开启（5.1）：点下即进入禁区，协调器此间不强杀（回 window_busy + 剩余预算）。

> // 🔴 提交键已点下：以下后置校验 MUST NOT 取消（禁区）。

> 提交窗口守卫（5.1）：分类栏目点击**消费未读、无回滚** ⇒ 窗口 MUST 覆盖点击那一刻；确认/滚动尾段只读，超预算自动过期也安全。

> 提交窗口守卫（5.1）：分类栏目点击消费未读、无回滚 ⇒ 窗口 MUST 覆盖点击；早退(no_target)/尾段都由 finally 关窗。

> commitWindow: browseGuard, // 5.1：XHS 评论提交 + 通知分类栏目点击窗口

> publishGuard 归发布写者（XHS runSubmit + FB publish-executor）；browseGuard 归浏览写者（XHS 评论/通知分类、FB 评论/加群）。在此集中创建、下注入各写者（enter/exit），并（批 B-2b 激活时）经 combineCommitWindows 聚合喂给协调器 writers 探针。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:596-600（`execute_xhs_command_once` 的签名里**没有** `commit_windows` 形参，只有 session/command/cancellation/deadline）、:563-566（Xiaohongshu 分支调用它时把 `commit_windows` 丢弃）；/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:237-239（宿主只在 `platform === 'facebook'` 时把窗口处理器传下去）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:236（`interaction_comment` 直接 `click(submit)`，无开窗）、:224（三个 `notification_browse_*` 直接点 tab，无开窗）、:272（`publish_submit` 直接 `click(submit)`，无开窗）`
- **具体缺哪几样**：
  1. 缺机制：Rust 的小红书执行入口 `execute_xhs_command_once`（engine.rs:596）根本没有 `commit_windows` 形参，Facebook 分支拿到而小红书分支被丢弃（engine.rs:563-566 vs :585-592）
  2. 缺宿主接线：`NativeBrowseSession.executeAndReport` 的窗口处理器带 `platform === 'facebook'` 条件（browse-session.ts:237），小红书传下去的是 `undefined`
  3. 缺评论回车窗口：预算 4000 / 标签 `xhs_comment_submit` 无对应物；xhs-command-router.js:236 直接 `click(submit)` 后 `await sleep(800)` 做后置校验，这 800ms 完全裸露在抢占之下
  4. 缺两处通知分类栏目窗口：预算 20000 / 标签 `xhs_notification_comments` 与 `xhs_notification_likes`/`xhs_notification_follows` 无对应物；router:224 点 tab 后直接抽项，「消费未读、无回滚」这一段无保护
  5. 缺发布提交窗口：预算 15000 / 标签 `xhs_publish_submit` 无对应物——注意宿主侧 `NativePublishExecutor` 是**无条件**把窗口处理器传下去的（publish.ts:56-57），但 Rust 小红书 `publish_submit` 走 `evaluate_router`、从不发起请求，所以处理器空转
  6. 缺「拿不到窗口即诚实判未开始」这条：Facebook 侧拿不到确认会返 `CommitWindowUnavailable`（commit_window.rs:107-112），小红书侧因为从不请求，等价于「无声照写」
  7. 注：Rust 侧的窗口协议与预算表已经存在且可复用（commit_window.rs:38-88 请求/应答，facebook/capability.rs:36-47 三张契约 `fb_join_click`=18500 / `fb_comment_enter`=20000 / `fb_publish_submit`=20000），缺的是小红书那四条契约与它们的 `enter` 调用点
- **可 port 的旧测试**：
  - CommitWindowGuard: enter 开窗、dispose 关窗；剩余预算如实 —— 锁开窗/关窗/剩余读数（test/execution/commit-window.test.ts）
  - CommitWindowGuard: 时基兜底：disposer 从未调用也会在预算耗尽后自动过期（卡死窗口绝不永久挡抢占） —— 锁安全设计①
  - CommitWindowGuard: 世代守卫（迟到的旧 disposer 不误关新窗） —— 锁安全设计②
  - executeComment: 提交后未确认生效 → ok:false reason submitted_unconfirmed（已提交、结果未知，绝不谎报未提交） —— 锁提交窗口存在的理由：已派发不得降格为未提交
  - 取消点: 评论逐字输入中途被接管 → 立刻停手 + 清场 + 诚实回 preempted_by_task（半截评论绝不留在框里） —— 锁「窗口之前可取消、窗口之内不可取消」的分界
  - browse-session: 通知分类点击未命中 tab → 诚实 no_target（不假报已看） —— 锁早退路径也必须正常关窗（对应 finally）
  - Native Facebook forwards the exact Join commit window to the shared coordinator guard（test/native-page-engine/browse-session.test.ts:300）—— 现成的 Native 侧窗口透传契约测试模板，小红书四条照此各写一条

### 验证码协助键入取证被按请求推断

- **对应任务**：3.1、3.2、3.3、3.4、3.5、3.6（仅覆盖「键入取证」与 `inputMode` 这一支）。**未覆盖**：`replayMode` / 轨迹回放 / 点击拟人节奏 / 落点数预检 / 回放前陈旧复检 / 抓帧前阻断复检 / 快照 crop 与 kind / 实时抓帧的连续 K 次清除判定与互斥 / 提交后有界复检 —— 见文末覆盖漏洞。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/captcha-assist.ts:445-659（runTypeSequence 全链取证）、:59-64（三个预算常量）、:66-79（点击拟人节奏基线）、:81-89（按 edgeId 派生每机偏置）、:105-120（快照环 8 帧 / 实时抓帧钳制 / 连续 3 次无遮罩才判清除）、:247-299（注入前的 invalid_target 三道预检）、:300-307（轨迹有效性与 replayMode 诚实标注）；云端探测器 /Users/baitianxing/codes/aidcp-cloud/src/comm/captcha-assist.ts:255-262（textNotExecuted 版本偏斜检测）`
  - 机制：旧实现把「有没有真打字」做成由真正派发字符的执行体产出的逐字段取证，随回执透传：焦点档位与焦点元素标签、清空结果、真实派发字符数、回读结论（匹配/不匹配/不可验证）、是否真按了提交键。其中派发字符数刻意由闭包逐字更新——被抢占或超预算时派发函数不返回、其内部计数丢失，只有闭包捕获的那个值才是真实数，用于如实回报；已派发的部分留在页面上就清场并如实回报，绝不提交。顺序被明确钉死为「打字 → 回读 → 提交」，反了必假阴性。提交前还要复检两件事：遮罩是否已经不在（可能是键入本身触发自动校验清掉了），焦点是否还在原档位（丢了就停手不提交，因为回车会从错误上下文提交）。提交后做 4 次 500 毫秒间隔的有界复检，途中探测抛错不据此判失败（回车常触发导航、探测打不到页面属正常），4 次全抛则诚实回「提交后无法取得判定」并带上已提交位，绝不误报点击失败。云端专门据此设了一道版本偏斜探测器：下发了文本却回执的输入模式不是「点击加键入」，就判定是老边缘忽略了文本、只点了坐标，标记出来告诉运营「客户端太旧、键入未执行」，而不是把只点击的结果当键入成功。
- **旧代码记下的真机经验**：

> 键入序列硬顶：24 字 × (110 flight + 75 dwell + ~60 RTT) + 长停顿 ≈ 8s，20s 远在 45s acquire 之内（design D12）。

> 逐字键入的对数正态中位(ms)，按 edgeId 派生每机偏置后传入 dispatchHumanTyping（design D2）。

> 提交后有界重试的 fresh 复检（迭代限界，绝不用 now() 当唯一终止条件）。

> typed 在闭包里由 onProgress 逐字更新：抛出（被抢占 / 超预算）时 dispatchHumanTyping 不返回、其内部计数丢失，只有闭包捕获的这个值才是真实派发数，用于「如实回报 typed」。

> // 已派发的部分留在页面上 ⇒ 清场 + 如实回报 typed，MUST NOT 提交。

> // ── 5.6 回读（editable 才有意义；顺序 MUST：type → read → submit，反了必假阴性）──

> // 遮罩在 Enter 前消失：键入本身可能已触发自动校验并清除（typed=N，未按 Enter）。

> // 焦点丢失/转移：Enter 会从错误上下文提交。停手不提交，诚实回执 + 重抓帧。

> // Enter 提交常触发导航，probe 打不到页面属正常；下一拍再试，绝不据此报 failed。

> // 4 次复检全抛：绝不误报 click_failed（那是 task 0 修的洞）。诚实 verdict_unavailable_after_submit + submitted 位（在 report 里）+ 尽力回带新帧。

> // ── 5.4 focus 探针 ── none = 唯一结构确定的失败 ⇒ no_target，零派发，绝不提交。

> // 探针抛错 fail-closed：无法确认焦点落定，绝不盲打。

> 自主判"验证码已清除"需连续 K 次探测都无遮罩才成立——多步验证码在旧挑战消失、新挑战未绘出之间有瞬时无遮罩窗口，单次没看到就发 risk.captcha_cleared 会提前解 restricted（自残）。

> 边缘环 > 云端近期集，确保云端放行的 snapshotId 边缘一定还留着（云端拦不到、边缘却已淘汰 = 白跑）。

> // 点击全程暂停实时 tick（互斥），避免抓到点击派发中途 / settle / 复检期间的画面。

> // 可观测丢弃：轨迹畸形/超限被丢，如实标注回落，绝不静默、绝不谎称用了轨迹。

> 现役日常点击默认 overshoot~15% / jitter 3 / moveDelay 8；验证码是反爬审查最严、专门用鼠标轨迹熵做指纹的场景，这里取**不低于日常**的档：恢复 overshoot + 小幅 jitter + 略慢移动 + 落点前读图停顿 + 点间对数正态停顿。中心值按 edgeId 派生每机偏置（见 captchaPacing），避免全 fleet 逐字相同的节奏自成车队指纹。

> 按 edgeId 派生 [-0.15, 0.15) 的每机偏置（FNV-1a），打散车队级节奏指纹。

> 落点回放前强制复检（change lease-strict-preemption 5.7）：快照是运营几十秒前看到的那一帧，落点按那一帧标定。回放前若页面已不是那一刻——阻断自行消失 / 换了阻断类型 / 页面被导航走——照旧坐标盲点就是在错误页面上乱点（抢占落地后那"错误页面"很可能正是发布编辑页）。

> 版本偏斜检测（change captcha-assist-text-answer，design D8 第二道）：下发了 text（textLen>0）却回执 inputMode 不是 click_type ⇒ 老边缘忽略了 text、只点了 points（能力闸漏网 = 闸自己错了）。标记以便控制台告知"客户端太旧、键入未执行"，而不是把只点击的结果当键入成功。typeReport 绝不含答案本身（D10）。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/main.ts:1007-1015（`replayMode: 'synthetic'` 写死、`inputMode: typeof payload.text === 'string' ? 'click_type' : 'click'` 按请求载荷推断）、:1002-1006（status 只由 reason 三分）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:1434-1454（`captcha_click_result` 的 ActionReceipt 里没有任何键入取证字段）、:1299-1370（键入/回读/提交各失败点只回一个 reason 字符串）、:1156-1237（capture_captcha 无阻断前置复检、无遮罩裁剪）；/Users/baitianxing/codes/aidcp-edge/src/main.ts:930-935（快照 crop 恒为整视口 `{x:0,y:0,...}`、kind 恒为 `'captcha'`）`
- **具体缺哪几样**：
  1. `inputMode` 由请求载荷推断（main.ts:1015 `typeof payload.text === 'string' ? 'click_type' : 'click'`）而不是由真派发字符的执行体产出 ⇒ 云端 textNotExecuted 探测器（aidcp-cloud/src/comm/captcha-assist.ts:257-259）永远不响，被彻底废掉
  2. `typeReport` 五个字段（focus / focusTag / cleared / typed / verified / submitted）在 Rust 回执结构里完全不存在（engine.rs:1441-1451 的 ActionReceipt 无对应字段），宿主也不填 ⇒ 「打了几个字、清没清干净、回读对不对、到底按没按回车」全部不可知
  3. `replayMode` 写死 `'synthetic'`（main.ts:1014），轨迹回放能力整体缺席：无 `sanitizeTrajectory` 校验、无「轨迹畸形→诚实回落并标注」的可观测丢弃
  4. 缺点击拟人节奏：Rust 只做 mouseMoved/Pressed/Released 加固定 80ms 间隔（engine.rs:1287-1298），旧实现的 jitter 2 / overshoot 概率 0.22 / moveDelay 11ms / 落点前读图停顿（中位 650ms，界 280–1600）/ 点间对数正态停顿（中位 950ms，界 420–2600）/ 上一点真实落点作下一点起步的光标连续性 / 按 edgeId 派生 ±0.15 每机偏置，全部没有对应物
  5. 缺「带文本时落点必须恰好 1 个」这道注入前预检：Rust 只校验 1..20（command.rs:729-731），带文本时最多 20 次盲点后再打字；旧实现落点不等于 1 就零派发回 invalid_target（captcha-assist.ts:289-296）
  6. 缺回放前的陈旧复检：旧实现在派发前判「阻断已自行消失 / 换了阻断类型 / 页面被导航走」三态并诚实拒绝 + 重抓帧（captcha-assist.ts:315），Native 只按 incidentId+snapshotId 找到快照就直接按坐标点（engine.rs:1245-1258）
  7. 缺抓帧侧的阻断前置复检：`capture_captcha`（engine.rs:1156）不判是否真被阻断 ⇒ 旧实现的「fresh probe 说没被阻断 → 只回 not_blocked、绝不发 cleared」这条诚实路径消失
  8. 缺遮罩裁剪：快照 `crop` 恒为整视口（main.ts:934 `{x:0,y:0,width,height}`），旧实现按遮罩矩形裁剪；`kind` 也恒为 `'captcha'`（main.ts:932），`unknown` 类阻断的协助帧被误标
  9. 缺实时抓帧循环的自主清除判定：旧实现连续 3 次探测无遮罩才发清除（LIVE_CLEAR_CONFIRMATIONS=3，防多步验证码的瞬时无遮罩窗口造成提前解 restricted 自残），Native 的抓帧循环（main.ts:975-993）只换帧、不判清除、从不发 `risk.captcha_cleared`
  10. 缺「点击全程暂停实时抓帧」的互斥（旧 `this.writing`）；Native 只在收到点击命令时把 live token 删掉（main.ts:956），settle 与复检期间没有防止抓到中途画面的机制
  11. 提交后复检从「4 次 × 500ms 有界重试 + 途中抛错不判失败 + 全抛则 verdict_unavailable_after_submit」换成「固定 settle 后单次 probe」（engine.rs:1418-1431），回车触发导航时那一次探测失败会直接被算进 blocked 判定
- **可 port 的旧测试**：
  - 键入：可编辑焦点 → 打字 + 回车 → 遮罩清除 ⇒ cleared + risk.captcha_cleared + typeReport 齐全 —— 锁取证字段必须齐全（这条正是新实现必然失败的那条）
  - 键入：焦点没落定（none）⇒ no_target，零字符派发、绝不提交 —— 锁 focus 探针的唯一结构性失败
  - 键入：中途复检 #1 遮罩已不在 ⇒ cleared_mid_sequence，零字符派发 —— 锁键入前复检
  - 键入：被抢占 ⇒ typed<len + 清场 + 未提交（reason takeover_during_type） —— 锁「如实回报真实派发数」这条核心不变量
  - 键入：Enter 提交后复检连抛 ⇒ verdict_unavailable_after_submit（不是 click_failed） —— 锁「探测打不到页面不等于失败」
  - 键入：带 text 但落点不是恰好 1 个 ⇒ 注入前拒绝（invalid_target），零点击零键入 —— 锁落点数预检
  - 键入：表外字符 ⇒ 注入前整单拒绝（text_unsupported_char），绝不"只帮你点一下" —— 锁字符集预检的拒绝时机（Native 有等价校验但需确认回执形状一致）
  - captcha assist capture: fresh probe says not blocked → 只回 not_blocked，绝不发 risk.captcha_cleared —— 锁抓帧前的阻断复检
  - captcha assist capture: 注入进行中 → 跳过抓帧，绝不回传半程画面 —— 锁抓帧与点击互斥
  - live capture: 自主判清除需连续 K 次无遮罩，且只发 risk.captcha_cleared（不发 click_result） —— 锁连续 3 次确认
  - live capture: 连续无遮罩不足 K 次不清除 —— 同上的否定面
  - 帧环：点击稍旧但仍在环内的 snapshotId 被接受；不在环内的判 stale_snapshot —— 锁 8 帧环语义（Native MAX_CAPTCHA_SNAPSHOTS=8 已对齐，可直接立契约）
  - 轨迹回放：带有效轨迹 → click_result replayMode=trajectory，落点权威 (200,150) —— 锁 replayMode 必须反映实际回放方式
  - 轨迹回放：畸形轨迹（clicks 长度不符）→ 诚实回落合成，replayMode=synthetic —— 锁可观测丢弃
  - 回放前复检：阻断已自行消失 → 只回 not_blocked（不发 cleared），绝不派发盲点 —— 锁回放前陈旧复检
  - 回放前复检：页面已被导航走（URL 变）→ stale_snapshot + 重抓帧，绝不派发盲点 —— 同上
  - 拟人注入：多点连续光标（下点从上点真实落点起步）+ press 数==落点数 + 有 mouseMoved 轨迹 —— 锁点击拟人化（可移植为 Rust input 层契约）
  - 拟人注入：真实随机源下落点仍落在 target±jitter 容差内（jitter 有界不脱靶） —— 锁抖动有界

### 逐命令回执诊断与在场感被平台判据包住

- **对应任务**：4.1（逐命令回执诊断平台中立）、4.2（会话级诊断）、4.3（闭环留证 + 不带正文/凭据/选择器）、4.4（明确不补在场感 / 陪伴界面事件，属产品范围）。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/browse-session.ts —— 全链每步都有 `[browse] …` 诊断行，例如 :3088（`notification.home: 评论N 赞藏N 关注N（无数字红点的 tab 待真机校准）`）、:3139（`notification.items: 上报 N 条评论/@`）、:3170（`${action}: 未找到分类 tab（no_target，不假报已看）`）、:3444（`检测到${label}弹窗，暂停操作，等待处理…`）、:3438（`阻断弹窗已消失，恢复浏览`）；317cd47^:src/main.ts:1385-1387（阻断上报的中文告警）`
  - 机制：旧实现在浏览闭环每一步都打一条带结果的诊断行：进了哪个分类、抽到几条、点没点中（未命中就明说是 no_target 而不是假报已看）、阻断弹窗出现与消失各一次、上报了什么。这些行同时被外壳用来点亮客户端的运行态。
- **旧代码记下的真机经验**：

> // 出现 / 消失各只记一次日志（blockingOverlayActive 状态翻转才打），不刷屏。

> 未命中分类 tab（选择器漂移/页面未渲染/单合并 tab）→ 诚实 no_target，**绝不**像旧码那样丢弃返回值、无条件报 viewed（那是静默假成功，且掩盖了 6.5.4 本要暴露的选择器漂移）。

> notification.open 失败（上报全 0 以便分诊收尾）

> 断连不当业务失败：冒泡到主循环重连，绝不假报「无未读」

> 既有 edge-fleet-console 规格要求被验证码拦住的环境必须浮到最上，但这条中文日志不含壳侧兜底正则要的「弹窗」「暂停操作」（那张表是小红书专属的）⇒ FB 环境的阻断态**从不置真**，卡在验证码上的机器在客户端里一直是绿的、运营不知道该救哪台。绝不靠措辞匹配，走结构化行。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:351-357（逐命令回执诊断整段包在 `if (this.options.platform === 'facebook')` 内）、:285-297 与 :312-329（page_cards / note_detail 的在场感事件同样只在 Facebook 分支）、:387（`emitFacebookAction` 只对 Facebook 调）；小红书侧只剩 :113（启动一行）与 :153（失败一行）`
- **具体缺哪几样**：
  1. 逐命令回执诊断（action / ok / effectPhase / reason 四元组）只在 Facebook 打（browse-session.ts:351-357）⇒ 一次小红书浏览闭环在日志里只剩「session ready」与「failed」两行
  2. 在场感 / 活动事件（feed 浏览、读贴、点赞、关注、评论、加群、popup、popup_cleared）全部在 Facebook 判据内 ⇒ 小红书环境在客户端左栏没有运行态叙述，被验证码拦住时也不会置「需要处理」态
  3. 注意方向相反的一处历史教训：壳侧的兜底正则（认「弹窗」「暂停操作」）原本是**小红书专属**的，Facebook 因为文案不含这两词而阻断态从不置真；现在小红书连那条中文日志也不打了，等于把两边都变成了「绿的」
- **可 port 的旧测试**：
  - Native Facebook action receipt logs bounded terminal phase and reason without payload content（test/native-page-engine/browse-session.test.ts:157）—— 现成模板，去掉平台条件后即可作为小红书的同款契约

### 恒假短路死码块内含而新引擎无对应物的能力清单

- **对应任务**：6.1（逐项对账）、6.2（删块与影子声明）、6.3（源码级检查禁止再现）、6.4（孤儿模块三分类）、6.5（工厂成员裁定）。
- **oracleQuality**：`direct`
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/main.ts:1043（`if (false && platformDriver.runtimeKind === 'browser') {`）至 :1213（块尾），共 170 行；配套影子声明 :88-103（`declare const WatcherSupervisor` / `evalRaw` / `createOverlayReportGate` / `captureBlockingOverlaySnapshot` / 五个 Facebook 类型与常量），注释自称「Review-only declarations for the compile-time-unreachable legacy assembly below」`
  - 机制：这 170 行是 07-23 之前真正在跑的 Facebook 浏览装配：创建带 lastScanText 的浮层监测体、按环境变量取确认窗（默认 2000ms）、进入阻断态时预热一张结构化现场快照、上报时若候选筛选落空就用监测体同源扫描文本回填证据、经上报闸做 unknown 延后确认与 detected/cleared 严格配对、把监测体挂进管家并与 CDP 不可恢复/重连联动、按冷待机与暂停态决定是否启动、装配带提交窗口的评论与加群执行器、创建带 feedUrl/startupId/tempo 的浏览会话、注册带任务租约与续租的命令路由、注册时先做一次交接收敛、并在检出与清除时各发一条结构化的客户端「需要处理 / 已恢复」事件。它被改成恒假而非删除，配上类型影子声明让编译通过——typecheck、剪枝、单测全绿，没有任何一道闸提示这段能力已不再执行。
- **旧代码记下的真机经验**：

> // Historical JavaScript Facebook assembly is compile-time unreachable during the cutover.
>   // The dist verifier rejects its selectors/modules, so this cannot become a packaged fallback.

> // Review-only declarations for the compile-time-unreachable legacy assembly below. `import()`
> // appears only in type positions and is erased by TypeScript, so none of these modules enters
> // the production dependency graph or provides a runtime fallback.

> FB 浏览高危动作会触发验证码 / FB 软限流（overlay.ts 归类 unknown）。把 captcha/unknown 翻转上报云端（risk.captcha_detected/cleared）：驱动远程验证码协助 + FB 限流退避（account-nurture-discipline-spine 云端 facebook-throttle-signals 依赖此信号把账号迁至 restricted）。复用小红书同一套上报闸（unknown 延后确认 / captcha 即时 fail-closed / detected-cleared 严格配对）。执行器另有每步 fresh 复检做本地 fail-closed。

> change fb-throttle-popup-zh-frequency-copy：回填同源证据用的监测体句柄。此块只在 useFacebookBrowse 下装配，driver 必返 FacebookOverlayMonitor；instanceof 只是诚实收窄——万一不是，回填静默不发生、退化为改动前行为（不假造证据、不假成功）。

> 快照候选筛选对 FB 标准限流弹窗必然落空（无 iframe / 未达尺寸阈 / 有关闭控件）⇒ overlay.text 为空 ⇒ 云端「无文案不臆断限流」返否定 ⇒ 真限流只到 warned 降速而非 restricted 刹车。用判定同源文本回填证据；判定本身不变。

> 清除侧同样必须显式：此前 FB 这条路径**什么都不打**（小红书侧会打），两侧都没有 ⇒ 阻断态只能靠「任何一次成功动作顺带清掉」这种假清除退出（已在壳侧收紧为只认本事件）。

> 用 WatcherSupervisor 托管 overlayMonitor 生命周期（CDP 不可恢复→停避免僵尸轮询；重连→重启），取代裸 overlayMonitor.start()（否则会话失联后监测体空轮询到进程退出）。

> 交接现在有界且会诚实抛出（change lease-strict-preemption）。此处是**全新会话**（零在飞写者），必然瞬时收敛；catch 只为不让一个诚实异常炸掉装配流程。

- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:459-578（Native 侧的 Facebook 阻断观测与上报，是块内 a/b/d/e/n 项的接替者）、:213-218（applyPacingSnapshot 空实现）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/capability.rs:36-47（三张提交窗口契约，接替块内 i 项）`
- **具体缺哪几样**：
  1. 【无对应物 1】结构化现场快照 `captureBlockingOverlaySnapshot`（:1066）：主候选 DOM 特征 + 最多 3 个备选候选 + rect / position+zIndex+opacity / iframeSrcs / hasClose / matchReasons / selector 路径。Native 上报把 `candidates` 写死为空数组（browse-session.ts:566），只带一段截断到 1000 字的 blockingText
  2. 【无对应物 2】上报闸的 episode 世代机制（:1113 → overlay-report-gate.ts:43-63）：离开阻断态即自增世代号、令在途的延后确认作废。Native 的手搓等价物（browse-session.ts:512-535）只有一个已报类型标记与一个 timer，没有世代号
  3. 【无对应物 3】阻断上报时的现场快照诊断行（旧 XHS 段 317cd47^:src/main.ts:1372-1377 打 `{kind, firstDetectedUrl, text, dom}`）—— Native 两侧都不打
  4. 【无对应物 4】监测体管家与 CDP 健康联动（:1139-1147 `fbSupervisor` + `cdp.unrecoverable` → stopAll / `cdp.reconnected` → startAll）—— Native 的 `probeTimer` 与 CDP 健康完全脱钩
  5. 【无对应物 5】连接级节奏快照注入（:1179 `tempo: client.getPacing()?.tempo`，旧 XHS 段还有 `opFloorsMs` 与 `dwellFloorMs`）—— Native 的 `applyPacingSnapshot` 是空函数（browse-session.ts:213-218，注释 `Pacing stays Cloud-owned`），身份翻转/重连后重注入这条路没有落点
  6. 【无对应物 6】监测体的即席复检接口（旧 `overlayMonitor.probeNow()` 供高危动作提交前 fail-closed 用）—— Native 把它内化进 Rust 的 `ensure_facebook_action_gate`，宿主侧不再有可调的即席探测句柄；小红书连 Rust 侧的动作闸也没有
  7. 【已有 Native 归属，不算缺】确认窗环境变量与默认 2000ms（:1058 ↔ browse-session.ts:520）；同源文本回填（:1087 ↔ FB 路由自带 blockingProbe 直出 blockingText，facebook-router/05-session.js:31-58 + 90-dispatch.js:46-47）；评论/加群执行器的提交窗口（:1154 / :1160 ↔ facebook/capability.rs:36-47 的 `fb_comment_enter`=20000 / `fb_join_click`=18500）；命令路由的任务租约与续租（:1183-1197 ↔ main.ts:1229-1243）；注册时交接收敛（:1200-1204 ↔ main.ts:1245-1249）；结构化 popup / popup_cleared 客户端事件（:1105 / :1124 ↔ browse-session.ts:543-548 与 :572-577，但仅 Facebook）
  8. 【机制性问题】这 170 行加 :88-103 的 16 行影子声明构成一个「编译期不可达 + 影子声明」的保留形态：typecheck 穷举不到、剪枝脚本挡在产物外、单测不覆盖 ⇒ 能力整批静默消失而无任何一道闸报警。同一机制已付过一次代价：块内的 Facebook 软限流上报直到 54ae5b2（07-26）才在 Native 会话补回，其间限流文案不产生阻断上报
- **可 port 的旧测试**：
  - Native Facebook probe reports sustained unknown blockers with same-source evidence（test/native-page-engine/browse-session.test.ts:348）—— 现成的 Native 阻断上报契约，小红书需一条等价物
  - test/browse/overlay-monitor.test.ts 的 captureBlockingOverlaySnapshot / buildBlockingOverlaySnapshotJs 两条 —— 若要把结构化快照补回 Rust，这两条是现成的字段级契约

## 覆盖漏洞

参照书里有、但本 change 的 tasks 里找不到对应任务的条目，逐条列出并给出补法建议。
**这些都不是「实装时顺手做掉」的量级**——除第 6 条外，每条都够单起一节任务或单起一个 change；
起草时漏了它们，等于这次修完仍留着同类的静默失效面。

1. **高危动作提交前的即席 fresh 复检 + `blocked_by_captcha` 诚实回执**（参照条目 2）。
   tasks §1 只有会话级停手闸（1.6），没有任何任务要求 Rust 小红书侧补 `ensure_*_action_gate`
   （对照 Facebook 的 `ensure_facebook_action_gate`，`native/page-engine/src/shared.rs:376`）。
   旧注释点名了这条为什么必须存在：闸门读的是缓存、可能过期约一个节拍，闸门放行后到真正点击之间的拟人停顿里
   若弹出验证码，只靠缓存会漏。缺它 ⇒ 小红书点赞 / 收藏 / 关注 / 评论会在验证码墙上按下去，且没有 `blocked_by_captcha`
   这个诚实回执理由可回。**建议**：在 §1 追加一条任务（Rust 侧小红书动作闸 + 复检失败按「有挑战」fail-closed），
   并 port 旧测试「like 命中 captcha → 放弃点击并上报 `blocked_by_captcha`」。

2. **停手等待循环的三个出口**（参照条目 2）。task 1.6 只要求「被暂停期间收到的浏览命令回诚实的未开始」，
   没有钉住另外两个出口：① 队列里已到的会话结束命令必须绕过闸门（否则登录墙 / 验证码常驻时云端的终止命令也终止不了会话）；
   ② 任务接管信号到达必须**抛出**、命令零副作用作废，**绝不只 return**。旧注释把后者的后果写得很直白：
   交接等的是「命令处理函数还没返回」，于是它无界地等一条正在等验证码的命令，而那个验证码只有这次交接要授予的
   协助任务才能点掉 ⇒ 闭环死锁、整台机器停摆。**建议**：把这两个出口写成 1.6 的显式验收标准，
   并 port 旧的两条死锁回归测试（`session.end` 不被弹窗 / captcha 阻塞）。

3. **监测体生命周期托管与 CDP 健康联动整条**（参照条目 4，**全条无任务**）。缺：
   `cdp.unrecoverable` → 停全部监测体 / `cdp.reconnected` → 整批重启（启动幂等）；
   存活度量「上次成功探测距今多久」（旧 `msSinceLastOkTick`，设计理由是「绝不把探测不了当成没情况——那是传感层的假成功」）；
   可配节拍（Native 写死 2 秒，旧骨架默认 1 秒且可注入）；sticky / reset 两档容错的选择位；
   「已装配但暂不启动」的待机日志。**现状后果**：连接进入不可恢复终态后，Native 的 2 秒探针循环会靠 catch 打日志
   一路空轮询到进程退出——正是旧注释点名要治的僵尸轮询。**建议**：单起一节任务（或单起一个 change）承接，
   本 change 至少要在 1.2 里避免把「写死 2 秒 + 无健康联动」这个形状固化到小红书上。

4. **验证码协助除「键入取证」之外的其余 9 项**（参照条目 6）。tasks §3 只覆盖键入取证与 `inputMode`。未覆盖：
   ① `replayMode` 写死 `'synthetic'`、轨迹回放能力整体缺席（含「轨迹畸形 → 诚实回落并标注、绝不谎称用了轨迹」）；
   ② 点击拟人节奏（jitter / overshoot 概率 / 落点前读图停顿 / 点间对数正态停顿 / 光标连续性 / 按 edgeId 派生每机偏置）——
   验证码是专门用鼠标轨迹熵做指纹的场景，Rust 现在是固定 80ms 间隔；
   ③ 带文本时「落点必须恰好 1 个」的注入前预检（现在最多 20 次盲点后再打字）；
   ④ 回放前的陈旧三态复检（阻断已自愈 / 换了阻断类型 / 页面被导航走）——抢占落地后那个「错误页面」很可能正是发布编辑页；
   ⑤ 抓帧前的阻断复检（旧实现「fresh probe 说没被阻断 → 只回 `not_blocked`、绝不发 `cleared`」这条诚实路径消失）；
   ⑥ 快照 `crop` 恒为整视口、`kind` 恒为 `'captcha'`（`unknown` 类阻断的协助帧被误标）；
   ⑦ 实时抓帧循环从不发 `risk.captcha_cleared`，也没有「连续 3 次无遮罩才判清除」（旧注释：多步验证码在旧挑战消失、
   新挑战未绘出之间有瞬时无遮罩窗口，单次没看到就发清除会提前解 `restricted` = 自残）；
   ⑧ 点击全程暂停实时抓帧的互斥；⑨ 提交后从「4 次 × 500ms 有界复检 + 途中抛错不判失败」退成「固定 settle 后单次 probe」。
   **建议**：单起一个 change 承接（这批与本 change 的「小红书会话看护」主题不同，属验证码协助自身的诚实度），
   本 change 只保留 §3 的键入取证一支。

5. **身份重立链的后半段**（参照条目 3）。tasks 5.4 只到「退回无身份态前先诚实回执在途发布」。未覆盖旧链的其余步骤：
   停全部监测体 → 停浏览 → 断开云端（在途发布必须**在关连接之前**判失败，否则失败回执发不出去）→
   **先导航回消费端首页再读身份**（触发失效时可能停在创作发布页 / 弹层态而无锚点）→ 读不出就停在无身份态、
   **绝不回落默认账号**（红线）→ 用新 id 换云端会话并重连 → 重注入节奏快照 → rebaseline → 重启监测体与浏览。
   其中「重注入节奏快照」在 Native 侧没有落点（`applyPacingSnapshot` 空实现）。
   **现状后果**：5.1–5.4 做完只能「发现」身份失效，无法「恢复」——检出后系统停在哪一步、会不会以旧 accountId 继续跑，
   tasks 没有定论。**建议**：在 §5 追加一条任务明确检出后的处置终点（至少要有「停在无身份态、绝不回落默认账号」这条红线断言）。

6. **结构化现场快照的字段集**（参照条目 1 与 8）。Native 上报把 `candidates` 写死为空数组，只带一段截断到 1000 字的
   `blockingText`；旧实现带主候选的 DOM 特征（标签 / id / class / role / aria-modal / selector 路径 / rect /
   position+zIndex+opacity / iframeSrcs / hasClose / matchReasons）加最多 3 个备选。它是云端命名与运营分诊的证据源。
   tasks 里只有 6.1 要求把它「对账登记为缺口」，没有任务补回。**建议**：本 change 按 6.1 登记即可（不扩范围），
   但要在登记里写明它的下游影响（无候选证据 ⇒ 云端只能靠一段文本命名阻断），别登记成一条无后果的字段缺失。
