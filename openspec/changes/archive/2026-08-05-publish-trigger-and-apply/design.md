# Design — publish-trigger-and-apply（A 重构收口阶段）

> 本文档落到具体 `file:line`（截至 2026-06-20 已逐处核对，行号可能随后续提交漂移，以符号/上下文为准）。
> 凡引用代码位置，cloud = `../aidcp-cloud`，edge = `../aidcp-edge`。

## 1. 背景与定位

前三阶段已建成「指令驱动执行底座 + 11 角色生产段 + 8 元数据决策角色 → `publishMetadata`」三层地基：

- **stage-1（`publish-edge-command-runtime`）**：协议 `publish.command` / `publish.command.result`（54 条消息），边缘
  `PublishCommandDispatcher`，云端 `CommandSequencer` + AC-PUB 双闸，`PublishExecutor` 守卫式接 sequencer。
- **stage-2（`publish-content-media-roles`）**：生产段拆 11 角色，稳定边界 `assembledContent` 八字段不变。
- **stage-3（`publish-metadata-compliance-roles`）**：8 个元数据决策角色 + `MetadataAggregator` → 并行键 `publishMetadata`；
  **纯决策、未应用到边缘、未落库**（§5 应用、§6 落库延后到本 stage）。

地基已能「生产一篇带元数据的终稿」，但仍是**空转流水线**：无触发器、元数据/配图不流向浏览器、来源血缘写死、人审默认关、
唯一活入口是两个 temp 旁路。本阶段把流水线接成闭环，并守住全仓三条红线（未授权不发、不静默假成功、不自残）。

### 1.1 评审结论（可实现性）

对 cloud / edge 双仓逐处核对后，**地基已就绪、缺口明确、红线已有双闸守护，强烈推荐实装、风险可控**。要点：

- 协议层 `PublishCommandKind` / `PublishCommandParams` 已含本阶段全部 kind 与 params，**本阶段大概率零协议改动**（见 §4）。
- `publishMetadata` 结构（`types.ts:222-249`）、`MetadataAggregator` 防篡改回正（`metadata-aggregator.ts:92-94`）、
  `RiskController` 的 `'publish'` action（`risk/types.ts:1`、`risk-controller.ts:51-58`）、AC-PUB 双闸
  （`publish-executor.ts:156-163`、`command-sequencer.ts:98-99`）、边缘 `kind_not_implemented` 诚实回报
  （`publish-command-handlers.ts:113-120,191-198`）均已实装，是本阶段的可靠底座。
- 主要缺口是「演员 + 编排」：触发器、`LikedNoteStore`、executor 读 metadata、sequencer 元数据 emit、4 个边缘 kind 处理器、
  飞书 `/publish`、删 temp、落库扩列。总量约 ~900 LoC，分散 cloud 7 文件 + edge 4 文件，工作量可控。

## 2. 关键设计决策（逐项落 file:line）

### 2.1 触发器 `PublishScheduler`（缺口①，proposal B 决策 1）

`PublishScheduler` 是**新增编排启动层**（新建 `cloud/src/publish-agent/publish-scheduler.ts`），不进 `RoleDispatcher`
——它不是 `SessionContext` 内的浏览角色，而是发布流水线的外部触发器。三扳机：

| 扳机 | 来源（已存在的可读 API） | 过 `canDo('publish')` | 过人审 |
| --- | --- | --- | --- |
| ① 概念积累（新概念计数 ≥ N） | `ConceptStore`（`concept-store.ts:67`，现有 `list()`/`loadPool()`，**待补计数**） | 是（硬前提） | 是 |
| ② 风控允许窗口 | `RiskController.getState()`（`risk-controller.ts:79`）+ `canDo('publish')`（`:51`） | 是（硬前提） | 是 |
| ③ 手动飞书 `/publish` | `CommandRouter`（`feishu/commands.ts:115`，现仅 `publish-test`，**待补 `/publish`**） | 否（人工授权越过） | **是（不可越）** |

- **复用单例（红线）**：`RiskController` 在 `server.ts:206-222` 一处初始化（PG 持久化、回退内存）、`ConceptStore` 在
  `server.ts:145-156` 初始化；`PublishScheduler` MUST 接收注入的同一实例，**绝不 `new`**。这是「账号风控最终状态只由云端
  `RiskController` 单写」的延伸——调度器只读 `getState()` / 调 `canDo('publish')`，不写状态。
- **重入保护**：`PublishOrchestrator.trigger()` 已有「pipeline already running, ignoring」保护，调度器无需自加锁，
  但扳机层应避免无意义重复唤起。
