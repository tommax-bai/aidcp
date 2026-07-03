<!--
进度回写格式：实装后用 HTML 注释把 task 标 [x]，写清 commit-sha / 偏离说明：
  <!- aidcp-cloud <commit-sha> 备注 ->
部署后追加：<!- <YYYY-MM-DD> deployed ->
本 change 纯 aidcp-cloud（中控仓只承载契约/spec），无 edge / 无协议改动；代码落 ../aidcp-cloud（默认分支 master），进度回写本仓。
实装前先确认：`ls -d ../aidcp-cloud`（缺失则停手，见 CLAUDE.md §0）。
依赖序：类型+新键（§1）→ 各决策角色（§2）→ MetadataAggregator waitAll 汇合（§3）→ server 注册（§4）→（可选）executor 落库 publishMetadata 血缘（§5）→ 测试（§6）→ 全量回归（§7）。
红线（贯穿全 task，验证手段须覆盖）：assembledContent 八字段逐字不动 / 合规 AI 声明强制不可降 / 不编造元数据凑数 / 可见范围必选不隐式 public / 本阶段不下发元数据 edge 指令。
<!-- aidcp-cloud f997638 实装：types+9键+METADATA_DEFAULT_VALUES / 8 决策角色(规则式) + MetadataAggregator(waitAll 8 键→publishMetadata+metadataScore+aiEnforced回正) / server 注册 +9 / 35 新测试(含 ComplianceDecider 0.6 红线 + aggregator 防篡改) / orchestrator 21 角色整链不阻塞 publishResult / assembledContent 八字段逐字不变。阈值统一 0.6(对齐 gatekeeper abort)。cloud 全量 263 绿、acceptance 18 绿(AC-PROTO-02=54 零协议改动)、typecheck 净。§5 落库延后 stage-4。 -->
-->

## 1. aidcp-cloud — 类型与黑板新键（依赖根，最先做）

- [x] 1.1 `src/publish-agent/types.ts` 新增类型：`Visibility`/`PublishMode` 联合，及 `TopicSelection`/`MentionSelection`/`LocationSelection`/`CollectionSelection`/`VisibilityDecision`/`PermissionDecision`/`PublishModeDecision`/`Compliance`(含 `aiEnforced?`)/`ComplianceDecision`/`PublishMetadata`(其中 `visibility` 非 null、`metadataScore: number`)，字段照 design.md「类型定义」节逐字对齐（验证：`cd ../aidcp-cloud && npm run typecheck` 退出码 0）
- [x] 1.2 `types.ts` 新增 `METADATA_DEFAULT_VALUES: Omit<PublishMetadata,'decidedAt'>` 常量（保守默认：列表空、地点/合集 null、`visibility:'self_only'`、权限全 disable、`mode:'draft'`、`compliance:{}`、`metadataScore:0`）——「不凑数/不伪造/最保守」单一来源（验证：`npm run typecheck`；常量值与 design.md 逐字一致）
- [x] 1.3 `types.ts` 的 `PipelineFields`（`:179-196` 块内）增九键：`topicSelection`/`mentionSelection`/`locationSelection`/`collectionSelection`/`visibilityDecision`/`permissionDecision`/`publishModeDecision`/`complianceDecision`/`publishMetadata`；`AssembledContent`（`:104-113` 八字段）逐字不动（验证：`npm run typecheck`；`grep -n "AssembledContent" src/publish-agent/types.ts` 八字段无增删、diff 仅新增）

## 2. aidcp-cloud — 各维度决策角色（依赖 §1；八角色单一职责，仿阶段2 风格）

> 每角色 `extends BasePublishRole`、实现 `extractInput`/`execute`/`outputKey`/`getDefaultOutput`，watchKeys 取 `createdContent`（话题需 `tags`）与/或 `assembledContent`（合规需 `aiScore`/`finalContent`）。**无论成败都写自己键**：`fallback:'default'`+`execute` 内自兜底，或 `fallback:'skip'`+非 undefined `getDefaultOutput()`（取 `METADATA_DEFAULT_VALUES` 对应切片）——否则 §3 waitAll 永不集齐（黑板 R1 死锁防护，`base-role.ts:81-94`/`pipeline-context.ts:40`）。需 LLM 的角色 prompt 构造器加到 `src/publish-agent/prompts.ts`（仿现有 `buildXxxPrompt`，AI 关键词集中常量便于审计）。每角色在 `roles/index.ts` 导出。

