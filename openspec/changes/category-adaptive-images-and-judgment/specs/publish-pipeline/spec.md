## ADDED Requirements

### Requirement: 内容质量评审随品类与人设自适应（不改放行闸与降级公式）

`QualityScorer` 的评审 SHALL 随本帖**内容品类**与账号**人设**自适应，MUST NOT 用单一「干货 / 信息密度」口味评判所有品类：干货类看信息量 / 实用性，情感 / 审美 / 生活类看共鸣 / 画面感 / 真实体验；「真实感」判据 SHALL 改为「是否贴合该账号人设声音」而非泛化真人腔。账号人设 SHALL 作为一等入参接入评审 prompt（从管线内已可达的 `soul` 取，无新增跨阶段 plumbing）。本要求 MUST NOT 改动既有诚实性约束：评审 LLM 失败时仍走降级公式 `qualityScore = round((1-aiScore)*70)`、MUST NOT 编造高分；MUST NOT 改动 `ApprovalGatekeeper` 的放行 / 人审 / 拒绝分支阈值（AC-PUB）。改评审 prompt 函数签名 SHALL 同步后台只读预览（`prompts-preview`）以保与线上同源。

#### Scenario: 情感类不因缺硬信息被压低
- **WHEN** 一篇情感 / 生活类笔记（共鸣强、无硬核数据）进入质量评审
- **THEN** 评审按该品类子标准（共鸣 / 画面感 / 真实体验）打分，MUST NOT 仅因「缺少具体数据 / 实用信息」而系统性压低其质量分

#### Scenario: 评审接人设声音
- **WHEN** 构造 `QualityScorer` 评审 prompt
- **THEN** prompt 含该账号人设（角色 / 语气 / 兴趣），「真实感」判据表述为「是否贴合该人设声音」

#### Scenario: 不动放行闸与降级公式
- **WHEN** 评审 LLM 失败，或审视 `ApprovalGatekeeper` 放行逻辑
- **THEN** `QualityScorer` 仍走 `round((1-aiScore)*70)` 降级、不造假分；`auto_publish` / `manual_review` / `retry` / `abort` 的阈值与分支未被本要求改动

### Requirement: 正文标点表达按品类分档且生成与后处理检测口径同步

正文表达约束（尤其感叹号上限）SHALL 按内容品类 / 人设分档，MUST NOT 对所有品类施加同一硬上限（生活 / 情感 / 美妆类可放宽、干货 / 克制类保持严）；反 AI 味的结构性约束（如排比套话）SHALL 跨品类保留。生成侧约束与后处理检测口径 SHALL **两侧同步**——`PostProcessor` 的感叹号 / 「过量感叹号」检测 MUST 接受同一品类 / 人设参数，使某品类在生成侧放宽后 MUST NOT 仍被后处理判为「过量」而被推向重写 / 人审。

#### Scenario: 生活类放宽感叹号且检测同步
- **WHEN** 一篇生活 / 情感类正文按放宽档写了数个感叹号
- **THEN** 生成 prompt 与 `PostProcessor` 检测使用同一放宽档；该正文 MUST NOT 因「过量感叹号」被判命中而推向 rewrite / manual

#### Scenario: 干货类仍保持克制
- **WHEN** 一篇干货 / 克制类正文
- **THEN** 感叹号上限仍取严格档，反 AI 味结构约束照常生效
