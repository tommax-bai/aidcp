# interaction-comment-capture-fidelity Specification

## Purpose
TBD - created by archiving change fix-interaction-and-comment-capture. Update Purpose after archive.
## Requirements
### Requirement: 点赞/收藏定位前等待互动栏渲染并容纳布局变体

执行端点赞/收藏 MUST 在定位互动栏前做有界等待互动栏渲染，且定位与后置校验的互动栏选择器 MUST 同时容纳 `.interactions.engage-bar` 与仅 `.engage-bar` 两种布局；仍找不到时 MUST 如实回报 `no-bar`（绝不假成功）。

#### Scenario: 互动栏晚渲染

- **WHEN** 命令下发瞬间互动栏尚未挂上（AI 总结流式重排 / 卡片回收中）
- **THEN** 执行端先有界等待互动栏出现再定位，避免在渲染完成前误报按钮缺失

#### Scenario: 互动栏为布局变体（仅 `.engage-bar`）

- **WHEN** 当前笔记的互动栏只带 `.engage-bar`、不带复合的 `.interactions.engage-bar`
- **THEN** 执行端仍能定位到点赞/收藏按钮并点击，不因复合选择器不命中而 `no-bar`

#### Scenario: 真的没有互动栏

- **WHEN** 有界等待超时后互动栏仍不存在
- **THEN** 回报 `ok:false reason=no-bar`，不点击、不假成功

### Requirement: 点赞/收藏可重试失败由云端有界重试，且不发兜底滚动

执行端回报**可重试**失败（点击后状态未翻转 / 互动栏一时缺失）时，云端 MUST 原地有界重试（每 note+action 至多 1 次），并 MUST NOT 对 like/collect 失败发兜底滚动（避免把详情页滚走）；**不可重试**失败（验证码阻断 / 已点过 / 无按钮）MUST 诚实终止、不重试。

#### Scenario: 点了没生效

- **WHEN** like/collect 回报 `state_unchanged`（或 `btn_no-bar` / `btn_no-btn`）且该 note+action 尚未重试
- **THEN** 云端从在途去重键回捞 noteId、原地重发一次；不发兜底滚动

#### Scenario: 验证码阻断

- **WHEN** like/collect 回报 `blocked_by_captcha`
- **THEN** 云端不重试，诚实终止该篇互动

#### Scenario: 重试用尽仍失败

- **WHEN** 一次重试后仍失败
- **THEN** 诚实结束该篇互动（不假成功、不无限重试）

### Requirement: 点赞/收藏会话预算按真成功回执扣减

点赞/收藏会话预算 MUST 在 `action.completed{ok:true}` 时扣减（与 follow/comment 同口径），MUST NOT 在下发时乐观扣减；失败或未达 MUST NOT 扣预算，重试成功 MUST 只扣一次。

#### Scenario: 下发但失败

- **WHEN** like/collect 下发后回报 `ok:false`
- **THEN** 不扣会话预算

#### Scenario: 真成功

- **WHEN** like/collect 回报 `ok:true`
- **THEN** 扣一次会话预算（重试后成功也只扣一次）

### Requirement: 现场评论跨屏累计采集且滚不动仍抓可见

执行端滚评论区 MUST 在滚动过程中逐屏抽取候选并按锚点去重累计（不止终态一屏），抽取前留短渲染门；当找不到可滚容器或滚不动时 MUST 仍抽取当前可见评论随回执带回，ok/reason 保持诚实。

#### Scenario: 短评论区不溢出

- **WHEN** 评论少到不产生滚动（`no_scroll`）
- **THEN** 回执 `ok:false reason=no_scroll`，但 candidates 带回当前可见评论（不再一条不采）

#### Scenario: 多屏评论

- **WHEN** 评论区可滚多屏
- **THEN** 累计去重后的候选条数多于仅取终态一屏

### Requirement: 云端采评论区分采集失败与真无评论

云端消费 `scroll_comments` 回执时 MUST 区分「采集失败（`ok:false`）」与「真无评论（`ok:true` 且候选为空）」，MUST NOT 把二者静默抹平为「无评论」。

#### Scenario: 采集失败

- **WHEN** `scroll_comments` 回报 `ok:false`（`no_target` / `no_scroll` / 异常）
- **THEN** 记可观测信号（warn），不当作「这篇没有评论」

#### Scenario: 真无评论

- **WHEN** `scroll_comments` 回报 `ok:true` 且候选为空
- **THEN** 按「这篇确无现场评论」处理

