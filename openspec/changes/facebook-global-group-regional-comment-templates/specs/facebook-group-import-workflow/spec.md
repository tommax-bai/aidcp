## MODIFIED Requirements

### Requirement: 群组导入可选应用公共账号分组范围且缺省不清空

单条添加和文件导入 SHALL 提供可选公共适用范围，并允许运营显式选择 `global` 或 `restricted + accountGroupLabels`，把该范围应用到本次提交所有导入目标。请求未携带任何范围字段时，已存在目标的范围 MUST 保持不变，新目标 SHALL 保持 `restricted + empty`；请求显式携带范围时，成功导入/更新的目标 SHALL 用该完整范围替换原值。`global` 与非空账号分组标签同时出现 MUST 整块拒绝。范围校验失败 MUST 在写目标、元数据和映射前拒绝该提交，不能出现半成功。

#### Scenario: 重复导入未选择范围时保留映射
- **WHEN** 已映射“华东组”的受限目标被再次导入且请求没有范围字段
- **THEN** 目标元数据按既有规则更新，而 `restricted + 华东组` 范围保持不变

#### Scenario: 导入统一应用全局范围
- **WHEN** 运营选择“全局分组”后导入一个 CSV
- **THEN** 本次成功导入或更新的每个目标都回读为 `global` 且标签集合为空

#### Scenario: 文件导入统一应用多个分组
- **WHEN** 运营选择受限模式及“华东组”和“招聘组”后导入一个 CSV
- **THEN** 本次成功导入或更新的每个目标都回读为 `restricted` 并同时映射这两个分组

#### Scenario: 显式受限空集合清除范围
- **WHEN** 运营明确提交 `restricted` 且账号分组集合为空
- **THEN** 成功目标的范围被清空并诚实标记为不会被自动或裸 `--join` 认领

#### Scenario: 矛盾范围不产生元数据半写
- **WHEN** 导入请求同时提交 `global` 和非空账号分组集合
- **THEN** 整个导入具名拒绝，群元数据、范围与 membership 均不改变
