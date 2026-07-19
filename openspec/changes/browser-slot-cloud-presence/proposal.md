## Why

浏览器槽位已被限制为少量并发，但桌面端仍把“启动核心并连接 Cloud”放在取得浏览器槽位之后：未获槽位的环境因此既拿不到人设真态，也不进入云端调度，形成没有日志、没有回执的“未启动黑洞”。同时，Edge 当前没有严格校验 Cloud 握手响应，异常响应也可能被显示为“已连接云端”，造成绿色在线但永远收不到任务的假成功。

## What Changes

- 将每个环境的控制面核心与浏览器执行槽位解耦：受信任的已绑定环境即使暂未取得浏览器槽位，也可先以 `browser_absent` 待机态连接 Cloud、接收账号真态和调度信号。
- 通过客户登录态下的环境所有权与持久账号绑定解析，为无浏览器启动提供最小、fail-closed 的账号引导；未知、冲突、越权或存储不可用时绝不猜测账号。
- 浏览器真正唤醒后重新读取平台登录身份；若与引导身份不同，先按真实身份重建 Cloud 会话，再允许任何浏览器动作。
- Cloud/Edge 任务链区分“引擎在线”和“浏览器就绪”；浏览器缺席的任务进入既有 FIFO 唤醒/槽位链并得到明确结果，不再静默消失。
- Edge 只在收到合法 `welcome` 且含有效 `sessionId` 后宣告连接成功；错误或畸形握手必须 fail-closed 并展示可诊断失败。
- 客户端将“云端连接”“浏览器运行/排队”“人设未知/已设置/未设置”作为互相独立的真态展示，禁止用本地 socket 打开或 `sessionId=?` 渲染绿色成功。

## Capabilities

### New Capabilities

- `edge-control-plane-presence`: 定义无浏览器控制面在线、严格 Cloud 握手、浏览器唤醒后身份复核以及引擎/浏览器双真态。

### Modified Capabilities

- `client-customer-auth`: 为已登录客户提供按环境所有权和权威绑定解析的最小控制面启动引导，所有不可解析情形 fail-closed。
- `browser-cold-standby`: 允许环境以浏览器缺席态首次启动，并复用冷待机唤醒与槽位释放机制。
- `edge-companion-ui`: 在浏览器排队或缺席时仍展示真实 Cloud 与人设状态，并拒绝假握手成功。
- `edge-task-execution-coordination`: 让控制面在线但浏览器缺席的任务走有界唤醒/排队回执，而不是被静默丢弃。

## Impact

- `aidcp-edge`: Electron 多环境监督器、核心启动生命周期、CDP 会话重附着、Cloud WebSocket 握手与状态 IPC/UI。
- `aidcp-cloud`: customer-auth 环境绑定引导接口、会话能力/在线状态语义、浏览器缺席任务唤醒与回执。
- 协议与兼容性：新增可选的 `browser_absent` 能力/状态；旧 Edge 保持现有行为，新 Edge 在 Cloud 不支持引导时诚实回退到仅排浏览器槽位，不猜测身份。
- 部署：Cloud 运行时变更发布到 `dev`；Edge 本轮完成源码、测试与推送，不生成安装包。
