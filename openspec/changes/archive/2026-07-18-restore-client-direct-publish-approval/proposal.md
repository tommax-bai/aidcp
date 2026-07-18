## Why

客户端稿件审核页的「发布 / 取消」被改接到异步委托任务队列后，按钮只确认“任务已排队”就关闭审核页，真正的审批决定还依赖后台 worker、ownership 与后续对账；因此会出现客户端看似操作成功、审批信号却未及时或未实际落下的情况。飞书审批仍直接写入共享审批信号，所以两端可靠性和语义发生分叉，也偏离现行“应用内直接审批、客户端只等待云端受理真态”的契约。

## What Changes

- 将客户端稿件审核页的「发布 / 取消」恢复到既有 `publish.approval_action` 边云 RPC，直接等待云端 first-writer-wins 审批写入结果。
- 客户端只有收到云端 `ok:true` 决定受理结果后才关闭审核页并投影对应审批状态；失败时保留审核页并展示具名原因，不再把“委托任务已排队”当成审批已生效。
- 保留委托任务的候选稿控制能力供独立委托入口使用，但稿件审核页 MUST NOT 通过异步委托任务间接完成即时审批。
- 不修改飞书回调、审批信号格式、版本闸、账号归属闸、发布调度器或协议枚举。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `edge-companion-ui`: 明确稿件审核页的即时审批必须等待既有边云 RPC 的权威受理结果，不得降级为异步委托任务排队回执。

## Impact

- `aidcp-edge`: `src/electron/renderer/renderer.js` 与稿件审核交互回归测试。
- `aidcp-cloud`: 无运行时代码改动；复用现有 `publish.approval_action` 处理器及共享审批信号写入逻辑。
- `aidcp`: 新增本 OpenSpec 变更与验证记录。
- 无数据库迁移、无协议新增、无 Electron 安装包构建；运行时行为恢复后仅需发布 Edge 客户端才能交付到运营端。
