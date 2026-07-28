# 退役实现参照（oracle）

> 用途：本 change 的多数条目属「以前能做、迁移后做不了」。退役的 TypeScript 实现仍在
> `/Users/baitianxing/codes/aidcp-edge/src/` 下（被构建期剪枝挡在生产外、宿主装配被恒假条件短路），可直接当行为参照。
> **只当参照书，不得把退役实现搬回生产**——那会击穿本次迁移的动机，且宿主那段是死码不是开关。
> 迁移前版本用 `git -C /Users/baitianxing/codes/aidcp-edge show 317cd47^:<path>`（小红书）或 `4f04e9c^`（Facebook/微信）读。

> **行号核对**：本文件成稿时抽查了 11 处 oracleLocation（`src/humanize/mouse-path.ts:1-136`、`src/browse/cdp-util.ts:176-207` / `:242-260`、`src/locating/engine.ts:213-235` / `:238-243`、`src/locating/matcher.ts:19-31`、`src/locating/cache.ts:89-121`、`src/locating/extractor.ts:84-100`、`src/facebook/viewport-scroll.ts:50-107`、`src/facebook/reels-reader.ts:353-373`、`native/page-engine/src/facebook/shared.rs:802-820`、`native/page-engine/src/facebook/feed_like.rs:421-450`），逐条与工作树实际内容一致，无需标注「行号待核」。

## ⚠️ 不可照抄的条目（先看这段）

下面三条的旧实现**不是可信参照物**，照抄的后果各不相同：

### ⑨ Reels 的单帧滚轮与三条裸事件点击 —— also-wrong（旧实现也错）

- **旧实现位置**：`/Users/baitianxing/codes/aidcp-edge/src/facebook/reels-reader.ts:353-357、365-367、369-373（也有缺陷的部分）；531-536（可参照的浮层点击）`
- **为什么不能照抄**：旧的 Reels 实现本身就是「一帧滚轮 + 三条裸鼠标事件」，没有惯性序列、没有轨迹、也没有按下失败补发抬起：见 src/facebook/reels-reader.ts:353-357（trustedClick 三条裸事件）、365-367（trustedWheel 单帧）、369-373（滚轮位移 70~100px 均匀取值）。照抄这里等于把同一个盲区搬回来。真正可复用的参照物在同仓另一处：src/facebook/viewport-scroll.ts:50-107 的惯性手势与 src/browse/cdp-util.ts:242-260 的原子点击——Reels 应当改指这两个原语，而不是照抄 reels-reader。另外 reels-reader.ts:531-536 的浮层点击确实走了拟人点击（dispatchClick + from + overshoot:false），这一处是 direct 可参照的。

### ⑯ 闸③反污染回写与锚点缓存：整体不存在 —— also-wrong（旧实现也错）

- **旧实现位置**：`/Users/baitianxing/codes/aidcp-edge/src/locating/cache.ts:1-136（AnchorCache 全体；:43 confirmThreshold 默认 2、:89-99 stage、:104-116 confirmStaged、:119-121 dropStaged、:128-135 snapshot/load）；/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:148-160（缓存优先读）、:219-225（成功后 recordHit / stage+confirm）、:238-243（失败后 recordFailure / dropStaged）；/Users/baitianxing/codes/aidcp-edge/src/client/edge-client.ts:583-588（anchor.get 通道，零调用方）`
- **为什么不能照抄**：判 also-wrong：这一层旧实现自己也只做了一半。① 主缓存是纯进程内 Map，snapshot/load 全仓**零调用方**（只有 like-runner.ts:45 会 new 一个空缓存），进程一重启锚点全丢，所谓「晋升」在真机上从未跨会话生效过。② 跨进程/跨账号共享的那条路（协议 anchor.get / anchor.report）边缘侧只有一个 getAnchor 包装、同样零调用方，云端 PG 主缓存同步从未接线。所以照抄它只能得到一个「重启即空」的缓存；要在新引擎里做，必须把持有位置和持久化一并设计，不能只搬类。

### ⑱ 守卫层（干扰扫描 + 多轮清障 + guard_blocked 终局）缺失 —— stale（旧假设已过时）

- **旧实现位置**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:118-130（进主流程前先跑守卫，不过则 guard_blocked/guard_unhandled）、:268-291（handleGuards 多轮清障，maxGuardRounds 默认 2，仍有残留报 guard_persist）；/Users/baitianxing/codes/aidcp-edge/src/locating/guard.ts:41-63（三条内置规则）、:66-76（findByText 关闭类按钮）、:86-108（scanInterrupts，同一规则命中一次即止）`
- **为什么不能照抄**：判 stale：三条内置规则是 2026-06 的小红书 / 通用形态，其中『overlay_mask』靠 data-type="mask" 与 data-role 里的 mask/overlay/backdrop 识别，是当时那版 DOM 的特征；FB 与 Reels 的阻断浮层（同意、频率限流、参与答题、登录检查点）完全不在这三条里。可照抄的是**编排骨架与阈值**（动作前必扫、清障最多 2 轮、无配对关闭动作即 unhandled 停手、扫描不依赖混淆 class），规则库必须按当前各平台重建，不能照搬那三条 match 条件。另注意：新引擎已在别处积累了旧守卫没有的真机经验（FB 同意浮层、频率限流弹窗、参与答题闸），这些应并入新守卫规则库而不是被守卫覆盖掉。

**补注一（不属 stale / also-wrong，但同样不能机械照搬）**：缺口 ① 里「逐帧延迟叠对数正态抖动」与「落点前瞄准停顿」在退役实现里是**默认关闭的可选项**，全仓只有验证码协助一处开启（`src/browse/captcha-assist.ts:335-336`）。任务 1.4 要求的「帧间延迟非恒定」是相对退役**默认行为**的一次抬高，不是回退到旧状态；抬高依据写在退役代码自己的注释里（`cdp-util.ts:203`）。别把它当「旧版本就这样」汇报。

**补注二（design 已点名的反例，参照书内不含该文件）**：退役的 Facebook 会话（`4f04e9c^:src/facebook/facebook-session.ts` L722 / L738）对云端已下发的时长又乘了一次风控档位，与已归档 `command-pacing` 的「云端已下发 dwellMs 不再叠 tempo」直接冲突，**照抄即 double-count**。时间指令的可信参照物是退役的小红书会话（`src/browse/browse-session.ts:504-556`，见缺口 ⑩），不是 Facebook 会话。

## 逐条参照

### ① 点击轨迹：贝塞尔逐帧移动 + 过冲回拉 + 落点抖动 + 逐帧延迟

- **对应任务**：1.4、2.1、2.4、2.5、2.7、7.4
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/humanize/mouse-path.ts:1-136（生成器）；/Users/baitianxing/codes/aidcp-edge/src/browse/cdp-util.ts:176-207（dispatchHover 逐帧派发）、219-240（dispatchClick）；均仍在工作树，无需 git show`
  - 点击分两段：先把光标沿一条三阶贝塞尔曲线从「当前/附近某点」逐帧移动到目标，再在落点做按下-松开。曲线的两个控制点落在起终连线的 1/3、2/3 处，各自叠一个方向随机的法向偏移，偏移幅度是「起终距离的 10%~30% 之间均匀取值」，于是每次路径都是一条左右不定的弧线而不是直线。时间参数走三次 ease-in-out，使采样点在两端密、中段疏——回放出来就是「起步慢、中段快、逼近再慢」（Fitts 定律形态）。点数按距离自动定：距离除以 8，裁进 15~60。落点本身叠 ±jitter 像素的抖动（默认 ±3），返回的末点就是真实落点，调用方把它当下一次点击的起点，保证光标位置连续、不会每次都从凭空某处冒出来。默认 15% 概率触发过冲：抵达后沿运动方向多走 5~15 像素，再回拉到落点。所有点取整像素。逐帧之间等一个固定 8ms（约 120fps）；高审查场景可开「每帧走对数正态抖动」，把帧间隔方差为 0 这个机器特征打散。起点缺省时不是目标点自己，而是目标左上方 40~160 像素处的随机点（模拟光标本来在别处）。
- **旧代码记下的真机经验**：
  > 贝塞尔鼠标轨迹生成（非瞬移）。
  >
  > 背景（见 docs/risk-control.md §3.5 / docs/anti-detection.md §5.1）：绝不直接派发 mousePressed 到目标坐标（瞬移=机器）。真人鼠标从当前位置沿曲线移动到目标，速度服从 ease-in-out（Fitts 定律：先快后慢逼近），常有 overshoot（越过目标再回拉）。
  >
  > 控制点（docs/anti-detection.md §5.1）：
  >  *  - P0 = from；P3 = to + 落点抖动(±jitter px)
  >  *  - P1,P2 在 P0→P3 连线两侧加随机垂直偏移（offset ∝ 距离），产生自然弧线
  >  *  - 时间参数 t 走 ease-in-out，使点在两端更密（慢）、中间更疏（快）
  >  *  - overshoot：在抵达 P3 后沿运动方向多走 5–15px 再回拉到 P3
  >
  > // 点数 ∝ 距离（远则多点），裁剪到 [15, 60]
  >
  > // 两侧随机垂直偏移：幅度 = U(0.1, 0.3) × 距离，左右随机
  >
  > // overshoot：沿运动方向多走 5–15px 再回拉到 target
  >
  > /** 逐帧移动间的延迟(ms)，默认 8（约 120fps，自然且不拖慢） */
  >
  > 逐帧延迟是否叠对数正态抖动（change captcha-assist-humanize-click）。默认 false = 固定 moveDelayMs（等周期，浏览路径零回归）。true = 每帧 `jitterAround(moveDelayMs)`，打散 dt 方差为 0 的机器特征（验证码等高审查场景用）。
  >
  > // 默认起点：目标左上方一段随机距离（模拟光标本来在别处）
  >
  > // 返回真实落点（含 jitter/overshoot 残差），供多点循环把上一落点作下一点起点、保光标连续。
  >
  > 拟人化（见 docs/risk-control.md §3 / docs/anti-detection.md §5）：
  >  *  - dispatchClick 不再瞬移落点，而是先沿贝塞尔轨迹逐帧 mouseMoved 再 press/release；
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/shared.rs:802-820（dispatch_facebook_click）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:739-750（小红书搜索框点击）、1283-1297（验证码落点点击）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/feed_like.rs:421-450（反应浮层点击，仅此处有 5 帧插值）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/reels.rs:248-259`
- **具体缺哪几样**：
  1. 整个 Rust 引擎里 `bezier` / `overshoot` / `jitter` / `hover` 四个词零命中（对 native/page-engine/src/**.rs 全文 grep）——曲线生成器整体不存在
  2. 缺「移动路径」：shared.rs:809 / engine.rs:741 / engine.rs:1287 / reels.rs:250 都只在目标坐标发 1 帧 mouseMoved，等于瞬移，然后立刻 press/release
  3. 缺法向偏移与弧线：唯一有插值的 feed_like.rs:428-440 是起点→终点的直线线性插值（smoothstep 缓动），没有控制点、没有随机弧线
  4. 帧数从 15~60 降到 5（feed_like.rs:428 `for step in 0..=4`），其余点击是 1 帧
  5. 缺落点抖动：所有点击都精确落在探针返回的几何中心，没有 ±3px 残差，也就没有可继承的「真实落点」
  6. 缺过冲回拉：没有任何路径在抵达后多走 5~15px 再回拉
  7. 逐帧延迟从「8ms 或可选对数正态」换成固定 18ms（feed_like.rs:438），且只在 5 帧插值那一处存在；其余点击帧间无延迟
  8. 缺光标连续性：新点击不返回落点、没有 lastCursor 概念，每次点击的起点都由被调方自己决定（feed_like 用探针给的 from_x/from_y，其余无起点）
- **可 port 的旧测试**：
  - test/humanize/mouse-path.test.ts『起点接近 from，末点接近 to（含落点抖动 ≤ jitter）』——锁「末点=目标+有界抖动」，可 port 成 Rust 轨迹生成器的属性测试
  - test/humanize/mouse-path.test.ts『点数随距离增加，且在 [15,60] 区间』——锁帧数下限，直接反证「1 帧瞬移」与「固定 5 帧」
  - test/humanize/mouse-path.test.ts『轨迹是曲线而非直线（存在垂直于连线的偏移）』——水平连线上要求出现 >5px 的 y 偏移，直接反证线性插值
  - test/humanize/mouse-path.test.ts『ease-in-out：两端步距小、中间步距大（速度变化）』——锁中段步距 > 首步距且 > 末步距
  - test/humanize/mouse-path.test.ts『overshoot：末段先越过 to 再回拉』——锁倒数第二点越过目标、末点回到目标附近
  - test/humanize/mouse-path.test.ts『所有点为整数像素』
  - test/humanize/mouse-path.test.ts『极近距离：退化为两点』——锁短距不生成无意义曲线

### ② 点击原子性：按下抛错必须补发抬起

- **对应任务**：1.3、2.2、2.3、2.5、2.8
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/cdp-util.ts:242-260（commitLeftClick）；安全边界顺序见同文件 151-164、233-237`
  - 按下与松开被单独封成一个「提交式左键」函数，且这个函数的签名里刻意不带任何选项参数——词法上就插不进取消点，任何死线/接管检查都只能发生在它之前。函数体用 try/finally：按下抛错时 finally 仍补发一次松开，补发自身的失败被吞掉，原始异常原样上抛不被覆盖。设计理由写在注释里：按下发了、松开没发就是「左键按住不放」，此后所有移动都变成拖拽或框选，页面被不可见地污染，而调用方只看到一个普通异常。另有一条相关的诚实闸：在进入这个原子区之前触发一次「按下即将派发」回调，把上游的「已派发提交」标记置真——即便按下响应超时或松开抛出（点击可能已经生效），也绝不谎报「压根没点」，否则云端按「提交前失败」重投就会双发。
