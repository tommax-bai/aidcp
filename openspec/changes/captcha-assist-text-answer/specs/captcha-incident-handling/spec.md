## ADDED Requirements

### Requirement: 协助键入必须在焦点落定后才派发字符

edge 收到含 `text` 的协助命令时，SHALL 在派发第一个字符前探测 `document.activeElement` 并分级为 `editable`（`INPUT` 非 disabled/readOnly / `TEXTAREA` / `isContentEditable`）、`opaque`（其余任何持有焦点的元素，含 iframe / shadow host / canvas / tabindex 容器）、`none`（null / `body` / `documentElement`）。

`none` 是**唯一结构确定的失败**：edge MUST 回 `status:'no_target'`、`reason:'focus_not_landed'`，MUST 派发 **0 个字符**，MUST NOT 执行提交键。这是「找不到目标报 `no_target` 而非 `ok`」在本能力上的落点——提交空答案会白烧一次挑战次数并把 incident 推向 `still_blocked` 假象。

`opaque` MUST NOT 被 fail-closed 拒绝：edge SHALL 照常键入，但 MUST 在回执中标注不可验证（见「协助键入的证据必须分级诚实」）。焦点探针自身抛错 MUST fail-closed 回 `failed` / `focus_probe_failed:<msg>`，MUST NOT 盲打。

#### Scenario: 落点没点中输入框
- **WHEN** 运营提交 `text` 且聚焦点击后 `activeElement` 为 `body`
- **THEN** edge 回 `no_target` / `focus_not_landed`，`typeReport.typed === 0`，MUST NOT 派发提交键，MUST NOT 报 `still_blocked` 或 `failed`

#### Scenario: 焦点落在跨源 iframe 或 canvas 上
- **WHEN** 聚焦后 `activeElement` 是 `IFRAME` / `CANVAS` / 带 tabindex 的容器
- **THEN** edge 判 `opaque` 并照常键入，回执标 `focus:'opaque'` 与 `verified:'unverifiable'`，MUST NOT 因不可读而拒绝键入

#### Scenario: 焦点探针抛错
- **WHEN** 焦点探针执行失败
- **THEN** edge 回 `failed` / `focus_probe_failed:<msg>`，MUST NOT 派发任何字符

### Requirement: 协助键入必须产生与字符数一一对应的真实键事件

edge 键入验证码答案 SHALL 为每个字符派发完整的 `keyDown`（携带 `text` / `unmodifiedText`）+ `keyUp` 事件对；需 Shift 的字符 MUST 由真实 Shift `keyDown`/`keyUp` 包裹。

edge MUST NOT 用 `el.value=` 直写 DOM 替代用户输入（`不得用 DOM 状态篡改替代用户输入` 在键入侧的具体化）。edge MUST NOT 用 `Input.insertText` 键入验证码答案——它产生 **0 个 keydown/keypress/keyup**，而「键事件数与字符数不匹配」是验证码厂商的成熟判据。本条**明确禁止复用现役的逐字符输入辅助**（其内部实现即为逐字符 `Input.insertText`，且为发帖 / 搜索 / 评论多处热点依赖）；协助键入 MUST 使用独立的 captcha 键盘原语。

字符集 MUST 限定为 ASCII 可见字符（`0x20`–`0x7E`）、长度 1–24。这是**结构性的权限边界**而非约定：无修饰键暴露、无功能键（`submit:'enter'` 除外）⇒ 键入序列在结构上不能触发浏览器快捷键、开发者工具或导航。表外字符 MUST 在注入前被拒绝。

#### Scenario: 键事件数与字符数自洽
- **WHEN** edge 键入 4 个字符的答案
- **THEN** 恰好派发 4 对 `keyDown`/`keyUp`，且 `Input.insertText` 的调用次数为 **0**

