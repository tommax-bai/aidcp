## Context

发布流水线在 `aidcp-cloud/src/publish-agent`，事件驱动黑板：各角色 watch 黑板键、产出新键接力。配图链路现状是**结构性单图**：

- 文生图请求写死单张（`wanxiang-client.ts:109` `n:1`，只取 `choices[0]`），`ImageProvider.generate` 返回单数 `ImageResult.url`（`image-provider.ts:11,20`）。
- 配图决策角色 `ImagePlanner`（`roles/image-planner.ts`）一次 LLM 调用既定主题又出一条完整万相 prompt，写键 `imagePlan`（其 `imageCount` 是死字段，写死 1、下游无人读）；`ImageGenerator`（`roles/image-generator.ts`）对单 prompt 调一次 `generate`，写 `imageDirective`。
- 四层中间产物全是单数 `imageUrl`（`types.ts:118/129/189`），落库 `publish_log.image_url` 单列（`publish-log-store.ts:27`）。
- 角色超时是 `BasePublishRole` 的 `Promise.race(execute, timeout)` 总闸（`base-role.ts:74-86`），超时走 `fallback:'skip'` → `getDefaultOutput()` 返回空 directive（`image-generator.ts:66-78`）。
- **下发链路已为多图设计好**：命令序列 `images: string[]` 循环发 `upload_image×N`（`command-sequencer.ts:114-116`），`set_cover` 仅 `images.length>1` 才发（:120）；边缘"一命令一图"（`publish-command-handlers.ts:627-639`）；协议消息类型集合不含图数概念。
- 数据库已有一根**闲置** `images TEXT[] DEFAULT '{}'` 列（`migrations/0004_publish_agent.sql:6`），当前 store 的 canonical SQL 不引用它。
- 风控：`upload_image`/`set_cover` 不经 `RiskController`，`publish` 配额整帖粒度。按角色配模型/温度的能力（`role_config` 表 + `/roles` 页）已上线。

约束：协议零改动（不触发四处同步）；红线「MUST NOT 静默假成功」「决策与执行解耦」必须逐张守住；小红书图文帖硬约束 1–9 张、不能 0 张、单图封面自动（无独立设封面控件）。

## Goals / Non-Goals

**Goals:**
- 按正文配多张图（默认 3、范围 1–6、硬上限 ≤9、下界 ≥1）。
- 把"决定配几张/画什么"与"把主题写成画图指令"拆成两个可独立配模型、独立失败重试、独立单测的决策角色；生成仍是独立执行角色。
- **并行**出图、**每张独立计时**，已成功的图绝不被超时整体清零。
- 部分成功诚实：M≥1 发 M 张、M=0 诚实失败、按真实上传成功数 K 记账。
- 数据模型多图化，旧路径零回归、迁移可回滚。

**Non-Goals（本 change 明确不做，留缝）:**
- 万相 `n>1` 批量出图（用 N 个不同 prompt 并发，而非一个 prompt 多采样）。
- 选非首图当封面 / 封面美学评分 / LLM 选封面（封面恒取成功序列首张；不引入封面索引）。
- 真正下发 `set_cover` 命令 + 边缘"设封面"页面 DOM 真机校准（独立后续 change；默认首图策略绕开尚未校准的边缘设封面操作）。
- 视频 / 纯文字内容类型；面板多图展示（读侧当前不 select 图片列）。
- 协议、边缘、console 改动（本 change 零改动）。

## Decisions

### D1. 配图决策拆三角色（选题 / 指令 / 生成），而非 2 角色结构化输出
- **选**：① `ImageSetPlanner`（图集选题，新）watch `createdContent` → 读正文决定张数 + 每张主题（业务语言）+ 风格倾向，写新键 `imageSetPlan`；② `ImagePromptComposer`（配图指令，新）watch `imageSetPlan` → 把每个主题翻成一条万相 prompt（统一风格/无文字/无真人/英文），写**现有键** `imagePlan`（升级为 `imagePrompts: string[]`）；③ `ImageGenerator`（现有升级）watch `imagePlan` → 并行出图。
- **为何**：选题是内容理解、指令是图模型话术，两种不同的活，拆开后各自可在 `role_config` 配不同模型/温度（选题配强模型、指令配便宜的）、各自单测只桩 LLM；主题成为一等公民、可供去重护栏与将来选封面复用。
- **替代（弃）**：单个升级版决策角色一次输出 `{count, [{theme,prompt}], style}`。省一次 LLM 调用，但选题与指令绑死同一模型、同生共死、不可分测。用户明确选 3 角色。
- **嵌入**：仅插一个新角色 + 一个新黑板键（`imageSetPlan`）；指令角色接管写 `imagePlan` 老键，故生成角色触发入口不变、下游零改触发。

