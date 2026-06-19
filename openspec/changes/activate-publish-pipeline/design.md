# 设计：activate-publish-pipeline（发帖链路激活）

> 本文为发帖流水线激活的技术设计决策稿，已吸收两轮评审（正确性评审 15 项 + 红线评审 5 项，全部采纳、驳回 0 项）。文中 file:line 均为勘察当时的近似位置，实装时以代码实际为准（接线点不变，行号可能漂移）。
> 产品前提（7 项，不可推翻）：① 新增 `PublishScheduler` 三扳机；② 配图端到端打通（`imageUrl→images[]` 三处同步）；③ 人审默认必过（去旁路）；④ `publish.result` 回写 `publish_log`；⑤ 修两个真 bug（补 `title`、`imageUrl→images[]`）；⑥ 来源血缘（真概念 + 真点赞 id）；⑦ 删两个 TODO(temp) 调试口。

## Context

发帖流水线（`PublishOrchestrator` + 6 角色：ContentScout / ContentCreator / ImageDirector / ContentAssembler / ApprovalGatekeeper / PublishExecutor）已在 `aidcp-cloud` 完整实装并在 `server.ts` 注册，但**生产中空转**——`grep .trigger(` 在生产代码无任何调用方，`orchestrator.trigger()` 仅初始化、从未被激活。整条链路当前只能靠两个 TODO(temp) 调试口（`/debug/publish` HTTP 8788 + CLI `trigger:publish-temp`）手动捅，正式触发源缺失。

勘察同时暴露五处必须一并修的硬伤（详见 `proposal.md` ## Why）：两个真 bug（envelope 漏 `title`、配图字段名错位 `imageUrl` vs `images[]`）、人审默认关（缺省即旁路飞书直发，违反 `AC-PUB`）、结果不回写（`publish.result` 被当观测消息丢弃，`publish_log` 永停 `draft`，属"静默假成功"变体）、来源血缘断（`sourceConcepts` 用 `tags` 充数、`sourceLikedIds` 写死 `[]`，且点赞笔记全无持久化）、配图被硬拒（edge `publish-post.ts:294-296` 对带图请求直接 `ok:false`）。

本变更将链路从"能跑但没人按按钮"激活为"三扳机自动 + 飞书手动、带图、结果如实回写、来源可追溯"的现役链路，且**不破坏任何安全红线**（`AC-PUB` 未授权绝不静默发布、`AC-PROTO` 协议不漂移、"MUST NOT 静默假成功"）。

权威约束文档：根仓 `docs/architecture.md`（边轻云重 + 状态单写）、`docs/protocol.md`（协议 v2）、`docs/risk-control.md`（状态机单写）。

## Goals

- **G1 激活触发源**：新增 `PublishScheduler`，三扳机任一触发 `PublishOrchestrator.trigger()`——① 概念积累阈值；② 风控允许窗口；③ 飞书 `/publish` 手动命令。
- **G2 修两个真 bug**：`publish.request` envelope 补 `title`；配图字段 `imageUrl`（单）→ `images[]`（数组）端到端打通。
- **G3 人审默认必过**：edge 人审条件由 `=== 'true'` 改为 `!== 'false'`，缺省即人审，仅显式 `AIDCP_REAL_PUBLISH=false` 才跳过；守住 `AC-PUB`。
- **G4 结果回写**：cloud `handler.ts` 接收 `publish.result` 回写 `publish_log`（`ok→updatePostId`、`!ok→updateStatus('failed')`），用 `recordId` 关联。
- **G5 来源血缘**：`sourceConcepts` = 真概念（触发输入 / `ConceptStore`），`sourceLikedIds` = 真点赞 id（新增 `LikedNoteStore` 落库点赞笔记供给）。
- **G6 配图端到端**：协议 `images[]` 三处同步 + edge 放开带图硬拒 + 图片下载/上传桥 + 失败降级纯文字并如实标注 `imagesOk`。
- **G7 删两个 temp 调试口**：`/debug/publish` HTTP 端口 + CLI `trigger:publish-temp`（含 `package.json` 脚本行）。

