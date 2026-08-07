## MODIFIED Requirements

### Requirement: Facebook 打开发帖框必须使用下发预算内的有界等待

cloud SHALL 仅为 Facebook `select_mode` 下发 `timeoutMs=40_000`，edge SHALL 将该值作为“等待首页发帖入口 + 点击后等待 composer 编辑器”的总 deadline。edge MUST 在 deadline 内以有界轮询容忍入口渐进渲染，入口出现后 SHALL 立即继续，MUST NOT 使用一次性快照或固定长睡眠代替就绪判断。入口等待阶段 MUST 不超过 20 秒，点击后 SHALL 使用总 deadline 的剩余预算等待编辑器。

cloud 等待 `facebook.publish.command.result` 的窗口 SHALL 为下发预算加既有结果余量，使 edge 必须先于 cloud 收敛。小红书 `select_mode` MUST NOT 因本要求携带 Facebook 预算，其既有等待语义 MUST 保持不变。

deadline 内始终没有可点击入口时 edge MUST 诚实返回 `no_target`；入口已点击但编辑器未在剩余预算内出现时 MUST 诚实返回 `post_validate_failed`。两种情况均 MUST NOT 假成功、MUST NOT继续上传、填写或提交。

#### Scenario: 首页入口晚渲染后成功打开 composer
- **WHEN** Facebook 已确认处于个人首页，发帖入口在前几轮探测中不存在、随后在 20 秒入口窗口内出现
- **THEN** edge SHALL 在入口出现后点击一次，并在总 40 秒 deadline 内确认编辑器出现后返回 `ok:true`

#### Scenario: 入口预算耗尽时诚实失败
- **WHEN** Facebook 个人首页在入口等待窗口内始终没有可见发帖入口
- **THEN** edge SHALL 返回 `ok:false,error:'no_target'`，MUST NOT 点击其他相似控件，MUST NOT继续后续发布指令

#### Scenario: 点击后编辑器未出现
- **WHEN** edge 已点击经确认的首页发帖入口，但编辑器未在总 deadline 剩余预算内出现
- **THEN** edge SHALL 返回 `ok:false,error:'post_validate_failed'`，MUST NOT 把点击动作本身当作成功

#### Scenario: Cloud 等待窗口覆盖 edge 预算
- **WHEN** cloud 下发 Facebook `select_mode.timeoutMs=40_000`
- **THEN** cloud SHALL 等待 40 秒预算加既有 8 秒结果余量，MUST NOT 在 edge 正常等待期间以默认 30 秒提前超时

#### Scenario: 小红书发布计划不受影响
- **WHEN** cloud 构建小红书发布命令计划
- **THEN** 小红书 `select_mode` MUST NOT 携带 Facebook 的 40 秒预算，既有单指令等待行为 MUST 保持不变
