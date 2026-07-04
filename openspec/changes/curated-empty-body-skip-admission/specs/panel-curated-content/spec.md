# panel-curated-content Delta

## MODIFIED Requirements

### Requirement: 按正文为空清理壳行——非按纳入原因

面板 SHALL 保留「清理空正文壳行」的接口，谓词为正文为空（NULL 或空串）且按 `account_id` 约束，MUST NOT 以「按纳入原因批量删除」实现。该能力主要用于清理历史遗留数据或异常恢复；正常写入路径中，自有收藏缺少非空正文时 MUST NOT 再补建新的空正文精选壳行。清理 MUST 返回真实清理条数，界面 MUST 呈现真实条数（可能因并发写入或历史数据变化而与事前预览不同），MUST NOT 回显预览数充当结果。

#### Scenario: 只清历史空正文壳行

- **WHEN** 带账号 A 执行清理空正文壳行
- **THEN** 仅删除账号 A 中正文为空（NULL 或空串）的历史/异常行，所有带正文的行（含高共鸣观测行）保留

#### Scenario: 清理回真实条数

- **WHEN** 清理实际删除了 N 行
- **THEN** 接口返回 N，界面呈现真实的 N，而非事前 facets 预览的估计数

#### Scenario: 清理不跨账号

- **WHEN** 带账号 A 执行清理
- **THEN** 其他账号的空正文壳行不受影响
