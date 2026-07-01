## MODIFIED Requirements

### Requirement: 会话必须在有界 idle 内自愈或终止

cloud orchestration SHALL 运行一个 wall-clock 看门狗：当超过 idle-nudge 阈值无任何 edge 上报/命令活动时，MUST 发起一次恢复性 nudge；当超过更长的 idle-end 阈值仍无活动时，MUST 触发 `session.should_end` 结束会话。会话存活性 MUST NOT 依赖外部进程强杀（SIGTERM）来打破停滞。

看门狗的两段阈值 SHALL 可配置且热加载：**恢复轻推**（idle-nudge）默认保持较短，用于在**不结束会话**的前提下自愈瞬时卡顿；**放弃结束**（idle-end，MUST 大于 idle-nudge）默认 1 小时，仅当戳不活的真死局才回收。

**关键联动不变量**：一次浏览决策的模型调用进行期间没有 edge 活动、空转计时在涨。故 idle-nudge 阈值 MUST **严格大于单次模型调用天花板**（见 `role-llm-config`，当前 ≥180s），且 MUST 大于详情页停留上限——两者取更大者再留余量（当前默认约 240s）。轻推阈值的**配置下限**亦 MUST ≥ 单次模型调用天花板，使运营经后台绝不能把轻推配到低于一次合法调用。idle-end 生产值 MUST 显著大于 idle-nudge，给「慢调用 + 重试」留空间。抬高单次模型调用天花板时 MUST 同步抬高本阈值，保持该不变量。

两段阈值 SHALL 按账号可配、运行时现读（改值下场即生效、无需重启），缺表/缺行/非法值 MUST 逐位回落写死默认（**绝不 brick**）。看门狗的判活基线 MUST 由 edge 的真实上报/命令活动驱动，MUST NOT 把会话内 excursion（通知巡视）误判为停滞而过早结束（巡视上报本身即刷新判活基线）。

#### Scenario: 短 idle 触发恢复 nudge
- **WHEN** 距上一次 edge 上报/命令活动超过 idle-nudge 阈值且会话仍 active
- **THEN** cloud 下发一次 `scroll` nudge 以尝试重新驱动循环，且 MUST NOT 因此结束会话

#### Scenario: 长 idle 触发会话结束
- **WHEN** 距上一次活动超过 idle-end 阈值（> idle-nudge）仍无任何活动
- **THEN** cloud 触发 `session.should_end` 并下发 `session.end`，干净结束而非无限静默

#### Scenario: 进行中的合法 thinking 决策不被轻推打断
- **WHEN** 一次浏览决策的模型调用正在进行、耗时处于单次模型调用天花板以内、其间无 edge 活动
- **THEN** 因 idle-nudge 阈值严格大于单次模型调用天花板，看门狗 MUST NOT 在该模型返回前注入恢复 nudge，避免滚走正要返回决策的页面

#### Scenario: 轻推配置下限不低于模型天花板
- **WHEN** 运营经后台把 idle-nudge 阈值配到低于单次模型调用天花板的值
- **THEN** 系统 MUST 拒绝或回落到配置下限（≥ 模型天花板），MUST NOT 让轻推短于一次合法模型调用

#### Scenario: 看门狗阈值按账号配置热加载
- **WHEN** 运营把某账号 idle-end 阈值改为另一合法值
- **THEN** 该账号下一次判活即按新阈值（无需重启）；配置缺失/非法时回落写死默认、云端照常运行
