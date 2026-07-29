## Why

Facebook 加群成功后，浏览器通常已经停留在目标群根页，但 Native 首帖读取仍无条件再次导航同一地址，造成一次可见刷新并丢失可安全复用的页面状态。需要在不降低目标群校验、页面阻断识别和首帖语义的前提下，消除这次冗余根页导航。

## What Changes

- Edge 在执行 Facebook `first_commentable_group_post` 前，对当前 CDP target 做一次实时、只读的群根页可复用性探测。
- 仅当当前页面被完整证明为目标群根页、已就绪、未阻断且真实帖子滚动容器位于顶部时，跳过根页导航。
- 任一探测字段缺失、异常或不满足时，保持现有行为，导航到规范化目标群根页一次。
- 首帖候选仍须重新探测，并在接受前证明页面上下文仍属于精确目标群根页；不复用加群 DOM、坐标或候选引用。
- 增加结构化复用/回退原因和覆盖零导航、单次回退、上下文变化的 Native 回归测试。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `facebook-scheduled-comment`: 将“首帖读取总是导航群 discussion stream”改为“先建立可信群根页；仅在当前状态实时证明可复用时跳过导航”。

## Impact

- 影响 `aidcp-edge` Native Facebook 首帖读取编排、页面探针及 fake CDP 回归测试。
- 不修改 Cloud 编排、协议 v2、配额、风险状态、评论提交或加群成功判据。
- 这是 Edge 运行时行为变化；源代码验证不代表已安装客户端更新，且本变更不包含安装包发布。
