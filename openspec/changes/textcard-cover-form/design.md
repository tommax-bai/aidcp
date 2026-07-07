# Design — textcard-cover-form

> 本设计经四视角并行设计（感知/渲染/接线/风险）→ 综合 → 对抗性评审（verdict: approve_with_fixes）产出；评审 7 条 must-fix 与 4 条 YAGNI 裁剪已全部吸收（正文以「修正」标注）。

## Context

- 洗稿链路配图风格 100% 由文字 prompt 决定（LLM 中文主体描述 + 品类风格档模板，`image-prompt-composer.ts:97-100`）；品类分类读的是洗稿后新文本；原图只作构图参考进万相 i2i（`wanxiang-client.ts:128-133`），风格/文字维度与原图零信息通路。
- 「图内无字、封面留白后期叠字」是既有红线（category-adaptive-images-and-judgment design D4），但叠字后处理从未实装——grep 全仓仅 prompt 字符串与注释两处。
- 全链路无任何视觉模型/OCR（grep 零命中）；`src/llm/` 全部为纯文本客户端；小红书图片 alt 恒空（edge `note-extractor.ts:223` 取 img alt 属性）。
- 参照图在精选入库时转存 OSS 并存 `curated_content.reference_images` JSONB（`ReferenceImageSnapshot{index,sourceUrl,ossUrl?,width?,height?,alt?,captureStatus,capturedAt}`）；归一化是严格白名单（`curated-content-store.ts:304-339`），未知字段读写皆被剥除；浏览闭环 `upsertObservation` 带新图时整体替换数组（`:488-491`）。
- 发布全局串行（`publish-scheduler.ts:119-120`）；单次模型调用天花板 180s、每图槽 240s（`image-generator.ts:28-34` 载明预算分解不变量）、流水线总闸 600s（`server.ts:813`）。
- ECS 以 systemd `npx tsx src/server.ts` 直跑源码（tsx 在 devDependencies）；rsync 排除 node_modules；cloud 现无任何原生依赖与字体资产。

## Goals / Non-Goals

**Goals:**
- 原笔记封面为文字卡时，新帖封面产出**同形态、同信息密度、不同表达**的文字卡；其余情况与全部内页维持现链路。
- 给系统补第一块视觉感知能力，并把多模态客户端做成 2.2-2.4（产后校验）可复用的共享缝。
- 双旗标默认关、影子模式先行、全程审计诚实、任一环节失败逐级降级到现有生成式路径——零回归可证。

**Non-Goals:**
- 不实装 2.2 产后校验（只建客户端缝）；不做照片类封面的标题叠字（独立后续，渲染器可复用）；不做内页文字卡；不做 per-persona 品牌配置系统；不做跨帖模板去重注册表；不做非首图封面（守 publish-multi-image 既有 MUST NOT）；不碰边缘与协议；不做「相似度越高越好」——形态借鉴而非复刻（承 curated-reference-images 红线）。

## Decisions

### D1 感知时机：发布时按需（read-through）+ 素材行内联缓存回写
判定在洗稿发布管线内、封面决策消费前执行：先查 `reference_images[0].formGuess` 且 `detectedFor === item.capturedAt`（新鲜度锚，重抓必变、零 TTL）命中即免调用；miss 才调视觉模型，结果 best-effort 回写素材行。只感知第一张有可用 URL 的图（ossUrl 优先、缺则 sourceUrl）。
理由：准入量（1000 行/账号 × ≤9 图）远大于洗稿触发量（个位数/天），入库全量感知 >99% 白花；且观测刷新会整体替换数组、入库注解随时被洗掉；read-through 一套机制同时覆盖历史空行与被刷行，无需 backfill。
**修正（评审 must-fix）**：回写 `annotateReferenceImageFormGuess(rowId, index, guess)` 必须实现为**单条 UPDATE + jsonb_set 定点写目标 item、WHERE 内嵌 capturedAt 锚比对**（PG 行锁下单语句原子，锚不符即 0 行弃写）——JS 读改写整数组是 TOCTOU，会把浏览闭环刚刷新的图集盖回旧值（丢新参照图比丢注解严重）。对 DB 内无 capturedAt 的存量项（归一化层读取时回填 read-time now、锚永不匹配），同一条写入顺带把归一化 capturedAt 落盘作锚，避免「缓存永不命中、每次发布白付一次视觉调用」。回写绝不 bump 行 `updated_at`（`selectForCreation` 按其排序，抬了扰动创作召回）。回写失败只记日志。
否决：入库时感知（成本倒挂+注解不保+仍需发布时兜底=两套机制）；独立缓存表（URL 非内容身份，徒增表+join）；感知全部 9 张（只有封面驱动行为，schema 按 item 设计留扩缝）。

