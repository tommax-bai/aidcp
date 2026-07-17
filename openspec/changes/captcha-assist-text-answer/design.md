## Context

远程协助链现役形态（`archive/2026-07-10-remote-captcha-assist` 起，经 `humanize-click` / `live-snapshot` / `trajectory-replay` 三次增强）：边缘检出阻断 → 云端建 incident + 发飞书卡 + 暂停该 edge 下发 → 运营开协助页 → 边缘有界实时抓帧回传 → 运营在截图上标 ≤2 个点（并被采集真实鼠标轨迹）→ 云端下发 `captcha.assist.click` → 边缘回放前强制 stale 复检 → 拟人回放 → settle → fresh 复检 → `cleared` / `still_blocked`。

**整条链只有鼠标。** 用户报障形态已确认为**模糊数字图片类字符识别码**（人工识别 + 键入数字），且是**在协助页上看见的** ⇒ 该类已能被检出（靠遮罩形状或厂商域名，不靠文案词表——词表 13 条全是滑块 / 点选、零条输入类），检测不是本 change 的准入前置。

**约束（全部已在代码中坐实）：**
- `captcha.assist.*` 是验证码暂停期间**唯一允许穿透传输层暂停**的下行通道（`ws-server.ts:217-225`）。往这条通道里加"键入任意字符 + 回车"，条目数不变、**语义边界变了**——必须自己补回收窄。
- 现有逐字输入函数 `dispatchKeystrokes`（`cdp-util.ts:321/334`）内部是逐字符 `Input.insertText`：**零 keydown/keypress/keyup**。且它是 FB 发帖 / XHS 搜索 / FB 评论的热点依赖，改它 = 改它们。
- 边缘主动命令白名单（`edge-client.ts:679`）与云端暂停穿透白名单（`ws-server.ts:224-225`）都是**逐条硬编码消息类型**、typecheck 抓不到遗漏。
- 协助页在 console 登录门**之外**（`App.tsx:22`，与 `/login` 并列），凭证是 URL 上的 incident 级 scoped token。
- 飞书群路由**无内外部标记**，`chat-target.ts:95-101` 自陈「谁看得见卡＝谁能批准…映射外部客户群 = 把批准按钮交给客户，系统内无闸可拦」。
- 「远程桌面」按钮背后无任何能力（见 proposal），**不能作为任何 Non-Goal 的推诿理由**。

## Goals / Non-Goals

**Goals:**
- 运营能在协助页对模糊数字图片类验证码键入答案并提交，全程拟人、绝不静默假成功。
- 键入失败时运营 MUST 能区分「答案打错了」与「字根本没打进去」。
- 不扩大暂停穿透通道的**语义**边界（条目数本就不变）。
- 键入这个更强的动词收到显式身份闸后面。
- 修掉点击链路 4 个既存诚实缺陷（它们在键入窗口下会变常发）。
- 移除背后无能力的「远程桌面」入口，连同其 spec 条款。

**Non-Goals:**
- **答案不在屏幕上的挑战**（短信码 / TOTP / 邮箱码 / FB checkpoint）：缺的是**码的来源信道**与 30–60s 时效窗，不是输入通道。加输入框对它们零帮助。
- **中文 / IME**：charset 白名单直接拒。非 ASCII 会强制回退到文本插入 = 零键事件 = 最坏检测面。
- **滑块 / 旋转 / 拖拽**：`spec.md:274` 已定案驳回，理由是无拖拽原语 + 把流畅滑块动画推给运营会诱发非人类瞬移落点。本 change 不动该结论。
- **音频挑战**（reCAPTCHA 无障碍）：需回传音频流给运营听，是另一条媒体链。
- **OCR / 自动识别 / 打码平台**：`archive/2026-07-10-remote-captcha-assist/design.md` 已定案。人工识别是本能力的前提，不是缺陷。
- **运营真实击键时序采集**：seam 已在协议里钉好形状，照 `humanize-click → trajectory-replay` 的分期先例后置。
- **VNC / 整页接管**：可交互即暴露整页而非验证码框，与「暂停期唯一穿透通道」的收窄取向相反。

