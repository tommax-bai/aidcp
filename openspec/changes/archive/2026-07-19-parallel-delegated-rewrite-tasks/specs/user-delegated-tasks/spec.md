## ADDED Requirements

### Requirement: 委托 worker 并发执行必须有界且准入原子

统一委托 worker SHALL 支持有界的并发执行，使互不冲突的任务不必等待上一条长耗时生成完整收敛。worker 的最大并发 MUST 可配置且默认不得突破发布生成全局默认帽 3。

领取任务、检查 delegated ownership 与 external busy、准备 attempt、标记派发并转为 `executing` 的准入段 MUST 串行完成；只有当前任务已经建立可观察 ownership 后，worker 才能放行下一条准入。执行器的长耗时等待 MAY 并行。系统 MUST NOT 因并发领取使同 lane 两条任务双发，也 MUST NOT 让它们对称观察彼此后双双延后。

`waiting_approval` 的周期对账不是新生成，SHALL 独立进行且 MUST NOT 因另一条兼容 lane 在执行而停止。

#### Scenario: 三条兼容任务并发而各自独立收敛

- **WHEN** worker 依次领取三条 ownership 互不冲突的参照洗稿任务，配置并发为 3
- **THEN** 三条执行器 MAY 同时在途并各自写回 attempt 与任务终态
- **AND** 任一条先收敛 MUST NOT 释放、覆盖或篡改另外两条的 claim 与账本

#### Scenario: 同 lane 并发领取仍只有一条起跑

- **WHEN** 两条 delegated ownership 冲突的任务在相邻 poll 到达
- **THEN** 第一条 SHALL 先建立 executing ownership
- **AND** 第二条 SHALL 观察到该 ownership 后延后
- **AND** MUST NOT 出现两条都执行或两条都因对称冲突而延后的结果
