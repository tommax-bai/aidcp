# Tasks — publish-trigger-and-apply（A 重构收口阶段）

> **依赖序**：协议同步（若有，先行）→ aidcp-cloud（scheduler → conceptstore 计数 → likedstore → sequencer 元数据/配图 emit
> → executor metadata + 落库 → feishu `/publish` + 删 temp）→ aidcp-edge（kind 处理器 + 图片上传桥 → 人审默认 + 放开硬拒）
> → 验收（AC-PUB / AC-PROTO / AC-CMD / AC-RISK）→ 双仓全量回归 → 部署（ECS 安全序列 + edge 本地）。
> cloud 内部序：scheduler 需 conceptstore 计数（task 2）与 likedstore（task 3）就位前可先搭壳，executor 落库（task 5）依赖
> likedstore（task 3）与 log-store 扩列（task 5.4）；edge kind 处理器（task 7）需先扩锚点（task 7.5）。
>
> **回写格式**：task 完成后用 HTML 注释把 `[ ]` 标 `[x]`，写清 commit-sha / 偏离说明 —— `<!-- <repo> <commit-sha> 备注 -->`
> （部署后追加 `<!-- <date> deployed -->`）。进度按 sub-repo 分节回写本仓。
>
> **范围**：本 change 默认六项一体（触发 + 配图应用 + 元数据应用 + 人审默认 + 血缘 + 落库）。若实施中实测配图 CDP 文件输入桥
> 风险超预期，按 design §6 收敛为五项、配图应用降为后续 change（见文末 Migration）。
>
> <!-- 2026-06-20 实施决策：CDP 文件输入桥（DOM.setFileInputFiles）依赖真实浏览器、CI 不可测，按 design §6 / Migration
> 取**五项一体**收敛 —— 本 change 交付「触发 + 元数据应用 + 人审默认 + 血缘 + 落库」；配图应用（upload_image / set_cover /
> 放开带图硬拒 / 配图失败降级 AC-CMD）整体下沉到后续 change `publish-media-upload`。2026-07-03 `publish-media-upload` 已归档，故本 change 中被下沉项以该归档记录收口。 -->

## 0. 协议同步（评估优先；多数情况判定无需改动）

- [x] 0.1 评估 `set_option` 是否需补 `optionKind` 枚举值 / `PublishCommandParams` 字段（design §4：`PublishCommandKind` / `PublishCommandParams` 已含本阶段全部 kind/params，大概率零改动）。验证：`diff <(sed -n '/PublishCommandKind/,/PublishCommandParams/p' ../aidcp-cloud/src/comm/protocol.ts) <(sed -n '/PublishCommandKind/,/PublishCommandParams/p' ../aidcp-edge/src/comm/protocol.ts)` 无输出 <!-- both 89cf903/45922a7 零改动：protocol.ts 已含 candidateKind/optionKind/optionValue/publishTime + 全部 kind，stage-1 已就位 -->
- [x] 0.2 若 0.1 有改动：两份 `src/comm/protocol.ts`（cloud/edge）逐字一致、`aidcp-cloud/src/comm/command-bridge.ts` 映射不变、`docs/protocol.md` 同步（**计数维持 54**，仅补 kind/params 说明）。验证：两仓 `npm run typecheck` 全过 + `AC-PROTO-*`（`test/acceptance/protocol-contract.test.ts`）全过 <!-- N/A：0.1 判定零改动，计数维持 54，两仓 AC-PROTO-02 断言 54 全过 -->

## 1. aidcp-cloud — 触发器 PublishScheduler（缺口①）

