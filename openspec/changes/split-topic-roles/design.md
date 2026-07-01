## Context

发布管线是事件驱动多角色（`BasePublishRole` + 黑板 `PipelineContext`，`watch` / `watchAll`）。话题当前的现状与痛点（均已坐实 `文件:行`）：

- **生成**：话题（=标签）由 `ContentCreator` 的单次 JSON 顺带产出（`content-creator.ts:77`），与正文/风格混在一次调用。名为「话题」的 `TopicStrategist` 只做 `dedup + slice(0,30)`、不调 LLM（`topic-strategist.ts:28-32`）——不是真正的生成或评判。
- **填写**：边缘 `add_with_candidate{topic}` → `buildTagInputRequest`（`op:'input'`）往 `role=button, text=话题` set value（`publish-command-handlers.ts:258-268`、`publish-post.ts:283-291`、`action-executor.ts:76-86`），从不打 `#`、不等下拉、不点建议。后置校验 `input_tag` 只要 tag 串出现在页面任意文本即过（`publish-post.ts:232-240`）→ 静默假成功。
- **`guard_persist`**：话题/`set_option` 等元数据步是唯一走通用守卫 `LocatingEngine.resolveAndAct`（先 `handleGuards`）的步；标题/正文/提交走 CDP 直驱、绕过守卫。发布页真实遮罩两轮清不掉 → `guard_persist`（`engine.ts:96-108,242-257`；`guard.ts:41-63`，其中 `overlay_mask` 无 `findDismiss`、去点 mask 自身空转）。

已有先例：`publish-pipeline` 已把「标题」从单次 JSON 拆成独立角色 `TitleCreator`（正文定稿后另一次调用）。本变更把同一治理路线应用到话题。

约束（用户已定，不可改）：① 评判=纯 LLM 相关性+质量、cloud 闭环、本期不做 edge 回传平台候选；② 填写=edge 完整真实交互，选择器需实机校准（gated）；③ 生成输入=定稿正文。

## Goals / Non-Goals

**Goals:**
- 话题的**生成 / 评判 / 填写**各自成独立专职角色，与正文角色彻底解耦；`ContentCreator` 不再产出标签。
- 边缘做**真实加话题**（`#`→下拉→选建议→校验真 token），修掉「静默假成功」与 `guard_persist`。
- 审批卡 / 落库 / 下发三者的话题**恒一致**（单一真源 `publishMetadata.topics`）。
- 下游 `MetadataAggregator` / `publishMetadata` / 协议 **零改动**；黑板不死锁；安全红线不破。

**Non-Goals:**
- 不做「平台真实话题候选」解析 / edge 回传（本期评判纯 LLM）。
- 不改协议（`add_with_candidate` payload 不变）。
- 不硬删 `CreatedContent.tags` / `AssembledContent.finalTags` 字段（保留恒 `[]`，硬删列为可选 follow-up，避免动「八字段稳定边界」的测试面）。
- 不改 `mention` / `location` / `collection` 的填写路径（同样弱校验，但本期不扩散）。

## Decisions

### D1. 三角色而非合并（尊重用户三分诉求）
- **决定**：`TopicGenerator`（LLM 生成）+ `TopicEvaluator`（LLM 评判）两个 cloud 角色 + edge `runAddTopic` 填写；删除 `TopicStrategist`。
- **备选**：把生成+评判合并成一次 LLM 调用（自评自筛）。对抗性评审指出纯 LLM 评判无新信号、偏仪式化、且多一个 180s 串行 + 翻倍失败面。
- **理由**：用户明确要求「生成/评判/填写」三分。保留独立评判换来：隔离「只筛不加」红线于可单测单元、后台可给评判配更严/更省的模型。延迟与失败面用 D2 缓解。评判仍做确定性 `dedup + slice(0,30)` 收口（不靠 LLM 凑数）。

### D2. 生成角色 watch `assembledContent`、与 `TitleCreator` 并行
- **决定**：`TopicGenerator` `watchKeys:['assembledContent']`，输入 `assembledContent.finalContent`（定稿正文），与 `TitleCreator`（同 watch `assembledContent`）并行；**不** watch `titleSelection`。
- **理由**：话题源于正文而非标题（也贴合约束③）。若串在标题后，`title→gen→eval` = 3×180s ≈ 540s 串行尾，可能撞穿 `pipelineTimeoutMs=600_000` 总闸、把已付费生成的配图一起废掉；而 `model-call-timeout-invariants` 只查单角色、查不出串行和。并行后话题腿仅 `gen→eval`。

### D3. `TopicEvaluator` 复用 `topicSelection` outputKey（最小爆炸半径）
- **决定**：新增中间键 `topicCandidates`（Generator→Evaluator 交接）；Evaluator 产出仍写现有键 `topicSelection`（同 `TopicSelection` 类型，不加 scores/rejected）。
- **理由**：`MetadataAggregator` 的 8 键 `waitAll`、`publishMetadata.topics`、其测试全部 **零改**——只是 `topicSelection` 的**生产者**从 `TopicStrategist`（watch `createdContent`）换成 `TopicEvaluator`（watch `topicCandidates`）。

