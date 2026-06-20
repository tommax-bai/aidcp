## Context

发帖黑板流水线在 `aidcp-cloud/src/publish-agent`。它是事件驱动的「键就绪触发」黑板：`PipelineContext`（`aidcp-cloud/src/publish-agent/pipeline-context.ts:4`）提供 `write`（写键并触发 watch，`:15`）、`watch`（单键就绪，`:59`）、`watchAll`（多键全就绪的 AND 触发，`:84`）、`waitFor`（Promise 等键，`:121`）、`get`/`snapshot`（读，`:116`/`:142`）。角色基类 `BasePublishRole`（`aidcp-cloud/src/publish-agent/roles/base-role.ts:12`）声明 `RoleConfig{name,watchKeys,waitAll?,timeoutMs?,fallback?}`（`:4`），实现 `extractInput`/`execute`/`outputKey`/`getDefaultOutput`，`register` 在 `waitAll && watchKeys.length>1` 时走 `watchAll`、否则走单键 `watch`（`:48-52`），异常走 `handleError` 按 `fallback` 决定写降级键（`fallback:'skip'` 时写 `getDefaultOutput()`，`:81-94`）。`PublishOrchestrator.trigger`（`aidcp-cloud/src/publish-agent/publish-orchestrator.ts:33`）写 `trigger` 启动链式反应；终止条件在 `awaitCompletion`（`:86`）：`publishResult` 写入、或 `scoutDecision.shouldPublish=false` 短路、或 2 分钟超时（`:24`/`:117`）。角色在 `server.ts:335-352` 集中 `registerRole`。

黑板 schema = `PipelineFields`（`aidcp-cloud/src/publish-agent/types.ts:179-196`）。稳定边界 `AssembledContent` 八字段在 `types.ts:104-113`（`finalContent/finalTags/imageUrl/aiScore/qualityScore/rewritten/flaggedPhrases/assembledAt`）。

阶段进程：
- **阶段1**（已归档）`publish-edge-command-runtime`：`CommandSequencer`（`command-sequencer.ts:64`）把终稿编排成有序 `publish.command`，逐条 send→await→advance，AC-PUB 双道授权闸。边缘协议预登记 `set_option/set_schedule` 与 `add_with_candidate(mention/location/collection)`，处理器回 `kind_not_implemented`（休眠）。
- **阶段2**（已落地，commit `cc7e732`）`publish-content-media-roles`：生产段 6→11 角色细拆，保住 `AssembledContent` 八字段边界；`ContentAssemblerRole`（`content-assembler.ts:27`）瘦身为纯组装 + `waitAll` 五键（`watchKeys:['cleanedContent','aiFlavorScore','qualityReport','imageDirective','coverSelection']`，`:31`）。
- **阶段3（本 change）**：元数据 + 合规决策角色。当前元数据近乎空白——话题只来自 `CreatedContent.tags`（`types.ts:88`），`ContentAssembler` 用 `finalTags: input.created.tags`（`content-assembler.ts:53`）；@/地点/合集/可见范围/权限/发布模式/合规声明无人决策；2026 AI 声明强制红线无落点——`aiScore` 已在黑板就绪（`AiFlavorScore`，`types.ts:142-146`；`AiFlavorScorerRole` 恒等投影，`ai-flavor-scorer.ts:25`）却未被用于强制声明。

纯 aidcp-cloud。契约与 spec 落本中控仓 aidcp。

## Goals / Non-Goals

**Goals：**
- 按版本 A「种类级」粒度新增 8 个 cloud 决策角色，覆盖话题/@/地点/合集/可见范围/权限/发布模式/合规声明，与阶段2 生产段细拆同风格（每角色单一职责、可脱浏览器单测）。
- 各维度写独立中间键，由唯一生产者 `MetadataAggregator`（`waitAll`）汇合为并行键 `publishMetadata`，并打覆盖度分 `metadataScore`。
- 2026 合规红线：含 AI 生成或 `aiScore` 超阈值 → 强制 AI 声明且不可降（`aiEnforced`）。
- `publishMetadata` 可选随 `recordId` 落库/记录血缘（可观测），不改发布行为。