- **旧代码记下的真机经验**：
  > 提交式左键（mousePressed → mouseReleased 原子区）。
  >
  > **签名里没有 options** —— 词法上就插不进取消点。这里是「已执行、未后置校验」窗口的最恶形态：press 发了、release 没发即抛出 = **左键按下不松开**，此后所有 mouseMoved 都变成拖拽 / 框选，页面被不可见地污染，而调用方只看到一个普通异常。
  >
  > try/finally 保证 press 抛错也补发 release，且不覆盖原始异常。
  >
  > // 按下之前是点击路径的**最后一个安全边界**：过了这一行，点击必须原子完成。
  >
  > 「按下事件即将派发」回调（change lease-strict-preemption 6.2）：在 commitLeftClick（press→release 原子区）**之前**、通过安全边界（checkpoint/deadline）**之后**触发一次——此刻 press 已在飞往浏览器的路上。用于把「已派发提交 submitDispatched」诚实置真：即便随后 press 响应超时 / release 抛出（点击可能已生效），也已标记为已派发，绝不谎报「压根没点」→ 云端按提交前失败重投 → 双发。**MUST NOT 在此抛出**（非取消点）。
  >
  > 安全取消点：**接管优先于死线**——「我被抢走了」比「我超预算了」更接近事实，而下游要靠异常类型区分「未开始（可重派）」与「超预算失败」。顺序写反 = 一次接管被报成 fill_deadline_exceeded。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/shared.rs:811-819；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:743-750、1289-1296；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/feed_like.rs:441-449；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/reels.rs:252-259`
- **具体缺哪几样**：
  1. 五处点击全部写成 `press().await?` 紧接 `release().await`——按下失败时 `?` 直接早返回，松开永不发出，浏览器留在左键按住状态
  2. 缺 try/finally（或 Rust 侧等价的 scopeguard / 显式 match 后补发）：全仓无任何「press 失败仍补 release」的补偿路径
  3. 缺「按下-松开是原子区」的结构隔离：三条派发是平铺在业务函数里的裸语句，没有一个无参数的提交函数把取消点挡在外面
  4. 缺「按下即将派发」的诚实置真钩子：native 侧点击不向上报告「已派发」，publish 路径的 submit_dispatched 只在 JS 路由里由 `click(el)` 之后无条件写 true，与「press 已发但 release/响应失败」这一窗口无关
- **可 port 的旧测试**：
  - test/browse/cdp-util.test.ts『dispatchClick: mousePressed 抛错时仍补发 mouseReleased，且原始异常原样上抛』——同时锁补发与「不吞原始异常」
  - test/browse/cdp-util.test.ts『dispatchClick: 任意取消/死线点都不留下「按下未松开」』——先数出安全检查点总数，再逐个检查点触发取消，每次都断言 press/release 计数相等且每个 press 后紧跟 release；这条的辅助断言 assertPressReleasePaired（test/browse/cdp-util.test.ts:52-60）可以整段 port 成 Rust 引擎的事件序列契约断言

### ③ 落点前瞄准停顿、点间停顿与每机节奏偏置（验证码协助的高审查节奏档）

- **对应任务**：2.1（只覆盖「落点停顿」这一样）、2.4（光标连续性）；验证码协助专用节奏档与每机节奏偏置无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/captcha-assist.ts:73-79（CAPTCHA_PACING 常量）、81-89（edgeIdBias）、158-167（captchaPacing）、320-341（合成注入循环）；配套 /Users/baitianxing/codes/aidcp-edge/src/browse/cdp-util.ts:122-133（hoverDwellMs / moveDelayJitter 选项）`
  - 验证码协助的合成点击不是复用浏览路径的默认参数，而是一档专用节奏：落点抖动 ±2px；过冲概率 0.22（按每机偏置在 0.10~0.35 间浮动）；逐帧延迟中心 11ms 且每帧走对数正态抖动；移动到位后、按下之前插一段「读图/瞄准」停顿，中位 650ms、区间 [280,1600]；多个落点之间再插一段停顿，中位 950ms、区间 [420,2600]；上一个点的真实落点作下一个点的起步点，保光标连续。所有中心值再按边缘机器标识派生一个 [-0.15,0.15) 的偏置（FNV-1a 哈希），避免整个车队逐字相同的节奏本身成为车队级指纹。
- **旧代码记下的真机经验**：
  > 点间对数正态停顿。中心值按 edgeId 派生每机偏置（见 captchaPacing），避免全 fleet 逐字相同的节奏自成车队指纹。
  >
  > /** 按 edgeId 派生 [-0.15, 0.15) 的每机偏置（FNV-1a），打散车队级节奏指纹。 */
  >
  > // 合成拟人注入：连续光标 + overshoot/jitter + 逐帧 dt 抖动 + 落点前读图停顿 + 点间对数正态停顿。
  >
  > // 上一点的**真实落点**作下一点起步，保光标连续。
  >
  > 移动到位后、按下之前的读图/瞄准停顿(ms)（change captcha-assist-humanize-click）。默认 0 = 无停顿（现有 click 零回归）。>0 时在 hover 与 press 之间插一段可注入 sleep 的 dwell。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:1283-1297（验证码落点循环）`
- **具体缺哪几样**：
  1. 缺瞄准停顿：移动与按下之间没有任何等待（mouseMoved 后直接 press）
  2. 点间停顿从「中位 950ms 的对数正态」换成固定 `sleep(80ms)`（engine.rs:1297）
  3. 缺过冲概率、缺落点抖动、缺逐帧对数正态抖动——这一档专用参数在 Rust 侧无任何对应常量
  4. 缺每机节奏偏置：引擎没有边缘标识入参，节奏无法按机器派生偏置，同一版二进制在全车队产出同一节奏形状
  5. 缺光标连续性：多落点循环里每个点都是独立的「瞬移+点击」，不把上一落点当起步点

### ④ 运营真机鼠标轨迹回放通道整体缺失（且被宿主静默丢弃）

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/humanize/trajectory-replay.ts:1-108（sanitizeTrajectory 36-52、replayTrajectory 59-107）；调用点 /Users/baitianxing/codes/aidcp-edge/src/browse/captcha-assist.ts:300-318`
  - 验证码协助允许云端把运营在后台上真实划过的鼠标轨迹带下来，边缘按被点那一帧的裁剪区把样本缩放后逐帧回放：落点权威仍取离散点（决定点哪里），轨迹样本只决定怎么移动、何时按下。每次按下之前补一帧移动到权威落点，保证按下坐标等于最后一次移动坐标；帧间时间差只裁剪长停顿（上限 120ms）绝不等比压缩（等比压缩会造出超人速度）；帧间时间差再叠一层轻抖动、坐标叠 ±1px 亚像素，不做逐字原样重放；按下与松开之间插一段中位 60ms、上限 200ms 的抖动停顿。轨迹校验有硬边界（版本号、样本数 ≤250、坐标归一化在 [0,1]、按下下标必须落在样本范围内、按下下标数量必须等于落点数），任一不过即判无效、回落合成路径并如实标注回落模式，绝不谎称用了轨迹；结尾还有一道防御：任何未被触发的落点补发按下，保证按下次数等于落点数、不静默漏点。
- **旧代码记下的真机经验**：
  > 落点权威取离散点（WHERE），轨迹样本只供"怎么移动/何时按下"（HOW/WHEN）。反检测要点：
  >  *  - **每次 press 前补一帧 move 到权威落点**：保证 mousedown 坐标 == 最后 mousemove 坐标，消除"mousedown 落在鼠标从未移动到的坐标"这一比合成路径更可检测的瞬移伪影。
  >  *  - **缩时只裁剪长停顿（Δt clamp），绝不等比压缩**：等比压缩会产生超人速度。
  >  *  - 帧间 dt 叠轻量对数正态抖动、坐标叠 ±1px 亚像素：不做 verbatim 原样重放（固定节流采样节奏本身是指纹）。
  >  *  - 样本数/单调/坐标/clicks 越界任一不过 → 判无效，调用方回落合成路径（绝不硬回放、绝不谎称用了轨迹）。
  >
  > /** 单帧最大停顿（ms）：长停顿裁到此值，短的照留（只裁不压缩）。 */
  >
  > // 按下前补一帧移动到权威落点（无瞬移伪影）。
  >
  > // 只裁剪长停顿，不等比压缩
  >
  > // ±1px 亚像素
  >
  > // 防御：validation 保证 clicks[i]<samples.length，理论上都已触发；重复下标等导致遗漏时补发，保证 press 次数 == points 数（不静默漏点）。
  >
  > // 可观测丢弃：轨迹畸形/超限被丢，如实标注回落，绝不静默、绝不谎称用了轨迹。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/command.rs:351-361（CaptchaClickParams，无 trajectory 字段且带 deny_unknown_fields）；/Users/baitianxing/codes/aidcp-edge/src/main.ts:992-1001（宿主投影，只透传 incidentId/snapshotId/points/settleMs/text/submit）、1014（replayMode 硬编码 'synthetic'）`
- **具体缺哪几样**：
  1. Rust 引擎里 `trajectory` 一词零命中：轨迹回放整条能力不存在
  2. 验证码点击参数结构体没有 trajectory 字段，且结构体带「拒绝未知字段」，云端真带下来也进不去引擎
  3. 宿主 main.ts:992-1001 手工枚举转发字段时把 payload.trajectory 丢掉，没有任何日志——旧实现丢弃时是要打「轨迹无效，回落合成」的可观测日志的
  4. main.ts:1014 把回执里的回放模式硬编码成 synthetic，不再区分「真用了轨迹」与「回落」；模式字段退化成常量
  5. 随之缺失的全部子机制：按下前补权威落点一帧、只裁不压缩的 120ms 上限、帧间抖动、±1px 亚像素、按下-松开之间的 60ms 抖动停顿、样本/下标五项校验、漏点补发
- **可 port 的旧测试**：
  - test/humanize/trajectory-replay.test.ts（整文件）——回放与校验的行为契约；能否 port 取决于 Rust 侧是否重建该通道，若本轮不重建应在 backlog 记为「能力缺席」而不是「测试缺席」

### ⑤ 小红书全线打字退化为一次性设值 + 合成事件（无任何硬件级输入）

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/humanize/keyboard-rhythm.ts:22-81（节奏生成）；/Users/baitianxing/codes/aidcp-edge/src/browse/cdp-util.ts:310-340（dispatchKeystrokes 逐字派发）；/Users/baitianxing/codes/aidcp-edge/src/flows/publish-command-handlers.ts:758-791（发布字段的分块突发式输入）`
  - 文本输入一律走浏览器调试协议的真实输入通道，逐字符写入，每个字符前先等一个对数正态采样出来的间隔：中位 110ms、分散度 0.35、裁剪进 [40,400]；标点与空白字符的间隔再乘 1.4（停顿感）；每个字符有 8% 概率额外叠一段 300~600ms 的长停顿（想词/切换输入法）。按字形切分（正确处理中文与 emoji）。唯一的取消缝安排在「这一字符的等待已结束、它的写入尚未发出」那一瞬，已写入的部分留在编辑器里并要求调用方负责清场。长正文另有一层工程妥协：不逐字到底，而是按块「突发式」输入并封顶往返次数（≤50 次）与总停顿预算（12s），块间叠对数正态停顿——因为每次写入都是一次协议往返（数十毫秒），长正文逐字会连同停顿一起把单步拖过云端 30 秒超时（真机实测过）。红线是所有字符都必须写入，封顶只缩时间与往返、不丢内容。关掉拟人时才回退成一次性整段灌入的旧快路径。
- **旧代码记下的真机经验**：
  > 背景（见 docs/risk-control.md §3 / docs/anti-detection.md §5.2）：搜索/评论时绝不一次性 Input.insertText 整段灌入。真人逐字符输入，按键间隔服从对数正态（中位 ~120ms），常用字快、生僻字/标点慢，偶有较长停顿（想词/切换输入法），间隔绝不均匀。
  >
  > 特征（docs/anti-detection.md §5.2）：
  >  *  - 平均间隔 ~80–150ms（对数正态，中位 medianMs）
  >  *  - 偶有长停顿 300–600ms（想词/切换输入法）
  >  *  - 标点/空白处间隔更长（停顿感）
  >  *  - 间隔不均匀（每字符独立采样）
  >
  > 为每个字符按键盘节奏采样"距上一键的延迟"，先 sleep 再用 Input.insertText 输入单字符，形成不均匀的真人打字节奏（替代一次性 insertText）。
  >
  > 循环边界是 generateKeyStrokes 返回的数组长度 ⇒ 天然按迭代次数限界，不存在「恒定 now 死循环」。
  >
  > 为何不逐字到底：每个 Input.insertText 是一次 CDP 往返（~数十 ms），长正文逐字 = 数百次往返，其固有开销会连同停顿一起把本步拖过云端 30s 单步超时（task-0 实测 seq=4 fill_field timeout）。故用 maxSends 封顶往返数、PAUSE_BUDGET 封顶总停顿——任意长度都稳在 30s 内，又不再是瞬时灌入。红线：全部字符都会输入（封顶只缩时间/往返，不丢内容）。
  >
  > // 唯一正确的取消缝：这一字符的等待已结束、它的 CDP 写尚未发出。
  >
  > // 按 grapheme 切，正确处理中文/emoji
  >
  > /** 标点/空白：稍慢（停顿感） */
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:34-44（dispatchInput 助手）、251（publish_fill_field）、236（interaction_comment）、256（add_with_candidate）、269（set_schedule）、242（plan_execute 的 input 步）；对照：/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/input.rs:93-137（逐字实现，参数与旧版一致，但只被 engine.rs:771 搜索框、facebook/comment.rs:173、facebook/publish.rs:554 三处消费）`
- **具体缺哪几样**：
  1. 小红书除搜索框以外的全部文本输入都不走硬件级输入：注入 JS 里用属性描述符的 setter 直接把整段文本写进 value（或对 contenteditable 直接赋 textContent），再手动派发 input / change 两个合成事件
  2. 因此缺：逐字符、对数正态间隔（中位 110 / 分散 0.35 / 裁剪 [40,400]）、标点 ×1.4、8% 概率的 300~600ms 长停顿、按字形切分
  3. 缺分块突发式的往返/停顿双封顶（≤50 次写入、12s 总停顿预算），也就没有「长正文不拖过单步超时又不瞬时灌入」这条平衡
  4. 缺逐字符的取消缝：整段是一次同步赋值，页面侧无法在中途让路
  5. 合成事件对 React/受控组件是「非可信输入」（isTrusted=false），与旧实现刻意补回硬件事件的方向相反
  6. Rust 侧其实已有等价的逐字实现（input.rs:343-372 的间隔参数与旧版逐项一致），但小红书路径完全没有接线到它
- **可 port 的旧测试**：
  - test/humanize/keyboard-rhythm.test.ts『逐字符：字符序列拼接还原原文（含多字节）』——锁「不丢内容」红线
  - test/humanize/keyboard-rhythm.test.ts『间隔分布合理：中位接近正常打字速度 (80–150ms)』
  - test/humanize/keyboard-rhythm.test.ts『间隔不均匀（非恒定）』
  - test/humanize/keyboard-rhythm.test.ts『存在偶发长停顿（想词）』
  - test/humanize/keyboard-rhythm.test.ts『标点/空白处间隔偏长』
  - test/flows/publish-command-handlers.test.ts『拟人填写：CDP 路径标题/正文逐字打字（多次 insertText，拼接==原值）而非一次性灌入』——写入次数必须等于字符数，直接反证一次性赋值
  - test/flows/publish-command-handlers.test.ts『拟人填写：pacing 关 → 回退一次性 insertText（旧快路径，零回归）』——锁「快路径只在显式关拟人时允许」
  - test/browse/cdp-util.test.ts『dispatchKeystrokes: 接管落在下一字符写出之前，且接管优先于死线』——锁逐字符取消缝的位置与异常分类顺序

