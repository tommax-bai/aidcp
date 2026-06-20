## Why

A 重构的发帖流水线前三阶段均已落地（committed、cloud 全绿）：

- **stage-1（`publish-edge-command-runtime`）** 把执行层改成指令驱动：协议 `publish.command` / `publish.command.result`（+2，54 条）、边缘 `PublishCommandDispatcher`（`navigate_entry` / `select_mode` / `fill_field` / `add_with_candidate` / `submit_publish` / `capture_postId` 实装；`upload_image` / `set_cover` / `set_option` / `set_schedule` 回 `kind_not_implemented`）、云端 `CommandSequencer`（`buildCommandSequence` / `executePublishSequence` / `sendAndWaitResult` / `onResult` + AC-PUB 双闸），`PublishExecutor` 守卫式接 sequencer。
- **stage-2（`publish-content-media-roles`）** 把生产段拆成 11 角色，稳定边界 `assembledContent` 八字段不变。
- **stage-3（`publish-metadata-compliance-roles`）** 落地 8 个元数据决策角色 + `MetadataAggregator` → 并行键 `publishMetadata`（`topics` / `mentions` / `location` / `collection` / `visibility` / `permissions` / `mode` / `publishTime` / `compliance` / `metadataScore`）；但**纯决策、未应用到边缘、未落库**（stage-3 §5 明确把应用与落库延后到本 stage）。

这套地基已能「**生产一篇带元数据的终稿**」，但还是一条**空转的流水线**——没有触发器拉动它跑、产出的元数据/配图不流向浏览器、来源血缘是假的、人审是默认关的、唯一能跑起来的入口是两个 temp 调试旁路。具体六处缺口：

1. **流水线无生产触发器**：`PublishOrchestrator.trigger()` 生产无调用方，只有 temp 调试口 `/debug/publish`（HTTP）与 CLI `trigger:publish-temp`，且两者都走旧 `publish.request` 整页路径，绕过了 stage-1 的指令驱动与 AC-PUB 闸。
2. **元数据/配图未应用到边缘**：`CommandSequencer.buildCommandSequence` 只发 `navigate_entry` / `select_mode` / `fill_field(title/content)` / `add_with_candidate(topic)×N` / `[submit/capture]`，**不发任何元数据/配图指令**；`publishMetadata` 不流向 executor / sequencer，边缘 `set_option` / `set_schedule` / `upload_image` / `set_cover` 仍回 `kind_not_implemented`，且 v1 路径对带图**硬拒**（`publish-post.ts:294-295`）。
3. **来源血缘断**：`publish_log.source_liked_ids` 写死 `[]`（`server.ts:378`），没有 `LikedNoteStore`、真实点赞内容零落库。
4. **人审默认关**：边缘只有 `AIDCP_REAL_PUBLISH === 'true'` 才挂审批闸（`main.ts:130`），缺省即裸发，违反「未明确授权 == 不发布」。
5. **元数据不落库**：`publishMetadata` 不写 `publish_log`，没有防篡改持久化（stage-3 延后的 §6）。
6. **temp 口旁路未删**：`/debug/publish` 与 `trigger:publish-temp` 仍在，是绕过指令驱动 + AC-PUB 的活旁路。

本 change 是 **A 重构的【收口阶段】**：补齐触发器、把元数据/配图应用到边缘、接通真实来源血缘、人审默认必过、元数据防篡改落库、删除 temp 旁路。收口后，发帖流水线从「空转地基」变成「飞书 `/publish` 或自动扳机拉动 → 生产终稿+元数据 → 经人审 → 逐条指令应用到边缘（含配图/元数据）→ 真实落库+血缘」的闭环。

## What Changes

> 本 change 的全部改动均为 **BREAKING**——它改变发帖流水线的**触发模型、下发指令集、人审默认行为与持久化 schema**，并删除既有 temp 触发旁路。

