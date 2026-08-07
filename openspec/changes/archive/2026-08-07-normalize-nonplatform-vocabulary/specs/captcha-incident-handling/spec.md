## MODIFIED Requirements

### Requirement: 云端必须接收并解析验证码上报，不得静默丢弃

云端 SHALL 在 `protocol.ts` 镜像 `captcha.detected` / `captcha.cleared` 两个消息类型与对应 payload（验证码检测与协助自本 change 起同属 `captcha.*` 顶层域，一族一属主；历史 `risk.` 前缀因把「消费方拿它干什么」编码进名字而废止），并在 `DefaultMessageHandler` 路由它们到验证码协调器；MUST NOT 让这两类上报落到 switch 的 `unsupported_type` default 被静默丢弃。两份 `protocol.ts` MUST 逐字一致、消息总数同步、`docs/protocol.md` 计数与表同步。

**`MessageType` 穷举守卫只护消息类型、不护 payload 字段。** 当协助能力以「扩既有载荷的可选字段」而非「新增消息类型」的方式演进时，字段级漂移（一侧加了字段、另一侧没加）**typecheck 与消息数断言都抓不到**。因此协助命令与回执的 payload MUST 有逐字段的两侧往返断言，且 panel HTTP 边界（从 `unknown` 手写解构处）MUST 有透传断言——在那里漏一个字段是静默丢弃且全绿。

#### Scenario: 验证码上报被正确路由

- **WHEN** 云端收到一帧 `captcha.detected{edgeId,kind,url}`
- **THEN** 云端将其交给验证码协调器处理（迁移状态 / 暂停 / 通知），而非返回 `error{code:'unsupported_type'}`

#### Scenario: 协议两侧不漂移

- **WHEN** 运行 `npm run typecheck` 与 `AC-PROTO` 合约测试
- **THEN** 边缘与云端两份 `protocol.ts` 的 `MessageType` 穷举一致、消息总数断言一致，且 `docs/protocol.md` 头部计数与表与代码一致

#### Scenario: 扩载荷字段不漂移

- **WHEN** 一侧的协助命令或回执 payload 新增 / 删改字段而另一侧未同步
- **THEN** 逐字段往返断言 MUST 失败；panel HTTP 边界未透传新字段时透传断言 MUST 失败

### Requirement: 验证码上报必须迁移账号风控状态（云端单写）

云端收到 `captcha.detected` SHALL 依 `kind` 经 `RiskController.applySignal` 迁移**归属账号**的风控状态：`kind:'captcha'` 提交 `confirmed` 信号（`normal`→`restricted`），`kind:'unknown'` 提交 `light` 信号（`normal`→`warned`）。账号风控终态 MUST 仅由云端 `RiskController` / `RiskStateMachine` 单写，迁移结果 MUST 持久化。

#### Scenario: 验证码置账号为 restricted

- **WHEN** 云端收到 `captcha.detected{kind:'captcha'}` 且归属账号当前为 `normal`
- **THEN** 该账号迁移为 `restricted`，且该状态经 `PgRiskStore` 持久化、跨进程重启仍生效

#### Scenario: 未知弹窗温和降级

- **WHEN** 云端收到 `captcha.detected{kind:'unknown'}` 且归属账号当前为 `normal`
- **THEN** 该账号迁移为 `warned`（而非 `restricted`），保留互动但整体放慢

### Requirement: 验证码期间必须按 edge 暂停指令下发且不死锁

云端 SHALL 在传输层（`EdgeCloudServer.pushToEdges`）维护按 `edgeId` 的暂停集合；收到 `captcha.detected` 即暂停向**该 edge** 下发浏览 / 互动指令，对其它 edge 无影响。暂停 MUST 在 `RoleDispatcher.restartSession`（每次 `edge.hello` 重连）后仍然生效（持于传输层而非会话态）。`session.end` MUST 仍可送达被暂停的 edge；MUST NOT 通过结束共享会话 / 丢弃 `SessionContext` 来实现暂停（会冻结所有 edge 并被重连清除）。

#### Scenario: 暂停只影响出问题的 edge