### D2 感知方式：视觉模型单次调用、严格 JSON、带弃权
输出限定 `{form: text_card|photo|illustration|other, confidence: 0..1, reason}`；解析沿精选评估角色的严格范式，核心字段缺失/类型不符 → error，绝不默认成功；置信阈值 `AIDCP_COVER_FORM_MIN_CONFIDENCE`（默认 0.75）在**消费端**施加、判定原样持久化（存观测不存策略，调阈值不重测存量）；error 不持久化（无负缓存——错误多瞬态，发布触发频率低）。内层闸 `AIDCP_COVER_FORM_TIMEOUT_MS` 默认 30s。
**修正（YAGNI 裁剪）**：砍 textDensity 三档——洗稿正文本身决定要点有无，误判影响为零，感知输出越窄越稳。
否决：像素统计启发式（需原生解码依赖+阈值不可标定+错了就是静默错）；alt 元数据（恒空，死路）；边缘侧感知（违边轻云重+协议四处同步+主动命令白名单静默丢弃陷阱）。

### D3 形态枚举与新鲜度
持久化枚举四值（screenshot 并入 other——无行为差异的分类是死分类）；管线层 `sensedForm` 另含 `unknown` 表「未感知/失败/低置信」，保「数据缺失不得误判」可审计。`CuratedReferenceImageFormGuess{form, confidence, detectedAt, detectedFor, model, provider?}`；归一化白名单显式扩展并校验（form 枚举、confidence 有限数 ∈[0,1]、时间戳正整数），非法即丢 formGuess 保图片本体。不做 upsert merge 对抗——注解是缓存，被刷掉=下次重测，自愈。

### D4 双旗标与影子模式
`AIDCP_COVER_FORM_SENSING`（感知）+ `AIDCP_PUBLISH_TEXTCARD_COVER`（决策+渲染），均默认关。感知开+渲染关=影子模式：注解与审计照落、封面照走生成式，面板核准确率后再放行渲染。photo→text_card 假阳性是最伤方向（错形态卡比通用图更违和），影子先行让判定质量零风险可观测；回滚=关旗标+重启。
**修正（评审 must-fix，门禁顺序）**：感知**只由感知旗标门控、先于且独立于渲染旗标执行**；渲染旗标只门控决策+文案 LLM。若按「渲染旗标第一关、任一不过零调用」实现，影子模式会被短路永不感知——spec 正文与角色内部顺序均按此统一（见 D6）。

### D5 多模态客户端隔离（2.2-2.4 共享缝）
新建 `src/llm/vision.ts` OpenAI 兼容多模态客户端（content 数组含 image_url），完整复用启动期厂商凭据映射（`server.ts` providerRuntime）与 token 记账钩子；dashscope 与 volcengine 的 compatible-mode 端点均接受该形状，零新增凭据面。**模型解析链绝不进全局文本模型回落层**（文本模型收到 image_url 会 400 或走错厂商——正确性问题非风格问题），单测锁死。
**修正（评审 must-fix，v1 收敛）**：现役 `isModelConfigurable` 只放行 `llmKind==='text'`（`role-catalog.ts:158-161`），面板对 vision 角色的模型写入会被拒、展示层会谎报回落文本模型。v1 解析链收敛为**env（`AIDCP_COVER_FORM_MODEL`/`AIDCP_COVER_FORM_PROVIDER`）→ 代码默认（dashscope qwen-vl flash 档，实装时 curl 探活定现役名）**两层；role-catalog 登记 `publish:CoverFormSensor`（llmKind 扩 'vision'）**仅作展示**（displayName 标注「模型经 env 配置」），面板可写的 vision 配置层列为独立 follow-up。换名恢复路径=改 env+重启（百炼下架潮场景）。
否决：扩品类分类角色兼判形态（输入域正交：它看洗稿新文本，形态是原图属性；且 2.2 无法复用）；复用文本客户端加参数（消息形状不同，污染文本调用面）。