- [x] 2.1 `roles/topic-strategist.ts` — `TopicStrategist`：watch `createdContent`，在 `tags` 基础上产 `selectedTopics`（硬约束 3-30、扩展原 tags、不编造凑数），`getDefaultOutput` 回原 tags 截断到 ≤30，`outputKey='topicSelection'`（验证：`npm run typecheck`；§6.1 单测断言数量落 [3,30]、含原 tags、空候选不捏造）
- [x] 2.2 `roles/mention-strategist.ts` — `MentionStrategist`：产 `selectedMentions`（去重、剔账号自身、≤10、无人选回 `[]` 不伪造），`outputKey='mentionSelection'`（验证：`npm run typecheck`；§6.2 单测断言去重/剔己/≤10/空回 `[]`）
- [x] 2.3 `roles/location-strategist.ts` — `LocationStrategist`：产 `selectedLocation`（可空、无则 null、不编造），`outputKey='locationSelection'`（验证：`npm run typecheck`；§6.3 单测断言有/无两分支、无候选回 null）
- [x] 2.4 `roles/collection-strategist.ts` — `CollectionStrategist`：产 `selectedCollection`（可空、无则 null、不编造），`outputKey='collectionSelection'`（验证：`npm run typecheck`；§6.3 单测断言有/无两分支、无候选回 null）
- [x] 2.5 `roles/visibility-decider.ts` — `VisibilityDecider`：产 `visibility`（`public|friends_only|self_only` 三选一、**云端必选非 null**）+ `visibilityReason`；LLM 失败/非法值降级 `self_only`、**绝不隐式 public**，`outputKey='visibilityDecision'`（验证：`npm run typecheck`；§6.4 单测断言正常三选一、失败降 self_only、不落 null/public）
- [x] 2.6 `roles/permission-decider.ts` — `PermissionDecider`：产 `permissions{comment:'allow'|'restrict'|'disable', save:'allow'|'disable'}`，`getDefaultOutput` 保守关闭，`outputKey='permissionDecision'`（验证：`npm run typecheck`；§6.5 单测断言合法组合 + 保守降级）
- [x] 2.7 `roles/publish-mode-decider.ts` — `PublishModeDecider`：产 `{mode:'immediate'|'draft'|'scheduled', publishTime:number|null}`，定时 MUST 未来且 ≤7 天（越界收敛、非定时 `publishTime=null`），`outputKey='publishModeDecision'`（验证：`npm run typecheck`；§6.6 单测断言三 mode、定时 ≤7 天、过期不接受）
- [x] 2.8 `roles/compliance-decider.ts` — `ComplianceDecider`（**2026 合规红线**）：watch `assembledContent`；硬编码 `AI_FLAVOR_THRESHOLD=0.6`，`aiScore > 0.6` **或** `finalContent` 命中 AI 关键词（`AI 生成/合成/AIGC/人工智能生成` 等）→ 强制 `compliance.ai=true`+`aiEnforced=true` 记 warn；优先级 `ai>ad>origin`；阈值/关键词不可被 prompt/人设/用户覆盖，`outputKey='complianceDecision'`（验证：`npm run typecheck`；§6.7 单测断言超阈强制、命中关键词强制、非 AI 不强制）
- [x] 2.9 `roles/index.ts` 导出全部八个新决策角色（同风格 `export { XxxRole } from './xxx.js'`）（验证：`npm run typecheck`；`grep -c "export { " src/publish-agent/roles/index.ts` 较前 +8）

## 3. aidcp-cloud — MetadataAggregator 汇合（依赖 §2；唯一生产者 publishMetadata）

- [x] 3.1 `roles/metadata-aggregator.ts` — `MetadataAggregator`：`watchKeys`=八维度中间键、`waitAll:true`、`outputKey='publishMetadata'`（仿 `ContentAssemblerRole` 五键 waitAll，`content-assembler.ts:27-35`）；汇合为单一 `publishMetadata`（含各选择 + `compliance` + `metadataScore` + `decidedAt`）；**只读 `assembledContent`（`snapshot.get`），绝不 `ctx.write('assembledContent',...)`**（验证：`npm run typecheck`；§6.8 单测断言 waitAll 八键集齐触发一次、产出 publishMetadata、不写 assembledContent）
- [x] 3.2 `MetadataAggregator` 内计算 `metadataScore`（D7 权重求和：话题 3-30 +0.2 / @数 1-10 +0.2 / 地点非 null +0.15 / 合集非 null +0.15 / 可见范围有效 +0.15 / 权限有效 +0.15，`Math.min(score,1.0)`；缺失/失败该项计 0、如实不虚高）（验证：`npm run typecheck`；§6.8 单测断言全有效=1.0 / 全缺失=0 / 部分按权重）
- [x] 3.3 `MetadataAggregator` 内 `aiEnforced` 防篡改回正：检出 `compliance.aiEnforced && !compliance.ai` → 强制回正 `ai=true`、记审计 error、绝不静默落 `ai=false`（验证：`npm run typecheck`；§6.8 单测断言篡改态被回正 ai=true 且记 error）
- [x] 3.4 `roles/index.ts` 导出 `MetadataAggregator`（验证：`npm run typecheck`；import 单测可解析）

