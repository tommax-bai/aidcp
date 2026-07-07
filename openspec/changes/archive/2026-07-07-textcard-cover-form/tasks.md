# Tasks — textcard-cover-form

> 依赖序：批 1 感知 → 批 2 渲染（与批 1 可并行）→ 批 3 接线（依赖 1+2）→ 批 4 部署与真机。全程双旗标默认关，各批可独立合入（零行为变化）。热点文件（`role-catalog.ts`、`publish-agent/types.ts`、`image-generator.ts`）改动走单独小 commit、与活跃 change `publish-trigger-and-apply` 串行集成，集成前 rebase 核对（`image-generator.ts` 刚被 record-image-generation-usage 动过）。

## 1. aidcp-cloud — 感知（批 A）

- [x] 1.1 新建 `src/llm/vision.ts` OpenAI 兼容多模态客户端（content 数组含 image_url；复用 providerRuntime 凭据映射与 token 记账钩子、既有 HTTP 错误语义）；模型解析链「env `AIDCP_COVER_FORM_MODEL`/`AIDCP_COVER_FORM_PROVIDER` → 代码默认（dashscope qwen-vl flash 档，实装时 curl 探活定现役名）」，单测锁死绝不落全局文本模型层。验证：单测 + `npm run typecheck` <!-- aidcp-cloud a07ebe0 vision.test.ts 7 测全过；qwen.ts 错误构造函数导出复用（零行为变化）；代码默认 qwen-vl-plus（长期稳定名），现役 flash 档待部署时 curl 探活后经 env 落 ECS -->
- [x] 1.2 素材存储演进：`CuratedReferenceImageFormGuess{form,confidence,detectedAt,detectedFor,model,provider?}` 类型（cloud `types.ts` 与 store 双镜像）；归一化白名单显式扩展（非法 formGuess 只丢注解保图片本体）。验证：store 单测覆盖透传/非法剥离 <!-- aidcp-cloud a07ebe0 curated-content-store-form-guess.test.ts 10 测全过；读写路径同经 normalizeCuratedReferenceImages 单漏斗 -->
- [x] 1.3 窄写口 `annotateReferenceImageFormGuess(rowId,index,guess)`：单条 UPDATE + jsonb 路径定点写、WHERE 内嵌 capturedAt 锚比对（锚不符 0 行弃写）；存量缺 capturedAt 项同一条写入顺带落归一化 capturedAt 作锚；绝不 bump `updated_at`。验证：单测覆盖守卫弃写、缺锚项落锚后二次命中缓存、updated_at 不变 <!-- aidcp-cloud a07ebe0 偏离：jsonb 路径用 #> ARRAY[$::text] 而非 ->$::int（单参数双 cast PG 推导不了）；index 语义=JSONB 数组位置（非 item.index 字段），已文档化 -->
- [x] 1.4 `CoverFormSensor` 服务：read-through（`detectedFor===capturedAt` 判新鲜）、只测首张可用图（ossUrl 优先）、30s 内层闸、error 不持久化、no_image/disabled 语义、best-effort 回写。验证：桩客户端单测覆盖 cached/vision/error/低置信/disabled 全分支 <!-- aidcp-cloud a07ebe0 cover-form-sensor.test.ts 13 测全过；另补 resolveCoverFormModel/Provider（env→默认两层解析，面板展示与装配共用） -->
- [x] 1.5 role-catalog 登记 `publish:CoverFormSensor`（llmKind 扩 union 加 'vision'，v1 仅展示、不开面板写入，displayName 标注「模型经 env 配置」）——热点文件单独小 commit 串行集成。验证：typecheck + 面板角色列表不报错 <!-- aidcp-cloud a23f8e5 偏离（评审 must-fix 落地）：facade 加 vision 分支使面板如实展示 env 解析结果（否则会谎报全局文本模型）；ModelEffectiveSource/llmKind union 扩 'vision'（panel/types.ts 同步）；另登记 publish:CoverCardWriter（text、可配模型）；role-config 系 26 测全过 -->

## 2. aidcp-cloud — 渲染（批 B，可与批 A 并行）

