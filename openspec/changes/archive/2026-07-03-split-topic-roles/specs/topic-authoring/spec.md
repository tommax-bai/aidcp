## ADDED Requirements

### Requirement: 话题由独立角色依定稿正文生成

系统 SHALL 以一个独立角色 `TopicGenerator`（角色 id `publish:TopicGenerator`）生成笔记话题候选，与内容生成解耦——话题 MUST NOT 再作为 `ContentCreator` 单次 JSON 的子字段被稀释。该角色 MUST `watchKeys=['assembledContent']`，以**定稿正文** `assembledContent.finalContent` 为输入，与 `TitleCreator` 并行（同 watch `assembledContent`），单次提示产出话题候选，写入新黑板键 `topicCandidates`（`{ candidates: string[], generatedAt }`）。产出的候选 MUST 去除前导 `#`、去首尾空白。红线：话题不足也 MUST NOT 编造补足（宁缺毋滥）；LLM 失败 / 超时 MUST 经 `fallback` 写空候选（`{candidates:[]}`），MUST NOT 让 `waitAll` 因缺键死锁。

#### Scenario: 正文定稿后激活、据定稿正文产出候选
- **WHEN** `ContentAssembler` 写出 `assembledContent`（含 `finalContent`）
- **THEN** `TopicGenerator` 激活，读 `assembledContent.finalContent` 生成话题候选，写入 `topicCandidates`

#### Scenario: 与标题并行、不串在标题之后
- **WHEN** 一篇帖子进入定稿后阶段
- **THEN** `TopicGenerator` 与 `TitleCreator` 均 watch `assembledContent`、并行激活，话题生成 MUST NOT 依赖 `titleSelection`（不引入 `title→gen→eval` 串行 LLM 尾）

#### Scenario: 红线——生成失败编造话题（反例）
- **WHEN** LLM 生成话题失败或产出为空，有实现想凑几个通用话题补足
- **THEN** MUST 被拒绝；正确行为是经 `fallback` 写空候选 `{candidates:[]}`，如实置空

### Requirement: 话题评判为独立角色、纯 LLM 只筛不加

系统 SHALL 以一个独立角色 `TopicEvaluator`（角色 id `publish:TopicEvaluator`）评判话题候选，`watchKeys=['topicCandidates']`。评判 MUST 为**纯 LLM** 相关性 / 质量 / 合规判断（本能力不依赖平台真实话题数据、不做边缘回传候选）。评判 MUST **只筛不加**：产出的选定话题 MUST 是候选的子集（`selected ⊆ candidates`），MUST NOT 新增候选之外的话题，再做确定性去重并截断到 ≤30。产出写入既有黑板键 `topicSelection`（`{ selectedTopics: string[], selectedAt }`，形状不变，接管原 `TopicStrategist`），下游 `MetadataAggregator` / `publishMetadata.topics` 零改动。LLM 失败 / 超时 MUST 经 `fallback` 写空选择（`{selectedTopics:[]}`）。

#### Scenario: 据候选评判产出选定话题
- **WHEN** `TopicGenerator` 写出 `topicCandidates`
- **THEN** `TopicEvaluator` 激活，按相关性 / 质量 / 合规筛选候选，去重截断 ≤30，写入 `topicSelection`

#### Scenario: 只筛不加、选定为候选子集
- **WHEN** 评判完成产出 `topicSelection.selectedTopics`
- **THEN** 每个选定话题 MUST 出现在 `topicCandidates.candidates` 中，MUST NOT 存在候选之外的新话题

#### Scenario: 评判失败保守置空
- **WHEN** `TopicEvaluator` 的 LLM 调用失败 / 超时
- **THEN** 经 `fallback` 写 `{selectedTopics:[]}`，`MetadataAggregator` 的 `waitAll` 仍能就绪、不死锁；本次帖子诚实无话题（不阻断有效帖）

### Requirement: 话题黑板键有唯一生产者且不死锁

新增键 `topicCandidates` SHALL 在 `PipelineFields` 登记类型，且 `topicCandidates` 恰由 `TopicGenerator` 唯一生产、`topicSelection` 恰由 `TopicEvaluator` 唯一生产（替换原 `TopicStrategist` 为该键的生产者）。两个新角色 MUST 经 `fallback`（`default` + `getDefaultOutput`）保证失败时仍写自己的键，使下游 `waitAll`（`MetadataAggregator` 8 键、`PublishExecutor` 依赖）不因某键永不就绪而死锁。

#### Scenario: 每个话题键恰一个生产者
- **WHEN** 审视生产段角色注册表
- **THEN** `topicCandidates ← TopicGenerator`、`topicSelection ← TopicEvaluator`，无两个角色写同一键，且 `TopicStrategist` 已删除、不再生产 `topicSelection`

#### Scenario: 失败链路仍写键、waitAll 不死锁
- **WHEN** 话题生成或评判失败降级
- **THEN** 对应角色经 `fallback` + `getDefaultOutput` 写空值键，`MetadataAggregator` 的 `waitAll` 终能就绪、流水线不超时

### Requirement: 话题生成 / 评判角色模型后台可独立配置且超时不短于模型预算

`TopicGenerator` / `TopicEvaluator` SHALL 各自登记 `role-catalog`（`publish:TopicGenerator` / `publish:TopicEvaluator`），供后台独立配置模型；未配置时回落默认模型且不回归。两角色默认 `timeoutMs` MUST ≥ 单次模型调用天花板（当前 ≥180000）并把该超时同传进各自的模型调用（不短于模型预算）。

