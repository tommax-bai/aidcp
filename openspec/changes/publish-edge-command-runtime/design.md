# Design — publish-edge-command-runtime（A 重构 · 阶段 1 地基）

> 设计状态：APPROVED FOR IMPLEMENTATION（已融合两份评审：红线缺陷 / 范围隔离 / 协议一致性）。
> 所有 file:line 已对照本机 `../aidcp-cloud` / `../aidcp-edge` 现役代码核对（截至 2026-06-20）；行号随后续提交会漂移，实施前以 `openspec status` / `grep` 复核为准。

## Context

A 设计把发布全链拆成 S1 内容生成 → S2 优化 → S3 元数据评估 → S4 审批 → S5 执行，S5 的每个角色映射到浏览器原子操作 E1-E10。现状里 S5 执行层是**单条 `publish.request` + 边缘整页脚本**：

- cloud 现役发布链是 `PublishOrchestrator` 串起 **6 个角色**——`ContentScout → ContentCreator → ContentAssembler → ImageDirector → ApprovalGatekeeper → PublishExecutor`（`../aidcp-cloud/src/publish-agent/roles/`）。`PublishExecutorRole.handleAutoPublish`（`../aidcp-cloud/src/publish-agent/roles/publish-executor.ts:96-130`）拼好终稿后 `pusher.pushToEdges(envelope)`（同文件 `:119`，envelope type=`publish.request` 见 `:109`），**不等结果**——拿到一个粗粒度 `PublishResult {recordId,status,dispatched,envelope}` 即返回。
- 边缘 `src/main.ts` `onPublishCommand`（`../aidcp-edge/src/main.ts:108`）收到 `publish.request` 后调 `publishPost()`（`:120`，实现在 `src/flows/publish-post.ts`）**整页跑完**，回一条粗粒度 `publish.result {ok, postId?, error?}`（`:147` `client.send('publish.result', …)`）。
- 协议两份 `src/comm/protocol.ts` 当前 `MessageType` **恰 47 条**（cloud `../aidcp-cloud/src/comm/protocol.ts:17-79`、edge `../aidcp-edge/src/comm/protocol.ts:17-79`，逐字一致），`PROTOCOL_VERSION=2`（`:14`），靠 `Record<MessageType,true>` 穷举守护 + `AC-PROTO-*` 防漂移。
- 审批信号文件机制**已存在**：cloud `getApprovalSignalPath(requestId)`（`../aidcp-cloud/src/feishu/ws-receiver.ts:89`）↔ edge `buildPublishApprovalSignalPath(requestId)`（`../aidcp-edge/src/publish/approval-gate.ts:45`），两端契约路径 `/tmp/aidcp-publish-approve-<requestId>.json`。**关联键是 `requestId`（字符串），不是 `recordId`**——发布链已用 `buildPublishApprovalRequestId()` 生成 requestId 走审批流（edge `main.ts` 已调用），本 change 复用该键，不改路径契约。

短板（三处根本性）：

- **无法逐字段控制**：cloud 只能整篇下发，控不了「这张图上传参数」「这个标签是否重复」「这次定时发布到几点」等执行细节；条件分支（有图才传、过审才提交）只能塞进边缘脚本。
- **无法逐步校验**：边缘一口气跑完，中途某步失败外部只拿到粗粒度 `error`，**无法定位失败在哪一步**，也无法在失败步停手。整页脚本天然倾向「跑到底再说」，与全仓红线「MUST NOT 静默假成功」冲突。
- **与浏览侧不对齐**：浏览闭环早已是「云端逐条下发参数化原子指令、边缘逐条执行 + 后置校验」（`page.scroll` / `interaction.like` / `profile.open`，复用 DOM-first 定位三道闸）；唯独发布层停在 v1 整页脚本，两套执行模型割裂，定位引擎的后置校验 / 重试升级 / 反污染回写在发布层完全没接上。

本阶段（地基）只改 S5 执行层的**执行模型**：把整页脚本改成 cloud 逐条下发参数化原子指令、边缘逐条执行 + 后置校验 + 如实回报。决策层（S1-S4 + 触发器）一概不动，留给后续 stage。

## Goals / Non-Goals

