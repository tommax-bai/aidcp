## ADDED Requirements

### Requirement: 内容投影与待审详情增量呈现平台原生定时信息

`GET /api/content/published` SHALL 在既有 item 上增量返回 `platform`、`publishMode`、`publishTime`、`scheduledAt` 与 `scheduledPlatformId`，历史行缺值时 null-safe。控制台待审详情 SHALL 在标题、正文、话题/其它稿件字段之后、批准动作之前提供“立即发布 / 定时发布”选择；选择定时时显示北京时间输入与 1 小时至 14 天约束。内部定时 id 只可作诊断文本，MUST NOT 渲染为公开链接。

#### Scenario: 待审详情编辑定时时间
- **WHEN** 小红书待审 item 的 `publishMode='scheduled'`
- **THEN** 控制台回显目标北京时间，时间或模式变化计入未保存改动并随 `modify_candidate` 提交

#### Scenario: 定时排队状态诚实展示
- **WHEN** item 状态为 `scheduled` 且尚无 `postUrl`
- **THEN** 控制台显示“定时发布，待公开确认”及目标时间，不显示“已发布”或可点击的伪链接