### ⑥ 小红书正文换行的段落原语与有界归尾确认丢失

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/flows/publish-command-handlers.ts:793-816（拆输入单元）、818-864（stabilizeContentAfterNewline）、866-892（逐单元执行）`
  - 小红书正文编辑器里换行不是普通字符而是一次段落结构事务，所以正文被拆成两类原语：纯文本写入与独立的回车按键，且任何一次文本写入都不许携带回车符。回车用「裸回车」（不带字符文本）让编辑器自己去执行段落拆分——带回车字符的那种形态是搜索框专用的，不用于正文。每发一次回车之后必须做一次有界确认：轮询编辑器状态，要求「已写前缀仍在 + 换行数达标 + 光标位于末端」，并且要连续命中两次才算稳定（一次不够，因为编辑器可能有延迟的选区事务把它覆盖回去）；探针发现选区偏移时会就地把选区折叠到末尾再确认下一轮；上限 1.5 秒、间隔 80ms，超时即抛「换行不稳定」，由上层清空正文并诚实失败。普通字符仍共享全局的往返/停顿封顶，不按行重置预算。
- **旧代码记下的真机经验**：
  > 小红书正文换行不是普通字符，而是 ProseMirror 的段落结构事务。`Input.insertText({text:'上一段\n下一段'})` 会让段落重排与 selection 更新互相抢跑：旧 selection 可能落回块尾字之前，后续块遂插到尾字前，尾字逐块倒序堆到文末（dev record #153）。
  >
  > 因此正文 MUST 拆为两类原语：纯文本 insertText 与独立 Enter；任何 insertText 都不携 CR/LF。普通字符仍共享 maxSends/PAUSE_BUDGET，避免按行重置预算使长正文往返数失控。
  >
  > Enter 已写入页面后不可取消：先有界确认「已写前缀仍在 + selection 连续两次位于末端」。探针发现 selection 偏移时会就地 collapse(false) 归尾；下一轮再确认没有被 ProseMirror 的延迟 selection 事务覆盖。命令 ACK 只代表 CDP 收到指令，不能替代此编辑器状态确认。
  >
  > // 裸 Enter 让 ProseMirror 自己执行 splitBlock；携 '\r' 的搜索框专用 keypress 形态不用于正文。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:251（publish_fill_field 直接 dispatchInput 整段）、34-44（dispatchInput 对 contenteditable 走 `el.textContent=value`）`
- **具体缺哪几样**：
  1. 缺「文本写入」与「独立回车」两类原语的拆分：整段（含 \n）一次性赋给 textContent，编辑器不会因此产生段落结构
  2. 缺「任何文本写入不许携带回车符」这条约束
  3. 缺裸回车按键派发（也就没有让编辑器自己执行段落拆分这条路径）
  4. 缺每次换行后的有界归尾确认：无「前缀仍在 + 换行数达标 + 光标在末端 + 连续两次稳定」四条件、无 1.5s/80ms 的轮询边界、无选区就地折叠归尾
  5. 缺失败态：确认不稳定时应清空正文并诚实失败，新实现只做一次整段回读比对（xhs-command-router.js:251 结尾的 norm 比较），比对不过报 publish_field_readback_mismatch，不区分「换行结构没建起来」这一具体病因
- **可 port 的旧测试**：
  - test/flows/publish-command-handlers.test.ts『多段正文：换行独立 Enter + selection 归尾，尾字不再被后续段落顶到文末』——一条用例同时锁四件事：CRLF 归一为一个回车、连续空行保留为两个连续回车、任何文本写入不带换行、每个回车后至少两次选区确认（断言 caretChecks.length >= 6）
  - test/flows/publish-command-handlers.test.ts『ProseMirror 真实段落边界：末段 p 内 caret 是语义末端，不要求等于外层 div 末端』
  - test/flows/publish-command-handlers.test.ts『ProseMirror 真实段落边界：前段 caret 先归到末段内部，下一轮确认末端』
  - test/flows/publish-command-handlers.test.ts『换行确认持续不稳定：清空正文并诚实失败，不留下逐渐积累的文末尾字』
  - test/flows/publish-command-handlers.test.ts『Enter 被页面吞掉：即使 caret 在末端也不能放行，必须清场并诚实失败』

### ⑦ 小红书滚动退化为页面内一次性平滑滚动（旧代码明写这在窄布局上是空操作）

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/humanize/scroll-physics.ts:1-98（惯性帧序列生成）；/Users/baitianxing/codes/aidcp-edge/src/browse/feed-scroller.ts:176-212（feed 滚动派发，关键注释在 177-184、191-194）；/Users/baitianxing/codes/aidcp-edge/src/browse/browse-session.ts:698-717（详情页正文/评论的惯性滚动）、281-282（评论滚动距离 150~290px）`
  - 一次滑动被拆成 8~15 帧的滚轮增量序列：各帧权重是一条钟形包络（用半个正弦近似「加速→峰值→惯性衰减」，端点加 0.15 偏置避免为零），再乘 0.85~1.15 的随机抖动；按权重分配位移，最后一帧吸收取整误差以保证总和精确且保号；每帧配一个 16~60ms 的不均匀延迟。目标总位移本身先叠 ±20% 随机（人手力度不均）。派发方式是先把光标移到可滚区中心，再逐帧派发真实滚轮事件——注释里写明这样做有三重理由：小红书宽窄两套布局的可滚元素不同，页面内的 scrollBy 在某些布局上是空操作导致 feed 永不推进；真实滚轮两布局通吃；还补回了硬件滚轮事件、消除「无滚轮事件」这一指纹并触发懒加载。派发失败只中止本轮滚动、绝不抛出（真机踩过：一次瞬时超时会让整个浏览循环结束）。feed 单次位移默认 500px（约半屏），刻意不用 800px（约整屏）以保留相邻两次扫描的可见卡片重叠。
- **旧代码记下的真机经验**：
  > 背景（见 docs/risk-control.md §3.3 / docs/anti-detection.md §5.3）：当前滚动是固定 3 步 × 300ms 的匀速分段，是机器特征。真人滑动手势有"加速 → 巡航 → 减速"的惯性：手指刚触碰时 deltaY 小，中段达到峰值，松手后惯性衰减尾逐渐变小；且帧间隔不均匀（模拟真实帧率波动）。
  >
  > 特征（docs/anti-detection.md §5.3）：
  >  *  - 开始：deltaY 小（手指刚触碰）
  >  *  - 中间：deltaY 达峰值（快速滑动）
  >  *  - 结束：deltaY 逐渐减小（惯性衰减）
  >  *  - 帧数 8–15，每帧间隔 16–60ms 不均匀
  >  *  - 各帧 deltaY 之和 = totalDistance（保号、整数）
  >
  > // 按权重分配位移，最后一帧吸收取整误差，保证总和精确
  >
  > // 速度包络：先升后降的钟形曲线（用 sin 半波近似惯性"加速→峰值→衰减"）。
  >
  > // 目标总位移加 ±20% 随机（人手力度不均），再切成惯性帧序列。
  >
  > 滚动机制：CDP 真实 mouseWheel 在 feed 区中心派发，浏览器原生滚动当前命中的可滚容器——小红书宽/窄两布局可滚元素不同（window/document 或内层 .feeds-page，见 docs/xhs-layout-states.md），旧的 window.scrollBy 在 document 不可滚的布局上是 no-op（feed 永不推进）。真实滚轮两布局通吃，且补回硬件 wheel 事件（消除"无 wheel 事件"指纹），并触发 XHS 懒加载。
  >
  > // 先把光标移到 feed 中心（hover 真实化），再逐帧派发滚轮，保留惯性节奏。
  >     // best-effort：单次派发失败（如通知巡视后回 feed 的页面导航瞬间，CDP 对 Input.dispatchMouseEvent 短暂超时）
  >     // 只中止本轮滚动、【绝不抛出】——否则一次瞬时超时就会让整个 browse loop 结束（真机实测踩过的坑）。
  >
  > // 默认 ~500（约半屏）：相邻两次扫描的可见卡片保留重叠，降低 AI 卡在两次扫描之间被整屏跳过的概率。
  >     // （原 800 ≈ 一整屏，相邻快照几乎不重叠 → borderline 卡只有一次被评估机会就划走。）
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:158（feed 翻页）、213（详情页评论滚动）、242（plan_execute 的 page.scroll 步）；引擎侧路由 /Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:708（未特化的命令一律落到注入路由）`
- **具体缺哪几样**：
  1. 小红书三处滚动全部改用页面内的 window.scrollBy（带 behavior:'smooth'）或元素 scrollBy，完全不派发滚轮事件——正是旧注释点名「在 document 不可滚的窄布局上是 no-op、feed 永不推进」那个实现
  2. 缺惯性帧序列：8~15 帧、钟形包络、0.85~1.15 权重抖动、最后一帧吸收取整误差全部没有
  3. 缺帧间不均匀延迟（16~60ms），换成滚完一次固定等 500ms（feed）/ 350ms（评论）
  4. 缺 ±20% 的总位移随机：feed 位移写成 max(360, 视口高×0.78) 的确定值，评论固定 500px，plan 步固定 max(200, value||500)
  5. 缺「先把光标移到可滚区中心」这一步，也就没有硬件级 hover 与滚轮事件，「无 wheel 事件」指纹回归
  6. feed 单次位移口径也变了：从「约半屏 500px 保留扫描重叠」变成约 0.78 屏
  7. Rust 侧其实有等价的惯性实现（input.rs:43-65 与 269-310，参数与旧版逐项一致：帧数 8~15、包络 sin×0.85+0.15、权重抖动 0.85~1.15、延迟 16~60ms、总位移 ±20%），但小红书路径完全没有接线到它
- **可 port 的旧测试**：
  - test/humanize/scroll-physics.test.ts『帧数在 8–15 之间』
  - test/humanize/scroll-physics.test.ts『各帧 deltaY 之和等于总位移（保号、精确）』
  - test/humanize/scroll-physics.test.ts『加速→减速：峰值在中段，首尾较小』
  - test/humanize/scroll-physics.test.ts『帧间延迟在 16–60ms 且不均匀』
  - test/humanize/scroll-physics.test.ts『负位移（向上滚）：每帧非正、总和守恒』
  - test/humanize/scroll-physics.test.ts『零位移：空序列』
  - test/facebook/viewport-scroll.test.ts『fb-scroll: 多帧惯性 wheel 守恒总距离，已移动时不走 JS 兜底』——同时锁「多帧」与「只有观测到没动才允许页面内兜底」；这条 port 过去正好把「直接用 scrollBy」判为违规

### ⑧ Facebook 侧残余的瞬时滚动（带目标进视野、详情页/评论滚动）

- **对应任务**：1.5、3.1、3.2、3.3、3.4、7.3
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/facebook/viewport-scroll.ts:50-107（统一惯性手势 + 条件兜底）；调用点 /Users/baitianxing/codes/aidcp-edge/src/facebook/like-executor.ts:346-356（把视口外目标卡滚进来）`
  - Facebook 的信息流与评论编辑器都走同一个视口滚动手势：先叠 ±20% 得到本次目标位移，再切成惯性帧序列逐帧派发真实滚轮（带符号，向上滚为负），派发前把光标移到视口中心。派发过程中的异常只记日志、不中断浏览循环。关键的诚实约束是「兜底只在观测到确实没动时才做一次」：滚动前后都成功量到滚动位置、且完全没变，才允许用一次页面内滚动兜底；量不到位置就宁可不猜、不补滚，避免在部分滚轮已生效的情况下制造第二段位移（旧实现是无条件双滚）。把目标卡带进视野时按「期望位移 = 卡顶 - 视口高×目标比例」计算，带死区与单步上限，滚够回合数仍不可见就诚实报「目标不可见」，绝不改点当前居中那张卡。
- **旧代码记下的真机经验**：
  > FB feed 与评论编辑器都走 document 视口；这里统一派发惯性 wheel，并且只有在观测到 wheel 没有推动页面时才做一次 JS 兜底，避免旧实现的无条件双滚。
  >
  > 本次手势的基准总位移（CSS 像素）。实际目标在 +/-20% 内抖动。**带符号**：正=向下、负=向上（点赞前把视口外的目标卡拟人地滚进视野需要能向上滚）。
  >
  > 输入异常不会中断 browse loop。只有前后都成功量到位置且完全没动时才允许 JS 兜底；量不到位置宁可不猜测补滚，避免在部分 wheel 已生效时制造第二段位移。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/feed_like.rs:263-274（带目标进视野：单帧精确 delta）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook-router/90-dispatch.js:58（feed 翻页的页面内兜底）、96（note_scroll_comments）；对照已正确接线的 /Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/feed.rs:555-580（feed 主滚动走惯性）`
- **具体缺哪几样**：
  1. 把目标卡滚进视野（feed_like.rs:266-273）用一次 dispatch_wheel 发一个精确计算出来的位移（卡顶 - 视口高×0.55，裁进 ±620），单帧、无惯性序列、无 ±20% 抖动，然后固定 sleep(250ms)
  2. 详情页/评论滚动（90-dispatch.js:96）走页面内 window.scrollBy + behavior:'smooth' + 固定 sleep(350ms)，完全没有滚轮事件
  3. feed 翻页的路由分支（90-dispatch.js:58）同样是页面内 scrollBy 且无条件执行——不是「观测到没动才兜底」，与旧实现刻意加的条件相反（注意：正常 page_scroll 已被 feed.rs:52 截走走惯性，这条路由分支是 initial_scan 之外的残留/兜底入口，仍会在真机上被走到）
  4. 缺「只在量到前后位置且完全没动时才兜底一次」这道诚实闸，也就重新打开了「部分滚轮已生效 + 再来一段页面内位移」的双滚窗口
- **可 port 的旧测试**：
  - test/facebook/viewport-scroll.test.ts『fb-scroll: 观测到 wheel 未移动时只作一次 JS 兜底』
  - test/facebook/viewport-scroll.test.ts『fb-scroll: 部分 wheel 已移动后 CDP 出错，不抛出也不双滚』
  - test/facebook/viewport-scroll.test.ts『fb-scroll: wheel 起步即失败时，仍有一次受限兜底且不抛出』
  - test/facebook/viewport-scroll.test.ts『scrollFacebookViewport: 负位移 → wheel 全部向上，回执位移带负号』
  - test/facebook/like-executor.test.ts『fb-like: 目标在视口下方 → 拟人 wheel 滚进视野后再定位（不瞬移）』——断言必须派发真实滚轮且点击脚本里不得含 scrollIntoView
  - test/facebook/like-executor.test.ts『fb-like: 有界滚动后目标仍不可见 → target_not_visible（绝不对当前居中的卡下手）』

### ⑨ Reels 的单帧滚轮与三条裸事件点击

> ⚠️ oracleQuality = `also-wrong` —— **不可照抄**，先看本文件开头那段。

