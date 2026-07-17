# captcha-incident-handling Specification

## Purpose
TBD - created by archiving change captcha-restrict-and-interaction-gating. Update Purpose after archive.
## Requirements
### Requirement: 云端必须接收并解析验证码上报，不得静默丢弃

云端 SHALL 在 `protocol.ts` 镜像 `risk.captcha_detected` / `risk.captcha_cleared` 两个消息类型与对应 payload，并在 `DefaultMessageHandler` 路由它们到验证码协调器；MUST NOT 让这两类上报落到 switch 的 `unsupported_type` default 被静默丢弃。两份 `protocol.ts` MUST 逐字一致、消息总数同步、`docs/protocol.md` 计数与表同步。

#### Scenario: 验证码上报被正确路由

- **WHEN** 云端收到一帧 `risk.captcha_detected{edgeId,kind,url}`
- **THEN** 云端将其交给验证码协调器处理（迁移状态 / 暂停 / 通知），而非返回 `error{code:'unsupported_type'}`

#### Scenario: 协议两侧不漂移

- **WHEN** 运行 `npm run typecheck` 与 `AC-PROTO` 合约测试
- **THEN** 边缘与云端两份 `protocol.ts` 的 `MessageType` 穷举一致、消息数断言均为 44，且 `docs/protocol.md` 头部计数与表与代码一致

### Requirement: 验证码上报必须迁移账号风控状态（云端单写）

云端收到 `risk.captcha_detected` SHALL 依 `kind` 经 `RiskController.applySignal` 迁移**归属账号**的风控状态：`kind:'captcha'` 提交 `confirmed` 信号（`normal`→`restricted`），`kind:'unknown'` 提交 `light` 信号（`normal`→`warned`）。账号风控终态 MUST 仅由云端 `RiskController` / `RiskStateMachine` 单写，迁移结果 MUST 持久化。

#### Scenario: 验证码置账号为 restricted

- **WHEN** 云端收到 `risk.captcha_detected{kind:'captcha'}` 且归属账号当前为 `normal`
- **THEN** 该账号迁移为 `restricted`，且该状态经 `PgRiskStore` 持久化、跨进程重启仍生效

#### Scenario: 未知弹窗温和降级

- **WHEN** 云端收到 `risk.captcha_detected{kind:'unknown'}` 且归属账号当前为 `normal`
- **THEN** 该账号迁移为 `warned`（而非 `restricted`），保留互动但整体放慢

### Requirement: 验证码期间必须按 edge 暂停指令下发且不死锁

云端 SHALL 在传输层（`EdgeCloudServer.pushToEdges`）维护按 `edgeId` 的暂停集合；收到 `risk.captcha_detected` 即暂停向**该 edge** 下发浏览 / 互动指令，对其它 edge 无影响。暂停 MUST 在 `RoleDispatcher.restartSession`（每次 `edge.hello` 重连）后仍然生效（持于传输层而非会话态）。`session.end` MUST 仍可送达被暂停的 edge；MUST NOT 通过结束共享会话 / 丢弃 `SessionContext` 来实现暂停（会冻结所有 edge 并被重连清除）。

#### Scenario: 暂停只影响出问题的 edge

- **WHEN** edge A 报验证码、edge B 正常浏览
- **THEN** 云端停止向 edge A 下发 scroll / interaction 指令，edge B 的下发不受影响

#### Scenario: 暂停期间会话仍可干净结束

- **WHEN** 某 edge 处于验证码暂停态、云端看门狗决定结束会话
- **THEN** `session.end` 仍能送达该 edge，会话干净终止，而非被暂停闸吞掉造成停滞

### Requirement: 必须去重冷却后发飞书通知，且失败不得静默

云端收到 `risk.captcha_detected` SHALL 通过既有 `FeishuMessenger` 发一张 notify-only 告警卡（复用 `buildAlertCard`），内容含归属账号、机器 / 远程桌面定位，便于人工前往处置；该卡 MUST NOT 带审批按钮、MUST NOT 写 `/tmp` 信号文件（与发布审批不同）。云端 SHALL 对同一 edge 的重复验证码上报施加冷却窗（默认约 10 分钟、可配）以防刷屏。告警发送失败 MUST 被记录，MUST NOT 被静默吞掉。

