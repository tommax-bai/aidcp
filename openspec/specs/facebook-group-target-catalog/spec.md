# facebook-group-target-catalog Specification

## Purpose
TBD - created by archiving change facebook-group-target-filters. Update Purpose after archive.
## Requirements
### Requirement: Facebook group targets carry optional business filters
Facebook group targets SHALL support optional `region`, `park`, and `direction` metadata. None of the three fields is required to create or list a target. Existing targets without metadata SHALL remain valid.

#### Scenario: URL-only target remains valid
- **WHEN** an operator imports a Facebook group URL without region, park, or direction
- **THEN** the target is accepted and its metadata fields are stored as null

#### Scenario: Metadata target is returned to the console
- **WHEN** a target has region, park, and direction metadata
- **THEN** the group target list returns those metadata fields with the target row

### Requirement: Facebook group URLs are canonicalized before storage
Facebook group import SHALL canonicalize every accepted URL to `https://www.facebook.com/groups/<slug-or-id>` before storage and duplicate detection. Query strings, fragments, locale parameters, share tracking parameters, and deeper path suffixes after the group identifier MUST NOT be stored as part of the target key. Invalid or non-group Facebook URLs SHALL be rejected as invalid imports.

#### Scenario: Query parameters are discarded
- **WHEN** an operator imports `https://www.facebook.com/groups/322376783153364/?cft[0]=abc&tn=-UC`
- **THEN** the stored group URL is `https://www.facebook.com/groups/322376783153364`

#### Scenario: Deeper post path is reduced to the group
- **WHEN** an operator imports `https://m.facebook.com/groups/group-a/posts/123?ref=share`
- **THEN** the stored group URL is `https://www.facebook.com/groups/group-a`

### Requirement: Re-import enriches existing group metadata without changing assignment state
When an import item resolves to an existing canonical group URL, the catalog SHALL update the target's group name, region, park, direction, and import batch from the new import when those values are provided. It MUST NOT reset enabled state, priority, join gating, membership, assignment, or coverage state.

#### Scenario: Existing target receives metadata
- **WHEN** a previously URL-only group is re-imported with region `河南区域` and park `同文1工业区`
- **THEN** the existing target row has those metadata fields after import and any membership row for the group remains unchanged

### Requirement: Group target list supports optional region, park, and direction filters
The group target list SHALL accept optional exact-match filters for region, park, and direction. Omitting any filter SHALL leave that dimension unconstrained. Combining filters SHALL apply all provided filters together with existing status and enabled filters.

#### Scenario: Region-only filter
- **WHEN** the group target list is requested with `region=河南区域`
- **THEN** only targets whose region is `河南区域` are returned, regardless of park or direction

#### Scenario: Combined optional filters
- **WHEN** the group target list is requested with `region=北宁区域`, `park=周山工业区/VSIP 1`, and `direction=机械和电气`
- **THEN** only targets matching all three provided metadata values are returned

### Requirement: Filter facets expose stored regions, parks, and directions
The Facebook group target catalog SHALL expose filter facets derived from stored targets. Facets SHALL include regions with their known parks and a de-duplicated direction list. Null or empty metadata values MUST NOT appear as selectable facet values.

#### Scenario: Region facets include nested parks
- **WHEN** stored targets include region `河南区域` with parks `同文1工业区` and `同文2工业区`
- **THEN** the facets response includes `河南区域` with those two park options

#### Scenario: Empty metadata is omitted from facets
- **WHEN** stored targets include URL-only rows with null region, park, and direction
- **THEN** those null values are not returned as selectable facets

### Requirement: Facebook 群目标可关联多个账号分组

Facebook 群目标目录 SHALL 在保持 canonical group URL 单一事实行的同时，支持零个或多个适用账号分组标签。一个目标 MAY 同时映射多个分组；映射 MUST 独立于 region、park、direction、enabled、priority、join gating 和 membership 事实，修改范围不得复制目标行或重置这些字段。无任何分组映射的目标仍可管理和明确 URL 人工作业，但 MUST NOT 进入自动或裸 `--join` 候选池。

#### Scenario: 一个群属于多个账号分组
- **WHEN** 运营把同一 canonical group URL 的适用分组设为“华东组”和“招聘组”
- **THEN** 目录仍只有一个目标事实行并返回两个分组标签，两个分组的账号都可把它视为候选，但数据库全局群归属锁仍只允许一个账号最终认领

#### Scenario: 无范围目标不进入自动池
- **WHEN** 某启用目标没有任何账号分组映射
- **THEN** 它仍出现在群组管理目录并标记“未设置适用分组”，但任何账号自动加群和裸 `--join` 都不得认领它

### Requirement: 群目标目录支持账号分组过滤和批量范围真态

群目标列表 SHALL 返回每行完整账号分组标签集合，并接受可选精确账号分组过滤；群组管理面 SHALL 支持选中一个或多个目标后以一个显式分组集合替换其范围。范围写入 MUST 校验目标存在、标签规范化且为当前 Facebook 账号实际使用的分组，任一非法时整块拒绝；成功后 SHALL 返回数据库回读的完整映射真态。

#### Scenario: 按账号分组过滤
- **WHEN** 群列表以账号分组“华东组”过滤
- **THEN** 只返回范围集合包含“华东组”的目标，目标属于其它分组的标签仍在该行完整返回

#### Scenario: 批量替换范围整块成功
- **WHEN** 运营选择三个现有目标并把完整范围集合替换为“招聘组”和“销售组”
- **THEN** 三个目标均只保留这两个映射，接口返回三个目标的回读真态

#### Scenario: 非 Facebook 账号分组拒绝
- **WHEN** 范围集合包含一个当前只由非 Facebook 账号使用或不存在的标签
- **THEN** 整个范围写请求具名拒绝，任何选中目标的映射都不改变

