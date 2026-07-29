# Tasks — image-postcheck-vision-model

## 1. Contract and storage

- [x] 1.1 定义整组视觉分析、类型专用 frame spec、风格聚类、逐槽参考绑定和视觉审计类型；所有新字段对历史数据可选/null-safe。
- [x] 1.2 `curated_content` 启动 schema 新增视觉分析 JSONB；以图片抓取锚 + provider/model/schema version 为 cache key，缓存命中零模型调用、失败不伪造成功。
- [x] 1.3 精选读取/洗稿触发透传缓存结果；不把 OCR 文本或原图具体文案纳入视觉分析契约。

## 2. aidcp-cloud — visual reverse analysis

- [x] 2.1 新增 `VisualReferenceAnalyzer`：整组分类/序列/聚类 → 按摄影、插画/3D、文字卡、UI/文档、图表信息图、混合类型分组专用分析 → 汇总 `setStyleBible + styleClusters + frameSpecs`。
- [x] 2.2 严格 JSON 解析、调用超时、分组有界并发、token usage 记账与诚实 `unavailable/partial` 状态；默认旗标关闭并支持影子落库。
- [x] 2.3 管线角色恒写键并接入 planner/composer；反推可用时源风格优先，现有内容品类风格仅作兜底。
- [x] 2.4 将整组分析改为轻量 set pass + specialist 小批次有界并发，提升 7–9 张文字卡分析可靠性；升级 cache schema，超时/失败状态不得在执行审计中丢成 `none`。 <!-- aidcp-cloud 753d66b -->
- [x] 2.5 扩展人物摄影 specialist：表情、视线、头部角度、身体姿态、手势、姿态能量及情绪效价/唤醒度；升级 cache schema，历史 v2 自动失效重算。 <!-- aidcp-cloud c77683e -->

## 3. aidcp-cloud — slot binding and provider

- [x] 3.1 `ImageSetPlanner` 按有效源图顺序产出 sourceArrayIndex/sourceIndex，视觉反推产出 sequenceRole；1/3/8/9 图均保持槽位顺序且图 0 仍为封面/钩子位。
- [x] 3.2 `ImagePlan` 为每槽生成独立参考绑定；默认仅绑定该槽主参考，绝不再把整组参考图传给每槽。
- [x] 3.3 Wan 多图请求明确各图片角色并保证主参考图最后；provider 返回真实参考使用状态，失败不进入发布 URL。
- [x] 3.4 文字卡保留确定性渲染；UI/文档、图表、混合类记录诚实路由状态，未接结构化重绘器时不得标为 deterministic redraw。
- [x] 3.5 为确定性文字卡派生白名单来源设计令牌（内部色板、渐变/网格、信息卡、分页、密度、中文词组断行），旗标关或分析不可用保持现有模板行为。 <!-- aidcp-cloud 753d66b -->
- [x] 3.6 将 `ImageSetPlanner` 补成内容视觉导演：读取有界首/中/尾正文，为每槽生成 `contentVisualBrief`；composer 明确正文人物表演优先、参考只管摄影语言及人物身份泛化。 <!-- aidcp-cloud c77683e -->
- [x] 3.7 将 `contentVisualBrief` 扩为公共字段 + 八类判别式 `categoryBrief`；反推 frame 可用时按源图类型校正，composer/fallback/文字卡文案分别消费对应分类语义。
- [x] 3.8 自主创作新增文章级 `visualSetBrief` 和固定枚举 `slotRole`；LLM 缺失/非法/失败时确定性兜底，洗稿张数和来源绑定行为零回归。
- [x] 3.9 composer 将原创槽位职责、整组连续性和类型参数写入生成指令，并按 `categoryBrief.kind` 诚实标记 generative/deterministic/specialized/region-guided 路由。

## 4. aidcp-cloud — visual fidelity audit

