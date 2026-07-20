## ADDED Requirements

### Requirement: 客户端人设视图只呈现当前真实人设并复用权威单写

面向客户的环境级人设读取 SHALL 仅在账号存在有效 `persona_config` 时返回当前 soul YAML；同时 SHALL 由 Cloud 解析并返回有界的人设摘要，包括身份名、定位、背景、语气、发言语言、兴趣方向、搜索种子与结构化点赞倾向。未绑定账号 MUST 返回明确 `missing` 且 persona 为空，MUST NOT 把后台编辑器使用的打包起点模板或任何示例人设冒充为当前人设。

客户确认更新 SHALL 复用与 Console 相同的人设单写通道和 soul 校验，写库成功后才刷新内存镜像并触发账号热加载；响应 SHALL 为写后真态，MUST NOT 本地或服务端乐观判成功。客户视图 MUST NOT 暴露内部 `updatedBy` 或账号键。

#### Scenario: 已绑定账号返回可读摘要与完整定义

- **WHEN** 客户读取一个已有合法账号人设的授权环境
- **THEN** Cloud 返回当前 soul YAML、由同一份 soul 解析出的有界摘要和 `updatedAt`
- **AND** 客户端无需复制 soul 解析器即可展示当前人设

#### Scenario: 未绑定账号不展示模板假态

- **WHEN** 授权环境已绑定账号但该账号没有人设行
- **THEN** 客户视图明确返回 `missing` 且不返回打包默认/起点模板作为当前人设

#### Scenario: 客户更新后运行链即时使用新人设

- **WHEN** 客户在停止环境中确认保存一份合法新人设
- **THEN** 写入成功后后续浏览与发布在账号再次运行时直接读取新人设，无需重启 Cloud
- **AND** 保存回执只声明人设已更新，MUST NOT 声称浏览器或首作已经启动
