## ADDED Requirements

### Requirement: 通用参数化发布指令协议与三处同步

系统 SHALL 通过一对通用消息驱动发帖执行层：`publish.command`（cloud → edge，payload `{recordId, seq, kind, params, timeoutMs?, reason?}`）下发单条参数化原子指令，`publish.command.result`（edge → cloud，payload `{recordId, seq, kind, ok, value?, error?, details?}`）回报单条执行结果。`kind` MUST 为枚举 `PublishCommandKind`，覆盖 A 的 E1-E10：`navigate_entry` / `select_mode` / `upload_image` / `set_cover` / `fill_field` / `add_with_candidate` / `set_option` / `set_schedule` / `submit_publish` / `capture_postId`。协议 MUST 采用「一条通用消息 + `kind` 参数」而非「每个 `kind` 一条消息」，新增消息计数 MUST 恰为 +2（两份 `protocol.ts` 的 `MessageType` 由 47 增至 49）。两份 `src/comm/protocol.ts` MUST 逐字一致，`aidcp-cloud/src/comm/command-bridge.ts` 映射与 `docs/protocol.md`（头部计数 + §2 表 + kind 枚举说明）MUST 同步登记，漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护暴露。

#### Scenario: 一条通用消息承载所有 kind
- **WHEN** cloud 需要让边缘执行 `fill_field` 与随后的 `submit_publish`
- **THEN** 两步都用同一条 `publish.command` 下发、靠 `kind` 与 `params` 区分，`MessageType` 不为每个 kind 各加一条；两份 `protocol.ts` 的消息总数为 49 且逐字一致，`npm run typecheck` 的穷举守护通过

#### Scenario: 后续新增 kind 不动消息定义
- **WHEN** 后续阶段需支持一个新的执行原子（如某新表单控件）
- **THEN** 只扩 `PublishCommandKind` 枚举与 `PublishCommandParams` 联合类型，`MessageType` 与消息计数维持 49 不变，`publish.command` / `publish.command.result` 两条消息定义不动

#### Scenario: 红线反例——每 kind 一条消息（禁止）
- **WHEN** 有人为 E1-E10 各新增一条独立 `MessageType`（如 `publish.fill_field` / `publish.submit` …）使消息数变成 57
- **THEN** 这违反「一条通用消息 + kind」参数化哲学，MUST 被拒绝；正确做法是仅扩 `PublishCommandKind` 枚举与 `params` 联合类型、消息数维持 49

#### Scenario: 协议三处同步缺一即失败
- **WHEN** 只改了 cloud `protocol.ts` 新增两条消息，未同步 edge `protocol.ts` / `command-bridge` / `docs/protocol.md`
- **THEN** `npm run typecheck` 的 `Record<MessageType,true>` 穷举守护与 `AC-PROTO-*` 报漂移、构建失败，MUST NOT 合并

### Requirement: 边缘指令运行时逐条执行并每条后置校验如实回报

边缘 SHALL 以 `PublishCommandDispatcher` 逐条分发 `publish.command`：每个 `kind` 对应一个参数化处理器，处理器 MUST 复用既有 `LocatingEngine`（`resolveAndAct` 与三道闸：后置校验、重试上限 + 升级、反污染回写）完成「定位 + 原子操作 + 后置校验」，MUST NOT 在发布层另起一套硬编码整页流程绕开定位引擎。每条指令执行后边缘 MUST 按真实结果回报一条对应 `recordId+seq` 的 `publish.command.result`：成功带 `ok:true` 与 `value`，失败带 `ok:false` 与真实 `error`（如 `no_target` / `post_validation_failed`），`details` 带 `actionId/outcome/attempts`。

#### Scenario: 逐条执行逐条回报
- **WHEN** cloud 依次下发 `navigate_entry`、`fill_field(title)`、`fill_field(content)`
- **THEN** 边缘 `PublishCommandDispatcher` 逐条分发到对应处理器，每条经 `LocatingEngine` 定位 + 操作 + 后置校验后回一条带相同 `recordId+seq` 的 `publish.command.result`，`ok/value/error` 反映该条真实结果