## 4. aidcp-cloud — server 注册（依赖 §2/§3；注册顺序无关正确性）

- [x] 4.1 `src/server.ts` 的 `registerRole` 段（`:335-352`，紧随 `ContentAssemblerRole`（`:350`）之后）`publishOrchestrator.registerRole(...)` 注册八个决策角色 + `MetadataAggregator`（需 LLM 的注入 `{ llmClient: llm }`）；每角色 MUST 实例化注册、MUST NOT 仅作类型联合/注释名字（验证：`npm run typecheck`；`grep -c "registerRole" src/server.ts` 较前 +9；§6.9 整链测验证九新角色均产出键）
- [x] 4.2 确认下游 `ApprovalGatekeeperRole`/`PublishExecutorRole` 的注册、watchKeys、发布判定未改（验证：diff 仅新增 registerRole 行；§6.9 orchestrator 整链测不回归）

## 5. aidcp-cloud — （可选）PublishExecutor 落库 publishMetadata 血缘（依赖 §3；全节可选、不改发布行为）

<!-- aidcp-cloud f997638：§5 落库 + §6.10 本阶段【跳过/延后 stage-4】——落库/防篡改持久化/边缘应用一并归 stage-4，规避"落库前 metadata 未就绪"竞态；stage-3 纯决策、产出 publishMetadata 在内存上下文(休眠)。 -->

> 全节可选（D6）：不落库本阶段决策与单测亦成立。落库纯属可观测/血缘，**绝不改 `handleAutoPublish`/`handleManualReview`/`handleAbort` 发布判定与指令行为**，**绝不给 `PublishExecutorRole.config.watchKeys` 加 `publishMetadata`**（维持 `['gateDecision']`，D3）。

- [ ] 5.1 （可选）`roles/publish-executor.ts` 落库软读 `snapshot.get('publishMetadata') ?? METADATA_DEFAULT_VALUES`（缺失记 warn 标元数据缺失、不卡发布、如实记缺失），随 `recordId` 落库；落库前再校验 `aiEnforced && !ai` → 记审计 error 拒绝降级（与 §3.3 双道守）（验证：`npm run typecheck`；§6.10 单测断言缺失→fallback+warn、发布路径与未落库逐路径一致、篡改态被拒） <!-- 延后 stage-4（deferred-optional，不卡 stage-3 归档）；见 §5 头注 -->
- [ ] 5.2 （可选）`src/publish-agent/publish-log-store.ts` 加可空列 `publish_metadata JSONB` + `ai_enforced BOOLEAN DEFAULT FALSE`（`ADD COLUMN IF NOT EXISTS` 幂等、向后兼容），`store` 加可选 `recordMetadata?`（仿现有可选 `updateStatus?`/`updatePostId?`，`publish-executor.ts:19-20`）（验证：`npm run typecheck`；§6.10 单测断言旧行无列兼容、DDL 重复执行幂等） <!-- 延后 stage-4（deferred-optional，不卡 stage-3 归档）；见 §5 头注 -->
- [x] 5.3 确认 `CommandSequencer.buildCommandSequence`（`command-sequencer.ts:81-104`）**未新增任何元数据指令**（仍止于 `add_with_candidate(topic)` + `submit_publish`/`capture_postId`，不含 `set_option`/`set_schedule`/`add_with_candidate(mention|location|collection)`）（验证：现有 `command-sequencer.test.ts` 不回归 + 断言指令集不含元数据指令） <!-- aidcp-cloud f997638：本 change 未触碰 CommandSequencer（proposal Impact 声明零元数据指令）；§7.1 AC-PROTO 零协议变更 + §7.2 全量回归绿 → 指令集天然不含元数据指令 -->

## 6. aidcp-cloud — 测试（依赖 §1-§5；各角色单测 + aggregator + orchestrator 整链）

> 测试放 `test/publish-agent/`（仿现有 `*.test.ts`），`tsx --test` 可脱浏览器。

