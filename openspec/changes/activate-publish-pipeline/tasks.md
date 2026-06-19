# Tasks：activate-publish-pipeline（发帖链路激活）

> **回写格式说明**（实装后用 HTML 注释把对应 task 标 `[x]`）：
> - 单条代码改动：`<!-- <repo> <commit-sha> 备注 -->`，如 `<!-- aidcp-cloud a1b2c3d 补 publishLogStore 注入 -->`。
> - `<repo>` 取 `aidcp-cloud` / `aidcp-edge` / `aidcp`（中控仓）。
> - 偏离设计的实装写清「偏离说明」（设计 file:line 为勘察近似值，行号可漂移、接线点不变；行号偏移不算偏离，逻辑/接口变化才算）。
> - 部署完成在对应 task 追加 `<!-- <YYYY-MM-DD> deployed -->`。
> - 进度按 sub-repo 分节回写本仓；跨仓 task 在各仓注释里分别标 sha。
> - 全部 task 完成 → `openspec validate activate-publish-pipeline --strict` → archive。
>
> **执行铁律**：分三批上线（Migration Plan），但本 tasks.md 内任务顺序即依赖序——协议三处同步 → cloud 接线 → edge 配图 → 验收 → 全量回归 → 部署。每条可独立验证（附验证手段）。改协议/风控/发布后回归纪律：**先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`**（edge / cloud 各一遍）。部署仅 cloud 到 ECS，绝不触碰同机 `isales`，执行前先做 CLAUDE.md §0 私钥与 sub-repo 检查。

## 1. 协议三处同步（先行；改 payload 字段不新增消息类型，守 AC-PROTO）

> 依赖序最前：后续 cloud / edge 代码均依赖新协议字段。三处 = cloud `protocol.ts` + edge `protocol.ts`（逐字一致）+ `docs/protocol.md`。command-bridge 仅核查无需改。

- [ ] 1.1 aidcp-cloud：`src/comm/protocol.ts` `PublishRequestPayload` 补 `recordId: number`（用于 `publish.result` 回写关联，供 edge 回读透传）。**注意：`title` 与 `images?: string[]` 已存在于协议**（实测协议无 `imageUrl` 字段，去掉 `images` 上的「本任务暂不实现」注释即可）；单数 `imageUrl` 仅出现在 executor 构造的 envelope，属 §2.2 executor 修复、**非协议改动**（验证：`tsc --noEmit` 通过；`grep -c imageUrl src/comm/protocol.ts` 为 0；接口含 `recordId`/`title`/`images?`）
- [ ] 1.2 aidcp-cloud：`src/comm/protocol.ts` `PublishResultPayload` 补 `recordId?: number` + `imagesOk?: boolean`（验证：接口含两新字段）
- [ ] 1.3 aidcp-cloud：`src/comm/protocol.ts` `PublishApprovalRequestPayload` 补 `images?: string[]`（验证：接口含 `images` 字段）
- [ ] 1.4 aidcp-cloud：`src/comm/protocol.ts` `ActionCompletedPayload` 补 `noteId?: string`（供 §3 LikedNoteStore 链路；验证：接口含 `noteId` 字段）
- [ ] 1.5 aidcp-edge：`src/comm/protocol.ts` 同步 1.1–1.4 四处改动，与 cloud **逐字一致**（验证：diff cloud/edge 两份对应接口零差异；`grep -c imageUrl` 两份均为 0）
- [ ] 1.6 aidcp-cloud：核查 `src/comm/command-bridge.ts` 无 `publish` case（`publish.request` 由 `PublishExecutor` 直造、不经映射），**确认无需改、无漂移**（验证：`grep -n publish src/comm/command-bridge.ts` 无动作映射条目）
- [ ] 1.7 aidcp（中控仓）：`docs/protocol.md` 确认消息类型总数**不变**（不新增消息类型）；§2 表补 `publish.request` / `publish.approval_request` / `publish.result` 新字段说明 + §3 加三条字段变化说明（`PublishRequestPayload` 加 recordId/title、imageUrl→images[]；`PublishApprovalRequestPayload` 加 images；`PublishResultPayload` 加 recordId/imagesOk；`ActionCompletedPayload` 加 noteId）（验证：头部计数未变、§2 表与 §3 含上述字段）
- [ ] 1.8 aidcp-cloud + aidcp-edge：两仓 `npm run typecheck` 通过，`Record<MessageType, true>` 穷举无漂移（验证：两仓 typecheck 退出码 0）

## 2. aidcp-cloud — 回写 / 触发 / 血缘 / 删 temp 口（依赖 §1）

> 全部依赖 §1 新协议字段已落。子序：先修真 bug + 回写（基础设施），再 LikedNoteStore 链路，再 PublishScheduler 三扳机，最后删 temp 口。

### 2A 修真 bug + executor 补字段 + 来源血缘（先修被依赖项）

- [ ] 2.1 `src/publish-agent/roles/publish-executor.ts`：构造 `publish.request` envelope payload 补 `title`（来自 `CreatedContent.title`）+ `recordId`（来自 `store.insert()` 返回），修真 bug ①（验证：`PublishExecutorRole` 既有断言通过，新断言验 payload 含 title/recordId）
- [ ] 2.2 `src/publish-agent/roles/publish-executor.ts`：配图字段 `AssembledContent.imageUrl` 映射为 `images: imageUrl ? [imageUrl] : undefined`，修真 bug ②（验证：单测验 imageUrl→images[0]、无图时 images undefined）
- [ ] 2.3 `src/publish-agent/roles/publish-executor.ts`：落库 `sourceConcepts` 改为真实概念（来自 `TriggerInput` / `ConceptStore`，**不再用 tags 充数**）（验证：单测验 sourceConcepts 取自触发输入概念关键词、非 tags）
- [ ] 2.4 `src/publish-agent/roles/publish-executor.ts`：落库 `sourceLikedIds` 改为真实点赞 id（来自 `TriggerInput`，**不再写死 `[]`**；无真实点赞时如实为空、不编造）（验证：单测验有点赞输入时填真 id、无点赞输入时为空数组）

### 2B publish.result 回写 publish_log（D2）

- [ ] 2.5 `src/publish-agent/publish-log-store.ts`：确认/补 `updatePostId(recordId, postId)`（`draft/needs_review → published`）与 `updateStatus(recordId, 'failed')`，并暴露 `PublishLogSink` 接口供 handler 注入（验证：单测验两方法 SQL 与状态迁移正确）
- [ ] 2.6 `src/comm/handler.ts`：`HandlerDeps` 新增 `publishLogStore?: PublishLogSink`（验证：`tsc --noEmit` 通过）
- [ ] 2.7 `src/comm/handler.ts`：`case 'publish.result'` 补回写逻辑——`payload.recordId && ok && postId → updatePostId()`；`recordId && !ok → updateStatus('failed')`；try/catch 包裹（回写失败只记日志、不丢消息），**不再当观测消息直接丢弃**（验证：单测验 ok=true 调 updatePostId、ok=false 调 updateStatus、抛错不崩）
- [ ] 2.8 `src/server.ts`：`new DefaultMessageHandler({ ..., publishLogStore })` 注入既有 store 单例（验证：启动无报错、handler 拿到 store 引用）

### 2C LikedNoteStore 点赞落库链路（D6；依赖 1.4 noteId）

- [ ] 2.9 `src/cache/liked-note-store.ts`（新建）：`LikedNoteStore` 类 + `init()` 幂等建表 `liked_notes`（`id` / `note_id TEXT UNIQUE` / `title` / `summary` / `author` / `liked_at`，及 `idx_liked_notes_liked_at` 索引）+ 方法 `recordLike(noteId, title, summary, author?)`（`ON CONFLICT (note_id) DO NOTHING`）/ `recentLikedNotes(since, limit)` / `countSince(since)`（验证：单测对桩 DB 验建表 DDL 与三方法）
- [ ] 2.10 `src/comm/handler.ts`：`case 'action.completed'` emit `interaction.occurred` 时透传 `payload.noteId`（验证：单测验 emit 事件含 noteId）
- [ ] 2.11 `src/server.ts`：`new LikedNoteStore(pgClient)` + `await init()`，订阅 `eventBus.on('interaction.occurred', ...)`——`action==='like' && noteId` 且 note 详情可得（取 `note.detail.arrived` 会话缓存的 title/content/author）时 `recordLike()` 落库；detail 不可得则跳过（诚实优先、宁缺毋假）（验证：单测/集成验点赞且 detail 可得→落库一行，detail 缺→不落库）

### 2D PublishScheduler 三扳机（D1；依赖 2A–2C 的真血缘与落库数据源）

- [ ] 2.12 `src/cache/concept-store.ts`：新增**只读** `newCandidateCountSince(lastPublishTime)` 与 `queryCandidatesSinceLastPublish()`（不改投影/写路径，不碰 change A 逻辑）（验证：单测验计数与查询，写路径无变更）
- [ ] 2.13 `src/publish-agent/publish-log-store.ts`：新增 `getMostRecentPublishTime()` 与 `getRecentTitles()`（供扳机①基准时间与去重）（验证：单测验返回最近发布时间/标题列表）
- [ ] 2.14 `src/publish-agent/publish-scheduler.ts`（新建）：`PublishScheduler` 类 + `generateTriggerInput()`（聚合真概念 + 真点赞 id 为 `TriggerInput`）+ 三扳机装置（① 概念积累阈值 N；② 风控允许窗口 `getState().status==='normal'` 且配额足；③ 手动 `/publish`）；`canTriggerByAuto()` → 自动两扳机**必过** `riskController.canDo('publish')`，false 时 MUST NOT 触发、MUST 如实记录被拒原因、MUST NOT 改写风控状态；手动 `/publish` 越过 canDo 但仍走人审。**MUST 复用 server.ts 既有 RiskController 单例，禁止 `new RiskController()`**（验证：单测验三扳机分流、canDo=false 自动被拒且记录、手动越权仍触发；grep 该文件无 `new RiskController`）
- [ ] 2.15 `src/feishu/commands.ts`：新增 `'publish'` 命令到 `CommandAction` / `parseCommand` / `CommandActions` / `CommandRouter.handle`，路由到 `PublishScheduler` 手动扳机（验证：单测验 `/publish` 解析为 publish action 并触发手动路径）
- [ ] 2.16 `src/server.ts`：实例化 `PublishScheduler`（注入 ConceptStore / RiskController 单例 / PublishOrchestrator / PublishLogStore / LikedNoteStore），挂概念积累与风控窗口扳机，把飞书 `/publish` 路由进来（验证：启动无报错、三扳机均接线、`grep .trigger(` 生产代码有 PublishScheduler 调用方）

### 2E 删两个 temp 调试口（D7；放最后，确保正式触发源已就位）

- [ ] 2.17 `src/server.ts`：删 `/debug/publish` —— `DEBUG_PORT` 读取（约 :74-75）+ 调试 http server 块（约 :280-301）（验证：`grep -rn 'debug/publish\|DEBUG_PORT' src/` 无残留、启动不再监听 8788）
- [ ] 2.18 删 CLI temp 触发口 —— 整文件 `src/cli/trigger-publish-temp.ts` + `package.json` 中 `trigger:publish-temp` 脚本行（验证：文件不存在、`npm run trigger:publish-temp` 报 missing script、`grep -rn trigger-publish-temp` 无残留）

## 3. aidcp-edge — 人审默认必过 + 配图放开 + 上传桥 + 降级（依赖 §1，与 §2 可并行落地、但配图 E2E 压后批上线）

> 子序：先人审默认必过（D3，守 AC-PUB），再回写透传 recordId/imagesOk，再放开配图硬拒 + 上传桥 + 降级。

### 3A 人审默认必过（D3，BREAKING）

- [ ] 3.1 `src/main.ts`：挂 `approvalGate` 条件由 `process.env.AIDCP_REAL_PUBLISH === 'true'` 改为 `!== 'false'`（缺省/非 false 都人审、仅显式 `=false` 跳过）；不改 `approval-gate.ts` / `publish-post.ts` 内既有 `approved===true` 才放行的守护逻辑，仅改挂载条件（验证：`AC-PUB-10` 断言通过——未设变量时 approvalGate 被挂、`=false` 时为 undefined）

### 3B 回写透传（依赖 1.1/1.2 协议字段、cloud 2.5–2.8 回写就绪）

- [ ] 3.2 `src/main.ts`：`onPublishCommand` 从 `publish.request.payload` 取 `recordId`，发布后回传 `publish.result` 时用原 `env.id` 回填 `id`、透传 `recordId`、如实标 `imagesOk`（验证：单测验回传 payload 含 recordId 与 imagesOk、id===原 env.id）

### 3C 配图端到端放开（D4，BREAKING，压最后批上线）

- [ ] 3.3 `src/flows/publish-post.ts`：删带图硬拒（约 :294-296 的 `ok:false` 早返回），改为进入配图流程（验证：单测验带 images 请求不再立即 ok:false 硬拒）
- [ ] 3.4 `src/publish/image-upload.ts`（新建）：图片 URL → 下载 → CDP 注入式上传桥；下载/上传失败抛可捕获错误供降级（验证：单测对桩 CDP 验下载+上传成功路径、失败路径抛错）
- [ ] 3.5 `src/flows/anchors.ts`：补图片上传锚点（文件选择/上传控件）（验证：anchors 含图片上传锚点项）
- [ ] 3.6 `src/flows/publish-post.ts`：新增 `input_images` 步骤 + 上传循环，调 `image-upload.ts`；图片获取/上传失败时**降级纯文字发布**并使 `publish.result.imagesOk=false`，成功则 `imagesOk=true`；**MUST NOT 谎报附图成功、MUST NOT 因图片失败把整次发布伪造成 ok:true 带图成功**（验证：单测验成功附图→imagesOk:true、失败→降级纯文字+imagesOk:false、不谎报）

## 4. 验收断言（新增 AC-PUB-* / 复用 AC-PROTO-*；依赖各自实现 task）

> 新增断言落对应 sub-repo 的 `test/acceptance/`。每条独立可跑。

- [ ] 4.1 aidcp-cloud：`AC-PUB-09` images 映射断言——`PublishRequestPayload` 无 `imageUrl`、仅 `images`；`PublishExecutor` 输出 payload 用 `images[]`（依赖 1.1 / 2.2；验证：`npm run test:acceptance -- AC-PUB-09` 通过）
- [ ] 4.2 aidcp-edge：`AC-PUB-10` 人审默认启用断言——`AIDCP_REAL_PUBLISH` 缺省/非 false 时 `approvalGate` 被挂、仅 `=false` 时 undefined（依赖 3.1；验证：`ac-pub-approval-required` 测试通过）
- [ ] 4.3 aidcp-cloud：`AC-PUB-11` 回写 recordId 断言——`publish.result` 含 recordId 时 handler 调 `updatePostId()`（ok）/`updateStatus('failed')`（!ok）、不丢弃（依赖 1.2 / 2.7；验证：`AC-PUB-11` 通过）
- [ ] 4.4 aidcp-edge：`AC-PUB-12` 图片降级标注断言——图片上传失败降级纯文字且 `imagesOk=false`、绝不谎报 ok 带图成功（依赖 3.6；验证：`AC-PUB-12` 通过）
- [ ] 4.5 aidcp-cloud + aidcp-edge：复用并确认不回归 `AC-PROTO-01/03/04/05`（协议不漂移、信封往返）；两份 protocol.ts 逐字一致断言通过（依赖 §1；验证：两仓 `npm run test:acceptance` 中 AC-PROTO-* 全过）

## 5. 全量回归（依赖 §1–§4 全部实现 + 新断言落地）

> 纪律顺序固定：先 acceptance → 再全量 test → 再 typecheck，edge / cloud 各一遍。安全红线必须全过。

- [ ] 5.1 aidcp-cloud：`npm run test:acceptance` 全过（含 `AC-PUB-*`、`AC-PROTO-*`、`PublishExecutorRole` auto_publish/manual_review 既有断言、`PublishOrchestrator` 完整链路断言不回归）（验证：退出码 0）
- [ ] 5.2 aidcp-cloud：`npm test` 全量通过（验证：退出码 0）
- [ ] 5.3 aidcp-cloud：`npm run typecheck` 通过（验证：退出码 0）
- [ ] 5.4 aidcp-edge：`npm run test:acceptance` 全过（含 `AC-PUB-01/07/08` 审批信号路径与卡片回调不回归 + 新增 `AC-PUB-10/12`）（验证：退出码 0）
- [ ] 5.5 aidcp-edge：`npm test` 全量通过（验证：退出码 0）
- [ ] 5.6 aidcp-edge：`npm run typecheck` 通过（验证：退出码 0）

## 6. 部署（仅 cloud 到 ECS `121.89.85.150`，CLAUDE.md §5 安全序列 + edge 默认人审上线说明）

> 执行前先做 §0 检查：私钥 `~/codes/isales-4.pem` 存在且 `chmod 600`；`../aidcp-cloud` 已在本机。**绝不触碰同机 `isales`**。edge 不部署（本地跑、连 ws://121.89.85.150:8787）。

- [ ] 6.1 ECS 先备份：`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`（验证：备份文件存在且可解压）
- [ ] 6.2 建新表 `liked_notes`：`LikedNoteStore.init()` 幂等建表随启动执行，或部署前手工执行同款 DDL（验证：PG `\dt liked_notes` 存在 + `idx_liked_notes_liked_at` 索引在）
- [ ] 6.3 `rsync` cloud 代码到 ECS（`--exclude .env --exclude node_modules --exclude .git`）（验证：远端代码同步、`.env` 未被覆盖）
- [ ] 6.4 `systemctl restart aidcp-cloud.service`（验证：命令成功返回）
- [ ] 6.5 healthcheck：`active (running)` + 8787 监听 + 飞书长连接已建立 + PG `select 1` 通过 + `liked_notes` 表存在 + 8788 不再监听（temp 口已删）（验证：逐项满足；失败即 6.6 回滚）
- [ ] 6.6 失败回滚：解压最近 `cloud.bak.<ts>.tar.gz` 覆盖 + restart + 重跑 6.5 healthcheck（验证：回滚后服务恢复）
- [ ] 6.7 aidcp（中控仓）：edge 默认人审上线说明——记录 **BREAKING 行为变更**：edge 本地启动起，未显式设 `AIDCP_REAL_PUBLISH=false` 即默认走飞书人审（`approved=true` 才发）；原依赖「不设变量即静默直发」的脚本会被人审拦住；现网手动触发改用飞书 `/publish`（`/debug/publish` 与 `trigger:publish-temp` 已删）。写入 `docs/handoff-*` 现役注记块（验证：handoff 文档含该说明）
