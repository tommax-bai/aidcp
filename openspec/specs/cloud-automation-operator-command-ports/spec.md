# cloud-automation-operator-command-ports Specification

## Purpose
TBD - created by archiving change split-cloud-automation-production-runtime. Update Purpose after archive.
## Requirements
### Requirement: 四条运营指令 SHALL 经鉴权的跨进程通道从 api 抵达 automation

系统 SHALL 以既有 paired command 形态（api 客户端 → automation route + receiver）承载
自由文本委托、发布 / 评论指令、委托任务卡片动作、调度启停这四条运营指令——它们的入站在 api、
处理器在 automation——MUST NOT 新造第二套命令机制。每条请求 SHALL 携带版本与部署 target
并由服务端注入 target，MUST NOT 由调用方选择 target。

指令不可达时，api 侧 SHALL 向运营者如实回报「指令未送达」，
MUST NOT 表述为已受理、已排队或已执行。

#### Scenario: 指令正常送达

- **WHEN** 运营者在飞书触发调度启停
- **THEN** api 经鉴权通道把指令送到 automation 的处理器
- **AND** 回报的结论来自 automation 的真实处理结果

#### Scenario: automation 不可达

- **WHEN** automation 进程不可达
- **THEN** 运营者看到「指令未送达」
- **AND** 不显示已受理、已排队或已执行

### Requirement: 自由文本委托的意图解析 SHALL 留在 automation

自由文本委托入口 SHALL 把原始文本整体交给 automation 解析。
api 侧 MUST NOT 自行解析意图后改调结构化入口——解析规则与语料都在 automation，
在 api 侧重做一份会让解析错误变成 api 的静默行为，且两份规则必然漂移。
委托端口的方法面 SHALL 显式包含自由文本入口。

#### Scenario: 运营者发来自由文本

- **WHEN** 运营者以自由文本触发委托
- **THEN** api 原样转发文本给 automation
- **AND** api 不产出 intent，也不改调结构化入口

#### Scenario: 解析失败

- **WHEN** automation 无法从文本解析出可执行意图
- **THEN** 回报具名的解析失败原因
- **AND** 不落一条无意图的委托任务

### Requirement: 调度启停 SHALL 收敛到单一处理器与单一幂等键空间

面板的调度启停与飞书的调度启停 SHALL 指向同一处理器、共用同一幂等键空间。
MUST NOT 为两个入口开两条独立 route——那会产生两份幂等键空间，
进程重启后互相看不见对方在跑什么。

#### Scenario: 两个入口先后触发同一次启停

- **WHEN** 面板与飞书先后对同一目标发出启停
- **THEN** 第二次按幂等键识别为重复
- **AND** 不产生第二次实际启停

#### Scenario: 进程重启后重放

- **WHEN** automation 重启后收到重放的启停指令
- **THEN** 按持久化的幂等键判定
- **AND** 不因内存态丢失而重复执行

### Requirement: 指令结果未知 SHALL 如实回报，MUST NOT 猜测结局

跨进程指令在传输失败或超时后，调用方 SHALL 回报「结果未知」，
MUST NOT 推断为成功或失败。重试 SHALL 依赖幂等键，
MUST NOT 以「再发一次总没错」的方式产生第二次副作用。

#### Scenario: 指令超时

- **WHEN** 指令已发出但响应超时
- **THEN** 回报结果未知
- **AND** 不记为成功也不记为失败

#### Scenario: 未知后重试

- **WHEN** 结果未知的指令被重试
- **THEN** 服务端按幂等键识别为同一次指令
- **AND** 不产生第二次副作用

