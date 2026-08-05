# cloud-automation-production-runtime Specification

## Purpose
TBD - created by archiving change split-cloud-automation-production-runtime. Update Purpose after archive.
## Requirements
### Requirement: automation 独立进程 SHALL 由本仓自己的 main() 装配生产运行时

`aidcp-automation` SHALL 在 `createAutomationCompositionRoot` 之上提供真实 `main()`，装配边-云
WebSocket 服务端、进程内事件总线与角色调度器、风控单写者、各调度器与监测体，以及 4a 的 API 客户端组、
4b 的同步读镜像、本 change 的 content 客户端组与运营指令 receiver。

该 `main()` MUST NOT 构造任何非 automation 属主的 store，MUST NOT 对非 automation 属主的数据库开池，
MUST NOT 接收调用方传入的 PG client，也 MUST NOT 把其它属主的模块复制为本地实现。
组装清单 SHALL 逐段对应单体 automation 段；**在本进程里没有消费者的对象 SHALL 从组装根删除，
而不是为它新开跨进程端口**。

后台扫描、认领、重试或恢复类持久任务 SHALL 按 `AIDCP_DEPLOY_ENV` 限定 `execution_target`；
target 缺失或非法时 MUST NOT 启动该 worker。

#### Scenario: 装配清单不含外属主 store

- **WHEN** source guard 检查 `AIDCP_SERVICE=automation` 的生产装配
- **THEN** 只构造 automation 属主 pool/store 与 api/content 的 HTTP 客户端
- **AND** 不出现任何外属主 store 构造或外属主库连接

#### Scenario: 某对象在本进程没有消费者

- **WHEN** 清单核对发现某对象的全部消费者都在 api 或 content 段
- **THEN** 该对象从 automation 组装根删除
- **AND** 不为它新增跨进程端口

#### Scenario: 部署 target 缺失

- **WHEN** `AIDCP_DEPLOY_ENV` 缺失或非 `dev`/`ol`
- **THEN** 依赖 `execution_target` 的持久任务 worker 不启动
- **AND** 启动以具名原因终止，不以默认 target 继续

### Requirement: 业务入口 SHALL 被同步读 readiness 闸住

automation 进程 SHALL 在所需同步读镜像完成首次装载、readiness 到达 `ready` 之前**不放行业务入口**，
与 api 进程同形。readiness 未达成时进程 MAY 继续监听内部端口以供探活，但 MUST NOT 开始消费边缘连接、
下发命令或执行调度。

#### Scenario: 镜像尚未装载完成

- **WHEN** 进程已监听内部端口但同步读 readiness 仍非 `ready`
- **THEN** 业务入口保持未启动且状态可观测
- **AND** 不接受边缘连接、不下发命令、不执行调度

#### Scenario: 镜像装载完成后放行

- **WHEN** 同步读 readiness 转为 `ready`
- **THEN** 业务入口启动一次且只启动一次
- **AND** 重复的就绪信号不重复启动业务入口

### Requirement: 依赖缺席 SHALL 停在具名原因上，MUST NOT 压成默认值

任一必需依赖缺席时，automation 启动 SHALL 以具名原因终止并输出结构化启动失败记录。
MUST NOT 用空数组、`false`、未绑定、代码默认值或 `?.` 静默吞掉把缺席伪装成可用。
跨进程边界的错误识别 SHALL 使用结构化守卫（按具名字段判定），MUST NOT 依赖 `instanceof`
——跨进程后它恒为 false，会把真实失败静默退化成兜底原因。

#### Scenario: 必需客户端未配置

- **WHEN** content 或 api 的内部地址 / 令牌缺失
- **THEN** 启动以具名原因终止并输出结构化失败记录
- **AND** 不以空实现或默认值继续启动

#### Scenario: 跨进程错误识别

- **WHEN** 跨进程调用返回一个具名领域错误
- **THEN** 调用方按结构化字段识别它
- **AND** 不因 `instanceof` 恒 false 而退化成兜底原因

### Requirement: readiness blocker 台账 SHALL 与门禁同批收缩且只许下降

两份台账 SHALL 在同一批次内一致收缩——派生仓的 `AUTOMATION_ROOT_READINESS_BLOCKERS`
与事实源 `boundaries/composition-root-independent-blockers.json`——
条目只许删除、不许新增空位回填。台账非空时 `runAutomationEntry()` MUST 保持 fail-closed，
MUST NOT 因为「已经写了 main()」而提前放行；台账清零后该闸的存在性 SHALL 仍由测试钉住。