## Non-Goals

- **NG1 不改风控状态机**：`PublishScheduler` 只**读** `RiskController.getState()` / `canDo('publish')`，绝不改写最终状态（状态单写归 `RiskController`）。
- **NG2 不接 `tempo` 降速旋钮、不接真实平台封号/限流信号**：超出本变更范围（CLAUDE.md §2 已知缺口）。
- **NG3 不改 `ConceptStore` 投影/写路径**：change A 已生产部署，本变更仅读 + 加只读计数方法。
- **NG4 不新增消息类型**：仅改既有 payload 字段，协议消息计数不变（见 D5）。
- **NG5 不修遗留 `AC-PROTO-02` 计数缺口**：测试穷举 44 vs 协议 47（缺 `notification.*` 三条）超范围，另行修复。
- **NG6 不动 `isales`**：ECS 同机另有独立服务，任何部署操作绝不触碰。
- **NG7 不改 command-bridge 映射**：`publish.request` 由 `PublishExecutor` 直造、不经 command-bridge，仅核查无漂移。

## Decisions

### D1 PublishScheduler 三扳机：自动两扳机过 canDo，手动越权但人审必过

**决策**：新建 `aidcp-cloud/src/publish-agent/publish-scheduler.ts`，封装三扳机装置：① 概念积累阈值（`ConceptStore` 新概念计数 `newConceptCount ≥ N`）；② 风控允许窗口（`RiskController.getState().status === 'normal'` 且发布配额足）；③ 手动飞书 `/publish` 命令。任一触发 `PublishOrchestrator.trigger()`。

- 自动两扳机（①②）**必过** `riskController.canDo('publish')`——风控不允许就不自动发。
- 手动 `/publish` **可越过** `canDo`（人工授权语义），但**任何真机发布仍必过发布前飞书人审**（见 D3），所以越权不等于绕过安全闸。

接线点（file:line，实装以实际为准）：

| 决策点 | 文件:行 | 现状 | 改动 |
|---|---|---|---|
| 三扳机装置 | `aidcp-cloud/src/publish-agent/publish-scheduler.ts`（新建） | — | 新建 `PublishScheduler` 类 + `generateTriggerInput()` |
| ①概念计数 | `aidcp-cloud/src/cache/concept-store.ts:88-130` | 有 `list()` / `addCandidate()` | 新增只读 `newCandidateCountSince(lastPublishTime)` / `queryCandidatesSinceLastPublish()` |
| ②风控窗口 | `aidcp-cloud/src/risk/risk-controller.ts:88-95` | 有 `canDo('publish')` | 复用 `server.ts:155-171` 既有单例，只读 |
| ③飞书命令 | `aidcp-cloud/src/feishu/commands.ts:20-145` | 有 `CommandAction`/`CommandRouter` 框架 | 新增 `'publish'` case 到 `parseCommand` / `CommandActions` / `CommandRouter.handle` |
| 自动约束 | `aidcp-cloud/src/publish-agent/publish-scheduler.ts:80-120` | — | `canTriggerByAuto()` → `canDo('publish')` |
| 接线 | `aidcp-cloud/src/server.ts` | 仅 `new PublishOrchestrator()` 注册 | 实例化 `PublishScheduler`、挂概念/风控扳机、把 `/publish` 命令路由进来 |

**备选与理由**：
- **备选 A：触发逻辑塞进 `server.ts` 内联**——驳回。三扳机 + 约束检查逻辑复杂且需单测，内联进 `server.ts` 不可测、违反"DOM-first 可换接口"同源的可测性原则。独立类便于注入桩跑无浏览器单测。
- **备选 B：复用旧 `Planner` 单体调度**——驳回。`Planner` 已废弃（CLAUDE.md §2 已删旧文件清单），现役是事件驱动多 Agent + `RoleDispatcher`，不在遗留路径上改代码。
- **采纳理由**：独立 `PublishScheduler` 类，三扳机显式分流、自动过 `canDo` / 手动越权但人审兜底，既满足产品"手动可越权"又守住 `AC-PUB`。

