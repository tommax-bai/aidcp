## ADDED Requirements

### Requirement: 重启遗留委托不得继续占用洗稿单飞 lane

发布生成的进程内 run 在 Cloud 重启后丢失时，持久化委托层 MUST 同步释放其遗留 `planning` / `executing` ownership，并先对旧 attempt 诚实收敛。不同来源与同源后续重新触发 MUST NOT 被已退出进程的 DB 状态持续判为 `delegated_ownership_busy`。

#### Scenario: 同源新任务在重启恢复后起跑

- **WHEN** 一条参照洗稿在生成中遭遇 Cloud 重启，运营随后对相同 `(accountId, sourceId)` 重新触发
- **THEN** 系统 SHALL 先收敛旧 attempt 并释放旧 ownership
- **AND** 新任务随后 SHALL 能按现有账号与全局容量帽申请生成 claim
- **AND** MUST NOT 每 30 秒反复暂缓直至旧任务 24 小时 deadline

#### Scenario: 不同来源仍保持并发

- **WHEN** 重启恢复释放旧 ownership 后，同一账号有多个不同 `sourceId` 的洗稿任务排队
- **THEN** 它们 SHALL 继续按 `(accountId, sourceId)` lane 并行准入
- **AND** 恢复逻辑 MUST NOT 把发布动作族重新退化为账号级串行
