# Tasks — textcard-cover-form

> 依赖序：批 1 感知 → 批 2 渲染（与批 1 可并行）→ 批 3 接线（依赖 1+2）→ 批 4 部署与真机。全程双旗标默认关，各批可独立合入（零行为变化）。热点文件（`role-catalog.ts`、`publish-agent/types.ts`、`image-generator.ts`）改动走单独小 commit、与活跃 change `publish-trigger-and-apply` 串行集成，集成前 rebase 核对（`image-generator.ts` 刚被 record-image-generation-usage 动过）。

## 1. aidcp-cloud — 感知（批 A）

- [ ] 1.1 新建 `src/llm/vision.ts` OpenAI 兼容多模态客户端（content 数组含 image_url；复用 providerRuntime 凭据映射与 token 记账钩子、既有 HTTP 错误语义）；模型解析链「env `AIDCP_COVER_FORM_MODEL`/`AIDCP_COVER_FORM_PROVIDER` → 代码默认（dashscope qwen-vl flash 档，实装时 curl 探活定现役名）」，单测锁死绝不落全局文本模型层。验证：单测 + `npm run typecheck`
- [ ] 1.2 素材存储演进：`CuratedReferenceImageFormGuess{form,confidence,detectedAt,detectedFor,model,provider?}` 类型（cloud `types.ts` 与 store 双镜像）；归一化白名单显式扩展（非法 formGuess 只丢注解保图片本体）。验证：store 单测覆盖透传/非法剥离
- [ ] 1.3 窄写口 `annotateReferenceImageFormGuess(rowId,index,guess)`：单条 UPDATE + jsonb 路径定点写、WHERE 内嵌 capturedAt 锚比对（锚不符 0 行弃写）；存量缺 capturedAt 项同一条写入顺带落归一化 capturedAt 作锚；绝不 bump `updated_at`。验证：单测覆盖守卫弃写、缺锚项落锚后二次命中缓存、updated_at 不变
- [ ] 1.4 `CoverFormSensor` 服务：read-through（`detectedFor===capturedAt` 判新鲜）、只测首张可用图（ossUrl 优先）、30s 内层闸、error 不持久化、no_image/disabled 语义、best-effort 回写。验证：桩客户端单测覆盖 cached/vision/error/低置信/disabled 全分支
- [ ] 1.5 role-catalog 登记 `publish:CoverFormSensor`（llmKind 扩 union 加 'vision'，v1 仅展示、不开面板写入，displayName 标注「模型经 env 配置」）——热点文件单独小 commit 串行集成。验证：typecheck + 面板角色列表不报错

## 2. aidcp-cloud — 渲染（批 B，可与批 A 并行）

- [ ] 2.1 字体子集流水线：`scripts/` 子集脚本（Noto Sans SC → AidcpSans SC 改名，8105 规范字+GB2312+Latin-1+CJK 标点 ≈9k 码点）+ `assets/fonts/` Regular/Bold TTF + OFL 许可文件 + `font-manifest.json`（码点+advance+sha256）入仓。验证：manifest sha256 校验 + 覆盖码点抽查（常用标点/数字/全角）
- [ ] 2.2 `src/render/` 分层：text-metrics（字形分段 + advance 行宽，内置 2-3% 安全系数）→ text-card-layout（纯函数：字号阶梯 116/100/84、断行、垂直缩减阶梯、cmap 剥离与过短失败）→ palettes（8×2×3 模板表 + FNV-1a 账号定色板版式 + (账号,帖子)种子定装饰，无位置抖动，seedKey 管道保留）→ text-card（satori→resvg 胶水 + lazy 工厂 + 字体 sha256 校验失败返 null）。验证：布局纯函数单测（截断/缩减/剥离全路径）、同输入 byte-equal、重试恒定、不同账号色板互异、对比度全表 ≥4.5:1 断言、混排 golden（中英数字+全角半角标点）断言无越界像素
- [ ] 2.3 package.json 精确 pin satori + @resvg/resvg-js、提交 lockfile；一枚像素 golden 测试 pin 版本。验证：本地 `npm ci` 后 golden 全过
- [ ] 2.4 （非阻塞，可后置）渲出 48 组合对比页供用户目检冻结色板 hex——先按浅底高对比八套默认开工，色值后改零成本。验证：用户确认后 palettes 定稿 commit

## 3. aidcp-cloud — 接线（批 C，依赖批 A+B）

