## Why

客户端“开发者详情”目前只有连接状态与短时原始日志，无法明确回答一条自动化命令是否已经下发、被 Edge 接收、通过校验并进入执行。排障时容易把“已下发”“已收到”“已执行”和“平台已确认”混为同一事实，也缺少统一且安全的命令摘要。

## What Changes

- 在开发者详情中增加按当前环境隔离的“引擎命令”诊断列表，展示命令类型、接收时间、当前阶段和安全摘要。
- 对 Cloud 主动下发命令统一生成 Edge 本地结构化诊断事件，明确区分已收到、已拒绝、已交给执行器及可观测终态；不得由接收事件推断平台成功。
- 仅通过逐命令白名单生成摘要；正文、回复、私信、Cookie、Token、二维码、完整 URL、浏览器调试地址及原始 payload 不得进入 renderer 或诊断日志。
- 命令诊断保留有界、跟随当前环境切换，不进入普通用户活动流，也不改变自动化命令路由或执行语义。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 开发者详情新增按环境隔离、阶段诚实且敏感字段白名单化的引擎命令诊断视图。

## Impact

- `aidcp-edge`: Cloud 主动命令接收边界、核心到 Electron 主进程的本地结构化事件、环境状态投影、renderer 开发者详情与测试。
- `aidcp`: `edge-companion-ui` OpenSpec delta 与界面说明同步。
- 不修改 Cloud API、Cloud→Edge 协议信封、命令 payload、执行器行为、风险状态或客户端普通活动流。
