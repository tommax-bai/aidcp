## MODIFIED Requirements

### Requirement: 当前笔记触发的自动联系评论复用当前上下文

当自动联系评论由自治浏览中的当前笔记触发（例如热帖引流线索在 `note.detail.arrived` 后经 `quality.pass` 命中）时，系统 SHALL 复用该当前 `note.detail` 上下文直接进入撰写/人审/发布流程，MUST NOT 再按标题搜索定位，MUST NOT 在当前上下文不可用时评论搜索到的相似笔记。该路径 MAY best-effort 继续采集当前详情页现场评论；采集失败不等于搜索兜底。后台或外部指定的非当前目标 MAY 继续使用标题搜索定位，但仍必须精确匹配目标 `noteId`。

自动联系评论的共用 comment 风险配额 SHALL 只在最终执行结果确认为 `commented` 后消费；任务触发成功但最终 `note_not_found`、`read_failed`、`compose_skipped`、`post_failed` 或其他未产出状态 MUST NOT 消费 comment 配额。联系评论尝试审计/子上限 MAY 在触发成功时记录，用于避免反复推审。

#### Scenario: 当前笔记触发 → 不搜索，直接评论当前笔记
- **WHEN** 热帖线索由当前笔记 `noteId=N` 的 `note.detail` 与质量通过事件触发
- **THEN** 任务 MUST 使用该 `note.detail` 作为评论目标，MUST NOT 下发 `xiaohongshu.search.execute` 或按标题搜索
- **AND** 评论发布目标 MUST 仍为 `noteId=N`

#### Scenario: 当前详情错配或丢失 → 不搜索兜底
- **WHEN** 当前详情 `noteId` 与目标 `noteId` 不一致，或当前笔记上下文不可用
- **THEN** 任务 MUST 诚实失败/未产出，MUST NOT 改按标题搜索并评论相似结果

#### Scenario: 未产出不消费 comment 风险配额
- **WHEN** 自动联系评论已触发但最终没有 `commented`
- **THEN** MUST NOT 记录共用 comment 风险配额消耗，但 MAY 记录一次联系评论尝试审计

#### Scenario: 外部指定目标仍可搜索但必须精确命中
- **WHEN** 后台/飞书入口只提供目标 noteId/title 且没有当前详情上下文
- **THEN** MAY 使用标题搜索定位；搜索结果中没有精确目标 noteId 时 MUST 不评相似笔记
