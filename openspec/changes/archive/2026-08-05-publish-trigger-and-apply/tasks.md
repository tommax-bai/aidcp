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
> 放开带图硬拒 / 配图失败降级 AC-CMD）整体下沉到后续 change `publish-media-upload`。下方被下沉的 task 留 [ ] 并标 DEFERRED。 -->

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

> **【2026-08-05 事实订正 · 动这四条之前必看】4.2 / 7.2 / 7.3 / 8.2 点名的落点已从生产剪除，
> 而它们要的能力**在现役路径上已经实装了**。照原文实装 = 零生产效果。**
>
> **① 落点是退役模块。** 这四条都指向 `aidcp-edge/src/flows/publish-command-handlers.ts`
> 与 `src/flows/publish-post.ts`。`flows/publish-command-handlers.js` **在退役名单上**
> （事实源 `aidcp-edge/scripts/native-engine-inventory.cjs` 的 `RETIRED_DIST_MODULES`），
> 本机实测生产 `dist/flows/` 只剩三个非业务件。**在那儿写代码，测试会绿、发版会成功，
> 运营机上跑的仍是 Native 引擎那一套。**（同一个陷阱今天已经咬过另一份提案，见
> `docs/deferred-defect-proposals-2026-08-05.md` §5。）
>
> **② 小红书配图上传已在现役路径实装，且做得比本条原文要求的更严。**
> 落点 `aidcp-edge/native/page-engine/src/engine.rs` 的 `execute_xhs_publish_upload_image`：
> 写之前先取**预览位身份基线**，写之后有界轮询等那一位出现「基线里没有的」身份——
> 因为旧判据「那个序号位上存在预览图」**会被上一次的残留预览满足**，一次根本没生效的上传照样回确认，
> 上游据此走到提交，最后发出去的稿子少一张图或配错图。四种终局各有独立原因码，
> 附件写下去之后的任何失败一律「不确定」、绝不回「未开始」。
>
> **③ 真正还缺的是 Facebook 那半，而且它是诚实缺席、不是静默假成功。**
> `native/page-engine/src/facebook-router/90-dispatch.js` 对 `publish_set_cover` /
> `publish_add_with_candidate` / `publish_set_option` / `publish_set_schedule` 一律回
> `kind_not_implemented`。要补就在**那里**补，不在退役模块里。
>
> **④ 原文写的 deferral 目标 `publish-media-upload` 已于 2026-07-03 归档。**
> 所以「deferred 到另一条 change」这个状态今天已经不成立——它要么已经交付（小红书那半，见②），
> 要么就是没人接（Facebook 那半，见③）。这四条**按此结案，不再挂 deferred**。

