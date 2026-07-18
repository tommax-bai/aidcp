## Context

Cloud 已有两条共享同一审批信号的入口：飞书卡片回调直接调用 `writeApprovalSignal`，客户端则可通过既有 `publish.approval_action` RPC 进入 `handlePublishApprovalAction`，由云端执行 requestId、账号归属、稿件状态、内容版本、在线预检与 first-writer-wins 校验。Edge 主进程、preload 和 core stdin↔WS 桥仍完整保留这条 RPC。

当前渲染层却不再调用它，而是把审核页按钮改成创建 `approve_candidate` / `reject_candidate` 委托任务。创建接口返回 queued 只证明任务入队，不能证明审批决定落盘；真正动作还依赖委托 worker、执行器装配、轮询、ownership 和异步失败回报。这使一个需要即时明确结果的人审动作被错误地变成后台目标任务。

## Goals / Non-Goals

**Goals:**

- 审核页按钮重新等待 Cloud 权威审批动作结果。
- 保持客户端为纯传输方，不在本地伪造审批成功或平台发布成功。
- 失败时保留审核上下文并展示云端拒因；成功时只投影“已通过 / 已驳回”。
- 用渲染层行为测试锁住直连 RPC，防止再次被异步任务回执替换。

**Non-Goals:**

- 不删除委托任务的候选稿控制能力，也不改变 console / API 的委托入口。
- 不修改 Cloud 审批信号、飞书卡片、发布调度、协议类型或 IPC 形状。
- 不把审批受理描述为平台已发布。

## Decisions

### 1. 审核页复用既有 `publishApproval` IPC

渲染层以当前 `envId`、`publish-<recordId>`、决定值和 `contentVersion` 调用 `window.aidcpEdge.publishApproval`。这条链路最终到达 Cloud `handlePublishApprovalAction`，与飞书共同使用 `writeApprovalSignal`。

不选择“加快委托 worker”或“创建任务后轮询到终态”，因为二者仍把审批决定拆成两个领域事实并增加不必要的可用性依赖；审核页已有精确账号、稿件、版本和动作，不需要规划、排队或重试语义。

### 2. 成功后只投影审批决定，失败保留页面

请求在途禁用发布、取消与删图入口。收到 `ok:true` 后关闭审核页，并把本地显示状态更新为 Cloud 返回的 `state`；该状态仅表示决定已受理。请求异常或 `ok:false` 时保持审核页打开，根据 `reason` 显示具名提示，允许用户在刷新真态后重试。

不做乐观关闭或乐观改态，因为版本冲突、账号离线、另一渠道先决和云端不可达都必须如实反馈。

### 3. 回归测试从入口语义验证而非只测函数存在

jsdom 测试断言点击发布调用 `publishApproval` 且不创建委托任务；成功应答关闭审核页并投影审批态；失败应答保留页面、显示拒因且不改审批态。另保留 core 桥与 Cloud handler 的现有单元/契约测试。

## Risks / Trade-offs

- [旧安装包仍包含委托任务路径] → 源码修复后需要按桌面发布流程另行打包交付；本 change 不自行构建安装包。
- [Cloud 与客户端版本不匹配] → RPC 与协议已在线上长期存在且未改枚举；不可用时客户端按 `unavailable` / 连接失败诚实留页。
- [飞书与客户端同时点击] → 继续由 Cloud first-writer-wins 信号裁决，后到入口返回已处理，不覆盖先到决定。

## Migration Plan

1. 先合入 Edge 渲染层修复与回归测试；Cloud 无需迁移或部署。
2. 按现有桌面发布流程另行构建并发布新客户端后做真机双通道验收。
3. 若需回滚，仅回滚 Edge 渲染层提交；Cloud 信号格式和数据均无需回滚。

## Open Questions

- 无。