#### Scenario: 首次验证码发卡

- **WHEN** 某 edge 首次报 `risk.captcha_detected`
- **THEN** 云端向飞书群发一张含"账号 / 机器 / 远程地址"的告警卡

#### Scenario: 冷却窗内不重复刷屏

- **WHEN** 同一 edge 在冷却窗内多次翻进验证码态
- **THEN** 云端只发一张卡，冷却窗内的重复上报不再发卡

#### Scenario: 发卡失败不静默

- **WHEN** 飞书发送返回非 2xx / `code!=0`
- **THEN** 云端记录该失败（日志 / 可观测），而非吞掉当作成功

### Requirement: 收到验证码清除必须恢复该 edge 下发

云端收到 `risk.captcha_cleared` SHALL 解除对该 `edgeId` 的传输层暂停，使浏览循环可继续（边缘清除弹窗后自行重扫并重报 `page.cards`，云端据此续刷）。风控状态 MUST NOT 因清除即自动回滚——降级由状态机恢复窗口或人工恢复命令驱动，避免一清除就解除安全姿态。

#### Scenario: 清除后恢复下发

- **WHEN** 某 edge 报 `risk.captcha_cleared`
- **THEN** 云端解除该 edge 的暂停，后续 `page.cards` 能再次触发决策与下发

#### Scenario: 清除不自动解除 restricted

- **WHEN** 一个被验证码置为 `restricted` 的账号随后报 `risk.captcha_cleared`
- **THEN** 该账号风控状态仍为 `restricted`（不自动回 `normal`），由恢复窗口或人工命令决定何时降级

### Requirement: 边缘 hello 必须声明账号与机器定位以供归属

边缘 SHALL 在 `hello` 的 `HelloPayload` 声明 `accountId` 与机器 / 远程桌面定位（如 `machineLabel` / `remoteAddr`）；云端 `onHello` MUST 将其登记到该连接（`EdgeSession` / 连接表），使验证码事件能确定**归属账号**（不再硬编码 `acc-default`）并在告警卡中给出"去哪台机器处置"。字段缺失时云端 MUST 安全降级（卡片至少给出 `edgeId`），MUST NOT 因缺字段崩溃。

#### Scenario: hello 带身份则卡片可定位

- **WHEN** 边缘 `hello` 声明了 `accountId` 与 `machineLabel` / `remoteAddr`
- **THEN** 该 edge 报验证码时，云端把状态迁移落到对应 `accountId`，告警卡含机器 / 远程地址

#### Scenario: 旧边缘缺身份字段仍可降级

- **WHEN** 早于本 change 的边缘 `hello` 未带 `accountId` / 机器定位
- **THEN** 云端不崩溃，告警卡至少带 `edgeId`，状态迁移落到默认账号（向后兼容）

### Requirement: 低置信未知遮罩的云端上报必须经一轮持续性确认

边缘对**最低置信的 `unknown` 阻断遮罩**（旁路监测按形状 / 尺寸 / iframe 启发式归类、无语义文案命中的那类）向云端上报 `risk.captcha_detected` 前 MUST 经**一轮持续性确认**：翻转进 `unknown` 时 MUST NOT 第一轮探测差异即上报，须延后约一个监测轮询周期后**复核遮罩仍在**才发。**单轮即消失的瞬时 `unknown`**（如离页返回途中一闪即被自愈掉的坏页）MUST NOT 上报 `risk.captcha_detected`、MUST NOT 触发账号风控状态迁移、MUST NOT 使云端暂停该 edge 下发。

`kind:'captcha'`（验证码厂商指纹命中）与登录墙类 MUST 保持**即时 fail-CLOSED**：MUST NOT 因本确认闸而延后，一经检出立即本地停手并即时上报 / 升级。本确认闸只作用于最低置信的 `unknown` 桶。

本要求约束的是**边缘何时上报**（上游），云端收到 `risk.captcha_detected` 后的 `kind→signal→state` 映射（`unknown→light→warned`、`captcha→confirmed→restricted`）、传输层暂停、告警、恢复语义**全部不变**。**不新增 / 改动任何消息类型，两份 `protocol.ts` 消息总数不变**（AC-PROTO-02 断言值不因本 change 变动）。

