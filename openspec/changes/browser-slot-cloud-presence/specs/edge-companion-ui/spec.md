## ADDED Requirements

### Requirement: 云端、浏览器与人设状态 SHALL 正交呈现

Electron 客户端 SHALL 分别呈现 Cloud 会话、浏览器执行层和 `personaBound` 三态。浏览器排队、缺席或冷待机 MUST NOT 自动推导 Cloud 离线；Cloud transport 打开或握手响应异常 MUST NOT自动推导 Cloud 已连接；persona 未收到 MUST 保持未知。

#### Scenario: 浏览器排队但 Cloud 与人设已知
- **WHEN** 环境以 browser-absent 状态完成有效 Cloud welcome 并收到 `personaBound=true`
- **THEN** 客户端显示 Cloud 已连接、人设已设置、浏览器正在排队或待机
- **AND** MUST NOT 把整个环境显示为离线

#### Scenario: 有 socket 但 welcome 无效
- **WHEN** WebSocket 已打开但 hello 收到 error 或畸形 welcome
- **THEN** 客户端显示云端连接失败及可诊断原因
- **AND** MUST NOT 显示绿色“已连接云端”或用未知人设弹出未设置向导

#### Scenario: 引导不可用
- **WHEN** 控制面启动因未绑定、冲突、越权或存储不可用而不能建立 Cloud 会话
- **THEN** 客户端明确显示对应云端未连接原因与独立的浏览器排队状态
- **AND** MUST NOT 用泛化“离线”掩盖原因

### Requirement: 启动数量与失败原因 SHALL 可核对

客户端 SHALL 如实展示生效浏览器并发、正在运行数、排队数以及每个未启动环境的具体状态。单个 AdsPower 环境被占用或启动失败 MUST 释放启动闩并继续处理后续队列项，MUST NOT 使剩余任务无回复。

#### Scenario: 第五个环境被其它设备占用
- **WHEN** 浏览器并发上限为 5，而第 5 个被放行环境被 AdsPower 拒绝为“由其它设备使用”
- **THEN** 客户端将该环境标为具体启动失败、归还其槽位并继续放行下一队列项
- **AND** 运行数、排队数与失败数之和可与已请求启动数核对
