## ADDED Requirements

### Requirement: 客户端批准动作可在同一版本闸内设置发布计划

客户端对 `pending_approval` 小红书稿件执行批准时 SHALL 可携带 `publishMode/publishTime`。Cloud MUST 以活会话账号校验稿件归属、比对客户端所见内容版本、按权威时刻校验发布计划；计划变化 MUST 经既有 `editDraft` 单写方法和内容版本 CAS 深合并同一 `publish_log.publish_metadata`，随后重读真实稿件并以更新后的内容版本写审批授权。任一账号、状态、版本、时间或 CAS 校验失败 MUST 整体拒绝，不得写批准、不得静默改成立即发布、不得部分修改。计划未变化 MUST NOT 无谓增加版本。旧客户端未提供新字段时 SHALL 沿用稿件当前发布计划。

#### Scenario: 批准时设置合法定时发布

- **WHEN** 客户对版本 v3 的待审小红书稿选择合法定时值并批准，且稿件当前为立即发布
- **THEN** Cloud 以 v3 CAS 把同一稿件改为 scheduled/目标时间、得到 v4，再以 v4 写批准授权并触发下发

#### Scenario: 批准时切回立即发布

- **WHEN** 客户把待审定时稿切为立即发布并批准
- **THEN** 同一 CAS 写入 `mode=immediate/publishTime=null`，保留其它元数据，审批签名绑定修改后的新版本

#### Scenario: 发布计划未变化不增版本

- **WHEN** 客户批准时提交的模式与时间等于草稿当前真态
- **THEN** Cloud 直接以当前版本授权，不执行空编辑、不增加内容版本

#### Scenario: 时间在批准时已失效

- **WHEN** 客户提交 scheduled 目标时间在 Cloud 权威校验时已不足未来 1 小时或超过 14 天
- **THEN** Cloud 返回时间拒因，稿件元数据和审批信号均不改变，绝不改成立即发布

#### Scenario: 版本冲突不部分批准

- **WHEN** 客户所见 v3 在批准前已被其它编辑更新为 v4
- **THEN** Cloud 返回 `version_stale` 与当前版本，不修改发布计划、不写审批授权

#### Scenario: 取消不修改发布计划

- **WHEN** 客户取消一条待审稿
- **THEN** Cloud 按既有取消语义写拒绝，忽略或拒绝任何发布计划字段，不编辑稿件元数据
