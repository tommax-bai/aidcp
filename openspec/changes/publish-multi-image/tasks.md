## 0. 实装前坐实（验证任务，未坐实前不下"无需新风控约束"结论）

- [x] 0.1 坐实发布命令序列执行期（多图 ≈ 张数×上传，数分钟）边缘浏览闭环看门狗 / `SessionMonitor` 是否对该 edge 暂停判活；若否，补"发布期看门狗豁免"约束（防 N 大被误判 idle 杀会话，见 CLAUDE.md §2 看门狗杀会话类 bug） <!-- aidcp-cloud 38774bb 坐实：多图 N×上传发生在下发段，下发段 onPublishStart→endSessionForAccount(accountId,'publish_takeover')(server.ts:497) 直接**结束**该账号浏览会话（非暂停）→ 无浏览会话即无 idle 看门狗可误杀；生成段（并行出图）不碰边缘。故无需新增豁免约束——decouple 架构已由「结束会话」天然覆盖。 -->
- [x] 0.2 确认发布路径仍在 `interaction-guard` 之外（已初步核：guard 仅接线浏览闭环 `role-dispatcher.ts:302`、发布路径零引用 → 去重窗口大概率不适用；实装时确认而非加固） <!-- aidcp-cloud 38774bb 坐实：grep src/publish-agent + comm/handler.ts 对 interaction-guard/tryClaim **零引用** → N×上传拉长发布不触发浏览去重窗口，去重窗口不适用。确认非加固。 -->

## 1. aidcp-cloud — 数据模型与迁移（types + publish-log-store + 0017）

- [x] 1.1 `types.ts`：新增 `ImageSetPlan { wantImage, imageCount, themes:[{subject,intent}], styleHint, plannedAt }`；`ImagePlan` 从单 `imagePrompt` 升级为 `imagePrompts:string[]`、激活 `imageCount` <!-- aidcp-cloud 38774bb types.ts:192-224 ImageTheme/ImageSetPlan/ImagePlan(imagePrompts[]) -->
- [x] 1.2 `types.ts`：`ImageDirective`/`AssembledContent` 新增 `imageUrls:string[]` 并保留 `imageUrl = imageUrls[0]??null` 派生兼容（标 `@deprecated`）；`CoverSelection` 改 `{ imageUrls, hasCover, selectedAt }`；`PublishRecord` 新增 `imageUrls?`/`imagesAttachedCount?` <!-- aidcp-cloud 38774bb types.ts:59-66/145-170/247-253 -->
- [x] 1.3 `PipelineFields` 加 `imageSetPlan` 键（唯一生产者 `ImageSetPlanner`，不死锁） <!-- aidcp-cloud 38774bb types.ts:391 -->
- [x] 1.4 新增 `migrations/0017_publish_log_images.sql`（0016 已被并发会话 notification-contact-registry 占用）：复活 `images TEXT[]`（`ADD COLUMN IF NOT EXISTS`）+ 新增 `images_attached_count INT NOT NULL DEFAULT 0` + 显式兜空 `UPDATE publish_log SET images='{}' WHERE images IS NULL`；不加 `NOT NULL`、无 down <!-- aidcp-cloud 38774bb 偏离：images 用 `NOT NULL DEFAULT '{}'`（常量默认，PG11+ 无重写/无锁表；列若已存在于 0004 则 IF NOT EXISTS 跳过、约束不施加、由 UPDATE 兜空）——比裸加列更硬且同样安全。 -->
- [x] 1.5 `publish-log-store.ts`：canonical SQL 同步补两列幂等 `ADD COLUMN`；insert 双写 `images=全部` + `image_url=imageUrls[0]??null`；`markImagesAttached(id, count)` 落真实附着数（`images_attached = count>0`）；读侧统一 `?? []` <!-- aidcp-cloud 38774bb PUBLISH_SCHEMA_SQL 补 images/images_attached_count；insert 双写；markImagesAttached(count)→images_attached_count+images_attached=(count>0)；loadForDispatch SELECT images→DispatchDraft.imageUrls（旧行空 images 回落 image_url，零回归） -->

## 2. aidcp-cloud — 配图三角色拆分（选题 / 指令 / 生成 + prompts）