- **对应任务**：3.5、3.6、7.5
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/facebook/reels-reader.ts:353-357、365-367、369-373（也有缺陷的部分）；531-536（可参照的浮层点击）`
  - 旧 Reels 换视频三级兜底：先发方向键，不动就发一帧滚轮（位移在 70~100 像素之间均匀取一个整数），还不动就对「下一个」按钮坐标发三条裸鼠标事件（移动、按下、松开）。三条事件之间没有路径、没有延迟、按下失败也不补发松开。只有反应浮层那一处走了完整的拟人点击（带起点、关掉过冲以贴住控件→浮层走廊）。
  - ⚠️ **caveat**：旧的 Reels 实现本身就是「一帧滚轮 + 三条裸鼠标事件」，没有惯性序列、没有轨迹、也没有按下失败补发抬起：见 src/facebook/reels-reader.ts:353-357（trustedClick 三条裸事件）、365-367（trustedWheel 单帧）、369-373（滚轮位移 70~100px 均匀取值）。照抄这里等于把同一个盲区搬回来。真正可复用的参照物在同仓另一处：src/facebook/viewport-scroll.ts:50-107 的惯性手势与 src/browse/cdp-util.ts:242-260 的原子点击——Reels 应当改指这两个原语，而不是照抄 reels-reader。另外 reels-reader.ts:531-536 的浮层点击确实走了拟人点击（dispatchClick + from + overshoot:false），这一处是 direct 可参照的。
- **旧代码记下的真机经验**：
  > 无注释（trustedClick / trustedWheel / randomReelWheelDistance 三个函数均无解释性注释，只有函数名）
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook/reels.rs:215-223（单帧滚轮，位移 70 + 时间戳取模 31）、248-259（三条裸鼠标事件）`
- **具体缺哪几样**：
  1. 单帧滚轮：无惯性帧序列、无帧间延迟、无 ±20% 抖动
  2. 随机源退化：位移抖动用「当前毫秒时间戳对 31 取模」代替随机采样（reels.rs:215），同一毫秒内的多次调用完全相同，且分布与墙钟耦合
  3. 点击仍是三条裸事件：无移动路径、无落点抖动、无过冲、无瞄准停顿
  4. 按下用 `?` 早返回，松开永不发出（与缺口②同形）

### ⑩ 云端下发的节奏中心值几乎无人消费（动作前犹豫全丢、离页停留只剩一处）

- **对应任务**：1.1、1.2、1.7、4.1、4.2、4.3、4.4、4.5、4.6、4.7、7.2
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/browse/browse-session.ts:504-512（thinkBefore）、514-535（ensureDetailDwell）、537-556（ensureFeedDwell）、568-584（effectiveFloor）、586-597（ensureMinInterval）、599-614（gateBeforeAction）、470-502（重连重注入与中途升档）；/Users/baitianxing/codes/aidcp-edge/src/humanize/timing.ts:113-126（jitterAround）、37-46（预设档位）`
  - 云端把内容相关的时长算成确定性中心值随指令下发（动作前犹豫、离页前总停留），边缘做四件事。一是叠抖动：中心值乘一个中位为 1 的对数正态噪声（犹豫用分散度 0.25、停留用 0.2）——不叠的话两个账号看同一篇会停得分毫不差，这本身是指纹。二是保证停留达标：从「详情页打开时刻」或「本批卡到达时刻」起算已停留时长，只补差额，已达标就不再等（把云端评估耗时天然吸收掉，不产生双重延迟）；缺中心值时从内置下限区间采样并叠当前风控档位的降速系数。三是最小间隔闸：每类操作有一个配置区间，用反射采样（不是硬裁——硬裁会在直方图边界堆出一根竖直左壁尖峰，本身可被识别）取值，再乘风控降速系数、除疲劳系数，夹进防呆上下界，保证「配置只能抬高延迟、抬不穿非零下限」；间隔与犹豫在同一跨度里只比一次、取较大者而不是相加。四是连接级快照的重注入与中途升档：重连时重注入并清掉间隔锚点（页面已变、首操作跳过间隔），中途收到档位刷新则只改降速系数、绝不借此清锚点跳过一次间隔。所有等待都是安全取消点：被独占任务接管即当场让路，绝不让一个 90 秒的停留预算把恢复任务的受理预算撑爆。
- **旧代码记下的真机经验**：
  > 动作前犹豫 / 感知（time directive `thinkMs`）：围绕云端中心值叠抖动后等待。缺 `thinkMs`（旧云端 / 自主动作）→ 不额外等待，由各动作自身的 humanPause 兜底。
  >
  > 返回 / 关闭详情页前确保**实际停留**达标（time directive `dwellMs`），治「无价值秒退」。
  >    * - 仅当确有打开的详情页（noteOpenedAt 非空）时生效；
  >    * - 中心值 = `dwellMs`（云端按内容算，已烘入 tempo）或缺失时从内置下限采样、**叠当前 tempo 档位**，再叠抖动；
  >    * - 已停留时长（含真实阅读）已达标则不叠加等待（无双重延迟）。
  >
  > 注（change pacing-fallback-hardening）：tempo 只叠在**边缘采样兜底**上，云端已下发的 `dwellMs` 不再叠（防 double-count）。
  >
  > feed 翻页前确保"看完本批新卡"的停留达标（time directive `dwellMs`，feed-scroll-card-floor）。
  >    * - 缺 `dwellMs` / ≤0（返回未刷新 / 旧云端 / 断连）→ 立即翻页、不额外等待；
  >    * - 中心值 = 云端按新卡数算的 `dwellMs`，叠抖动为目标；
  >    * - 从"本批卡到达时刻"起算已停留，已达标则不叠加（评估耗时被吸收，无双重延迟）；
  >
  > 围绕一个**中心值**叠加对数正态抖动（指令级节奏 Command Pacing 的边缘抖动层）。
  >  *
  >  * 云端基于内容算出的 `dwellMs`/`thinkMs` 是确定性中心值；若边缘直接照用，两个账号看同一篇笔记会停得分毫不差——这本身是指纹。本函数用 median=1.0 的乘性 lognormal 噪声（`center · exp(sigma · N(0,1))`）把它打散成带随机性的实际时长。
  >
  > 动作前统一闸（替代散落的 thinkBefore + 引导性 humanPause）：折 think（云端犹豫）与最小间隔，同一「now→执行本动作」跨度**只比一次、用 `max` 不用 `+`**（设计 §3.1）。
  >
  > clamp 下界 OP_MIN_FLOOR[op] > 0 → **配置只能抬高延迟、抬不穿非零下限**（绝不零延迟红线）。
  >
  > 背景（见 pacing-floor-configurable-min-interval 设计 §7 防指纹）：最小间隔 gating 会把「补差额」补到 floor 这一固定值，硬裁采样在直方图 min 处堆出一根竖直左壁尖峰——本身是可被行为分析识别的指纹。反射采样把超出 [lo,hi] 的样本按边界**反弹**回区间内（周期 = 2·span 的三角波折叠），保证结果恒落在 [lo,hi]，同时把原本会堆在墙上的左/右尾质量摊回分布内、消掉竖直壁。
  >
  > 安全取消点：停留只消耗时间、不碰页面。被接管即当场让路，绝不让一个 90s 的停留预算把系统恢复任务的受理预算撑爆（change lease-strict-preemption）。
  >
  > 重连后重注入 welcome pacing 快照（设计 §4.3 最严重缺口修复）：BrowseSession 只构造一次，identity 翻转重连复用同一对象，若不重注入则连接级快照退化成进程级、风控升级到不了边缘节奏层。
  >
  > 中途风控档位刷新（change pacing-fallback-hardening）：会话稳定连接期间收到 cloud 的 `pacing.update`，只更新兜底节奏所用 tempo（校验正数、否则忽略）。**不动 `lastActionEndAt`**——中途刷新 ≠ 重连，不得借此跳过一次最小间隔
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/command.rs:75-325（14 处 think_ms / dwell_ms 字段声明）；/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/browse-session.ts:264-276（唯一消费者 ensureFacebookScrollDwell）、213-218（applyPacingSnapshot 空实现）、121（pacing.update 直接丢弃）；/Users/baitianxing/codes/aidcp-edge/src/native-page-engine/command-mapper.ts:53-69（字段投影白名单）`
- **具体缺哪几样**：
  1. Rust 侧对 think_ms / dwell_ms 的读取点为零：全仓 grep `.think_ms` / `.dwell_ms` 只命中结构体声明与 5 处构造时写 `None`（facebook/runtime.rs:128、facebook/feed.rs:177/244/274、engine.rs:630/1630/1652），没有一处把它变成等待
  2. 动作前犹豫整体消失：14 个命令的 think_ms 一路解析进结构体后无人使用——打开笔记、点赞、收藏、关注、评论、翻图、滚评论、开主页、通知巡视、加群前都不再有犹豫
  3. 离页停留只剩一处、且只在 Facebook：宿主 src/native-page-engine/browse-session.ts:268 判定条件是「平台是 facebook 且命令是 page_scroll 且已记录过卡到达时刻」，小红书全线、以及 note_close / navigation_back 的 dwellMs 全部无人消费——「无价值秒退」治理失效
  4. 缺最小间隔闸整层：没有按操作类别的 floor 配置、没有反射采样（也就没了「消竖直左壁尖峰」这个防指纹动作）、没有 tempo 乘算、没有疲劳系数、没有防呆上下界、没有「间隔与犹豫取 max 不相加」
  5. 缺连接级 pacing 快照：applyPacingSnapshot 被实现成空函数，注释写着「Pacing stays Cloud-owned. Each Native command receives the already-authorized timing fields.」——但接收到的字段并没有被消费，这句注释是个已经不成立的前提
  6. 缺中途档位刷新：src/native-page-engine/browse-session.ts:121 对 pacing.update 直接 return，风控升档到不了边缘节奏层
  7. 缺间隔锚点语义：没有 lastActionEndAt，也就没有「重连清锚点 vs 中途刷新不清锚点」这对区分
  8. 唯一保留的抖动：ensureFacebookScrollDwell 里的 jitterAround(center, 0.2)（src/native-page-engine/browse-session.ts:271），口径与旧 ensureFeedDwell 一致
- **可 port 的旧测试**：
  - test/browse/browse-session.test.ts『pacing: navigation.back 带 dwellMs 且停留不足 → 兜底停留（治秒退）』
  - test/browse/browse-session.test.ts『pacing: 真实阅读已超过 dwellMs → 不叠加等待（无双重延迟）』
  - test/browse/browse-session.test.ts『pacing: navigation.back 缺 dwellMs（旧云端）仍非零停留（不秒退）』
  - test/browse/browse-session.test.ts『pacing: interaction.like 的 thinkMs → 执行前犹豫等待』
  - test/browse/browse-session.test.ts『pacing: page.scroll 带 dwellMs 且刚到卡（停留不足）→ 翻页前兜底停留』
  - test/browse/browse-session.test.ts『pacing: page.scroll 缺 dwellMs（返回未刷新/旧云端）→ 立即翻页不额外停留』
  - test/browse/browse-session.test.ts『让路: 命令停在翻页前停留时被接管 → 交接毫秒级收敛、零页面写（长停留预算不得撑爆受理预算）』
  - test/browse/pacing-min-interval.test.ts『min-interval: think 与间隔取 max 非相加（remaining 主导）』
  - test/browse/pacing-min-interval.test.ts『min-interval: think 主导时 wait = think（间隔较小），仍不相加』
  - test/browse/pacing-min-interval.test.ts『min-interval: 配极小 floor（远低于防呆下限）→ 边缘二次夹抬到防呆下限 800、不塌零』
  - test/browse/pacing-min-interval.test.ts『min-interval: 云端慢回（elapsed ≥ floor）→ gate 不额外 sleep、不塌零』
  - test/browse/pacing-min-interval.test.ts『min-interval: 重连 applyPacingSnapshot 重置锚点 → 紧接动作跳过间隔（§3.2 不变量2）』
  - test/browse/pacing-min-interval.test.ts『pacing.update: 中途升档放大最小间隔且不重置锚点』
  - test/browse/pacing-min-interval.test.ts『ensureDetailDwell: 云端已下发 dwellMs 不再随 tempo 放大（防 double-count）』
  - test/humanize/timing.test.ts『sampleReflect: 反射消掉硬左壁尖峰——边界处样本远少于硬裁 sampleDelay』

### ⑪ 注入路由的通用点击助手把「滚动到视口中心」瞬移写回去了（旧测试明令禁止）

- **对应任务**：2.6、7.4（只覆盖 Facebook 浮层提交那一半）；两个注入路由通用点击助手里的 scrollIntoView 瞬移无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/facebook/like-executor.ts:360-387（浮层反应项必须坐标点击的红线）；断言在 /Users/baitianxing/codes/aidcp-edge/test/facebook/like-executor.test.ts:193-225（『点击脚本里绝不能再有 scrollIntoView 瞬移』）`
  - 两条真机实证出来的分层规则。其一：把视口外的目标滚进视野必须用拟人滚轮手势，点击脚本里绝不许再有「滚动到视口中心」这种瞬移——这条被写成断言钉在测试里。其二：控件的事件机制逐个不同，浮层态的选项一律走坐标点击。真机 A/B 实证过：对浮层里的「赞」项在页面内直接调 click() 会返回「点了」但反应根本不生效（平台把纯 click 事件当成 hover 态忽略，它监听的是真实的按下/松开）；改成坐标派发按下-松开才真提交。同时定位必须限定在已打开的那个浮层内，绝不全文档搜索——信息流每张卡的点赞按钮标签也叫「赞」，全文档搜会点错帖。找不到就返回失败、不点，诚实。
- **旧代码记下的真机经验**：
  > 【红线：浮层反应项必须走 CDP 坐标点击，绝不 in-page element.click】真机 A/B 实证（本轮，簇82）：对浮层「赞」项 in-page `el.click()` 返回 `clicked=true` 但**反应不生效**（FB 把纯 'click' 事件当 hover 态忽略、监听的是真实 mousedown/mouseup）；改用 CDP `Input.dispatchMouseEvent` press/release（dispatchClick）才真提交。这是 FB **逐控件事件机制不一致**的又一例（cta / composer 亦有先例）——浮层态选项一律坐标点击。
  >
  > 且**只在打开的反应浮层 dialog 内**定位「赞」项坐标（scoped，见 buildPickerLocateJs），绝不全文档搜索（feed 每卡 Like 按钮 aria-label 亦「赞」，全文档搜会点错帖）。无浮层 / 找不到 → false（不点，诚实）。
  >
  > // overshoot=false：路径紧贴「控件→浮层」走廊，避免 overshoot 甩出浮层 hover 区致其收起。
  >
  > assert.ok(!clickExpr.includes('scrollIntoView'), '点击脚本里绝不能再有 scrollIntoView 瞬移');
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:45-51（click 助手）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook-router/00-shared.js:34-38（click 助手）`
- **具体缺哪几样**：
  1. 两个注入路由的通用点击助手第一件事就是 el.scrollIntoView({block:'center',inline:'center'})——正是旧测试点名禁止的瞬移，而且它会把页面位置瞬间跳到目标居中，滚动位移完全不受节奏层控制
  2. 小红书路由的这个助手随后只派发一个伪造的 mousemove（坐标写成元素外接框左上角 +4px，与真实落点无关），再调 el.click()：三者都不是硬件级事件
  3. 消费面：小红书的点赞/收藏/关注（xhs-command-router.js:233）、评论提交（236）、话题候选（256）、发布提交（272）、plan 步（242）全部经此助手；Facebook 路由助手用于 feed_refresh 与 note_browse_images 等分支
  4. 注：Facebook 的加群点击（facebook-router/40-group-join.js:158 的 target.click()）与信息流点赞主控件（10-feed-like.js:150 的 target.control.click()）走的是页面内点击，这与旧实现一致、是真机验证过的正确形态；需要坐标点击的浮层项在 feed_like.rs:421-450 也确实走了坐标——所以这一条的缺口是通用助手里的 scrollIntoView 瞬移 + 伪造 mousemove，不是「所有页面内点击都该改」