### D2 publish.result 回写：补 recordId 关联 + handler 接线 + store 注入

**决策**：edge 发完回传 `publish.result` 时透传 `recordId`（取自 `publish.request.payload.recordId`），cloud `handler.ts` 用 `recordId` 回写 `publish_log`——`ok=true→updatePostId()`（`draft/needs_review → published`），`ok=false→updateStatus('failed')`。`HandlerDeps` 注入 `publishLogStore`，`server.ts` 初始化时接线。

回写链路（file:line）：

1. `aidcp-cloud/src/publish-agent/roles/publish-executor.ts:97-117` —— `store.insert(record)` 拿 `recordId`，构造 envelope `payload` 补 `recordId` + `title`、改 `imageUrl→images[]`：
   ```
   payload = { recordId, title, content, tags, images?: imageUrl ? [imageUrl] : undefined }
   ```
2. edge 接 `publish.request`，执行发布拿 `postId`，回传 `publish.result`：`{ id: env.id, payload: { ok, postId?, error?, recordId, imagesOk } }`（`aidcp-edge/src/main.ts:106-146`，透传 `recordId`、如实标 `imagesOk`）。
3. cloud `aidcp-cloud/src/comm/handler.ts:209-225` `case 'publish.result'`：
   ```
   if (payload.recordId && deps.publishLogStore) {
     if (payload.ok && payload.postId) await publishLogStore.updatePostId(payload.recordId, payload.postId);
     else if (!payload.ok) await publishLogStore.updateStatus(payload.recordId, 'failed');
   }  // try/catch 包裹：回写失败只记日志、不丢消息
   ```
4. `aidcp-cloud/src/comm/handler.ts:55-70` `HandlerDeps` 新增 `publishLogStore?: PublishLogSink`。
5. `aidcp-cloud/src/server.ts:176-187` `new DefaultMessageHandler({ ..., publishLogStore })`。

**备选与理由**：
- **备选 A：用 envelope id 关联（不传 recordId）**——驳回。`publish_log` 主键是自增 `id`（`recordId`），envelope id 是消息层 uuid，二者无映射；要查回得另存一张映射表，徒增复杂度。直接透传 `recordId` 最简。
- **备选 B：cloud 侧用内存表暂存 envelopeId→recordId**——驳回。断连/重启即丢，违反"结果如实回写"。透传 `recordId` 无状态、重启安全。
- **采纳理由**：`recordId` 随 envelope 往返，handler 无状态回写，断连重启安全，且彻底消除"`publish_log` 永停 draft"的静默假成功变体。

### D3 人审默认必过：AIDCP_REAL_PUBLISH 条件 === 'true' 改 !== 'false'（BREAKING）

**决策**：`aidcp-edge/src/main.ts:127` 把挂 `approvalGate` 的条件从 `process.env.AIDCP_REAL_PUBLISH === 'true'` 改为 `!== 'false'`：
```
const approvalGate = process.env.AIDCP_REAL_PUBLISH !== 'false'
  ? { requestId, pollIntervalMs, timeoutMs, consumeSignal }
  : undefined;
result = await publishPost(..., approvalGate);
```
语义：缺失或任何非 `'false'` 值 → 人审必过（默认）；仅显式 `'false'` → 跳过人审（本地开发）。`AC-PUB` 红线由既有 `aidcp-edge/src/publish/approval-gate.ts:82-149`（仅 `approved === true` 才放行）+ `aidcp-edge/src/flows/publish-post.ts:245-250`（未批返回 `approval_rejected_or_timeout`）守护，无需改这两处逻辑，仅改挂载条件。

**为何破坏性**：原先靠"不设环境变量即静默直发"的脚本/调用会被人审拦住——这正是要修的旁路，破坏性是预期且必要的。