- [x] 4.1 `src/publish-agent/command-sequencer.ts` `buildCommandSequence` 扩展：从 `publishMetadata` emit `add_with_candidate`（`mention` / `location` / `collection`）/ `set_option`（`visibility` / `permissions` / 各合规声明）/ `set_schedule`（`mode==='scheduled'` 时按 `publishTime`）；按配图 emit `upload_image`×N / `set_cover`。序列序：`navigate_entry → select_mode → upload_image×N → set_cover → fill_field(title/content) → add_with_candidate(topic)×N → add_with_candidate(mention|location|collection)×N → set_option×N → set_schedule → [授权]submit_publish → capture_postId`。验证：`test/publish-agent/command-sequencer.test.ts` 断言序列含元数据/配图指令、顺序正确 <!-- aidcp-cloud 89cf903 元数据 emit 全做：SEQ-08/09 断言 mention/location/collection 经 candidateKind、visibility/declaration_ai 经 set_option、scheduled→set_schedule，全在 submit 前。配图 emit（upload_image/set_cover）DEFERRED→publish-media-upload -->
- [x] 4.2 **【按 2026-08-05 事实订正结案，见本节抬头：落点已退役，能力在现役路径已实装（小红书）/ 诚实缺席（Facebook）】** 配图上传失败降级纯文字：`upload_image` 回 `ok:false` → 标 `imagesOk=false`、跳过依赖图的 `set_cover`、继续余下文字/元数据指令；`imagesOk` 如实（**MUST NOT 伪造有图**）。验证：单测桩 `upload_image ok:false` → 序列降级、`imagesOk=false`、不报带图成功 <!-- DEFERRED → publish-media-upload（配图 CDP 桥下沉，本 change 不发图指令故无降级面） -->
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
- [x] 7.2 **【按 2026-08-05 事实订正结案，见本节抬头：落点已退役，能力在现役路径已实装（小红书）/ 诚实缺席（Facebook）】** `src/flows/publish-command-handlers.ts` 实装 `upload_image`：URL → 下载到 `/tmp` → CDP 文件输入桥（`DOM.setFileInputFiles` 类机制）→ 后置校验图进入编辑区 → 清理临时文件；失败回真实 `error`（`upload_failed` / `no_target` / `post_validation_failed`），替换 `kind_not_implemented`。验证：jsdom/CDP 桩单测成功 + 失败两路、失败不翻 `ok:true` <!-- DEFERRED → publish-media-upload（CDP 文件输入桥依赖真实浏览器、CI 不可测）；当前 upload_image 诚实回 kind_not_implemented -->
- [x] 7.3 **【按 2026-08-05 事实订正结案，见本节抬头：落点已退役，能力在现役路径已实装（小红书）/ 诚实缺席（Facebook）】** 实装 `set_cover`（复用 `LocatingEngine`，定位封面入口选定、后置校验封面已设）。验证：单测定位失败回 `ok:false` + 真实 error <!-- DEFERRED → publish-media-upload（依赖配图先就位）；当前 set_cover 诚实回 kind_not_implemented -->
- [x] 7.4 实装 `set_option`（按 `optionKind` 路由 `visibility` / `permissions` / 各声明开关/单选，engine 定位、后置校验选中态==期望）。验证：单测校验不符回 `post_validation_failed` <!-- aidcp-edge 45922a7 buildSetOptionRequest 按 optionKind 路由 + valueValidator best-effort 后置校验；AC-CMD-S4 set_option 测过；缺控件→no_target 不假成功 -->
- [x] 7.5 实装 `set_schedule`（定位时间选择器填 `publishTime`、后置校验已设定）。验证：单测覆盖成功 / 失败两路 <!-- aidcp-edge 45922a7 buildSetScheduleRequest + valueValidator('定时')；AC-CMD-S4 set_schedule 测过 -->

## 8. aidcp-edge — 人审默认 + 放开硬拒（缺口④ + 配图前置）

- [x] 8.1 `src/main.ts:130` 审批闸条件 `process.env.AIDCP_REAL_PUBLISH === 'true'` → `!== 'false'`（缺省即挂闸，仅显式 `AIDCP_REAL_PUBLISH=false` 才跳过）；审批信号路径契约 `/tmp/aidcp-publish-approve-<requestId>.json` 两端不漂移。验证：单测/手测缺省即挂闸、显式 `false` 才跳过、其余取值一律挂闸 <!-- aidcp-edge 45922a7 main.ts 闸条件改 !== 'false'（默认必过人审，AC-PUB）；AC-PUB-* 6 测全过、信号路径契约不漂移 -->
- [x] 8.2 **【按 2026-08-05 事实订正结案，见本节抬头：落点已退役，能力在现役路径已实装（小红书）/ 诚实缺席（Facebook）】** 放开 `src/flows/publish-post.ts:294-295` v1 整页带图硬拒（`images are not supported in phase one`），带图走配图流程 / 指令驱动路径。验证：带图 payload 不再返回硬拒 error <!-- DEFERRED → publish-media-upload（与配图应用同批放开，避免放开后无桥导致带图必败）-->

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

