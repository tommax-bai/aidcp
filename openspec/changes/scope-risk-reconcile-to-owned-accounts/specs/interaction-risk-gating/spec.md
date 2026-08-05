## MODIFIED Requirements

### Requirement: 配额判定依据的计数必须与库内事实一致

配额准入判定所依据的计数 SHALL 与 `risk_counters` 的库内事实一致。系统 MUST 具备检出二者偏差的机制，MUST NOT 让「内存计数只在控制器创建时回放一次、此后只累加本进程自己写的那些」这一事实成为不可观测的默认状态。

具体要求：

- 控制器建立时 MUST 从库回放当日窗口计数；账号归属被本实例占位成功、或归属变更后重新解析控制器时，MUST 强制重放，MUST NOT 复用可能陈旧的内存值。
- 系统 MUST 周期性地把内存计数与库内当日总量对账。判据 MUST 是「偏差是否为零」，MUST NOT 引入容忍阈值。
- 偏差非零 MUST 告警（含 accountId、动作、内存值、库值）并以库为准重建该账号计数，MUST NOT 静默沿用偏差计数继续做准入判定。
- **对账范围 MUST 限定为「归属为本 target 的账号」。** 归属在另一个 target 的账号 MUST 跳过，MUST NOT 判为偏差、MUST NOT 告警：`risk_counters` 是 dev / ol 共用且不带 `execution_target` 的既成事实账本，而内存计数只跟随本进程的记账；对不由本进程驱动的账号，二者结构上不可能相等，把它算成偏差会把这条零容忍信号退化成常态噪音。本进程之所以持有这些账号的内存计数，是因为面板 / 客户端的只读用量与配额查询会顺手物化控制器——**只读查询 MUST NOT 因此把该账号带进对账范围**。
- **归属读不到（无归属行、读失败）MUST 跳过并计数**，MUST NOT 默认按本 target 处理后进入对账。
- **跳过 MUST 可数、全跳过 MUST 可见**：每轮 MUST 能报出「已物化 / 实际对账 / 因归属跳过 / 因归属未知跳过」四个数；当已物化账号数不为零而实际对账数为零时，MUST 响亮记录一次——过滤器写错导致对账全线静默失效，与「一切正常」在告警面上长得一模一样。
- 偏差告警 MUST 标明是哪个 target 报出的，MUST NOT 让共用告警列表里的 dev / ol 两方来源不可分辨。

#### Scenario: 外部写入的计数行被对账检出

- **WHEN** 某归属为本 target 的账号，其 `risk_counters` 中出现一行不是由本进程内存计数产生的当日记录
- **THEN** 下一次对账 MUST 检出偏差并告警
- **AND** 该账号的内存计数 MUST 被以库为准重建，重建后与库内当日总量逐项相等

#### Scenario: 归属在另一个 target 的账号不产生偏差告警

- **WHEN** 某账号归属为另一个 target，该 target 正常驱动它并持续写入 `risk_counters`，而本进程因面板只读查询物化了它的控制器
- **THEN** 本进程的对账 MUST 跳过该账号
- **AND** MUST NOT 就该账号发出偏差告警，MUST NOT 把它计入偏差

#### Scenario: 归属未知的账号跳过而不冒充本 target

- **WHEN** 某已物化账号读不到归属（无归属行或归属读失败）
- **THEN** 对账 MUST 跳过该账号并计入「归属未知」跳过数
- **AND** MUST NOT 默认按本 target 处理后对账，MUST NOT 因此发出偏差告警

#### Scenario: 一轮全部跳过必须响亮

- **WHEN** 某一轮对账的已物化账号数不为零，而实际参与对账的账号数为零
- **THEN** 系统 MUST 响亮记录这一轮的四个计数
- **AND** MUST NOT 与「逐项相等、无偏差」这一正常结果在观测上不可区分

#### Scenario: 归属占位后强制重放

- **WHEN** 某账号首次在本 target 上握手成功并被本实例占位归属
- **THEN** 该账号的计数 MUST 从库重放一次
- **AND** MUST NOT 直接使用握手前可能已存在的内存计数

#### Scenario: 对账不放宽到阈值

- **WHEN** 某归属为本 target 的账号，其内存计数与库内当日总量相差 1
- **THEN** 系统 MUST 按偏差处理（告警 + 重建）
- **AND** MUST NOT 因差值小而判为一致

#### Scenario: 偏差告警标明来源 target

- **WHEN** 本进程发出一条风控偏差告警
- **THEN** 该告警 MUST 携带本进程的 `execution_target` 标注
- **AND** 在 dev / ol 共用的告警列表里 MUST 能据此分辨来源
