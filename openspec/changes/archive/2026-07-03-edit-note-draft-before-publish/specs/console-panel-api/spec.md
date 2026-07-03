## ADDED Requirements

### Requirement: 待审草稿编辑端点（JWT 守护、依赖缺失非致命、拒因映射 HTTP）

面板层 SHALL 暴露 `PUT /api/publish/:recordId/draft` 用于就地编辑待审正文草稿的标题 / 正文 / 可见范围 / 话题。该端点 MUST 落在既有 JWT 鉴权闸之下（以 JWT 主体作编辑者审计），MUST 在其依赖的草稿写对象缺失时返回 503（非致命、绝不崩塌关键闭环），MUST 对请求体做类型校验，并 MUST 把拥有者对象返回的可区分拒因映射为可区分 HTTP 语义（`not_found` → 404；`version_conflict` / `already_decided` / `not_pending` → 409；`invalid_title` / 非法字段 → 400；缺可见范围 → 422；成功 → 200 携写回后的 `recordId` / `contentVersion` / 标题 / 正文 / 元数据）。该端点 MUST NOT 发裸 SQL，一切写经拥有者对象。

#### Scenario: 编辑成功回写真态
- **WHEN** 已鉴权运营 PUT 合法的标题 / 正文 / 可见范围 / 话题到一条待审草稿
- **THEN** 端点经拥有者对象单写、返回 200 及写回后的 `contentVersion` 与字段真态

#### Scenario: 依赖缺失非致命
- **WHEN** 草稿写对象未注入
- **THEN** 端点返回 503 而非崩塌，其余面板接口与关键闭环不受影响

#### Scenario: 拒因映射可区分 HTTP
- **WHEN** 编辑因版本冲突 / 授权在途 / 非待审 / 非法标题 / 缺可见范围被拒
- **THEN** 端点分别返回 409 / 409 / 409 / 400 / 422，前端据码回不同文案，绝不混淆

### Requirement: 已发布投影增量带出内容版本号

只读聚合接口 `GET /api/content/published` SHALL 在既有投影上**增量**带出 `content_version`，供前端渲染草稿生命周期标签并快照「人所见的版本」以随授权携带。该扩展 MUST 为加性——MUST NOT fork 抽屉或另起端点、MUST NOT 改动既有字段语义，与已归档的发布历史 item 形状协调。

#### Scenario: 投影含版本号
- **WHEN** 控制台拉取已发布 / 待审历史
- **THEN** 每条 item 额外带 `content_version`，其余既有字段语义不变

#### Scenario: 加性不 fork
- **WHEN** 本能力扩展投影
- **THEN** 复用同一端点与 item 形状（仅新增字段），不新建并行端点、不 fork 只读抽屉
