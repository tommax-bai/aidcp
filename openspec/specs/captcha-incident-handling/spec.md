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