### D6 决策与文案合一：新角色 CoverCardWriter
watch `[createdContent, postCategory]` waitAll、与图集选题角色并行（关键路径零新增串行延迟）。内部顺序（承 D4 修正）：**参照图存在 → 感知（仅感知旗标门控，影子在此完成注解+审计）→ 渲染旗标 → 形态与置信 → 渲染出口与 OSS 上传器可用** → 全过才调一次文本 LLM 产 `CoverCardCopy{title, bullets 0-5, tags ≤3}`。恒写管线键 `coverCardPlan`（fallback 'skip' + 默认输出=生成式兜底），下游三键合流永不挂死（沿品类分类角色先例，`base-role.ts:100-107`）。
**修正（评审 must-fix，角色闸预算）**：`timeoutMs ≈ 240s`（30s 感知 + 一次 180s 文案 + 余量）；文案违规重试一次**只在角色闸剩余预算内执行**，预算不足直接回落生成式，不做第二次全额调用——否则最坏 390s 串进管线把 600s 总闸顶爆（诚实 failed 但白丢发布额度）。
**修正（YAGNI 裁剪）**：CoverCardCopy 砍 badge 角标字段——对「同形态同密度」非必要，模板侧留槽不接 LLM。
否决：扩图集选题角色条件输出卡文案（条件 schema 使本就脆的解析更脆+违「双任务稀释准确率」的既有拆分定案）；独立裁决角色+文案角色（多一键一层挂死面）；确定性切正文当要点（散文非列表，产出不可控=静默丑成功）。

### D7 渲染栈：satori + @resvg/resvg-js，云端进程内
satori（纯 JS + yoga WASM，object-JSX 免 react）排版 → SVG，@resvg/resvg-js（napi 预编译平台包，走 registry/npmmirror，无 GitHub postinstall）栅格化 PNG。四备选中唯一同时满足：零 apt 依赖（不碰同机 isales）、零协议改动、字体入仓确定性、可脱网单测。版本精确 pin + lockfile 提交。工厂 lazy dynamic import + 字体 sha256 校验，任一失败 → 返回 null + 显式告警：服务启动不崩，text_card 请求诚实降级生成式（audit `renderer_unavailable`）。
否决：node-canvas（apt cairo/pango 动共享 OS 状态）；sharp+SVG text（fontconfig CJK 不可控）；边缘 Chromium 渲染（协议四处同步+白名单陷阱+发布被边缘在线率绑架）；puppeteer（300MB 与 isales 抢内存）；resvg-wasm 双轨兜底（为假想失败提前双轨=过度设计）。

### D8 字体：Noto Sans SC（OFL 1.1）子集化改名入仓
《通用规范汉字表》8105 字 + GB2312 + Latin-1 + CJK 标点 ≈9k 码点，Regular+Bold 共约 7MB；name 表改「AidcpSans SC」（OFL 保留名合规）；同仓提交子集脚本与 `font-manifest.json`（码点集合 + 每码点 advance 宽度 + sha256）。advance 清单是确定性行宽测量的引擎（运行时零字体解析、断行可单测）——这是子集流水线的主收益而不只是省体积。渲染前 cmap 覆盖预检：未覆盖码点（含 emoji）确定性剥离并审计，剥后标题过短 → 显式失败降级。
否决：全量不子集（30-35MB×2 入仓、satori 嵌全量更慢，cmap 校验与降级路径照样要建）；阿里普惠体（许可禁修改、子集化即修改，法律灰区）。

### D9 画布
逻辑设计网格 1080×1440（3:4），resvg 输出 1728×2304——与 ECS 现役生成式配图像素一致（env `AIDCP_SEEDREAM_IMAGE_SIZE=1728x2304`），图集内不混尺寸。渲染耗时 ~0.5s。

### D10 主题：离散格点确定性选取（**修正：砍抖动层**）
8 色板 × 2 版式 × 3 角部装饰 = 48 离散组合。FNV-1a(accountId) 定账号主配色对与版式（账号内视觉身份稳定=像真人品牌）；FNV-1a(accountId+sourceId，缺则标题哈希) 只定装饰选择（账号间分散、不可聚类）。色板 hex 固定，对比度 ≥4.5:1 离线全表单测可证；同 (账号,帖子) 重试字节恒定（种子刻意不含随机运行令牌，可测不变量）。绝不从参照图取色。
评审裁剪理由：每帖标题/要点文本本就不同，PNG 字节天然互异，位置抖动层对平台侧同质化检测增量≈0，却带来一整层参数边界+重试恒定性测试面；seedKey 管道保留，抖动维度后补零成本。
否决：帖帖随机换皮（真人恰有稳定视觉身份+随机不可测）；per-account 面板配置（YAGNI，token 化色板留缝）；跨帖去重注册表（1-2 帖/天/账号，48 组合远超车队规模）。