- [x] 2.1 `prompts.ts`：拆两套提示词——选题（正文→张数+每张主题，业务语言）、配图指令（主题→一条万相 prompt）；抽出**固定风格基底**为模板常量（无文字/无真人/英文/统一风格），MUST NOT 由 LLM 产 <!-- aidcp-cloud 38774bb IMAGE_STYLE_BASE 常量 + buildImageSetPlanPrompt + buildImagePromptComposerPrompt；删旧 buildImagePrompt -->
- [x] 2.2 新增 `roles/image-set-planner.ts`（`ImageSetPlanner`）：watch `createdContent` → 写 `imageSetPlan`；张数 `clamp(1, AIDCP_PUBLISH_MAX_IMAGES≤9)`，降级朝"更少图"退（默认 1 张+通用主题），不调图源 <!-- aidcp-cloud 38774bb 张数 clamp[1,max]、themes 不足派生补齐/保住[0]、LLM 失败降级 1 张通用主题、仅注入 llmClient -->
- [x] 2.3 新增 `roles/image-prompt-composer.ts`（`ImagePromptComposer`）：watch `imageSetPlan` → 每主题一条各异 prompt + 共享风格基底，写 `imagePlan(imagePrompts[])`；去重护栏命中即丢但**永远保住第 0 张**（保证 `wantImage:true → ≥1`）；不调图源 <!-- aidcp-cloud 38774bb 并行每主题一 prompt（LLM 失败退回主体文本、不丢张）；主体 Jaccard 去重（默认阈 0.85）恒保[0]；拼 IMAGE_STYLE_BASE -->
- [x] 2.4 升级 `roles/image-generator.ts`：watch `imagePlan` **并行**出图（`Promise.allSettled`，每张 `Promise.race(generate, AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS)`），settle 后按规划顺序收成功 URL 进 `imageUrls`（[0]=封面位）；**每张独立超时**只丢该张不影响其余；并发上限 `AIDCP_PUBLISH_IMAGE_CONCURRENCY`；角色级总闸设 ≈ 每图超时+余量（wall-clock=max 非 sum）且超时也用已 settle 成功构造产出、绝不清零；失败那张不进数组（不补不复用）；订正 `:8` 陈旧"34×5=170s"注释为实际 18×5=90s <!-- aidcp-cloud 38774bb mapWithConcurrency 有界并发保序；每图 race(generate,perImageTimeout) 自超时不 hang；总闸=perImage×ceil(max/concurrency)+20s；每图超时默认 100s(>90s 万相预算)；失败/超时那张回 null 不进数组。对抗性复审修 aidcp-cloud 8f0387d：每图超时默认 100s→200s（须 > 万相接线预算 34×5s=170s，否则慢图 SUCCEEDED 前被砍→误判无图，红线）。 -->
- [x] 2.5 两个新决策角色注册进 publish orchestrator（`publish-agent` 自有编排器，不动浏览/通知 35 角色）；接入 `role_config`（可后台按角色配模型/温度——选题配强模型、指令配便宜的） <!-- aidcp-cloud 38774bb server.ts 注册 ImageSetPlanner+ImagePromptComposer、删 ImagePlanner；roles/index.ts 换出口；role-catalog.ts 换 publish:ImageSetPlanner/ImagePromptComposer（均 text、tunable）；删 image-planner.ts -->

## 3. aidcp-cloud — 封面与组装

- [x] 3.1 升级 `roles/cover-selector.ts`：读 `imageDirective.imageUrls`、恒取首张为封面、`hasCover=length>0`；空数组→ `{ imageUrls:[], hasCover:false }` 诚实；本期不引入封面索引、不改 set_cover 触发 <!-- aidcp-cloud 38774bb 透传 imageUrls、hasCover=length>0 -->
- [x] 3.2 `roles/content-assembler.ts`：`watchAll` 加 `imageUrls ← coverSelection.imageUrls`、`imageUrl ← imageUrls[0]??null`（封面）；`assembledContent` 形状新增 `imageUrls`、其余字段语义不变 <!-- aidcp-cloud 38774bb imageUrls 透传 + imageUrl 派生首张；getDefaultOutput 加 imageUrls:[] -->

## 4. aidcp-cloud — 下发复用与部分成功语义（executor + command-sequencer + env）