#### Scenario: 表外字符前置拒绝
- **WHEN** 云端或 edge 收到含中文、控制字符或长度 > 24 的 `text`
- **THEN** MUST 在任何注入动作之前拒绝整单，MUST NOT 只执行点击而静默丢弃 `text`

### Requirement: 协助键入的节奏必须拟人且不被传输层压平

协助键入的每字符按键间隔 SHALL 服从对数正态分布（复用现役键盘节奏模型：中位 ~110ms、偶发想词长停顿、间隔绝不均匀），按键按下时长（dwell）SHALL 独立采样且非零。中心值 MUST 按 `edgeId` 派生每机偏置，与鼠标侧已有的每机偏置要求对齐——避免全 fleet 逐字相同的节奏自成车队指纹。

edge MUST 补偿 CDP 往返时延（从下一次采样延迟中扣除实测 RTT）。不补偿则 RTT 严格叠加、分布右移，重载环境下按键间隔趋近 RTT 地板 —— **采样得到的对数正态会被传输层抹平成常数**，拟人化在最敏感的现场失效。

#### Scenario: 键入节奏保留方差
- **WHEN** 在注入了合成 RTT 的环境下键入答案
- **THEN** 实测按键间隔的变异系数 MUST 保留（MUST NOT 只断言字符数正确——那在节奏被压平时照样通过）

### Requirement: 协助键入前必须强制清空目标字段

edge SHALL 在键入前清空已聚焦的字段，清空 MUST NOT 是可选项。不清空则重试时残文与新答案拼接，会在一个已 `restricted` 的账号上无界消耗挑战次数。

`editable` 焦点 SHALL 用选中 + 删除并**回读确认为空**，回执标 `cleared:'verified'`；`opaque` 焦点 SHALL 用键盘全选 + 删除，回执标 `cleared:'attempted'`，MUST NOT 声称已清空。全选所需的修饰键 MUST 只存在于该原语内部，MUST NOT 进入运营可表达的动作词汇。

#### Scenario: 可读字段清空并确认
- **WHEN** 焦点为 `editable` 且字段内有残留文本
- **THEN** edge 清空后回读确认为空，回执标 `cleared:'verified'`

#### Scenario: 不可读字段只能尽力清空
- **WHEN** 焦点为 `opaque`
- **THEN** edge 尽力清空并标 `cleared:'attempted'`，MUST NOT 标 `verified`

### Requirement: 协助键入的证据必须分级诚实

edge 回执 SHALL 携带 `typeReport`：焦点分级、焦点元素 tag（供事后取证，MUST NOT 据此分支）、清空三态、**实际派发字符数**、回读三态（`match` / `mismatch` / `unverifiable`）、是否已提交。

`typed` MUST 是实际派发的字符数，MUST NOT 用 `typed || text.length` 之类回退到意图值。被抢占或超预算中断时，edge MUST 尽力清场、如实回报 `typed`、MUST NOT 执行提交。

运营 MUST 能从回执区分「答案打错了」（`verified:'match'` + `still_blocked`）与「字根本没打进去」（`focus:'none'` 或 `verified:'unverifiable'`）。把不可验证抹平成成功，与静默假成功同罪。

#### Scenario: 打进去了但答案不对
- **WHEN** `editable` 焦点、回读与答案一致、提交后仍被阻断
- **THEN** 回执为 `still_blocked` + `verified:'match'`，协助页展示「字打进去了，但答案不对」

#### Scenario: 不可验证不得报成成功
- **WHEN** `opaque` 焦点、提交后仍被阻断
- **THEN** 回执为 `still_blocked` + `verified:'unverifiable'`，MUST NOT 声称字符已落入

#### Scenario: 中断时如实回报已派发数
- **WHEN** 键入进行到第 3 个字符时租约被夺或超出预算
- **THEN** 回执 `typed === 3`、尽力清场、MUST NOT 执行提交、MUST NOT 报 `cleared`

### Requirement: 协助键入的动作顺序必须是 键入 → 回读 → 提交

