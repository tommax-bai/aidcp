## RENAMED Requirements

- FROM: `### Requirement: 定向评论两型——内容评论与带群评论共用撰写链`
- TO: `### Requirement: 定向评论两型——内容评论与联系评论共用撰写链`

## MODIFIED Requirements

### Requirement: 定向评论两型——内容评论与联系评论共用撰写链

内容评论 SHALL 复用既有按需评论撰写链（读笔记现场与在场评论→人设撰写→去 AI 味→人审）。联系评论 SHALL 在相同撰写链之上追加该账号配置的联系方式（审核卡展示合并后最终文本，审=发；边端以既有整段插入方式追加）。两型的评论正文均 SHALL 基于笔记信息自动生成，MUST NOT 要求额外人工文案输入。账号未配置联系方式时联系评论 MUST 触发即以 contact_info_missing 拒绝（fail-closed），MUST NOT 退化为内容评论静默发出。

#### Scenario: 内容评论走既有撰写与人审
- **WHEN** 触发内容评论且目标定位命中
- **THEN** 评论正文由既有撰写链基于笔记现场自动生成，经人审通过后发布

#### Scenario: 联系评论追加联系方式且审=发
- **WHEN** 触发联系评论且账号已配置联系方式
- **THEN** 审核卡展示「正文+联系方式」合并文本，审核通过后按同一合并文本发布

#### Scenario: 未配联系方式触发即诚实拒绝
- **WHEN** 对未配置联系方式的账号触发联系评论
- **THEN** 触发即以 contact_info_missing 拒绝，MUST NOT 降级为内容评论发出