- [x] 4.1 新增 `VisualFidelityAuditor`，比较主参考与生成图，输出形态/主体/构图/色彩/风格分数及真人、乱码、水印、逐字复制/原创风险。
- [x] 4.2 不通过时每槽有界重生成一次；重试仍失败则丢弃该槽。视觉模型不可用时标 `unverified`，MUST NOT 假 pass。
- [x] 4.3 逐槽绑定、路由、分析来源和审计结果汇总到 `ImageDirective`/发布 metadata，M<N 继续按既有保序语义发布。
- [x] 4.4 确定性文字卡同样执行产后视觉比较；首次失败以严格来源令牌重渲染一次，二次失败丢槽，模型不可用诚实 `unverified`。 <!-- aidcp-cloud 753d66b -->
- [x] 4.5 审计增加 `contentAlignment` 与逐槽 brief；已有失败后重试审计 `unverified` 必须丢槽，不得覆盖已知真人/乱码/原创风险。 <!-- aidcp-cloud c77683e -->
- [x] 4.6 `contentAlignment` 按分类字段核验人物、文字信息结构、图表关系、场景事件、静物状态、插画隐喻、UI 任务和拼贴分区；图表/UI 增加禁止编造数据/能力的提示约束。
- [x] 4.7 新增自主创作 `content_alignment` 审计模式：无主参考图时按 slot/type/brief 核验，复制检查标不适用，失败有界重试且未知不得覆盖已知失败。

## 5. aidcp-console — explainable audit

- [x] 5.1 精选素材详情显示视觉分析状态、风格来源、类型/风格簇与缓存模型；旧行无字段时显示未分析、不报错。
- [x] 5.2 发布详情显示 source→output 槽位绑定、生成路由、是否使用参考图、逐槽评分/风险/重试与未核验原因；不得把 `used` 等同于“保真通过”。
- [x] 5.3 发布详情展示逐槽正文情绪/人物表演 brief 与内容一致性分数，历史记录 null-safe。 <!-- aidcp-console 2b58528 -->
- [x] 5.4 发布详情按八类可读展示 `categoryBrief`，不直接 dump JSON，历史无分类字段时维持现有展示。
- [x] 5.5 发布详情展示原创图集策略、槽位职责和审计模式；原创内容核验不得显示成参考图保真，复制检查不适用须可解释且历史 null-safe。

## 6. Verification and rollout

- [x] 6.1 单测覆盖严格解析、缓存命中/失效、非摄影字段差异、失败诚实状态、源风格优先与旧行为 flag-off 回归。
- [x] 6.2 单测覆盖 1/3/8/9 图顺序、每槽独立绑定、Wan 主参考最后、缺图保序、文字卡回归。
- [x] 6.3 单测覆盖 audit pass/fail/retry/unavailable、乱码/真人/水印/复制风险及 metadata/panel null-safe。
- [x] 6.4 cloud/console typecheck 与目标测试通过；`openspec validate image-postcheck-vision-model --strict` 通过。
- [x] 6.5 提交、推送、落默认分支并部署 dev；只开启反推影子并完成一组真实 UI/文档样本反推与缓存复用验证，绑定/源风格/审计保持关闭。
- [ ] 6.6 按 `docs/real-machine-acceptance-backlog.md` 簇 83 完成同素材生成 A/B、逐槽绑定、源风格与产后审计真图验收，再逐阶段开 dev 旗标。
- [x] 6.7 补齐轻量 set/specialist 分批、来源文字卡设计令牌、中文词组断行、确定性卡审计/重渲染/丢槽及 flag-off 回归测试。 <!-- aidcp-cloud 753d66b；2026-07-15 deployed dev -->
- [x] 6.8 补齐正文首/中/尾摘录、视觉 brief 解析/兜底、人物 prompt 冲突优先级、人物反推 v3、contentAlignment 及 failed→unverified 丢槽回归测试。 <!-- cloud full 2082/2082; targeted 64/64 + 38/38; console 123/123 + 1 skipped -->
- [x] 6.9 覆盖八类严格解析、分类兜底/源类型校正、分类 prompt、文字卡首/中/尾语义、分类审计与控制台 null-safe 展示；通过 acceptance、全量测试、typecheck、build 和 OpenSpec strict。
- [x] 6.10 覆盖原创 1/多图策略、槽位职责兜底、类型路由、内容审计 pass/fail/retry/unavailable、copy not-applicable 和参照路径零回归。
- [x] 6.11 cloud/console acceptance、目标测试、全量测试、typecheck/build 与 OpenSpec strict 通过；提交推送、快进默认分支、部署 dev 并回写健康与未完成真实样本边界。

## 7. Change record

- [x] 7.1 回写 commits、validation、deploy 和未完成真实样本验收项。
- [ ] 7.2 6.6 全部满足后 archive。

### 7.1 Record (2026-07-15)