### Goals
1. **参数化指令下发**：cloud `CommandSequencer` 把终稿 +（占位）元数据经 `buildCommandSequence` 编排成有序指令序列，逐条下发（支持条件分支：有图才 `upload_image`、过审才 `submit_publish`）。
2. **原子执行与校验**：边缘各处理器复用 `LocatingEngine` 五层编排（守卫→定位→执行→后置校验→晋升）+ 三道闸，无硬编码整页流程。
3. **诚实回报**：`publish.command.result` 完整报 `ok/value/error/details`，绝不静默假成功——找不到目标报 `no_target`、后置校验失败报 `post_validation_failed`（红线）。
4. **AC-PUB 人审强制**：`submit_publish` 前必过授权（复用现有审批信号文件 + 序列内截止双重闸），严格相等 `approved === true`。

### Non-Goals（属后续 stage，勿拉进来）
- **不改 S1-S4**：6 角色（ContentScout/ContentCreator/ContentAssembler/ImageDirector/ApprovalGatekeeper 及 PublishExecutor 的内容决策）保持不动；本阶段只接管 `PublishExecutor` 末段「如何把终稿落到浏览器」的下发模型。
- **不拉入新业务逻辑**：合规检查、质量评估、配额仍由上游决策，`CommandSequencer` 只参数化编排。
- **不重拆角色 / 不做决策器 / 不做触发器**：不重拆内容生产/配图/质检角色、不做元数据维度决策器、不做合规声明、不做触发器（`PublishScheduler`）、不做来源血缘 `LikedNoteStore`、不删 temp 调试口。元数据维度在 `params` 中先以**占位**预留。
- **不修改现有消息**：47 条既有 `MessageType` 全保留，仅新增 2 条（`publish.command` / `publish.command.result`），对其余消息完全向后兼容。
- **不碰 isales / 其他产品线**。

## Decisions

### Decision 1：协议 = 一条通用消息 + kind 参数（非每 kind 一条）

**选择**：✅ 通用消息 `publish.command`（cloud→edge）/ `publish.command.result`（edge→cloud）+ `kind` 参数。消息计数 **47 → 49（+2）**。

| 维度 | 每 kind 一条（57 条） | 通用消息 + kind（选中，49 条） |
| --- | --- | --- |
| 消息计数 | 47+10=57 | 47+2=49 |
| 协议演进成本 | 每新增 kind 改 enum + `PayloadMap` + handler | 仅扩 `PublishCommandKind` 枚举 + `params/value` 联合类型 |
| 云端编排灵活性 | 固定序列，难条件分支 | 逐条下发，支持条件分支 / 重试策略 |
| 验证一致性 | 每 kind 独有 validator | 所有 kind 复用 `LocatingEngine` 五层逻辑 |
| 穷举守护 | 57 条都在 `PayloadMap` | 49 条，`Record<MessageType,true>` 穷举完整 |
| 实施复杂度 | handler 中 57 个 case | `PublishCommandDispatcher` + 处理器 Map |

**理由**：① 消息计数（49）与 `MessageType` 穷举数一致，便于守护验证；② 逐条下发松耦合，支持条件分支与按 kind 的重试策略；③ 后续新增 kind（如 `upload_image` / `set_cover` / `set_option`）仅扩 `PublishCommandKind` 枚举与 `PublishCommandParams` 联合类型，不动消息定义。

**关联键**：`recordId + seq` 为**业务级永久关联键**（请求/结果配对靠它，全局唯一）；`envelope.id` 仅供日志追踪、不用于关联。注意：此 `recordId` 是 `PublishLogStore.insert` 返回的发布记录主键（数字），与 AC-PUB 审批文件的 `requestId`（字符串）是两个不同的键——前者关联指令请求/结果，后者关联人审授权。

**取代接线**：
- 旧：`PublishExecutorRole.handleAutoPublish → pusher.pushToEdges(publish.request) →` 不等待（`publish-executor.ts:107-129`）。
- 新：`PublishExecutorRole.handleAutoPublish → sequencer.executePublishSequence() →` `send publish.command → await publish.command.result → advance`。

### Decision 2：边缘执行架构 = 完全复用 LocatingEngine 五层编排 + 三道闸

**选择**：✅ 完全复用 `../aidcp-edge/src/locating/engine.ts` 的 `LocatingEngine.resolveAndAct`（类在 `:80`，`resolveAndAct` 在 `:96`，`maxAttempts` 缺省 3 在 `:90`）与三道闸，**不在发布层另起一套硬编码整页流程**。

