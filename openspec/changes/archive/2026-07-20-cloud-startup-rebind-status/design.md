## Context

renderer 当前把所有正在启动或运行的环境纳入 Cloud 汇总，并以 `connectedCloudKey !== target.key` 判定待重绑。核心刚启动时会诚实地把 `connectedCloudKey` 置空，直到握手日志确认实际 Cloud；空值因此被误当作与 dev/ol 不一致。

## Goals / Non-Goals

**Goals:**

- 首次启动的未知实际 Cloud 不再触发红色“待重绑”。
- 已知实际 Cloud 与目标不一致时继续如实提示待重绑。
- 保持显式重绑 pending/failed 的现有展示与动作不变。

**Non-Goals:**

- 不增加新的连接中状态、颜色或交互。
- 不修改 core、Cloud 地址解析、重绑 IPC、浏览器状态或任务生命周期。

## Decisions

- 待重绑的不一致判断增加“实际 Cloud 已知”前提：只有非空 `connectedCloudKey` 与目标不同才构成不一致。空值继续代表尚无可比较的实际连接证据。
- 显式 `cloudRebind.state === 'pending'` 仍独立计入待重绑，避免改变用户主动发起重绑后的既有反馈。
- 用现有 renderer 源码结构测试锁定条件，不引入新的状态模型。

## Risks / Trade-offs

- [首次连接期间顶部只显示目标 Cloud，尚不能证明已经连上] → 保持本次最小范围；环境自身的连接状态继续承载启动/失败信息，顶部只移除错误的人工动作提示。
- [误伤真实 Cloud 切换提示] → 回归测试同时覆盖空实际值和已知实际值不一致两种输入。