#### Scenario: 一闪而过的未知遮罩不惊动云端

- **WHEN** 边缘旁路监测某一轮把页面判成 `unknown` 阻断遮罩，但在确认窗内（约一个轮询周期）遮罩已消失、页面回到非阻断态
- **THEN** 边缘 MUST NOT 发 `risk.captcha_detected`，归属账号维持 `normal`、会话不被暂停；且因从未发过 `detected`，MUST NOT 发出无配对的孤儿 `risk.captcha_cleared`

#### Scenario: 持续存在的未知遮罩照常上报

- **WHEN** 一堵真实持续的未知阻断遮罩在确认窗后复核仍在
- **THEN** 边缘照常发一次 `risk.captcha_detected{kind:'unknown'}`，云端按既有映射迁移该账号 `normal→warned` 并暂停该 edge（行为不变）

#### Scenario: 验证码指纹类不被确认闸延后

- **WHEN** 边缘检出 `kind:'captcha'`（厂商滑块指纹）或登录墙
- **THEN** 边缘 MUST 即时本地停手并按现状即时上报 / 升级，MUST NOT 因低置信确认闸而延后（真验证码仍走 `confirmed→restricted`）

### Requirement: 瞬时阻断自愈时边缘自动上报清除且不留孤儿

边缘旁路监测从阻断态翻回非阻断态时 MUST 自动发 `risk.captcha_cleared`（现役行为，保留）。结合上条确认闸，边缘 MUST 保证 `detected` 与 `cleared` **配对**：只有真正发过 `risk.captcha_detected` 的阻断态，其自愈才发对应 `risk.captcha_cleared`；被确认闸抑制、从未上报过的瞬时 `unknown`，其消失 MUST NOT 触发孤儿 `cleared`，也 MUST NOT 遗留一条已发但永不清除的 `detected`。

#### Scenario: 上报过的阻断自愈后发配对 cleared

- **WHEN** 边缘曾就一堵持续遮罩发过 `risk.captcha_detected`，该遮罩随后自行消失
- **THEN** 边缘发一次 `risk.captcha_cleared`，云端解除该 edge 暂停、恢复下发（风控状态按既有语义不自动回滚）

#### Scenario: 被抑制的瞬时遮罩消失不发孤儿 cleared

- **WHEN** 一次被确认闸抑制、从未上报的瞬时 `unknown` 遮罩消失
- **THEN** 边缘 MUST NOT 发 `risk.captcha_cleared`（无配对 `detected`），云端侧无任何暂停 / 恢复扰动

### Requirement: 阻断告警卡片账号展示必须昵称优先

云端发送验证码 / 未知阻断弹窗 Feishu 告警卡时，卡片可见账号标识 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于 Feishu 文案，告警落库、风控状态迁移、edge 暂停 / 恢复和日志关联 MUST 继续使用真实 `accountId`。

#### Scenario: 未知阻断告警标题展示昵称

- **WHEN** 账号 `acc-1` 已捕获昵称 `工程师大白` 且该账号上报 `risk.captcha_detected{kind:'unknown'}`
- **THEN** Feishu P1 告警卡标题中的账号后缀 SHALL 展示 `工程师大白`
- **AND** 告警落库与风控迁移仍 SHALL 使用 `acc-1`

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 账号 `acc-2` 尚未捕获昵称且该账号上报验证码或未知阻断
- **THEN** Feishu 告警卡 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或隐藏账号标识

### Requirement: Facebook checkpoint and login states are detected by URL/location

For Facebook platform sessions, overlay detection SHALL include URL/location classification in addition to DOM masks/dialogs/iframes. URLs or routes indicating `/checkpoint`, login walls, account recovery, temporarily blocked states, or equivalent full-page blocking states MUST be classified as blocking incidents and reported through the existing captcha/risk incident path. Detection MUST fail closed before posting or other account-scoped actions.