- [x] 2.1 字体子集流水线：`scripts/` 子集脚本（Noto Sans SC → AidcpSans SC 改名，8105 规范字+GB2312+Latin-1+CJK 标点 ≈9k 码点）+ `assets/fonts/` Regular/Bold TTF + OFL 许可文件 + `font-manifest.json`（码点+advance+sha256）入仓。验证：manifest sha256 校验 + 覆盖码点抽查（常用标点/数字/全角） <!-- aidcp-cloud dcecef6 8516 码点全覆盖（含 8105 表——经 data/characters.json 拉取，任务原写的 data.json 路径 404）；TTF 各约 2.66MB；重跑字节级一致（recalcTimestamp=False） -->
- [x] 2.2 `src/render/` 分层：text-metrics（字形分段 + advance 行宽，内置 2-3% 安全系数）→ text-card-layout（纯函数：字号阶梯 116/100/84、断行、垂直缩减阶梯、cmap 剥离与过短失败）→ palettes（8×2×3 模板表 + FNV-1a 账号定色板版式 + (账号,帖子)种子定装饰，无位置抖动，seedKey 管道保留）→ text-card（satori→resvg 胶水 + lazy 工厂 + 字体 sha256 校验失败返 null）。验证：布局纯函数单测（截断/缩减/剥离全路径）、同输入 byte-equal、重试恒定、不同账号色板互异、对比度全表 ≥4.5:1 断言、混排 golden（中英数字+全角半角标点）断言无越界像素 <!-- aidcp-cloud dcecef6 test/render 34 测全过（含边缘像素带=背景色断言）；偏离：布局层可产 glyph_uncovered（标题被全剥离时）；生产几何下缩减阶梯 2-3 级实际不可达（最坏 1375px 第 1 级即解），加 contentHeightPx 测试缝供全阶梯用例；额外审计项 bullets_capped_to_5/tags_capped_to_3/tags_row_overflow_trimmed -->
- [x] 2.3 package.json 精确 pin satori + @resvg/resvg-js、提交 lockfile；一枚像素 golden 测试 pin 版本。验证：本地 `npm ci` 后 golden 全过 <!-- aidcp-cloud dcecef6 satori@0.26.0 + @resvg/resvg-js@2.6.2 精确 pin；golden=同进程双渲 byte-equal + 跨实例重试恒定（不存跨平台 sha，防平台栅格差异假红） -->
- [ ] 2.4 （非阻塞，可后置）渲出 48 组合对比页供用户目检冻结色板 hex——先按浅底高对比默认开工，色值后改零成本。验证：用户确认后 palettes 定稿 commit <!-- 非阻塞 follow-up：默认八套浅底高对比已上（对比度全表 ≥4.5 单测锁），目检后改 hex 零成本 -->

## 3. aidcp-cloud — 接线（批 C，依赖批 A+B）

- [x] 3.1 `publish-agent/types.ts` additive 演进：ImageForm/CoverCardCopy{title,bullets,tags}/CoverCardPlan/gateReason/renderStatus/CoverFormAudit/ReferenceImageSnapshot.formGuess/ImagePlan 与 ImageDirective 透传字段/PipelineFields 加键——热点文件与 publish-trigger-and-apply 串行。验证：typecheck + 既有验收基线不红 <!-- aidcp-cloud a07ebe0（formGuess+决策/审计类型）+ f485f09（透传字段）；集成时 origin/master 无并发改动、零冲突 -->
- [x] 3.2 `CoverCardWriter` 角色：门禁序（参照图存在 → 感知【仅感知旗标门控，影子在此落注解+审计】→ 渲染旗标 → 形态置信 ≥`AIDCP_COVER_FORM_MIN_CONFIDENCE`(默认 0.75) → 渲染出口与 OSS 上传器可用）；文案 prompt 只喂洗稿产物（`prompts.ts` 文件尾追加 builder）；产后校验（标题归一化不等 + ≥12 连续字重叠 + 引流词/违禁词闸）+ 剩余预算内重试一次；角色闸 240s、fallback 'skip' 恒写 `coverCardPlan` 兜底；role-catalog 登记。验证：单测覆盖每个 gateReason 分支、flag off 零 LLM、影子模式感知照跑、LLM 失败恒写兜底、重试预算不足直接回落 <!-- aidcp-cloud f485f09 cover-card-writer.test.ts 14 测全过（含预算不足跳过重试、影子模式感知照跑断言）；候选标签取洗稿产物 createdContent.tags（防搬运：原笔记话题不入生成上下文） -->
- [x] 3.3 `ImagePromptComposer` waitAll 扩三键 + 决策盖章透传进 ImagePlan（与角色注册同一 commit 防合流挂死；text_card 时照产 0 号生成式提示词）。验证：单测三键合流 + 盖章透传 + 生成式提示词恒在 <!-- aidcp-cloud f485f09 composer 14 测全过（新增盖章透传 + flag-off 常量两用例） -->
- [x] 3.4 `ImageGenerator` 注入 textCardRenderer + seq0 特判：渲染+ObjectStore 字节直传在进入每图槽之前独立结算（30s 内层闸 `AIDCP_TEXTCARD_RENDER_TIMEOUT_MS`）、成功替换 0 号槽、失败以完整 240s 槽走 0 号生成式提示词、双失败沿既有 M<N；角色总闸公式加渲染超时项；执行器不二次读旗标。验证：单测三级降级链全路径 + 渲染失败后生成式享完整槽预算断言 + 既有并行/保序/部分成功测试不红 <!-- aidcp-cloud f485f09 image-generator-textcard.test.ts 8 测全过（rendered/failed_generative/failed_none/超时独立结算/OSS 直传失败/旧计划无审计零回归/generative 决策零渲染调用）；渲染种子 postKey=referenceNote.sourceId（重试恒定、不含随机 runToken）；既有 generator 28 测不红 -->
- [x] 3.5 `server.ts` 装配（读双旗标 `AIDCP_COVER_FORM_SENSING`/`AIDCP_PUBLISH_TEXTCARD_COVER`、构造 sensor/renderer 注入、角色注册）+ publish-executor 把 CoverFormAudit 并列写入 publishMetadata + panel-store null-safe 解析。验证：flag off 全管线 deep-equal 验收测试（合入门禁）+ 旧行解析 null 断言 <!-- aidcp-cloud f485f09 渲染工厂 lazy：仅渲染旗标开才 import/初始化（关=零加载）；偏离：flag-off 等价性由 publish-orchestrator 全管线测试（30 角色、断言产物形状与现版一致）+ 旧计划无 coverFormAudit 断言 + panel null-safe 断言合力锁定，未另写字面 deep-equal 用例（stamp 常量字段本身即 spec 允许的差异面） -->
- [x] 3.6 回归纪律全跑：`npm run test:acceptance` → `npm test` → `npm run typecheck`（AC-PUB-* 必须全绿）。验证：全绿后提交推送 <!-- worktree: acceptance 44/44 + 全量 1531/1531 + typecheck 零错；land-change 集成序重跑全绿后 ff 推送 origin/master -->

