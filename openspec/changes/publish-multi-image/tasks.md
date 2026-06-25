## 0. 实装前坐实（验证任务，未坐实前不下"无需新风控约束"结论）

- [ ] 0.1 坐实发布命令序列执行期（多图 ≈ 张数×上传，数分钟）边缘浏览闭环看门狗 / `SessionMonitor` 是否对该 edge 暂停判活；若否，补"发布期看门狗豁免"约束（防 N 大被误判 idle 杀会话，见 CLAUDE.md §2 看门狗杀会话类 bug）
- [ ] 0.2 确认发布路径仍在 `interaction-guard` 之外（已初步核：guard 仅接线浏览闭环 `role-dispatcher.ts:302`、发布路径零引用 → 去重窗口大概率不适用；实装时确认而非加固）

## 1. aidcp-cloud — 数据模型与迁移（types + publish-log-store + 0017）

- [ ] 1.1 `types.ts`：新增 `ImageSetPlan { wantImage, imageCount, themes:[{subject,intent}], styleHint, plannedAt }`；`ImagePlan` 从单 `imagePrompt` 升级为 `imagePrompts:string[]`、激活 `imageCount`
- [ ] 1.2 `types.ts`：`ImageDirective`/`AssembledContent` 新增 `imageUrls:string[]` 并保留 `imageUrl = imageUrls[0]??null` 派生兼容（标 `@deprecated`）；`CoverSelection` 改 `{ imageUrls, hasCover, selectedAt }`；`PublishRecord` 新增 `imageUrls?`/`imagesAttachedCount?`
- [ ] 1.3 `PipelineFields` 加 `imageSetPlan` 键（唯一生产者 `ImageSetPlanner`，不死锁）
- [ ] 1.4 新增 `migrations/0017_publish_log_images.sql`（0016 已被并发会话 notification-contact-registry 占用）：复活 `images TEXT[]`（`ADD COLUMN IF NOT EXISTS`）+ 新增 `images_attached_count INT NOT NULL DEFAULT 0` + 显式兜空 `UPDATE publish_log SET images='{}' WHERE images IS NULL`；不加 `NOT NULL`、无 down
- [ ] 1.5 `publish-log-store.ts`：canonical SQL 同步补两列幂等 `ADD COLUMN`；insert 双写 `images=全部` + `image_url=imageUrls[0]??null`；`markImagesAttached(id, count)` 落真实附着数（`images_attached = count>0`）；读侧统一 `?? []`

## 2. aidcp-cloud — 配图三角色拆分（选题 / 指令 / 生成 + prompts）

- [ ] 2.1 `prompts.ts`：拆两套提示词——选题（正文→张数+每张主题，业务语言）、配图指令（主题→一条万相 prompt）；抽出**固定风格基底**为模板常量（无文字/无真人/英文/统一风格），MUST NOT 由 LLM 产
- [ ] 2.2 新增 `roles/image-set-planner.ts`（`ImageSetPlanner`）：watch `createdContent` → 写 `imageSetPlan`；张数 `clamp(1, AIDCP_PUBLISH_MAX_IMAGES≤9)`，降级朝"更少图"退（默认 1 张+通用主题），不调图源
- [ ] 2.3 新增 `roles/image-prompt-composer.ts`（`ImagePromptComposer`）：watch `imageSetPlan` → 每主题一条各异 prompt + 共享风格基底，写 `imagePlan(imagePrompts[])`；去重护栏命中即丢但**永远保住第 0 张**（保证 `wantImage:true → ≥1`）；不调图源
- [ ] 2.4 升级 `roles/image-generator.ts`：watch `imagePlan` **并行**出图（`Promise.allSettled`，每张 `Promise.race(generate, AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS)`），settle 后按规划顺序收成功 URL 进 `imageUrls`（[0]=封面位）；**每张独立超时**只丢该张不影响其余；并发上限 `AIDCP_PUBLISH_IMAGE_CONCURRENCY`；角色级总闸设 ≈ 每图超时+余量（wall-clock=max 非 sum）且超时也用已 settle 成功构造产出、绝不清零；失败那张不进数组（不补不复用）；订正 `:8` 陈旧"34×5=170s"注释为实际 18×5=90s
- [ ] 2.5 两个新决策角色注册进 publish orchestrator（`publish-agent` 自有编排器，不动浏览/通知 35 角色）；接入 `role_config`（可后台按角色配模型/温度——选题配强模型、指令配便宜的）

## 3. aidcp-cloud — 封面与组装