#### Scenario: Checkpoint URL stops automation
- **WHEN** a Facebook session navigates to a URL containing a checkpoint route
- **THEN** edge classifies the page as blocked, reports the incident through the existing risk/captcha path, and does not continue browsing or commenting

#### Scenario: Login wall stops automation
- **WHEN** a Facebook session lands on a login wall while account-scoped work is expected
- **THEN** edge reports login/identity loss and stops assigning work to that account, rather than treating the page as empty results

### Requirement: Facebook overlay detection runs before submit attempts

Facebook comment submit or other account-scoped actions SHALL perform a fresh blocking-state check immediately before the action. If URL/location or DOM classification indicates checkpoint/login/temporarily blocked state, the action MUST fail honestly and MUST NOT submit.

#### Scenario: Fresh pre-submit check blocks unsafe submit
- **WHEN** a Facebook comment editor was previously available but the page enters checkpoint/login state before submit
- **THEN** the pre-submit blocking check fails the action honestly and no submit key/click is sent

### Requirement: 验证码告警必须创建可远程协助的 incident

云端收到 `risk.captcha_detected` 后，除既有风控迁移、edge 暂停和 Feishu 告警外，还 SHALL 为该次阻断创建或更新一个远程协助 incident。incident MUST 绑定真实 `edgeId`、`accountId`、`kind`、首次检测 URL、创建时间、过期时间和当前处理状态；若缺少 `edgeId` 或无法定位在线 edge，系统 MUST 诚实标记该 incident 不可远程协助，并保留远程桌面处置文案。incident MUST NOT 让 cloud 新开浏览器处理平台验证码。

#### Scenario: 验证码创建远程协助 incident
- **WHEN** cloud 收到 `risk.captcha_detected{edgeId:'edge-1', accountId:'acc-1', kind:'captcha'}`
- **THEN** cloud 创建一个绑定 `edge-1` 与 `acc-1` 的 open incident，并继续执行既有 restricted、pause edge、Feishu 告警流程

#### Scenario: 无 edge 归属时不可远程协助
- **WHEN** cloud 收到无法定位 `edgeId` 或对应 edge 不在线的验证码上报
- **THEN** incident 状态 MUST 诚实显示不可远程协助，MUST NOT 广播截图或点击命令到其它 edge

### Requirement: Feishu 验证码告警必须提供受保护的云端处理入口

当远程协助 incident 可用时，Feishu 验证码 / 未知阻断告警卡 SHALL 包含一个“去处理”入口，指向该 incident 的云端协助页。入口 MUST 使用正常 console JWT 鉴权或短期签名 token；签名 token MUST 只授权读取、刷新和提交该 incident 的协助动作，MUST NOT 授权账号启停、风控状态写入、发布审批或其它管理操作。Feishu 卡 MUST NOT 直接承载验证码截图或“已解决”按钮。

#### Scenario: 告警卡展示去处理入口
- **WHEN** cloud 为验证码 incident 发送 Feishu 告警卡且 assist 已启用
- **THEN** 卡片包含指向该 incident 的受保护 action URL，卡片正文仍说明可远程桌面兜底

#### Scenario: token 作用域受限
- **WHEN** 操作者使用 Feishu action URL 打开协助页
- **THEN** cloud 只允许该 token 访问对应 incident 的截图、刷新和点击接口，MUST NOT 接受该 token 调用账号风险或调度管理接口

### Requirement: 云端协助页必须只展示 edge 捕获的现场截图

协助页 SHALL 通过 cloud 请求原 edge 捕获当前阻断遮罩截图，并展示该截图供人工点击。截图 MUST 来源于原 edge 的原浏览器会话，MUST 包含截图时间、过期状态和坐标映射信息；cloud MUST NOT 使用另一个浏览器访问平台页面来生成截图。截图数据 MUST 短期保存并受大小限制，MUST NOT 写入普通日志或长期暴露在 Feishu 消息中。

#### Scenario: 请求现场截图
- **WHEN** 操作者打开可用 incident 的协助页并请求刷新截图
- **THEN** cloud 向该 incident 绑定的 edge 发送截图请求，edge 从当前原浏览器捕获阻断遮罩截图并返回 snapshot id 与坐标映射

