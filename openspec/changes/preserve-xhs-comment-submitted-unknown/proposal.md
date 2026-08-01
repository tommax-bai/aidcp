## Why

小红书执行端已经能区分“评论已出现但编辑器未清空”和“提交后的确认状态不可读”，但 Cloud 只把旧原因 `submitted_unconfirmed` 识别为“已提交、结果未知”。另外两个同义回执会被误判成“未提交”，不写去重账并允许后续重试，存在同一笔记重复评论的风险。

## What Changes

- Cloud 将小红书评论的三个已知提交后不确定回执统一归一为现有 `submitted_unconfirmed` 结果。
- 归一后的评论写入笔记级评论去重账，并终止自动重试，但不计作平台确认成功。
- 保持提交前失败和提交前抢占的既有语义：不写去重，分别按失败或放弃本轮处理。
- 用闭集单元测试覆盖三个提交后原因以及提交前失败/抢占反例；不改变 Edge、协议字段或真实账号行为。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `comment-interaction`: 补充评论提交后不确定回执的统一归类、去重、不重试和不计确认成功契约。

## Impact

- 代码属主：`aidcp-cloud/src/comment-agent/edge-steps.ts` 及其测试。
- 下游复用现有 `CommentPostResult.status='submitted_unconfirmed'` 与评论去重流程，不新增协议消息或数据库迁移。
- Edge、Console、桌面安装包及 OL 环境不受影响。