- **WHEN** edge A 报验证码、edge B 正常浏览
- **THEN** 云端停止向 edge A 下发 scroll / interaction 指令，edge B 的下发不受影响

#### Scenario: 暂停期间会话仍可干净结束

- **WHEN** 某 edge 处于验证码暂停态、云端看门狗决定结束会话
- **THEN** `session.end` 仍能送达该 edge，会话干净终止，而非被暂停闸吞掉造成停滞

### Requirement: 必须去重冷却后发飞书通知，且失败不得静默

云端收到 `captcha.detected` SHALL 通过既有 `FeishuMessenger` 发一张 notify-only 告警卡（复用 `buildAlertCard`），内容含归属账号、机器定位（`machineLabel` / `edgeId`），便于人工前往处置；该卡 MUST NOT 带审批按钮、MUST NOT 写 `/tmp` 信号文件（与发布审批不同）、MUST NOT 展示远程桌面入口或远程地址文案（该入口已随本 change 移除）。云端 SHALL 对同一 edge 的重复验证码上报施加冷却窗（默认约 10 分钟、可配）以防刷屏。告警发送失败 MUST 被记录，MUST NOT 被静默吞掉。

#### Scenario: 首次验证码发卡

- **WHEN** 某 edge 首次报 `captcha.detected`
- **THEN** 云端向飞书群发一张含"账号 / 机器 / Edge"的告警卡

#### Scenario: 冷却窗内不重复刷屏

- **WHEN** 同一 edge 在冷却窗内多次翻进验证码态
- **THEN** 云端只发一张卡，冷却窗内的重复上报不再发卡

#### Scenario: 发卡失败不静默

- **WHEN** 飞书发送返回非 2xx / `code!=0`
- **THEN** 云端记录该失败（日志 / 可观测），而非吞掉当作成功

### Requirement: 收到验证码清除必须恢复该 edge 下发

云端收到 `captcha.cleared` SHALL 解除对该 `edgeId` 的传输层暂停，使浏览循环可继续（边缘清除弹窗后自行重扫并重报 `page.cards`，云端据此续刷）。风控状态 MUST NOT 因清除即自动回滚——降级由状态机恢复窗口或人工恢复命令驱动，避免一清除就解除安全姿态。

#### Scenario: 清除后恢复下发

- **WHEN** 某 edge 报 `captcha.cleared`
- **THEN** 云端解除该 edge 的暂停，后续 `page.cards` 能再次触发决策与下发

#### Scenario: 清除不自动解除 restricted

- **WHEN** 一个被验证码置为 `restricted` 的账号随后报 `captcha.cleared`
- **THEN** 该账号风控状态仍为 `restricted`（不自动回 `normal`），由恢复窗口或人工命令决定何时降级

### Requirement: 低置信未知遮罩的云端上报必须经一轮持续性确认

边缘对**最低置信的 `unknown` 阻断遮罩**（旁路监测按形状 / 尺寸 / iframe 启发式归类、无语义文案命中的那类）向云端上报 `captcha.detected` 前 MUST 经**一轮持续性确认**：翻转进 `unknown` 时 MUST NOT 第一轮探测差异即上报，须延后约一个监测轮询周期后**复核遮罩仍在**才发。**单轮即消失的瞬时 `unknown`**（如离页返回途中一闪即被自愈掉的坏页）MUST NOT 上报 `captcha.detected`、MUST NOT 触发账号风控状态迁移、MUST NOT 使云端暂停该 edge 下发。

`kind:'captcha'`（验证码厂商指纹命中）与登录墙类 MUST 保持**即时 fail-CLOSED**：MUST NOT 因本确认闸而延后，一经检出立即本地停手并即时上报 / 升级。本确认闸只作用于最低置信的 `unknown` 桶。

本要求约束的是**边缘何时上报**（上游），云端收到 `captcha.detected` 后的 `kind→signal→state` 映射（`unknown→light→warned`、`captcha→confirmed→restricted`）、传输层暂停、告警、恢复语义**全部不变**。**不新增 / 改动任何消息类型，两份 `protocol.ts` 消息总数不变**（AC-PROTO-02 断言值不因本 change 变动）。

#### Scenario: 一闪而过的未知遮罩不惊动云端