#### Scenario: 截图过期
- **WHEN** 协助页持有的 snapshot 已超过有效期
- **THEN** 页面 MUST 要求刷新截图后再提交点击，cloud MUST NOT 将过期 snapshot 的点击当作有效操作

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
- **WHEN** edge 收到 assist 点击命令但 fresh probe 显示当前已无 captcha/unknown 阻断
- **THEN** edge MUST 不执行点击，并发送或保持 `risk.captcha_cleared` 的正常清除路径

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `risk.captcha_cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。**实时抓帧循环 MUST NOT 用单次 probe 看不到遮罩就自主发 `risk.captcha_cleared`**：多步验证码在旧挑战消失、新挑战未绘出之间存在瞬时无遮罩窗口，自主判 cleared MUST 经连续 K 次确认 + 最小 settle 才成立。**实时循环的自主 probe 结果 MUST NOT 经 `click_result` 混入 `incident.lastResult`**，以免把非运营发起的探测记成一次复检、污染审计与前端"上次复检"。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `risk.captcha_cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

#### Scenario: 实时循环瞬时无遮罩不误清除
- **WHEN** 实时循环某一 tick 的单次 probe 未见遮罩，但下一挑战尚未绘出
- **THEN** 系统 MUST 要求连续 K 次确认 + 最小 settle 后才判 cleared，单次未见 MUST NOT 触发 `risk.captcha_cleared` 或提前解 `restricted`

#### Scenario: 自主探测不混入运营复检结果
- **WHEN** 实时循环自主 probe 得到状态
- **THEN** 该结果 MUST NOT 经 `click_result` 通道写入 `incident.lastResult`，前端"上次复检"只反映运营点击发起的复检

#### Scenario: 点击后仍被阻断
- **WHEN** edge 执行 assist 点击序列后 fresh probe 仍显示 captcha/unknown
- **THEN** edge 返回 still_blocked，cloud 保持该 edge 暂停并向协助页展示新的处理状态

#### Scenario: 手动解决告警不恢复 edge
- **WHEN** 操作者在告警列表中手动解决对应 captcha 告警但 edge 尚未发送 `risk.captcha_cleared`
- **THEN** cloud MUST 只闭合告警日志行，MUST NOT 将 incident 标记 cleared，MUST NOT resume 该 edge

### Requirement: 暂停期间只允许 captcha assist 恢复命令穿透

当某 edge 因验证码处于暂停态时，cloud 传输层 SHALL 继续阻止普通浏览、互动、发布页面动作等命令下发；但 SHALL 允许该 edge 绑定 incident 的截图与人工点击协助命令穿透暂停闸。穿透白名单 MUST 精确限定为 captcha assist 恢复路径与既有 `session.end` / 纯 UI 状态消息，MUST NOT 泛化为所有控制命令。

#### Scenario: 普通命令仍被暂停闸拦截
- **WHEN** edge `edge-1` 处于 captcha 暂停态且 cloud 尝试下发 `browse.next`
- **THEN** 该普通浏览命令仍被暂停闸拦截

#### Scenario: assist capture 可穿透暂停闸
- **WHEN** edge `edge-1` 处于 captcha 暂停态且操作者请求刷新协助截图
- **THEN** cloud 可向 `edge-1` 下发该 incident 的 `captcha.assist.capture` 命令

### Requirement: 远程协助必须可审计且短期留存

系统 SHALL 记录远程协助 incident 的关键审计事件，包括创建、截图刷新、点击提交、edge 结果、清除、过期和失败；审计记录 MUST 包含操作者来源、incident id、edge/account 归属、时间和结果，但 MUST NOT 把截图二进制、平台 cookie、验证码答案推断或敏感 token 写入普通日志。截图和签名 token MUST 有短期过期策略。

#### Scenario: 记录点击审计
- **WHEN** 操作者提交一次远程协助点击
- **THEN** cloud 记录该 incident 的点击审计事件与结果状态，但不记录截图二进制或签名 token 明文

#### Scenario: incident 过期
- **WHEN** incident 超过有效期且未清除
- **THEN** cloud 将其标记 expired，协助页显示需重新触发或远程桌面处理，MUST NOT 继续接受旧 token 的点击请求

