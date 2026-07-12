## Why

管理后台内容排期的发帖、评论、联系评论当前只有「关 / 开」两档；「开」意味着每条都进入飞书审批。对低风险账号或特定自动动作，运营希望在后台显式预授权，让系统到点自动执行，同时飞书只收到可审计通知。

## What Changes

- 将内容排期中自动发帖、自动评论、自动联系评论从布尔开关升级为三档模式：`off`（关）、`review`（开，仍走飞书审批）、`auto_approve`（免审，后台预授权）。
- `review` 模式保持现有行为：生成/撰写后发送飞书审批卡，未通过不发布/不评论。
- `auto_approve` 模式不发送交互审批卡；系统保留授权信号/审批闸结构，自动写入预授权结果并发飞书通知卡，说明本次由后台免审配置触发。
- 自动发帖免审仍落库草稿、记录内容版本、经现有发布派发器下发；不得新增绕过 dispatcher 或 `approved===true` 复核的直发路径。
- 自动评论与自动联系评论免审只跳过飞书等待，不跳过 persona、风控、配额、去重、联系方式、边端在线、租约与提交后验证等运行闸。
- 浏览中热帖触发的自动联系评论沿用同一 `contactCommentMode`，账号未开或为 `off` 时不触发，`review` 人审，`auto_approve` 仅通知。

## Capabilities

### New Capabilities

### Modified Capabilities
- `content-schedule`: 内容排期动作开关从 boolean 升级为三档模式，并定义免审预授权的发帖/评论行为。
- `feed-hot-lead-group-comment`: 浏览热帖自动联系评论读取同一联系评论三档模式，而不是只读布尔开关。

## Impact

- `aidcp-cloud`: `account_content_schedule` 自愈 schema、store DTO、panel API、ContentScheduler、PublishExecutor/dispatcher 装配、CommentScheduler 审批入口、飞书通知卡与测试。
- `aidcp-console`: 内容排期 DTO、三档控件、乐观更新与回归测试。
- `aidcp`: OpenSpec 变更与验证。该变更不新增外部依赖，不改变 edge 协议。
