# publish-generation-concurrency Specification

## Purpose
TBD - created by archiving change parallel-rewrite-drafts. Update Purpose after archive.
## Requirements
### Requirement: 并行单位为参照稿——键控单飞，两种粒度一套框架

发布生成段 SHALL 以「输入身份」为单飞键控制并发：参照洗稿轮以 `(accountId, sourceId)` 为键，自主创作轮（无参照稿）以 `(accountId)` 为键。同键同刻至多一轮在跑；跨键（含同账号不同参照稿）SHALL 允许并行，仅受容量帽约束。自主创作路径 MUST NOT 按参照稿粒度放开并行（其输入为确定性素材选取，同账号并发必产相似草稿）。键分量 MUST 使用平台侧稳定的 `sourceId`，MUST NOT 使用可变的精选行自增 id。

#### Scenario: 同账号跨参照稿并行放行
- **WHEN** 同一账号对两篇不同参照笔记（sourceId 不同）先后触发洗稿，容量帽未满
- **THEN** 两轮生成并行推进，各自独立落库待审、各发各的审批卡

#### Scenario: 同参照稿并发拒绝
- **WHEN** 同一账号对同一篇参照笔记（同 sourceId）在前一轮生成尚未结束时再次触发
- **THEN** 第二次触发被同步拒绝、返回 `duplicate_source` 机器原因码，MUST NOT 排队、MUST NOT 静默吞掉

#### Scenario: 自主路径保持账号单飞
- **WHEN** 某账号一轮自主创作（排期 / 飞书 `/publish` / 自动扳机）生成中，同账号又到达一次自主触发
- **THEN** 第二次以既有语义诚实跳过（飞书黄卡 / 排期让槽），MUST NOT 与第一轮并发生成；飞书 20s 重推的去重继续由该单飞闸兜底

#### Scenario: 同源串行重洗放行
- **WHEN** 某参照稿的前一轮已收敛（草稿已落库待审或已终态），运营对同一参照稿再次触发洗稿
- **THEN** 允许再生成一版（多版本对比属挑选场景的合法用法），堆积由账号在途帽兜量；MUST NOT 以「已有同源草稿」为由拒绝串行重洗

### Requirement: claim 检查与置位同步原子，claim 归属唯一且释放覆盖全程

单飞与容量判定 SHALL 在一个零 `await` 的同步段内完成「查键 + 查账号在途帽 + 查全局帽 + 置位」，判定与置位之间 MUST NOT 跨任何异步边界（关掉忙标志迟置位的 TOCTOU）。claim 的置位与释放 MUST 归同一个 owner 所有：置位后由其发起异步生成管线，释放在覆盖**含触发输入构建在内全程**的 finally 中执行——任何数据库瞬时错误或管线异常 MUST NOT 使键永久卡死。触发入口的异步结果通知链（如 console fire-and-forget 结果卡）SHALL 显式接到该轮的收敛结果上，MUST NOT 因入口改造而出现无人续接的静默失败。

#### Scenario: 并发双触发恰一成功
- **WHEN** 同键两次触发在同一瞬间到达
- **THEN** 恰有一次 claim 成功进入生成，另一次同步收到拒绝原因码；MUST NOT 两次都进入、也 MUST NOT 两次都被拒

#### Scenario: 输入构建阶段抛错不卡死键
- **WHEN** 一轮已 claim 的生成在构建触发输入阶段（数据库读取）抛出异常
- **THEN** claim 于 finally 释放、该键立即可再触发；该轮以失败收敛并沿结果通知链如实上报

#### Scenario: 触发结果卡有人续接
- **WHEN** console 触发的一轮洗稿以 skipped / failed 收敛
- **THEN** 既有的异步结果卡链对该轮如实补黄 / 红卡，MUST NOT 因触发入口经由新的同步 claim 方法而丢失结果通知

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

### Requirement: 编排器多轮簿记——run 注册表与向后兼容观测

