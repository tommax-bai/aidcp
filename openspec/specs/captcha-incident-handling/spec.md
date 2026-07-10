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

协助页提交点击时，cloud SHALL 将点击序列作为归一化坐标发送给该 incident 绑定的原 edge；edge MUST 校验 incident、snapshot、当前阻断态和坐标边界后，将坐标映射回当前浏览器视口并派发真实输入事件。cloud MUST NOT 在自身环境执行点击，MUST NOT 将点击命令广播到多个 edge，MUST NOT 用 DOM 状态篡改替代用户输入。

#### Scenario: 有效点击序列派发到原 edge
- **WHEN** 操作者基于最新 snapshot 提交两个图片点位和一个验证按钮点位
- **THEN** cloud 只向绑定 edge 发送点击命令，edge 将这些点映射到原浏览器并通过输入事件执行

#### Scenario: stale snapshot 拒绝点击
- **WHEN** 操作者基于已过期或已被替换的 snapshot 提交点击
- **THEN** cloud 或 edge MUST 拒绝该点击并返回 `stale_snapshot`，MUST NOT 盲目点击当前页面

#### Scenario: edge 当前不在阻断态
- **WHEN** edge 收到 assist 点击命令但 fresh probe 显示当前已无 captcha/unknown 阻断
- **THEN** edge MUST 不执行点击，并发送或保持 `risk.captcha_cleared` 的正常清除路径

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `risk.captcha_cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `risk.captcha_cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

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

### Requirement: 小红书笔记访问限制弹窗不得作为账号级验证码事故上报

边缘 SHALL 识别小红书 Web 笔记访问限制弹窗（如 `access-modal`、`access-limit-app`、文案“当前笔记暂时无法浏览 / 请打开小红书App扫码查看”）为可恢复的笔记访问限制状态，而非账号登录墙、验证码或未知账号级阻断。该类弹窗出现时，边缘 MUST NOT 触发 `risk.captcha_detected`、MUST NOT 将浏览命令队列长期暂停为 captcha/unknown；它 MAY 通过关闭浮层或直接导航回健康来源列表恢复。若访问限制发生在正在打开的笔记上，边缘仍须诚实失败或返回列表，MUST NOT 冒充已成功读取该笔记。

#### Scenario: 失效详情路由弹出 access-limit-app
- **WHEN** 小红书页面出现可见 `access-modal` / `access-limit-app`，并包含“当前笔记暂时无法浏览”或“请打开小红书App扫码查看”等文案
- **THEN** 边缘将其分类为非阻断可恢复弹窗，MUST NOT 上报为验证码或 unknown 阻断，后续 `navigation.back` / 返回来源列表命令仍可执行

#### Scenario: 真验证码仍按账号级风控处理
- **WHEN** 页面出现验证码厂商 iframe、滑块/点选验证容器或“安全验证 / 滑动验证 / 请完成验证”等挑战文案
- **THEN** 边缘仍按 captcha 阻断处理并暂停高风险动作，MUST NOT 因 access-limit 兜底放宽真实验证码判断