- **WHEN** 边缘旁路监测某一轮把页面判成 `unknown` 阻断遮罩，但在确认窗内（约一个轮询周期）遮罩已消失、页面回到非阻断态
- **THEN** 边缘 MUST NOT 发 `captcha.detected`，归属账号维持 `normal`、会话不被暂停；且因从未发过 `detected`，MUST NOT 发出无配对的孤儿 `captcha.cleared`

#### Scenario: 持续存在的未知遮罩照常上报

- **WHEN** 一堵真实持续的未知阻断遮罩在确认窗后复核仍在
- **THEN** 边缘照常发一次 `captcha.detected{kind:'unknown'}`，云端按既有映射迁移该账号 `normal→warned` 并暂停该 edge（行为不变）

#### Scenario: 验证码指纹类不被确认闸延后

- **WHEN** 边缘检出 `kind:'captcha'`（厂商滑块指纹）或登录墙
- **THEN** 边缘 MUST 即时本地停手并按现状即时上报 / 升级，MUST NOT 因低置信确认闸而延后（真验证码仍走 `confirmed→restricted`）

### Requirement: 瞬时阻断自愈时边缘自动上报清除且不留孤儿

边缘旁路监测从阻断态翻回非阻断态时 MUST 自动发 `captcha.cleared`（现役行为，保留）。结合上条确认闸，边缘 MUST 保证 `detected` 与 `cleared` **配对**：只有真正发过 `captcha.detected` 的阻断态，其自愈才发对应 `captcha.cleared`；被确认闸抑制、从未上报过的瞬时 `unknown`，其消失 MUST NOT 触发孤儿 `cleared`，也 MUST NOT 遗留一条已发但永不清除的 `detected`。

#### Scenario: 上报过的阻断自愈后发配对 cleared

- **WHEN** 边缘曾就一堵持续遮罩发过 `captcha.detected`，该遮罩随后自行消失
- **THEN** 边缘发一次 `captcha.cleared`，云端解除该 edge 暂停、恢复下发（风控状态按既有语义不自动回滚）

#### Scenario: 被抑制的瞬时遮罩消失不发孤儿 cleared

- **WHEN** 一次被确认闸抑制、从未上报的瞬时 `unknown` 遮罩消失
- **THEN** 边缘 MUST NOT 发 `captcha.cleared`（无配对 `detected`），云端侧无任何暂停 / 恢复扰动

### Requirement: 阻断告警卡片账号展示必须昵称优先

云端发送验证码 / 未知阻断弹窗 Feishu 告警卡时，卡片可见账号标识 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于 Feishu 文案，告警落库、风控状态迁移、edge 暂停 / 恢复和日志关联 MUST 继续使用真实 `accountId`。

#### Scenario: 未知阻断告警标题展示昵称

- **WHEN** 账号 `acc-1` 已捕获昵称 `工程师大白` 且该账号上报 `captcha.detected{kind:'unknown'}`
- **THEN** Feishu P1 告警卡标题中的账号后缀 SHALL 展示 `工程师大白`
- **AND** 告警落库与风控迁移仍 SHALL 使用 `acc-1`

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 账号 `acc-2` 尚未捕获昵称且该账号上报验证码或未知阻断
- **THEN** Feishu 告警卡 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或隐藏账号标识

### Requirement: 验证码告警必须创建可远程协助的 incident

云端收到 `captcha.detected` 后，除既有风控迁移、edge 暂停和 Feishu 告警外，还 SHALL 为该次阻断创建或更新一个远程协助 incident。incident MUST 绑定真实 `edgeId`、`accountId`、`kind`、首次检测 URL、创建时间、过期时间和当前处理状态；若缺少 `edgeId` 或无法定位在线 edge，系统 MUST 诚实标记该 incident 不可远程协助。incident MUST NOT 让 cloud 新开浏览器处理平台验证码。

系统 MUST NOT 声称存在「远程桌面处置」这一后路：本系统不提供任何远程桌面能力，incident 与告警 MUST NOT 展示远程桌面入口或远程地址文案。不可远程协助时的诚实表述是**「本次无法远程协助」**，MUST NOT 暗示存在另一条已就绪的处置通道。

