## Why

小红书正文编辑器会把换行解释为 ProseMirror 段落结构变更；当前 Edge 却可能把“换行 + 换行后的文字”放进同一次 `Input.insertText`。实机 dev 记录 #153 因此出现光标回退，多个分块尾部被后续文字逐步顶到文末，最终虽被 `post_validate_failed` 拦住而未发布，但有效稿件失败且运营短暂看到错序正文。

## What Changes

- 小红书正文填写把普通文本与换行拆成不同输入原语：普通文本仍走拟人化 `Input.insertText`，每个换行独立派发真实 Enter，任何 `Input.insertText` 都不得携带换行。
- 每次 Enter 后确认段落结构数达到预期，并在继续写字前把 selection 明确归到正文末尾，避免 Enter 被吞或旧 selection 将后续文字插到上一段尾部之前。
- 对换行输入增加有界的已写前缀/光标确认；无法确认时清场并诚实返回失败，绝不进入提交步骤。
- 增加覆盖多段正文、连续空行、分块边界尾字倒序积累以及取消清场的 Edge 回归测试；保持标题、话题、协议和 Cloud 编排不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `publish-pipeline`: 小红书 `fill_field(content)` 必须把换行作为独立段落输入，逐次确认光标归尾与已输入前缀，防止分块尾字错序后仍继续填写或提交。

## Impact

- 代码：`aidcp-edge/src/flows/publish-command-handlers.ts` 及对应测试。
- 行为：仅改变小红书正文的 Edge 输入原语和后置确认；标题、话题、Cloud、Console、协议及审批内容不变。
- 运行：源码验证止于 Edge 测试/typecheck、提交推送与 dev 客户端源码态验证；不构建或发布桌面安装包。