- [ ] 3.1 升级 `roles/cover-selector.ts`：读 `imageDirective.imageUrls`、恒取首张为封面、`hasCover=length>0`；空数组→ `{ imageUrls:[], hasCover:false }` 诚实；本期不引入封面索引、不改 set_cover 触发
- [ ] 3.2 `roles/content-assembler.ts`：`watchAll` 加 `imageUrls ← coverSelection.imageUrls`、`imageUrl ← imageUrls[0]??null`（封面）；`assembledContent` 形状新增 `imageUrls`、其余字段语义不变

## 4. aidcp-cloud — 下发复用与部分成功语义（executor + command-sequencer + env）

- [ ] 4.1 `roles/publish-executor.ts`：无图判据 `:212` 从 `!imageUrl` 改 `imageUrls.length===0`；下发 `:308-312` 改 `images: imageUrls` / `cover: imageUrls[0]`；落 `markImagesAttached(id, K)`；`roleTimeoutMs` 按张数上调（env，覆盖审批240s+张数×上传60s+余量）；`submit_publish` 成功后任何超时 MUST NOT 翻 `failed`
- [ ] 4.2 `command-sequencer.ts`：all-or-nothing `imagesOk` 改为计数 `K`（真实上传成功条数）；**早停判据 `:178`** 从 `!imagesOk` 改 `K===0`（K≥1 即有效帖、照发 K 张）；`set_cover` skip 判据 `:183` 随之；**保持** set_cover 触发仅 `images.length>1`（本期不改）
- [ ] 4.3 env 接线 + 充足默认：`AIDCP_PUBLISH_MAX_IMAGES`（默认 3、夹 ≤9）、`AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`（每图超时 > 单图轮询总预算）、`AIDCP_PUBLISH_IMAGE_CONCURRENCY`（并发上限，默认=张数上限）

## 5. aidcp-cloud — 单测与回归（三向隔离 + 红线）

- [ ] 5.1 `ImageSetPlanner` 单测（仅桩 LLM）：张数 clamp 边界、越界夹回、`wantImage:true→≥1`、降级朝更少图、不依赖图源
- [ ] 5.2 `ImagePromptComposer` 单测（仅桩 LLM）：去重保住第 0 张、近似项丢弃不补不复用、不依赖图源
- [ ] 5.3 `ImageGenerator` 单测（仅桩图源）：并行 `allSettled` 收集部分成功、某张超时只丢该张不影响其余、保序（[0]=封面位）、**总闸超时返回已 settle 不清零**（反例红线）、失败那张不进数组不伪造、M=0 空产出
- [ ] 5.4 部分成功语义测：M≥1 发 M 张、M=0 诚实 failed、上传 K 计数记账、`images_attached_count` 等于真实 K、`submit_publish` 后不翻 failed
- [ ] 5.5 封面 / 组装测：多图恒取首张、无图诚实空封面、`assembledContent` 含 `imageUrls`、`imageUrl` 派生=首张
- [ ] 5.6 数据模型兼容测：旧路径读 `imageUrl` 拿首图零回归、迁移 0017 幂等可重入 + `images IS NULL` 兜底
- [ ] 5.7 红线回归零漂移：`AC-PROTO-*`（两份 protocol.ts 不漂移、协议未改）、`AC-PUB-*`（未授权绝不静默发布）

## 6. 验证序列（CLAUDE.md §4，本地代码级）

- [ ] 6.1 cloud `npm run test:acceptance`（AC-PUB-* / AC-PROTO-* 全过）
- [ ] 6.2 cloud `npm test` 全量
- [ ] 6.3 cloud `npm run typecheck`
- [ ] 6.4 `openspec validate publish-multi-image --strict`

## 7. 部署与真机（gated，显式放行才做）

- [ ] 7.1 迁移 0017 上 ECS：先备份 → 应用 → 验 `images`/`images_attached_count` 列存在 + `images IS NULL` 已兜底
- [ ] 7.2 全 master rsync 部署（先 dry-run surface scope，连带 master 累积改动）→ restart → healthcheck（active + 8787 + 飞书长连 + PG select 1）→ 失败回滚
- [ ] 7.3 部署后 grep 关键文件确认新码生效 + 看新启动日志（不仅信 rsync 回执）
- [ ] 7.4 真机 E2E：飞书 `/publish [accountId]` 触发，验多图真出图（并行、wall-clock≈最慢单张）、M/K 记账、封面=成功序列首张、真帖多图上账号；edge"一命令一图"多图上传通道复用正确（edge 零改动）

## 8. 归档

- [ ] 8.1 全 task 绿 + `validate --strict` 通过 → `openspec archive publish-multi-image`（delta 合并进 `openspec/specs/`）
