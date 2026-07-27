## Why

Facebook 评论目前把搜索关键词当作必填条件，空关键词会直接以 `no_keywords` 结束；排期“自动联系评论”也只会从已加入群中评论，并不会像 `/comment --join --contact` 那样先加入一个新群。真实账号探针同时证明：群讨论流首个可评论帖可以稳定取得 permalink，但详情页若按 DOM 顺序取正文，可能把背景信息流中的另一篇帖子当成生成上下文。后续 Gi Vo 真机回归又证明：Facebook 有时把时间锚点的 DOM `href` 降级为群首页片段，而正式 `/groups/<group>/posts/<post>` 只保留在该锚点的 React link/story 数据中；仅扫描 DOM `href` 会把真实可评论帖子误报为 `no_candidates`。

## What Changes

- Facebook 评论配置有关键词时继续走群内关键词搜索；关键词为空时不搜索，直接选择群讨论流第一条具备稳定 permalink 且可评论的帖子。
- 首帖选择同时接受 DOM 中的 canonical permalink，或 Facebook 自身 React link/story 数据明确给出的 canonical permalink；不从混淆参数、文本或顺序猜测帖子 ID。
- 首帖 permalink 打开后，正文、讨论和评论编辑器按同一个 canonical post identity 绑定；目标缺失、重复或上下文不一致时诚实失败，不回落 DOM 第一帖或搜索替代帖。
- Cloud 对 Edge 回传的等价 canonical 群帖形态统一按帖子身份验收，包括 `/groups/<group>?multi_permalinks=<post>`，但仍拒绝非群帖和派生不出稳定帖子身份的值。
- Facebook 排期 `contact_comment` 改为先加入一个新群，平台确认已成为成员后再走上述选帖、生成、审批与联系方式评论链；非 Facebook 的联系评论行为保持不变。
- 管理后台中 Facebook 的“自动联系评论”展示名改为“加群评论（联系）”；清空关键词后不新增“当前使用群内首帖”之类的状态提示。
- 独立 Facebook“自动加群”动作继续只加群，不隐式评论。
- 不修改本次已知的 Facebook 加群识别、群别名/数字 ID 作用域或 `observation_only` 问题；该问题由独立任务处理。

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `facebook-scheduled-comment`: 将关键词从执行前置条件改为搜索/首帖路由条件，并定义首帖选择与无搜索链路。
- `facebook-note-scoped-targeting`: 将生成上下文读取与评论编辑器一起绑定到请求的 canonical post identity。
- `content-schedule`: Facebook 联系评论排期改为“加群评论（联系）”，同时保持独立自动加群动作不变。

## Impact

- Control：OpenSpec delta 与 `docs/protocol.md` 中 `note.open` 的首帖选择参数。
- Cloud：Facebook 评论配置生效判定、评论调度分支、Edge 步骤封装、排期联系评论触发与用户可见通知。
- Edge：`note.open` Facebook 命令处理、群首帖选择、目标帖正文/讨论精确读取及相关测试。
- Console：Facebook 评论关键词空值 UX 与排期动作展示文案。
- 无数据库迁移；内部 `contact_comment` 字段、API 字段和持久化键保持兼容。