- cloud `023b5da`、console `8c27fc2` 已 fast-forward 到各自 `origin/master`。
- cloud acceptance + 全量 `2061/2061`、typecheck、build 通过；console 全量 `123/123`（另 1 skipped）、typecheck、build 通过；OpenSpec strict validate 通过。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-110212.visual-reference.tar.gz` 与同时间戳 `.env` 备份；cloud/console checksum 复核无漂移。
- dev 健康：`aidcp-cloud.service=active`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、console 新资产 HTTP 200、飞书 `WSClient onReady`。
- DB：`curated_content.visual_analysis` 已以幂等启动 DDL 建为 `jsonb`。真实影子样本 row 342（2 图）由 `dashscope/qwen3.7-plus` 得到 `analyzed`，两帧均为 `ui_document` + `ui_document` 专用字段；未混入摄影参数。首次整组+专用两次调用分别 7712/6967 tokens，第二次复跑缓存命中且零模型调用。
- dev 当前仅 `AIDCP_REFERENCE_VISUAL_ANALYSIS=true`；`AIDCP_REFERENCE_VISUAL_BINDING=false`、`AIDCP_REFERENCE_SOURCE_STYLE=false`、`AIDCP_VISUAL_FIDELITY_AUDIT=false`。未触发真实洗稿、未生成草稿、未做真人/摄影/文字卡/图表同素材 A/B；这些边界登记在簇 83。

### 7.1 Follow-up record (2026-07-15 12:10)

- cloud `753d66b` 已 fast-forward 到 `origin/master` 并部署 dev；控制面四个视觉旗标均保持开启，新增超时/分批使用代码默认 `120s / 3张`。
- 反推改为轻量 set pass + specialist 三张一批有界并发，cache schema 升为 `visual-reference-v2`；七张同类文字卡测试确认调用为 `1 + 3` 批。
- 确定性文字卡现在从反推结果派生内部色板、渐变/细网格、信息卡、页码和中文词组断行，并进入主参考图产后审计；首次失败严格重渲染，二次失败丢槽，模型不可用保留并标 `unverified`。
- validation：acceptance `50/50`、cloud 全量 `2072/2072`、目标回归 `59/59`、typecheck、build、OpenSpec strict 均通过；视觉样张复核为 1728×2304，薄荷渐变/细网格/卡片/分页已生效，“模型”未跨行拆字。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-120918.textcard-style-fidelity.tar.gz`、`/opt/aidcp/cloud/.env.bak.20260715-120918`；部署内容 checksum 与 `753d66b` 快照一致。
- dev 健康：`aidcp-cloud.service=active`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、PG `select 1`、飞书 `WSClient onReady`；同机四个 isales 服务保持 running。
- 尚未代用户再次触发真实洗稿，6.6 保持 pending；下一次同素材测试将验证 v2 反推、来源文字卡令牌与产后审计的真实记录。

### 7.1 Content-semantics follow-up record (2026-07-15 14:07)