发布编排器 SHALL 以 run 注册表（键为抗碰撞随机 runId）簿记并行轮次，每轮持有独立的黑板 context；一轮收敛只摘除自己的注册项，MUST NOT 影响其他在跑轮（禁止「先结束轮抹掉在跑轮」的单槽行为）。对外观测 SHALL 演进为多 run 形状且向后兼容：保留旧的单快照字段并**显式定义聚合规则**（取最新启动的 running 轮；无 running 则最近一次终态——失败态 MUST NOT 被并行 running 轮永久遮蔽），新增 runs 数组带每轮账号 / 类型 / 参照稿 / 启动时刻 / 快照。

#### Scenario: 两轮并发簿记互不干扰
- **WHEN** 两轮生成并发推进、先启动的一轮先收敛
- **THEN** 先收敛轮摘除自己的注册项，后一轮的 context 与观测快照不受影响地继续

#### Scenario: 旧版消费端不白屏
- **WHEN** console 尚未升级、仍按旧单快照形状消费观测接口
- **THEN** 旧字段按聚合规则持续有值、页面正常渲染，MUST NOT 因新增字段或多轮并发而白屏或冻结

### Requirement: 超时僵尸轮不得落库——中止标记与落库点拦截

生成管线超时或中止后，该轮 SHALL 被打上中止标记；落库待审与发审批卡的执行点 MUST 检查该标记——已对外报 failed 的轮次 MUST NOT 再落库草稿、MUST NOT 再发审批卡（一次触发两个结局是静默假成功变体，且僵尸落库会穿透单飞键与容量帽）。已发生的模型 / 生图消耗如实记账为沉没成本。

#### Scenario: 超时后在途角色完成不产生第二结局
- **WHEN** 一轮生成在总闸超时被判 failed，其在途模型调用随后返回、下游角色继续接力到落库点
- **THEN** 落库点检查中止标记后放弃写入与发卡，该轮全局唯一结局为 failed；同键随后的新触发不受僵尸干扰

### Requirement: 进程重启对在途生成轮诚实失败

单飞 claim、容量帽与 run 注册表为进程内存态。进程重启时在途生成轮 SHALL 直接丢失且不自动恢复——console 无产出、无审批卡即真相，运营重新触发即可；MUST NOT 假装恢复或伪造终态。已落库待审草稿不受影响（持久层承载）。

#### Scenario: 重启后干净起步
- **WHEN** 云端进程在若干生成轮在途时重启
- **THEN** 重启后 claim 表与注册表为空、可立即接受新触发；在途轮无任何残留半成品被误当有效草稿

### Requirement: 委托入口不得重新串行化跨来源洗稿

结构化 Edge、console 或 API 洗稿先进入统一委托层时，委托层 MUST 保留发布生成段的输入身份并发语义：参照洗稿以 `(accountId, sourceId)` 为单飞 lane，不同稳定 `sourceId` SHALL 能并行进入 PublishScheduler，且继续受账号在途帽与全局生成帽约束。委托层 MUST NOT 以同账号 `actionFamily=publish` 的粗粒度 ownership 把跨来源洗稿重新串行化。

参照洗稿完成生成、候选已持久化并进入 `waiting_approval` 后，该任务 MUST NOT 继续占用参照洗稿生成 lane；同源串行重洗与跨来源新洗稿均可继续按容量帽准入。无参照稿的自主发布仍按账号单飞。

#### Scenario: 三条 Edge 洗稿委托同时进入生成

- **WHEN** 同一账号从 Edge 连续提交三条不同稳定 `sourceId` 的洗稿委托，账号与全局容量均空闲
- **THEN** 三条任务 SHALL 能同时进入发布生成段
- **AND** MUST NOT 因另一条同账号发布任务处于 planning 或 executing 而得到 `delegated_ownership_busy`

#### Scenario: 待审批洗稿不阻塞另一来源

- **WHEN** 一条参照洗稿已生成候选并处于 `waiting_approval`，同账号另一 `sourceId` 的洗稿委托到达
- **THEN** 新任务 SHALL 可立即申请发布生成 claim
- **AND** MUST NOT 等待前一候选被批准、驳回或下发终结

#### Scenario: 普通稿仍保持账号单飞

- **WHEN** 同账号已有一条无参照稿的自主发布委托处于生成或既有 ownership 保护期
- **THEN** 第二条自主发布委托 SHALL 等待
- **AND** MUST NOT 因委托 worker 支持并发而同时生成相似普通稿

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

