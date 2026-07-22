## ADDED Requirements

### Requirement: Account table exposes a unified configuration column
管理后台账号表 SHALL 使用“配置”作为账号级平台配置入口的唯一表头。平台列 MUST 只展示账号的平台事实，MUST NOT 再附着 Facebook 或其他平台的配置入口。

#### Scenario: Facebook account configuration is shown in the configuration column
- **WHEN** 运营查看包含 Facebook 账号的账号表
- **THEN** 该账号的既有 Facebook 配置入口显示在“配置”列，且平台单元格只显示 Facebook 平台标签

#### Scenario: Video Channels runtime control is shown in the configuration column
- **WHEN** 运营查看包含视频号账号的账号表
- **THEN** 该账号的既有运行控制入口显示在“配置”列，且表格不再显示“运行控制”表头

#### Scenario: Unsupported platform has an explicit empty state
- **WHEN** 账号平台没有账号级配置入口
- **THEN** “配置”列显示明确空态，系统 MUST NOT 展示其他平台的配置入口

### Requirement: Configuration entry consolidation preserves domain behavior
统一配置列 SHALL 只改变入口的表格位置与表头语义。视频号运行控制与 Facebook 配置 MUST 继续使用各自既有的加载、编辑、保存和错误处理流程。

#### Scenario: Operator opens a platform-specific configuration entry
- **WHEN** 运营从统一“配置”列打开视频号运行控制或 Facebook 配置
- **THEN** 系统打开该平台既有配置界面，并继续调用原有账号级接口和保存流程

#### Scenario: Read-only account table does not opt into configuration actions
- **WHEN** 其他页面以只读方式复用账号表且未提供配置 render prop
- **THEN** 表格 MUST NOT 增加“配置”列或任何可写配置入口