edge SHALL 严格按「键入 → 回读校验 → 提交键」顺序执行。回读 MUST 在提交之前——提交后字段可能已被清空或页面已导航，此时回读必然假阴性，**会把一次成功报成失败**（与假成功对称的另一种不诚实）。

回读 MUST 读取字段全文并检查多余内容，MUST NOT 只比对前 N 个字符——前缀探针无法区分「残文 + 新文拼接」与「正确输入」，也无法发现输入被目标吞掉大部分的情况。

#### Scenario: 回读先于提交
- **WHEN** edge 键入答案并需要提交
- **THEN** edge MUST 先回读校验再派发提交键，MUST NOT 提交后再读

### Requirement: 序列中途阻断消失后必须停止注入

协助命令的每个**非首次点击**动作（清空 / 键入 / 提交键）派发前，edge SHALL 重跑 fresh 阻断复检与位置比对。遮罩已不在时 edge MUST 立即停手、MUST NOT 继续注入，并走既有 settle + fresh 判据回 `cleared` / `cleared_mid_sequence`；阻断类型或位置已变时 MUST 回 `stale_snapshot` / `page_moved_mid_sequence` 并重抓帧供运营在新帧上重标。

本条是「暂停期只允许 captcha assist 恢复命令穿透」这一收窄在键入侧的延续：穿透白名单的**条目数**不因键入能力而变，但键入是比点击更强的动词，其语义边界必须由本条自行收回——注入只在「遮罩确实还在」的窗口内成立。

#### Scenario: 打字前遮罩已自行消失
- **WHEN** 聚焦点击后、键入首字符前的复检显示已无阻断遮罩
- **THEN** edge MUST 派发 **0 个字符**、MUST NOT 提交，回 `cleared` / `cleared_mid_sequence`

#### Scenario: 提交前页面已换
- **WHEN** 键入完成后、提交键派发前的复检显示阻断类型或位置已变
- **THEN** edge MUST NOT 提交，回 `stale_snapshot` / `page_moved_mid_sequence` 并重抓帧

### Requirement: 提交后判据不可得不得报成失败

edge 派发提交键后 SHALL 用**有界重试**重新探测阻断态。文本类验证码提交成功的正常形态就是表单 POST 或页面导航，此时阻断探针会抛错——把它当失败会**将一次成功报成 `failed`**（点击类挑战走 XHR，故此路径历史上从未暴露）。

有界重试后判据仍不可得时，edge MUST 回 `failed` / `verdict_unavailable_after_submit` 且 `typeReport.submitted === true`，MUST NOT 复用 `click_failed` 之类会被误读为「注入本身失败」的原因码，并 SHALL 尽力回带一帧新截图。

#### Scenario: Enter 提交触发导航
- **WHEN** edge 派发 Enter 后阻断探针连续抛错至重试上限
- **THEN** edge 回 `verdict_unavailable_after_submit` + `submitted:true`，MUST NOT 回 `click_failed`

### Requirement: 验证码答案明文是独立敏感类别

运营键入的验证码答案 MUST NOT 被写入普通日志、数据库、incident 对象、回执载荷、URL、浏览器本地存储或 Feishu 卡片。既有审计条款只禁止「验证码答案**推断**」入日志；运营键入的是**答案本身**，是本能力引入的新敏感类别，必须独立成文。

协助键入的审计 SHALL 只记录**操作者来源、时刻、字符数**（who / when / how-many），MUST NOT 记录内容（what）。答案 MUST 只存活于下发调用栈，构造命令后即发走。

`text` 畸形时 MUST **整单拒绝**，MUST NOT 沿用鼠标轨迹的「丢弃装饰、保留点位继续」策略——「悄悄丢掉你的打字、只帮你点了一下」正是静默假成功要禁止的形态。

#### Scenario: 审计不含答案
- **WHEN** 运营提交一次含答案的协助键入
- **THEN** 审计记录含 actor / 时刻 / 字符数与结果状态，MUST NOT 含答案明文