**备选与理由**：
- **备选 A：删掉环境变量、永远人审**——驳回。本地开发联调需要一个显式逃生口，否则每次测试都要走飞书。保留 `=false` 显式旁路兼顾安全与开发体验。
- **备选 B：默认 `true`（人审）但用别的变量名做旁路**——驳回。复用既有变量名，向后兼容（已设 `=true` 的脚本行为不变），不引入新约定。
- **采纳理由**：默认安全（不设/设非 false 都人审，符合 `AC-PUB`）+ 显式旁路（仅 `=false`，不会无意旁路）+ 向后兼容（已设 `=true` 行为不变）。新增 `AC-PUB-10` 断言守护（缺省时 `approvalGate` 必被挂）。

### D4 配图端到端：协议改 images[] + edge 放开硬拒 + 下载上传桥 + 降级标注

**决策**：
1. 协议字段：`PublishRequestPayload` 把 `imageUrl?: string` 改为 `images?: string[]`；`PublishApprovalRequestPayload` 补 `images?: string[]`；`PublishResultPayload` 补 `imagesOk?: boolean`（如实标注图片上传是否成功）。两份 `protocol.ts` 逐字一致（D5）。
2. 角色侧映射：`PublishExecutor` 把 `AssembledContent.imageUrl` 映射为 `images: imageUrl ? [imageUrl] : undefined`（`aidcp-cloud/src/publish-agent/roles/publish-executor.ts:107-117`）。万相 `WanxiangClient.generate()` 返回公网 CDN URL，配图链路直接消费，无需改万相。
3. edge 放开硬拒：删 `aidcp-edge/src/flows/publish-post.ts:294-296` 的带图 `ok:false`，新增 `input_images` 步骤 + 上传循环；新建 `aidcp-edge/src/publish/image-upload.ts`（图片下载 + CDP 注入式上传桥）；`aidcp-edge/src/flows/anchors.ts` 补图片上传锚点。
4. 降级：图片获取/上传失败则降级纯文字发，`publish.result.imagesOk=false` 如实标注（不静默假成功）。

**备选与理由**：
- **备选 A：cloud 把图片下载成 base64 直传 edge**——驳回为默认，列为可选增强。edge 拿 CDN URL 自行下载更省协议带宽，且与现有"边缘做原子操作"分工一致；base64 直传仅在 edge 无外网下载能力时作为后备。
- **备选 B：协议保留单数 `imageUrl`**——驳回。协议侧本就是数组语义（`images?: string[]`），单数是 bug 源头；小红书支持多图，数组面向未来。
- **采纳理由**：协议统一为数组、边缘自行下载上传、失败如实降级标注，三者闭合配图链路且不破坏"边轻云重"与"不静默假成功"。

### D5 协议三处同步 + 不新增消息类型（守 AC-PROTO）

**决策**：协议改动仅涉及 payload 字段，**不新增消息类型**，故消息计数不变。三处同步：
- `aidcp-cloud/src/comm/protocol.ts` 与 `aidcp-edge/src/comm/protocol.ts` **逐字一致**：
  - `PublishRequestPayload`（cloud `:352-361` / edge `:348-357`）补 `recordId: number`。**实测：协议 `title` 与 `images?: string[]` 已存在、协议本无 `imageUrl`**——故"`imageUrl→images[]`"仅是 `PublishExecutor` 构造 envelope 的修复（见 D2/D4），协议层只需新增 `recordId`（并去掉 `images` 的「本任务暂不实现」注释）。
  - `PublishResultPayload`（cloud `:364-371`）补 `recordId?: number` + `imagesOk?: boolean`。
  - `PublishApprovalRequestPayload`（cloud `:264-275` / edge `:261-272`）补 `images?: string[]`。
  - `ActionCompletedPayload`（cloud `:483-487`）补 `noteId?: string`（供 D6）。
- `aidcp-cloud/src/comm/command-bridge.ts`：**核查无需改**——`publish.request` 由 `PublishExecutor` 直造、不经 command-bridge 映射（grep 无 publish case，符合预期）；仅确认无漂移。
- `docs/protocol.md`（根仓）：消息类型总数**不变**；§2 表补 `publish.request` / `publish.approval_request` / `publish.result` 的新字段说明 + §3 字段变化说明三条。

