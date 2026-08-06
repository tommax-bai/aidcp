# restricted-account-policy Delta

## ADDED Requirements

### Requirement: 受限处置策略为全局单行配置且热生效

系统 SHALL 提供一份全局单行「受限处置策略」配置,含两个字段:`mode`(`browse_only` 只浏览 / `full_pause` 浏览也暂停)与 `recoveryHours`(受限自动恢复时长,单位小时)。配置 SHALL 落库并经内存镜像热加载,写入 SHALL 与跨进程失效信号同事务推进(dev/ol 共库双进程);该镜像 MUST 在配置镜像穷举注册表登记。缺行或字段非法时 MUST 逐项回落默认(`browse_only` / 72),MUST NOT 因配置缺失拒绝启动或抛错(绝不 brick)。后台修改后 MUST NOT 需要重启进程即生效。

#### Scenario: 表为空时行为与写死默认逐位一致

- **WHEN** 配置表无行或字段为 null
- **THEN** 模式取 `browse_only`、恢复时长取 72 小时,与配置化之前的默认行为逐位一致

#### Scenario: 后台修改后热生效

- **WHEN** 运营在后台把模式改为 `full_pause` 并保存成功
- **THEN** 本进程判定即刻按新模式执行,另一 target 进程在失效信号轮询上界内跟进,均无需重启

### Requirement: 受限自动恢复经单写通道逐级回迁

系统 SHALL 以周期扫描接活风控状态机的恢复路径:受限账号自「恢复基点」起满 `recoveryHours` 小时且无新风控信号 → 自动恢复到 `warned`;`warned` 满既有 7 天窗口 → 自动恢复到 `normal`。恢复 MUST 经该账号 controller 的单写通道(恢复信号 + 持久化),MUST NOT 绕过 controller 直改风控状态存储。`frozen` MUST NOT 被扫描器恢复。两种模式(`browse_only` / `full_pause`)下自动恢复均 SHALL 生效。

#### Scenario: 受限满窗自动回警告

- **WHEN** 账号处于 `restricted`,自恢复基点起已满 `recoveryHours` 且期间无新风控信号
- **THEN** 扫描器经该账号 controller 发恢复信号,状态变为 `warned` 并持久化

#### Scenario: 窗口内新信号顺延恢复

- **WHEN** 受限账号在窗口内又收到风控信号
- **THEN** 恢复基点顺延,本轮扫描不恢复该账号

#### Scenario: 冻结不被扫描

- **WHEN** 账号处于 `frozen` 且已停留超过任意时长
- **THEN** 扫描器不对其发任何恢复信号,唯一出口仍是人工

### Requirement: 恢复基点取 statusSince 与 lastSignalAt 的较大者

恢复窗口的计时基点 SHALL 为 `max(statusSince, lastSignalAt)`(`lastSignalAt` 缺失时取 `statusSince`)。手动加严(`manual_restrict`)不记信号时间戳,若以 `lastSignalAt` 单独作基点会被立即判满窗——该路径 MUST 被基点规则排除:手动受限账号 MUST 从进入受限时刻起足额等满窗口。

#### Scenario: 手动受限不被秒恢复

- **WHEN** 运营刚以 `manual_restrict` 把账号置为 `restricted`(该账号无任何信号时间戳)
- **THEN** 扫描器在满 `recoveryHours` 之前 MUST NOT 恢复该账号

### Requirement: 双进程共库下扫描器只写属主账号

dev/ol 两个 automation 进程共库,扫描器 SHALL 只对本进程 `execution_target` 拥有的账号发恢复信号;非属主账号 MUST 跳过。若条件写因属主竞争被拒,MUST 记驱逐告警并放弃该账号本轮恢复,MUST NOT 形成第二个写者,MUST NOT 把放弃伪装成已恢复。

#### Scenario: 非属主账号被跳过

- **WHEN** 一个受限满窗账号的属主是另一 target
- **THEN** 本进程扫描器不对其发恢复信号

### Requirement: 恢复时刻三处消费口径同源

「恢复时刻」(基点 + 窗口)SHALL 由单一实现推导,view 判定的剩余等待时长、续场闸的恢复时刻、扫描器的满窗判断三处 MUST 引用同一实现,MUST NOT 各自拼算式。

#### Scenario: 三处读数一致

- **WHEN** 同一时刻分别从 view 判定、续场闸裁决、扫描器判窗读取某受限账号的恢复时刻
- **THEN** 三者给出同一数值

### Requirement: 手动通道不受自动恢复窗口约束

客户端「解除受限」与运营信号(`manual_restrict` / `manual_freeze` / `manual_unfreeze` / `operator_override_recover`)的既有语义与即时性 SHALL 保持不变,MUST NOT 因引入自动恢复而被延迟、拦截或改写目标状态。

#### Scenario: 客户端解除受限立即生效

- **WHEN** 客户在受限满窗之前于客户端发起「解除受限」且云端校验通过
- **THEN** 恢复按既有语义立即执行,不等待 `recoveryHours`

### Requirement: 策略配置的面板编辑非乐观且枚举对齐

automation SHALL 提供策略配置的读写面板端点(api 透传),写入 SHALL 返回写后真态;console SHALL 提供模式选择与恢复小时数编辑,其枚举取值 MUST 与云端逐字一致。非法值(未知模式、非正小时数)MUST 被拒绝并可区分地呈现,MUST NOT 静默落库。

#### Scenario: 非法小时数被拒

- **WHEN** 后台提交 `recoveryHours = 0` 或负数或非整数
- **THEN** 写入被拒并返回可区分的失败,配置保持原值
