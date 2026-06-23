## ADDED Requirements

### Requirement: 全局 textModel 即「默认模型」，不新造冗余全局层

后台 SHALL 把既有的全局文本模型名（`model_config.text_model`，经 `PUT /api/config/model` 可改、热加载生效）在文案上**正名为「默认模型」**，使其在角色 / 分类配置语境中表意清晰——它是模型解析优先级链**末端的全局默认**（角色与分类「回落到默认」即回落到它）。本要求为**纯正名**：系统 MUST NOT 为此新增任何第二个全局模型层级、新表或新写接口，既有 `model_config` 单行存储、读写接口与热加载行为 MUST 保持不变（YAGNI，避免冗余层）。

#### Scenario: 默认模型即既有全局 textModel
- **WHEN** 在后台查看「默认模型」
- **THEN** 其值与 `GET /api/config/model` 返回的全局 `textModel` 一致，改它即改全局默认（无独立的第二全局层）

#### Scenario: 正名不改既有存储与行为
- **WHEN** 经正名后的「默认模型」入口修改全局文本模型名
- **THEN** 仍写 `model_config` 单行、仍 `PUT /api/config/model`、仍无需重启热加载生效，行为与正名前逐字一致

#### Scenario: 角色与分类回落指向默认模型
- **WHEN** 某角色无 per-role 覆盖、其分类也无默认模型
- **THEN** 其生效模型回落到「默认模型」（即全局 `textModel`），后台「生效来源」标注为继承默认
