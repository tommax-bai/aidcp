## MODIFIED Requirements

### Requirement: automation-owner 动态事实必须由完整 snapshot 承重并由 event outbox 加速
系统 SHALL 由 automation owner 为全局周掩码、Edge presence、publish in-flight、captcha availability
与 automation config-mirror health 生成 runtime snapshot。状态变化 SHALL 向
automation 属主 `event_outbox` 写入 target-scoped `sync_read.changed` 通知；通知仅作唤醒和积压重放，
完整 snapshot SHALL 是崩溃恢复与漏通知自愈的承重来源。

变更检测 SHALL 只由**事实本身**的变化触发。参与变更检测的 payload MUST NOT 包含观测时刻、
序号或其他每次观测都会变化而不描述事实的字段；投递时刻 SHALL 只由 envelope 的 `asOf` 承担。
payload digest MUST 继续覆盖**整份** payload —— 消除 churn 的正确形态是把非事实字段移出 payload，
MUST NOT 改成「digest 排除若干字段」（那会让同一 cursor 下的 payload 漂移不再可检出）。

#### Scenario: runtime 状态变化触发快速刷新
- **WHEN** automation 的 Edge presence、in-flight、captcha 或 health generation 前进
- **THEN** automation SHALL 为同一 target/stream 写入或合并一条持久 outbox 通知
- **AND** api 收到通知后 SHALL 拉取不低于该 generation 的完整 snapshot

#### Scenario: 事实未变化的周期观测
- **WHEN** owner 按周期重新观测某 runtime stream，而事实内容与上一次完全相同
- **THEN** generation MUST 保持不变且 MUST NOT 写入任何 outbox 通知
- **AND** 该 stream 的通知写入速率 SHALL 与事实变化频率同阶，MUST NOT 与观测周期同阶

#### Scenario: 恒定事实的长期观测
- **WHEN** 某 runtime stream 的事实在很长时间内保持恒定（含内容恒为空的合法稳态）
- **THEN** 该 stream 在此期间写入的通知条数 SHALL 为零
- **AND** 系统 MUST NOT 依靠周期性写入通知来维持该镜像的新鲜度

#### Scenario: outbox 通知丢失但周期 snapshot 成功
- **WHEN** 状态已经变化但通知写入或 LISTEN 唤醒失败
- **THEN** api SHALL 由下一轮完整 snapshot 收敛到 owner 当前值
- **AND** 系统 MUST NOT 依赖每条 runtime delta 都曾成功投递

#### Scenario: outbox handler 未成功应用快照
- **WHEN** api 因结构、target、网络或 apply 错误未成功应用相应 snapshot
- **THEN** automation 的 `(consumer,target,topic)` cursor MUST 停在该通知之前
- **AND** 后续轮询 SHALL 重放积压而不是确认丢弃

### Requirement: 配置镜像健康必须按消费进程分域并保留传输新鲜度
api SHALL 直接投影 api 本地 refresher health；automation SHALL 生成只描述 automation 本地镜像的
health snapshot。面板聚合 SHALL 带 `sourceService`、source `asOf` 与 delivery state。
automation health 的 delivery 已陈旧时，api MUST 将该整段标为 unavailable，而不是继续展示旧条目
为 fresh。

面板聚合所用的 source `asOf` SHALL 取自 delivery envelope 的 `asOf`。
automation health payload MUST NOT 自带观测时刻字段 —— 那是投递元数据而非镜像健康事实，
放进 payload 会让「健康度变没变」的判据恒真。

#### Scenario: automation health 传输陈旧
- **WHEN** api 上一次收到的 automation health snapshot 已超过 freshUntil
- **THEN** 面板 SHALL 将 automation health 标为 unavailable/stale
- **AND** 即使 payload 内旧条目写着 fresh，也 MUST NOT 对外宣称 automation 镜像健康

#### Scenario: api 本地与 automation 远端状态不同
- **WHEN** api 本地镜像 fresh 而 automation 某 gate mirror stale
- **THEN** 面板 SHALL 分别展示两个 source service 的真态
- **AND** MUST NOT 聚合成一个全局 fresh 结论

#### Scenario: automation 本地没有在跑的镜像刷新器
- **WHEN** automation 进程内并没有配置镜像刷新器（该刷新器属 api）
- **THEN** automation health payload SHALL 如实报告「未启用、无条目」
- **AND** MUST NOT 为了让该段看起来健康而编造条目表

## ADDED Requirements

### Requirement: 镜像新鲜度续期 MUST NOT 依赖变更通知通道

每个消费进程的周期 owner fetch 间隔 SHALL **严格小于**该 stream 的新鲜期窗口，
使任一 stream 只靠周期 fetch 即可保持 fresh。变更通知 SHALL 只承担降低变化可见延迟的作用，
MUST NOT 成为某条 stream 保持新鲜所必需的一环。

判据是「**假设该 stream 的通知全部消失，它是否仍能长期保持 fresh**」；
答案为否即违反本要求，MUST NOT 以「实际上通知一直有」为由放行。

#### Scenario: 长期无变化的 stream 保持新鲜

- **WHEN** 某 stream 的事实长期未变化，因而完全没有变更通知产生
- **THEN** 消费方 SHALL 仅凭周期 owner fetch 的续鲜路径保持该镜像 fresh
- **AND** 该镜像 MUST NOT 出现周期性 stale 抖动

#### Scenario: 刷新周期与新鲜期相等

- **WHEN** 周期 fetch 间隔被配置为等于或大于新鲜期窗口
- **THEN** 该配置 MUST 被判为不合法
- **AND** MUST NOT 依靠某条 stream 恰好有高频通知来掩盖这一点

#### Scenario: 就绪度判据受抖动污染

- **WHEN** 某镜像参与进程就绪度判定
- **THEN** 它的 fresh/stale 状态 SHALL 反映事实与传输的真实情况
- **AND** MUST NOT 因轮询周期与新鲜期卡在边界而周期性地把进程报成 not_ready