> **注**：以上 Non-Goals **MUST NOT** 被表述为「已有远程桌面兜底所以不做」——该兜底不存在，且本 change 正在移除它的入口。它们各自的理由是自洽的（来源信道 / 检测面 / 无原语 / 另一条链 / 已定案 / 取向冲突），不依赖任何后路。

## Decisions

### D1. 扩既有 `click` 载荷，不新增 MessageType，不建 actions DSL

**选择**：`CaptchaAssistClickPayload += text?: string` / `submit?: 'enter'`。

**否决 A（新增 `captcha.assist.input` 消息类型）**：要动边缘主动命令白名单 + 云端暂停穿透白名单**两处 typecheck 抓不到的硬编码列表** + `docs/protocol.md` 计数与表。收益仅是"语义更干净"。`trajectory-replay` 已立先例：additive optional 扩展，白名单不动。

**否决 B（actions DSL：`actions: (Click|Type|Key|Clear)[]`）**：v1 的校验器只接受 `click{1,2} clear? type? key?` —— 与两个 flat 字段**逐字等价**，交付**零能力增量**。评委票面 2:1 支持 DSL，但拆开看无一票为容器本身投（两票的理由是可嫁接的观点与常量）。其红利论证（"未来支持滑块"）站不住：`spec.md:274` 驳回滑块的原文理由是**无拖拽原语**，容器一条都不解。且 `points` ↔ `actions` 双表示 day-1 就是重复编码。**DSL 降级为 `protocol.ts` 里一行 seam 注释**：未来若真出现多字段表单，把 `text`/`submit` 升格为 `actions[]`、`points` 退化为派生的 click 子序列。

**代价（必须补偿）**：`Record<MessageType,true>` 穷举守卫只护消息类型、**不护字段**。⇒ 补 AC-PROTO-07（两份 `protocol.ts` 对两个 payload 的逐字段往返断言，继 `WelcomePayload.pacing` 之后第二例）+ panel HTTP 边界透传断言（`panel-server.ts:281` 从 `unknown` 手写解构，漏字段 = 静默丢弃 + typecheck 全绿）。这两条**缺一即裸奔**。

### D2. 新建 captcha 专用键盘原语，MUST NOT 复用 `dispatchKeystrokes`

**理由**：`dispatchKeystrokes` 内部逐字符 `Input.insertText` ⇒ **零 keydown/keypress/keyup**。「键事件数与字符数不匹配」是厂商成熟判据，验证码正是其主战场——用它等于在最敏感的现场自曝。且它是四处热点依赖，改它的行为 = 改 FB 发帖 / XHS 搜索 / FB 评论。

**新建 `captcha-type.ts`**：ASCII 键位表（0-9 / a-z / A-Z / 空格 / 常见标点 → key/code/vk/needsShift，**表外字符诚实拒绝**）；`dispatchTypedChar` 真 keyDown(text) + dwell + keyUp，需 Shift 的用真实 Shift keyDown/keyUp 包裹，try/finally 保证 keyUp 与 Shift-up 必发（照抄 `commitLeftClick` 已定案形状，**无 options 参数 ⇒ 词法上插不进取消点**）；`dispatchHumanTyping` 复用 `humanize/keyboard-rhythm.ts` 的 lognormal（median 110 / σ0.35 / 8% 长停顿 / clamp[40,400]）取 flight，dwell 另采样 lognormal(median 75, σ0.3) clamp[30,180]。

**RTT 补偿**：测量上次 CDP 往返、从下次 sleep 减掉。不补则 RTT 严格叠加、右移分布——重载 AdsPower 下键间隔趋近 RTT 地板 = **花钱买的 lognormal 被传输层抹平成常数**。`medianMs` 按 edgeId 派生偏置（`spec.md:374` 已把每机偏置写成 MUST，此处对齐到键盘侧）。

### D3. 焦点三态，`opaque` 打但不 fail-closed

`activeElement` 只读探针 → `editable`（INPUT 非 disabled/readOnly / TEXTAREA / contentEditable：可清、可读、证据最强）/ `opaque`（**其余任何持有焦点的元素**：iframe / shadow host / canvas / tabindex 容器）/ `none`（null / body / documentElement）。