### D11 渲染器契约：独立接口、布局所有权自持
注入 `ImageGeneratorDeps` 可选字段；**绝不实现生图提供方接口、绝不进路由表**（渲染不吃 prompt，硬套 generate(prompt) 是假接口，进路由就存在被跨源 fallback 的可能）。输入仅 `(copy, seedKey)`——签名不含品类、不含任何原图信息（防搬运的编译期结构保证）。返回显式结果：成功带 PNG 字节 + meta（paletteId/layoutId/字号/行数/truncated/sanitized/reductions），失败带原因枚举（invalid_copy|glyph_uncovered|render_failed）。断行/字号阶梯（116/100/84）/垂直缩减阶梯（要点行数→条数→丢标签行）全部自有纯函数，satori 只做盒子定位（每行 nowrap）——CJK 断行黑盒怪癖不进布局所有权，升级依赖不改布局。
**修正（评审 must-fix，字形度量差）**：自算 advance 行宽与 satori 实际排版存在字形度量差（Latin kerning、标点挤压），行宽预算内置 **2-3% 安全系数**（CJK 无 kerning 基本零损、Latin 混排吃余量），并在布局单测/golden 集强制**混排样例**（中英数字混合、全角半角标点相邻）断言渲染产物无越界像素——该余量是布局所有权契约的一部分。

### D12 执行分支与降级链（**修正：渲染在每图槽机制之前独立结算**）
配图执行角色 seq 0 特判：`coverForm==='text_card'` 且 card 与渲染器与 OSS 上传器俱在才渲染（上传器缺席在门禁即关 `renderer_unavailable`——渲染字节没有 provider 临时 URL 可用）。**渲染+字节直传 OSS 在进入每图超时槽机制之前独立结算**（内层闸 `AIDCP_TEXTCARD_RENDER_TIMEOUT_MS` 默认 30s）；成功=替换 0 号槽产出（不前插不移位，seq/imageCount/内页序全不变）；失败后 0 号以**完整每图槽预算（240s）**用计划内恒在的生成式提示词走 provider；双失败落既有 M<N 保序过滤（封面由首张成功内页顶上）。角色总闸公式相应加渲染超时项（`perImageTimeoutMs × waves + renderTimeoutMs + 余量`）。
评审修正理由：若渲染共用每图槽，最坏序列 30s 渲染 + 185s 万相轮询尾部 + 30s 转存 = 245s > 240s，兜底生图会在收尾前被槽闸砍掉——由本特性引入的尾部回归，违反 `image-generator.ts:28-34` 载明的预算分解不变量。
单一决策源=coverCardPlan（经 ImagePromptComposer 盖章进 ImagePlan），执行器不二次读旗标（防「plan 说渲、执行器说旗标关」裂脑）。
否决：渲染封面前插内页后移（破坏 imageCount 语义与保 0 号去重护栏）；执行角色改 waitAll 两键（破坏「配图计划=唯一完整指令」的决策执行解耦契约）。

### D13 防搬运：结构隔离 + 文案校验，不做相似度度量
R1 感知输出类型收窄为枚举（无颜色/坐标/OCR 字段）、渲染链路对原图像素/URL 零入口——既有「参照图可借色彩构图」许可对文字卡渲染路径**明确不适用**。R2 文案 prompt 只喂洗稿产物；产后校验器（可读原文但不入 prompt）断言：卡面标题≠原标题（归一化后）、任一行与原标题/正文无 ≥12 连续字符逐字重叠、无原作者名/水印词/二维码/联系方式/价格促销词、过既有违禁词闸；违规带紧约束重试一次（角色闸剩余预算内），仍违规回落生成式。R5 AI 标识只走既有合规元数据+发布声明，卡面绝不画水印（违 2.3 定案+自造跨号聚类指纹）。
否决：pHash 相似度阈值闸（需把原图像素引入渲染链=污染入口，且文字卡低熵图上不可标定）；渲染产物再过视觉 QA（确定性渲染+校验断言已在源头消灭乱码/溢出类假成功，无增量信息且把 2.2 耦进来）。

### D14 审计
`CoverFormAudit{coverForm('generative'|'text_card' 二值决策), sensedForm, sensedSource('cached'|'vision'|'none'), gateReason(ok|flag_off|no_reference_images|form_unknown|low_confidence|form_not_text_card|renderer_unavailable|copy_llm_failed), renderStatus(not_attempted|rendered|render_failed_generative|render_failed_none), renderMeta?{themeKey,truncated,sanitized,reductions}}`，与参照图审计并列落 ImageDirective 与 publishMetadata，面板 null-safe additive。决策与执行结局分离（比三值 coverForm 正交，每跳可回放「为什么这帖没出文字卡」）。诚实红线：降级用了生成图绝不标 text_card、unknown 绝不猜成 text_card。

