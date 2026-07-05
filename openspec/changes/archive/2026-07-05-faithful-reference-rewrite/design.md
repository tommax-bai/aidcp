# Design: 保真参照洗稿角色链

## D1. 参照路径从常规自由创作中分叉

现状 `triggerManual(accountId, { referenceNote })` 仍构造同一个 `TriggerInput`，但新链路在角色层做分叉：

- `ContentScout` 在 `referenceNote` 存在时不激活，避免再次做选题侦察和方向重写。
- `ContentCreator` 在 `referenceNote` 存在时不激活，避免常规 prompt 的「补充个人经验」继续污染参照稿。
- 新保真角色链监听同一个 `trigger`，最终由 `FidelityAuditor` 写入标准 `createdContent`。

这样下游 `CategoryClassifier`、配图三角色、`ContentCleaner`、质量评分、`ContentAssembler`、`TitleCreator`、话题、元数据、人审和发布执行都无需改动。

## D2. 四角色职责

1. `ReferenceAnalyzer`
   - 输入：`TriggerInput.generateInput.referenceNote` 和账号人设。
   - 输出：`referenceAnalysis`，包含原文主旨、结构大纲、事实/数据/时间/人物、论点、禁止新增清单。
   - 失败策略：`abort`。分析失败不得发布。

2. `FaithfulRewritePlanner`
   - 输入：`referenceAnalysis` + 账号人设。
   - 输出：`faithfulRewritePlan`，按段列出保留信息、表达改写方式、标题方向和不得新增内容。
   - 失败策略：`abort`。

3. `FaithfulDraftWriter`
   - 输入：`referenceAnalysis` + `faithfulRewritePlan` + 账号人设。
   - 输出：`faithfulDraft`，只产草稿，不直接写 `createdContent`。
   - 失败策略：`abort`。

4. `FidelityAuditor`
   - 输入：原文、`referenceAnalysis`、`faithfulRewritePlan`、`faithfulDraft`。
   - 输出：通过时写 `createdContent`；不通过时写 `pipelineAbort`。
   - 审核维度：事实覆盖、未授权新增、视角/身份漂移、结构偏离、近似照抄。

## D3. 审核通过后复用下游

`FidelityAuditor` 通过后将草稿转换为既有 `CreatedContent`：

- `title` 为草稿种子标题，仅作后续 `TitleCreator` 的参考；最终标题仍由 `TitleCreator` 基于定稿正文生成。
- `content` 为保真改写正文。
- `tone` 与 `style` 保持现有字段形状。
- `tags` 仍为空数组，话题由 `TopicGenerator`/`TopicEvaluator` 后续生成。

## D4. 角色配置

四个新角色加入 `ROLE_CATALOG`：

- `ReferenceAnalyzer` / `FidelityAuditor`：`publish_gate` 或判定类语义，不开放温度。
- `FaithfulRewritePlanner` / `FaithfulDraftWriter`：`publish_create`，文本角色，可按角色配置模型；`FaithfulDraftWriter` 开放温度，`FaithfulRewritePlanner` 可配置模型但温度关闭以保持计划稳定。

后台不需要新页面：现有角色配置页从 `/api/roles` 读取目录并渲染，新增目录项即可出现。

## D5. 风险与取舍

- 保真链比常规创作多 4 次文本调用，成本和耗时上升；这是保真约束的代价。
- `ContentCleaner` 后续仍可能做去 AI 味重写。为降低漂移，短期保持原链路但审核点前置；若后续发现清洗导致保真破坏，再独立改造「参照稿清洗后复审」。
- 标题/话题下游会再创作，但它们基于保真正文，不得改正文事实；人审仍是最后闸。

