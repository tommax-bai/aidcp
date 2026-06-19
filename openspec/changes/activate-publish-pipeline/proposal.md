# activate-publish-pipeline

## Why

发帖流水线（`PublishOrchestrator` + 6 角色：ContentScout / ContentCreator / ImageDirector / ContentAssembler / ApprovalGatekeeper / PublishExecutor）已在 `aidcp-cloud` 完整实装并在 `server.ts` 注册，但**生产中空转**——`grep .trigger(` 在生产代码无任何调用方，`orchestrator.trigger()` 仅初始化、从未被激活。整条链路当前只能靠两个 TODO(temp) 调试口（`/debug/publish` HTTP 8788 + CLI `trigger:publish-temp`）手动捅一下，正式触发源缺失。

同时勘察暴露五处必须一并修的硬伤：

1. **两个真 bug（会导致编译/发布残废）**：① `PublishExecutor` 构造 `publish.request` envelope 时**漏填 `title`**，与协议 `PublishRequestPayload` 要求不符（publish-executor.ts:107-117）；② 配图字段名错位——角色侧产出单数 `imageUrl`，协议侧是数组 `images?: string[]`，发图无法端到端打通。
2. **人审默认关**：edge `main.ts:127` 只有 `AIDCP_REAL_PUBLISH === 'true'` 才挂 `approvalGate`，缺省即**旁路飞书人审直接真机发布**，违反 `AC-PUB` 红线（未授权绝不静默发布）。
3. **结果不回写**：edge 发完回传 `publish.result`，但 cloud `handler.ts:209-212` 把它当观测消息丢弃，从不调 `updatePostId()` / `updateStatus()`——`publish_log` 永远停在 `draft`，发布成功/失败的真实状态丢失（一种"静默假成功"变体）。
4. **来源血缘断**：`PublishExecutor` 落库时 `sourceConcepts` 用 `tags` 充数、`sourceLikedIds` 写死 `[]`（server.ts:269-270），帖子来自哪些概念 / 哪些点赞笔记无从追溯。点赞笔记当前**全无持久化**，诚实填 `sourceLikedIds` 缺数据源。
5. **配图被硬拒**：edge `publish-post.ts:294-296` 对任何带图请求直接 `ok:false` 返回，配图链路在边缘端被堵死。

本变更激活触发源、修两个真 bug、把人审改成默认必过、补回写与血缘、删两个临时调试口，让发帖流水线从"能跑但没人按按钮"变成"三扳机自动 + 飞书手动、带图、结果如实回写、来源可追溯"的现役链路。

## What Changes

- **新增 `PublishScheduler`**（cloud）：三扳机任一触发 `PublishOrchestrator.trigger()`——① 概念积累阈值（`ConceptStore` 新概念计数 `newConceptCount ≥ N`）；② 风控允许窗口（`RiskController.getState().status === 'normal'` 且发布配额足）；③ 手动飞书 `/publish` 命令。自动两扳机（①②）**必过 `riskController.canDo('publish')`**；手动 `/publish` 可越过 `canDo`（人工授权），但**任何真机发布仍必过发布前飞书人审**。
- **配图端到端打通**：协议 `imageUrl`（单）→ `images: string[]`（数组）三处同步（edge / cloud 两份 `protocol.ts` 逐字一致 + `command-bridge` 映射核查 + `docs/protocol.md` 头部计数与表）；`ImageDirective.imageUrl → images:[url]` 映射；放开 edge 带图硬拒，补"图片 URL → 下载 → 上传"桥。
- **【BREAKING】人审默认必过**（行为变更）：去掉 edge「不带 `AIDCP_REAL_PUBLISH` 就跳过人审」旁路，条件从 `=== 'true'` 改为 `!== 'false'`——任何真机发布必须飞书 `approved=true` 才点发布；仅显式 `AIDCP_REAL_PUBLISH=false` 才跳过（本地开发）。原先靠"不设环境变量即静默直发"的脚本/调用会被人审拦住，属破坏性行为变更（守住 `AC-PUB` 红线）。
- **`publish.result` 回写 `publish_log`**：cloud `handler.ts` 新增 `publish.result` 回写逻辑——`ok=true → updatePostId()`（`draft/needs_review → published`）、`ok=false → updateStatus('failed')`；关联用信封 id（edge 用原 `publish.request` 的 `env.id` 回填 `publish.result.id`，并透传 `recordId`）。`HandlerDeps` 注入 `publishLogStore`，`server.ts` 初始化时接线。
- **修两个真 bug**：① `publish.request` envelope 补 `title`（来自 `CreatedContent.title`）；② `imageUrl`（单）→ `images[]`（数组）映射修正。
- **来源血缘落实**：`sourceConcepts` = 真概念（来自触发输入 / `ConceptStore`），`sourceLikedIds` = 真点赞 id（不再写死 `[]`）。
- **【BREAKING】新增轻量点赞存储 `LikedNoteStore`**（cloud，新表 `liked_notes`）：在真实 `like` 完成、note 详情可得时落库，为 `sourceLikedIds` 与 `metrics.likedSinceLastPublish` 提供诚实数据源。需补协议 `ActionCompletedPayload.noteId` 字段 + handler 事件透传 + server 订阅落库（涉及协议字段新增，按 BREAKING 评估）。
- **【BREAKING】删两个 TODO(temp) 调试口**：cloud `/debug/publish`（127.0.0.1:8788 HTTP 端口）+ CLI `trigger:publish-temp`（连 `package.json` 脚本）。移除后现网手动触发改用飞书 `/publish` 命令，原依赖这两个口的联调/脚本会失效，属破坏性接口移除。