- **可 port 的旧测试**：
  - test/facebook/like-executor.test.ts『fb-like: 目标在视口下方 → 拟人 wheel 滚进视野后再定位（不瞬移）』——其中「点击脚本里绝不能再有 scrollIntoView」这一条断言可直接 port 成对注入路由脚本文本的静态契约检查
  - test/facebook/like-executor.test.ts『fb-like[jsdom] 两段: 反应浮层「赞」项走 CDP 坐标点击、落点=浮层项坐标（非首卡回归：不点到别卡「赞」，簇82）』——锁「浮层项必须坐标点击且落点限定在浮层内」

### ⑫ 闸①后置校验：从统一闸退化成逐命令自制的检查片段

- **对应任务**：5.1、5.6
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:39-41（PostValidator 接口）、:213-235（执行→重取根→校验→只有 valid 才 return ok）；/Users/baitianxing/codes/aidcp-edge/src/flows/like-post.ts:27-75（点赞态判据）；/Users/baitianxing/codes/aidcp-edge/src/flows/publish-post.ts:203-251（发布各步判据）`
  - 旧实现把「后置校验」做成引擎骨架里一道**结构性强制**的环节：执行层返回后，引擎必须重新取一次页面根（rootAfter），把请求 + 新根交给一个外部注入的校验器；校验器返回 true 才允许回 ok=true，否则一律走失败分支。校验器是接口而非内嵌代码，所以每个业务动作都必须显式提供一个「什么叫真的发生了」的判据，缺了就编译不过。判据本身按动作分家：点赞看翻转态、发布各步看输入回读/页面身份/话题 token/封面激活。
- **旧代码记下的真机经验**：
  > 三道闸（决定"自愈"不变"自残"）：
  >  *  1) 后置校验：操作后必须验证业务结果真实发生，校验不过才判失败。
  >
  > 🔴 从这里到 validate 返回，**MUST NOT 取消**：页面已经被写、结果尚未校验，
  >       //    中止 = 把一次可能已生效的写当成没发生（且缓存记账全在校验之后，会一并漂移）。
  >
  > 后置校验"点赞态是否真实翻转"（aria-pressed / 选中类名 / 可访问名变化），
  >  *     校验不过判失败，绝不静默成功（复用引擎三道闸）。
  >
  > 真实页面里点赞翻转可能落在按钮自身或其包裹容器上，故向上回溯有限层级。
  >
  > 策略：扫描所有可能的点赞控件（可访问名/title/aria-label 含"点赞/赞/like/喜欢/心形"），
  >  * 只要其中之一进入已点赞态即判通过。这样既能覆盖"按钮自身翻转"也能覆盖"容器翻转"。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:52-57（active/selected/done/fail/ambiguous 三件套）、:233、:236、:239、:251、:266、:269、:272、:287（每条命令各写一遍自己的后置检查）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/effect.rs:16-38（EffectTracker）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:556-596（execute_platform_command_once，无校验环节）`
- **具体缺哪几样**：
  1. 缺「统一强制的校验环节」：新引擎的命令执行主干（engine.rs:556-596）里没有任何 post-check 步骤，校验完全下沉到注入 JS 的每个 if 分支里各写一遍——某条命令忘了写，就是直接 done() 返回 confirmed，没有任何机械手段能发现
  2. 缺「重新取一次页面根再校验」的语义：旧引擎是 execute 后 dom.getRoot() 拿新快照；新引擎在同一次注入 JS 调用里对**同一个 DOM 活引用**（如 control 变量）复查，页面若整段重渲染，旧引用已脱离文档树，active(control) 恒 false 或恒沿用旧态
  3. 缺「校验器可注入 / 可替换」：判据焊死在混淆 JS 里，不能按平台/账号/A-B 换判据，也不能在不起浏览器的情况下单独测一条判据
  4. 把「校验不过 = 失败」换成「校验不过 = effectPhase:'ambiguous'，ok=false」：方向对（EffectPhase::Ambiguous 永不回落 Confirmed，effect.rs:31-37），但只表达「不确定」，不再表达旧引擎那条「校验失败 ⇒ 缓存锚点疑似失效 ⇒ 下一轮换路径」的因果（engine.ts:238-244）
  5. 缺跨命令一致性：xhs 侧有 8 处后置检查、FB 侧只有加群（facebook/group_join.rs:222-320）做了带 deadline 的轮询复查，其余靠注入 JS 里一句 sleep 后复读；同一个「后置校验」在新引擎里有至少三种强度
- **可 port 的旧测试**：
  - engine.test.ts『缓存命中 + 后置校验通过 → success(source=cache)』(test/locating/engine.test.ts:52) —— 锁住「校验通过才回 ok，且只执行一次」
  - engine.test.ts『取消点恰好两处（进守卫前 / 每轮重试边界）：execute → validate 之间是禁区』(test/locating/engine.test.ts:289) —— 锁住「写页面到校验返回之间不得有取消点」，可 port 成 Rust 层对 commit_window / cancellation 检查位置的契约测试

### ⑬ 闸①判据退化：状态翻转判定改用 className 子串，正是旧代码点名禁止的假成功

- **对应任务**：5.1（只覆盖「必须有校验环节」，判据强度未覆盖）；实现点在 `xhs-command-router.js`，本 change 按 design 不碰 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/flows/like-post.ts:27-60（属性白名单 + 3 层祖先回溯）；/Users/baitianxing/codes/aidcp-edge/src/flows/publish-command-handlers.ts:346-360（coverActiveValidator，fail-closed）`
  - 旧实现对「状态已翻转」有两套明确纪律。一是判据用**属性白名单 + 有限层级回溯**：只认 aria-pressed / aria-selected / data-liked / data-selected 四个属性等于 'true'，另外允许 class / aria-label / title 里出现「已点赞 / 取消点赞 / liked / active / selected」，且沿祖先最多回溯 3 层（因为真实页面翻转可能落在包裹容器上）。二是**对没实测过的判据一律 fail-closed**：封面校验只认一个精确锚点属性，实测校准前宁可诚实失败，也明确写下「绝不用宽泛 [class*=cover][class*=active] 子串误命中页面既有节点假成功」。
- **旧代码记下的真机经验**：
  > 封面后置校验：**fail-closed**——只认精确锚点 `note.publish_cover_active`（断言所选图真成封面，非仅点到）。
  >  * 真实 DOM 在 task-0 校准前不含此锚点 → 诚实失败，绝不用宽泛 [class*=cover][class*=active] 子串误命中页面既有节点假成功。
  >
  > "已点赞"态的判定信号（任一命中即视为点赞已生效）
  >
  > "已点赞"态的文本/类名关键词（可访问名或 class 含其一即视为已点赞）
  >
  > 在某元素及其祖先/自身上判断是否处于"已点赞"态。
  >  * 真实页面里点赞翻转可能落在按钮自身或其包裹容器上，故向上回溯有限层级。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:52（active）、:53（selected）、:287（set_cover 用 selected(tile)||selected(preview) 判封面已设）`
- **具体缺哪几样**：
  1. 把属性白名单 + 有限回溯换成一条 className 正则子串：/(active|selected|liked|collected|followed)/i.test(el.className)——任何混淆构建出的类名里偶然含 active/selected 就判「已生效」，这正是旧代码点名禁止的那类子串误命中
  2. 缺祖先回溯：新 active() 只看被点的那一个元素，翻转落在包裹容器上时判不出来（旧实现为此专门回溯 3 层）
  3. 缺 fail-closed 纪律：封面（:287）用 selected(tile)||selected(preview) 加一条 /已.*封面|封面.*已/ 文本正则，全是宽泛子串；旧实现在没有实测锚点时选择诚实失败而不是宽判
  4. aria-pressed 之外只多认 data-active='true'，丢了 aria-selected / data-liked / data-selected 三个属性信号；另一边 selected() 又新增了 aria-checked/aria-selected/aria-current 与 data-cover，两套判据口径不一致（active 与 selected 各认一半）
  5. interaction_like（:233）在 active(control) 之外补了 text(control).includes('已')——一个中文单字子串，会被「已读」「已关注」等任意含『已』的邻近文案误命中
- **可 port 的旧测试**：
  - xhs-semantic-class.test.ts『端到端：缓存锚点(classHint) → 引擎定位 span.like-wrapper → 点击 → 翻转 liked → success(cache)』(test/locating/xhs-semantic-class.test.ts:146) —— 锁住「翻转判定必须认到真实 liked 态」，可 port 成注入 JS 的 active() 契约测试（含反例：类名含 active 但业务未生效必须判否）

### ⑭ 闸①话题 token 校验退化为正文子串，实机校准过的真 token 判据丢失

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/flows/publish-post.ts:255-287（committedTopicPill）、:292-294（topicPillValidator）；对照被它取代的旧宽判在同文件 :233-241（case 'input_tag' 全局子串）`
  - 旧实现专门为「话题真的贴上了没有」做过一次实机校准，并把结论落成一个独立校验器：只认正文编辑器里生成的真话题元素（带 data-topic 的话题 token），比对时先剔除其中的隐藏后缀文本，再对话题名做**精确相等**比较（去前导 #、去所有空白、小写）。仅有纯文本 #关键词（用户打了字但没从下拉候选提交）明确判 false。它取代的正是「在整页里找子串」那版宽判，理由写在注释里。
- **旧代码记下的真机经验**：
  > 是否已在正文编辑器里生成「真话题 token」（change split-topic-roles，实机校准）。
  >  * XHS 提交话题后正文出现 `a.tiptap-topic[data-topic]`（文本 `#话题名`，`data-topic.name` = 话题名）。
  >  * 断言存在文本或 `data-topic.name` 与 keyword 匹配的 token；仅有纯文本 `#keyword`（未从下拉提交）→ false，
  >  * 治「静默假成功」（老 input_tag 校验只查全局子串，纯文本也误判成功）。
  >
  > token 文本形如「#话题名」，另含隐藏后缀 span.content-hide「[话题]#」——比对前先剔除该后缀。
  >
  > 精确匹配（**非子串**）：子串会把已存在的「#考研数学」误判成「考研」已贴上——正是本 change 要杜绝的静默假成功。
  >
  > 关键词后置校验器（best-effort）：校验目标值/关键词已出现在页面。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:256（publish_add_with_candidate 的 topic/mention 分支，末尾 norm(read).includes(norm(p.value)) 即判 done）`
- **具体缺哪几样**：
  1. 缺「真 token」判据：新实现只把正文文本读回来做 includes，用户打了 #考研 但下拉没提交、页面上只有裸文本时照样判成功——旧注释点名这就是要杜绝的静默假成功
  2. 缺精确相等：includes 让已存在的『#考研数学』把『考研』误判成已贴上（旧注释逐字写了这个反例）
  3. 缺隐藏后缀剔除：旧实现要先去掉 token 内的隐藏后缀 span 再比对，新实现直接读整段 innerText
  4. 缺 data-topic 结构信号：完全不看属性，只看文本
  5. 归一化更弱：旧实现去前导 # + 去所有空白 + 小写；新 norm() 只把连续空白折成单空格并 trim，前导 # 与大小写差异会导致误判
  6. 读回目标错位：新实现读的是整个编辑器文本（before + ' ' + value 是它自己刚写进去的），等于用自己写进去的输入证明输入生效——自证循环
- **可 port 的旧测试**：
  - （无同名旧用例可直接引用，但 committedTopicPill 的两条反例在注释里写死，可直接落成新引擎注入 JS 的契约测试：①只有裸文本 #关键词 必须判失败；②页面已有『#考研数学』时『考研』必须判失败）

### ⑮ 闸②重试上限 + 升级：整条机制缺席，escalated 语义被掏空

- **对应任务**：1.6、5.2、5.3
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:103-104（maxAttempts 默认 3、maxGuardRounds 默认 2）、:137-245（重试主循环）、:247-264（到顶判 no_target / escalated:systemic_revision）；/Users/baitianxing/codes/aidcp-edge/src/locating/types.ts:138-148（outcome 与 EscalationKind 三态枚举）`
  - 旧实现把「失败 → 换路径重试 → 到顶升级」做成引擎主循环：最多尝试 3 轮，每轮重新取页面根、重新定位、执行、后置校验。失败按原因分流——缓存命中但校验失败则把该动作标记为强制走模型重选（forceLlm），模型选不出则继续下一轮。三轮跑完仍不成，按「有没有真按下去过」分两种终局：一次都没执行过报 no_target；执行过但业务结果始终没发生，判定为平台系统性改版，报 escalated(systemic_revision) 并停手。它同时区分第三种升级 llm_unavailable：模型不可用时**立刻升级、不再重试**，不与改版混淆。