- `none` = **唯一结构确定的失败** ⇒ `no_target` / `focus_not_landed`，零字符派发，**MUST NOT 提交**（提交空答案 = 白烧一次挑战次数 + 把 incident 推向 still_blocked 假象）。
- `opaque` ⇒ **打，但报 `unverifiable`**，不拒绝。

**否决「非 editable 即 fail-closed」**：其论据「div 没 tabindex 就不会拿焦点」在本任务点名的场景（焦点被 canvas 抢走）下失效——厂商挂 tabindex 的 canvas / 容器会真拿焦点。代价不对称：拒绝 = **确定的死路**（无远程桌面后路）；打进去 = 字符落在一个**复检刚证明仍被遮罩挡住**的页面上，而遮罩的职能就是吃输入。v1 因此**不拆 iframe / opaque**（同一个决策：打、但验不了），只报 `focusTag` 供事后取证、**不据此分支**。

### D4. 提交只走 Enter，带 text 时 points 必须恰好 1 个

**理由（无人提过的失效路径）**：聚焦输入框会**滚动页面** ⇒ 第 2 个"提交按钮"落点在序列内失效（它标定于滚动前的像素），而 `sameLocation` 只比 origin+pathname、检测不到。Enter 跟随焦点、免疫滚动。顺带消掉双提交路的疣。

### D5. 顺序 MUST：type → read → submit

反了则 Enter 已清空框 / 换了页，回读必假阴性 ⇒ **把成功报成失败**（与假成功对称的另一种不诚实）。回读 MUST 读全文 + 查 extra——前 N 字探针是已上膛的雷（`publish-command-handlers.ts:728-731` 列过两个致命面：残文+新文拼接照样放行、被吞 90% 也判成功）。

### D6. 清空前置强制，不做开关

三家设计都把它做成可选，理由「盲发全选会选中整页」**是无效的**：select-all 跟随焦点，而焦点闸已经先跑过了；Backspace 导航返回自 Chrome 52 起已不存在。**不清空 = 重试时残文拼接 = 在一个 `restricted` 账号上无界烧挑战次数。** `editable` → JS select + Backspace + 回读 ⇒ `verified`；`opaque` → 键盘 select-all（darwin Meta / 其余 Ctrl，**修饰键只活在这个原语内部、绝不进运营的动作词汇**）+ Backspace ⇒ `attempted`（**绝不声称清空了**）。

### D7. 序列中途复检 ×2

打字前、Enter 前各重跑一次 fresh 阻断复检 + 位置比对。**真实机制是焦点丢失（静默空打）而非焦点转移（误发）**：遮罩消失时被聚焦的 input 随之出 DOM、`activeElement` 退回 body。爆炸半径 = 遮罩确实还在的那个窗口。这条同时是「键入没有扩大穿透通道语义」那个论证的**唯一支柱**——没有它，那个论证是空的。

### D8. 跨版本 fail-closed，能力位收进 `EdgeClient` 构造函数

老边缘会**忽略未知字段、只点 points、照常回 cleared/still_blocked** = 教科书级静默假成功，且两份 `protocol.ts` 一致性与 typecheck 都抓不到。⇒ 边缘声明构建能力 `captcha_assist_text_v1`，云端 live 查当前连接（不用 `onDetected` 快照——incident 可能比连接活得久），未声明即 409。

**构建位 MUST NOT 进 driver 常量**：`edgeCapabilities` 是三个 driver 的静态常量、两条装配路径（`main.ts:351` + `wechat-channels/runtime.ts:133`），漏一个 driver = 该平台永久 409 且与"客户端太老"在运营视角**不可区分**。构建能力 ≠ 平台能力，混进去是类别错误。收进 `EdgeClient` 构造函数内部 ⇒ 两条装配路径都拿不掉、新增平台不可能漏。

**第二道（检测而非预防）**：`lastDispatch.textLen > 0 && 回执 inputMode !== 'click_type'` ⇒ 标 `text_not_executed`。闸做预防，检测抓「闸自己错了」。

### D9. 授权面不变：键入与点击共用同一条授权路径，**不新增身份闸**