- **轮询 vs 事件**：扳机①②低频轮询（缺省 30min，`AIDCP_SCHEDULER_INTERVAL_MS` 可调）读计数 + 风控态；扳机③飞书消息即时触发。
  总开关 `AIDCP_PUBLISH_SCHEDULER_ENABLED`（**缺省 false**），避免误自动发。
- **新概念计数语义**：`ConceptStore` 补 `countNewSince(ts)` / `getNewConceptsSince(ts)`；基线时间取「上次成功发布时间」
  ——从 `publish_log` 最近成功记录读（`publish-log-store.ts:116-117` 已有 `ORDER BY published_at DESC LIMIT 1`，可扩为
  按 status 过滤）；首次发布前以服务启动时间或全量计数兜底。

### 2.2 元数据/配图应用到边缘（缺口②，proposal B 决策 2、3）

`CommandSequencer.buildCommandSequence`（`command-sequencer.ts:81-103`）现只发 6 类基础指令
（`navigate_entry` / `select_mode` / `fill_field(title)` / `fill_field(content)` / `add_with_candidate(topic)×N` /
`[submit_publish / capture_postId]`），`:96` 注释明确「`upload_image` / `set_schedule` 本阶段未入序列」。扩展为：

```
navigate_entry
→ select_mode
→ upload_image × N            (配图，失败降级纯文字)
→ set_cover                   (有图且封面选定)
→ fill_field(title) / fill_field(content)
→ add_with_candidate(topic)×N
→ add_with_candidate(mention|location|collection)×N   (from publishMetadata)
→ set_option(visibility|permissions|各声明)            (from publishMetadata)
→ set_schedule               (mode==='scheduled' 时按 publishTime)
→ [人审通过] submit_publish
→ capture_postId
```

- **executor 读 metadata + 竞态保险**：`PublishExecutor.execute`（`publish-executor.ts:91`）现签名为
  `execute(input, _context: PipelineContext)` —— `_context` 闲置、下划线即未用。改为读
  `context.get('publishMetadata')`（`pipeline-context.ts:116` 已实装 `get<K>`），并把 metadata 经
  `handleAutoPublishViaSequencer`（`publish-executor.ts:151`）传给 sequencer。
- **竞态保险（低风险但须显式处理）**：`PublishExecutor` 的 `watchKeys: ['gateDecision']`（`publish-executor.ts:60`）
  **不监听 `publishMetadata`**；而决策角色与门禁角色并行、无强序，`gateDecision` 可能先于 `publishMetadata` 就绪。
  读取时若 `publishMetadata` 未就绪：取保守默认（可见范围 `self_only`、不发元数据指令；`METADATA_DEFAULT_VALUES`
  见 `types.ts:239`），或显式 `context.waitFor('publishMetadata', timeoutMs)`（`pipeline-context.ts:121` 已实装），
  timeout 后仍走保守默认。**绝不因缺元数据崩溃、绝不因缺元数据跳过 AC-PUB 人审或伪造成功。**
- **配图失败降级（红线，不伪造）**：`upload_image` 回 `ok:false` → sequencer 标 `imagesOk=false`、跳过依赖图的
  `set_cover`、走纯文字路径继续余下指令；`imagesOk` 如实落库。`command-sequencer.ts:33` 现有 `images URL ... 暂不入序列，仅预留`
  注释，本阶段放开。
- **AC-PUB 第二闸不变**：未授权时元数据/配图指令仍下发（它们在提交前），但 `submit_publish` / `capture_postId` 截止不入序列
  ——保持 `command-sequencer.ts:98-99` 的 `if (!input.approvedByUser) return cmds;`。

### 2.3 边缘 kind 处理器（缺口②，proposal B 决策 2、3）

实装 `publish-command-handlers.ts:114-118` 现回 `notImplemented()`（`:191-198` 诚实回 `kind_not_implemented`，无假成功）
的四类，**复用 `LocatingEngine` 三道闸**（`engine.ts`，处理器现已经 `:134-135` `new LocatingEngine(...).resolveAndAct(req)`
走五层编排，`:151` 注释「engine 内部已跑后置校验，result.ok 即真实结果，此处绝不翻成 ok:true」）：

- `upload_image`：URL → 下载到 `/tmp` → CDP 文件输入桥（`DOM.setFileInputFiles` 类机制）→ 后置校验图进入编辑区 → 清理临时文件。
  失败回 `upload_failed` / `no_target` / `post_validation_failed`。
- `set_cover`：定位封面入口（弹窗/缩略图）选定，后置校验封面已设。
- `set_option`：按 `optionKind`（`protocol.ts:408`）路由（`visibility` / `permissions` / 声明开关），engine 定位开关/单选，
  后置校验选中态 == 期望。
