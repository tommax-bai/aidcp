## MODIFIED Requirements

### Requirement: 排期评论在 edge 接管失败前如实报告未开始

排期评论在 prepare 或 commit 阶段**未能取得 edge 租约**时，SHALL 产出 `not_started` 的非成功结果。该判定 MUST **与具体租约错误码无关**：凡「租约未取得、任务体未执行、零条评论业务命令下发」的失败，一律归为 `not_started`——包括但不限于 acquire 超时、edge 离线、连接断开、浏览器控制面不可用（`edge_unhealthy`）、浏览器停泊唤不醒（`browser_wake_failed`）。实现 MUST NOT 依赖一张逐码枚举的白名单，因为新增租约错误码时类型检查不会提示遗漏（向联合类型增补成员是变宽而非变窄）；判定 SHALL 以「任务体是否已经执行过」为准，仅把**释放阶段**的失败（`release_timeout`，发生在评论可能已真实发出之后）排除在 `not_started` 之外。

对应飞书结果卡 MUST 明确本次未搜索、未选中笔记、未发布评论，并给出可审计的接管失败原因；MUST NOT 使用“已选中笔记”“发布未确认”等仅适用于已进入候选或提交阶段的措辞。该结果 MUST NOT 被记录为已评论、已发布或候选已选中。

接管失败原因 SHALL 按**处置语义**分档呈现，MUST NOT 把语义相反的失败混为一句话：浏览器控制面不可用（边端在线、连接正常，但浏览器驱不动）MUST 与边端离线／失联可辨识区分；浏览器停泊唤不醒 MUST 标明为可恢复。

`not_started` 结果 MUST 触发排期小时格回流（归还本小时名额、打开小时内重试窗），MUST NOT 因为被误分类为阶段性失败而使该账号本小时的排期名额零动作白烧。

#### Scenario: prepare acquire 超时

- **WHEN** 自动排期评论在搜索候选前等待 edge acquire 超时
- **THEN** 结果卡显示浏览器未能接管且本次未搜索、未选中、未发布，零条评论业务命令被下发

#### Scenario: 浏览器控制面不可用

- **WHEN** 自动排期评论申请租约时 edge 回 `cdp_unhealthy`（云端得到 `edge_unhealthy`）
- **THEN** 结果为 `not_started`，结果卡明确本次未搜索、未选中、未发布，且原因标明为「边端在线但浏览器控制面不可用」而非「边端离线」
- **AND** 排期小时格被归还，MUST NOT 白烧该账号本小时的评论名额

#### Scenario: 新增租约错误码不需要改判定

- **WHEN** 未来新增一个发生在租约取得阶段的错误码，且未在任何白名单里登记
- **THEN** 该失败仍被归为 `not_started`（默认偏向诚实），MUST NOT 因为「不认识这个码」而被写成发布阶段失败

#### Scenario: 释放阶段失败不得改写为未开始

- **WHEN** 评论任务体已执行完毕，仅在释放租约时超时（`release_timeout`）
- **THEN** 该失败 MUST NOT 被归为 `not_started`（评论可能已真实发出），MUST NOT 因此归还小时格并触发重复评论

#### Scenario: 已进入流程后的失败保持阶段语义

- **WHEN** 排期评论已经取得租约并在候选选择、撰写或提交阶段失败
- **THEN** 系统保留对应阶段的真实失败说明，不把该失败改写成 `not_started`
