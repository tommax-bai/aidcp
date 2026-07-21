## ADDED Requirements

### Requirement: 视频号启动与鉴权 SHALL 经机器级临时浏览器通道串行

Edge SHALL 让每个视频号环境的启动初始化进入同一条机器级临时浏览器通道。通道容量 SHALL 固定为 1、同级严格 FIFO；多个视频号环境 MUST 按顺序完成会话校验与 connector 启动，MUST NOT 并发初始化。

已保存会话有效且身份匹配时，Edge SHALL 在浏览器关闭状态启动 connector 并释放通道，MUST NOT 为了证明登录而无条件打开浏览器。会话缺失、过期或需要 challenge 时，Edge MAY 在持有该通道租约期间打开鉴权 sidecar；登录确认后 SHALL 保存会话、关闭并确认 sidecar 已退出，随后释放通道。

失败、超时、环境关闭、子进程退出或生命周期代际切换 SHALL 释放租约；旧代迟到消息 MUST NOT 释放新代租约。手动重登或重新检查登录 MUST 复用同一通道，MUST NOT 另开绕过路径。

#### Scenario: 多个有效会话按顺序无浏览器启动
- **WHEN** 多个视频号环境同时启动，且各自保存的会话均有效、身份匹配
- **THEN** 它们按 FIFO 逐个完成校验与 connector 启动，全程不打开鉴权浏览器，每个环境完成后立即释放临时通道

#### Scenario: 会话过期才占通道打开浏览器
- **WHEN** 一个视频号环境轮到初始化且会话过期
- **THEN** 它在持有临时通道期间打开鉴权 sidecar，确认登录并关闭浏览器后释放通道，下一个排队环境才开始

#### Scenario: 进程退出不会卡死通道
- **WHEN** 当前持有临时通道的视频号核心异常退出
- **THEN** 外壳回收该租约并放行 FIFO 队首，迟到的旧代释放消息不得影响新持有者

### Requirement: 视频号 API-only 运行态 SHALL 与浏览器占用解耦

视频号完成鉴权后 SHALL 通过 API/Cloud 数据面运行，浏览器状态 SHALL 为 `closed`，且 MUST NOT 占用公共执行槽位或临时浏览器通道。Edge 只有在当前身份匹配、授权为 active、connector 已启动、Cloud interaction capability 已协商、环境未暂停/解绑，并存在当前进程生命周期内的新鲜 API/Cloud 成功往返证据时，才 SHALL 把环境投影为「运行中」。仅有历史登录成功或保存会话 MUST NOT 证明运行中。

#### Scenario: API-only 运行但浏览器关闭
- **WHEN** 视频号身份与授权有效、connector/Cloud 协商完成且有新鲜成功往返
- **THEN** 客户端显示环境「运行中」与浏览器「已关闭」，公共槽位和临时通道占用均不包含该环境

#### Scenario: 只有旧登录记录不得显示运行中
- **WHEN** 视频号仅存在曾经登录成功的保存会话，但 connector 未启动、Cloud 未协商或没有当前进程内成功往返
- **THEN** 客户端 MUST NOT 显示「运行中」，并按真实缺口显示连接中、需登录、已暂停或失联