#### Scenario: 两角色可在后台单独配模型
- **WHEN** 运营在后台为 `publish:TopicGenerator` / `publish:TopicEvaluator` 指定模型
- **THEN** 两角色分别用各自配置的模型；未配置则回落默认、行为不回归

#### Scenario: 角色超时不短于模型天花板
- **WHEN** 校验模型调用超时不变量
- **THEN** `TopicGenerator` / `TopicEvaluator` 的 `timeoutMs` ≥ 180000，且传入模型调用的超时不短于该值

### Requirement: 边缘做真实加话题交互、校验真话题 token，绝不静默假成功

边缘填写话题 SHALL 做**真实的平台加话题交互**：聚焦正文富文本编辑器 → 键入 `#关键词` 触发平台建议下拉 → 从下拉中选中匹配建议（点击或 Enter 提交）→ 后置校验 MUST 断言一个**真话题 token / pill 节点**已生成，MUST NOT 以「关键词字符串出现在页面任意文本」判成功（此为红线「静默假成功」）。定位失败 / 下拉未出现 / token 未生成 MUST 诚实回 `no_target` / `post_validate_failed`，MUST NOT 伪造成功。

#### Scenario: 真实交互并校验真 token
- **WHEN** 边缘收到一条话题填写指令且真实加话题通道已启用
- **THEN** 聚焦正文 → 键入 `#关键词` → 等建议下拉 → 选中匹配建议 → 校验页面出现对应真话题 token / pill 节点，成功才回 `ok`

#### Scenario: 红线反例——只查全局子串判成功（禁止）
- **WHEN** 有实现只检查关键词字符串出现在页面任意元素文本（正文常含同词）即判成功
- **THEN** MUST 被拒绝；正确校验是断言真话题 token / pill 节点存在，token 未生成即诚实失败

#### Scenario: 下拉未出现诚实失败
- **WHEN** 键入 `#关键词` 后平台建议下拉在超时内未渲染
- **THEN** 诚实回 `no_target`（不点、不假装成功），话题为增强项、失败不阻断有效帖

### Requirement: 边缘真实加话题由显式开关门控、未校准不上线

边缘真实加话题通道 SHALL 由**显式配置开关**（`AIDCP_PUBLISH_TOPIC_CDP`）门控，MUST NOT 仅以「CDP 是否注入」判是否启用（生产 CDP 恒注入，会使兜底路径不可达）。**实机校准 + 端到端确认（真话题 `a.tiptap-topic` 真被贴上）之前，默认关闭、走原有填写路径为净兜底**，MUST NOT 在未确认时于生产静默丢光话题；确认通过后 SHALL 默认启用，并保留 env kill-switch（显式 `0/false/no/off` 回退兜底）。真实交互所需的下拉容器选择器 / 真 token 选择器 / 提交行为 SHALL 经一次真机 DOM 校准确认。

#### Scenario: 显式 kill-switch → 走兜底路径
- **WHEN** `AIDCP_PUBLISH_TOPIC_CDP` 设为 `0`/`false`/`no`/`off`
- **THEN** 边缘走原有话题填写路径（不启用真实交互 handler），作为出问题时的即时回退

#### Scenario: 实机确认后默认启用真实交互
- **WHEN** 真机 DOM 校准 + 端到端确认已完成（真话题 token 真被贴上），且未设 kill-switch
- **THEN** 边缘走真实加话题 handler（`#`→下拉→选建议→校验真 token）

#### Scenario: 红线反例——按 CDP 存在与否路由（禁止）
- **WHEN** 有实现以 `this.cdp` 是否注入决定启用真实 handler，而生产 CDP 恒注入
- **THEN** MUST 被拒绝；否则校准前生产会对每个话题报失败、静默丢光话题（假阴性）

### Requirement: 话题单一真源 publishMetadata.topics、审批卡等于落库等于下发

笔记话题的唯一真源 SHALL 为 `publishMetadata.topics`。因话题在正文定稿后才产出，`assembledContent.finalTags` 不再承载话题（恒空）。`PublishExecutor` 的**所有**发卡 / 落库路径（含成功 / `failed` / `abort` 记录）SHALL 从 `publishMetadata.topics` 取话题写入，MUST NOT 从 `finalTags` 取（否则审批卡显示空而下发发真话题）。`PublishExecutor` SHALL 把 `publishMetadata` 纳入其 `waitAll` 依赖，以消除取值竞态。审批卡展示的话题 MUST 等于落库话题、MUST 等于下发时驱动的话题。

#### Scenario: 三处话题一致
- **WHEN** 一份草稿走完生成、落库、审批、下发
- **THEN** 审批卡展示的话题 = 落库 `publishMetadata.topics` = 下发段驱动的话题，三者恒一致

#### Scenario: 所有落库路径读 publishMetadata.topics
- **WHEN** `PublishExecutor` 在成功 / `failed` / `abort` 任一路径落库
- **THEN** 其 tags 字段取自 `publishMetadata.topics ?? []`，MUST NOT 取自 `finalTags`

#### Scenario: executor 等 publishMetadata 就绪
- **WHEN** `PublishExecutor` 激活
- **THEN** 其 `waitAll` 依赖含 `publishMetadata`，取 `publishMetadata.topics` 不再存在读到未就绪值的竞态