- **旧代码记下的真机经验**：
  > 2) 重试上限 + 升级：连续失败到上限 → 判系统性改版 → 停手并升级，绝不静默成功。
  >
  > // ---- 第二道闸：重试到上限 → 升级，绝不静默成功 ----
  >
  > 校验失败：不晋升、不静默
  >
  > 缓存锚点疑似失效，后续强制走 LLM
  >
  > MUST > 云端单次模型调用天花板 180s（见 client/cloud-selector.ts 的不变量）：压小了会把一次
  >    * **尚在进行的合法 thinking 选择**误判成 llm_error，而引擎见 llm_error 立刻升级上报、不再重试
  >    * ⇒ 一条本可成功的发布指令被判失败。
  >
  > systemic_revision // 连续校验失败，疑似系统性改版
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:556-596（execute_platform_command_once，函数名即「只跑一次」）、:496-531（唯一的重试：只读命令遇 CdpError/CdpConnectFailed 才重连并再跑一次）、:849-885（search 专属的 2 次 Enter 重试）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:242（plan_execute 里 attempts 恒为 1、outcome 直接写 'escalated'）`
- **具体缺哪几样**：
  1. 缺重试轮数上限这个概念：新引擎每条命令只跑一次；除了搜索回车（2 次）与只读命令的断连重连（1 次），没有任何「换路径再试」
  2. 缺 forceLlm 式的路径降级：旧引擎第二轮会主动放弃缓存锚点改走模型；新引擎没有第二条定位路径可换（见下一条缺口）
  3. 缺「执行过 vs 没执行过」的终局分流：新引擎用 EffectPhase 表达（NotStarted / Dispatched / Ambiguous / Confirmed，effect.rs:16-38），方向一致，但没有对应 no_target 与 systemic_revision 的区分——所有失败最终都塌成 ambiguous 或一条 reason 字符串
  4. escalated 语义被掏空：plan_execute（xhs-command-router.js:242）在单次尝试后就写 outcome:'escalated'、attempts:1，而旧口径里 escalated(systemic_revision) 的成立前提是「连续 maxAttempts 次校验都失败」——同一个词现在表示的是完全不同强度的事实
  5. 缺 llm_unavailable 这一档升级（因模型路径本身没了），以及旧代码明写的「见 llm_error 立刻升级、不再重试」这条纪律
  6. attempts 字段仍在协议里（model.rs:474-480，且 :526 把它 clamp 到 10），但注入 JS 只会填 1——字段活着、含义死了，云端据此做的任何「重试次数」判断都读到假值
- **可 port 的旧测试**：
  - engine.test.ts『系统性改版：连续校验失败到上限 → escalated(systemic_revision)，绝不静默成功』(test/locating/engine.test.ts:114) —— 锁住 maxAttempts=3、执行 3 次、终局 escalated/systemic_revision，可 port 成 Rust 层重试编排契约测试
  - engine.test.ts『LLM 选不出且无缓存 → no_target（不伪造成功）』(test/locating/engine.test.ts:199) —— 锁住「没定位到就不执行任何操作」且终局是 no_target 而非 escalated
  - engine.test.ts『静默误命中防护：缓存命中但校验失败 → 自愈走 LLM 重定位成功』(test/locating/engine.test.ts:76) —— 锁住 attempts=2、第一次点 decoy、第二次点 real，是「换路径重试」的最小契约

### ⑯ 闸③反污染回写与锚点缓存：整体不存在

> ⚠️ oracleQuality = `also-wrong` —— **不可照抄**，先看本文件开头那段。

- **对应任务**：5.4、5.5、5.7
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/cache.ts:1-136（AnchorCache 全体；:43 confirmThreshold 默认 2、:89-99 stage、:104-116 confirmStaged、:119-121 dropStaged、:128-135 snapshot/load）；/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:148-160（缓存优先读）、:219-225（成功后 recordHit / stage+confirm）、:238-243（失败后 recordFailure / dropStaged）；/Users/baitianxing/codes/aidcp-edge/src/client/edge-client.ts:583-588（anchor.get 通道，零调用方）`
  - 旧实现把锚点分主缓存与暂存区两层：运行时只读主缓存；模型新解析出的锚点先进暂存区，同一锚点连续确认成功达到阈值（默认 2 次）才晋升主缓存；任何一次后置校验失败就直接丢弃暂存项，永不晋升。暂存中若新解析出的锚点与上次不一致，确认计数归零（说明还不稳定）。另有三种模式：运行时读写、只读（生产推荐，运行时绝不回写、新锚点只能离线或金丝雀晋升）、只写（get 恒空强制每次走模型，仅建库阶段用）。主缓存命中成功会累计命中数并清零失败数，命中后校验失败则累计失败数。
  - ⚠️ **caveat**：判 also-wrong：这一层旧实现自己也只做了一半。① 主缓存是纯进程内 Map，snapshot/load 全仓**零调用方**（只有 like-runner.ts:45 会 new 一个空缓存），进程一重启锚点全丢，所谓「晋升」在真机上从未跨会话生效过。② 跨进程/跨账号共享的那条路（协议 anchor.get / anchor.report）边缘侧只有一个 getAnchor 包装、同样零调用方，云端 PG 主缓存同步从未接线。所以照抄它只能得到一个「重启即空」的缓存；要在新引擎里做，必须把持有位置和持久化一并设计，不能只搬类。
- **旧代码记下的真机经验**：
  > 3) 反污染回写：LLM 新锚点先暂存，连续确认成功才晋升主缓存（见 cache.ts）。
  >
  > 反污染要义：一次 LLM 解析**不**直接覆盖主缓存，避免单次错误被复制成系统性故障。
  >
  > read-write：运行时读主缓存；LLM 新锚点先进暂存区，连续确认成功 confirmThreshold 次才晋升主缓存。
  >  * - read-only ：只读主缓存，运行时绝不回写（生产推荐）。新锚点只能离线/金丝雀晋升。
  >  * - write-only：get 始终返回空（强制每次走 AI），仅用于建库阶段批量写主缓存。
  >
  > 若暂存的锚点与新解析不一致，重置确认计数（说明还不稳定）
  >
  > 暂存锚点校验失败：丢弃，不让其晋升
  >
  > 语义类名线索（反混淆白名单内的稳定 class，如 like-wrapper）。
  >    * 用于无 aria/role/text 的站点（如小红书）按"已知语义 class"匹配；
  >    * 命中加分但绝不信任任意 class——只认 extractor 白名单识别出的语义 class。
- **新引擎现状**：`新引擎无对应物。最接近的两处：/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:107-129（EngineSession 的进程内会话态，仅有 seen_post_ids / active_list_url / last_refresh_reload_at_ms）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook-router/00-shared.js:205-228（window.__aidcpNativeFirstPostTargets，页面态的目标绑定表）`
- **具体缺哪几样**：
  1. 缺锚点这个概念本身：注入 JS 每次都从选择器常量表现场找元素（xhs-command-router.js:59、:90、:145-152），没有「上次成功用的定位指纹」可复用，也就无所谓污染或晋升
  2. 缺暂存区 / 确认阈值（默认 2）/ 晋升 / 丢弃四个动作，以及「暂存锚点变化即重置计数」这条不稳定性检测
  3. 缺三种缓存模式（read-write / read-only / write-only）与它们背后的运维意图：生产只读、建库只写
  4. 缺命中与失败计数（hitCount / failCount / lastVerified），因此也没有「某锚点连续失败 ⇒ 疑似改版」这类可观测信号
  5. 缺跨进程持有：唯一的进程内状态在 EngineSession（engine.rs:107-129），无持久化、无快照导出；FB 侧那张目标绑定表挂在 window 上（00-shared.js:205-211），页面一 reload 就没了
  6. 缺定位指纹的多信号结构（role / text / textMatch / scope / attributes / classHint）——注入 JS 用的是硬编码 CSS 选择器串与关键词表，改版即整条命令失效，没有可自愈的中间表示
- **可 port 的旧测试**：
  - cache.test.ts『反污染：暂存锚点不直接进主缓存，连续确认达阈值才晋升』(test/locating/cache.test.ts:9) —— 纯逻辑，可逐字 port 成 Rust 单测
  - cache.test.ts『暂存校验失败 dropStaged 阻止晋升』(test/locating/cache.test.ts:27)
  - cache.test.ts『暂存锚点变化会重置确认计数（不稳定不晋升）』(test/locating/cache.test.ts:38)
  - cache.test.ts『read-only 模式不暂存但允许读取已有主缓存』(test/locating/cache.test.ts:48)
  - cache.test.ts『write-only 模式 get 恒为空（强制走 AI）』(test/locating/cache.test.ts:55)
  - cache.test.ts『snapshot/load 往返一致』(test/locating/cache.test.ts:63) —— 这条在 port 时应升级为「跨进程/跨会话往返」，因为旧实现的往返从未被真实调用
  - engine.test.ts『反污染回写：LLM 新锚点需连续确认才晋升主缓存』(test/locating/engine.test.ts:139) —— 锁住「第一次成功不晋升、只进暂存；第二次确认才晋升」

### ⑰ 匹配唯一性闸（置信度 0.6 / 分差 0.15 / 权重表）缺失：新引擎「首个可见即取」

- **对应任务**：5.8（本 change 明确**不**承接，只要求把边界记下来、不得被当成已覆盖）
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/matcher.ts:1-8（职责声明）、:19-22（confThreshold 0.6 / marginThreshold 0.15）、:24-31（权重 role 1.0 / text 2.0 / attr 1.0 / classHint 5.0 及其算式说明）、:38-42（contains 双向包含）、:94-132（打分、排序、conf 闸、margin 闸、ambiguous 降级）`
  - 旧实现明确把「反静默误命中」当成匹配层的核心职责，写死了不是「找到第一个就点」：对作用域内每个候选元素按锚点指定的多个信号分别打分（角色权重 1、可见文本权重 2、每个稳定属性权重 1、语义类名权重 5），得分是命中权重除以被指定权重；排序后取最佳，只有当最佳分达到 0.6 且与次佳的分差达到 0.15 时才判命中；分不够判 miss，分够但有并列/接近候选判 ambiguous，两种都降级到模型重选——注释原话是宁可多花一次也不点错。语义类名权重取 5 是算过的：5/(1+2+5)=0.625 刚好越过 0.6，保证在小红书这种既无 aria 又无文字的站点上，单靠语义类名也能命中。
- **旧代码记下的真机经验**：
  > 反"静默误命中"是这里的核心职责：
  >  * - 不是"找到第一个就点"，而是对每个候选按 anchor 指定的多个信号（role/text/attrs）打分；
  >  * - 只有当**唯一**候选同时满足"置信度达标 + 与次佳分差达标"才判 hit；
  >  * - 否则判 ambiguous / miss，交由上层降级到文本 LLM 重选，宁可多花一次也不点错。
  >
  > 语义 class 命中（如 like-wrapper）：在无 aria/role/text 的站点（小红书）里，
  > // 这是唯一可用且高度可信的稳定信号。权重取得足够大，使得即便锚点同时指定了
  > // role/text（为兼容暴露无障碍属性的站点而保留）但在 XHS 上二者均落空，
  > // 仅凭语义 class 命中也能越过 confThreshold(0.6)：5/(1+2+5)=0.625。
  >
  > 置信度够，但有并列/接近候选 → 不唯一 → 防误命中，降级 LLM
  >
  > contains：双向包含都算（锚点是元素文本子串，或反之）
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:14-19（first()：按选择器顺序取首个可见）、:145-152（findByWords()：按 button/span/div 三档取首个文本含关键词的）、:59-89 与 :90-118（卡片与详情抽取同样首个即取）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook-router/00-shared.js:213-228（唯一的歧义判据：first-post 目标绑定冲突时报 ambiguous_target）`
- **具体缺哪几样**：
  1. 缺打分：没有任何多信号一致性评分，一个 CSS 选择器命中就用
  2. 缺置信度闸 0.6：没有「信号不够就不动手」这个状态，找到即执行
  3. 缺分差闸 0.15 与 ambiguous 状态：页面上两个等价候选时，新实现按 DOM 顺序取第一个，正是旧注释点名的误命中
  4. 缺权重表（1 / 2 / 1 / 5）与那条算式约束——语义类名要能单独越过阈值这件事在新引擎里无处表达
  5. 缺 contains 的双向包含语义（锚点文本是元素文本子串或反之），新引擎 findByWords 只做单向 includes
  6. 缺 miss / ambiguous / hit 三态与它们各自的降级目标；新引擎只有「找到 / 没找到」两态，没找到就是 control_not_found 终局
  7. FB 侧仅在 first-post 场景保留了一条歧义判据（同一目标引用绑到两个不同根即报 ambiguous_target），是唯一残留的唯一性检查，且不基于打分
- **可 port 的旧测试**：
  - matcher.test.ts『唯一高置信度 → hit』(test/locating/matcher.test.ts:10)
  - matcher.test.ts『多个等价候选 → ambiguous（防静默误命中）』(test/locating/matcher.test.ts:20) —— 最关键一条：锁住「并列候选不许随便点一个」
  - matcher.test.ts『信号都不匹配 → miss』(test/locating/matcher.test.ts:29)
  - matcher.test.ts『稳定属性提升唯一性，打破并列』(test/locating/matcher.test.ts:37)
  - matcher.test.ts『空清单 → miss』(test/locating/matcher.test.ts:54)
  - xhs-scoped-search.test.ts『matcher: after scoped extract, like-wrapper hits uniquely』(test/locating/xhs-scoped-search.test.ts:114)
  - xhs-semantic-class.test.ts『matcher：仅靠语义 classHint 即可唯一命中点赞控件』(test/locating/xhs-semantic-class.test.ts:98) —— 锁住权重 5 那条算式约束

### ⑱ 守卫层（干扰扫描 + 多轮清障 + guard_blocked 终局）缺失

> ⚠️ oracleQuality = `stale` —— **不可照抄**，先看本文件开头那段。

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:118-130（进主流程前先跑守卫，不过则 guard_blocked/guard_unhandled）、:268-291（handleGuards 多轮清障，maxGuardRounds 默认 2，仍有残留报 guard_persist）；/Users/baitianxing/codes/aidcp-edge/src/locating/guard.ts:41-63（三条内置规则）、:66-76（findByText 关闭类按钮）、:86-108（scanInterrupts，同一规则命中一次即止）`
  - 旧实现在每个原子操作前先扫一遍页面，按规则识别已知的偶现干扰（模态框、遮罩层、登录过期提示），命中就先点它内部的关闭类按钮再继续主流程；扫描按规则逐条来、同一规则命中一次即止。清障最多做 2 轮，2 轮后仍有残留则判 guard_persist 停手。识别不依赖混淆 class，走 role/aria-modal/文本；关闭按钮按可见文本在「关闭、取消、知道了、我知道了、稍后再说、跳过」里找，且只认 role 为按钮或链接且可见的元素。规则枚举不完的部分留了一个可注入的模型兜底检测接口。若某条干扰没有配对的关闭动作，直接报 unhandled_guard 而不是硬闯。
  - ⚠️ **caveat**：判 stale：三条内置规则是 2026-06 的小红书 / 通用形态，其中『overlay_mask』靠 data-type="mask" 与 data-role 里的 mask/overlay/backdrop 识别，是当时那版 DOM 的特征；FB 与 Reels 的阻断浮层（同意、频率限流、参与答题、登录检查点）完全不在这三条里。可照抄的是**编排骨架与阈值**（动作前必扫、清障最多 2 轮、无配对关闭动作即 unhandled 停手、扫描不依赖混淆 class），规则库必须按当前各平台重建，不能照搬那三条 match 条件。另注意：新引擎已在别处积累了旧守卫没有的真机经验（FB 同意浮层、频率限流弹窗、参与答题闸），这些应并入新守卫规则库而不是被守卫覆盖掉。
- **旧代码记下的真机经验**：
  > 守卫层：清理偶现干扰（弹窗/遮罩/活动浮层/青少年模式/登录过期提示）。
  >  *
  >  * 每个原子操作前先扫一遍 DOM，发现已知干扰 → 上层先处置（关闭/跳过）再继续主流程。
  >  * 规则枚举不完的部分，可注入 LLM 判定兜底（detectExtra）。
  >
  > 常见小红书/通用干扰的内置规则（按文本/role/属性识别，不依赖混淆 class）
  >
  > 同一规则命中一次即可
  >
  > 多轮后仍有干扰
  >
  > 安全点 ①：进守卫之前（守卫会关浮层 = 页面写）
  >
  > 被接管 ≠ 关不掉浮层：绝不降级成 guard_blocked
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:154-289（命令分发段：进任何动作前都没有干扰扫描；:157 仅在 browse_next 时顺手关一次详情弹层）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook.rs:415-416、:1195（consent_probe，FB 同意浮层专用一条）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/facebook-router/00-shared.js:378-383（对话框只用来做作用域回溯，不做清障）`
- **具体缺哪几样**：
  1. 缺「动作前必扫一遍干扰」这个统一环节：新引擎任何命令都直接开始找目标元素，浮层挡住时表现为目标找不到（control_not_found）或点到浮层，而不是先清障
  2. 缺多轮清障与轮数上限（2 轮）以及 guard_persist 这个终局
  3. 缺 guard_blocked / guard_unhandled 两个终局态，以及「没有配对关闭动作就停手、不硬闯」这条纪律
  4. 缺关闭按钮的中文文案词库（关闭 / 取消 / 知道了 / 我知道了 / 稍后再说 / 跳过）与「只认可见的按钮或链接」这条约束
  5. 缺可注入的模型兜底检测接口（规则枚举不到的偶现干扰）
  6. 现存的替代品只有两处且都是单点专用：xhs 侧只在翻页时关一次详情弹层；FB 侧只有同意浮层探测，各自独立、没有共享的干扰规则库