> **移除背景（原「远程桌面处置文案」条款）**：远程地址是边缘启动时从环境变量读取的自陈自由文本，全仓仅两行源码读取它，无示例配置、无文档、无界面入口，从未被填写过；控制台把该字符串直接当链接、Feishu 卡把它当一行文字打印。系统**不提供任何远程桌面能力**，其真机验证自 2026-06-21 起一直 DEFERRED。保留一个背后什么都没有的处置入口，会让「协助不了就走远程桌面」成为一条不存在的推诿路径——这与「MUST NOT 静默假成功」同源。故本 change 移除远程桌面入口与远程地址文案（控制台按钮、Feishu 卡片行、边缘环境变量读取、两份 `protocol.ts` 的 hello 载荷 `remoteAddr` 字段、云端 session / incident / panel 类型的连带字段），**无外部消费方、风险为零**。若将来确需远程桌面，前置是先决定运营机上部署何种第三方工具（采购与运维决策），届时另行立项。

#### Scenario: 验证码创建远程协助 incident
- **WHEN** cloud 收到 `captcha.detected{edgeId:'edge-1', accountId:'acc-1', kind:'captcha'}`
- **THEN** cloud 创建一个绑定 `edge-1` 与 `acc-1` 的 open incident，并继续执行既有 restricted、pause edge、Feishu 告警流程

#### Scenario: 无 edge 归属时不可远程协助
- **WHEN** cloud 收到无法定位 `edgeId` 或对应 edge 不在线的验证码上报
- **THEN** incident 状态 MUST 诚实显示不可远程协助，MUST NOT 广播截图或点击命令到其它 edge，MUST NOT 展示远程桌面入口

### Requirement: 人工点击必须由原 edge 注入原浏览器并绑定 snapshot

协助页提交点击时，cloud SHALL 将点击序列作为归一化坐标发送给该 incident 绑定的原 edge；edge MUST 校验 incident、snapshot、当前阻断态和坐标边界后，将坐标映射回当前浏览器视口并派发真实输入事件。**当实时抓帧开启时，snapshot 绑定 MUST 放宽为"近期帧集"**：边缘 MUST 为每个 incident 保留最近 N 帧环、云端 MUST 相应保留最近 N 帧集，`submitClick` 的 `snapshot_mismatch` 守卫 MUST 放宽为"提交的 `snapshotId ∈ 近期集"，并用**该被点帧自己的 crop** 缩放坐标——否则运营点的稍旧但"与所见一致"的帧会被云端上游拦死、边缘帧环成死代码、白跑不降反升。cloud MUST NOT 在自身环境执行点击，MUST NOT 将点击命令广播到多个 edge，MUST NOT 用 DOM 状态篡改替代用户输入。

#### Scenario: 有效点击序列派发到原 edge
- **WHEN** 操作者基于最新 snapshot 提交两个图片点位和一个验证按钮点位
- **THEN** cloud 只向绑定 edge 发送点击命令，edge 将这些点映射到原浏览器并通过输入事件执行

#### Scenario: 稍旧但在近期集内的帧可提交
- **WHEN** 实时抓帧已推进 latest，但操作者提交的是被冻结的稍旧帧、其 `snapshotId` 仍在近期 N 帧集内
- **THEN** cloud MUST 放行该点击，edge MUST 用该被点帧自己的 crop 缩放坐标注入，MUST NOT 因非 latest 而判 `stale_snapshot`

#### Scenario: 超出近期集的 stale snapshot 拒绝点击
- **WHEN** 操作者基于已被挤出近期集或已过期的 snapshot 提交点击
- **THEN** cloud 或 edge MUST 拒绝该点击并返回 `stale_snapshot`，MUST NOT 盲目点击当前页面