含 `text` 的提交与纯点击**走完全相同的授权**（incident 级 scoped token）。协助页从飞书卡点开即可键入。

**否决「键入需 console 登录身份」**（该方案曾被采纳，2026-07-17 用户纠正后推翻）。当初的论证是「群路由无内外部标记 ⇒ 卡的可见范围不是授权范围；把点 2 个像素升级成往生产浏览器打任意 ASCII + 回车需要显式身份闸」。**两处都站不住：**

1. **「升级」是修辞夸大**。点击已经能点页面上**任意坐标**；键入受的约束**严格更紧**——只能进已聚焦的那个元素（焦点由一次已授权的点击建立）、仅 ASCII 可见字符 `0x20`–`0x7E`、长度 ≤24、无修饰键暴露、无功能键（Enter 除外）⇒ **结构上**不能触发浏览器快捷键 / 开发者工具 / 导航（D2 的字符集边界），且只在「遮罩确认仍在」的窗口内成立（D7）。相对既有点击面，键入的**边际暴露面接近零**。
2. **它掐掉的正是这条链的设计意图**。协助页刻意放在 console 登录门**之外**（`App.tsx:22`，与 `/login` 并列），凭证是 URL 上的 scoped token —— 就是为了让运营收到飞书卡、**在手机上点开就能处置**。要求先登录控制台会让「收到卡 → 立刻解决」变成「收到卡 → 找电脑 → 登录 → 处置」，而验证码是**有时效的现场**。远程桌面已确认不存在（D13）⇒ 这条链是唯一的远程处置路径，掐它没有退路。

**「卡的可见范围 = 操作范围」这一暴露面是既有性质，不由本 change 引入**：它今天就完整适用于协助点击（以及其它审批卡）。本 change **不扩大它、也不假装解决它**，如实记入 Risks 并指向其真正的归属（路由层的内外部标记，独立问题）。

**推论**：console 侧无需登录态感知、无需挂 Bearer、输入框无需按 token 有无 disable。少一堆状态。

### D10. 答案明水数据分类

现有 spec `:262` 只禁「答案**推断**」入日志；运营键入的是**答案本身**，是本能力独有的新敏感类别。MUST NOT 落日志 / 落库 / 进 incident / 进 lastResult / 进 lastDispatch / 进 URL / 进 localStorage / 进飞书卡。审计只留 **actor + 时刻 + charCount**（who / when / how-many，**never what**）。incident 全在进程内 Map、无持久化 ⇒ 天然不落库，但必须成文——一次 `logger.info(payload)` 就全泄。

`text` 只活在 `submitClick` 的调用栈，构造 envelope 即发走。

**与 trajectory 的策略刻意相反**：trajectory 畸形 → 丢弃装饰、保留 points 继续；**text 畸形 → 整单拒绝**。「悄悄丢掉你的打字、只帮你点了一下」正是红线要禁的形态。此对照 MUST 写进代码注释。

### D11. task 0：既存诚实缺陷先修（准入，非附加）

这 4 条今天点击路径就有；键入把它们从潜伏变成常发，故必须先合并、先验证：

1. `handleCapture` 缺互斥闸 + `!kind` 分支**单次 probe 即 `sendRiskCleared()`**（`:165-177`）绕过 K=3。且 `noteViewerPresence` 会自动 re-arm capture，**live 关着时运营手点「刷新」照样触发**。⇒ 删该 `sendRiskCleared`，只留 `not_blocked` 回执（cloud 已把 `not_blocked` → cleared，面板照常更新）。`risk.captcha_cleared` 所有权收归 `liveTick` 的 K=3 与 overlay 监测体独占——**这正是 `spec.md:226` 已成文的 MUST，`handleCapture` 是它唯一的漏网之鱼**。
2. Enter 提交导航 → `probeBlockingKind()` 抛 → **一次成功被报成 `failed`**，且 `sendRiskCleared()` 永不执行。文本验证码成功的正常形态就是 POST / 导航；点击类走 XHR 所以从没炸。⇒ 有界重试（4 次 / 500ms，迭代限界）+ 新 reason `verdict_unavailable_after_submit`（**不是** `click_failed`）。
3. `sendRiskCleared` 排在 `sendClickResult` 之后 + `client.send` 断连即抛 ⇒ 承重的那条（解生产账号暂停）被装饰性的那条挡住。⇒ 排序前置 + 各自 try/catch。
4. `clicking` → `writing` 改名：`clicking` 是 v1 的名字，留着它，后来者必然新开一个 `typing` 集合再把洞开一次。