**Non-Goals（均属 stage-4 及以后）：**
- edge 应用元数据：`set_option` 等处理器、`CommandSequencer.buildCommandSequence`（`command-sequencer.ts:81`）把元数据指令入序列、`add_with_candidate(mention/location/collection)` 落地。
- 触发器 `PublishScheduler`（定时发布的实际触发）、来源血缘 `LikedNoteStore`、真机配图上传。
- 不改协议（`src/comm/protocol.ts`，`PROTOCOL_VERSION` 不动）、不碰 aidcp-edge、不改 `ApprovalGatekeeperRole`（`approval-gatekeeper.ts:15`）/`PublishExecutorRole`（`publish-executor.ts:57`）的发布判定与授权闸。

## Decisions

### D1：按维度拆角色，不合并为单一 MetadataEvaluator

对齐阶段2 生产段细拆风格（`AiFlavorScorerRole`/`ContentCleanerRole` 等每角色单一职责、可独立单测）。8 个决策角色 + 1 个 `MetadataAggregator`。否决「单一 MetadataEvaluator 一把抓」——粒度太粗、难独测、合规红线被埋没；也否决「165 全量一步一角色」——过细。

各维度角色 watchKeys、产出键与红线：

| 维度 | 角色 | outputKey | 产出形状 | 空可接受 | 云端硬必选 | 红线 |
|-----|------|-----------|---------|---------|----------|------|
| 话题 | `TopicStrategist` | `topicSelection` | `{selectedTopics: string[]}` (3-30) | 否（≥3） | 否 | 不编造凑数 |
| @提及 | `MentionStrategist` | `mentionSelection` | `{selectedMentions: string[]}` (≤10) | 是 | 否 | 去重剔己、不伪造 |
| 地点 | `LocationStrategist` | `locationSelection` | `{selectedLocation: string\|null}` | 是 | 否 | 无则 null |
| 合集 | `CollectionStrategist` | `collectionSelection` | `{selectedCollection: string\|null}` | 是 | 否 | 无则 null |
| 可见范围 | `VisibilityDecider` | `visibilityDecision` | `{visibility, visibilityReason}` | 否 | 是（非 null） | 失败降 `self_only`，不隐式 `public` |
| 权限 | `PermissionDecider` | `permissionDecision` | `{permissions:{comment,save}}` | 否 | 否 | — |
| 发布模式 | `PublishModeDecider` | `publishModeDecision` | `{mode, publishTime:number\|null}` | 是 | 否 | 定时 ≤7 天 |
| 合规声明 | `ComplianceDecider` | `complianceDecision` | `{compliance:{ai?,ad?,origin?,aiEnforced?}}` | 是（可全空） | ai 是（强制时） | AI 声明强制不可降 |

各角色 watchKeys 取 `createdContent`（话题需 `tags`，参 `ContentCreatorRole` 产出 `tags`，`content-creator.ts:68`）与/或 `assembledContent`（合规需 `aiScore`/`finalContent`，参 `types.ts:107`/`:104`）。`fallback` 用 `'default'`（参 `AiFlavorScorerRole`，`ai-flavor-scorer.ts:16`）或 `'skip'` + `getDefaultOutput()`，**保证无论成败都写自己键**——这是黑板死锁防护（R1）：`base-role.ts:81-94` 的 `handleError` 只在 `fallback==='skip'` 时写 `getDefaultOutput()`，故各角色必须用 `'default'` 在 `execute` 内自兜底（参 `content-cleaner.ts:43-48` 的 `executeWithFallback`）或 `'skip'` + 非 undefined `getDefaultOutput()`；否则 `MetadataAggregator` 的 `waitAll` 永不集齐（`pipeline-context.ts:40` 需 `ready.size === keys.length`）。

### D2：聚合走单一生产者 MetadataAggregator（waitAll 各维度键），产出并行键 publishMetadata

仿 `ContentAssemblerRole`（`content-assembler.ts:27-35`：`waitAll:true` 五键 → `assembledContent`）。`MetadataAggregator` 的 `watchKeys` = 八个维度中间键、`waitAll:true`、`outputKey='publishMetadata'`。`base-role.ts:48` 的 `waitAll && watchKeys.length>1` 分支据此走 `context.watchAll(...,{once:true})`，故 `publishMetadata` **单一生产者**、无多写竞争。