#### Scenario: 台账仍有未清条目

- **WHEN** 台账中仍存在任一 readiness blocker
- **THEN** 可执行入口拒绝启动并列出具名 blocker
- **AND** 不因生产装配已写好而放行

#### Scenario: 两份台账不一致

- **WHEN** 派生仓台账与事实源台账条目不一致
- **THEN** 门禁失败
- **AND** 不接受任一单侧修改

### Requirement: 验收 SHALL 按运行形态分层，MUST NOT 混层声称

验收 SHALL 按运行形态分层记录：loopback HTTP 契约测试只证明 route/client 的方法面与失败语义；
dev 单体部署只证明现网零回归；**只有 api / automation / content 三个独立进程都启动并互相通信，
才证明独立运行时生效**。任一层的通过 MUST NOT 被表述为其它层的结论。

#### Scenario: 契约测试全过

- **WHEN** 四条指令与七条 content authority 的 loopback 契约测试全部通过
- **THEN** 记录为 route/client 面闭合
- **AND** 不声称三进程可运行或独立启动已验证

#### Scenario: dev 单体部署健康

- **WHEN** dev 上单体部署健康检查全过
- **THEN** 记录为现网零回归
- **AND** 不声称 automation 独立进程已验证

### Requirement: 关停 SHALL 在有界时间内真正结束进程，MUST NOT 依赖对端自行断开

automation 进程收到终止信号后，其关停路径 SHALL 在有界时间内走完并使进程退出。关停路径上任何「等待对端自行断开」的步骤 MUST NOT 存在无界等待。

关闭边-云连接入口时，SHALL **主动断开当前在线的每一条边缘连接**并给出「服务端下线」语义的关闭码，而不是只停止接受新连接后等待它们自己结束。

> 停止接受新连接与断开已建立的连接是两件事。只做前者时，底层服务端要等**所有**已建立的连接结束才回调；而边缘客户端只会持续心跳、不会主动下线，于是那个回调永远不触发。表现是进程管理器的停止超时上限被吃满、整组被强杀，而关停日志停在「开始」上、既没有完成也没有失败。

主动断连之后 SHALL 有一个**有界兜底**：在给定时限内仍未完成关闭握手的连接 SHALL 被强制掐断。MUST NOT 因为单条卡死的连接而让整个关停重新变成无界等待。

关停干净走完后，入口 SHALL 以退出码 0 显式结束进程。MUST NOT 依赖「没有句柄了事件循环自然退出」——那让「关停完成」与「还剩一个句柄没还」两种状态在进程管理器那一侧完全同形。关停失败 SHALL 以非 0 退出。

关停路径上 SHALL 只有一个信号处理器，且它 SHALL 在收到第一个信号时摘除自己，使**第二个信号落回运行时默认处置、当场结束进程**。MUST NOT 存在第二个常驻处理器把重复信号吞掉——那会让「关停卡死时补一刀信号」这条逃生口失效，运维除了强杀之外没有别的手段。

#### Scenario: 关停时仍有边缘连着

- **WHEN** 进程收到终止信号，且此时有一条或多条边缘连接在线
- **THEN** 每一条在线连接 SHALL 收到「服务端下线」语义的关闭
- **AND** 关停 SHALL 在有界时间内完成，MUST NOT 等待边缘自行断开

#### Scenario: 某条连接不回关闭握手

- **WHEN** 主动断连后有连接在给定时限内没有完成关闭握手
- **THEN** 该连接 SHALL 被强制掐断
- **AND** 关停 SHALL 继续走完，MUST NOT 因它而无界挂起

#### Scenario: 关停干净

- **WHEN** 关停路径全部走完且没有抛错
- **THEN** 进程 SHALL 以退出码 0 结束
- **AND** 该结束 SHALL 可从进程管理器状态中与「被超时强杀」区分开

#### Scenario: 补发第二个终止信号

- **WHEN** 第一个信号之后关停仍未结束，运维补发第二个终止信号
- **THEN** 进程 SHALL 立刻结束
- **AND** MUST NOT 只记录一条「重复信号」然后继续挂着