- `set_schedule`：定位时间选择器填 `publishTime`（`protocol.ts:412`），后置校验已设定。
- **锚点扩展（位置修正）**：锚点声明在 **`edge/src/flows/anchors.ts`**（`publish-command-handlers.ts:24` 由此 import
  `XHS_PUBLISH_*_ACTION_ID` / `*_ANCHOR_HINT` / `*_GOAL`），**不是** `src/locating/anchors.ts`（该路径不存在）。
  补配图/封面/可见范围/权限/定时/提及/合集等新锚点（仿 `anchors.ts:117-181` 既有 `XHS_PUBLISH_*` 三件套：
  `ACTION_ID` + `GOAL` + `ANCHOR_HINT`）；新锚点经三道闸的反污染回写（stage→confirm），**engine 不改**。
- **放开带图硬拒**：`publish-post.ts:294-295` 的 `if ((payload.images?.length ?? 0) > 0) return {ok:false, error:'[images] images are not supported in phase one'}` 删除/放行。

### 2.4 人审默认必过（缺口④，proposal B 决策 4）

`main.ts:130` 的 `process.env.AIDCP_REAL_PUBLISH === 'true'` → `!== 'false'`。语义反转：缺省即挂闸，只有显式
`AIDCP_REAL_PUBLISH=false`（受控测试）才跳过。审批信号路径契约 `/tmp/aidcp-publish-approve-<requestId>.json`
由 edge `buildPublishApprovalSignalPath`（`approval-gate.ts:45-46`）与 cloud `getApprovalSignalPath` 两端一致，
**不漂移**。`submit_publish` 前严格 `approved === true`（云端第一闸 `publish-executor.ts:156` 经 `isApproved` 读，
catch 落 false → needs_review，`:159-163`）。这把「未明确授权 == 不发布」从「需主动开启」变成「默认成立」。

### 2.5 来源血缘 `LikedNoteStore`（缺口③，proposal B 决策 5）

新建 `cloud/src/publish-agent/liked-note-store.ts`（`liked_notes` 表，DDL `CREATE TABLE IF NOT EXISTS`，
仿 `publish-log-store.ts:13-21` 风格）。在真实 `like` 完成时落库被赞内容来源：

- **挂点**：`server.ts:226` 已订阅 `eventBus.on('interaction.occurred', ...)`（现仅驱动 `RiskController.record`）；
  本阶段在同处或新增订阅里把 `like` 写 `LikedNoteStore`。
- **accountId 缺口（已知）**：`interaction.occurred` 事件（`handler.ts:242-243`）现只携带 `{action, noteId, ...}`、
  **不携带 accountId**（accountId 在 `handler.ts:269` 的 `session.accountId` 上）。方案 A：从 hello/session 上下文回填；
  方案 B：单账号 MVP 取 `DEFAULT_ACCOUNT_ID`。**建议 B（简单可行），多账号留 follow-up**。
- **回取**：`PublishExecutor` 落库发布记录时 `sourceLikedIds = likedNoteStore.listSince(基线)`，取代 `server.ts:378`
  写死的 `sourceLikedIds: []`；`sourceConcepts` 取真实概念（`server.ts:377` 现已用 `record.tags`）。
  无来源如实空数组、不编造。

### 2.6 元数据落库 + 防篡改（缺口⑤，proposal B 决策 6，stage-3 §6）

`publish_log`（`publish-log-store.ts:15-21`）加 `publish_metadata JSONB` + `ai_enforced BOOLEAN`（DDL `IF NOT EXISTS`
幂等，与现风格一致），INSERT（`:75`）/SELECT（`:116`）同步。`PublishExecutor` 落库写两列；落库前若检出
`publishMetadata.compliance.aiEnforced && !ai`（`types.ts:207-213`）→ 拒绝降级、保持 `ai=true`、记审计日志
（对齐 `metadata-aggregator.ts:90-94` 的回正红线，强制声明一经置位不可降级）。落库不改任何发布判定，仅如实持久化。

### 2.7 删 temp 旁路（缺口⑥，proposal B 决策 7）

删 `server.ts:397-418`（`/debug/publish` HTTP 端口 + `debugPayload` + `debugServer`，含 `:402-403` 的 TODO(temp) 注记口）
+ 整文件 `cloud/src/cli/trigger-publish-temp.ts`（`:15` 直发 `publish.request` 整页、绕过指令驱动 + AC-PUB）+
`package.json:18` 的 `"trigger:publish-temp"` 脚本。删后唯一正式触发 = 飞书 `/publish`（经 `PublishScheduler` 走指令驱动 + AC-PUB）。
**删后全仓不得残留任何直接构造 `publish.request` 整页或绕过 AC-PUB 人审的发布入口**（验收时全仓 grep `publish.request` 下发点）。

