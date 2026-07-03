## ADDED Requirements

### Requirement: 内容排期评论字段写入与发帖字段严格同构

内容排期写通道（`PUT /api/content-schedule/:accountId`）SHALL 新增 `commentEnabled`（布尔）与 `commentDailyCap`（0..50 整数）两字段，校验与既有发帖字段严格同构：非法值（类型错 / 越界 / 非整数）SHALL 整块拒、绝不部分落库；写后 SHALL 回读真态；未配 / 默认一律 fail-closed（评论不自动）。写仍只经内容排期存储的一等单写方法，MUST NOT raw UPDATE、MUST NOT 乐观假成功。

#### Scenario: 评论字段合法写回读真态
- **WHEN** 运营为某账号打开自动评论并设日上限 2
- **THEN** UPSERT 经单写方法完成，接口返回回读的真实行（commentEnabled=true、commentDailyCap=2）

#### Scenario: 非法评论上限整块拒
- **WHEN** 提交 `commentDailyCap` 为 -1、1.5 或 51
- **THEN** 整块拒绝、绝不部分落库，拒绝与成功可区分呈现