- [x] 1.1 新增 `src/publish-agent/publish-scheduler.ts`：三扳机（① 概念积累计数 ≥ N、② 风控允许窗口、③ 手动飞书 `/publish`）任一调 `PublishOrchestrator.trigger()`；自动扳机（①②）硬过 `riskController.canDo('publish')`（false 即不触发），手动 `/publish` 越过 `canDo` 但标记仍走人审。验证：单测覆盖三扳机 + 自动扳机 `canDo=false` 不触发 + 手动越权可触发 <!-- aidcp-cloud 89cf903 publish-scheduler.test.ts 6 测全过（概念阈/canDo=false拦截/风控窗口/skip/手动越权/buildTriggerInput） -->
- [x] 1.2 `PublishScheduler` 接收 server 注入的同一 `RiskController`（`server.ts` 单点初始化）/ `ConceptStore` 单例，**绝不 `new`**（红线：风控状态单写、复用单例）。验证：单测断言用注入实例、无内部实例化 <!-- aidcp-cloud 89cf903 PublishSchedulerDeps 全注入（risk/conceptStore/likedStore/publishLog/orchestrator/soul），scheduler 内零 new -->
- [x] 1.3 总开关 `AIDCP_PUBLISH_SCHEDULER_ENABLED`（**缺省 false**，防误自动发）+ 轮询间隔 `AIDCP_SCHEDULER_INTERVAL_MS`（缺省 30min）；扳机①②低频轮询、扳机③即时。验证：单测断言缺省关闭时自动扳机不触发 <!-- aidcp-cloud 89cf903 偏离：env 名落地为 AIDCP_PUBLISH_AUTO（缺省 false）+ AIDCP_PUBLISH_AUTO_INTERVAL_MIN（缺省 30）；语义一致：缺省关、显式 =true 才轮询，手动 /publish 即时不受开关影响 -->
- [x] 1.4 重入保护：依赖 `PublishOrchestrator.trigger()` 既有「already running, ignoring」，扳机层避免无意义重复唤起。验证：单测断言运行中第二次扳机被忽略 <!-- aidcp-cloud 89cf903 复用 publish-orchestrator.ts:34-35 status==='running' 即 warn 并忽略；scheduler 不另起并发 trigger -->

## 2. aidcp-cloud — ConceptStore 新概念计数（缺口①支撑）

- [x] 2.1 `src/cache/concept-store.ts` 补 `countNewSince(ts)` / `getNewConceptsSince(ts)`；基线取「上次成功发布时间」（从 `publish_log` 最近成功记录读，复用 `publish-log-store.ts` 既有 `ORDER BY published_at DESC LIMIT 1`，可扩为按 status 过滤），首次发布前以服务启动时间 / 全量计数兜底。验证：单测覆盖有新概念 / 无新概念 / 首次发布兜底三路 <!-- aidcp-cloud 89cf903 concept-store.ts:152 countNewSince + :161 getNewConceptsSince（discovered_at > to_timestamp）；基线由 scheduler 经 publish-log getMostRecentPublishTime 提供、首发兜底 null→保守窗口 -->

## 3. aidcp-cloud — LikedNoteStore 来源血缘（缺口③）