### D12. 租约：checkpoint + 中途 re-touch，不进 commit window

租约只在受理时查一次（`main.ts:813-826`）、无 checkpoint。**但 `strictlyOutranks` 用 `>`（`edge-task-coordinator.ts:220-222`）⇒ captcha 独占 system_recovery 顶档、不会被抢占——暴露面是 expiry 不是 preemption**（三份设计的抢占分析全瞄错了）。⇒ 采 checkpoint + 序列中途 re-touch；**不采 commit window 登记**（只为一个不会发生的抢占付复杂度）。

**预算算术**：24 字 × (110ms flight + 75ms dwell + ~60ms RTT) ≈ 5s，含 8% 长停顿 ≈ 6s；+ 3 次复检 ≈ 0.1s + settle 1.5s ≈ **8s**。`deadlineAt = now + 20s` 硬顶，远在 45s acquire / 60s 兜底之内。**不新增可配项。**

### D13. 移除「远程桌面」入口

`AIDCP_REMOTE_ADDR` 是边缘自陈的**自由文本**，console 直接当 `href`、飞书卡当文字打。系统自身零远程桌面能力；真机验收自 2026-06-21 DEFERRED 至今、从未填过。⇒ 删 console 按钮 + 飞书卡「远程地址」行 + edge 两处 env 读取 + 两份 `protocol.ts` 的 `EdgeHelloPayload.remoteAddr` + 云端 session / incident / panel types 连带字段。**无消费方，风险为零。** spec `:170`「保留远程桌面处置文案」的前提已不存在，一并改。

**不做**：接通真远程桌面。那要先决定运营机上用什么第三方工具（ToDesk / 向日葵 / RDP / VNC），是采购与运维决策、不是代码。留白比留一个假入口诚实。

### D14. console 顺手建 `lastResult.status` 的 Record 穷举表

现有两张 Record 表是 **incident 八态**；`click_result` 的 status 在 console 是**裸打英文枚举、无表**。⇒ 加 status 值**不会**自动报错（"免费机械同步"是事实错误），新增的 `no_target` 本来就会从这个洞溜走。建表才有守卫。同时把 `typeReport` 渲染成三句人话（**整个 change 的用户价值兑现点**）：「字打进去了，但答案不对」/「焦点在不可读元素内，无法证明字符已落入，请对照新画面确认」/「那一点没点到输入框」。

## Risks / Trade-offs

