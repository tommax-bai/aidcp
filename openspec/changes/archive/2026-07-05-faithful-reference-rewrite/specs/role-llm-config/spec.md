# role-llm-config Specification Delta

## MODIFIED Requirements

### Requirement: 角色目录白名单暴露，区分模型类型，遗留与纯规则角色不列

系统 SHALL 提供角色目录，**只列出现役且真正调用大模型的角色**，每项标注 `roleId`（带 `browse:` / `publish:` 前缀防撞键）、显示名、所属组、`llmKind`（`text` / `image` / `none`）与是否可调温度。纯规则角色与 v1 遗留路径角色 MUST NOT 出现在目录中。温度 MUST 仅对生成 / 改写类角色开放。

保真参照洗稿新增的发布侧文本角色 SHALL 进入同一角色目录并可配置模型：`publish:ReferenceAnalyzer`、`publish:FaithfulRewritePlanner`、`publish:FaithfulDraftWriter`、`publish:FidelityAuditor`。其中 `FaithfulDraftWriter` 为生成/改写类，可开放温度；分析、规划、审核类强调确定性结构化输出，MUST NOT 开放温度。

#### Scenario: 目录只含现役 LLM 角色

- **WHEN** 请求 `GET /api/roles`
- **THEN** 返回的角色均为现役且 `llmKind !== 'none'`，纯规则角色与 v1 遗留角色不在其中

#### Scenario: 保真洗稿角色可配置

- **WHEN** 打开管理后台角色配置页
- **THEN** 能看到四个保真参照洗稿角色，并能按角色配置其文本模型；只有 `FaithfulDraftWriter` 渲染温度输入

#### Scenario: 判定类角色不开放温度

- **WHEN** 目录中一个判定/审核类角色（如 `ReferenceAnalyzer` 或 `FidelityAuditor`）被读取
- **THEN** 其 `tunable.temperature` 为 false，前端据此不渲染温度输入

