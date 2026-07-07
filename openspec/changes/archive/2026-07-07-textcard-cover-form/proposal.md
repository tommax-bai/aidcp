# textcard-cover-form — 文字卡封面形态跟随 + 原图形态感知

## Why

洗稿发布的配图与原笔记形态严重脱节：知识/教程类原笔记的封面几乎都是「排版文字卡」（标题+要点的海报式封面，信息密度高），而现链路封面按品类风格档纯生图产出（tech 类还是全库唯一的矢量插画档），且「图内无字、留白后期叠字」红线中的叠字环节从未实装——产出封面既无模型画的字也无程序叠的字，钩子信息量归零（实例：`publish/66cd1d4f…/03462eb06a4e/0.png` vs 原图文字卡）。系统全链路无任何视觉感知，「原图是文字卡」这一事实进不了任何决策。

## What Changes

- **原图形态感知**：洗稿发布时对原笔记封面（参照图第一张）做视觉模型分类（`text_card|photo|illustration|other`+置信度），发布时按需执行、结果回写素材行作缓存（以图片抓取时间戳为新鲜度锚，重抓自动失效）；新建 OpenAI 兼容多模态客户端（复用既有厂商凭据与 token 记账），此客户端即后续产后校验（category-adaptive-images-and-judgment 任务 2.2-2.4）的共享缝，本 change 不实装 2.2。
- **文字卡确定性渲染**：原封面判为文字卡且置信达标时，新帖封面由云端进程内确定性排版渲染产出同形态文字卡（洗稿标题+要点+标签），satori+resvg 栈、子集化 OFL 字体入仓、断行/字号/缩减全部纯函数所有权、主题由账号哈希从本系统模板表确定性选取；绝不从原图取色/取版式（防搬运结构隔离）。
- **发布管线接线**：新增封面形态决策角色（门禁+卡片文案 LLM，恒写管线键防合流挂死）；配图执行角色 0 号封面槽特判渲染、失败立即落回恒在的 0 号生成式提示词、双失败沿用既有少图保序语义；全程审计（感知来源/门禁原因/渲染结局），降级绝不谎标。
- **双旗标默认关**：感知旗标 + 渲染旗标全关时行为与现版逐字节等价；感知开+渲染关=影子模式（注解与审计照落、封面照走生成式），先核判定准确率再放行渲染。
- 运维：aidcp-cloud 首次引入运行时依赖（satori、@resvg/resvg-js，精确 pin）与字体资产；部署序列补 ECS 生产依赖安装步骤（全量安装——服务以 tsx 直跑源码，tsx 在 devDependencies，禁用 `--omit=dev`）；健康检查加渲染冒烟。

## Capabilities

### New Capabilities
- `cover-form-sensing`: 发布时按需的原图封面形态视觉判定、素材行缓存回写、弃权语义与多模态客户端隔离。
- `text-card-rendering`: 云端确定性文字卡渲染——渲染栈与字体资产、字形覆盖与溢出红线、主题确定性与反指纹、渲染输入结构隔离（防搬运）。
- `publish-textcard-cover`: 发布管线的封面形态决策角色、卡面文案独立与产后校验、执行分支与诚实降级链、旗标/影子模式/零回归。

### Modified Capabilities
- `publish-multi-image`: 「并行出图且每张独立计时」requirement 放宽——0 号封面槽在配图计划决策为文字卡且渲染依赖俱备时 MAY 由注入的确定性渲染器产出（渲染在进入每图超时槽机制之前独立结算，失败后以完整每图槽预算走生成式兜底），其余张语义不变；渲染器 MUST NOT 实现生图提供方接口或进入其路由。

## Impact

- **代码**：仅 aidcp-cloud（边缘与协议零改动）。感知：`src/llm/vision.ts`（新）、`src/cache/curated-content-store.ts`（JSONB 白名单扩展+窄写口）、`src/config/role-catalog.ts`（登记，热点文件需串行）；渲染：`src/render/`（新，分层纯函数）、`assets/fonts/`（新）、`scripts/` 子集化脚本；接线：`src/publish-agent/types.ts`、新角色文件、`roles/image-prompt-composer.ts`（waitAll 扩键+盖章透传）、`roles/image-generator.ts`（注入渲染器+seq0 分支）、`src/server.ts` 装配、`prompts.ts` 文件尾追加 builder。
- **依赖**：satori + @resvg/resvg-js（精确 pin，napi 预编译走 registry/npmmirror，零 apt 依赖，不碰同机 isales）；Noto Sans SC 子集化改名字体约 7MB 入仓（OFL 1.1 合规）。
- **数据**：`curated_content.reference_images` JSONB item 加可选 `formGuess`（读写白名单双向兼容，旧行零迁移）；发布元数据加 `CoverFormAudit`（沿参照图审计先例，面板 null-safe 解析）。
- **部署**：dev ECS 需一次生产依赖安装（rsync 排除 node_modules）；回滚=关旗标+重启。
- **并行协调**：`role-catalog.ts`/`types.ts` 与活跃 change `publish-trigger-and-apply` 串行集成；`publish-multi-image` 的 delta 与活跃 change `category-adaptive-images-and-judgment` 改不同 requirement、可共存但归档按序；`image-generator.ts` 刚被 record-image-generation-usage 动过，集成前 rebase 核对。