- **可 port 的旧测试**：
  - engine.test.ts『守卫层：偶现弹窗被清除后再继续主流程』(test/locating/engine.test.ts:167) —— 锁住执行顺序：第一个动作必须是点关闭按钮、第二个才是主操作，且弹窗真被移除。这条的编排断言可直接 port，DOM 桩需换成当前平台形态

### ⑲ 定位缺口的模型兜底路径整体消失：找不到即终局，无第二条路

- **对应任务**：5.4（暂存区的锚点原料依赖它）；模型兜底路径本身无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:162-193（缓存缺口 → 抽清单 → 模型选编号 → 构候选锚点）、:69-90（anchorFromElement）；/Users/baitianxing/codes/aidcp-edge/src/locating/selector.ts:1-8（关键防护）、:62-87（提示词，含小红书无障碍属性缺失的处置）、:99-127（编号解析 + 越界防幻觉）；/Users/baitianxing/codes/aidcp-edge/src/locating/extractor.ts:60-100（语义 class 白名单与边界匹配）`
  - 旧实现在缓存锚点没命中时不放弃：把当前作用域内的可交互元素抽成一份编号清单（只输出角色、可见文本、稳定属性白名单、语义类名、结构路径，绝不输出混淆 class），交文本模型做选择题，模型只被允许回一个整数编号或 -1。回来的编号必须落在清单内，否则判 index_out_of_range，防模型幻觉。选中后不直接晋升，而是据此构造候选锚点交给第三道闸。提示词里明确写了小红书这类站点刻意不给无障碍属性时改用语义类名推理，并交代不要凭随机/混淆类名猜（那些已被上游过滤、不会出现在清单里）。
- **旧代码记下的真机经验**：
  > 文本 LLM 元素选择（缓存缺口时的"做选择题"路径）。
  >  *
  >  * 把作用域内的可交互元素清单格式化成编号列表，交豆包/Qwen 文本模型选出目标编号。
  >  * 关键防护：
  >  * - 强约束输出为编号（或 -1 表示无），并**校验编号在范围内**，防 LLM 幻觉越界。
  >  * - 选择器只产出"选哪个元素"，不直接操作，便于上层加后置校验。
  >
  > 防幻觉：编号必须落在清单范围内
  >
  > 部分站点（如小红书）刻意不提供任何无障碍属性：role 多为 generic、
  >     无 aria-label、无"点赞"等文字，图标是纯 SVG，计数是裸数字。此时请改用
  >     **语义类名** class~="..." 推理
  >
  > 类名命中目标语义时，即使没有任何文字/aria 也应大胆选它；
  >     但不要凭随机/混淆类名（无语义的乱码）猜测——这些已被上游过滤、不会出现在清单里。
  >
  > 选元素是一段**纯等待**（平台侧零副作用）：接管时就地作废在飞请求。选择器 MUST 让
  >         // TaskTakeoverError 原样穿出——吞成 llm_error 会走下面的 escalated 分支，把一次「让路」
  >         // 谎报成「模型不可用、已升级」。
  >
  > 语义 class 线索（如 like-wrapper）随锚点回写，便于晋升后按稳定语义 class 命中。
- **新引擎现状**：`新引擎无对应物。终局在注入 JS 里直接给出：/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:233（control_not_found）、:236（comment_editor_not_found / comment_submit_not_found）、:248（publish_mode_not_found）、:251（publish_field_not_found）、:289（unsupported_command）`
- **具体缺哪几样**：
  1. 缺「作用域内可交互元素清单」这个中间表示：新引擎没有 extractInteractiveElements 的等价物，也就没有任何东西可以喂给外部判断器
  2. 缺模型选择题路径与 CloudElementSelector：新引擎的定位规则是编译进二进制的固定选择器串，改版即命令级失效，没有兜底
  3. 缺编号越界这类防幻觉校验（新引擎无模型输入，此条属附带丢失）
  4. 缺「选中元素 → 构造候选锚点」这一步（anchorFromElement 会挑出 aria-label / data-testid / data-id / name / type 与语义类名作为指纹），因此第三道闸即使补上也无原料
  5. 缺提示词里那套针对无障碍属性缺失站点的定位知识（改用语义类名、不许凭混淆类名猜）——这是本仓少见的、写成自然语言的定位经验
  6. 副作用：旧引擎「见 llm_error 立刻升级为 llm_unavailable、不再重试」与「选元素是纯等待、可就地作废、TaskTakeoverError 必须原样穿出」两条纪律在新引擎里无处安放，取消语义改由 commit_window（commit_window.rs:38-91）与 EffectTracker 表达
- **可 port 的旧测试**：
  - engine.test.ts『云端选元素在飞时被接管 → 就地作废抛 TaskTakeoverError，不等满 200s、零页面副作用』(test/locating/engine.test.ts:237) —— 锁住「让路不得谎报成模型不可用」+「零页面写、零缓存记账」，取消语义部分可 port 到 Rust 的 cancellation/commit_window 契约
  - engine.test.ts『LLM 选不出且无缓存 → no_target（不伪造成功）』(test/locating/engine.test.ts:199)
  - xhs-semantic-class.test.ts『端到端：无缓存 → 选择器按 classHint 选中 like-wrapper（不误选 comment/collect）』(test/locating/xhs-semantic-class.test.ts:183)
  - xhs-scoped-search.test.ts『e2e: explore + modal, selector only sees the single modal like-wrapper』(test/locating/xhs-scoped-search.test.ts:159) —— 锁住「作用域限定后清单里只剩唯一目标」

### ⑳ 语义 class 白名单的边界匹配退化为 [class*="like"] 子串

- **对应任务**：本 change 无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/extractor.ts:60-72（设计原则注释）、:73-78（白名单四项）、:84-100（matchSemanticClass，按 class token 内 - _ 或边界分隔做词边界匹配）；/Users/baitianxing/codes/aidcp-edge/src/locating/types.ts:47-52（classHint 的信任边界）`
  - 旧实现的原则是绝不信任任意 class：混淆构建会把类名打成随机串，不可作定位依据；但少数站点对核心互动控件保留人类可读、跨改版稳定的语义类名（点赞、评论、收藏、分享四个 wrapper），这四个是手写语义而非编译产物，才被允许作为稳定属性参与匹配。匹配方式是把 class 拆成 token，要求白名单片段是整个 token，或被连字符/下划线包裹——既容忍 BEM 与前缀写法，又不会把随机串里偶然出现的子串误当语义命中。命中后只输出规范化的语义片段，绝不输出原始混淆 class。