```
PublishCommandDispatcher（新，../aidcp-edge/src/flows/publish-command-handlers.ts）
├── 处理器（kind → 处理器 Map）：
│     NavigateEntryHandler / SelectModeHandler / FillFieldHandler / AddWithCandidateHandler
│     / SetScheduleHandler / SubmitPublishHandler / CapturePostIdHandler
│     （upload_image / set_cover / set_option 协议层登记 kind，处理器实装见 Decision 6 / Open Q1）
│     每个：buildRequest()→ActionRequest, buildValidator()→后置校验, run()→engine.resolveAndAct + 校验 + 组装 result
└── 复用 LocatingEngine（既有，不改）
      ├── 五层：守卫 → 定位 → 执行 → 后置校验 → 晋升
      └── 三道闸：
          R1 后置校验失败不晋升缓存（validator 在 engine.ts:184，失败→ outcome 'no_target' :220）
          R2 重试上限 → escalated（maxAttempts 轮，engine.ts:228 outcome 'escalated'）
          R3 反污染：LLM 新锚点先 cache.stage（engine.ts:190）、确认后 cache.confirmStaged（:191）
      返回 ActionResult {ok, reason, actionId, outcome, attempts}
```

**红线约定（R1 诚实失败的边缘面）**：处理器 `run()` 中
- 若 `result.ok=false` → 立即返回 `PublishCommandResultPayload {ok:false, error:result.reason, details:{actionId,outcome,attempts}}`；
- 后置校验 `validator.validate() === false` → 立即返回 `{ok:false, error:'post_validation_failed'}`，**不伪造 ok=true、MUST NOT `count||1` 兜底**；
- 三道闸完整继承（不改 engine 任何一行）。

落点示意：`FillFieldHandler.run()`——`engine.resolveAndAct(buildRequest())` 取 `result`，`!result.ok` 即回失败；`result.ok` 时再读 DOM 由 `buildValidator()` 做后置校验（DOM 里能读到刚填入内容），校验失败回 `post_validation_failed`、绝不假成功。`AddWithCandidateHandler` 的 candidates 由 cloud `buildCommandSequence` 预生成后随 `params` 下发（见 Decision 3 / Open Q2），边缘只定位点击，不在边缘实时拉候选。

**处理改进建议（评审吸收/驳回）**：
- ❌ **驳回**「`goal` 字段精度」建议：当前 `goal` 是描述性，不影响 LLM 定位准确率（LLM 经 `actionId + anchorHint` 精确定位）。若需优化属后续阶段。
- ✅ **吸收**「`add_with_candidate` validator 难区分 `selectedIndex`」：本阶段保持简化（只校验「标签已加上」），精确到 selectedIndex 的校验留下一版本。
- ✅ **吸收**「tag loop 编排混乱」：明确分工——cloud `buildCommandSequence` 预生成 candidates 后逐条 `add_with_candidate` 下发，边缘只点击。

### Decision 3：云端 CommandSequencer 编排 + 诚实驱动

**选择**：✅ 新增 `../aidcp-cloud/src/publish-agent/command-sequencer.ts`（现不存在），作为独立组件负责编排 + 驱动 + 重试。

```
PublishExecutorRole.handleAutoPublish（publish-executor.ts:96-130）
├─ [AC-PUB 第1道] 读 getApprovalSignalPath(requestId) → approved===true ? continue : 置 status='failed' 返回
├─ sequencer.executePublishSequence(input)
│   ├─ buildCommandSequence():
│   │     navigate_entry → fill_field(title) → fill_field(content)
│   │     → add_with_candidate(tag)×N → [set_schedule? if publishTime]
│   │     → [AC-PUB 第2道：if !input.approvedByUser → 序列截止，submit_publish 不入序列]
│   │     → submit_publish → capture_postId
│   └─ for cmd in sequence: await sendAndWaitResult(cmd); if !result.ok return {ok:false, failedAt:{seq,kind,error}}
└─ return {ok:true, postId} | {ok:false, failedAt}
```

**红线约定**：
1. **AC-PUB 双重闸（R2）**：
   - 第 1 道在 `PublishExecutorRole.handleAutoPublish`（读 `getApprovalSignalPath(requestId)`、`JSON.parse` → `approved === true` 严格相等；文件不存在/解析失败 → `approvedByUser=false` → `status='failed'` 返回，不下发）。
   - 第 2 道在 `CommandSequencer.buildCommandSequence`（加入 `submit_publish` 前检查 `input.approvedByUser`，未授权则序列截止于提交前——`return cmds` 直接返回，调用方再试也生成不出提交指令）。
