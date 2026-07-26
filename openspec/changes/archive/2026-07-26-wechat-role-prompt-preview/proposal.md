## Why

管理后台已经把视频号收件箱的三个真实 LLM 角色列入角色目录，但 prompt 预览 provider 只识别浏览侧与发布侧，导致这些 interaction 角色错误落入“暂不支持预览”。同一次目录—预览审计还发现若干后来新增的现役文本/视觉角色没有忠实预览，违背“现役模型角色 prompt 在后台只读可见”的既有约定。

## What Changes

- 为视频号收件箱的意图分类、模板润色、风险复核三项角色提供与运行时同源的 prompt 预览。
- 全量核对真实模型调用、角色目录与预览来源，补齐 Facebook 加群判定、此前漏入目录的 Facebook 定向评论撰写、封面文字卡文案及三个视觉模型角色的真实 prompt / 文本指令预览。
- 让运行时调用与后台预览复用同一 prompt 构建函数或注册表，避免复制两份 prompt 后漂移。
- 增加目录级完整性回归测试：除明确不具备文本 prompt 的角色外，现役模型角色必须能返回非空、可用的忠实预览；渲染失败仍诚实降级且不影响运行闭环。
- 保持接口只读、保持现有角色调用行为和 prompt 文本不变；不新增 prompt 编辑能力。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `role-llm-config`: 将现役模型角色的忠实 prompt 预览要求明确覆盖 interaction、命令式/独立浏览角色、发布文本角色和视觉模型角色，并增加目录—预览完整性约束。

## Impact

- `aidcp-cloud`: 角色 prompt 构建函数、预览注册与覆盖测试。
- `aidcp-console`: 不改接口与页面结构；查看器补充“不使用人设”的真实来源说明，并呈现后端新增的可用预览。
- `aidcp`: `role-llm-config` OpenSpec 增量与实施记录。
- 无数据库、协议或写接口变更；运行时 prompt 语义保持不变。
