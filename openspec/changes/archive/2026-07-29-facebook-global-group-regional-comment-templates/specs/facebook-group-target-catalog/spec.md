## MODIFIED Requirements

### Requirement: Facebook 群目标可关联多个账号分组

Facebook 群目标目录 SHALL 在保持 canonical group URL 单一事实行的同时，以显式 `accountScopeMode` 表达 `global|restricted` 范围。`global` 目标允许任意 Facebook 账号成为候选且 MUST NOT 依赖账号当前分组标签；`restricted` 目标 MAY 关联零个或多个真实账号分组标签，零映射继续表示未设置范围且 MUST NOT 进入自动或裸 `--join` 候选池。范围 MUST 独立于 region、park、direction、enabled、priority、join gating 和 membership 事实，修改范围不得复制目标行或重置这些字段。`global` 与非空标签集合 MUST NOT 同时成为有效写入真态。

#### Scenario: 一个受限群属于多个账号分组
- **WHEN** 运营把同一 canonical group URL 的范围设为 `restricted`，适用分组为“华东组”和“招聘组”
- **THEN** 目录仍只有一个目标事实行并返回两个分组标签，两个分组的账号都可把它视为候选，但数据库全局群归属锁仍只允许一个账号最终认领

#### Scenario: 全局群适用所有 Facebook 账号
- **WHEN** 某启用目标的范围为 `global`
- **THEN** 任意当前分组的 Facebook 账号以及未分组 Facebook 账号都可把它视为候选，但非 Facebook 账号、陈旧账号投影和其它既有闸仍不得放行

#### Scenario: 无范围目标不进入自动池
- **WHEN** 某启用目标范围为 `restricted` 且没有任何账号分组映射
- **THEN** 它仍出现在群组管理目录并标记“未设置适用分组”，但任何账号自动加群和裸 `--join` 都不得认领它

### Requirement: 群目标目录支持账号分组过滤和批量范围真态

群目标列表 SHALL 返回每行完整 `accountScopeMode` 与账号分组标签集合，并接受可选的显式范围模式或精确账号分组过滤。群组管理面 SHALL 支持选中一个或多个目标后把完整范围替换为 `global` 或 `restricted + labels`。范围写入 MUST 校验目标存在、模式与标签组合不矛盾、标签规范化且为当前 Facebook 账号实际使用的分组，任一非法时整块拒绝；成功后 SHALL 返回数据库回读的完整范围真态。旧客户端只提交 `accountGroupLabels` 时 MUST 按 `restricted` 解释。

#### Scenario: 筛选全局范围
- **WHEN** 群列表以范围模式 `global` 过滤
- **THEN** 只返回显式全局目标，不把受限空范围或普通账号分组目标混入

#### Scenario: 按账号分组过滤
- **WHEN** 群列表以账号分组“华东组”过滤
- **THEN** 只返回 `restricted` 且范围集合包含“华东组”的目标，目标属于其它分组的标签仍在该行完整返回

#### Scenario: 批量替换为全局范围
- **WHEN** 运营选择三个现有目标并把范围替换为 `global`
- **THEN** 三个目标均回读为全局且标签集合为空，既有 membership 与群目标业务字段不改变

#### Scenario: 全局与非空标签矛盾时拒绝
- **WHEN** 范围写请求同时提交 `global` 和一个或多个真实账号分组标签
- **THEN** 整个请求具名拒绝，任何选中目标的范围都不改变

#### Scenario: 非 Facebook 账号分组拒绝
- **WHEN** `restricted` 范围集合包含一个当前只由非 Facebook 账号使用或不存在的标签
- **THEN** 整个范围写请求具名拒绝，任何选中目标的映射都不改变

## ADDED Requirements

### Requirement: 变更生效时现存群目标一次性迁移为全局

版本化数据迁移 SHALL 在单个事务中把迁移开始时已经存在的全部 Facebook 群目标范围设为 `global`。为避免 DEV 迁移经共享 PostgreSQL 改变未升级 OL 旧代码的候选资格，迁移 SHALL 原样保留既有账号分组映射作为休眠兼容数据；新实现对 `global` 资格 MUST 忽略这些映射，后续显式范围写仍按正常规则清理或替换映射。迁移 MUST 更新范围审计信息并回读核验目标数及兼容映射逐行未变；MUST NOT 修改 membership、enabled、priority、join gating、region、park、direction 或其它群事实。迁移后的新目标 SHALL 继续使用安全默认 `restricted + empty`，除非导入请求显式选择其它范围。

#### Scenario: 全部现存目标迁移为全局
- **WHEN** 数据迁移开始时目录已有一批全局、受限多标签和未设置范围目标
- **THEN** 事务完成后这些现存目标全部为 `global`、范围标签为空，目标总数和 membership 事实不变

#### Scenario: 迁移失败不留下半完成范围
- **WHEN** 全局迁移在更新或核验阶段失败
- **THEN** 整个事务回滚，不得出现部分目标已全局而部分目标仍受限的状态

#### Scenario: 迁移后新导入不自动变全局
- **WHEN** 迁移完成后导入新群且请求未携带范围字段
- **THEN** 新目标保持 `restricted + empty`，不会因历史批量迁移而自动进入所有账号候选池