### D2. N 张为各异画面（并行单图调用），不用万相 `n>1`
- **为何不用 `n>1`**：`n>1` 出的是同一语义的多采样（画面近重复），做不出图文叙事递进，且一个慢任务卡死即全失败、无法部分成功。N 个不同 prompt + 共享**固定风格基底**（模板常量，不让 LLM 产）= 统一风格、不同主体。
- **去重护栏**：prompt 归一化近似比对，命中即丢该张（不补不复用）——但**永远保住第 0 张**（封面位），由护栏自身保证 `wantImage:true → ≥1 张`，不让护栏吃光导致"本可发图却自杀"。
- **接口零改**：并发调现有单图 `generate(prompt, style)`，不动 `ImageProvider` 接口、不动 `WanxiangClient` 的 `n:1`。

### D3.（关键正确性）N 张**并行**生成、每张独立计时，已成功的图绝不被清零
- **并行生成**（用户定）：N 张同时发起、各自轮询，wall-clock ≈ 最慢单张（而非 N 张相加）——发布更快。用 `Promise.allSettled`：每张 `Promise.race(generate, perImageTimeout)` 各自独立超时，全部 settle 后收集 `fulfilled` 的真实 URL（按规划顺序保序，[0] = 钩子图/封面位），`rejected` / 超时那张**直接不进数组**（不补空、不复用别张）。`allSettled` 天然收集部分成功，无"循环被丢弃"问题。
- **角色总闸（修 blocker）**：`BasePublishRole` 的 `Promise.race` 总闸（`base-role.ts:74`）超时即 `fallback:'skip'` → `getDefaultOutput()` 空 directive（`image-generator.ts:66`），会把已生成的图整体清零（已核实）。并行下总闸只需设为 **每图超时 + 余量**（≈ max 而非 sum），保证 `allSettled` 在总闸前结算 → 拿到部分成功；即便总闸真触发，也 MUST 用"已 settle 的成功 URL"构造产出、绝不返回空清零。
- **并发护栏**（红队的 DashScope 突发压力顾虑）：并发上限 env `AIDCP_PUBLISH_IMAGE_CONCURRENCY`（默认 = 张数上限，对 ≤6 张实为不限；可调小以节流）。某张被图源限流即如实失败那张（不伪造、不全批拖死）。
- env：`AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`（每图超时）、`AIDCP_PUBLISH_MAX_IMAGES`（张数上限）、`AIDCP_PUBLISH_IMAGE_CONCURRENCY`（并发上限）。
- **不变量（写进注释）**：每张图的诚实判定与单图逐字同构——失败那张回空、不进数组、不伪造。
- **注**：仅**生成**并行；**上传**仍是边缘"一命令一图" FIFO 顺序（N 条 `upload_image`），故 `PublishExecutor` 角色超时仍随张数覆盖"审批 + N×上传"，与生成并行无关。

### D4. 部分成功：生成侧 M、上传侧 K，两端都按真实数诚实记账
- 生成侧：想要 N 成 M，`imageDirective.imageUrls = [M 个真实成功 URL]`（失败那张不进数组）。`M≥1` 继续；`M=0` → 执行端判据从 `!imageUrl` 改为 `imageUrls.length===0`，诚实 failed、不发卡、不下发。
- 上传侧：把命令序列的 all-or-nothing `imagesOk` 改为计数 `K`（真实上传成功条数）。**必改点** `command-sequencer.ts:178`（早停判据 `!imagesOk → K===0`）、:183（`set_cover` skip 判据）。`K≥1` 即有效帖、照发 K 张；`K===0` 才 failed。
- 记账：`markImagesAttached(id, count)` 落真实附着数；新增列 `images_attached_count INT`，`images_attached BOOLEAN = count>0` 派生保留（向后兼容旧读者）。**杜绝"要 6 张实成 2 张被读成 6 张"**。
- 提交后保护：`submit_publish` 成功后任何超时 MUST NOT 把记录翻成 `failed`（executor 总闸不能简单线性放大）。

### D5. 封面恒取成功序列首张，本期不引入封面索引、不改 set_cover 触发
- `CoverSelector` 从"单图直选"升级为"读 `imageUrls[]`、恒取首张、`hasCover = length>0`"。封面 = `imageUrls[0]`（即成功序列首张，钩子图）。
- **不引入 `coverIndex` 字段、不改 `command-sequencer.ts:120` 的 `set_cover` 触发条件**：避免提前接通"选非首图 → 下发 set_cover"这条会踩边缘未校准设封面操作的路径。平台默认首图即封面，本期天然正确。
- **替代（弃）**：本 change 就做 `coverIndex` 一等公民 + 美学/LLM 选封面。红队指出这是"为未来付费、给现在埋雷"（恒零字段贯穿多文件 + 接通会踩 fail-closed 桩），按 YAGNI 推迟到边缘设封面校准那一期一起做、一起真机验证。

### D6. 复活闲置 `images` 列，加列不改旧列，迁移 0017
- 复活 `migrations/0004` 已建的 `images TEXT[]`（不新建重复列）；保留 `image_url` 单列**双写**（`image_url = imageUrls[0] ?? null`）兼容旧记录/审计/面板；新增 `images_attached_count INT`。
- 迁移 `0017` 纯 `ADD COLUMN IF NOT EXISTS`、幂等可重入；**显式兜空** `UPDATE publish_log SET images='{}' WHERE images IS NULL`（因 0004 的 `IF NOT EXISTS` 跳过时不应用新约束，列可能为 NULL）；读侧统一 `?? []`；不加 `NOT NULL`、无 down 迁移、前后向不 brick。`0012` 缺号、`0013-0016` 已用（`0016_notification_contacts.sql` 由并发会话的 notification-contact-registry change 占用），下一空号 `0017`。