- **旧代码记下的真机经验**：
  > 反混淆"语义 class 白名单"。
  >  *
  >  * 设计原则（与反混淆设计一致）：**绝不信任任意 class**。混淆构建会把 class
  >  * 打成随机串（如 .css-1a2b3c），不可作为定位依据；但少数站点（典型如小红书）
  >  * 对核心互动控件保留**人类可读、跨改版稳定的语义 class**（like-wrapper /
  >  * comment-wrapper / collect-wrapper / share-wrapper）。这些是手写语义而非
  >  * 编译产物，值得作为"稳定属性"参与匹配。
  >  *
  >  * 只认这里列出的精确语义片段：用单词边界匹配（- _ 或串首尾分隔），既容忍
  >  * BEM/前缀（note-footer__like-wrapper、xhs-like-wrapper），又不会把随机串
  >  * 里偶然出现的子串误当语义命中。
  >
  > 从元素 class 中识别"已知语义 class"。命中返回规范化的语义片段，否则 null。
  >  * 用单词边界（class token 内以 - _ 或边界分隔）匹配，避免子串误命中。
  >
  > 边界匹配：pat 必须是整个 token，或被 - _ 包裹（容忍 BEM/前缀）。
  >
  > 不输出混淆 class；输出 role/text/稳定属性 + 结构路径（tag+nth）。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:73-74（[class*="like"] / [class*="collect"]）、:90（详情根 [class*="note-detail"] 等）、:95（[class*="desc"] / [class*="content"]）、:105-107（[class*="like"] / [class*="collect"] / [class*="comment"]）、:284（[class*="preview"]）、:52（active() 的 className 子串正则）`
- **具体缺哪几样**：
  1. 把词边界匹配换成 CSS 属性子串选择器 [class*="…"]：混淆类名里偶然含 like / collect / comment / content / preview 的元素都会命中，正是旧注释点名要避免的子串误命中
  2. 缺白名单闭集：新引擎按需现场拼子串（like / collect / comment / title / author / desc / content / note-detail / noteDetail / preview / upload / note-card / publish-item…），没有一份「只认这几个手写语义片段」的清单，也就没有「其余 class 一律不信」这条界
  3. 缺 BEM/前缀容忍的显式语义：子串匹配虽然也能命中 note-footer__like-wrapper，但同时命中 css-1like3c 这类噪声，等于用放宽换兼容
  4. 缺「只输出规范化语义片段、不输出原始混淆 class」这条输出侧约束（新引擎不产出元素清单，此条随清单一并丢失）
  5. 子串匹配与「首个可见即取」叠加放大：:105 的 [class*="like"] 取首个可见，页面上任何更靠前的含 like 类名节点都会被当成点赞控件读计数
- **可 port 的旧测试**：
  - xhs-semantic-class.test.ts『matchSemanticClass：白名单精确边界匹配，容忍 BEM/前缀，拒绝子串误命中』(test/locating/xhs-semantic-class.test.ts:80) —— 最直接可 port 的一条，纯字符串逻辑，可原样落成注入 JS 或 Rust 的语义类名匹配契约测试
  - xhs-semantic-class.test.ts『反混淆：仅纯混淆 class 的元素不被当作可交互（不信任任意 class）』(test/locating/xhs-semantic-class.test.ts:71)
  - xhs-semantic-class.test.ts『XHS 风格 DOM（无 aria/role/text）：extractor 通过语义 class 抽出互动控件』(test/locating/xhs-semantic-class.test.ts:55)

### ㉑ 两个可换接口（DomProvider / ActionExecutor）消失：脱离浏览器单测定位逻辑的能力没了

- **对应任务**：1.3 / 1.4 的「Rust 假 CDP 测试」隐含需要可替换的执行层；两个抽象本身无对应任务 —— 见文末覆盖漏洞
- **旧实现**：`/Users/baitianxing/codes/aidcp-edge/src/locating/engine.ts:24-41（DomProvider / ActionExecutor / PostValidator 三个接口）、:61-67（EngineDeps 全部靠注入）；/Users/baitianxing/codes/aidcp-edge/src/cdp/dom-provider.ts:1-13（设计取舍注释）、:30-63（CDP 实现：取 outerHTML 再用 jsdom 解析）；/Users/baitianxing/codes/aidcp-edge/src/cdp/action-executor.ts:1-12（为何用页面侧 JS 而非坐标点击）、:27-30（结构路径即 XPath）、:37-58（执行后校验命中，未命中即抛）`
  - 旧实现把「拿 DOM」和「把操作落到页面」抽成两个窄接口，引擎只依赖接口。真机下的 DOM 提供者通过 CDP 取整页 outerHTML，再在 Node 侧用 jsdom 解析成标准 Document，让抽取与匹配这两段纯函数不必改动即可复用；单测下直接塞一个 jsdom document。执行器把抽取产出的结构路径（tag+nth，不含混淆 class）转成 XPath，在页面侧重新定位再操作，并在执行后检查表达式是否真返回 true，未命中即抛错。设计取舍写在注释里：用快照而非 DOM 树是为了复用既有抽取逻辑，一次操作周期内 DOM 稳定；jsdom 无布局，可见性判定是 best-effort。
- **旧代码记下的真机经验**：
  > 提供当前 DOM 根（真实边缘下由 CDP 快照，单测下为 jsdom document）
  >
  > 执行层：把原子操作落到真实页面（CDP click/input/scroll）
  >
  > 设计取舍：
  >  * - 用 outerHTML 快照而非 DOM.getDocument 树，是为了直接复用既有 DOM-first 抽取逻辑；
  >  *   抽取/匹配是纯函数，快照足够（一次操作周期内 DOM 稳定）。
  >  * - jsdom 无布局，可见性判定走 best-effort（与单测一致），真实可见性可后续接 CDP 增强。
  >
  > 为什么在浏览器侧用 JS 执行而非 Input.dispatchMouseEvent 坐标点击：
  >  * - 结构路径定位天然对改版更稳，且无需读取布局坐标；
  >  * - 触发原生事件序列（focus/input/change）可覆盖大多数受控组件。
  >  * 后续如需真实硬件级事件，可在此切换到 Input.* 域。
  >
  > 抽取/匹配均作用于通用 DOM（既可在浏览器 page.evaluate 中运行，也可在 jsdom 中单测）。
- **新引擎现状**：`/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/engine.rs:107-123（EngineSession 直接持有 CdpSession，无抽象层）、:556-596（平台分发直接对着 session.cdp）；/Users/baitianxing/codes/aidcp-edge/native/page-engine/src/xhs-command-router.js:1-4（注入 JS 只在真实页面里运行，document 是全局隐式依赖）`
- **具体缺哪几样**：
  1. 缺 DOM 提供者抽象：新引擎的定位逻辑写在注入 JS 里，隐式依赖真实页面的 document / getComputedStyle / getBoundingClientRect，没有可替换的 DOM 来源
  2. 缺执行器抽象：Rust 侧直接对 session.cdp 发指令，注入 JS 直接调 el.click()；没有一层可以在测试里替成假执行器并记录调用序列
  3. 后果：定位与判据逻辑无法脱离浏览器单测。旧仓 test/locating/ 下 912 行用例全部跑在 jsdom 桩上、无需起浏览器；新引擎对应逻辑只能靠真机验证
  4. 缺「结构路径（tag+nth，不含混淆 class）」这个可搬运的定位表示；注入 JS 用现场 CSS 选择器，无法把一次成功的定位序列化出来给别处复用或断言
  5. 缺执行后的命中自检：旧执行器要求页面侧表达式返回 true 才算执行成功，未命中即抛（会被引擎当 exec_error 并换路径）；新 click()（xhs-command-router.js:45-51）在元素不可见时返回 false，但多数调用点不查返回值，直接进 sleep 后复检
- **可 port 的旧测试**：
  - test/cdp/dom-provider.test.ts『CdpActionExecutor 用 XPath 表达式驱动点击并校验命中』(test/cdp/dom-provider.test.ts:39) 与『CdpActionExecutor 在元素未命中（返回非 true）时抛错』(:60) —— 锁住「执行未命中必须抛、不得当成功」，可 port 成注入 JS 的 click 返回值契约
  - test/cdp/dom-provider.test.ts『CdpDomProvider 把页面 HTML 快照解析成可抽取的 Document』(:20) 与『CdpDomProvider 在 evaluate 异常时抛错』(:33)
  - test/locating/extractor.test.ts 全部三条（:6 抽取可见可交互元素，排除隐藏元素 / :29 作用域消歧：信息流中只抽取目标卡片内的元素 / :50 作用域不存在时返回空清单）—— 纯 DOM 逻辑，是「注入 JS 可脱机测」这件事能否成立的最小验证集

## 覆盖漏洞

下列条目在参照书里有、但本 change 的 `tasks.md` 里找不到对应任务。**它们是起草时的覆盖漏洞，不是「已具名不做」**—— design.md 的「具名不做的事」只登记了文件输入原语、最小间隔 gating 与反射采样、可见性/几何/歧义拒绝、其他平台的**指针**调用点这四类，下面一条都不在其中。

### ④ 运营真机鼠标轨迹回放通道整体缺失（且被宿主静默丢弃）

- **漏在哪**：这条含一个**红线级**事实：宿主 `src/main.ts:992-1001` 手工枚举转发字段时把轨迹样本丢掉且不打任何日志，`:1014` 又把回执里的回放模式硬编码成 `synthetic`——云端把真轨迹带下来时，边缘既没用它、也没如实说没用，那个字段现在是常量。旧实现在这里是要打「轨迹无效、回落合成」的可观测日志的。这是「静默假成功」的一个变体（谎报回放模式），不该等第二个 change。
- **建议**：至少把「丢弃必须可观测 + 回放模式字段不得硬编码」拆成本 change 一条任务（改 `main.ts` 会与 `restore-native-xiaohongshu-session-guards` 撞车，可只改回执模式与日志两处并串行集成）。轨迹通道本体（引擎参数结构体加字段、按下前补权威落点一帧、只裁不压缩的 120ms 上限、五项校验、漏点补发）工作量大，另起 change 承接并在 `docs/real-machine-acceptance-backlog.md` 的验证码协助簇留名。

### ⑤ 小红书全线打字退化为一次性设值 + 合成事件

- **漏在哪**：小红书除搜索框外的全部文本输入不走硬件级输入通道，用属性描述符 setter 直接灌值再派合成事件（对 React 受控组件是 `isTrusted=false` 的非可信输入）。**Rust 侧其实已有逐字实现、参数与旧版逐项一致（`input.rs:93-137`），只是小红书路径没接线**——这不是「重建能力」而是「已有原语没接上」，成本远低于本 change 其他条目。design 只声明「其余平台的**指针**调用点未做盘点」，文本输入这一半无人具名。
- **建议**：要么在本 change 加一条「盘点并接线小红书文本输入到已有逐字原语」（实现点在 `xhs-command-router.js`，属 `restore-native-xiaohongshu-action-honesty` 单写区，需与属主对齐落地方式，处置形态同 5.3）；要么在 4.7 的残留缺口登记里一并写明，不能整条无声消失。

### ⑥ 小红书正文换行的段落原语与有界归尾确认丢失

- **漏在哪**：旧实现为此踩过真机坑并把结论写死在注释里（dev record #153：段落重排与选区更新互相抢跑，尾字逐块倒序堆到文末），由此立了「正文必须拆成纯文本写入 + 独立裸回车」「任何文本写入不许携带回车符」「每次回车后有界确认：前缀仍在 + 换行数达标 + 光标在末端且连续两次稳定」三条纪律。新实现把整段（含换行）一次性赋给 `textContent`，段落结构根本不会生成，失败只报一个笼统的回读不一致、不区分病因。这是本参照书里**真机代价最高**的一条经验，本 change 无任何承接方。
- **建议**：单独立 change（发布链路的正文填写），把旧的五条测试用例整组 port；本 change 至少在 4.7 或 5.8 的残留缺口登记里点名，避免它随退役代码被剪枝后无人记得。

### ⑦ 小红书滚动退化为页面内一次性平滑滚动

- **漏在哪**：旧注释**逐字写明**页面内 `scrollBy` 在小红书窄布局上是空操作、feed 永不推进——新实现正是回到了那个被点名的形态。同缺口 ⑤：**Rust 侧已有等价惯性滚轮实现、参数逐项一致（`input.rs:43-65`、`:269-310`），小红书路径没接线**。本 change 第 3 节只把手势扩到 Facebook 的对齐滚动与 Reels 兜底，小红书三处滚动一条没提。
- **建议**：本 change 第 3 节可顺势加一条「小红书三处滚动改接共享惯性手势」（同属单写区，需与属主对齐）；不做则必须登记为残留缺口，并把 `test/facebook/viewport-scroll.test.ts` 那条「已移动时不走 JS 兜底」列为待 port。

### ⑪ 两个注入路由通用点击助手里的 `scrollIntoView` 瞬移（本 change 只覆盖了 Facebook 浮层那一半）

- **漏在哪**：`xhs-command-router.js:45-51` 与 `facebook-router/00-shared.js:34-38` 两个通用点击助手第一件事就是 `el.scrollIntoView({block:'center'})`——**正是旧测试写成断言明令禁止的瞬移**（`test/facebook/like-executor.test.ts:193-225`），它让页面位置瞬间跳变、完全绕开节奏层；小红书那个助手还额外派发一个坐标写成元素外接框左上角 +4px 的伪造 `mousemove`。任务 2.6 只处理 Facebook 反应浮层的起点与过冲，没覆盖这两个助手。
- **建议**：`facebook-router/00-shared.js` 不在任何并行 change 的 Impact 里，本 change 可直接加一条「删掉通用点击助手里的 scrollIntoView 与伪造 mousemove，改由拟人滚轮手势带目标进视野」，并把旧测试那条静态断言（点击脚本文本里不得含 `scrollIntoView`）port 成常驻门禁。注意 oracle 已澄清：**不是所有页面内点击都该改**——加群按钮与信息流点赞主控件走页面内点击是真机验证过的正确形态。

### ⑬ 状态翻转判据退化为 className 子串（5.1 只要求「有校验环节」，未要求判据强度）

- **漏在哪**：新实现用一条 `/(active|selected|liked|collected|followed)/i` 测 `className`，混淆构建里偶然含 `active` 的类名即判「已生效」；还补了 `text(control).includes('已')` 这个中文单字子串，「已读」「已关注」都会误命中。旧实现是属性白名单（四个属性等于 `'true'`）+ 最多回溯 3 层祖先，且对没实测过的判据一律 fail-closed。任务 5.1 只要求「按同一绑定目标读回业务结果」——**一条子串正则完全满足 5.1 的字面**。
- **建议**：在 5.1 或 5.6 里补一句判据强度要求（属性白名单 + 有限祖先回溯 + 无实测锚点时 fail-closed、禁子串误命中），并把 `xhs-semantic-class.test.ts:146` 那条反例（类名含 active 但业务未生效必须判否）列为待 port。实现点在单写区，处置形态同 5.3。

### ⑭ 话题 token 校验退化为正文子串（含一处自证循环）

- **漏在哪**：旧实现为「话题真的贴上了没有」做过实机校准：只认正文里生成的真 token（带 `data-topic`）、剔隐藏后缀、对话题名做**精确相等**，纯文本 `#关键词` 明确判 false，并把「子串会把已存在的『#考研数学』误判成『考研』已贴上」这个反例逐字写进注释。新实现读整段编辑器文本做 `includes`，而它读回的正是它自己刚写进去的那段——**自证循环：用输入证明输入生效**。本 change 无任何任务覆盖。
- **建议**：与缺口 ⑥ 合并进「发布链路正文/话题填写」的后继 change；注释里写死的两条反例可直接落成契约测试、不需要真机。至少在残留缺口里点名，别让「实机校准过的判据」无声流失。

### ⑱ 守卫层（动作前干扰扫描 + 多轮清障 + 停手终局）缺失

- **漏在哪**：旧引擎在每个原子操作前先扫一遍已知干扰、命中即先关再继续，清障最多 2 轮、残留即停手，且「没有配对关闭动作就报未处置、不硬闯」。新引擎任何命令都直接开始找目标，浮层挡住时表现为「目标找不到」或直接点到浮层。design.md 与 tasks.md 从头到尾没出现过守卫层——它既不在三道闸内，也不在具名不做的清单里，是**纯遗漏**。
- **建议**：本 change 至少在 5.8 的承接边界里显式写下「守卫层不在本 change 内、由 X 承接」，否则「三道闸已恢复」会被读成「定位层已补齐」。另起 change 时按其 stale caveat 重建规则库，并把新引擎已积累的真机经验（FB 同意浮层、频率限流弹窗、参与答题闸、登录检查点）并入，**不要让新守卫覆盖掉它们**。

### ⑲ 定位缺口的模型兜底路径整体消失（直接掐断 5.4 的原料）

- **漏在哪**：旧引擎缓存没命中时把作用域内可交互元素抽成编号清单交文本模型选，选中后据此构造候选锚点交第三道闸，并带编号越界防幻觉、「见模型不可用立刻升级不再重试」、「选元素是纯等待、接管必须原样穿出、不得吞成模型错误」三条纪律。新引擎的定位规则是编译进二进制的固定选择器串，找不到即终局。**后果直接落在本 change 上**：任务 5.4 要求「非确定性来源得到的新锚点先暂存」，但新引擎没有任何非确定性来源，暂存区会是一个永远空的结构。
- **建议**：这是 5.4 的**前置依赖**，实装 5.4 前必须先裁定——要么本 change 承认 5.4 只建结构不接来源并把这点写进 5.6 的盘点，要么把模型兜底纳入范围（注意 D7：不许复活 TS 定位层，清单抽取与锚点构造须在 Rust/注入侧重建）。其中那份写成自然语言的定位经验（无无障碍属性站点改用语义类名推理、不许凭混淆类名猜）是本仓少见的资产，别丢。

### ⑳ 语义 class 白名单的边界匹配退化为 `[class*="like"]` 子串

- **漏在哪**：旧实现的界是「绝不信任任意 class，只认四个手写语义片段，且用词边界匹配（整 token 或被 `-`/`_` 包裹）」；新引擎按需现场拼 `[class*="…"]`（like / collect / comment / content / preview / desc …），既无白名单闭集，又把 `css-1like3c` 这类噪声一并命中。**与「首个可见即取」叠加会放大**：页面上任何更靠前的含 `like` 类名节点都会被当成点赞控件读计数。本 change 无对应任务。
- **建议**：`xhs-semantic-class.test.ts:80` 那条是纯字符串逻辑、最容易 port，可先落成契约测试再改实现。归属上与缺口 ⑰（匹配唯一性闸）同批处置更省事。

### ㉑ 两个可换接口（DOM 提供者 / 执行器）消失：定位逻辑脱离浏览器单测的能力没了

- **漏在哪**：旧引擎只依赖两个窄接口，真机下 DOM 提供者取整页快照再在 Node 侧解析、单测下直接塞桩，因此 `test/locating/` 下 912 行用例全部不需要起浏览器。新引擎的定位与判据写在注入 JS 里、隐式依赖真实页面全局对象，Rust 侧直接对 CDP 会话发指令。**后果落在本 change 的可验证性上**：任务 1.3 / 1.4 / 1.5 都要求「Rust 假 CDP 测试」，5.1–5.5 的三道闸更需要能脱机跑判据；没有可替换的 DOM 来源与执行层，这些断言只能退化成真机验收。旧执行器还有一条本 change 没覆盖的纪律：执行后页面侧表达式必须返回 true 才算执行成功，未命中即抛。
- **建议**：在 6.1 之前先确认 Rust 侧假 CDP 的能力边界；若不足以支撑 1.3–1.5，应把「建立可替换的 DOM 来源与执行层」提成本 change 的前置任务，而不是把断言降级成真机项。`test/locating/extractor.test.ts` 三条与 `test/cdp/dom-provider.test.ts` 两条是「注入 JS 可脱机测」能否成立的最小验证集。

### ③ 的后半：验证码协助的专用节奏档与每机节奏偏置

- **漏在哪**：任务 2.1 覆盖了「落点停顿」这一样，但验证码协助那一整档专用参数（落点抖动 ±2px、过冲概率 0.22、逐帧中心 11ms 且每帧对数正态、瞄准停顿中位 650ms、点间停顿中位 950ms）以及**按边缘机器标识派生 [-0.15,0.15) 偏置**这件事，本 change 一条没提。后者的意义不是拟人而是**反车队指纹**：同一版二进制若在全车队产出同一节奏形状，节奏本身就是车队级标识。Rust 引擎目前连边缘标识入参都没有。
- **建议**：与缺口 ④ 同批处置（两者共用验证码协助这条路径）。「引擎接受边缘标识并据此派生节奏偏置」是一条独立且便宜的要求，可在 2.1 里顺手加一个入参位（默认无偏置＝行为等价），把改口的成本先付掉。

### 已具名不做、**不属**覆盖漏洞的条目（列此以免被重复当成漏洞）

- **⑰ 匹配唯一性闸（置信度 0.6 / 分差 0.15 / 权重表 1-2-1-5）**：任务 5.8 已把「可见性 / 几何 / 歧义拒绝」显式划给各平台目标解析能力，本 change 只承接三道闸。**但 5.8 的要求是「把边界记下来、不得被当成已覆盖」**——实装时必须真的写下这一条，并把旧注释那条算式约束（`5/(1+2+5)=0.625`，让语义类名单独越过 0.6 阈值）带给承接方，否则它会随退役代码一起消失。
- **最小间隔 gating 与反射采样兜底（缺口 ⑩ 的一部分）**：任务 4.7 已明文登记为残留缺口。反射采样那条的理由（硬裁会在直方图 floor 处堆出一根竖直左壁尖峰、本身可被行为分析识别）必须一并带走，否则后继者会以为它只是个采样细节。

