## MODIFIED Requirements

### Requirement: 容量有界且诚实快拒——账号在途帽与全局并发帽

生成段 SHALL 设两层容量帽且帽满一律同步诚实拒绝，MUST NOT 排队：① 每账号在途帽（默认 20，env 可配）约束“生成中轮数 + 已落库待审数”之和，判定 MUST 纳入同步 claim 段（在途 claim 计数精确、落库数允许轻微滞后）并 MUST 覆盖全部触发入口（console / 飞书 / 排期 / 自动扳机）——只闸单一入口会被其余入口结构性击穿；② 全局并发生成帽（默认 3，env 可配）保护模型与生图供应商。自主生成仍按账号单飞，同账号同刻最多 1 轮；在全局容量空闲时，同账号不同参照稿的洗稿轮最多可并行 3 轮。帽满原因码：账号帽满 `publish_capacity`、全局帽满按入口复用既有拒绝形态（console `publish_busy`、飞书 skipped 黄卡、排期让槽）。

#### Scenario: 账号在途帽满诚实拒绝

- **WHEN** 某账号“生成中 + 待审”合计已达 20（或 env 覆盖后的帽值），又一次洗稿触发到达
- **THEN** 同步返回 `publish_capacity`，console 提示引导先处理（批准 / 驳回）存量待审草稿；MUST NOT 排队或静默丢弃

#### Scenario: 排期入口同样受帽约束

- **WHEN** 某无人审的账号排期扳机逐小时触发、其在途待审草稿数已达账号帽
- **THEN** 后续排期触发被帽拒绝而不再产新草稿，MUST NOT 无界堆积草稿与审批卡

#### Scenario: 三篇跨来源洗稿并行

- **WHEN** 全局没有其他生成轮占槽，同一账号依次触发三篇不同 `sourceId` 的洗稿
- **THEN** 三轮 SHALL 同时进入生成；第四轮 SHALL 因全局并发帽同步返回 `publish_busy`

#### Scenario: 普通稿仍保持账号单飞

- **WHEN** 某账号已有一轮自主生成在跑，同账号再次触发普通稿生成
- **THEN** 第二轮 SHALL 以 `already_running` 诚实跳过，MUST NOT 因全局帽提高到 3 而并行生成相似普通稿

#### Scenario: 全局帽满按入口语义拒绝

- **WHEN** 全局并发生成数已达帽值，console 又触发一轮洗稿
- **THEN** 同步返回 `publish_busy`（语义=并发已满非全局串行），用户稍后重试即可；飞书与排期入口分别走黄卡与让槽语义