- cloud `c77683e`、console `2b58528` 已快进到各自 `origin/master`；OpenSpec 契约提交 `0063f12` 已快进到 `origin/main`。
- `ImageSetPlanner` 现在读取有界首/中/尾正文并逐槽生成 `contentVisualBrief`；composer 明确正文控制情绪、神态、视线、动作与姿态，参考图只控制画面类型、景别/镜头、构图、光影、色调和材质。人物允许按正文清晰露脸，但必须身份泛化，不得对应来源真人/名人或复制 logo/平台标识。
- 摄影 specialist cache schema 升为 `visual-reference-v3`，新增表情、视线、头部/身体姿态、手势、姿态能量及效价/唤醒度；v2 缓存自动失效。生成式产后审计新增 `contentAlignment`；已知失败后第二次 `unverified` 必须丢槽。确定性文字卡仍做视觉保真审计，但不为正文一致性 OCR 卡面文字。
- validation：cloud 全量 `2082/2082`、目标回归首轮 `64/64` 与收口 `38/38`、typecheck、build；console 全量 `123/123`（另 1 skipped）、目标 `20/20`、build；OpenSpec strict 均通过。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-1405-image-content.tar.gz`、`/opt/aidcp/cloud/.env.bak.20260715-1405-image-content`、`/opt/aidcp/console.bak.20260715-1405-image-content.tar.gz`。部署后 cloud/console 干净提交快照按 checksum 复核无内容漂移。
- dev 健康：`aidcp-cloud.service=active`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、console HTTP 200、PG 校验 `ok=1`、飞书 `WSClient onReady`；四个 isales 服务均 active/running。四个视觉旗标均为 `true`。
- 本次发布后 cloud `master` 并行快进到后继 `354d6a6`（独立 Facebook note key 修复，`c77683e` 仍为其祖先）并由对应任务在 14:09 重启；最终 dev cloud 与 `354d6a6` 干净归档按 checksum 无内容漂移，因此本变更与并行修复均在当前运行态，未互相覆盖。
- 未代用户再次触发真实人物洗稿，因而没有宣称新链路已通过同素材真人视觉验收；6.6 与 7.2 继续 pending，待用户试跑后核对 v3 反推、逐槽 brief、`contentAlignment` 和最终人物神态。

### 7.1 Typed-category follow-up record (2026-07-15 14:50)

- cloud `45b0411`、console `e7d3046` 已快进到各自 `origin/master`；cloud 提交包含同期默认分支上的 Facebook feed 点赞竞态修复 `56112be`，未覆盖并行变更。
- `contentVisualBrief` 已扩为公共叙事字段 + 八类判别式 `categoryBrief`；planner 严格解析并分类兜底，反推 frame 可按源图类型纠正分类，composer/fallback/产后 `contentAlignment` 均消费类型专用语义。信息图禁止编造数字，UI/文档禁止暗示未证明的已上线能力。
- 确定性文字卡文案读取洗稿后正文的有界首/中/尾语义，并显式组织核心结论、信息层级、重点词、阅读顺序和信息密度；原文重叠与禁用词校验保持不变。发布详情按八类展示可读标签与关键字段，历史无分类字段继续兼容旧人物展示。
- validation：cloud acceptance `50/50`、全量 `2095/2095`、分类目标回归 `45/45`、typecheck、build；console 全量 `124/124`（另 1 skipped，`maxWorkers=2`）、相关目标 `21/21`、typecheck、build；OpenSpec strict 均通过。console 首次默认并发全量有 1 条未改动 Facebook 图片用例超时，随后该文件独立 `8/8` 及降并发全量均通过。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-144625.image-category-brief.tar.gz`、`/opt/aidcp/cloud/.env.bak.20260715-144625.image-category-brief`、`/opt/aidcp/console.bak.20260715-144625.image-category-brief.tar.gz`。cloud/console 均由干净提交归档构建部署，部署后 checksum dry-run 无内容漂移。
- dev 健康：`aidcp-cloud.service=active/running`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、console 新资产 HTTP 200、PG `ok=1`、飞书 `WSClient onReady`；四个 isales 服务均 active/running。四个视觉旗标均保持 `true`。
- 未代用户触发新的真实洗稿，也未替用户评价最终图片质量；6.6 与 7.2 继续 pending，待用户试跑后按同素材逐槽核对类型 brief、正文一致性、视觉风格和人物神态。

### 7.1 Autonomous-visual follow-up record (2026-07-15 15:43)

- cloud `c2b3ad1`、console `b9c3bb3` 已快进到各自 `origin/master`；OpenSpec 契约提交已基于同期并行任务的最新 `origin/main` 重放并快进，不覆盖并行记录。
- 原创稿件现在生成文章级 `visualSetBrief`，逐槽带固定 `slotRole` 和八类判别式 `categoryBrief`；composer 消费整组连续性、槽位职责与类型参数，并按能力诚实标记生成式、确定性文字卡、专用生成和区域引导路由。无来源图时使用独立 `content_alignment` 审计，`copyCheck=not_applicable`，失败仅有界重试一次且未知结果不得覆盖已知失败。
- validation：cloud acceptance `52/52`、全量 `2113/2113`、原创视觉目标回归 `70/70`、收口审计回归 `9/9`、typecheck、build；console 全量 `125` passed + `1` skipped（`maxWorkers=2`）、发布详情目标 `22/22`、typecheck、build；OpenSpec strict 均通过。console 默认并发曾有一条未改动配额页用例超时，独立复跑 `3/3` 及降并发全量均通过。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-154018.autonomous-visual.tar.gz`、`/opt/aidcp/cloud/.env.bak.20260715-154018.autonomous-visual`、`/opt/aidcp/console.bak.20260715-154018.autonomous-visual.tar.gz`。cloud/console 均从默认分支干净归档构建部署，部署后 checksum dry-run 无内容漂移。
- dev 健康：`aidcp-cloud.service=active`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、console 新资产 HTTP 200、PG `select 1`、飞书 `WSClient onReady`；四个 isales 服务均 active/running。原有四个参考视觉旗标保持 `true`，新增 `AIDCP_AUTONOMOUS_VISUAL_AUDIT=true`。
- 本次未代用户触发真实原创稿件发布或真实图片生成，因而只确认规划、路由、审计与展示链路已通过代码验证，不宣称最终图像质量已经真图验收；洗稿同素材 A/B 的 6.6 与归档 7.2 继续 pending。