#### Scenario: edge 当前不在阻断态
- **WHEN** edge 收到 assist 注入命令但注入前的 fresh probe 显示当前已无 captcha/unknown 阻断
- **THEN** edge MUST 不执行注入，MUST 回 `not_blocked` 回执，且 MUST NOT 由这一次单次 probe 发出 `captcha.cleared` —— 清除交由旁路监测体的翻转闸这条正常路径达成（见「远程协助后的恢复必须由 edge 复检清除驱动」的三条发出权划分）

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `captcha.cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。**实时抓帧循环 MUST NOT 用单次 probe 看不到遮罩就自主发 `captcha.cleared`**：多步验证码在旧挑战消失、新挑战未绘出之间存在瞬时无遮罩窗口，自主判 cleared MUST 经连续 K 次确认 + 最小 settle 才成立。**实时循环的自主 probe 结果 MUST NOT 经 `click_result` 混入 `incident.lastResult`**，以免把非运营发起的探测记成一次复检、污染审计与前端"上次复检"。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

**`captcha.cleared` 的发出权 MUST 限于三条路径**：① 运营发起的注入之后、经有界 settle 与 fresh probe 确认（本要求主句）；② 实时循环的连续 K 次确认；③ 旁路监测体的阻断态翻转闸。

**未经注入的单次 probe MUST NOT 发出该消息**，包括截图请求（手动刷新）与注入前的 stale 复检：它们与实时循环共用同一个「旧挑战已消失、新挑战未绘出」的瞬时无遮罩窗口，却既无 settle 也无连续确认——单次 probe 在这两处与在实时循环里同样不可信，据此上报即提前解 `restricted`（自残）。这两处发现当前无阻断时 MUST 只回 `not_blocked` 回执（cloud 的既有映射已据此更新 incident），恢复交由 ② / ③ 达成：旁路监测体本就在独立轮询，遮罩真的消失时它的翻转闸会发出配对的 `cleared`，故不发不会使该 edge 滞留暂停态。

**`captcha.cleared` 的发送 MUST 排在 `click_result` 之前，且二者 MUST 各自独立容错。** 前者承重（解除生产账号的下发暂停），后者只驱动界面；把承重的那条排在装饰性的那条之后，会让传输异常时"已解决的验证码"永远到不了云端、账号无限期处于暗停状态。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `captcha.cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

#### Scenario: 实时循环瞬时无遮罩不误清除
- **WHEN** 实时循环某一 tick 的单次 probe 未见遮罩，但下一挑战尚未绘出
- **THEN** 系统 MUST 要求连续 K 次确认 + 最小 settle 后才判 cleared，单次未见 MUST NOT 触发 `captcha.cleared` 或提前解 `restricted`

#### Scenario: 手动刷新截图不得绕过 K 次确认
- **WHEN** 运营在协助页点「刷新」，edge 的单次 probe 未见遮罩
- **THEN** edge MUST 只回 `not_blocked` 回执，MUST NOT 发送 `captcha.cleared`；恢复由旁路监测体的翻转闸达成

#### Scenario: 注入前复检发现遮罩已消失
- **WHEN** 运营提交了协助命令，但注入前的 stale 复检的单次 probe 未见遮罩
- **THEN** edge MUST NOT 注入、MUST 只回 `not_blocked` 回执，MUST NOT 发送 `captcha.cleared`（该 probe 未经 settle 与连续确认）

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
- **WHEN** 操作者在告警列表中手动解决对应 captcha 告警但 edge 尚未发送 `captcha.cleared`
- **THEN** cloud MUST 只闭合告警日志行，MUST NOT 将 incident 标记 cleared，MUST NOT resume 该 edge

### Requirement: 远程协助可复刻运营真实鼠标轨迹

系统 SHALL 允许控制台采集运营在协助页画面上的真实鼠标轨迹，并把它随既有 `captcha.assist.click` 命令上送、由原边缘复刻到原浏览器。轨迹 MUST 作为既有命令的**可选附加字段**承载，MUST NOT 新增 MessageType。**离散落点始终是落点的权威来源**；轨迹仅贡献移动路径与按下时机。无轨迹或轨迹无效时，系统 MUST 诚实回落到合成拟人路径（见"协助注入点击必须达到不低于日常点击的合成拟人度"），MUST NOT 谎称使用了轨迹。风控语义（detected→restricted、cleared 不自动回 normal、只有真实清除才发 `captcha.cleared`）MUST 保持不变。

