## ADDED Requirements

### Requirement: 排期评论在 edge 接管失败前如实报告未开始

排期评论在 prepare 或 commit 租约尚未取得时发生 edge acquire timeout、edge 离线或连接断开，SHALL 产出 `not_started` 的非成功结果。对应飞书结果卡 MUST 明确本次未搜索、未选中笔记、未发布评论，并给出可审计的接管失败原因；MUST NOT 使用“已选中笔记”“发布未确认”等仅适用于已进入候选或提交阶段的措辞。该结果 MUST NOT 被记录为已评论、已发布或候选已选中。

#### Scenario: prepare acquire 超时
- **WHEN** 自动排期评论在搜索候选前等待 edge acquire 超时
- **THEN** 结果卡显示浏览器未能接管且本次未搜索、未选中、未发布，零条评论业务命令被下发

#### Scenario: 已进入流程后的失败保持阶段语义
- **WHEN** 排期评论已经取得租约并在候选选择、撰写或提交阶段失败
- **THEN** 系统保留对应阶段的真实失败说明，不把该失败改写成 `not_started`