2. **失败立即停止（R1 的云端面）**：`executePublishSequence` 中某条 `result.ok=false` 即 `return {ok:false, failedAt:{seq:cmd.seq, kind:cmd.kind, error:result.error ?? 'unknown'}}`，后续指令 MUST NOT 下发。
3. **关联与释放**：
   - pending map 以 `key = ${cmd.recordId}:${cmd.seq}` 为业务关联键；条目存 `{recordId, seq, commandId(仅日志), sentAt, timeoutMs, resolve, reject, timeoutHandle}`。
   - `sendAndWaitResult(cmd, timeoutMs=30000)`：下发 `publish.command`、注册 promise + `setTimeout` 超时 `reject` + `pending.delete(key)`（防泄漏）。
   - `onResult(payload, envelopeId)`：按 `${payload.recordId}:${payload.seq}` 查 pending → `clearTimeout` → `pending.delete` → `resolve(payload)`；`envelopeId` 仅日志，不参与查找。

**处理评审 2（吸收）**：
- ✅「时间窗口竞态」：双重闸两处都查 approved 且各自锁定局部变量，中途改文件无法翻转已锁定决策；防文件篡改的库表 + version 强方案留 phase 2。
- ✅「重连状态不一致」：pending promise 已在 cloud 端锁定 approvedByUser 值与待处理项，重连无法影响已发出的 `publish.command`。
- ✅「文件 IO 异常」：容错明确——文件不存在 → `approved=false` → 失败，不假成功、不重试。

**不吸收（属后续阶段）**：❌ 库表替代文件（需 migration、新增表，phase 2）；❌ version + checksum（当前两端 `approved===true` 检查已足够，属过度设计）。

### Decision 4：协议三处同步 + 穷举守护

**同步清单**：

- **C1 cloud `../aidcp-cloud/src/comm/protocol.ts`**：
  - `MessageType` enum（`:17-79` 区域）+2：`| 'publish.command'` / `| 'publish.command.result'`。
  - 新增接口：`PublishCommandPayload {recordId,seq,kind,params,timeoutMs?,reason?}`、`PublishCommandKind`（E1-E10 十枚举 `navigate_entry`/`select_mode`/`upload_image`/`set_cover`/`fill_field`/`add_with_candidate`/`set_option`/`set_schedule`/`submit_publish`/`capture_postId`）、`PublishCommandParams`（按 kind 的联合类型）、`PublishCommandResultPayload {recordId,seq,kind,ok,value?,error?,details?}`（`details:{actionId?,outcome?,attempts?,durationMs?}`）。
  - `PayloadMap`（`Record<MessageType, …>` 穷举表）+2 条目，映射两条新消息。
- **C2 edge `../aidcp-edge/src/comm/protocol.ts`**：与 C1 **逐字一致**（`diff -u` 两份 protocol.ts 的 MessageType / Payload 块无输出）。
- **C3 cloud `../aidcp-cloud/src/comm/command-bridge.ts`**：**无需登记 publish.command 映射**。`command-bridge.edgeCommandToEnvelope`（`:20`）只负责把 `RoleDispatcher` 的浏览闭环 `EdgeCommand`（`scroll→page.scroll`、`profile_open→profile.open`）翻译成 envelope；而 `publish.command` 由 `CommandSequencer.sendAndWaitResult` **直接 `makeEnvelope('publish.command', …)` 构造并 `pushToEdges`**，不经 command-bridge。本阶段对 command-bridge 仅做**核查无漂移**（`grep -n publish src/comm/command-bridge.ts` 应无发布指令映射条目）。
- **C4 本仓 `docs/protocol.md`**：头部消息计数 47→49；§2 表 +2 行；补 `kind` 枚举映射（E1-E10）与「`recordId+seq` 为业务关联键、`envelope.id` 仅日志」说明。

**守护**：`npm run typecheck`（`Record<MessageType,true>` 穷举：两份 protocol.ts 不一致即失败）+ `AC-PROTO-*` 验收（两份 protocol.ts 不漂移、`PayloadMap` 条目数 = `MessageType` 数 = 49）。验收测试断言 `ALL_MESSAGE_TYPES.length === 49`、`Object.keys(PayloadMap).length === 49`。守护落点：双仓现有 `test:acceptance` 的 `AC-PROTO-*` 用例扩到 49 条穷举；可选追加 `diff -u` 两份 protocol.ts 的 CI/pre-commit 检查。

### Decision 5：AC-PUB 人审闸 + 防并发

