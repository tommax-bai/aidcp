## Why

发帖执行层（A 设计的 S5）当前是**单条 `publish.request` + 边缘整页脚本**：cloud `PublishExecutor` 拼好终稿后下发一条 `publish.request`，边缘 `publishPost()` 在浏览器里**一口气跑完整页发布流程**（进创作页→选模式→传图→填标题/正文→加标签→提交→抓 postId），最后只回一条 `publish.result {ok, postId?, error?}`。

这套地基有三处根本性短板：

- **无法逐字段控制**：cloud 只能整篇下发，控不了「这张图上传参数」「这个标签是否重复」「这次定时发布到几点」等执行细节；想做条件分支（有图才传、过审才提交）只能塞进边缘脚本。
- **无法逐步校验**：边缘一口气跑完，中途某步失败（标题没填进去、标签没加上）外部看不见——只拿到一个粗粒度 `error`，**无法定位失败发生在哪一步**，也无法在失败步停手而不假成功。这与全仓红线「MUST NOT 静默假成功」冲突：整页脚本天然倾向「跑到底再说」。
- **与浏览侧不对齐**：浏览闭环早已是「云端逐条下发参数化原子指令、边缘逐条执行并回报、每步后置校验」（`page.scroll` / `interaction.like` / `profile.open` 等，复用 DOM-first 定位三道闸）；唯独发布层还停在 v1 整页脚本，两套执行模型割裂，定位引擎的后置校验 / 重试升级 / 反污染回写在发布层完全没接上。

本 change 是 **A 重构的【阶段 1 地基】`publish-edge-command-runtime`**：把发帖执行层从「发一条 `publish.request`、边缘整页流程」改造成「cloud 逐条下发参数化原子指令、边缘逐条执行并回报、每步后置校验」，让发布层与浏览侧共用同一套指令驱动 + 定位三道闸的执行模型。**范围严格限定在执行层（S5）**——内容仍由现有 6 角色产出、触发仍用现有 temp 调试口，决策层（内容生产 / 配图 / 质检 / 元数据 / 合规 / 触发器）一概不动，留给后续 stage 2-4。

## What Changes