### D4. 审批==下发：单一真源 `publishMetadata.topics`
- **决定**：话题生成变晚 → `finalTags` 恒 `[]`；`PublishExecutor` 的**四处**落库/发卡（含 `failed`/`abort` 记录）tags 全部改读 `publishMetadata.topics`，并把 `publishMetadata` 加进 executor 的 `waitAll`（顺带消除 `context.get('publishMetadata')` 取值 race）。
- **理由**：若审批卡仍读 `finalTags` 会「审批显示空、下发发真话题」。`publish-dispatcher.ts:175` 已读 `metadata.topics` 不变 → 卡==落库==下发按构造成立。`MetadataAggregator` 不改。

### D5. edge `runAddTopic` 由显式开关门控，不靠 `this.cdp`
- **决定**：新增 `AIDCP_PUBLISH_TOPIC_CDP`（默认 **OFF**）门控 `runAddTopic`；OFF 时保留现有 `buildTagInputRequest` 路径。实机校准（下拉容器选择器 / 真 token 选择器 / Enter-vs-click 提交行为）完成前不打开。
- **备选**：按 `this.cdp` 存在与否路由（原设计）。评审指出生产 cdp **恒注入**，该「无 cdp 兜底」在生产不可达 → Phase B 合并到实机校准之间会**在生产静默丢光话题**（假阴性，同样是「行为撒谎」）。
- **理由**：把「未校准不上线」变成运行时可强制，而非仅 tasks.md 口头约束。

### D6. `runAddTopic` 镜像已校准的 CDP 直驱 handler
- **决定**：聚焦 `.tiptap.ProseMirror`（复用 `runFillField` 的 focus）→ `typeHumanized('#'+kw)` 触发建议下拉 → 轮询等下拉容器（≤4s）→ 用盒模型中心点（复用 `findShadowButtonCenter` 的 `DOM.getDocument(pierce)` 走查）点文本精确匹配的建议（`dispatchClick` 精确落点；无命中则 Enter 兜底）→ `topicPillValidator` 断言真话题 pill/token 节点出现（**非**全局子串）→ fail-closed 回 `no_target`/`post_validate_failed`。
- **理由**：与标题/正文/提交同一条「直驱+绑定式后置校验」路线；把「静默假成功」换成诚实的真 token 校验。

## Risks / Trade-offs

- **[串行延迟] `gen→eval` 仍在关键路径增 ~180–360s** → D2 并行标题、评判失败保守空、监控总时长；总闸 600s 且并行后余量足。
- **[翻倍失败面] 两个 `fallback:'default'` LLM 角色，任一超时 → 话题空** → 符合「失败保守」教条；两角色各自单测其默认空；接受话题为增强项、空话题不阻断有效帖。
- **[edge 假阴性] 未校准的 `topicPillValidator` 会把真成功报失败** → D5 开关默认 OFF + 现路径为净兜底；开关仅在 B5 实机校准并提交 DOM 样本后打开。
- **[话题为 best-effort、失败仅 warn] 话题静默丢仍不阻断发布** → 本期沿用（话题是增强非必需）；如需强约束再单开 change 把话题移出 best-effort 并回传实际落地清单。
- **[`finalTags` 恒空的遗留列] `publish_log` 的 `tags` 若仍从 `finalTags` 落会写空** → D4 四处一并改读 `publishMetadata.topics`，勿遗漏任一 insert 点。

## Migration Plan

- **落地顺序**：Phase A（cloud 两角色 + 解耦正文）→ Phase B（edge `runAddTopic` + 收紧校验，B5 实机校准为 gated）→ Phase C（审批==下发接线 + 回归）。A/C 可先上线（开关 OFF，边缘行为不变）；B 的开关待实机校准后再开。
- **数据迁移**：无。`publish_metadata.topics` JSONB 形状不变（`string[]`），旧草稿重放一致；内存黑板的在飞 run 重启即弃（非问题）。
- **回归**：cloud 与 edge 各 `npm run test:acceptance` → `npm test` → `npm run typecheck`；`AC-PROTO-*`（协议未漂移，本期无协议改动天然成立）/ `AC-PUB-*`（未授权绝不发布）须绿。
- **回滚**：Phase B 关开关即回退到原填写路径；Phase A/C 为角色替换，回滚即还原 `TopicStrategist` 注册与 executor tags 源。

## Open Questions

1. **[GATED 实机]** 边缘话题下拉容器选择器、已提交 token/pill 节点选择器、以及 XHS 是「点建议」还是「Enter 提交」——须真机 CDP 抓一次 DOM 样本确认后方可打开 `AIDCP_PUBLISH_TOPIC_CDP`。
2. 超时 env 命名：新增 `AIDCP_PUBLISH_TOPIC_TIMEOUT_MS` 还是复用标题的？两者默认 180_000。
3. `TopicSelection` 保持最简（不带评判理由/被弃列表）——确认后台/可观测性暂不需要暴露评判 rationale（未来加是增量安全）。
