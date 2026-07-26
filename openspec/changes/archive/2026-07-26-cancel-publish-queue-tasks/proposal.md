## Why

管理后台的发布队列可以看到尚未进入生成生命周期的排队任务，但当前没有就地取消入口。运营人员只能等待任务自行执行或通过其它渠道干预，容易造成错误任务继续占用队列与生成资源。

## What Changes

- 在“发布队列”的每个排队任务卡片上增加明确的取消操作与二次确认。
- 取消请求携带任务当前版本，拒绝基于过期页面状态误取消已经发生变化的任务。
- 取消成功后刷新排队任务和发布生命周期；并按服务端返回状态区分“已取消”与“取消请求已受理”。
- 取消失败时保留任务卡片并显示可理解的原因，版本冲突同时刷新最新状态。

## Capabilities

### New Capabilities

- `publish-queue-task-cancellation`: 管理员从发布队列安全取消对应排队发布任务的交互、并发保护与反馈契约。

### Modified Capabilities

None.

## Impact

- `aidcp-console`: 发布队列任务卡片、取消 mutation、查询失效与回归测试。
- Cloud API: 复用现有 `POST /api/delegated-tasks/:taskId/cancel` 及任务 `version`，不新增接口或数据库迁移。
- Runtime: `queued` / `deferred` 任务可立即终止；已进入 `planning` 的任务由现有 Cloud 工作器在安全边界收口。