#### Scenario: 控制台采集轨迹并与落点同基准
- **WHEN** 运营在协助页画面上移动并点击
- **THEN** 控制台 MUST 节流采样归一化坐标 `{x,y}`（[0,1]）+ 相对首样本毫秒 `t`，采样基准 MUST 与落点采集用**同一元素的 rect**
- **AND** MUST 在 `pointerdown` 时记录当前样本下标进 `clicks`，与 `points` 顺序对齐
- **AND** 画面 `snapshotId` 变更时 MUST 连同已选落点一起重置轨迹缓冲；不可交互态 MUST 不采样

#### Scenario: 落点权威，样本仅供移动时序
- **WHEN** 边缘回放轨迹
- **THEN** 每个 `mousePressed`/`mouseReleased` 的坐标 MUST 取权威落点 `points[i]` 的缩放值，MUST NOT 取样本漂移坐标（运营点完把鼠标移开也不受影响）

#### Scenario: 按下前必须补一帧移动到权威落点
- **WHEN** 边缘将在某个落点按下
- **THEN** 在 `mousePressed` 之前 MUST 补发一帧 `mouseMoved` 到该权威落点，保证 mousedown 坐标 == 最后一次 mousemove 坐标，MUST NOT 出现"mousedown 落在鼠标从未移动到的坐标"的瞬移伪影

#### Scenario: clicks 与 points 语义校验
- **WHEN** 收到带 `trajectory` 的点击
- **THEN** `clicks.length` MUST 等于 `points.length`；回放 MUST 按样本下标建 press 查找表、允许 `clicks` 非单调（运营先点 B 再点 A）
- **AND** 任一不满足（长度不等/下标越界）MUST 丢弃 trajectory 并诚实回落合成路径

#### Scenario: 缩时只裁剪长停顿，不等比压缩
- **WHEN** 轨迹总时长超过上限或含超长停顿
- **THEN** 系统 MUST 通过裁剪单个大 `Δt`（clamp 长停顿）来收敛，MUST NOT 等比压缩全程时序（避免产生超人速度）

#### Scenario: 回放叠抖动不做 verbatim 原样重放
- **WHEN** 边缘逐帧派发轨迹
- **THEN** 帧间 `dt` MUST 叠对数正态抖动、坐标 MUST 叠 ±1px 亚像素，去除零 `dt`；MUST NOT verbatim 原样重放固定节流采样节奏

#### Scenario: 三层守卫与可观测丢弃
- **WHEN** 轨迹在 panel 入口 / 云端 `submitClick` / 边缘消费端任一层被判畸形或超限
- **THEN** 系统 MUST 钳制（降采样/单调化/时长上限/坐标范围）或丢弃 trajectory 并**保留 `points` 继续**
- **AND** 丢弃 trajectory MUST 产生可观测日志/计数，MUST NOT 静默丢

#### Scenario: 回放模式回执用于度量
- **WHEN** 边缘完成一次协助点击并回报结果
- **THEN** `captcha.assist.click_result` MUST 携带 `replayMode`（`trajectory` 或 `synthetic`），使云端可把复检结果与所用输入模式关联

#### Scenario: 回放异常诚实回报
- **WHEN** 回放中途抛错，或轨迹为空/极短（运营秒点无移动）
- **THEN** 抛错 MUST 走既有 catch 如实回 `failed`；空/极短轨迹 MUST 回落合成、MUST NOT 当作有效轨迹硬回放

### Requirement: 协助注入点击必须达到不低于日常点击的合成拟人度

当运营通过云端协助页提交离散落点后，边缘把这些落点注入原浏览器时，注入动作的合成拟人度 MUST NOT 低于日常浏览点击。系统 MUST 复用既有贝塞尔 + ease-in-out + overshoot 拟人路径，且 MUST NOT 使用比日常点击更弱的参数（现状的 `jitter:0` + `overshoot:false` 被禁止作为常态）。所有随机与停顿 MUST 走可注入随机源以保证桩测确定性；回执与风控语义（见"远程协助后的恢复必须由 edge 复检清除驱动"）MUST 保持不变。