- **文件路径统一**：`/tmp/aidcp-publish-approve-<requestId>.json`，内容 `{approved:boolean, approvedAt:number, approver?:string}`；复用 cloud `getApprovalSignalPath(requestId)`（`ws-receiver.ts:89`）/ edge `buildPublishApprovalSignalPath(requestId)`（`approval-gate.ts:45`），**两端契约不漂移**（改发布链时这两个函数必须仍产出同一路径）。
- **双重检查 + 严格相等** `approved === true`：信号文件缺失 / 解析失败 / `approved !== true` → `approvedByUser=false` → 失败、不假成功、不重试。
- **防并发**：
  - 时间窗口竞态：两处检查间隔极短且都锁定局部 `approvedByUser`，中途改文件无法翻转已锁定的决策。
  - 重连不一致：pending promise 已锁状态，重连不影响已发出的提交决策。
  - 幂等：`PublishExecutor` 返回 `status='failed'` 后发布记录 status 不再翻转；重新审批需人工改库表或清旧信号文件后重发请求。
- **可观测性**：`PublishExecutor` 与 `CommandSequencer` 两处 AC-PUB 失败都记 warn/error 日志便于审计；`PublishCommandResultPayload.details` 带 `actionId/outcome/attempts` 追踪每条指令；发布记录 status 落最终态（published/failed）。
- **更强方案留 phase 2**：库表 + transaction + version 替代文件（绝对防篡改/竞态），非本阶段。

### Decision 6：边界隔离 — 不碰 S1-S4，仅改 S5 执行

| 范围 | 现役角色 | 本阶段 | 理由 |
| --- | --- | --- | --- |
| S1 内容生产 | ContentScout / ContentCreator / ContentAssembler | 无改动 | `CommandSequencer` 只接收已组装终稿（`AssembledContent`），不参与生产 |
| S1 配图 | ImageDirector | 无改动 | 配图结果作为参数（`imageUrl`），不改 |
| S4 审批 | ApprovalGatekeeper | 无改动 | AC-PUB 是独立人审信号（文件），不干涉该角色的 gate 决策 |
| 触发 | 现有 temp 调试口 / 未来 PublishScheduler | 无改动 | 触发仍走现有 temp 口；本阶段不引入触发器 |
| 发布后回写 | LikedNoteStore / ProvenanceWriter / isales | 无改动 | 本阶段不动；isales 绝不触碰 |

**兼容性 / 过渡**：地基阶段 `publish.request → publishPost()` 旧路径与新 `publish.command` 路径**并行保留**（以现有 temp 口仍可触发测试为约束）；本阶段不删 temp 口、不强制切换。旧路径下线时机由后续 stage 决定。协议 +2 对其余消息完全向后兼容，`PROTOCOL_VERSION` 仍为 2。

**地基阶段处理器范围裁剪**：先落最小可端到端集（`navigate_entry` / `select_mode` / `fill_field` / `add_with_candidate` / `set_schedule` / `submit_publish` / `capture_postId`）；`upload_image` / `set_cover` / `set_option` 在协议层一次性登记 kind，处理器实装可随地基阶段补齐或紧随其后（Open Q1）。选择器以最佳推断起步，未命中如实 `no_target`，必要时按实机 CDP 抓 DOM 校准（沿用 deepread-lineage 实机校准纪律）。

## Risks & Mitigations

| # | 风险 | 触发条件 | 缓解 | 落点 |
| --- | --- | --- | --- | --- |
| V1 | 协议漂移（cloud 改 edge 未同步） | 手改 / 合并冲突 | `Record<MessageType,true>` 穷举 + `AC-PROTO-*` + `diff -u` 两份 protocol.ts | Decision 4 守护；可选 pre-commit / CI `diff` 检查 |
| V2 | 边缘执行超时（定位 LLM 慢、三重试触发） | 网络延迟 / 复杂场景 | `timeoutMs` 随 `publish.command` 下发、可配（缺省 30s） | `sendAndWaitResult(cmd, timeoutMs=30000)` |
| V3 | pending map 泄漏（promise 永不 resolve） | 边缘崩溃 / 断连 | 超时 handler 自动 `pending.delete(key)` + reject + error 日志 | `command-sequencer.ts` 超时 handler |
| V4 | AC-PUB 文件竞态（读 false 中途改 true） | 检查时间窗 | 双重检查 + 严格相等 `approved===true` + 局部变量锁定；库表升级属 phase 2 | Decision 5 |
| V5 | 指令 params 类型错误 | 编排生成违反 `PublishCommandParams` | TS 编译检查 + 各 kind 组合单测 | `npm run typecheck` + 单测 |
| V6 | 新旧路径混用混乱 | 过渡期配置不当 | 地基阶段并行、temp 口测旧路径；切换/下线留后续 stage，文档标记弃用期 | Decision 6 |
| V7 | 选择器实机不命中 | 推断选择器与真实 DOM 不符 | 沿用实机 CDP 抓 DOM 校准纪律，未命中如实 `no_target` 不假成功 | 处理器 `buildRequest`/`buildValidator` |
| V8 | tag loop 编排时机不清 | candidates 预生成时机模糊 | `buildCommandSequence` 中明确预生成 candidates 后逐条 `add_with_candidate` 下发，边缘只点击 | Decision 2 / 3 |