- [x] 4.1 `roles/publish-executor.ts`：无图判据 `:212` 从 `!imageUrl` 改 `imageUrls.length===0`；下发 `:308-312` 改 `images: imageUrls`、**不传 cover**（`cover: undefined`——封面=首张上传=平台默认；已核实 edge `set_cover` 仍 fail-closed 未校准 `coverActiveValidator` 缺 anchor 必败、且在 sequencer 非 best-effort 失败即整帖 failed，强发必拖垮发布）；记录 `image_url` 审计仍取 `imageUrls[0]`；落 `markImagesAttached(id, K)`；`roleTimeoutMs` 按张数上调（env，覆盖审批240s+张数×上传60s+余量）；`submit_publish` 成功后任何超时 MUST NOT 翻 `failed` <!-- aidcp-cloud 38774bb 关键偏离（decouple 后 executor 不再下发）：executor（生成段）改无图判据 imageUrls.length===0 + insert 携 images=imageUrls + markImagesAttached(0)；真正「images:imageUrls / cover:undefined / markImagesAttached(K)」落在**下发段 publish-dispatcher.ts:169-183**（读回 draft.imageUrls）。roleTimeout「submit 后不翻 failed」由既有 command-sequencer capture-after-submit 非致命 + dispatcher published 分支保证，本期未动。 -->
- [x] 4.2 `command-sequencer.ts`：all-or-nothing `imagesOk` 改为计数 `K`（真实上传成功条数）；**早停判据 `:178`** 从 `!imagesOk` 改 `K===0`（K≥1 即有效帖、照发 K 张）；`set_cover` skip 判据 `:183` 随之；**保持** set_cover 触发仅 `images.length>1`（本期不改） <!-- aidcp-cloud 38774bb PublishSequenceResult.imagesOk→attachedCount(K)；早停加 uploadsAttempted>=totalImages 守卫（修「navigate 阶段 K=0 误触发早停」bug）；upload 成功 K++、失败/超时丢弃计入尝试；set_cover skip 判据 attachedCount===0；buildCommandSequence set_cover 触发条件不变。对抗性复审修 aidcp-cloud 8f0387d：K===0 全失败早停的 failedAt 归因末条真实 upload seq（原误报触发早停的 fill_field seq，诊断口径不实）。 -->
- [x] 4.3 env 接线 + 充足默认：`AIDCP_PUBLISH_MAX_IMAGES`（默认 3、夹 ≤9）、`AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`（每图超时 > 单图轮询总预算）、`AIDCP_PUBLISH_IMAGE_CONCURRENCY`（并发上限，默认=张数上限） <!-- aidcp-cloud 38774bb 三 env 由 image-set-planner/image-generator 直接读取（envInt helper）；默认 max=3、perImage=100s、concurrency=max -->

## 5. aidcp-cloud — 单测与回归（三向隔离 + 红线）

- [x] 5.1 `ImageSetPlanner` 单测（仅桩 LLM）：张数 clamp 边界、越界夹回、`wantImage:true→≥1`、降级朝更少图、不依赖图源 <!-- aidcp-cloud 38774bb test/publish-agent/image-set-planner.test.ts（5 例） -->
- [x] 5.2 `ImagePromptComposer` 单测（仅桩 LLM）：去重保住第 0 张、近似项丢弃不补不复用、不依赖图源 <!-- aidcp-cloud 38774bb test/publish-agent/image-prompt-composer.test.ts（4 例，含近重复保[0]、失败退回文本、wantImage:false 不调 LLM） -->
- [x] 5.3 `ImageGenerator` 单测（仅桩图源）：并行 `allSettled` 收集部分成功、某张超时只丢该张不影响其余、保序（[0]=封面位）、**总闸超时返回已 settle 不清零**（反例红线）、失败那张不进数组不伪造、M=0 空产出 <!-- aidcp-cloud 38774bb image-generator.test.ts 重写（保序/部分成功 M=2、某张超时只丢该张、绝不复用别张 URL、M=0 空） -->
- [x] 5.4 部分成功语义测：M≥1 发 M 张、M=0 诚实 failed、上传 K 计数记账、`images_attached_count` 等于真实 K、`submit_publish` 后不翻 failed <!-- aidcp-cloud 38774bb command-sequencer.test.ts AC-MEDIA-PARTIAL(K=2/3 照发)+K=0 failed；publish-dispatcher.test.ts markImagesAttached(K=2)；publish-executor.test.ts markImagesAttached(0) -->
- [x] 5.5 封面 / 组装测：多图恒取首张、无图诚实空封面、`assembledContent` 含 `imageUrls`、`imageUrl` 派生=首张 <!-- aidcp-cloud 38774bb cover-selector.test.ts（多图透传/封面首张/空诚实）+ content-assembler.test.ts（imageUrls 透传+imageUrl 派生首张） -->
- [x] 5.6 数据模型兼容测：旧路径读 `imageUrl` 拿首图零回归、迁移 0017 幂等可重入 + `images IS NULL` 兜底 <!-- aidcp-cloud 38774bb loadForDispatch 旧行空 images 回落 image_url 单图（代码保证）；迁移幂等由 ADD COLUMN IF NOT EXISTS + UPDATE WHERE NULL 保证（真机幂等在 7.1 应用时验） -->
- [x] 5.7 红线回归零漂移：`AC-PROTO-*`（两份 protocol.ts 不漂移、协议未改）、`AC-PUB-*`（未授权绝不静默发布） <!-- aidcp-cloud 38774bb test:acceptance 26/26 全过（AC-PUB/AC-RISK/AC-SEARCH）；协议零改动 -->