### D7. 数据模型数组化 + 单数派生兼容字段，零回归
- `ImageDirective` / `AssembledContent` 新增 `imageUrls: string[]`，保留 `imageUrl = imageUrls[0] ?? null` 作派生兼容字段（老单测/老分支零回归），过渡后标 `@deprecated` 再删。`CoverSelection` 改为 `{ imageUrls, hasCover, selectedAt }`。
- `imagePlan` 从单 `imagePrompt` 升级为 `imagePrompts: string[]`，`imageCount` 字段激活=目标张数。
- `assembledContent` 新增 `imageUrls`（上传全集）、`imageUrl` 保留=封面（首张）；这使下游 `PublishExecutor` 因新能力**确需改动**（读 `imageUrls` 下发全集），是预期的新能力扩展，非历史细拆的"下游零改动"语境。

## Risks / Trade-offs

- **[每图超时与角色总闸冲突]** → 并行下总闸 ≈ 每图超时 + 余量（wall-clock 是 max 非 sum），`allSettled` 在总闸前结算拿到部分成功；即便总闸触发也返回已累积、绝不清零（D3）。
- **[并行生成突发压垮图源 / 限流]** → 并发上限 env `AIDCP_PUBLISH_IMAGE_CONCURRENCY`（默认 = 张数上限、可调小节流）；被限流那张如实失败、不伪造、不拖死全批（D3）。
- **[executor 角色超时砍断已提交发布]** → roleTimeoutMs 覆盖 审批(240s)+N×上传(60s/张)+余量，且 `submit_publish` 成功后禁止任何超时翻 `failed`（D4）。
- **[发布期边缘被看门狗误杀]** → 多图发布占用边缘数分钟；浏览闭环看门狗/SessionMonitor 是否在该 edge 发布期暂停判活**待坐实**（Open Question 1），未坐实前不下"无需新风控约束"结论。
- **[同账号 N:1 去重窗口被拉长的发布超出]** → 已初步坐实大概率不适用：`interaction-guard` 仅接线于浏览闭环、发布路径零引用；实装前确认发布仍在该 guard 之外即可（Open Question 2）。
- **[assembledContent 字段集变更触及稳定边界要求]** → 本 change 显式新增 `imageUrls` 一个字段并经 spec delta 声明；下游 executor 改动是新能力预期，非历史细拆红线所禁的"静默改形"。
- **[`images` 列约束不一致]** → 迁移显式 NULL 兜底 + 读侧 `?? []`，不依赖"幂等无害"含糊（D6）。
- **[ECS 部署连带 master]** → 部署是全 master rsync 快照，会连带累积的其它 master 改动；部署前 dry-run + surface scope。

## Migration Plan

1. 迁移 `0017`：复活 `images` + 加 `images_attached_count` + NULL 兜底（纯加列、幂等）。canonical SQL（`publish-log-store.ts`）同步补这两列的 `ADD COLUMN IF NOT EXISTS`。
2. 代码：两新角色 + 升级生成/封面/组装/执行/命令序列 + 类型数组化 + 兼容字段 + prompts 拆两套 + 风格基底常量。
3. 验证序列（CLAUDE.md §4）：cloud `npm run test:acceptance`（AC-PUB-*/AC-PROTO-* 应零回归）→ `npm test` → `npm run typecheck`。
4. 部署：全 master rsync（dry-run 先看 scope）→ restart → healthcheck → 失败回滚。
5. **回滚**：代码回滚到单图版即可；新列/复活列留着无害（旧码读 `image_url` 单列），无 down 迁移，前后向不 brick。

## Open Questions

1. **发布期看门狗豁免**：发布命令序列执行期（多图 ≈ N×上传），边缘浏览闭环看门狗/SessionMonitor 是否已对该 edge 暂停判活？若否，N 大时可能被误判 idle 杀会话（CLAUDE.md §2 记的看门狗杀会话类 bug），需新增"发布期看门狗豁免"约束。→ 实装前坐实。
2. **去重窗口（已初步坐实：大概率不适用）**：经核 `interaction-guard` 仅接线于浏览闭环 dispatcher（`role-dispatcher.ts:302` `tryClaim`），发布路径（`publish-agent` / `comm`）对其**零引用**——发布是手动单节点定向命令、不走浏览互动去重。故"N×上传拉长发布超出去重窗口"大概率非问题；实装前**确认发布仍在该 guard 之外**即可（确认而非加固）。
3. **默认张数 3**（已定）。上限/并发可经 `AIDCP_PUBLISH_MAX_IMAGES` / `AIDCP_PUBLISH_IMAGE_CONCURRENCY` 调整。
4. 选题角色产出的"主题"近期是否需要喂给标签/正文（`TopicStrategist`）？本 change 仅供去重与封面位，留缝不接。
