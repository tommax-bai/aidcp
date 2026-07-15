## ADDED Requirements

### Requirement: 搜索提交 MUST 用真实用户手势，未确认跳转 MUST 有界重试

边端在搜索结果页采卡**之前**的「提交搜索」这一步，MUST 使用**真实用户手势**驱动小红书搜索框（尤其已灰度 AI 搜索、搜索框为 `textarea[name="aiSearchTextarea"]`、结果落 `/search_result_ai` 的账号——其「回车导航」不响应纯程序化聚焦）：

- **聚焦 MUST 派发真实指针点击**（对可见搜索框坐标发 `Input.dispatchMouseEvent` 按下+抬起），MUST NOT 仅用程序化 `el.focus()` 聚焦即提交。取不到可见搜索框坐标时 MAY 回退程序化聚焦（诚实降级），MUST NOT 因此静默假成功。
- **回车 MUST 携带字符文本**（`text:'\r'`，产生真实 `keypress` 形态），MUST NOT 只发不带 text 的裸 `keydown`（裸回车在 AI 搜索框上不触发导航）。
- 输入完成到回车之间 MUST 留一个**停顿地板**，让搜索框内部状态就绪，MUST NOT 输入后立即回车导致提交被忽略。
- 首次回车在有界窗口内**未确认跳转到结果页**时，MUST **有界重试回车**（受尝试上限约束），MUST NOT 把「点击一个可能不可见（0×0）的提交按钮」当作唯一或必需兜底；提交按钮点击**仅在其确可见时** MAY 作为附加尝试。
- 所有提交尝试用尽仍未确认到达结果页时，MUST 走既有诚实失败契约（以采卡时刻实时 URL 判定，回 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`，MUST NOT 采/报当前页 feed）。本要求是既有「搜索采卡前 MUST 确认已到达搜索结果页」契约的**提交侧补全**：既有契约保证「到不了不撒谎」，本要求保证「用对手势真的到得了」。

此要求 MUST 同时覆盖 `/search_result` 与 `/search_result_ai` 两种结果页；两者的 URL 判据、关键词（含双重编码）归一、卡片提取沿用现状、不因页型分叉。

#### Scenario: AI 搜索框——真实点击聚焦 + 带文本回车 → 跳转成功
- **WHEN** 边端在 AI 搜索账号上提交搜索
- **THEN** MUST 先对可见搜索框派发真实指针点击聚焦，逐字输入关键词
- **AND** MUST 在输入后留停顿地板再派发**携带 `text:'\r'`** 的回车
- **AND** 以采卡时刻实时 URL 确认到达 `/search_result` 或 `/search_result_ai` 后照常采卡上报

#### Scenario: 首次回车未跳转 → 有界重试回车
- **WHEN** 边端派发回车后在有界窗口内实时 URL 仍非结果页
- **THEN** MUST 再次派发回车（受尝试上限约束），MUST NOT 仅点一个不可见的提交按钮就放弃
- **AND** 若在重试内确认跳转，则照常采卡；全部尝试用尽仍未跳转，MUST 回 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}` 且不采/报当前页

#### Scenario: 纯程序化聚焦 / 裸回车 / 仅点不可见按钮 → 视为违规
- **WHEN** 有实现仅用程序化 `el.focus()` 聚焦、或发不带字符文本的裸回车、或仅依赖点击一个不可见提交按钮来提交搜索
- **THEN** MUST 视为不满足本要求（AI 搜索框上这些方式不可靠、会造成大面积 `not_on_search_page` 假阴性）