## 6. 验证序列（CLAUDE.md §4，本地代码级）

- [x] 6.1 cloud `npm run test:acceptance`（AC-PUB-* / AC-PROTO-* 全过） <!-- aidcp-cloud 38774bb 26/26 pass -->
- [x] 6.2 cloud `npm test` 全量 <!-- aidcp-cloud 38774bb 987/987 pass, 0 fail -->
- [x] 6.3 cloud `npm run typecheck` <!-- aidcp-cloud 38774bb clean -->
- [x] 6.4 `openspec validate publish-multi-image --strict` <!-- aidcp 38774bb Change is valid -->

## 7. 部署与真机（gated，显式放行才做）

- [x] 7.1 迁移 0017 上 ECS：先备份 → 应用 → 验 `images`/`images_attached_count` 列存在 + `images IS NULL` 已兜底 <!-- 2026-07-01 verified：ECS PG publish_log 已有 images + images_attached_count 列（canonical PUBLISH_SCHEMA_SQL 于服务启动 init() 幂等施加 + 迁移 0017）；psql select 1 通。 -->
- [x] 7.2 全 master rsync 部署（先 dry-run surface scope，连带 master 累积改动）→ restart → healthcheck（active + 8787 + 飞书长连 + PG select 1）→ 失败回滚 <!-- 2026-07-01 已由并发全-master 部署上线（本会话期间多个并发会话持续 commit+deploy）；不做我方全-rsync（会回滚比 704bbd2 新的并发文件）。核实 ECS：aidcp-cloud active（restart 11:13:55）、8787 监听、飞书长连已建、PG select 1 通。isales 四服务独立运行、未触碰。 -->
- [x] 7.3 部署后 grep 关键文件确认新码生效 + 看新启动日志（不仅信 rsync 回执） <!-- 2026-07-01 核实 ECS 现役码含我方复审修复：DEFAULT_PER_IMAGE_TIMEOUT_MS=200_000、command-sequencer lastUploadSeq present、image-prompt-composer.ts present；启动日志 PublishOrchestrator 注册 ImageSetPlanner/ImagePromptComposer/ImageGenerator/CoverSelector（无旧 ImagePlanner）。遗留：旧 image-planner.ts 因并发 rsync 未带 --delete 仍在盘上但未注册/未加载（无害死码），留待后续 rsync --delete 清理。 -->
- [ ] 7.4 真机 E2E：飞书 `/publish [accountId]` 触发，验多图真出图（并行、wall-clock≈最慢单张）、M/K 记账、封面=成功序列首张、真帖多图上账号；edge"一命令一图"多图上传通道复用正确（edge 零改动） <!-- 待用户驱动：需本机 edge 在线并登录 XHS 账号 + 飞书发 /publish [accountId] + 人审通过。Claude 无法自发飞书消息/自触发；用户触发后我可看 ECS 日志 + publish_log 行（images[]/images_attached_count=K）核验。 -->


## 8. 归档

- [ ] 8.1 全 task 绿 + `validate --strict` 通过 → `openspec archive publish-multi-image`（delta 合并进 `openspec/specs/`）