### Requirement: 验证码可交互态必须近实时回传现场帧

当验证码 incident 处于可交互态时，系统 SHALL 支持边缘对该 incident 运行一个**有界、自终止、内容去重**的低帧率抓帧循环，使控制台总能看到接近活体的挑战画面。该能力 MUST 复用既有 `captcha.assist.capture` 命令的可选 `live` 字段进入（MUST NOT 新增 MessageType、MUST NOT 新增未在 edge onMessage 白名单内的主动命令）。本能力服务**自刷新 / 多步换图的点选类**验证码；滑块/拖拽类不在范围。抓帧只读、MUST NOT 篡改页面。

#### Scenario: 进入与不带 live 的零回归
- **WHEN** 云端以带 `live` 的 `captcha.assist.capture` 请求抓帧
- **THEN** 边缘推首帧后进入有界实时循环
- **AND** 不带 `live` 的 capture MUST 维持今天的单次抓帧行为（零回归）

#### Scenario: 内容去重且有最小推帧间隔
- **WHEN** 实时循环每个 tick 抓到一帧
- **THEN** MUST 与上次已推帧做内容比较，内容未变 MUST NOT 推送
- **AND** MUST 有最小推帧间隔硬地板与单帧字节/帧率上限，即便去重被动画/倒计时击穿也不全速推大图

#### Scenario: 循环三重有界自终止
- **WHEN** 实时循环运行
- **THEN** MUST 受最大时长、最大帧数、遮罩消失三重约束自终止，MUST NOT 遗留孤儿循环
- **AND** 收敛 MUST 用注入 timer + 迭代计数，MUST NOT 拿 `now()` 当终止条件（防桩测恒定 now 死循环）

#### Scenario: 抓帧与点击互斥
- **WHEN** 边缘正在派发协助点击
- **THEN** 实时 tick MUST 被 `clicking` 互斥暂停，避免抓到点击派发中途的半程态

#### Scenario: 实时窗口绑运营在场
- **WHEN** 运营尚未打开协助页
- **THEN** 系统 MUST 以控制台既有轮询等在场信号 re-arm 抓帧，MUST NOT 仅靠一个固定盲目窗口在运营到场前就自终止

#### Scenario: 迟到实时帧不复活已清除态
- **WHEN** 一帧实时 snapshot 在 incident 已 `cleared`/`expired` 之后到达
- **THEN** 云端 MUST 忽略该帧、MUST NOT 把状态复活为 `ready`

#### Scenario: 控制台选点期冻结与多步换图区分
- **WHEN** 运营已放下至少一个落点、其后实时帧到达
- **THEN** 控制台 MUST 冻结当前画面与已选点（周期自刷新的同一挑战不冲掉选点）
- **AND** 当挑战内容实质改变（换问题）时 MUST NOT 静默沿用旧帧让运营点错，MUST 给显式"挑战已变、请重看"提示并允许手动解冻到最新帧

### Requirement: 远程协助可复刻运营真实鼠标轨迹

系统 SHALL 允许控制台采集运营在协助页画面上的真实鼠标轨迹，并把它随既有 `captcha.assist.click` 命令上送、由原边缘复刻到原浏览器。轨迹 MUST 作为既有命令的**可选附加字段**承载，MUST NOT 新增 MessageType。**离散落点始终是落点的权威来源**；轨迹仅贡献移动路径与按下时机。无轨迹或轨迹无效时，系统 MUST 诚实回落到合成拟人路径（见"协助注入点击必须达到不低于日常点击的合成拟人度"），MUST NOT 谎称使用了轨迹。风控语义（detected→restricted、cleared 不自动回 normal、只有真实清除才发 `risk.captcha_cleared`）MUST 保持不变。

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
- **THEN** MUST 沿用既有 `settle → reprobe → still_blocked / failed / 回传新截图` 回执，MUST NOT 因拟人化改动而静默假成功；只有真实清除才发 `risk.captcha_cleared`

### Requirement: 小红书笔记访问限制弹窗不得作为账号级验证码事故上报

