## MODIFIED Requirements

### Requirement: Facebook 群组面板 API 暴露账号分组范围读模型

Facebook 群组列表 SHALL 为每个目标返回完整 `accountScopeMode` 和 `accountGroupLabels`，接受可选显式范围模式或精确账号分组过滤；facets 或等价只读端点 SHALL 返回当前 Facebook 账号实际使用的可选分组、全局目标计数及受限空范围目标计数。导入和批量范围 API SHALL 接受 `global` 或 `restricted + accountGroupLabels`，并让“未提供范围”“显式全局”“显式受限空集合”的语义可区分。`global` 与非空标签、非法目标或非法 Facebook 分组标签 MUST 使整个请求拒绝；成功写入 SHALL 返回数据库回读真态。既有 URL-only、元数据导入和 labels-only 旧请求继续有效，labels-only 按 restricted 解释。

#### Scenario: 列表区分全局和未设置范围
- **WHEN** 目录同时含 global 目标、restricted 多标签目标和 restricted 空范围目标
- **THEN** API 为每行返回可区分的范围模式和标签，并返回对应 facets 计数

#### Scenario: 批量全局写返回真态
- **WHEN** Console 把一批现有目标范围替换为 global
- **THEN** API 整块校验并写入后返回每个目标 `accountScopeMode=global` 且标签为空的数据库真态

#### Scenario: 旧 labels-only 写保持兼容
- **WHEN** 旧客户端只提交 `accountGroupLabels=["华东组"]`
- **THEN** API 按 `restricted` 范围处理，不把该请求解释为 global

## ADDED Requirements

### Requirement: Facebook 群组面板 API 管理区域通用评论模板

Panel API SHALL 提供区域通用评论模板目录读取及单区域完整模板集合替换写。读取 SHALL 返回区域、完整模板集合、更新时间和更新人；写入 SHALL 校验区域非空且当前存在于群目标目录、模板集合类型/数量/长度合法，并在数据库成功后返回回读真态。非法请求 MUST 整块拒绝，不得只保存部分模板。该接口 MUST 经由 automation 配置权威写入，不得在 API 组合根形成第二写者。

#### Scenario: 读取区域模板目录
- **WHEN** Console 打开 Facebook 群组配置
- **THEN** API 返回所有已配置区域的通用模板真态且不包含账号私有模板

#### Scenario: 替换一个区域的完整模板集合
- **WHEN** 运营为一个现有群区域提交两条合法模板
- **THEN** API 经权威写入并返回该区域恰好两条模板及数据库更新时间

#### Scenario: 非法模板写不产生部分成功
- **WHEN** 同一写请求中任一模板类型错误、超长或区域不存在
- **THEN** API 具名拒绝，原区域模板集合保持不变
