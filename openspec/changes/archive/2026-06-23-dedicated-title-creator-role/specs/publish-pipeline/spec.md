## ADDED Requirements

### Requirement: 标题由独立角色在正文定稿后生成

系统 SHALL 以一个独立角色 `TitleCreator`（角色 id `publish:TitleCreator`）生成发帖标题，与内容生成解耦以避免单次 LLM 调用的注意力稀释。该角色 MUST `watchKeys=['assembledContent']`，以**最终定稿正文** `assembledContent.finalContent` 为输入（MUST NOT 取草稿 `createdContent.content`——正文经去 AI 味环节改写后才定稿，标题须忠于真正发出的文字），单次短提示产出一个 ≤18 可见字符的钩子标题，写入新黑板字段 `titleSelection`（`{title, source:'llm'|'derived', decidedAt}`）。`source` MUST 如实标注：LLM 真产出为 `'llm'`，任何派生/兜底为 `'derived'`，MUST NOT 把派生标题标为 `'llm'`。

#### Scenario: 正文定稿后激活、据定稿正文产出标题
- **WHEN** `ContentAssembler` 写出 `assembledContent`（含 `finalContent`）
- **THEN** `TitleCreator` 激活，读 `assembledContent.finalContent` 单独生成一个 ≤18 字标题，写入 `titleSelection`，`source='llm'`

#### Scenario: 取定稿正文而非草稿
- **WHEN** 去 AI 味环节把草稿里的某句话删改、`finalContent` 与 `createdContent.content` 不一致
- **THEN** `TitleCreator` 据 `finalContent`（真正发出的版本）拟标题，标题不引用已被删改的草稿句子

#### Scenario: 标题与正文分两次 LLM 调用
- **WHEN** 生成一篇帖子
- **THEN** 正文由 `ContentCreator` 一次调用产出、标题由 `TitleCreator` 在其后另一次调用产出，标题不再作为「标题+正文+标签」单次 JSON 里被稀释的子字段

### Requirement: 标题生成失败则发布失败且绝不造假标题

`TitleCreator` 失败（LLM 调用失败 / 超时 / 多次重试后仍不合规）时系统 MUST 判该次发布失败，MUST NOT 派生或编造一个标题去顶替继续发布。角色失败策略为 `abort`：失败时**不写 `titleSelection`**，下游发布因缺该字段而不激活、本次流水线判 `failed`。角色默认 `timeoutMs=120000`。失败 MUST 即时冒泡为流水线失败，MUST NOT 让流水线干等到 `pipelineTimeoutMs` 才超时。

#### Scenario: 标题 LLM 失败则不发布、判失败
- **WHEN** `TitleCreator` 的 LLM 调用连续失败、重试用尽
- **THEN** 不写 `titleSelection`，`PublishExecutor` 不激活、不下发任何发布指令，本次流水线判 `failed`

#### Scenario: 红线反例——派生假标题顶替（禁止）
- **WHEN** 标题生成失败，有实现想用「正文首行切一段」当标题继续发布
- **THEN** 这违反「失败=发布失败、不造假标题」，MUST 被拒绝；正确行为是判失败、不发布

#### Scenario: 失败即时判定不挂死
- **WHEN** `TitleCreator` `abort`
- **THEN** 流水线即时收敛为 `failed`（与 `ContentCreator` 现有 `abort` 行为一致），MUST NOT 干等到 18 分钟 `pipelineTimeoutMs`

### Requirement: 发布严格接在标题就绪事件之后

`PublishExecutor` MUST 在「审批门结论 + 标题就绪」两个事件都满足后才激活：`watchKeys=['gateDecision','titleSelection']` 且 `waitAll:true`。由此发送飞书人审卡片时标题 MUST 已生成，审批卡标题栏 MUST 取自 `titleSelection.title`（真实标题），MUST NOT 在标题缺失时发出卡片或发布。

#### Scenario: 标题就绪才发布
- **WHEN** `gateDecision` 与 `titleSelection` 均写出
- **THEN** `PublishExecutor` 激活，先发飞书审批卡、人审通过后下发发布序列

#### Scenario: 审批卡显示真实标题
- **WHEN** `PublishExecutor` 发送飞书人审卡片
- **THEN** 卡片标题栏为 `titleSelection.title`（真正会发出的 ≤18 字标题），而非正文首行派生值；人工「通过」即认可该真实标题+正文+配图

#### Scenario: 标题缺失则审批卡不发、不发布
- **WHEN** `titleSelection` 因标题 `abort` 而从未写出
- **THEN** `PublishExecutor` 不激活，既不发审批卡也不发布（无「标题缺失」的卡片）

### Requirement: 标题长度收口云端一处且记录等于真实发布

标题长度 MUST 在云端**一处**收敛到 ≤18 可见字符，且为字形安全截断：MUST 用按 grapheme 的计数与边界回退（`title-clamp.ts` 的 `clampTitle`），超长时回退到最近词/标点边界、无边界则硬切到 18，**MUST NOT 返回空串**、MUST NOT 从汉字词或 emoji 代理对中间盲切。被收敛后的同一个标题值 MUST 同时用于：`publish_log` 写入、下发 edge 的 `fill_field(title)`、飞书审批卡、以及 `manual_review`/`abort` 状态记录——做到记录==下发==审批卡==真实发布。edge MUST NOT 对标题再做任何截断或策略处理，只原样填入云端下发的标题；edge 填入失败按真实结果如实回报。

#### Scenario: 字形安全截断、不返空
- **WHEN** 标题为 25 个连续汉字、无空格/标点边界
- **THEN** `clampTitle` 返回恰 18 个 grapheme 的非空标题，不从某个汉字中间或 emoji 中间切断

#### Scenario: 记录等于真实发布
- **WHEN** 一次发布成功
- **THEN** `publish_log.title`、下发 edge 的标题、飞书审批卡标题三者为同一个 ≤18 字字符串，等于平台上真正显示的标题

#### Scenario: 红线反例——记录与真发不一致（禁止）
- **WHEN** 有实现让云端存全长标题、靠 edge 盲切到 20 才发布
- **THEN** 这造成 `publish_log` 记录 ≠ 真实发布（失真红线），MUST 被拒绝；长度收口 MUST 发生在 DB 写入与下发之前

#### Scenario: edge 不做标题策略
- **WHEN** edge 收到 `fill_field(title)` 指令
- **THEN** edge 原样把云端标题填入发布页，不截断、不改写；若填入后置校验失败则回 `ok:false` 与真实 error，MUST NOT 自行裁剪标题去"修复"

### Requirement: 标题角色模型可后台独立配置且零回归回落

`TitleCreator` MUST 经按角色取模型通道调用（`roleLlm('publish:TitleCreator')` + `RoleConfigStore`），并在角色目录登记，使管理后台「角色配置页」可独立配置其文本模型与温度。未配置时 MUST 零回归回落全局默认模型（当前 qwen3.7-max），MUST NOT 因缺 `role_config` 行而 brick。

#### Scenario: 未配置回落全局
- **WHEN** `role_config` 无 `publish:TitleCreator` 行
- **THEN** `TitleCreator` 用全局默认模型/温度调用，行为零回归

#### Scenario: 后台独立配置生效
- **WHEN** 运营在「角色配置页」给 `publish:TitleCreator` 设一个模型/温度
- **THEN** 该角色后续调用用所配模型/温度，不影响其他角色
