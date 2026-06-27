## MODIFIED Requirements

### Requirement: 会话必须在有界 idle 内自愈或终止

cloud orchestration SHALL 运行一个 wall-clock 看门狗：当超过 idle-nudge 阈值无任何 edge 上报/命令活动时，MUST 发起一次恢复性 nudge；当超过更长的 idle-end 阈值仍无活动时，MUST 触发 `session.should_end` 结束会话。会话存活性 MUST NOT 依赖外部进程强杀（SIGTERM）来打破停滞。

看门狗的两段阈值 SHALL 可配置且热加载：**恢复轻推**（idle-nudge）默认保持较短（约 2min，且 MUST 大于详情页停留上限以免正常长停留中途误触），用于在**不结束会话**的前提下自愈瞬时卡顿；**放弃结束**（idle-end，MUST 大于 idle-nudge）默认 1 小时，仅当戳不活的真死局才回收。两段阈值 SHALL 按账号可配、运行时现读（改值下场即生效、无需重启），缺表/缺行/非法值 MUST 逐位回落写死默认（**绝不 brick**）。看门狗的判活基线 MUST 由 edge 的真实上报/命令活动驱动，MUST NOT 把会话内 excursion（通知巡视）误判为停滞而过早结束（巡视上报本身即刷新判活基线）。

#### Scenario: 短 idle 触发恢复 nudge
- **WHEN** 距上一次 edge 上报/命令活动超过 idle-nudge 阈值且会话仍 active
- **THEN** cloud 下发一次 `scroll` nudge 以尝试重新驱动循环，且 MUST NOT 因此结束会话

#### Scenario: 长 idle 触发会话结束
- **WHEN** 距上一次活动超过 idle-end 阈值（默认 1h，> idle-nudge）仍无任何活动
- **THEN** cloud 触发 `session.should_end` 并下发 `session.end`，干净结束而非无限静默

#### Scenario: 看门狗阈值按账号配置热加载
- **WHEN** 运营把某账号 idle-end 阈值由默认 1h 改为更短值
- **THEN** 该账号下一次判活即按新阈值（无需重启）；配置缺失/非法时回落写死默认、云端照常运行

## ADDED Requirements

### Requirement: 单场计时须排除会话内 excursion 耗时且不被时限中途打断

会话监测体的单场时长判定 MUST 排除会话内 excursion（通知巡视）所耗时间：excursion 开始时 MUST 暂停时限判定，excursion 结束时 MUST 把该段从单场已用时长扣除（恢复后再判）。时限 MUST NOT 在 excursion 进行中触发 `session.should_end` 把 excursion 中途打断——该结束须**延期**到 excursion 结束、扣除其耗时后，若真实浏览时长仍超限再判结束。暂停态 MUST 用多原因引用计数（而非布尔）以正确处理嵌套/并发暂停，且 MUST 在会话重启/拆除时清空、绝不跨场残留。excursion 期间 MUST NOT 冻结空闲看门狗（巡视上报持续刷新判活基线，卡死巡视由看门狗有界兜底）。

#### Scenario: 巡视期到点不中途结束、延期到巡视结束
- **WHEN** 单场时限在通知巡视进行中到达
- **THEN** 云端 MUST NOT 当场结束会话/打断巡视；待巡视结束、扣除巡视耗时后，若真实浏览时长仍超限再触发 `session.should_end`

#### Scenario: 巡视耗时不计入单场时长
- **WHEN** 一场会话内发生了一次耗时 T 的通知巡视
- **THEN** 该 T 不计入单场已用时长（巡视结束时从计时扣除），单场剩余浏览时长不被巡视吃掉

#### Scenario: 卡死巡视仍被看门狗兜底
- **WHEN** 巡视异常卡住、长时间无任何 edge 上报
- **THEN** 空闲看门狗（未被冻结）在 idle-end 阈值内照常触发 `session.should_end`，会话自愈终止而非永久冻结
