## ADDED Requirements

### Requirement: 待审草稿发布方式经既有乐观 CAS 单写编辑

待审草稿的 `publishMode/publishTime` 修改 MUST 经拥有 `publish_log` 的同一个 `editDraft` 单写方法和 `content_version` 乐观 CAS 完成，MUST NOT 新增裸 SQL 写口。写方法 SHALL 深合并 `publish_metadata.mode/publishTime` 并保留其它元数据；合法修改成功 MUST 使版本自增 1，非法时间、非待审状态或版本冲突 MUST 整体拒绝且不部分落库。

#### Scenario: 修改定时方式使旧授权失效
- **WHEN** 审核人在 v3 待审稿上选择合法定时并提交修改
- **THEN** 元数据写为 scheduled/目标时间、内容版本变为 v4，任何携 v3 的旧授权在下发闸被拒

#### Scenario: 切回立即发布清空时间
- **WHEN** 审核人把 scheduled 待审稿切回 immediate
- **THEN** 同一 CAS 写将 `mode='immediate'` 且 `publishTime=null`，其它元数据逐字保留