## 4. 部署与真机（批 D）

- [x] 4.1 部署 runbook（`docs/deployment-environments.md`）补「package.json 变更批：rsync → ECS 全量 `npm ci`（禁 `--omit=dev`，tsx 在 devDependencies；registry 备 npmmirror）→ restart → healthcheck」；healthcheck 加渲染冒烟（golden 卡 1728×2304 非零字节）。验证：dev ECS 冒烟通过（顺带验 glibc 兼容） <!-- 2026-07-07 deployed dev@a23f8e5：备份 /opt/aidcp/backups/aidcp-cloud-20260707-234120.{tgz,env} → rsync → npm ci（npmmirror）→ 渲染冒烟 SMOKE OK bytes=100629 dims=1728x2304 theme=warm-gray:poster:corner-arc → restart → 健康全绿（active/NRestarts=0/8787+8090/panel 200/PG ok/飞书 onReady/isales 未碰）；runbook 增补见同批 docs commit -->
- [ ] 4.2 dev 影子模式（感知开渲染关）跑数次真机洗稿发布，经 panel API/psql 核对 sensedForm 准确率与 no_image/error 占比。验证：审计字段回放完整、准确率达标（photo→text_card 假阳性为放行前重点核对项） <!-- 影子模式已于 2026-07-07 在 dev 开启（.env AIDCP_COVER_FORM_SENSING=true、渲染旗标未设=关）；探活：qwen-vl-plus 经 ECS key 对本 change 缘起原图判 text_card conf=0.95（代码默认模型即现役可用）。准确率核对需真机洗稿发布积累 → 已解耦登记 real-machine-acceptance-backlog 簇 13 -->
- [ ] 4.3 达标后 dev 开渲染旗标真机发一帖 text_card 封面、飞书人审复核卡面；真机项登记 `docs/real-machine-acceptance-backlog.md`。验证：发布成功 + 审计 renderStatus='rendered' + 人审通过 <!-- 已解耦登记 real-machine-acceptance-backlog 簇 13（放行渲染=ECS .env 加 AIDCP_PUBLISH_TEXTCARD_COVER=true + 重启，回滚=删行重启） -->

## 5. 控制仓收口

- [x] 5.1 tasks.md 按 sub-repo 分节回写 commit-sha 与偏离说明；`openspec validate textcard-cover-form --strict`；部署验证后 archive（注意与 category-adaptive-images-and-judgment 的 publish-multi-image delta 归档按序）。验证：`openspec list` 无遗留 <!-- 本 commit；publish-multi-image delta 与 category-adaptive 改不同 requirement（并行出图 vs 风格基底），先归档本 change 无冲突 -->

## 6. 可选 follow-up（不阻塞主线）

- [ ] 6.1 console 发布详情只读展示封面形态审计行。验证：面板人工目检
- [ ] 6.2 飞书审批卡加渲染封面预览图（触 feishu 热点文件，与 publish-trigger-and-apply 排期串行）。验证：审批卡人工目检
- [ ] 6.3 面板可写的 vision 角色模型配置层（isModelConfigurable 放行 'vision' + facade 分支 + panel types union + console 展示）。验证：面板改名热生效
