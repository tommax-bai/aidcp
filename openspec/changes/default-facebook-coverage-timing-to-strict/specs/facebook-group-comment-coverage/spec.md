## MODIFIED Requirements

### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage selector SHALL, per account, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined. When no joined group satisfies warmup/cooldown and the relaxed fallback is enabled, the selector SHALL fall back to joined groups ordered least-recently-commented; the relaxed result MUST be flagged for human review and MUST still exclude non-joined or left groups.

**放开兜底的默认极性 SHALL 为关闭**，且 MUST 只能由显式配置开启。缺少配置、配置为空或取值无法识别时，选群口 SHALL 走严格模式：一个合规群都没有就本轮不评论，MUST NOT 退而求其次去评一个不满足预热或仍在冷却中的群。

该默认值 MUST 由代码承载，MUST NOT 仅依赖运行时配置来维持。理由是失效模式：运行时配置文件不进版本库、部署时被显式排除，因此「它应该是关的」这件事在代码库里没有任何记录；换机、重建或从更早备份恢复都会让它静默回到开启，而且**不报错、不告警、日志里也看不出来**。把默认极性放在代码里，是让这条安全姿态跟着版本走、而不是跟着某一台机器上的一个文件走。

放开兜底 SHALL 被理解为一次**具名的临时放宽**，而不是一个常备档位：它在最需要预热与冷却的时刻把这两道闸丢掉，因此开启它 MUST 是一个显式且可追溯的决定。

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage selector runs for an account
- **THEN** it never comments in a group that account has not joined

#### Scenario: Relaxed fallback still chooses least-recently-commented joined groups
- **WHEN** all of an account's joined groups are inside warmup or cooldown and relaxed fallback is enabled
- **THEN** the selector chooses from `status='joined'` groups ordered by least-recently-commented and flags the result as relaxed for review

#### Scenario: 未配置时走严格模式
- **WHEN** 放开兜底的配置缺失、为空或取值无法识别，且账号名下所有已加入群都处在预热期或冷却中
- **THEN** 本轮不评论、不加群，如实回报无可用目标，MUST NOT 选中任何不合规的群

#### Scenario: 只有显式开启才放开
- **WHEN** 运维显式把放开兜底配置为开启，且账号名下所有已加入群都不合规
- **THEN** 选群口按最久没评排序选出一个已加入群，并把结果标记为放开态交人把关