#### Scenario: 注入路径非瞬移且带人类特征
- **WHEN** 边缘对某个落点注入点击
- **THEN** MUST 沿贝塞尔曲线逐帧 `mouseMoved` 后再 `mousePressed`/`mouseReleased`（非瞬移）
- **AND** MUST 以适度概率保留 overshoot（越过目标再回拉）并叠加小幅落点 jitter，press 仍落在运营指定目标

#### Scenario: 多点之间光标连续
- **WHEN** 一次协助包含多个落点（依次点击）
- **THEN** 下一个落点的移动起点 MUST 取上一个落点的**真实落点**（含 jitter/overshoot 残差），MUST NOT 让每点各自从随机起点冒出

#### Scenario: 逐帧移动延迟带抖动
- **WHEN** 边缘逐帧派发 `mouseMoved`
- **THEN** 帧间延迟 MUST 带抖动（对数正态或等价），MUST NOT 是方差为 0 的固定周期

#### Scenario: 落点前读图停顿与点间对数正态停顿
- **WHEN** 边缘移动到目标后、按下之前
- **THEN** MUST 插入一段可注入的读图/瞄准停顿（dwell）
- **AND** 多点之间 MUST 用对数正态采样的停顿替代固定时距，仅在非末点后停顿

#### Scenario: 节奏参数按机器派生避免车队指纹
- **WHEN** 多台边缘对同类验证码执行协助注入
- **THEN** 节奏分布的中心值 MUST 含按 `edgeId` 派生的每机偏置，MUST NOT 让全 fleet 使用逐字相同的固定节奏常量

#### Scenario: 拟人化不改变诚实回执
- **WHEN** 注入后遮罩仍在或注入过程抛错
- **THEN** MUST 沿用既有 `settle → reprobe → still_blocked / failed / 回传新截图` 回执，MUST NOT 因拟人化改动而静默假成功；只有真实清除才发 `captcha.cleared`

### Requirement: 小红书笔记访问限制弹窗不得作为账号级验证码事故上报

边缘 SHALL 识别小红书 Web 笔记访问限制弹窗（如 `access-modal`、`access-limit-app`、文案“当前笔记暂时无法浏览 / 请打开小红书App扫码查看”）为可恢复的笔记访问限制状态，而非账号登录墙、验证码或未知账号级阻断。该类弹窗出现时，边缘 MUST NOT 触发 `captcha.detected`、MUST NOT 将浏览命令队列长期暂停为 captcha/unknown；它 MAY 通过关闭浮层或直接导航回健康来源列表恢复。若访问限制发生在正在打开的笔记上，边缘仍须诚实失败或返回列表，MUST NOT 冒充已成功读取该笔记。

#### Scenario: 失效详情路由弹出 access-limit-app
- **WHEN** 小红书页面出现可见 `access-modal` / `access-limit-app`，并包含“当前笔记暂时无法浏览”或“请打开小红书App扫码查看”等文案
- **THEN** 边缘将其分类为非阻断可恢复弹窗，MUST NOT 上报为验证码或 unknown 阻断，后续 `navigation.back` / 返回来源列表命令仍可执行

#### Scenario: 真验证码仍按账号级风控处理
- **WHEN** 页面出现验证码厂商 iframe、滑块/点选验证容器或“安全验证 / 滑动验证 / 请完成验证”等挑战文案
- **THEN** 边缘仍按 captcha 阻断处理并暂停高风险动作，MUST NOT 因 access-limit 兜底放宽真实验证码判断

### Requirement: Blocking-state surveillance SHALL run on every Native browse platform

The edge's Native browse runtime MUST run a periodic blocking-state observation for **every** platform whose browse sessions it drives, not only for Facebook. Platform identity MAY select which classifier is applied, but it MUST NOT decide whether any observation runs at all: a supported browse platform without a running blocking observation is an unguarded session and MUST NOT be started as if it were guarded.

For Xiaohongshu the observation MUST at minimum distinguish a captcha/verification challenge state and a login-wall state from a non-blocking state, and it MUST act on them:

- Captcha state MUST fail closed immediately: the edge MUST stop ordinary browse locally and MUST send `captcha.detected{kind:'captcha'}` carrying the edge id, the owning account id when known, and the observed location.
- Login-wall state MUST stop ordinary browse locally. The edge MUST NOT report a login wall as an account-level captcha incident, and MUST NOT report any browse command that was suppressed by it as successful.
- Returning to a non-blocking state MUST send exactly one paired `captcha.cleared` when — and only when — a `captcha.detected` was actually sent for that episode. A suppressed or never-reported episode MUST NOT produce an orphan `cleared`, and a reported episode MUST NOT be left with a `detected` that is never cleared.

While the edge is locally stopped for a blocking state, browse commands that arrive MUST receive a truthful not-started result; they MUST NOT be silently dropped and MUST NOT be answered as if the page action had happened.

This requirement MUST NOT add or remove protocol message types; the two `protocol.ts` copies keep the same `MessageType` enumeration and message count.

#### Scenario: Xiaohongshu captcha reaches the cloud

- **WHEN** a Xiaohongshu browse session's periodic observation classifies the current page as a captcha/verification challenge
- **THEN** the edge stops ordinary browse locally and sends one `captcha.detected{kind:'captcha'}` with the edge id and observed location
- **AND** the cloud can migrate the owning account's risk state and offer remote assistance, exactly as it does for the Facebook path

#### Scenario: Self-healed Xiaohongshu block sends one paired clear

- **WHEN** a Xiaohongshu blocking state for which `captcha.detected` was sent disappears and the page returns to a non-blocking state
- **THEN** the edge sends exactly one `captcha.cleared` and resumes ordinary browse
- **AND** it does not send a second `detected` for the same episode

#### Scenario: Never-reported episode produces no orphan clear

- **WHEN** a blocking observation never resulted in a `captcha.detected` and the page returns to a non-blocking state
- **THEN** the edge sends no `captcha.cleared`
- **AND** the cloud sees no pause/resume disturbance for that edge

#### Scenario: Login wall is not reported as an account-level captcha incident

- **WHEN** a Xiaohongshu browse session observes a login wall
- **THEN** the edge stops ordinary browse locally and waits for login
- **AND** it does not send `captcha.detected` for the login wall, and it does not report the suppressed browse commands as successful

#### Scenario: A supported browse platform is never left unobserved

- **WHEN** the Native browse runtime starts a session for a platform it declares as supporting browse
- **THEN** a periodic blocking-state observation is running for that session
- **AND** no platform is excluded from observation by a platform-identity guard placed ahead of the observation itself

### Requirement: Unavailable blocking classifications SHALL be declared absent, never simulated

The low-confidence `unknown` blocking bucket requires a real blocking-overlay classifier (shape/iframe/wording heuristics over a visible obstructing surface). Where no such classifier exists for a platform, the edge MUST treat that bucket as **declared absent** and MUST NOT synthesize it from an unrelated signal.

Specifically, a generic "the page type was not recognized" outcome MUST NOT be mapped to a blocking report. Those two facts are different: "I did not recognize this page" is not evidence of an obstructing surface, and mapping one to the other turns every page-recognition miss into an account risk downgrade.

Evidence text carried with a blocking report MUST come from the same page text that produced the classification, bounded in length; the edge MUST NOT fabricate evidence text, and MUST NOT loosen the classification thresholds in order to produce evidence.

When the low-confidence bucket is absent for a platform, the delayed-confirmation gate that governs it has nothing to gate; the immediate fail-closed handling of the captcha and login-wall classes MUST remain in force regardless.

#### Scenario: Unrecognized page type is not a blocking report

- **WHEN** a Xiaohongshu periodic observation returns a page whose type could not be recognized, with no captcha or login-wall classification
- **THEN** the edge sends no `captcha.detected`
- **AND** the owning account's risk state is not migrated and the edge is not paused

#### Scenario: Absent bucket does not weaken the fail-closed classes

- **WHEN** a platform has no low-confidence blocking classifier
- **THEN** its captcha and login-wall classes are still handled immediately and fail closed
- **AND** the absence of the low-confidence bucket is recorded as a declared gap rather than covered by a substitute signal

#### Scenario: Evidence text is never fabricated

- **WHEN** a blocking report is sent but the classification produced no usable page text
- **THEN** the report omits evidence text rather than carrying invented or unrelated text
- **AND** the classification decision itself is unchanged by the absence of evidence text