**备选与理由**：
- **备选 A：把回写做成新消息 `publish.backfill`**——驳回。徒增一条消息类型、破坏计数、还要补 command-bridge 映射；复用 `publish.result` 透传 `recordId` 零新增消息。
- **采纳理由**：零新增消息类型 → 计数不变 → 不触动 `AC-PROTO-02` 既有计数缺口、不新增漂移面；`Record<MessageType,true>` 穷举 + `npm run typecheck` 仍是漂移防线。

### D6 LikedNoteStore：补 noteId 事件链路落库点赞笔记（BREAKING）

**决策**：新建 `aidcp-cloud/src/cache/liked-note-store.ts`（`LikedNoteStore` + 新表 `liked_notes`），在真实 `like` 完成且 note 详情可得时落库，为 `sourceLikedIds` 与 `metrics.likedSinceLastPublish` 提供诚实数据源。补完整事件链路：

1. 协议：`ActionCompletedPayload` 补 `noteId?: string`（`aidcp-cloud/src/comm/protocol.ts:483-487`）——属协议字段新增，按 BREAKING 评估。
2. handler 透传：`aidcp-cloud/src/comm/handler.ts:193-207` `case 'action.completed'` emit `interaction.occurred` 时带上 `noteId`。
3. server 订阅落库：`aidcp-cloud/src/server.ts:175+` `eventBus.on('interaction.occurred', ...)`，若 `action === 'like'` 且有 `noteId`，从会话缓存（`note.detail.arrived` 缓存的 note detail）取 title/content/author 落库。
4. 初始化：`aidcp-cloud/src/server.ts:220+` `new LikedNoteStore(pgClient)` + `init()`，注入 handler。

表结构：
```
CREATE TABLE IF NOT EXISTS liked_notes (
  id SERIAL PRIMARY KEY,
  note_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  author TEXT,
  liked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_liked_notes_liked_at ON liked_notes(liked_at DESC);
```
方法：`recordLike(noteId, title, summary, author?)`（`ON CONFLICT (note_id) DO NOTHING`）、`recentLikedNotes(since, limit)`、`countSince(since)`。

**备选与理由**：
- **备选 A：`sourceLikedIds` 继续写死 `[]`**——驳回。违反产品决策⑥来源血缘，且"数据缺失不得误判"红线要求诚实。
- **备选 B：从浏览会话内存里抓点赞 id、不落库**——驳回。会话结束即丢，跨会话/重启的血缘追溯断；轻量表落库是诚实数据源的最小代价。
- **备选 C：复用现成 note 缓存表**——驳回（若不存在专用表）。点赞是有业务语义的事件（唯一约束 + 时间序），独立轻量表语义清晰、查询高效。
- **采纳理由**：最小新表 + 完整事件链路（协议 noteId → handler 透传 → server 订阅落库）补齐数据源，诚实填 `sourceLikedIds`，不破坏状态单写（只新增 liked_notes 写，不碰风控/概念投影）。

### D7 删两个 temp 调试口（BREAKING）

**决策**：
- 删 `/debug/publish` HTTP 端口：`aidcp-cloud/src/server.ts:74-75`（`DEBUG_PORT`）+ `:280-301`（调试 http server 块）。
- 删 CLI `trigger:publish-temp`：整文件 `aidcp-cloud/src/cli/trigger-publish-temp.ts` + `aidcp-cloud/package.json` 脚本行（`~:18`）。

移除后现网手动触发改用飞书 `/publish` 命令（D1③）。原依赖这两个口的联调/脚本会失效，属破坏性接口移除。

**备选与理由**：
- **备选 A：保留调试口、仅加鉴权**——驳回。两个 TODO(temp) 口本就是临时绕过正式触发源的产物；正式触发源（三扳机 + 飞书命令）一旦到位，调试口即冗余且是 `AC-PUB` 旁路风险面，应删干净。
- **采纳理由**：正式触发源就绪后删临时口，缩小攻击/旁路面，符合"激活后清理脚手架"。

