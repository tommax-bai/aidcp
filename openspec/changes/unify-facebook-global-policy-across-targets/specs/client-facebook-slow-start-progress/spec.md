## MODIFIED Requirements

### Requirement: Cloud 以环境级权威事实原子设置冷启动进度

Cloud SHALL 提供当前客户环境作用域的独立冷启动进度读取与写入，且 MUST 保持既有 operation-policy 客户响应形状不变。写入只接受 `envKey` 路径参数与严格请求 `{ expectedRevision, day, completed }`。Cloud MUST 复核环境 ownership、Facebook 平台、唯一环境绑定事实与当前冷启动生命周期；客户端 MUST NOT 提交 `accountId`、日期锚点、总天数、配额、HTTP 目标或运行授权。

`day` MUST 是当前全局 `slowStart.totalDays` 范围内的整数，该总天数取**跨全部运行目标唯一一份**的全局策略。Cloud SHALL 以中国标准时当前自然日为第 `day` 天重写既有环境锚点，并按 `completed` 原子新增或删除该环境的完成事实；完成事实 MUST 按环境唯一标识存放，MUST NOT 按 execution target 各记一套。同一事务 MUST 创建新 operation-policy revision、写入可区分的前后进度审计并推进相关同步读镜像。写成功 SHALL 返回同一环境的完整写后投影。

#### Scenario: 修改当前天数

- **WHEN** 当前环境冷启动 active，运营以当前 revision 提交 `{ day: 4, completed: false }`
- **THEN** Cloud 把环境锚点调整为中国标准时今天是第 4 天并保持未完成
- **AND** 后续配额与运行时投影按全局第 4 天曲线计算

#### Scenario: 显式标记完成

- **WHEN** 当前环境冷启动 active，运营提交合法 day 与 `completed=true`
- **THEN** Cloud 写入该环境的完成事实并返回 `state=graduated, completed=true`
- **AND** 后续运行时不再以 active 冷启动接管
- **AND** 其它运行目标读到该环境同样为已完成

#### Scenario: 取消完成恢复所选天数

- **WHEN** 当前环境已 graduated，运营提交合法 day 与 `completed=false`
- **THEN** Cloud 删除该环境的完成事实并同时刷新锚点，使写后状态为该 day 的 active 冷启动
- **AND** 不因旧锚点已经过期而立即再次毕业
- **AND** 其它运行目标读到该环境同样恢复为 active

#### Scenario: 非冷启动状态拒绝进度写

- **WHEN** 当前权威配置既非 active 也非 graduated 冷启动
- **THEN** Cloud 具名拒绝进度写并返回可用的当前投影
- **AND** 不修改锚点、完成事实、policy revision 或审计成功记录

#### Scenario: 非法范围与环境拒绝关闭

- **WHEN** day 超出当前全局范围、请求含额外字段、环境不归属客户、平台不是 Facebook或绑定冲突
- **THEN** Cloud 返回可区分的校验或范围拒绝
- **AND** 不修改任何冷启动或 operation-policy 事实