## 3. 时序与竞态分析

`publishMetadata` 产生时序（`metadata-aggregator.ts`）：

```
8 决策角色（TopicStrategist / MentionStrategist / … / ComplianceDecider）
  → watchAll 8 键全到达 → MetadataAggregator.execute() → ctx.write('publishMetadata', …)  [T1]
PublishExecutor 监听 gateDecision（watchKeys=['gateDecision']，publish-executor.ts:60）   [T2]
  → execute 读 context.get('publishMetadata')   [可能 T2 < T1 → 返回 undefined]
```

- **风险等级：低，但须显式缓解**。`gateDecision` 与 `publishMetadata` 并行决策、无依赖序，executor 不监听 metadata。
- **缓解**：读取前 `const md = context.get('publishMetadata') ?? {...METADATA_DEFAULT_VALUES}`（`types.ts:239`），
  或 `await context.waitFor('publishMetadata', timeoutMs)`（`pipeline-context.ts:121`）；timeout 后仍取保守默认。
  **不论哪条路径，AC-PUB 人审与 `submit_publish` 前授权检查照常执行**，绝不因缺元数据放弃授权链。

## 4. 协议影响

本阶段**不新增消息**——`publish.command` / `publish.command.result` + `PublishCommandKind`（`protocol.ts:381-389`，
含 `upload_image` / `set_cover` / `set_option` / `set_schedule`）+ `PublishCommandParams`（`:397-413`，含 `imageUrl` /
`optionKind` / `optionValue` / `publishTime`）已在 stage-1 预留齐，cloud（`:381-413`）/ edge（`:383-412`）逐字同步、无差异。
若 `set_option` 需补 `optionKind` 枚举说明，两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge.ts` 映射不变 +
`docs/protocol.md` 同步（**计数维持 54**，仅 kind/params 说明补充）。漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护。
（多数情况 task 0.1/0.2 评估后判定无需改动。）

## 5. 风险与缓解

| 风险 | 级别 | 缓解 |
| --- | --- | --- |
| 配图 CDP 文件输入桥稳定性 | 中 | 失败降级纯文字 + `imagesOk` 如实；若桥风险超预期，按 §6 把配图应用降为 follow-up change |
| `publishMetadata` 读取竞态 | 低 | executor 取保守默认 / `waitFor`，绝不因缺元数据跳过 AC-PUB（§3） |
| 自动扳机误发 | 中 | `AIDCP_PUBLISH_SCHEDULER_ENABLED` 缺省 false + 自动扳机硬过 `canDo('publish')` |
| 单例被旁路 `new` | 中 | `PublishScheduler` / `LikedNoteStore` 经 server 注入同一 `RiskController`（`server.ts:206`）/ `ConceptStore`（`:145`）单例 |
| `interaction.occurred` 无 accountId | 低 | 单账号 MVP 取 `DEFAULT_ACCOUNT_ID`（§2.5 方案 B），多账号 follow-up |
| 删 temp 后无法本地调试 | 低 | 调试经 `AIDCP_REAL_PUBLISH=false` 受控关人审，不保留绕过授权链的触发口 |

## 6. 拆分判断

六项（触发 / 配图应用 / 元数据应用 / 人审默认 / 血缘 / 落库）互为前提、一体收口（无触发器则 temp 旁路无法删、
无 `LikedNoteStore` 则血缘断、无落库则元数据应用无审计），**默认不拆**，本 change 即第一（也是唯一）子块。

唯一可独立的是**配图应用（proposal B2）**：若 CDP 文件输入桥验证风险过高（中风险项），可收敛本 change 为**五项**
（触发 + 元数据应用 + 人审默认 + 血缘 + 落库），把**配图应用作为后续 change**。届时：

- 本 change 范围去掉：`command-sequencer` 的 `upload_image` / `set_cover` emit（task 4.1 配图部分、4.2）、
  edge `upload_image` / `set_cover` 处理器（task 7.1、7.2）、放开 v1 带图硬拒（task 8.2）、配图相关锚点（task 7.5 子集）。
- **后续 change（Migration 列出）**：`publish-media-upload`（暂名）——CDP 文件输入桥 + 配图/封面 kind 处理器 +
  `upload_image` / `set_cover` 序列 emit + 放开 `publish-post.ts:294-295` 硬拒 + 配图失败降级纯文字的 AC-CMD。
  其前置依赖（本 change 的元数据应用 + 人审默认 + 落库）已满足，可独立验证。

当前默认**六项一体**实施；仅当实施中实测配图桥风险超预期，才触发上述收敛。