## Risks / Trade-offs

> 评审已确认的关键风险（R1–R5 来自红线评审，全部修正落地于上文 Decisions）。

- **[风险 R1] 手动越权缺人审（违反 AC-PUB）** → **[缓解]** D3：`AIDCP_REAL_PUBLISH !== 'false'` 默认挂 `approvalGate`，仅显式 `=false` 旁路；新增 `AC-PUB-10` 断言守护（`aidcp-edge/test/acceptance/ac-pub-approval-required.test.ts`）。
- **[风险 R2] publish.result 回写链路完全缺失（静默假成功变体）** → **[缓解]** D2：handler `case 'publish.result'` 补 `updatePostId()`/`updateStatus()` + `HandlerDeps` 注入 `publishLogStore` + `server.ts` 接线；新增 `AC-PUB-11` 断言（含 `recordId`、handler 调 update）。
- **[风险 R3] 配图 imageUrl→images[] 协议混乱** → **[缓解]** D4/D5：`PublishRequestPayload` 统一为 `images[]`，`PublishExecutor` 改映射，两份 protocol.ts 逐字一致；新增 `AC-PUB-09` 断言（payload 无 `imageUrl`、仅 `images`）。
- **[风险 R4] 协议计数破坏（AC-PROTO）** → **[缓解]** D5：仅改 payload 字段、不新增消息类型，计数不变；`docs/protocol.md` 仅补字段说明；`Record<MessageType,true>` 穷举 + `npm run typecheck` 防漂移。
- **[风险 R5] LikedNoteStore 无法落库（事件链路不完整）** → **[缓解]** D6：补 `ActionCompletedPayload.noteId` + handler emit 透传 + server 订阅落库，三段链路闭合。
- **[风险 R6] publish.result 丢失，publish_log 永停 draft** → **[缓解]** handler 回写包 try/catch（失败只记日志不丢消息）；运维侧加定时清理作业（每小时扫 `draft` 龄 >2h 标记告警），作为兜底监控（非本变更阻塞项，列入 Open Questions）。
- **[风险 R7] 手动 /publish 频繁发布触发风控 frozen** → **[缓解]** 手动越权语义即"人工担责"；文档明示 `/publish` 越 `canDo` 但频繁使用会被风控冻结；自动两扳机仍受 `canDo` 约束不会失控。
- **[风险 R8] Edge 图片上传能力不成熟** → **[缓解]** D4 降级：图片下载/上传失败则纯文字发、`imagesOk=false` 如实标注，绝不静默假成功；新增 `AC-PUB-12` 断言。
- **[风险 R9] 删 /debug/publish 影响现网联调** → **[缓解]** 改用飞书 `/publish` 命令做手动触发测试，能力等价且经人审；删除与触发源就绪同批上线，无空窗。
- **[Trade-off] 拆三 Change vs 单 Change** → 选拆三个（见 Migration Plan）：基础设施/协议（低风险）先行、调度（中风险）次之、配图 E2E（高风险）压后，缩小每批 blast radius、便于独立回滚；代价是协议字段先落但暂无消费方（短期无害，类型穷举保证一致）。

## Migration Plan

分三个 Change 分阶段上线，每批独立验收 + 可独立回滚。

**Change 1：基础设施与协议（M 级 / 低风险）**
- 两份 `protocol.ts` 三处字段同步（`recordId`/`title`/`images[]`/`imagesOk`/`noteId`）+ `docs/protocol.md` 字段说明（计数不变）。
- `HandlerDeps` 补 `publishLogStore`；`handler.ts` `case 'publish.result'` 补回写；`action.completed` 透传 `noteId`。
- 删两个 temp 调试口（D7）。
- 验收：`AC-PROTO-01/03/04/05`（不漂移、信封往返）+ 新增 `AC-PUB-09/11`。