```
createdContent / assembledContent 就绪
  ├─ TopicStrategist      → topicSelection
  ├─ MentionStrategist    → mentionSelection
  ├─ LocationStrategist   → locationSelection
  ├─ CollectionStrategist → collectionSelection
  ├─ VisibilityDecider    → visibilityDecision
  ├─ PermissionDecider    → permissionDecision
  ├─ PublishModeDecider   → publishModeDecision
  └─ ComplianceDecider    → complianceDecision
        └─(waitAll 八键)→ MetadataAggregator → publishMetadata (+ metadataScore)

[发布链并行，互不依赖]
  assembledContent → ApprovalGatekeeper(watch ['assembledContent'], approval-gatekeeper.ts:18)
        → gateDecision → PublishExecutor(watch ['gateDecision'], publish-executor.ts:60)
        → publishResult（终止条件，publish-orchestrator.ts:95）
```

**为何用并行新键、不进 assembledContent**：阶段2 刚保住八字段稳定边界，下游对 `assembledContent` 八字段强耦合——`ApprovalGatekeeperRole.extractInput` 直取 `snapshot.assembledContent`（`approval-gatekeeper.ts:30-32`）、硬编码规则读 `aiScore/flaggedPhrases/qualityScore`（`:66-77`）；`PublishExecutorRole.extractInput` 取 `gateDecision + assembledContent`（`publish-executor.ts:84-89`），落库读八字段（`:108-117`）。元数据进 `assembledContent` 会破边界、连带改下游。`publishMetadata` 与 `assembledContent` 平行，互不依赖。`MetadataAggregator` 与各角色**只读 `assembledContent`**（`snapshot.get('assembledContent')`），绝不 `ctx.write('assembledContent', ...)`。

### D3：publishMetadata 不挂入下游终止条件，pipeline 终止仍由 publishResult/scoutDecider 决定

`PublishExecutorRole.config.watchKeys` 维持 `['gateDecision']`（`publish-executor.ts:60`），**不加 `publishMetadata`**——否则元数据链未就绪会卡住发布。`awaitCompletion`（`publish-orchestrator.ts:86-124`）的终止条件不变：`publishResult` 写入 / `scoutDecision.shouldPublish=false` / 超时。元数据链与发布链并行各跑。`PublishExecutor` 落库时若需带元数据，用 `snapshot.get('publishMetadata')` 软读，缺失则 `?? METADATA_DEFAULT_VALUES`（fallback 明确），不阻塞、不报错。

*风险*：若发布链先于元数据链完成，落库时 `publishMetadata` 可能未就绪。**处理**：落库取 fallback 默认值并记一条 warn（覆盖度 0、可见范围 `self_only`），不卡发布；血缘以「元数据缺失」如实记录，符合「数据缺失不误判」红线。可选优化：落库前 `await ctx.waitFor('publishMetadata', shortTimeout)`（`pipeline-context.ts:121`），超时即 fallback——见 Open Questions，倾向不引入新等待。

### D4：ComplianceDecider 是 2026 合规红线，aiEnforced 防篡改

触发条件硬编码（不可被 prompt/人设/用户覆盖）：`assembledContent.aiScore > AI_FLAVOR_THRESHOLD(=0.6)`（`aiScore` 形参见 `types.ts:107`） **或** 终稿 `finalContent` 命中 AI 生成关键词（`AI 生成/合成/AIGC/人工智能生成` 等）→ `compliance.ai=true` + `compliance.aiEnforced=true`，记 warn。注意区别于 `ApprovalGatekeeper` 现有的 `aiScore>0.6 && flagged>=3 → abort`、`aiScore>=0.5 → manual_review` 阈值（`approval-gatekeeper.ts:67-76`）：那是发布闸的质量阈值，本红线是合规声明阈值，二者独立、互不替代。

防篡改两道守：
1. **类型标记**：`Compliance.aiEnforced?: boolean`，置 true 即「红线强制」。
2. **落库/聚合前校验**：`MetadataAggregator` 与 `PublishExecutor` 检出 `aiEnforced && !ai` → 视为篡改，强制回正 `ai=true`、记审计 error，绝不静默落 `ai=false`。

优先级 `ai > ad > origin`：多声明并存时 AI 声明最高。`ad`/`origin` 由策略/人设决定（非红线）。

### D5：元数据「已决但 edge 应用延后 stage-4」——本阶段不发任何元数据 edge 指令