边缘 SHALL 识别小红书 Web 笔记访问限制弹窗（如 `access-modal`、`access-limit-app`、文案“当前笔记暂时无法浏览 / 请打开小红书App扫码查看”）为可恢复的笔记访问限制状态，而非账号登录墙、验证码或未知账号级阻断。该类弹窗出现时，边缘 MUST NOT 触发 `risk.captcha_detected`、MUST NOT 将浏览命令队列长期暂停为 captcha/unknown；它 MAY 通过关闭浮层或直接导航回健康来源列表恢复。若访问限制发生在正在打开的笔记上，边缘仍须诚实失败或返回列表，MUST NOT 冒充已成功读取该笔记。

#### Scenario: 失效详情路由弹出 access-limit-app
- **WHEN** 小红书页面出现可见 `access-modal` / `access-limit-app`，并包含“当前笔记暂时无法浏览”或“请打开小红书App扫码查看”等文案
- **THEN** 边缘将其分类为非阻断可恢复弹窗，MUST NOT 上报为验证码或 unknown 阻断，后续 `navigation.back` / 返回来源列表命令仍可执行

#### Scenario: 真验证码仍按账号级风控处理
- **WHEN** 页面出现验证码厂商 iframe、滑块/点选验证容器或“安全验证 / 滑动验证 / 请完成验证”等挑战文案
- **THEN** 边缘仍按 captcha 阻断处理并暂停高风险动作，MUST NOT 因 access-limit 兜底放宽真实验证码判断

### Requirement: Facebook 限流文案识别必须覆盖「频率」框架的中文变体，且判据只用长专属句片段

边缘与云端两侧的 Facebook 限流文案判据 MUST 覆盖 Facebook 中文界面的**「频率」框架**限流措辞（如「限制了你发帖、评论或执行其他操作的频率」「我们限制了你发帖」「限制了你执行此操作的频率」），不得只覆盖既有的「封锁 / 不可用」框架（「暂时被限制」「操作被封锁」「你暂时无法使用」「功能暂时不可用」「此功能暂时无法使用」）。

判据 MUST 由**长专属句片段**构成：每条词条 MUST 是足以唯一指认限流语境的整句中段。判据 MUST NOT 包含「限制」「频率」这类在 Facebook 群规则页、隐私设置页等正常页面广泛出现的裸词——因为误报代价与漏报代价严重不对称：一次误报使账号迁入 `restricted` 并钉住其恢复窗、且风控状态按既有语义不自动回滚，只能人工恢复；而一次漏报仅维持现状。

两仓各自维护的词条集合 MUST 语义一致。两侧 MUST 各有单元测试锁住词条集合，使任一侧新增 / 删除词条而另一侧未同步时测试失败——现存漂移（一侧独有的词条因另一侧不上报而成为永不可达的死代码）MUST 在本要求下被消除。

本要求只约束**文案判据的覆盖面与构成纪律**。命中后的 `kind→signal→state` 映射、状态迁移、传输层暂停与恢复语义 MUST 全部维持现状；MUST NOT 新增或改动任何消息类型（两份 `protocol.ts` 消息总数不变）。

#### Scenario: 频率框架的中文限流弹窗被识别为阻断态

- **WHEN** Facebook 页面出现「为让社群免受垃圾信息打扰，我们限制了你发帖、评论或执行其他操作的频率。你可以稍后再试。」这类频率框架文案
- **THEN** 边缘 MUST 将其分类为阻断态并经既有遮罩上报通道上报，MUST NOT 判为无事而静默丢弃

#### Scenario: 正常页面出现的裸词不触发限流判定

- **WHEN** Facebook 群规则页、隐私设置页或其他正常页面中出现「限制」或「频率」等裸词，但不含任何限流句片段
- **THEN** 判据 MUST NOT 命中，账号 MUST 维持既有风控状态，MUST NOT 发出限流上报

#### Scenario: 两仓词条集合漂移被测试拦截

- **WHEN** 任一仓的限流词条集合被新增或删除，而另一仓未同步
- **THEN** 该仓的单元测试 MUST 失败，使漂移从「无人发现」降级为「测试失败」

### Requirement: 判为阻断态的遮罩上报必须携带非空证据文案