**Change 2：PublishScheduler 与自动触发（H 级 / 中风险）**
- `PublishScheduler` 类 + 三扳机接线；飞书 `/publish` 命令；`ConceptStore.newCandidateCountSince()`；`server.ts` 接线 + `interaction.occurred` 订阅 + `LikedNoteStore` 初始化落库。
- 验收：概念积累触发 / 飞书命令触发 / 风控约束 / `LikedNoteStore` 落库 / `sourceConcepts` 真概念 + 新增 `AC-PUB-10`（人审默认启用）。

**Change 3：配图 E2E 打通（H 级 / 高风险）**
- edge 删带图硬拒（`publish-post.ts:294-296`）+ `input_images` 步骤 + `image-upload.ts` 下载上传桥 + `anchors.ts` 锚点；cloud 图片下载 base64 为可选后备。
- 验收：带图不硬拒 / 失败降级纯文字 / `imagesOk` 如实标注 + 新增 `AC-PUB-12`。

**回归红线（每批必过）**：`AC-PUB-01/07/08`（审批信号路径与卡片回调）、`AC-PROTO-01/03/04/05`、`PublishExecutorRole` auto_publish/manual_review 既有断言、`PublishOrchestrator` 完整链路断言。纪律：先 `npm run test:acceptance`，再全量 `npm test`，再 `npm run typecheck`（edge / cloud 各一遍）。

**部署**（仅 cloud 到 ECS `121.89.85.150`，按 CLAUDE.md §5 安全序列）：
- Change 2 起需建新表 `liked_notes`（`LikedNoteStore.init()` 幂等建表，或随部署执行 DDL）。
- 序列：sub-repo 测试过 → ECS 先备份（`cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（exclude `.env`/`node_modules`/`.git`）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连 + PG `select 1` + `liked_notes` 表存在）→ 失败即回滚。绝不触碰同机 `isales`。

**回滚步骤**：
```
# 按 Change 粒度回滚（高风险 Change 3 可单独 revert）
git revert <commit-sha-change-3>   # 配图 E2E（边缘改动，回滚后退回纯文字发）
git revert <commit-sha-change-2>   # 调度（回滚后退回无自动触发，但协议/回写仍在）
git revert <commit-sha-change-1>   # 协议/基础设施（最后回滚）
# 数据回滚：liked_notes 为新增表，回滚代码后表可保留（无外键依赖、不影响旧路径）；
#           如需彻底回滚 DROP TABLE liked_notes（数据可弃，仅血缘补充）。
# 部署回滚：ECS 解压最近 cloud.bak.<ts>.tar.gz 覆盖 + restart + healthcheck。
# 验证：npm run test:acceptance && npm test && npm run typecheck（edge / cloud 各一遍）。
```

## Open Questions

- **OQ1 概念积累阈值 N 取值**：①扳机的 `newConceptCount ≥ N` 中 N 暂未定（影响自动发帖频率）；建议初值保守（如 N=20），上线后据风控/质量观测调参。
- **OQ2 发布配额"足"的判定**：②扳机"发布配额足"复用 `effectiveQuotas()` 的哪一档（保守/正常/激进）与具体阈值待定；默认随风控状态 `normal` 取正常档。
- **OQ3 publish_log draft 兜底清理作业**：R6 提到的定时扫 `draft` 龄超时告警是否纳入本变更，还是作为运维侧独立任务？倾向独立任务（非链路阻塞）。
- **OQ4 cloud base64 直传后备是否本期实现**：D4 备选 A 列为可选后备，取决于 edge 实测外网下载图片的稳定性；建议 Change 3 先验证 edge 直接下载，不稳再补 base64 通道。
- **OQ5 note detail 会话缓存可得性**：D6 落库依赖 `note.detail.arrived` 已缓存当前 note；若 like 发生在详情未抵达的边缘场景，`noteId` 有但 title/content 缺——此时落库策略（跳过 vs 仅存 noteId）待定，倾向仅在 detail 可得时落库（诚实优先，宁缺毋假）。