- **[卡的可见范围 = 操作范围]** 协助页在 console 登录门外、凭 URL scoped token 授权；飞书群路由无内外部标记（`chat-target.ts:95-101` 自陈「系统内无闸可拦」），卡若被路由到外部客户群，看得见的人就能操作。 → **Mitigation**：**无**。这是**既有性质**，今天就完整适用于协助点击与其它审批卡，**不由本 change 引入、也不被本 change 扩大**（D9：键入的边际暴露面接近零）。真正的归属是路由层的内外部标记，属独立问题。**登记，不在本 change 内解决。**
- **[焦点假阳性]** `activeElement` 可编辑但不是验证码框（FB 群参与审批答题框是已发生过的真机原型，`comment-executor.ts:636-641`）→ 报 `editable`、照打。机械上发现不了。 → **Mitigation**：D7 复检保证 kind/URL 未变且遮罩仍在 + crop 是遮罩 rect 外扩 24px + `focusTag` 供事后取证。**既有点击链就有这个性质，键入不放大它，但后果更重** ⇒ 列真机验收项。
- **[合成击键节奏可被指纹]** GeeTest 自述持续采集 keystroke timings；lognormal + 每机偏置 + RTT 补偿做不到 OS 级不可分辨。 → **Mitigation**：无法根除，明知的残余风险。seam 已钉好「采集运营真实击键时序」的形状，作为后续分期（照 `humanize-click → trajectory-replay` 先例）。
- **[cleared 断连不可达（H3 的第二半）]** `overlay-report-gate:56-59` 无论 send 成没成都 `reportedKind = null`、消费掉唯一的 cleared ⇒ 断连时解决掉的验证码永不到云端、账号一直暗着。 → **Mitigation**：本 change 只修排序（零成本），**不修记账**——那要改 gate 的「已投递 vs 已尝试」语义，是既存 bug 的独立 change。**登记 backlog。**
- **[incident TTL 30min 只在 `onDetected` 刷新]**、无续期入口。键入窗口比点击长 ⇒ 边际更紧但未越界。 → 正交既存问题，**登记**。
- **[帧环 / 近期集算术]** 边缘环 8 帧、云端近期集 5 —— 实时抓帧下运营在稍旧帧上打字期间可能被淘汰。 → **Mitigation**：先探 dev/ol 的 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED`（**实测默认关**，`server.ts:1752` `=== 'true'` 才开）⇒ 引信可能没点着。**开着才把 8→16 / 5→12 提成独立 bugfix change**（它对纯点击同样有价值），不捆进本 change、也不拿它论证选型。
- **[console 三处手抄 union 不在 `/api/version` 指纹对拍内]**（`aidcp-enums.ts:9-42` 只护 8 组）：cloud 改了 console 零提示。 → 本 change 只补回「api.ts 有、页面没加」这一个方向（D14 的 Record 表），另一半仍全静默。**登记。**
- **[能力闸 fail-closed ⇒ 合并后到装包前该能力一直是暗的]** 运营机未换装即 409。 → **Mitigation**：409 文案必须是人话（「该机器客户端版本过旧，不支持远程输入」），不是裸打英文 reason。交付需一次 edge 出包 + 逐台换装，列入真机验收前置。
- **[trade-off：拒绝 opaque vs 打 opaque]** 选了"打"（D3）。若真机显示 opaque 场景下的键入大量落空且不可验证，需回头重估——但回不到"拒绝"（无后路），只能是拆 iframe。
- **[trade-off：走扩载荷而非新消息类型]** 换来白名单三处不动，代价是字段级漂移无机械守卫。 → 由 AC-PROTO-07 + HTTP 边界断言补偿；且把 AC-PROTO-07 写成**可被后续所有「扩载荷」路线照抄的模板**，把一次性成本变成资产。

## Migration Plan

1. **task 0 先行**（4 个既存诚实缺陷）：可独立合并、独立验证，对纯点击链路即刻有正收益。
2. 键入路径（edge → cloud → console）按 tasks 顺序落地；能力闸 fail-closed ⇒ 未换装的运营机保持今天的行为（只点击），**零回归**。
3. dev 部署 cloud + console。
4. edge 出包 + 逐台运营机换装 → 真机验收（新簇）。
5. **回滚**：能力位是构建期常量 ⇒ 回滚 = 装回旧包，云端自动 409 退回纯点击。云端侧无 env 开关（**不新增可配项**）；如需紧急关停，回滚 cloud 到本 change 之前即可（协议字段 additive optional，旧云端不发 text、新边缘照常只点击）。

## Open Questions

1. **`no_target` 加进 `click_result` 的 status 联合**——判断值得（红线词汇，且 `invalid_target` 现语义是坐标越界、混用运营看不懂）。代价是 console 手抄镜像 +1 值。若倾向零枚举增量，可退回 `invalid_target` + reason 消歧，但那会让运营在「点空了」与「坐标越界」之间看到同一个词。**默认按加。**
2. **dev/ol 的 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED` 实际是否开着**——决定帧环算术是否需要提独立 bugfix change。实装前探一次即可，不阻塞。
3. **classifier 词表是否需要扩**——用户报障的模糊数字图片类已能被检出（在协助页上看见的），故非准入。但若后续发现同类站点漏检，扩词表 MUST 用**真实文案**（`join-executor.ts:243/484` 的裸词「退出」误命中输入法「退出联想输入」已付过一次代价），不能凭猜。
