## MODIFIED Requirements

### Requirement: 标题由独立角色在正文定稿后生成

系统 SHALL 以一个独立角色 `TitleCreator`（角色 id `publish:TitleCreator`）生成发帖标题，与内容生成解耦以避免单次 LLM 调用的注意力稀释。该角色 MUST `watchKeys=['assembledContent']`，以**最终定稿正文** `assembledContent.finalContent` 为输入（MUST NOT 取草稿 `createdContent.content`——正文经去 AI 味环节改写后才定稿，标题须忠于真正发出的文字），单次短提示产出一个 ≤18 可见字符的钩子标题，写入新黑板字段 `titleSelection`（`{title, source:'llm'|'derived', decidedAt}`）。`source` MUST 如实标注：LLM 真产出为 `'llm'`，任何派生/兜底为 `'derived'`，MUST NOT 把派生标题标为 `'llm'`。同理，话题亦自 `ContentCreator` 解耦：`ContentCreator` 自话题拆分能力起 SHALL 仅产出正文（及 tone / style），MUST NOT 再产出标签，标题由 `TitleCreator`、话题由 `TopicGenerator` 各自独立调用产出。

#### Scenario: 正文定稿后激活、据定稿正文产出标题
- **WHEN** `ContentAssembler` 写出 `assembledContent`（含 `finalContent`）
- **THEN** `TitleCreator` 激活，读 `assembledContent.finalContent` 单独生成一个 ≤18 字标题，写入 `titleSelection`，`source='llm'`

#### Scenario: 取定稿正文而非草稿
- **WHEN** 去 AI 味环节把草稿里的某句话删改、`finalContent` 与 `createdContent.content` 不一致
- **THEN** `TitleCreator` 据 `finalContent`（真正发出的版本）拟标题，标题不引用已被删改的草稿句子

#### Scenario: 标题、正文、话题分多次 LLM 调用
- **WHEN** 生成一篇帖子
- **THEN** 正文由 `ContentCreator` 一次调用产出（**仅正文**，不含标题、不含标签）、标题由 `TitleCreator`、话题由 `TopicGenerator` 各自另次调用产出；标题与话题 MUST NOT 再作为「标题+正文+标签」单次 JSON 里被稀释的子字段

### Requirement: ContentAssembler 瘦身但产出同形 assembledContent（稳定边界、下游零改动）

`ContentAssembler` SHALL 瘦身为**纯组装**角色：`watchAll`（`waitAll: true`）`cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 就绪后仅做字段拼装，MUST NOT 再持有 `llmClient` / `postProcessor`、MUST NOT 做任何 LLM 调用或外部 IO。它 SHALL 产出 `assembledContent`，字段为 `{ finalContent, finalTags, imageUrls, imageUrl, aiScore, qualityScore, rewritten, flaggedPhrases, assembledAt }`：`imageUrls` ← `coverSelection.imageUrls`（上传全集），`imageUrl` ← 封面（`imageUrls[0] ?? null`，保留为向后兼容的单数派生字段）。**自话题拆分能力起，`finalTags` 恒为 `[]`**——话题改由独立 `TopicGenerator` / `TopicEvaluator` 产出、经 `publishMetadata.topics` 落地并成为唯一真源，`finalTags` 不再承载笔记话题；这是话题拆分能力显式许可的语义变更（与多图能力显式新增 `imageUrls` 同类的预期演进），MUST NOT 被读作历史细拆所禁的静默改形。除此显式变更外，其余字段集 / 语义与细拆前一致。下游 `PublishExecutor` 因多图能力 SHALL 读 `imageUrls` 下发上传全集；`ApprovalGatekeeper`（watch `assembledContent`）MUST NOT 因字段拼装方式而改注册。本要求 MUST NOT 触及协议或 edge。

#### Scenario: 瘦身后仅组装、无 LLM / 无 IO

- **WHEN** `cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 五键全部就绪
- **THEN** `ContentAssembler` 仅做字段映射（`finalContent ← cleanedContent.content`、`finalTags ← createdContent.tags`（因 `createdContent.tags` 自话题拆分起恒 `[]`，`finalTags` 恒 `[]`）、`imageUrls ← coverSelection.imageUrls`、`imageUrl ← imageUrls[0] ?? null`、`aiScore ← aiFlavorScore.aiScore`、`qualityScore ← qualityReport.qualityScore`、`rewritten`/`flaggedPhrases ← cleanedContent`），其依赖中不含 `llmClient` / `postProcessor`

#### Scenario: 多图能力新增 imageUrls 字段、其余形状不变

- **WHEN** 重组后的生产段跑完、`ContentAssembler` 写出 `assembledContent`
- **THEN** `assembledContent` 含 `finalContent` / `finalTags` / `imageUrls` / `imageUrl` / `aiScore` / `qualityScore` / `rewritten` / `flaggedPhrases` / `assembledAt`；`imageUrls` 为上传全集、`imageUrl` 为封面（首张派生），`finalTags` 恒 `[]`（话题移交独立角色），其余字段语义与细拆前等价

#### Scenario: 下游消费方按多图能力读取

- **WHEN** 一轮发布流水线在多图能力下完整跑通
- **THEN** `ApprovalGatekeeper` 仍 watch `assembledContent`、`PublishExecutor` 仍 watch `gateDecision`；`PublishExecutor` 读 `assembledContent.imageUrls` 下发上传全集、读封面字段下发 `cover`，读 `publishMetadata.topics` 作为话题真源，端到端结果（`gateDecision` / `publishResult`）形状与单图等价

#### Scenario: 红线——细拆波及协议或越界改形（反例）

- **WHEN** 任一改动改了 `assembledContent` 除 `imageUrls`（多图能力显式新增）/ `finalTags` 恒空（话题拆分能力显式许可）外的字段集 / 字段名 / 字段语义，或触及协议 / edge
- **THEN** MUST 视为越界、不予合入（稳定边界 `assembledContent` 除各能力显式许可的变更外不可破，且 MUST NOT 触及协议 / edge）