- **协议：新增通用参数化指令消息（+2，BREAKING）**
  - 新增 `publish.command`（cloud → edge）`{recordId, seq, kind, params}` 与 `publish.command.result`（edge → cloud）`{recordId, seq, kind, ok, value?, error?}`。
  - `kind` 枚举覆盖 A 的 E1-E10：`navigate_entry` / `select_mode` / `upload_image` / `set_cover` / `fill_field` / `add_with_candidate` / `set_option` / `set_schedule` / `submit_publish` / `capture_postId`。
  - **关键：是「一条通用消息 + `kind` 参数」而非「每个 kind 一条消息」**——这是 A 参数化哲学的核心；消息计数因此只 **+2（47 → 49）**，而非 +10。后续新增 kind 只扩 `PublishCommandKind` 枚举与 `params` 联合类型，不动消息定义。
  - **三处同步**（铁律）：两份 `src/comm/protocol.ts`（cloud / edge 逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts` 的动作↔消息映射 + `docs/protocol.md`（头部计数 47→49 + §2 表新增两行 + kind 枚举说明）。
  - **关联键**：`recordId + seq` 是业务级永久关联键（请求/结果配对靠它），`envelope.id` 仅供日志追踪、不用于关联。

- **边缘：实现「指令运行时」（BREAKING——边缘发布流程重构）**
  - `onPublishCommand` 的整页 `publishPost()` 路径，改为 `PublishCommandDispatcher` 逐条分发：每个 `kind` 一个**参数化处理器**，**复用现有 DOM-first 定位引擎**（`LocatingEngine.resolveAndAct` / 三道闸 / `runStep`）做「定位 + 原子操作 + 后置校验」。
  - 逐条执行、逐条回 `publish.command.result`：`ok` / `value` / `error` 如实回报——找不到目标报 `no_target`、后置校验失败报 `post_validation_failed`，**MUST NOT 静默假成功**（红线）。

- **云端：新增 `CommandSequencer` 取代 `PublishExecutor` 的「发一条 `publish.request`」（BREAKING——发布执行层下发模型重构）**
  - `CommandSequencer` 把「终稿 +（占位）元数据」编排成**有序指令序列**，驱动 `send → await result → advance`；某 `kind` 失败到重试上限 → `escalate`（诚实失败、不假成功、不继续后续指令）。
  - `submit_publish` **之前必须过人审**（AC-PUB）：**复用现有审批信号文件机制**（cloud `getApprovalSignalPath` ↔ edge `buildPublishApprovalSignalPath`，路径 `/tmp/aidcp-publish-approve-<requestId>.json` 两端契约一致）；未授权时序列截止在 `submit_publish` 之前，绝不下发提交。
  - `CommandSequencer` 接管 `PublishExecutor` 末段的下发职责（取代 `pusher.pushToEdges(publish.request)` + 无等待）；上游 6 角色产出的终稿仍是 `CommandSequencer` 的输入。

> **BREAKING 说明**：本 change 重构**发布执行层的协议（+2 消息）与边缘发布流程（整页脚本 → 指令运行时）**。`publish.request` / `publishPost()` 的去留与过渡策略由 design.md 定（地基阶段倾向保留旧路径并行，以现有 temp 口仍可触发测试为约束）；协议 +2 对其余消息完全向后兼容。

## Capabilities

### New Capabilities

- `publish-pipeline`: 发帖执行层的**指令驱动运行时**——通用参数化指令协议（`publish.command` / `publish.command.result` + `kind` 枚举覆盖 E1-E10）、边缘逐 `kind` 处理器（复用 DOM-first 定位三道闸做定位 + 原子操作 + 后置校验、如实回报不假成功）、云端 `CommandSequencer`（终稿→有序指令序列、`send→await→advance`、失败重试到顶 escalate、`submit_publish` 前强制人审）。

### Modified Capabilities

<!-- 不修改任何既有 capability 的 requirement。本 change 复用 command-pacing 的 thinkMs/dwellMs（指令可携带，机制不变）、复用 follow-decision 等浏览侧 capability 共享的 DOM-first 定位三道闸（engine 不改），故均不列为 modified；发布执行层此前未沉淀为独立 spec capability，本次以 publish-pipeline 新建。 -->

## Impact

- **aidcp-cloud**
  - 新增 `src/publish-agent/command-sequencer.ts`（`CommandSequencer`：`buildCommandSequence` / `executePublishSequence` / `sendAndWaitResult` / `onResult`，`recordId:seq` pending map + 超时清理）。
  - 改 `src/publish-agent/roles/publish-executor.ts`：末段由「拼 `publish.request` + `pusher.pushToEdges` + 无等待」改为注入并调用 `CommandSequencer.executePublishSequence`；保留 AC-PUB 文件检查作为第一道闸。
  - 改 `src/comm/handler.ts`：新增 `case 'publish.command.result'` → 路由到 `commandSequencer.onResult(payload, env.id)`。
  - 改 `src/comm/protocol.ts`：`MessageType` +2、新增 `PublishCommandPayload` / `PublishCommandKind` / `PublishCommandParams` / `PublishCommandResultPayload`、`PayloadMap` +2。
  - 改 `src/comm/command-bridge.ts`：登记发布指令的动作↔消息映射（保持协议三处同步守护可过）。

- **aidcp-edge**
  - 新增指令运行时（如 `src/flows/publish-command-handlers.ts` + `PublishCommandDispatcher`）：每 `kind` 一个参数化处理器，复用 `src/locating/engine.ts` 的 `LocatingEngine` / 三道闸 / `runStep`。
  - 改 `src/main.ts` `onPublishCommand`：地基阶段新增 `publish.command` 分发路径到 `PublishCommandDispatcher`（与现有 `publish.request → publishPost()` 路径并行，过渡策略见 design）。
  - 改 `src/comm/protocol.ts`：与 cloud 逐字一致同步上述类型。
  - 复用 `src/publish/approval-gate.ts` 的审批信号路径（两端契约不漂移）。

- **协议三处**（铁律，由 `npm run typecheck` 的 `Record<MessageType,true>` 穷举守护 + `AC-PROTO-*` 验收暴露漂移）
  - 两份 `src/comm/protocol.ts`（逐字一致，diff 无输出）；`aidcp-cloud/src/comm/command-bridge.ts` 映射；`docs/protocol.md`（头部计数 47→49 + §2 表 +2 行 + kind 枚举与 `recordId+seq` 关联键说明）。

- **依赖**
  - 强依赖：边缘 `LocatingEngine` 及三道闸（不改其逻辑，只在发布层复用）；现有审批信号文件机制（不改路径契约）。
  - 协议守护：`AC-PROTO-*`（两份 protocol.ts 不漂移）必须仍全过；新增发布层验收 AC（诚实失败 / AC-PUB 闸 / 按序停止 / 关联回报 / 超时清理）。

- **与现有 6 角色的关系**
  - 内容生产链 `ContentScout → ContentCreator → ContentAssembler → ImageDirector → ApprovalGatekeeper → PublishExecutor` **保持不动**；6 角色产出的终稿仍是 `CommandSequencer` 的输入，本 change 只接管 `PublishExecutor` 末段「如何把终稿落到浏览器」的执行模型。

- **与后续 stage 的关系（不属于本阶段，勿拉进来）**
  - stage 2-4：内容生产 / 配图 / 质检角色重拆、元数据维度决策器、合规声明、触发器（`PublishScheduler`）、来源血缘 `LikedNoteStore`、删 temp 调试口——一概不在本阶段。本阶段内容仍由现有 6 角色产出、触发仍用现有 temp 口测试；元数据维度在指令 `params` 中先以**占位**形式预留，由后续 stage 落实决策。
