## Why

发布目标浏览器在本机并发槽位已满时会进入现有 FIFO 启动队列，但当前 Cloud 把本次 `browser_wake_failed` 与其他接管失败一样作废授权，导致浏览器稍后真正启动后，原发布也不会继续。系统已经具备持久授权、待审草稿补偿扫描和本地 FIFO 唤醒，缺的是把“暂时没槽位”接成可恢复等待，而不是再造一套调度器。

## What Changes

- 仅将发布租约申请阶段的 `browser_wake_failed` 归类为可恢复的浏览器槽位等待：保留草稿与授权，不计发布失败，不触发熔断，并由现有补偿扫描自动重试。
- 保持真实离线、CDP 不健康、无响应 acquire timeout 和发布序列已开始后的现有保守语义；这些结果不得伪装成槽位等待。
- 对操作员和客户端诚实表达“已批准，等待浏览器槽位，稍后自动重试”，并抑制周期扫描产生的重复通知。
- Edge 在任务租约释放后立即重新应用最新的冷待机提示；只有既有安全闸确认近期无浏览器工作时才关闭浏览器并归还槽位，不能因发布完成而强制驱逐仍在工作的账号。
- 保持本机严格 FIFO、不抢占、不插队；同账号发布仍按现有 `accountTail` 串行，不引入新的全局发布队列、状态机或数据库表。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `publish-dispatch-resilience`: 发布在零业务命令副作用阶段因浏览器槽位等待而唤醒失败时，授权必须保留并自动重试；其他失败与序列副作用边界保持不变。
- `browser-cold-standby`: 任务租约释放后应立即重判已有待机提示，在安全且近期无工作时及时归还浏览器槽位。

## Impact

- `aidcp-cloud`: `PublishDispatcher` 的租约失败分类、通知去重、补偿扫描行为和回归测试；服务器通知文案。
- `aidcp-edge`: task coordinator 进入空闲时向 Electron 外壳发私有生命周期提示，外壳复用现有 `applyBrowserStandbyHint()` 安全重判；聚焦生命周期/调度测试。
- 控制仓：修改 `publish-dispatch-resilience` 与 `browser-cold-standby` 行为契约。
- 不新增协议消息类型、数据库迁移、依赖或配额配置；不构建桌面安装包。