- **【BREAKING】新增生产触发器 `PublishScheduler`（三扳机）**：任一触发 `PublishOrchestrator.trigger()`：① 概念积累阈值（`ConceptStore` 新概念计数 ≥ N）；② 风控允许窗口（`RiskController.getState().status === 'normal'` 且发布配额足）；③ 手动飞书 `/publish`。自动两扳机（①②）MUST 过 `riskController.canDo('publish')`；手动 `/publish` 可越过 `canDo`（人工授权），**但仍 MUST 过发布前飞书人审**。复用 server 已持久化的 `RiskController` / `ConceptStore` 单例。
- **【BREAKING】删除两个 temp 触发旁路**：删 `server.ts` 的 `/debug/publish` HTTP 端口与 CLI `trigger:publish-temp`（整个 `src/cli/trigger-publish-temp.ts`）；正式触发改为飞书 `/publish`（经 `PublishScheduler` 走指令驱动 + AC-PUB），删后 MUST NOT 存在任何绕过指令驱动 / AC-PUB 的发布入口。
- **【BREAKING】配图 e2e 端到端打通**：边缘实装 `upload_image` / `set_cover`（图 URL → 下载到 `/tmp` → CDP 文件输入桥），放开 v1 带图硬拒；`CommandSequencer` 按 `images` / `cover` 发 `upload_image` / `set_cover`；上传失败 MUST 降级纯文字、`imagesOk` 如实回报（MUST NOT 伪造有图）。
- **【BREAKING】边缘应用元数据指令**：`CommandSequencer` 从 `publishMetadata` 发 `add_with_candidate`（`mention` / `location` / `collection`）/ `set_option`（`visibility` / `permissions` / 各声明）/ `set_schedule`（定时）；边缘实装这些 kind 处理器（替换 `kind_not_implemented`），**每条后置校验、如实回报**。
- **【BREAKING】人审默认必过**：边缘审批闸条件由 `=== 'true'` 改为 `!== 'false'`（仅显式 `AIDCP_REAL_PUBLISH=false` 才跳过）；`submit_publish` 前 MUST 过 `approved === true`（AC-PUB）。
- **【BREAKING】真实来源血缘**：新增 `LikedNoteStore`（`liked_notes` 表），在真实 `like` 完成时落库；发布记录 `sourceConcepts` = 真概念、`sourceLikedIds` = 真点赞 id（不再写死 `[]`）。
- **【BREAKING】元数据落库 + 防篡改（stage-3 延后的 §6）**：`publish_log` 加 `publish_metadata` JSONB + `ai_enforced`；`PublishExecutor` 落库 `publishMetadata`，持久化前若检出 `aiEnforced && !ai` 的篡改态 MUST 拒绝降级并记审计日志（对齐 stage-3 合规红线）。

## Capabilities

### New `publish-pipeline`

> 说明：`publish-pipeline` capability 由 stage-1/2/3 三个 change 引入但**尚未归档**（截至本 change，`openspec/specs/` 下无 `publish-pipeline`，三个前序 change 仍 active）。按 openspec 约定，本 change 的 spec delta 同样写在 `## ADDED Requirements` 下、补充本阶段（触发 + 应用 + 血缘 + 人审 + 落库）的新 requirement；归档时各 change 的 delta 依序合并入同一 `publish-pipeline` spec，requirement 名互不重叠。

- `publish-pipeline`（本阶段补充）：发帖流水线的**触发与收口层**——`PublishScheduler` 三扳机触发（自动扳机过 `canDo('publish')`、手动越权仍过人审）、`CommandSequencer` 把 `publishMetadata` / 配图编排进指令序列、边缘实装元数据与配图 kind 处理器（每条后置校验、失败如实降级不伪造）、`LikedNoteStore` 接通真实来源血缘、人审默认必过（`!== 'false'`）、`publishMetadata` 防篡改落库、删除 temp 触发旁路后无任何绕过指令驱动 / AC-PUB 的入口。

### Modified Capabilities

<!-- 不修改任何已合并 capability 的 requirement。本阶段复用 command-pacing 的 thinkMs/dwellMs（指令可携带、机制不变）、复用 DOM-first 定位三道闸（engine 不改，仅在新 kind 处理器中复用）、复用既有审批信号文件机制（路径契约不漂移）。RiskController 状态机不改（只读 getState / 调 canDo('publish')）。这些既有 capability 均不列为 modified；发布流水线的触发/应用/血缘/落库行为统一收口到 publish-pipeline（本阶段 ADDED）。 -->

## Impact

- **aidcp-cloud**
  - 新增 `src/publish-agent/publish-scheduler.ts`（`PublishScheduler`：三扳机轮询 + `ConceptStore` 新概念计数 + `RiskController.getState()` 监听 + 手动 `/publish` 接入；自动扳机过 `canDo('publish')`，统一调 `PublishOrchestrator.trigger()`）。
  - 新增 `src/publish-agent/liked-note-store.ts`（`LikedNoteStore`：`liked_notes` 表 DDL + 真实 like 落库 + `listSince` 回取点赞 id 供血缘）。
  - 改 `src/cache/concept-store.ts`：补「新概念计数」（如 `countNewSince(ts)` / `getNewConceptsSince(ts)`），供 PublishScheduler 扳机①判定。
  - 改 `src/publish-agent/command-sequencer.ts`：`buildCommandSequence` 扩展，从 `publishMetadata` / 配图 emit `upload_image` / `set_cover` / `add_with_candidate(mention|location|collection)` / `set_option(visibility|permissions|声明)` / `set_schedule`；上传/元数据失败如实降级、不伪造。
  - 改 `src/publish-agent/roles/publish-executor.ts`：读 `publishMetadata`（去掉 `_context` 闲置、加竞态保险）传给 sequencer；落库 `publishMetadata` + `aiEnforced` 防篡改；`sourceLikedIds` 从 `LikedNoteStore.listSince()` 回取。
  - 改 `src/publish-agent/publish-log-store.ts`：`publish_log` 加 `publish_metadata` JSONB + `ai_enforced` 列、INSERT/SELECT 同步。
  - 改 `src/feishu/commands.ts`：新增 `/publish` 指令（手动扳机，接 `PublishScheduler` / `PublishOrchestrator.trigger()`，越过 `canDo` 但仍走人审）。
  - 改 `src/server.ts`：删 `/debug/publish` 端口、`sourceLikedIds: []` 改真实回取、装配 `PublishScheduler` + `LikedNoteStore` 并接 RiskController/ConceptStore 单例；挂 like 事件 → `LikedNoteStore` 落库。
  - 删 `src/cli/trigger-publish-temp.ts`（整文件）+ `package.json` 的 `trigger:publish-temp` 脚本。