#### Scenario: 畸形答案整单拒绝
- **WHEN** 云端收到超长或含表外字符的 `text`
- **THEN** MUST 拒绝整个提交，MUST NOT 降级为「只执行点击」

### Requirement: 协助键入与协助点击共用同一授权面

含 `text` 的协助提交 SHALL 与纯点击走**完全相同**的授权路径（incident 级 scoped token）。系统 MUST NOT 为键入新增身份闸——协助页刻意置于控制台登录门之外、凭 URL 上的 scoped token 授权，正是为了让运营收到 Feishu 卡后能立即处置；验证码是有时效的现场，且远程桌面处置通道并不存在（见 REMOVED «远程桌面处置文案»），本链是唯一的远程处置路径。

键入相对既有点击面的**边际暴露接近零**：点击已可作用于页面任意坐标，而键入只能进入已聚焦元素（焦点由一次已授权的点击建立）、字符集与长度受限、无修饰键与功能键、且只在阻断遮罩确认仍在的窗口内成立。

「卡的可见范围即操作范围」是本链的**既有性质**（Feishu 群路由无内部 / 外部标记），MUST 如实记录为已知暴露面，MUST NOT 被表述为已由本能力解决；它的归属是路由层的内外部标记，不在本能力范围内。

#### Scenario: Feishu 链接可直接键入
- **WHEN** 持 incident 级 scoped token 的请求提交含 `text` 的协助命令
- **THEN** cloud MUST 照常校验并下发，MUST NOT 因缺少控制台登录身份而拒绝

#### Scenario: 点击流零回归
- **WHEN** 持 incident 级 scoped token 的请求提交纯点击（无 `text`）
- **THEN** cloud MUST 照常放行，行为与本 change 之前逐字节一致

### Requirement: 边缘未声明键入能力时必须 fail-closed

cloud SHALL 在下发含 `text` 的协助命令前，查询该 edge **当前连接**声明的构建能力；未声明键入能力时 MUST 拒绝并回可辨识原因（如 `edge_lacks_text_capability`），MUST NOT 下发。

理由：旧边缘会**忽略未知字段、只执行点击、照常回 `cleared` / `still_blocked`** —— 教科书级静默假成功，且两份 `protocol.ts` 的一致性守卫与 `typecheck` 都抓不到。能力查询 MUST 基于当前连接而非 incident 创建时的快照（incident 可能比连接活得久）；无法确定时 MUST fail-closed，且原因 MUST 能区分「在线但未声明」与「连接状态未知」。

键入能力位是**构建能力**而非平台能力，MUST NOT 登记进各平台 driver 的能力常量——那样漏配一个 driver 会使该平台永久静默 fail-closed，且在运营视角与「客户端太老」不可区分。它 MUST 在边缘客户端构造处统一附加，使所有装配路径都无法遗漏。

cloud SHALL 额外做**版本偏斜检测**（下发了 `text` 但回执未标明执行了键入 ⇒ 标记异常）：闸做预防，检测抓「闸自己错了」。

#### Scenario: 旧客户端拒绝键入
- **WHEN** 运营对一台未声明键入能力的 edge 提交含 `text` 的命令
- **THEN** cloud MUST 拒绝、MUST NOT 下发，协助页展示人话提示（客户端版本过旧，不支持远程输入）

#### Scenario: 偏斜检测
- **WHEN** 云端下发了 `text` 但回执未标明键入模态
- **THEN** cloud MUST 标记该结果异常，MUST NOT 当作正常完成

## MODIFIED Requirements

### Requirement: 验证码告警必须创建可远程协助的 incident

云端收到 `risk.captcha_detected` 后，除既有风控迁移、edge 暂停和 Feishu 告警外，还 SHALL 为该次阻断创建或更新一个远程协助 incident。incident MUST 绑定真实 `edgeId`、`accountId`、`kind`、首次检测 URL、创建时间、过期时间和当前处理状态；若缺少 `edgeId` 或无法定位在线 edge，系统 MUST 诚实标记该 incident 不可远程协助。incident MUST NOT 让 cloud 新开浏览器处理平台验证码。