- [x] 6.1 `test/publish-agent/topic-strategist.test.ts`：数量落 [3,30]、扩展原 tags、**反例**空候选不编造凑数（metadataScore 该维度 0）（验证：`npm test -- test/publish-agent/topic-strategist.test.ts` 退出码 0）
- [x] 6.2 `test/publish-agent/mention-strategist.test.ts`：去重、剔账号自身、≤10、无人选回 `[]` 不伪造（验证：`npm test -- test/publish-agent/mention-strategist.test.ts`）
- [x] 6.3 `test/publish-agent/location-collection-strategist.test.ts`（或拆两文件）：地点/合集无候选回 `null`、**反例**不编造（验证：`npm test -- <file>`）
- [x] 6.4 `test/publish-agent/visibility-decider.test.ts`：正常三选一非空 + reason、失败降 `self_only`、**反例**不隐式 `public`、不落 `null`（验证：`npm test -- test/publish-agent/visibility-decider.test.ts`）
- [x] 6.5 `test/publish-agent/permission-decider.test.ts`：合法权限组合、失败保守默认（验证：`npm test -- test/publish-agent/permission-decider.test.ts`）
- [x] 6.6 `test/publish-agent/publish-mode-decider.test.ts`：定时落未来且 ≤7 天、超界收敛、非定时 `publishTime=null`（验证：`npm test -- test/publish-agent/publish-mode-decider.test.ts`）
- [x] 6.7 `test/publish-agent/compliance-decider.test.ts`（**红线核心**）：`aiScore > 0.6` 强制 `ai=true`+`aiEnforced=true`、命中 AI 关键词（未超阈）仍强制、非 AI 不强制（`aiEnforced` false/缺省）、优先级 `ai>ad>origin`（验证：`npm test -- test/publish-agent/compliance-decider.test.ts`）
- [x] 6.8 `test/publish-agent/metadata-aggregator.test.ts`：waitAll 八键集齐触发一次（部分降级仍触发不挂起）、`metadataScore` 全有效=1.0/全缺失=0/部分按权重、**反例** `aiEnforced && !ai` 篡改态被回正 `ai=true` 记 error、**反例**绝不 `ctx.write('assembledContent',...)`（验证：`npm test -- test/publish-agent/metadata-aggregator.test.ts`）
- [x] 6.9 扩 `test/publish-agent/publish-orchestrator.test.ts`（整链断言）：跑完一轮断言 (a) `publishMetadata` 已产出（含 compliance + metadataScore），(b) **`assembledContent` 仍为且仅为原八字段、值与阶段2 同形、未注入任何元数据字段**（不回归断言），(c) 元数据链与发布链并行、`publishResult` 终止条件不受 `publishMetadata` 影响（验证：`npm test -- test/publish-agent/publish-orchestrator.test.ts`）
- [ ] 6.10 （可选，仅当做 §5）扩 `test/publish-agent/publish-executor.test.ts`：元数据缺失→fallback+warn、落库不改发布路径（与未落库逐路径一致）、篡改态被拒、旧行无列兼容（验证：`npm test -- test/publish-agent/publish-executor.test.ts`） <!-- 延后 stage-4（deferred-optional，仅当做 §5 才需；不卡 stage-3 归档） -->

## 7. aidcp-cloud — 全量回归（依赖 §1-§6；安全红线必须全过）

- [x] 7.1 `cd ../aidcp-cloud && npm run test:acceptance`：AC-PUB（未授权绝不静默发布）、AC-PROTO（两份 protocol.ts 不漂移——本阶段零协议改动应天然不动）、AC-RISK 全过、无新失败（验证：命令退出码 0）
- [x] 7.2 `cd ../aidcp-cloud && npm test`：全量单测含 §6 新增全过、阶段2 既有 publish-agent 测试不回归（验证：命令退出码 0）
- [x] 7.3 `cd ../aidcp-cloud && npm run typecheck`：全仓类型零错误（含两份 protocol.ts `Record<MessageType,true>` 穷举不漂移）（验证：命令退出码 0）

<!-- 2026-07-03 deployed — verified via read-only ECS probe: all sampled stage-3 role files (compliance-decider / metadata-aggregator / permission-decider / visibility-decider) present on /opt/aidcp/cloud, md5 identical to local master, service active. Deploy vehicle: full ECS→HEAD upgrade (control-repo c4ef902). Remaining [ ] tasks are explicit stage-4 deferrals (§5.1/5.2/6.10). -->