- **aidcp-edge**
  - 改 `src/flows/publish-command-handlers.ts`：实装 `upload_image` / `set_cover`（URL → `/tmp` 下载 → CDP 文件输入桥 → 后置校验 → 清理）与 `set_option` / `set_schedule`（`LocatingEngine` 定位开关/单选/时间选择器，按 `optionKind` 路由），替换 `kind_not_implemented`；每条后置校验、如实回报。
  - 改 `src/flows/publish-post.ts`：放开 v1 带图硬拒（`294-295` 的 `images are not supported in phase one`）。
  - 改 `src/main.ts`：审批闸条件 `AIDCP_REAL_PUBLISH === 'true'` → `!== 'false'`（人审默认必过）。
  - 扩 `src/locating/anchors.ts`（或等价锚点声明）：补配图/封面/可见范围/权限/定时/提及/合集等新锚点；复用现有 `LocatingEngine` 三道闸，不改 engine。
  - 改 `src/comm/protocol.ts`：协议层本阶段**不增减消息**（kind/params 已在 stage-1 预留齐），如需补 `optionKind` 枚举值则两份逐字同步。

- **协议**
  - 本阶段**不新增消息**（`publish.command` / `publish.command.result` + `PublishCommandKind` 枚举 stage-1 已覆盖 E1-E10）。若 `set_option` 需补 `optionKind` 枚举/`PublishCommandParams` 字段，MUST 两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge.ts` 映射不变 + `docs/protocol.md` 同步（计数维持 54，仅 kind/params 说明补充）；漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护。

- **DB（ECS PostgreSQL 库 `aidcp`）**
  - `publish_log` 加列：`publish_metadata JSONB`、`ai_enforced BOOLEAN`（DDL `IF NOT EXISTS` 幂等）。
  - 新表 `liked_notes`（点赞内容来源血缘）。
  - 不记敏感值，仅在 tasks/部署文档记 DDL 与服务位置。

- **依赖**
  - 强依赖且不改：边缘 `LocatingEngine` 及三道闸（仅复用做新 kind 定位+后置校验）；既有审批信号文件机制（路径契约不漂移）；`RiskController` 状态机（只读 `getState` / 调 `canDo('publish')`）；server 已持久化的 `RiskController` / `ConceptStore` 单例（复用、不新建实例）。
  - 配图桥引入「URL 下载 + CDP 文件输入」边缘能力（小风险，失败降级纯文字兜底）。
  - 安全红线必须仍全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、`AC-RISK-*`（绝不自残、被禁 `record` 返 false）。

- **与 stage-1/2/3 的关系**
  - stage-1 的 `CommandSequencer` / 指令运行时 / AC-PUB 双闸是本阶段触发与应用的执行底座（扩展其指令集、不破其闸）。
  - stage-2 的 `assembledContent` 八字段稳定边界**保持不变**（本阶段只读，不注入字段）。
  - stage-3 产出的 `publishMetadata` 并行键是本阶段「应用到边缘 + 落库」的输入；stage-3 显式延后的 §5（应用）与 §6（落库）在本阶段收口。stage-3 的合规红线（`aiEnforced` 不可降级）本阶段在落库点强制执行。
  - 三个前序 change 归档时其 `publish-pipeline` delta 与本阶段 delta 依序并入同一 spec，requirement 名互不重叠。

> 拆分说明：本 change 范围为 A 重构收口阶段的**完整六项**（触发 + 配图应用 + 元数据应用 + 人审默认 + 血缘 + 落库），已锁定 B 决策 1-7 一体收口、互为前提（无触发器则 temp 旁路无法删、无 LikedNoteStore 则血缘断、无落库则元数据应用无审计），故不再拆为多个子 change；如实施中发现配图桥（B2）风险超预期需独立验证，可将其降级为「先纯文字闭环 + 配图 follow-up change」——届时本 change 范围收敛为触发+元数据应用+人审+血缘+落库五项，配图应用作为后续 change 在此处 Migration 列出。当前默认六项一体。
