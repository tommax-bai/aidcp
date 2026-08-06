# client-facebook-slow-start-progress Specification

## Purpose
TBD - created by archiving change configure-facebook-slow-start-progress. Update Purpose after archive.
## Requirements
### Requirement: 客户端仅在已确认冷启动模式下显示进度控件

桌面客户端 SHALL 在已建、当前客户可见且平台明确为 Facebook 的环境运行策略区中，把“当前天数”和“已完成”控件紧接在“主浏览入口”之后。只有既有运行策略投影与独立冷启动进度投影均完整确认，且当前选择为 `slow_start` 时两个控件才 SHALL 显示；普通、规则、消费、未知、读取中、非 Facebook 或非归属环境 MUST NOT 显示这些控件。

`slowStart.state=active` 与 `slowStart.state=graduated` SHALL 都表示环境仍选择了冷启动配置；毕业只停止冷启动运行时限制，不得把客户端选择器静默改成普通模式，否则运营无法取消完成状态。

#### Scenario: 冷启动模式显示相邻控件

- **WHEN** 客户端收到当前 Facebook 环境完整投影且已确认选择为 `slow_start`
- **THEN** “当前天数”和“已完成”紧接“主浏览入口”显示
- **AND** 当前天数范围来自投影的 `totalDays`

#### Scenario: 其它模式隐藏控件

- **WHEN** 已确认模式为普通、规则或消费，或运行策略尚未完整确认
- **THEN** 客户端不显示冷启动天数和完成控件

#### Scenario: 完成后仍可取消完成

- **WHEN** Cloud 回读 `slowStart.state=graduated` 且 `completed=true`
- **THEN** 客户端仍显示冷启动为已选择并保留进度控件
- **AND** 运营可提交 `completed=false` 恢复所选天数的 active 生命周期

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

### Requirement: 进度读写使用非乐观 CAS 回读

Cloud 独立进度投影 SHALL 返回 `slowStartProgress: { day, totalDays, completed }` 和既有最小 operation-policy 投影；`off` 或 `unknown` 的 `day` MUST 为 null，其余状态的 `day` MUST 落在 `1..totalDays`。既有 operation-policy 路由的 `slowStart` 字段 MUST 继续只包含 `state`，以兼容已安装客户端的精确响应校验。进度写 SHALL 使用统一 operation-policy `policyRevision` 做 compare-and-swap，以便与模式切换及其它进度修改串行化；revision 冲突 MUST 返回最新可用投影且不得覆盖较新状态。

客户端 SHALL 按 `envKey` 隔离进度缓存和写反馈。提交任一控件时 SHALL 发送完整 `{ day, completed }` 元组、禁用重复提交并继续显示最后确认值；只有同环境、revision 已推进且 day/completed 与请求一致的完整回包才可收敛为新值。失败、不完整或晚到回包 MUST NOT 冒充成功。

#### Scenario: 并发模式切换阻止旧进度写

- **WHEN** 运营读取冷启动进度后另一个请求先把环境切换到其它模式并推进 revision
- **THEN** 旧 revision 的进度写以冲突结束并返回最新模式投影
- **AND** 不重新创建或改写冷启动锚点

#### Scenario: 写入期间保留最后确认值

- **WHEN** 客户端已提交新的 day/completed 但 Cloud 尚未返回完整写后投影
- **THEN** 两个控件保持最后确认值、禁用并显示等待 Cloud 回读
- **AND** 不提前改变模式、配额或完成文案

#### Scenario: 环境切换隔离晚到回包

- **WHEN** 环境 A 的进度写尚未完成时运营切换到环境 B
- **THEN** A 的回包只更新 A 的缓存
- **AND** 不改变 B 的控件、模式或反馈