### D15 运维（**修正：全量安装**）
依赖精确 pin；部署 runbook 增补「package.json 变更批必须 ssh 到 ECS 跑**全量 `npm ci`**（或沿既有文档 `npm install`，`deployment-ecs.md:270,291`；registry 备 npmmirror），顺序 rsync → npm ci → systemctl restart → healthcheck（含渲染冒烟）」。**禁用 `npm ci --omit=dev`**：ECS 以 `npx tsx src/server.ts` 直跑源码，tsx/typescript 在 devDependencies，omit 后重启即崩。健康检查渲染冒烟=渲一张 golden 卡断言 1728×2304 非零字节（顺带验证 napi 预编译包与该机 glibc 兼容）。回滚=关旗标+重启；深回滚走既有备份序列。字体资产随 rsync 自动走（排除项不误伤 assets）。

## Risks / Trade-offs

- [photo→text_card 假阳性（最伤方向）] → 0.75 阈值消费端施加 + 影子模式先行核准确率 + 边缘默认人审闸兜底；unknown/低置信/解析失败一律弃权走生成式，无任何猜形态路径。
- [视觉模型下架/限流（百炼下架潮）] → error 弃权不阻发布 + env 换名免代码改动；无负缓存使瞬态故障自愈。
- [napi 预编译包与 ECS glibc 不兼容 / npm install 漏跑] → lazy 工厂→null→诚实降级（服务不崩）；健康检查渲染冒烟把兼容性验证前置到部署环节；runbook 显式步骤化。
- [混排标题溢出（自算行宽 vs satori 度量差）] → 2-3% 安全系数 + 混排 golden 断言无越界像素；溢出消解全程审计，无法消解显式失败。
- [模板同质化新指纹] → 账号哈希定主题（账号间分散）+ 文本天然互异；发布量 1-2 帖/天/账号下 48 组合充足；若车队扩容再补抖动层（seedKey 管道已留）。
- [浏览闭环并发刷新 vs 注解回写] → 单条 UPDATE + WHERE 锚比对原子弃写；绝不整数组回写。
- [CoverCardWriter 尾部把 600s 总闸顶爆] → 角色闸 240s + 重试只花剩余预算；典型值感知 1-3s + 文案十几秒，被并行角色掩盖。
- [热点文件撞车] → role-catalog.ts/types.ts 与 publish-trigger-and-apply 串行小 commit；image-generator.ts 集成前 rebase 核对（record-image-generation-usage 刚动过）；publish-multi-image delta 与 category-adaptive 改不同 requirement、归档按序。

## Migration Plan

批 A 感知（vision.ts + store 演进 + sensor 服务）→ 批 B 渲染（字体流水线 + src/render/ 分层）→ 批 C 接线（types/角色/composer/generator/server 装配 + flag-off deep-equal 验收）→ 批 D 部署（依赖 pin + runbook + 冒烟 → dev 影子模式核准确率 → 放行渲染旗标真机一帖 + 飞书人审复核）。批间可独立合入（全程旗标关=零行为变化）。回滚：关旗标+重启（秒级）；深回滚走既有备份序列。

## Open Questions

- 视觉模型定名：默认 dashscope qwen-vl flash 档，实装时 curl 探活定现役名（下架潮在即，env 可换名）。需用户认可厂商取向。
- 字体许可：推荐 Noto Sans SC（OFL）子集改名，约 7MB 入仓。需用户确认接受 OFL 路线与仓库体积。
- 色板视觉冻结：8 色板 hex 实装后渲 48 组合对比页供目检（**非阻塞**，先按浅底高对比默认开工，色值后改零成本）。
- emoji：v1 卡面完全无 emoji（文案生成禁用+校验剥离）；需要点缀则后补 emoji 字体（+10-25MB）。推荐 v1 接受无 emoji。
- 飞书审批卡加渲染封面预览：人审是防搬运最后复核，推荐加，但触 feishu 热点文件，列为可选 follow-up 与 publish-trigger-and-apply 排期串行。
- 面板可写的 vision 角色模型配置层（isModelConfigurable/facade/panel types/console 四处）：v1 用 env，面板层独立 follow-up。