> 注：评审草案中以 MySQL `ENUM` / `UNIX_TIMESTAMP()` 描述的「dispatch_status crash recovery」迁移不落本阶段——本仓持久化是 PostgreSQL（ECS 同机 `aidcp` 库），且崩溃恢复（启动扫描超时中间态）属 phase 2 增强；本阶段以「pending map 内存态 + 超时清理 + 发布记录 status 最终态」覆盖正常失败/超时路径，不引入新表结构。

## Migration Plan

- **本阶段（地基）**：协议 +2（向后兼容、`PROTOCOL_VERSION` 不变）；实现边缘 `PublishCommandDispatcher` 与最小处理器集、cloud `CommandSequencer`；改 `PublishExecutor` 末段接 sequencer（保留 AC-PUB 第 1 道文件检查）；改 `handler.ts` 路由 `publish.command.result`；改 `command-bridge.ts` 登记映射；改 `docs/protocol.md`。新旧路径并行，现有 temp 口仍可触发测旧路径。
- **双仓回归纪律**：`npm run test:acceptance`（先）→ `npm test`（全量）→ `npm run typecheck`。安全红线全过：`AC-PROTO-*`（不漂移）、`AC-PUB-*`（未授权不发布、两端审批路径契约一致）、新增发布层 AC（诚实失败 / 按序停止 / 关联回报 / 超时清理）。
- **部署**：cloud 按 ECS 安全序列（先备份 `/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak` → `rsync --exclude .env --exclude node_modules --exclude .git` → `systemctl restart aidcp-cloud.service` → healthcheck `active(running)` + 8787 监听 + 飞书长连 + PG `select 1` + isales 未触碰 → 失败回滚）；edge 本地发布、连 `ws://121.89.85.150:8787`。部署前先做 §0 私钥（`~/codes/isales-4.pem` `chmod 600`）与 sub-repo 在机检查。
- **回滚**：协议 +2 完全向后兼容；若新路径异常，退回 `publish.request` 旧路径（地基阶段并行保留）即可，无需改 `PROTOCOL_VERSION`。后续若引入 sequencer 开关，可由配置/注入控制是否激活（缺省走新路径）。

## Open Questions

| # | 问题 | 现状 / 倾向 | 时间表 |
| --- | --- | --- | --- |
| Q1 | `upload_image` / `set_cover` / `set_option` 处理器随地基一并实装，还是先登记 kind、处理器紧随其后？ | 倾向地基先落最小可端到端集（navigate/select_mode/fill/add_candidate/set_schedule/submit/capture），传图类处理器随后补；协议层 kind 一次性登记齐全 | 本阶段 / 紧随其后 |
| Q2 | `add_with_candidate` 的 tag 候选由 cloud 预生成还是边缘实时查询？ | 倾向 cloud `buildCommandSequence` 预生成 candidates 后逐条下发；边缘只定位点击（需确认 edge selector 是否支持离线候选） | 本阶段 spike |
| Q3 | `set_schedule` 的 `publishTime` 格式（毫秒时间戳 vs cron）？ | 倾向毫秒时间戳，与后续 S3 元数据格式对齐（待 stage 确认） | 待 stage 确认 |
| Q4 | 旧 `publish.request` / `publishPost()` 何时下线？ | 不在本阶段；地基保留并行，切换/下线由后续 stage 决定 | 后续 stage |
| Q5 | AC-PUB 文件不存在是否需重试 / 人工补审回路？ | 本阶段「不存在→失败不重试」；理想回路（文件不存在→人工审批→写文件→重发请求）属后续 stage | 本阶段确认行为 |
| Q6 | 图片上传失败的重试策略是否云端统一下发？ | `PublishCommandPayload` 预留 `timeoutMs`/`reason`，重试策略字段本阶段不激活；需与 edge-runtime 确认 | Q1 同步 |
