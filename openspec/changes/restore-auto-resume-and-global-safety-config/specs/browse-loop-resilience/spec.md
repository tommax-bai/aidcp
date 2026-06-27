## ADDED Requirements

### Requirement: 浏览循环因结束命令停止后须可被云端浏览类命令唤醒重启

边端浏览循环在收到会话结束命令（`session.end`）停止后（循环退出、不再上报），若随后收到云端**浏览类推进命令**（如 `page.scroll`、`navigation.back` 等），MUST 能**重启浏览循环**并重新上报 `page.cards`，使云端决策环得以继续；MUST NOT 把这类命令静默堆进**无人消费**的命令队列致其永久堆积（既有缺陷：循环停止后命令被入队但无消费者）。重启 MUST 幂等（循环已在跑时为安全空操作），且重启语义 MUST 与自动续场配套——云端续场重开会话后下发的引导命令必须能让已停的边端循环复活。重启 MUST NOT 在边端**主动诚实下线/关闭**流程中误触（关闭中收到的迟到命令不得复活循环）。

#### Scenario: 结束后收到浏览类命令重启已停循环

- **WHEN** 边端浏览循环已因 `session.end` 停止，随后收到云端一条浏览类推进命令（如续场引导的 `page.scroll`）
- **THEN** 边端重启浏览循环、重新评估当前页并上报 `page.cards`，云端据此续驱决策环

#### Scenario: 浏览类命令 MUST NOT 静默堆积无人消费

- **WHEN** 浏览循环未在运行时收到云端浏览类命令
- **THEN** 命令 MUST 触发循环重启被消费，MUST NOT 仅入队后无任何消费者而永久静默堆积

#### Scenario: 关闭流程中迟到命令不复活循环

- **WHEN** 边端正在主动诚实下线/关闭，期间收到一条迟到的云端浏览类命令
- **THEN** 边端 MUST NOT 因该命令重启浏览循环（关闭语义优先），干净退出

## MODIFIED Requirements

### Requirement: 会话必须在有界 idle 内自愈或终止

cloud orchestration SHALL 运行一个 wall-clock 看门狗：当超过 idle-nudge 阈值无任何 edge 上报/命令活动时，MUST 发起一次恢复性 nudge；当超过更长的 idle-end 阈值仍无活动时，MUST 触发 `session.should_end` 结束会话。会话存活性 MUST NOT 依赖外部进程强杀（SIGTERM）来打破停滞。

看门狗的两段阈值 SHALL 可配置且热加载：**恢复轻推**（idle-nudge）默认保持较短（约 2min，且 MUST 大于详情页停留上限以免正常长停留中途误触），用于在**不结束会话**的前提下自愈瞬时卡顿；**放弃结束**（idle-end，MUST 大于 idle-nudge）默认 1 小时，仅当戳不活的真死局才回收。两段阈值 SHALL **为全局可配（取消账号维度——所有账号共用同一对阈值）**、运行时现读（改值下场即生效、无需重启），缺表/全局行缺失/非法值 MUST 逐位回落写死默认（**绝不 brick**）。看门狗的判活基线 MUST 由 edge 的真实上报/命令活动驱动，MUST NOT 把会话内 excursion（通知巡视）误判为停滞而过早结束（巡视上报本身即刷新判活基线）。

#### Scenario: 短 idle 触发恢复 nudge
- **WHEN** 距上一次 edge 上报/命令活动超过 idle-nudge 阈值且会话仍 active
- **THEN** cloud 下发一次 `scroll` nudge 以尝试重新驱动循环，且 MUST NOT 因此结束会话

#### Scenario: 长 idle 触发会话结束
- **WHEN** 距上一次活动超过 idle-end 阈值（默认 1h，> idle-nudge）仍无任何活动
- **THEN** cloud 触发 `session.should_end` 并下发 `session.end`，干净结束而非无限静默

#### Scenario: 看门狗阈值全局配置热加载
- **WHEN** 运营把**全局** idle-end 阈值由默认 1h 改为更短值
- **THEN** **所有账号**下一次判活即按新阈值（无需重启）；配置缺失/非法时回落写死默认、云端照常运行