- [ ] 3.1 `publish-agent/types.ts` additive 演进：ImageForm/CoverCardCopy{title,bullets,tags}/CoverCardPlan/gateReason/renderStatus/CoverFormAudit/ReferenceImageSnapshot.formGuess/ImagePlan 与 ImageDirective 透传字段/PipelineFields 加键——热点文件与 publish-trigger-and-apply 串行。验证：typecheck + 既有验收基线不红
- [ ] 3.2 `CoverCardWriter` 角色：门禁序（参照图存在 → 感知【仅感知旗标门控，影子在此落注解+审计】→ 渲染旗标 → 形态置信 ≥`AIDCP_COVER_FORM_MIN_CONFIDENCE`(默认 0.75) → 渲染出口与 OSS 上传器可用）；文案 prompt 只喂洗稿产物（`prompts.ts` 文件尾追加 builder）；产后校验（标题归一化不等 + ≥12 连续字重叠 + 引流词/违禁词闸）+ 剩余预算内重试一次；角色闸 240s、fallback 'skip' 恒写 `coverCardPlan` 兜底；role-catalog 登记。验证：单测覆盖每个 gateReason 分支、flag off 零 LLM、影子模式感知照跑、LLM 失败恒写兜底、重试预算不足直接回落
- [ ] 3.3 `ImagePromptComposer` waitAll 扩三键 + 决策盖章透传进 ImagePlan（与角色注册同一 commit 防合流挂死；text_card 时照产 0 号生成式提示词）。验证：单测三键合流 + 盖章透传 + 生成式提示词恒在
- [ ] 3.4 `ImageGenerator` 注入 textCardRenderer + seq0 特判：渲染+ObjectStore 字节直传在进入每图槽之前独立结算（30s 内层闸 `AIDCP_TEXTCARD_RENDER_TIMEOUT_MS`）、成功替换 0 号槽、失败以完整 240s 槽走 0 号生成式提示词、双失败沿既有 M<N；角色总闸公式加渲染超时项；执行器不二次读旗标。验证：单测三级降级链全路径 + 渲染失败后生成式享完整槽预算断言 + 既有并行/保序/部分成功测试不红
- [ ] 3.5 `server.ts` 装配（读双旗标 `AIDCP_COVER_FORM_SENSING`/`AIDCP_PUBLISH_TEXTCARD_COVER`、构造 sensor/renderer 注入、角色注册）+ publish-executor 把 CoverFormAudit 并列写入 publishMetadata + panel-store null-safe 解析。验证：flag off 全管线 deep-equal 验收测试（合入门禁）+ 旧行解析 null 断言
- [ ] 3.6 回归纪律全跑：`npm run test:acceptance` → `npm test` → `npm run typecheck`（AC-PUB-* 必须全绿）。验证：全绿后提交推送

## 4. 部署与真机（批 D）

- [ ] 4.1 部署 runbook（`docs/deployment-environments.md`）补「package.json 变更批：rsync → ECS 全量 `npm ci`（禁 `--omit=dev`，tsx 在 devDependencies；registry 备 npmmirror）→ restart → healthcheck」；healthcheck 加渲染冒烟（golden 卡 1728×2304 非零字节）。验证：dev ECS 冒烟通过（顺带验 glibc 兼容）
- [ ] 4.2 dev 影子模式（感知开渲染关）跑数次真机洗稿发布，经 panel API/psql 核对 sensedForm 准确率与 no_image/error 占比。验证：审计字段回放完整、准确率达标（photo→text_card 假阳性为放行前重点核对项）
- [ ] 4.3 达标后 dev 开渲染旗标真机发一帖 text_card 封面、飞书人审复核卡面；真机项登记 `docs/real-machine-acceptance-backlog.md`。验证：发布成功 + 审计 renderStatus='rendered' + 人审通过

## 5. 控制仓收口

- [ ] 5.1 tasks.md 按 sub-repo 分节回写 commit-sha 与偏离说明；`openspec validate textcard-cover-form --strict`；部署验证后 archive（注意与 category-adaptive-images-and-judgment 的 publish-multi-image delta 归档按序）。验证：`openspec list` 无遗留

## 6. 可选 follow-up（不阻塞主线）

- [ ] 6.1 console 发布详情只读展示封面形态审计行。验证：面板人工目检
- [ ] 6.2 飞书审批卡加渲染封面预览图（触 feishu 热点文件，与 publish-trigger-and-apply 排期串行）。验证：审批卡人工目检
- [ ] 6.3 面板可写的 vision 角色模型配置层（isModelConfigurable 放行 'vision' + facade 分支 + panel types union + console 展示）。验证：面板改名热生效