当边缘将 Facebook 遮罩判为阻断态并上报时，上报载荷 MUST 携带**非空的证据文案**。边缘 MUST NOT 因遮罩快照的候选筛选落空（弹窗不带 iframe、且未同时满足尺寸阈值与无关闭控件的启发式）而报出**无文案的空壳阻断**。

当快照候选为空导致证据文案缺失时，边缘 MUST 用**分类判定时已取得的同一份页面文本**回填该证据文案，并截断至有界长度。回填 MUST NOT 改变分类判定本身——判定仍完全由既有文案判据在既有文本上完成，回填只决定「已判定为阻断的那一刻随上报携带什么证据」。

本要求存在的理由：云端对无文案的上报按「无文案不臆断限流」返回否定，使一次真实限流只落到最低置信档、仅触发降速而非刹车。证据文案与判定文本不同源时，判据补得再全也不会改变结果。

边缘 MUST NOT 为满足本要求而放宽遮罩快照的 DOM 可信阈（尺寸阈值、关闭控件启发式）——放宽会把良性弹层拖进快照，成倍放大误报面，而误报代价是账号停摆至恢复窗结束且需人工恢复。

#### Scenario: 快照候选为空时证据文案被回填

- **WHEN** 边缘将某遮罩判为阻断态，而遮罩快照的候选筛选结果为空（如标准 Facebook 限流弹窗：无 iframe、尺寸未达阈值、带关闭控件）
- **THEN** 上报载荷的证据文案 MUST 非空，其内容取自分类判定时已取得的同一份页面文本并截断至有界长度

#### Scenario: 回填不改变判定

- **WHEN** 某页面的文本不命中任何限流判据
- **THEN** 该页面 MUST NOT 因证据回填机制而被判为阻断态——回填只在已判定为阻断后生效

#### Scenario: 快照候选非空时沿用原证据

- **WHEN** 遮罩快照的候选筛选正常选出元素、证据文案本就非空
- **THEN** 边缘 MUST 沿用该文案，回填 MUST NOT 覆盖已有证据

### Requirement: 确认的平台限流告警必须以独立类型与更高优先级发出且冷却不跨类型吞没

当云端确认一次上报命中 Facebook 限流文案判据时，其告警 MUST 以**独立于泛化阻断告警的类型**发出，MUST 标注可使运营一眼辨识的标题，且优先级 MUST 高于未命中任何语义判据的泛化未知阻断告警。「已确认限流」这一事实 MUST 透传至告警构造，MUST NOT 在告警构造前被丢弃而使确凿的平台限流与任意不明弹层呈现为同款。

告警冷却 MUST 按**告警类型分维**，MUST NOT 使一种阻断类型的告警在冷却窗内吞没另一种类型的告警。由于告警记录的落库动作位于冷却闸之后，跨类型吞没会同时导致卡片不发**与**记录不落——本要求 MUST 同时消除这两者。

告警路由 MUST 沿用统一口径（来源会话 → 团队群 → 默认群），本要求 MUST NOT 引入任何路由特例。告警类型取值 MUST NOT 要求数据库迁移。

#### Scenario: 确认的限流发出独立类型的高优先级告警

- **WHEN** 云端确认某次上报的证据文案命中 Facebook 限流判据
- **THEN** 告警 MUST 以独立类型发出、标题明确指认为 Facebook 限流阻断、优先级高于泛化未知阻断告警，且面板 MUST 可按该类型过滤

#### Scenario: 未命中判据的未知遮罩仍发泛化告警

- **WHEN** 某未知遮罩上报的证据文案未命中任何限流判据
- **THEN** 告警 MUST 仍按既有泛化阻断类型与优先级发出，行为不变

#### Scenario: 冷却不跨类型吞没

- **WHEN** 同一边缘在冷却窗内先后发生一次验证码告警与一次确认的限流告警
- **THEN** 限流告警 MUST 照常发出且其告警记录 MUST 落库，MUST NOT 被前一条不同类型的告警的冷却吞没

#### Scenario: 同类型冷却行为不变

- **WHEN** 同一边缘在冷却窗内连续发生两次同类型告警
- **THEN** 既有的去重冷却行为 MUST 维持不变

