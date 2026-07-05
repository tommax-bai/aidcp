# publish-pipeline Specification Delta

## ADDED Requirements

### Requirement: 参照洗稿走保真专用角色链后再进入既有发布下游

当 `TriggerInput.generateInput.referenceNote` 存在时，发布管线 SHALL 走参照专用保真角色链，而不是常规自由创作角色链。常规 `ContentScout` 和 `ContentCreator` MUST NOT 在参照路径产出选题/正文；参照路径 SHALL 由 `ReferenceAnalyzer`、`FaithfulRewritePlanner`、`FaithfulDraftWriter`、`FidelityAuditor` 四个 LLM 角色完成，且只有 `FidelityAuditor` 判定通过后才能写入标准 `createdContent` 字段。`createdContent` 写入后，既有配图、去 AI 味、质量评分、标题、话题、元数据、人审和下发链路 SHALL 原样复用。

四个保真角色职责如下：

- `publish:ReferenceAnalyzer`：抽取原稿主旨、结构、事实/数据/人物/时间线、核心论点和禁止新增清单。
- `publish:FaithfulRewritePlanner`：生成段落级改写计划，明确每段保留点、可改表达和不可新增内容。
- `publish:FaithfulDraftWriter`：按计划写成小红书正文草稿，只写 `faithfulDraft`，MUST NOT 直接写 `createdContent`。
- `publish:FidelityAuditor`：对比参照原文与草稿，检查事实覆盖、未授权新增、视角/身份漂移、结构偏离和近似照抄；通过才写 `createdContent`，失败 MUST 中止管线。

#### Scenario: 参照路径旁路常规创作

- **WHEN** `trigger.generateInput.referenceNote` 非空
- **THEN** `ContentScout` / `ContentCreator` 不产出常规 `scoutDecision` / `createdContent`，由保真角色链产出候选正文

#### Scenario: 审核通过后才进入下游

- **WHEN** `FidelityAuditor` 判定草稿忠实且非近似照抄
- **THEN** 其将草稿转换为 `createdContent`，下游既有配图 / 标题 / 话题 / 人审 / 发布链继续运行

#### Scenario: 审核失败中止

- **WHEN** `FidelityAuditor` 发现草稿新增原稿没有的事实、虚构个人经历、改变原作者身份视角、遗漏关键结论或近似照抄
- **THEN** 该角色 MUST 写 `pipelineAbort` 并使本次发布失败，不得落待审草稿

#### Scenario: 常规发布不受影响

- **WHEN** 普通 `/publish` 或自动发布触发且无 `referenceNote`
- **THEN** 仍走既有 `ContentScout` → `ContentCreator` 常规创作路径，保真角色链不激活

### Requirement: 保真洗稿禁止未授权新增事实

参照保真改写产物 SHALL 只使用参照原文中存在的信息以及账号人设允许的表达风格。系统 MUST 禁止新增参照原文未出现的测试结果、百分比数据、部署经验、身份背书、时间线、人物关系、外部结论或案例；若需要补背景，只能使用泛化过渡句，不得构成新的事实主张。FidelityAuditor MUST 将未授权新增事实判为失败。

#### Scenario: 禁止虚构实测数据

- **WHEN** 原文未提供「我方实测延迟降低 58%」等数据
- **THEN** 保真成稿不得新增该数据；若新增则审核失败

#### Scenario: 保留原稿身份边界

- **WHEN** 原文由项目早期成员/committer 复盘项目史
- **THEN** 成稿不得改写成「我作为使用者刚接入试了试」的身份视角，除非原文明确给出该视角