系统 MUST NOT 声称存在「远程桌面处置」这一后路：本系统不提供任何远程桌面能力，incident 与告警 MUST NOT 展示远程桌面入口或远程地址文案（见 REMOVED «远程桌面处置文案»）。不可远程协助时的诚实表述是**「本次无法远程协助」**，MUST NOT 暗示存在另一条已就绪的处置通道。

#### Scenario: 验证码创建远程协助 incident
- **WHEN** cloud 收到 `risk.captcha_detected{edgeId:'edge-1', accountId:'acc-1', kind:'captcha'}`
- **THEN** cloud 创建一个绑定 `edge-1` 与 `acc-1` 的 open incident，并继续执行既有 restricted、pause edge、Feishu 告警流程

#### Scenario: 无 edge 归属时不可远程协助
- **WHEN** cloud 收到无法定位 `edgeId` 或对应 edge 不在线的验证码上报
- **THEN** incident 状态 MUST 诚实显示不可远程协助，MUST NOT 广播截图或点击命令到其它 edge，MUST NOT 展示远程桌面入口

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `risk.captcha_cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。**实时抓帧循环 MUST NOT 用单次 probe 看不到遮罩就自主发 `risk.captcha_cleared`**：多步验证码在旧挑战消失、新挑战未绘出之间存在瞬时无遮罩窗口，自主判 cleared MUST 经连续 K 次确认 + 最小 settle 才成立。**实时循环的自主 probe 结果 MUST NOT 经 `click_result` 混入 `incident.lastResult`**，以免把非运营发起的探测记成一次复检、污染审计与前端"上次复检"。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

**`risk.captcha_cleared` 的发出权 MUST 被收归于两条路径：实时循环的连续 K 次确认，与旁路监测体的阻断态翻转闸。任何其它路径 MUST NOT 发出该消息——包括截图请求（手动刷新）处理中的单次 probe。** 截图请求发现当前无阻断时，MUST 只回 `not_blocked` 回执（cloud 据此更新 incident），MUST NOT 借此绕过 K 次确认直接上报清除：手动刷新与实时循环共用同一个瞬时无遮罩窗口，单次 probe 在此处与在实时循环里同样不可信。

**`risk.captcha_cleared` 的发送 MUST 排在 `click_result` 之前，且二者 MUST 各自独立容错。** 前者承重（解除生产账号的下发暂停），后者只驱动界面；把承重的那条排在装饰性的那条之后，会让传输异常时"已解决的验证码"永远到不了云端、账号无限期处于暗停状态。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `risk.captcha_cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

#### Scenario: 实时循环瞬时无遮罩不误清除
- **WHEN** 实时循环某一 tick 的单次 probe 未见遮罩，但下一挑战尚未绘出
- **THEN** 系统 MUST 要求连续 K 次确认 + 最小 settle 后才判 cleared，单次未见 MUST NOT 触发 `risk.captcha_cleared` 或提前解 `restricted`

#### Scenario: 手动刷新截图不得绕过 K 次确认
- **WHEN** 运营在协助页点「刷新」，edge 的单次 probe 未见遮罩
- **THEN** edge MUST 只回 `not_blocked` 回执，MUST NOT 发送 `risk.captcha_cleared`

#### Scenario: 键入进行中不得抓帧
- **WHEN** 某 incident 正在派发协助键入序列，此时收到截图请求
- **THEN** edge MUST 跳过该次抓帧，MUST NOT 回传键入中途的半程画面，MUST NOT 因此触发清除判定

#### Scenario: 自主探测不混入运营复检结果
- **WHEN** 实时循环自主 probe 得到状态
- **THEN** 该结果 MUST NOT 经 `click_result` 通道写入 `incident.lastResult`，前端"上次复检"只反映运营点击发起的复检