#### Scenario: 处理器复用而非绕开定位引擎
- **WHEN** 实现 `fill_field` 处理器
- **THEN** 它构造 `ActionRequest` 交 `LocatingEngine.resolveAndAct` 执行、用 validator 做后置校验、继承三道闸（缓存反污染的 stage→confirm、重试上限→escalated），而非自写 `querySelector` + 直填的整页脚本

#### Scenario: 后置校验失败如实回报
- **WHEN** `fill_field` 执行后读 DOM 校验不到刚填入的内容（后置校验失败）
- **THEN** 边缘回报 `publish.command.result {ok:false, error:'post_validation_failed'}`，`details` 带 `actionId/outcome/attempts`，MUST NOT 回报 `ok:true`

#### Scenario: 红线反例——谎报成功（禁止）
- **WHEN** 某指令找不到目标元素或后置校验失败
- **THEN** 边缘 MUST NOT 伪造 `ok:true` 或用 `count||1` 等兜底掩盖失败；MUST 回报 `ok:false` 与真实 `error`（如 `no_target` / `post_validation_failed`），自愈不自残

### Requirement: 云端 CommandSequencer 编排有序指令并诚实驱动

云端 SHALL 新增 `CommandSequencer`，把「终稿 +（占位）元数据」经 `buildCommandSequence` 编排成有序指令序列，并以 `executePublishSequence` 驱动 `send → await result → advance`。某指令失败时 `CommandSequencer` MUST 重试到上限后 `escalate`（诚实失败：返回 `{ok:false, failedAt:{seq,kind,error}}`），MUST NOT 在失败后继续下发后续指令、MUST NOT 上报假成功。`CommandSequencer` MUST 取代 `PublishExecutor` 末段「发一条 `publish.request` 且不等待」的旧下发模型；上游 6 角色产出的终稿仍为其输入。

#### Scenario: 终稿编排为有序指令序列
- **WHEN** `PublishExecutor` 拿到 6 角色产出的终稿与（占位）元数据
- **THEN** `CommandSequencer.buildCommandSequence` 产出有序序列（如 `navigate_entry → fill_field(title) → fill_field(content) → add_with_candidate(tag)×N → submit_publish → capture_postId`），由 `executePublishSequence` 逐条下发并等待结果再推进

#### Scenario: 失败到重试上限即 escalate 停止
- **WHEN** 10 条指令序列执行到第 5 条，重试到上限仍 `ok:false`
- **THEN** `CommandSequencer` 停止，第 6-10 条 MUST NOT 被下发，返回 `{ok:false, failedAt:{seq:5, kind, error}}`，发布记录最终态为失败

#### Scenario: 红线反例——序列中途失败仍报发布成功（禁止）
- **WHEN** 序列在 `fill_field(content)` 处失败（`ok:false`），但程序仍将整个发布标记为成功 / 继续下发后续指令
- **THEN** 这违反诚实失败红线，MUST NOT 发生；`CommandSequencer` MUST 在该失败步即停、返回 `{ok:false, failedAt}`，不伪造发布成功、不跑到 `submit_publish`

#### Scenario: 红线反例——绕开 sequencer 整页下发（禁止）
- **WHEN** 有人在新路径上保留「`PublishExecutor` 直接 `pusher.pushToEdges(publish.request)` 后不等结果、由边缘整页脚本跑完」
- **THEN** 这是被本阶段取代的旧执行模型，新发布执行 MUST 走 `CommandSequencer` 的逐条 `send→await→advance`，不得在新路径上保留无等待的整页下发

### Requirement: submit_publish 前强制人审闸（AC-PUB）