> **【2026-08-05 立论过期结案】11.1–11.3 描述的是「把单体 `aidcp-cloud` rsync 到 `/opt/aidcp/cloud` 再重启」这套部署动作，
> 而根 `CLAUDE.md` §8.0（2026-08-05 立、OVERRIDE 级）已定：**`aidcp-cloud` 永不部署到任何环境**——
> dev 与 OL 都已切到 api / automation / content 三个派生服务，单体已停并 disable。
> 照这三条执行会把一个已停用的单体重新拉起来，而它一起来就会去抢按 target 单实例的自动化写者锁与 8787，
> **把正在跑的派生服务顶掉**（前科见记忆 `monolith-unit-still-enabled-steals-lock`）。
> 所以这不是「还没做」，是**做了就出事**。
>
> 本 change 的云端改动实际已随派生服务的常规部署上线；要复核就核派生服务，不核单体。
> 11.4 是真机端到端，按 2026-08-05 用户裁定不再登记、不再统计。

- [x] 11.1 **【按 §8.0 立论过期：单体永不部署，见本节抬头】** §0 前置检查：`ls -d ../aidcp-edge ../aidcp-cloud` 确认 sub-repo 存在 + 私钥 `~/codes/dev-0722.pem` 存在且 `chmod 600`；缺失即停手告知用户 <!-- 部署按用户指示延后（A 全阶段统一部署） -->
- [x] 11.2 **【按 §8.0 立论过期：单体永不部署，见本节抬头】** ECS 先备份（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ DB 迁移（`publish_log` 加 `publish_metadata` / `ai_enforced` 列 + `liked_notes` 建表，DDL `IF NOT EXISTS` 幂等）→ `systemctl restart aidcp-cloud.service`
- [x] 11.3 **【按 §8.0 立论过期：单体永不部署，见本节抬头】** healthcheck：`active (running)` + 8787 监听 + 飞书长连接已建立 + PG `select 1`；失败即回滚。**任何 ECS 操作绝不碰同机 `isales`**
- [x] 11.4 **【按用户裁定清账：真机端到端不再登记，见本节抬头】** edge 本地跑、连 `ws://121.89.85.150:8787`，验证飞书 `/publish` → 指令驱动 → 人审 → 配图/元数据应用 → 真实落库 + 血缘端到端（`AIDCP_REAL_PUBLISH` 缺省即挂人审；受控放行用 `AIDCP_REAL_PUBLISH=false`）

## Migration（仅当实施中实测配图桥风险超预期才触发）

> <!-- 2026-06-20 已触发：本 change 取五项一体收敛，配图应用下沉 publish-media-upload（见下）。 -->
> 默认六项一体，本 change 即第一（也是唯一）子块；以下为 design §6 的收敛预案，**非默认路径**。

- 若 CDP 文件输入桥（task 7.2 `upload_image` / task 7.3 `set_cover`）实测风险过高，本 change 收敛为**五项**（触发 + 元数据应用 + 人审默认 + 血缘 + 落库）：从范围去掉 task 4.1 的配图 emit 部分、task 4.2、task 7.2 / 7.3、task 8.2 放开带图硬拒、task 7.1 配图/封面锚点子集。
- 配图应用作为**后续 change `publish-media-upload`（暂名）**：CDP 文件输入桥 + `upload_image` / `set_cover` 处理器 + 序列 emit + 放开 `publish-post.ts:294-295` 硬拒 + 配图失败降级纯文字的 AC-CMD。其前置（本 change 的元数据应用 + 人审默认 + 落库）已满足，可独立验证。

> <!-- 五项一体已交付（cloud 89cf903 / edge 45922a7，双仓全量回归绿 + strict 通过）。DEFERRED 至 publish-media-upload：
> 4.2 / 7.2 / 7.3 / 8.2 + 4.1 配图 emit 子集 + 7.1 配图/封面锚点子集 + 9.3 配图降级 AC-CMD。部署（§11）按用户指示与 A 全阶段统一进行。 -->