类比阶段1 指令链路的「休眠」：决策产出 + 落库，但 `CommandSequencer.buildCommandSequence`（`command-sequencer.ts:81-104`）**指令集不变**——现有序列止于 `navigate_entry/select_mode/fill_field(title)/fill_field(content)/add_with_candidate(topic)`（`:88-94`），授权后再加 `submit_publish/capture_postId`（`:101-102`）；本阶段不加 `set_option/set_schedule/add_with_candidate(mention|location|collection)`（`:96` 注释已标 upload_image/set_schedule 暂不入序列）。edge 对这些 kind 继续回 `kind_not_implemented`（`aidcp-edge/src/flows/publish-command-handlers.ts`），本阶段不实装其处理器。stage-4 时 edge 指令应用端回查 `publish_log` 该 recordId 的元数据作为「建议值/审计参考」，最终应用由 stage-4 设计；用户手改以用户为准。

**附录性约束（明确划界，避免误读）**：本设计**不**定义任何 stage-4 指令协议（`set_option`/`set_schedule` 的 params 形状）、不定义 edge 应用界面/逻辑、不定义指令下发的优先级与冲突解决——这些全属 stage-4 及 stage-5。stage-3 与 stage-4 的唯一契约点 = `publish_log` 表里落库的元数据字段（stage-4 回查作建议值）。

### D6：落库为可选最小改动，向后兼容

`PublishExecutor` 现走 `store.insert`，接口定义在 `publish-executor.ts:8-21`（`PublishLogStore.insert(record:{title,content,tags,imageUrl,status,qualityScore,aiScore})`，实际调用 `:109-117`/`:217`/`:255`）；底层 `PublishLogStore.insert`（`publish-log-store.ts:73-88`）写 `publish_log` 表（DDL `PUBLISH_SCHEMA_SQL`，`:14-26`）。本阶段可在 insert 后**追加一次可选写**（如 `store.recordMetadata?(recordId, publishMetadata)`，仿现有可选 `updateStatus?`/`updatePostId?`，`publish-executor.ts:19-20`），或扩 `store` 接口加可空入参——二者皆**不改发布判定**（`handleAutoPublish`/`handleManualReview`/`handleAbort` 路径不变，`:108`/`:216`/`:254`）。`publish_log` 若落库则加可空列 `publish_metadata JSONB` + `ai_enforced BOOLEAN DEFAULT FALSE`，DDL 幂等（`ADD COLUMN IF NOT EXISTS`，呼应现有 `CREATE TABLE IF NOT EXISTS`），旧行兼容。**落库纯属可观测/血缘**，即便不落库本阶段决策与单测亦成立——落库列为可选 task（tasks §5 全标可选）。

### D7：metadataScore 覆盖度计算规则（如实、不虚高）

`MetadataAggregator` 内权重求和，各维度有效才计分，缺失/失败计 0：话题(数量 3-30) +0.2 / @(数量 1-10) +0.2 / 地点非 null +0.15 / 合集非 null +0.15 / 可见范围有效 +0.15 / 权限有效 +0.15，`Math.min(score,1.0)` 封顶。某维度 LLM 失败 → 该项 0 分（如实反映缺失，不为凑分编造，对齐 spec「不得编造元数据凑数」反例）。`metadataScore` 仅供审计/可观测，**不**作为本阶段任何决策的输入或 stage-4 的强依赖。

## 类型定义（types.ts 新增）

落到 `aidcp-cloud/src/publish-agent/types.ts`（紧随阶段2 中间键之后，约 `:159` 之后；`PipelineFields` 扩在 `:179-196` 块内、`AssembledContent`（`:104-113`）逐字不动）：