## Capabilities

### New Capabilities

- `publish-pipeline-activation` — 发帖流水线激活：三扳机触发调度（概念积累 / 风控窗口 / 飞书手动）、人审默认必过的真机发布闸、`publish.result → publish_log` 状态回写、来源血缘（真概念 + 真点赞 id）、配图端到端（协议 `images[]` + 下载上传桥）。

### Modified Capabilities

<!-- 无。现有 7 个 spec（author-profile-visit / browse-loop-resilience / command-pacing / deep-read-fidelity / detail-deep-read / follow-decision / note-extraction-fidelity）均为浏览/互动/风控/节奏相关，无发帖能力 spec；本变更新增能力，不修改既有 spec 需求。 -->

## Impact

- **aidcp-cloud**（主要落点）：
  - 新建 `src/publish-agent/publish-scheduler.ts`（三扳机装置 + `generateTriggerInput()`）。
  - 新建 `src/cache/liked-note-store.ts`（`LikedNoteStore` + `liked_notes` 表 init）。
  - `src/cache/concept-store.ts` 新增 `newCandidateCountSince()` / `queryCandidatesSinceLastPublish()`。
  - `src/publish-agent/publish-log-store.ts` 新增 `getMostRecentPublishTime()` / `getRecentTitles()`；激活 `updatePostId()` / `updateStatus()` 调用链。
  - `src/publish-agent/roles/publish-executor.ts` 补 `title`、改 `imageUrl→images[]`、落库真血缘（concepts/likedIds）。
  - `src/comm/handler.ts` `HandlerDeps` 注入 `publishLogStore`、`publish.result` case 补回写、`action.completed` 透传 `noteId`。
  - `src/server.ts` 接线 `PublishScheduler`、注入 `publishLogStore`、初始化 `LikedNoteStore` 并订阅 `interaction.occurred` 落库；删 `/debug/publish`（74-75、280-301）。
  - `src/feishu/commands.ts` 加 `/publish` 命令（`CommandAction` / `parseCommand` / `CommandActions` / `CommandRouter.handle`）。
  - 删 `src/cli/trigger-publish-temp.ts` 整文件 + `package.json` 脚本行。
- **aidcp-edge**：
  - `src/main.ts:127` 人审条件改 `!== 'false'`；`publish.result` 透传 `recordId`。
  - `src/flows/publish-post.ts` 删带图硬拒（294-296）、新增 `input_images` 步骤与上传循环。
  - 新建 `src/publish/image-upload.ts`（图片下载 + CDP 注入式上传桥）。
  - `src/flows/anchors.ts` 补图片上传锚点。
- **协议三处同步**：edge / cloud 两份 `src/comm/protocol.ts` 逐字一致（`PublishRequestPayload` 补 `recordId`——`title`/`images?: string[]` 已存在、协议本无 `imageUrl`；`PublishResultPayload` 补 `recordId`/`imagesOk`；`PublishApprovalRequestPayload` 补 `images`；`ActionCompletedPayload` 补 `noteId`）+ `aidcp-cloud/src/comm/command-bridge.ts`（核查：`publish.request` 不经 command-bridge 生成，由 `PublishExecutor` 直造，**无需改映射**，仅确认无漂移）+ `docs/protocol.md`（头部计数与 §2 表；本变更仅改 payload 字段、不新增消息类型，计数不变，仅补字段说明）。`imageUrl→images[]` 的"错位"是 executor 构造 envelope 时的 bug（用了协议外的单数 `imageUrl`、漏 `title`），修在 `PublishExecutor`，非协议层。
- **数据**：新增表 `liked_notes`（id / note_id UNIQUE / title / summary / author / liked_at）；`publish_log` 查询新增（`getMostRecentPublishTime` / `getRecentTitles`），激活 `updatePostId` / `updateStatus` 写路径。ECS 部署需建新表。
- **依赖**：
  - **万相（WanxiangClient）**：复用既有 `generate()`（返回公网 CDN URL），无需改；配图链路消费其 URL。
  - **RiskController**：复用 server.ts 既有单例，仅读 `getState()` / `canDo('publish')`，不改写状态（遵守状态单写）。
  - **ConceptStore（依赖 change A）**：change A 已生产部署、`ConceptStore` 已接活；本变更仅**读** `ConceptStore`（`list()` + 新增计数方法），不写、不改其投影逻辑，无冲突。
- **WIP 冲突评估**：与最近提案 `skip-profile-visit-if-followed` **无冲突**——后者只改 `role-dispatcher.ts`（浏览/互动驱动），本变更改发帖驱动（`PublishScheduler` / `PublishExecutor` / 发布相关 handler 分支），两条路径独立，可并行。
- **回归红线**：必须继续守护 `AC-PUB-01/07/08`（审批信号路径与卡片回调）、`AC-PROTO-01/03/04/05`（协议不漂移、信封往返）、`PublishExecutorRole` auto_publish / manual_review 既有断言、`PublishOrchestrator` 完整链路断言；新增 `AC-PUB`（images 映射、人审默认启用、`publish.result` 回写 recordId、图片降级标注）。注：现存遗留 `AC-PROTO-02` 计数（测试穷举 44 vs 协议 47，缺 `notification.*` 三条）超出本变更范围，另行修复。
