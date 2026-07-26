## ADDED Requirements

### Requirement: 客户灵感库 SHALL 最小披露来源发布时间证据

客户鉴权域的精选列表与详情白名单 DTO SHALL 返回 `sourcePublishedAtText`、`sourcePublishedAt`、`sourcePublishedAtPrecision`、`sourcePublishedAtStatus` 和 `sourcePublishedAtObservedAt`，值均来自账号隔离后的精选行。接口 MUST NOT 为缺失字段生成回落时间，MUST NOT 因增加该字段而直出完整内部行或其它账号数据。

#### Scenario: 列表与详情返回同一来源时间

- **WHEN** 当前授权环境读取一条带已解析来源发布时间的灵感列表项和详情
- **THEN** 两个 DTO 返回一致的来源时间证据字段，仍只包含客户白名单字段

#### Scenario: 历史行字段诚实为空

- **WHEN** 当前账号的历史精选行没有来源发布时间证据
- **THEN** 客户 DTO 对应字段为空或省略，不以 `updatedAt` 填充

#### Scenario: 账号隔离不因时间字段减弱

- **WHEN** 客户请求另一账号的精选 id
- **THEN** 仍返回同形未找到响应，不泄漏其来源发布时间原文或标准时间