```typescript
export type Visibility = 'public' | 'friends_only' | 'self_only';
export type PublishMode = 'immediate' | 'draft' | 'scheduled';

export interface TopicSelection { selectedTopics: string[]; decidedAt: number; }
export interface MentionSelection { selectedMentions: string[]; decidedAt: number; }
export interface LocationSelection { selectedLocation: string | null; decidedAt: number; }
export interface CollectionSelection { selectedCollection: string | null; decidedAt: number; }
export interface VisibilityDecision { visibility: Visibility; visibilityReason: string; decidedAt: number; }
export interface PermissionDecision {
  permissions: { comment: 'allow' | 'restrict' | 'disable'; save: 'allow' | 'disable' };
  decidedAt: number;
}
export interface PublishModeDecision { mode: PublishMode; publishTime: number | null; decidedAt: number; }
export interface Compliance { ai?: boolean; ad?: boolean; origin?: boolean; aiEnforced?: boolean; }
export interface ComplianceDecision { compliance: Compliance; decidedAt: number; }

export interface PublishMetadata {
  selectedTopics: string[];
  selectedMentions: string[];
  selectedLocation: string | null;
  selectedCollection: string | null;
  visibility: Visibility;           // 云端必选、非 null
  visibilityReason: string;
  permissions: PermissionDecision['permissions'];
  mode: PublishMode;
  publishTime: number | null;
  compliance: Compliance;           // 含 aiEnforced 防篡改标记
  metadataScore: number;            // 0-1 覆盖度（D7）
  decidedAt: number;
}

export const METADATA_DEFAULT_VALUES: Omit<PublishMetadata, 'decidedAt'> = {
  selectedTopics: [],          // 不凑数
  selectedMentions: [],        // 不伪造 @
  selectedLocation: null,
  selectedCollection: null,
  visibility: 'self_only',     // 最保守（硬必选）
  visibilityReason: 'fallback',
  permissions: { comment: 'disable', save: 'disable' },
  mode: 'draft',
  publishTime: null,
  compliance: {},
  metadataScore: 0,
};
```

`PipelineFields`（`types.ts:179`）增九键：`topicSelection / mentionSelection / locationSelection / collectionSelection / visibilityDecision / permissionDecision / publishModeDecision / complianceDecision / publishMetadata`。各角色 `getDefaultOutput()` 取 `METADATA_DEFAULT_VALUES` 对应切片（保守、不编造），与 `ContentAssemblerRole.getDefaultOutput`（`content-assembler.ts:62-73`）的「写空/零值不写假成功」一脉相承。

## Risks / Trade-offs

- **[黑板键膨胀]** 阶段2 11 角色（`server.ts:335-352`）+ 本阶段 9（8 决策 + 聚合）→ ~20。`waitAll` 各键无论成败都写防死锁（D1），单测覆盖各分支。
- **[元数据链未就绪 → 落库取默认值]** D3 软读 + fallback，不卡发布；以「缺失」如实记录，不误判。
- **[ComplianceDecider 误触发强制声明]** 阈值/关键词宁可偏严（合规优先），`aiEnforced` 只升不降（D4）。
- **[LLM 决策不稳定]** 各角色 `getDefaultOutput()` 提供保守降级；`metadataScore` 如实反映缺失。
- **[落库列变更]** 可选、幂等、向后兼容；不落库也成立。

## Migration Plan

1. aidcp：合并 spec delta（`specs/publish-pipeline/spec.md`）。
2. aidcp-cloud：按 tasks 实装类型 → 各决策角色 → `MetadataAggregator` → `server.ts` 注册（紧随 `:350` 的 `ContentAssemblerRole` 之后、`ApprovalGatekeeper`（`:351`）之前或之后均可，注册顺序无关正确性）→ 可选落库；`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（AC-PUB/AC-PROTO/AC-RISK 不回归——本阶段不碰协议/发布行为）。
3. 验证 `AssembledContent` 八字段不回归（orchestrator 整链测断言 `publishMetadata` 已产出且 `assembledContent` 仍为且仅为原八字段）。
4. cloud 按 ECS 安全序列部署（先确认私钥 + sub-repo；备份→rsync→restart `aidcp-cloud.service`→healthcheck→失败回滚；不碰同机 `isales`）。
5. 回滚：cloud 回退备份；DB 列为可空 `ADD COLUMN IF NOT EXISTS`，回滚无需删列。

## Open Questions

- 落库形态：单列 `publish_metadata JSONB` vs 拆若干扁平列？倾向 JSONB（演进灵活），但 `ai_enforced` 单列便于 DB 层约束/审计——实装时定。
- `PublishExecutor` 落库前是否 `waitFor('publishMetadata', shortTimeout)`（`pipeline-context.ts:121`）兜底，还是纯 `snapshot.get(...) ?? METADATA_DEFAULT_VALUES`？倾向后者（更简、不引入新等待），落库 warn 标元数据缺失即可。
- AI 关键词清单的维护位置（`prompts.ts` 集中常量 vs `ComplianceDecider` 内）——倾向集中常量便于审计，仿 `prompts.ts` 现有各 `buildXxxPrompt` 构造器集中布局。