#### Scenario: 点击后仍被阻断
- **WHEN** edge 执行 assist 点击序列后 fresh probe 仍显示 captcha/unknown
- **THEN** edge 返回 still_blocked，cloud 保持该 edge 暂停并向协助页展示新的处理状态

#### Scenario: 手动解决告警不恢复 edge
- **WHEN** 操作者在告警列表中手动解决对应 captcha 告警但 edge 尚未发送 `risk.captcha_cleared`
- **THEN** cloud MUST 只闭合告警日志行，MUST NOT 将 incident 标记 cleared，MUST NOT resume 该 edge

### Requirement: 云端必须接收并解析验证码上报，不得静默丢弃

云端 SHALL 在 `protocol.ts` 镜像 `risk.captcha_detected` / `risk.captcha_cleared` 两个消息类型与对应 payload，并在 `DefaultMessageHandler` 路由它们到验证码协调器；MUST NOT 让这两类上报落到 switch 的 `unsupported_type` default 被静默丢弃。两份 `protocol.ts` MUST 逐字一致、消息总数同步、`docs/protocol.md` 计数与表同步。

**`MessageType` 穷举守卫只护消息类型、不护 payload 字段。** 当协助能力以「扩既有载荷的可选字段」而非「新增消息类型」的方式演进时，字段级漂移（一侧加了字段、另一侧没加）**typecheck 与消息数断言都抓不到**。因此协助命令与回执的 payload MUST 有逐字段的两侧往返断言，且 panel HTTP 边界（从 `unknown` 手写解构处）MUST 有透传断言——在那里漏一个字段是静默丢弃且全绿。

#### Scenario: 验证码上报被正确路由

- **WHEN** 云端收到一帧 `risk.captcha_detected{edgeId,kind,url}`
- **THEN** 云端将其交给验证码协调器处理（迁移状态 / 暂停 / 通知），而非返回 `error{code:'unsupported_type'}`

#### Scenario: 协议两侧不漂移

- **WHEN** 运行 `npm run typecheck` 与 `AC-PROTO` 合约测试
- **THEN** 边缘与云端两份 `protocol.ts` 的 `MessageType` 穷举一致、消息总数断言一致，且 `docs/protocol.md` 头部计数与表与代码一致

#### Scenario: 扩载荷字段不漂移

- **WHEN** 一侧的协助命令或回执 payload 新增 / 删改字段而另一侧未同步
- **THEN** 逐字段往返断言 MUST 失败；panel HTTP 边界未透传新字段时透传断言 MUST 失败

## REMOVED Requirements

### Requirement: 远程桌面处置文案

**Reason**: 该文案所指的后路**从不存在**。远程地址是边缘启动时从环境变量读取的自陈自由文本，全仓仅两行源码读取它，无示例配置、无文档、无界面入口，从未被填写过；控制台把该字符串直接当链接、Feishu 卡把它当一行文字打印。本系统**不提供任何远程桌面能力**，其真机验证自 2026-06-21 起一直 DEFERRED。保留一个背后什么都没有的处置入口，会让「协助不了就走远程桌面」成为一条不存在的推诿路径 —— 这与「MUST NOT 静默假成功」同源：向运营展示一个不可能奏效的出口，就是对能力边界撒谎。

**Migration**: 移除远程桌面入口与远程地址文案（控制台按钮、Feishu 卡片行、边缘环境变量读取、两份 `protocol.ts` 的 hello 载荷字段、云端 session / incident / panel 类型的连带字段）。不可远程协助时的诚实表述改为「本次无法远程协助」，不再暗示存在另一条通道。**无外部消费方**（该字段从未被填过），移除风险为零。若将来确需远程桌面，前置是先决定运营机上部署何种第三方工具（属采购与运维决策），届时另行立项 —— 留白比留一个假入口诚实。