- [x] 3.1 新增 `src/publish-agent/liked-note-store.ts`：`liked_notes` 表 DDL（`CREATE TABLE IF NOT EXISTS`，仿 `publish-log-store.ts` 风格）+ 真实 like 落库 + `listSince()` 时间窗回取点赞 id。验证：单测插入后 `listSince` 取回；DDL 幂等（重复建表不报错） <!-- aidcp-cloud 89cf903 偏离：落地路径 src/cache/liked-note-store.ts（与既有 cache/* 同侧，经 cache/index.ts 导出）；方法名 recentSince/countSince（非 listSince），liked_notes(note_id UNIQUE) DDL 幂等 -->
- [x] 3.2 `src/server.ts` 在既有 `eventBus.on('interaction.occurred', ...)` 订阅处（或新增订阅）把 `like` 写 `LikedNoteStore`；accountId 单账号 MVP 取 `DEFAULT_ACCOUNT_ID`（多账号留 follow-up）。验证：模拟 `interaction.occurred(like)` 事件后 `liked_notes` 有记录 <!-- aidcp-cloud 89cf903 server.ts interaction.occurred handler：action==='like' && noteId → likedNoteStore.recordLike(noteId)（try/catch 包裹，PG 缺失不崩） -->

## 4. aidcp-cloud — CommandSequencer 元数据/配图 emit（缺口②）

- [x] 4.1 `src/publish-agent/command-sequencer.ts` `buildCommandSequence` 扩展：从 `publishMetadata` emit `add_with_candidate`（`mention` / `location` / `collection`）/ `set_option`（`visibility` / `permissions` / 各合规声明）/ `set_schedule`（`mode==='scheduled'` 时按 `publishTime`）；按配图 emit `upload_image`×N / `set_cover`。序列序：`navigate_entry → select_mode → upload_image×N → set_cover → fill_field(title/content) → add_with_candidate(topic)×N → add_with_candidate(mention|location|collection)×N → set_option×N → set_schedule → [授权]submit_publish → capture_postId`。验证：`test/publish-agent/command-sequencer.test.ts` 断言序列含元数据/配图指令、顺序正确 <!-- aidcp-cloud 89cf903 元数据 emit 全做：SEQ-08/09 断言 mention/location/collection 经 candidateKind、visibility/declaration_ai 经 set_option、scheduled→set_schedule，全在 submit 前。配图 emit（upload_image/set_cover）DEFERRED→publish-media-upload -->
- [x] 4.2 配图上传失败降级语义已迁移并由 `publish-media-upload` 收口：实机校准后最终口径为「图文全图失败诚实 failed + `images_attached=false` 回正」，而非旧设想的纯文字继续；本 change 不再定义该语义。<!-- fulfilled by archived change 2026-07-03-publish-media-upload tasks 1.3/1.6/6.4 + specs/publish-pipeline -->
- [x] 4.3 AC-PUB 第二闸不变：未授权时元数据/配图指令仍下发（提交前），`submit_publish` / `capture_postId` 截止不入序列（保持 `if (!input.approvedByUser) return cmds;`）。验证：单测断言未授权序列含元数据指令但截止在提交前 <!-- aidcp-cloud 89cf903 SEQ-09 断言未授权含 set_option 但无 submit_publish；AC-PUB 第二闸完整 -->

## 5. aidcp-cloud — PublishExecutor metadata + 落库（缺口②⑤⑥）

- [x] 5.1 `src/publish-agent/roles/publish-executor.ts` 读 `context.get('publishMetadata')`（去掉 `_context` 闲置下划线）传给 sequencer；竞态保险：未就绪时取保守默认（可见范围 `self_only`、不发元数据指令；`METADATA_DEFAULT_VALUES`）或 `context.waitFor('publishMetadata', timeoutMs)`，timeout 后仍取保守默认，**绝不崩溃 / 绝不跳过 AC-PUB 人审 / 绝不伪造成功**。验证：单测覆盖 metadata 就绪 / 未就绪两路，未就绪仍执行授权链 <!-- aidcp-cloud 89cf903 execute(input, context) 读 context.get('publishMetadata')+trigger；未就绪走既有授权链不崩 -->
- [x] 5.2 落库 `publishMetadata` + `ai_enforced`；落库前若检出 `publishMetadata.compliance.aiEnforced === true && ai === false` 的篡改态 → 拒绝降级、强制 `ai=true`、记一条审计日志（对齐 stage-3 `metadata-aggregator` 回正红线）。验证：单测断言篡改态被拒绝、`ai=true` 落库、有审计日志 <!-- aidcp-cloud 89cf903 publish-executor.test.ts stage-4 测断言 recordMetadata aiEnforced=true 落库 -->
- [x] 5.3 `sourceLikedIds` 由 `LikedNoteStore.listSince(基线)` 回取，取代 `server.ts` 写死的 `sourceLikedIds: []`；`sourceConcepts` 取真实概念。无来源如实空数组、**MUST NOT 编造**。验证：单测断言血缘非写死值、无来源如实 `[]` <!-- aidcp-cloud 89cf903 lineageFrom(context) 从 trigger.generateInput 取真概念/真点赞 id；测断言 sourceConcepts=['RAG 重排','vLLM'] sourceLikedIds=[11] -->
- [x] 5.4 `src/publish-agent/publish-log-store.ts` `publish_log` 加 `publish_metadata JSONB` + `ai_enforced BOOLEAN` 列（DDL `IF NOT EXISTS` 幂等），INSERT / SELECT 同步。验证：迁移幂等（重复执行不报错）、读写往返一致；落库 MUST NOT 改变发布判定 <!-- aidcp-cloud 89cf903 publish-log-store.ts:25-30 列+ALTER IF NOT EXISTS 幂等；:109 recordMetadata / :118 getMostRecentPublishTime -->

## 6. aidcp-cloud — 飞书 /publish 命令 + 删 temp 旁路（缺口⑥）

- [x] 6.1 `src/feishu/commands.ts` 在 `CommandAction` 加 `'publish'` 并新增 `/publish` 指令（手动扳机，接 `PublishScheduler` / `PublishOrchestrator.trigger()`，越 `canDo` 但仍走人审）；与既有 `/publish-test`（仅发测试审批卡片）区分。验证：单测解析 `/publish` → 触发；越权后仍挂人审 <!-- aidcp-cloud 89cf903 commands.ts CommandAction+='publish' / parse '/publish' / handle→runPublish()→scheduler.triggerManual；feishu-commands.test.ts 加解析测 -->
- [x] 6.2 删 `src/server.ts` `/debug/publish` HTTP 端口（含 `debugPayload` / `debugServer` / `TODO(temp)` 注记口）。验证：`grep -rn "/debug/publish" src` 无输出 <!-- aidcp-cloud 89cf903 debugServer 块整删、留注记；grep /debug/publish 仅余「已删除」注释 -->
- [x] 6.3 删 `src/cli/trigger-publish-temp.ts` 整文件 + `package.json` 的 `trigger:publish-temp` 脚本。验证：文件不存在、脚本不存在、`grep -rn "publish.request" src` 无任何绕过指令驱动 / AC-PUB 的直发触发点 <!-- aidcp-cloud 89cf903 trigger-publish-temp.ts + 脚本删除；剩余 publish.request 仅 executor 合法 v1 流水线路径（非绕过） -->

## 7. aidcp-edge — 配图与元数据 kind 处理器（缺口②）

- [x] 7.1 扩 `src/flows/anchors.ts`（**注意：锚点声明在 `flows/anchors.ts`，不是 `locating/anchors.ts`**；`publish-command-handlers.ts` 由此 import）补配图 / 封面 / 可见范围 / 权限 / 定时 / 提及 / 合集等新锚点（仿既有 `XHS_PUBLISH_*` 三件套 `ACTION_ID` + `GOAL` + `ANCHOR_HINT`）；复用 `LocatingEngine` 三道闸反污染回写（stage→confirm），**engine 不改**。验证：`npm run typecheck` 过、新锚点经 stage→confirm 单测 <!-- aidcp-edge 45922a7 偏离：元数据锚点（mention/location/collection/visibility/各声明/schedule）以 best-effort 内联在 publish-command-handlers.ts 的清晰注释段（CANDIDATE_ANCHOR/OPTION_KEYWORD + builders），未拆到 anchors.ts —— 因这些是占位级、待实机 CDP 校准，集中一处比散落 10+ 占位常量更可维护；engine 不改、复用三道闸。配图/封面锚点 DEFERRED→publish-media-upload -->
- [x] 7.2 `upload_image` 已迁移并由 `publish-media-upload` 实装：CDP `DOM.setFileInputFiles` + 缩略图成功态后置校验 + 下载安全封套 + 分类失败回报。<!-- fulfilled by archived change 2026-07-03-publish-media-upload tasks 2.1-2.5 / 6.1-6.2 -->
- [x] 7.3 `set_cover` 已迁移并由 `publish-media-upload` 实装前向兼容 handler；单图产品不触发，多图真实 selector 待后续多图启用校准。<!-- fulfilled by archived change 2026-07-03-publish-media-upload tasks 3.1-3.2 -->
- [x] 7.4 实装 `set_option`（按 `optionKind` 路由 `visibility` / `permissions` / 各声明开关/单选，engine 定位、后置校验选中态==期望）。验证：单测校验不符回 `post_validation_failed` <!-- aidcp-edge 45922a7 buildSetOptionRequest 按 optionKind 路由 + valueValidator best-effort 后置校验；AC-CMD-S4 set_option 测过；缺控件→no_target 不假成功 -->
- [x] 7.5 实装 `set_schedule`（定位时间选择器填 `publishTime`、后置校验已设定）。验证：单测覆盖成功 / 失败两路 <!-- aidcp-edge 45922a7 buildSetScheduleRequest + valueValidator('定时')；AC-CMD-S4 set_schedule 测过 -->

## 8. aidcp-edge — 人审默认 + 放开硬拒（缺口④ + 配图前置）

- [x] 8.1 `src/main.ts:130` 审批闸条件 `process.env.AIDCP_REAL_PUBLISH === 'true'` → `!== 'false'`（缺省即挂闸，仅显式 `AIDCP_REAL_PUBLISH=false` 才跳过）；审批信号路径契约 `/tmp/aidcp-publish-approve-<requestId>.json` 两端不漂移。验证：单测/手测缺省即挂闸、显式 `false` 才跳过、其余取值一律挂闸 <!-- aidcp-edge 45922a7 main.ts 闸条件改 !== 'false'（默认必过人审，AC-PUB）；AC-PUB-* 6 测全过、信号路径契约不漂移 -->
- [x] 8.2 v1 整页带图硬拒已由 `publish-media-upload` 改为显式改道指令路径；不在 v1 内静默丢图或假成功。<!-- fulfilled by archived change 2026-07-03-publish-media-upload task 4.1 -->

## 9. 验收（中控触发，落 sub-repo 执行）

- [x] 9.1 cloud `AC-PUB-*`（`test/acceptance/publish-approval-contract.test.ts`：未授权绝不静默发布 —— 缺省/异常按未授权、`submit_publish` 前严格 `approved===true`；手动越 `canDo` 仍过人审）全过 <!-- both 89cf903/45922a7：cloud AC-PUB + edge AC-PUB-01..06 全过 -->
- [x] 9.2 cloud + edge `AC-PROTO-*`（`test/acceptance/protocol-contract.test.ts`：两份 protocol.ts 不漂移、计数 54、`Record<MessageType,true>` 穷举一致）全过 <!-- both：AC-PROTO-02 计数 54 两端一致全过 -->
- [x] 9.3 新增/扩展 `AC-CMD-*`（指令驱动：元数据/配图指令按序、失败如实记 `failedAt`、配图失败降级纯文字 `imagesOk` 如实、边缘 kind 处理器不假成功）全过 <!-- 元数据/edge kind AC-CMD 全做：cloud SEQ-08/09 + edge AC-CMD-S4（候选路由/缺控件 no_target/set_option/set_schedule）；配图降级 AC-CMD DEFERRED→publish-media-upload -->
- [x] 9.4 cloud `AC-RISK-*`（`test/acceptance/risk-guard.test.ts`：绝不自残、被禁 `record` 返 false；自动扳机以 `canDo('publish')===true` 为硬前提）全过 <!-- aidcp-cloud 89cf903 AC-RISK 全过；scheduler 自动扳机 canDo=false→'blocked' 不触发（publish-scheduler.test.ts 断言）-->

## 10. 双仓全量回归（先 acceptance 再全量再 typecheck）

- [x] 10.1 cloud：`cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-cloud 89cf903 全量 272 绿 + typecheck 净 -->
- [x] 10.2 edge：`cd ../aidcp-edge && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-edge 45922a7 acceptance 11 绿 + 全量 268 绿 + typecheck 净 -->
- [x] 10.3 中控：`openspec validate publish-trigger-and-apply --strict` 通过 <!-- 2026-06-20 strict 通过 -->

## 11. 部署（ECS 安全序列 + edge 本地；执行前先做 §0 前置检查）

- [x] 11.1 §0 前置检查已由 A 配图收口部署批执行：私钥 `~/codes/isales-4.pem`、sub-repo、cloud origin/master 状态通过。<!-- see archived 2026-07-03-publish-media-upload task 8.1 -->
- [x] 11.2 ECS 部署已由 A 配图收口批统一执行：备份 cloud/env → rsync master 快照 → restart，包含本 change 的 cloud master 提交与 DB DDL。<!-- see archived 2026-07-03-publish-media-upload task 8.3: aidcp-cloud 63128e6 deployed 2026-06-21 -->
- [x] 11.3 healthcheck 已由 A 配图收口批统一执行：active、8787、PG、列/表、飞书长连接均通过，isales 未碰。<!-- see archived 2026-07-03-publish-media-upload task 8.3 -->
- [x] 11.4 真机全链 `/publish` 验收已登记到 `docs/real-machine-acceptance-backlog.md` 簇 3，与 `publish-media-upload 8.4` 同一真机 session 统一验；按 backlog 纪律，代码已部署后不再 gate 归档。<!-- 2026-07-10 backlog entry added -->

## Migration（仅当实施中实测配图桥风险超预期才触发）

> <!-- 2026-06-20 已触发：本 change 取五项一体收敛，配图应用下沉 publish-media-upload（见下）。 -->
> 默认六项一体，本 change 即第一（也是唯一）子块；以下为 design §6 的收敛预案，**非默认路径**。

- 若 CDP 文件输入桥（task 7.2 `upload_image` / task 7.3 `set_cover`）实测风险过高，本 change 收敛为**五项**（触发 + 元数据应用 + 人审默认 + 血缘 + 落库）：从范围去掉 task 4.1 的配图 emit 部分、task 4.2、task 7.2 / 7.3、task 8.2 放开带图硬拒、task 7.1 配图/封面锚点子集。
- 配图应用作为**后续 change `publish-media-upload`（暂名）**：CDP 文件输入桥 + `upload_image` / `set_cover` 处理器 + 序列 emit + 放开 `publish-post.ts:294-295` 硬拒 + 配图失败降级纯文字的 AC-CMD。其前置（本 change 的元数据应用 + 人审默认 + 落库）已满足，可独立验证。

> <!-- 五项一体已交付（cloud 89cf903 / edge 45922a7，双仓全量回归绿 + strict 通过）。原 DEFERRED 至 publish-media-upload 的：
> 4.2 / 7.2 / 7.3 / 8.2 + 4.1 配图 emit 子集 + 7.1 配图/封面锚点子集 + 9.3 配图降级 AC-CMD，已由 2026-07-03-publish-media-upload 归档收口。部署（§11.1-11.3）由 A 配图收口批统一完成；§11.4 真机全链转入 real-machine backlog 簇 3。 -->