系统 SHALL 在 `submit_publish` 指令下发前强制通过人审授权，**复用现有审批信号文件机制**（cloud `getApprovalSignalPath` ↔ edge `buildPublishApprovalSignalPath`，路径 `/tmp/aidcp-publish-approve-<requestId>.json`，两端契约 MUST 一致）。授权 MUST 以严格相等 `approved === true` 判定；信号文件缺失、解析失败或 `approved !== true` 时，`CommandSequencer` MUST 在序列中止于 `submit_publish` 之前、绝不下发提交指令、发布记录置为失败，MUST NOT 静默发布。

#### Scenario: 已授权才下发 submit_publish
- **WHEN** `/tmp/aidcp-publish-approve-<requestId>.json` 存在且 `approved === true`
- **THEN** `CommandSequencer` 在序列中加入并下发 `submit_publish`，随后 `capture_postId` 抓取真实 postId

#### Scenario: 未授权时序列截止在提交前
- **WHEN** 审批信号文件不存在 / 解析失败 / `approved !== true`
- **THEN** `CommandSequencer.buildCommandSequence` 截止在 `submit_publish` 之前（不加入提交指令），返回失败，发布记录最终态为失败

#### Scenario: 红线反例——缺省直发（禁止）
- **WHEN** 审批信号缺失（文件不存在）或为 false，但程序把缺省 / 异常当作放行仍下发了 `submit_publish`
- **THEN** 这违反 AC-PUB，MUST NOT 发生；严格相等判定 + 提交前截止 MUST 保证「未明确授权 == 不发布」，缺省与异常一律按未授权处理

#### Scenario: 两端审批信号路径不漂移
- **WHEN** 修改发布链时改动了审批信号文件路径
- **THEN** cloud `getApprovalSignalPath` 与 edge `buildPublishApprovalSignalPath` MUST 仍产出同一路径 `/tmp/aidcp-publish-approve-<requestId>.json`，`AC-PUB-*` 验收 MUST 仍全过

### Requirement: 指令与结果按 recordId+seq 关联

系统 SHALL 以 `recordId + seq` 作为指令与结果配对的**业务级永久关联键**：`publish.command` 与其对应 `publish.command.result` MUST 携带相同的 `recordId` 与 `seq`，`CommandSequencer` MUST 以 `recordId:seq` 为键维护 pending map 并据此配对回报、推进序列。`envelope.id` 仅供日志追踪、MUST NOT 用于业务关联。`CommandSequencer` MUST 在结果到达时按键 resolve 并删除 pending 项；结果在 `timeoutMs`（缺省 30s）内不到达时 MUST reject 并自动清理该 pending 项、记 error 日志，pending map MUST NOT 泄漏。

#### Scenario: recordId+seq 配对请求与结果
- **WHEN** cloud 下发 `publish.command {recordId:100, seq:3, kind:'fill_field'}`，边缘回报 `publish.command.result {recordId:100, seq:3, ok:true}`
- **THEN** `CommandSequencer.onResult` 以 `recordId:seq`（`100:3`）找到对应 pending 项并 resolve，推进到下一条指令

#### Scenario: envelope.id 不用于关联
- **WHEN** 同一发布的多条指令复用或重发导致 `envelope.id` 变化、但 `recordId+seq` 不变
- **THEN** 配对仍以 `recordId+seq` 为准、不受 `envelope.id` 影响；`envelope.id` 仅落日志用于追踪单次请求

#### Scenario: 结果到达即释放 pending 项
- **WHEN** 某 `seq` 的结果正常到达
- **THEN** `onResult` 按 `recordId:seq` 找到 pending 项 resolve 后将其从 map 删除，不残留

#### Scenario: 超时清理不泄漏
- **WHEN** 边缘崩溃 / 断连使某 `seq` 结果在 `timeoutMs`（缺省 30s）内不到达
- **THEN** 该 pending 项超时 reject、自动从 map 清理并记 error 日志，pending map MUST NOT 泄漏
