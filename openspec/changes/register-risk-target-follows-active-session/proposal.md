## Why

2026-07-23 的 cloud 提交 `6b6b542`（"risk-target-follows-active-session: account ownership follows the active
connection"，已是 `origin/master` 祖先）把「账号归属」的设计整个反转了，但控制仓里**没有任何 OpenSpec 记录**
（全仓 grep 零命中）。

- **原设计**（随 `risk-state-cross-process-integrity` 上线）：先到先得 + 非属主拒绝——归属只在
  `accounts.execution_target` 为空时条件写占位；非属主的边缘握手以 `execution_target_mismatch` 拒绝；另有
  一个显式改归属端点；并有 observe / enforce 两档观察期开关。
- **现网实际**：归属跟随当次活跃连接——每次握手把归属**无条件改写**为正在接入的 target；握手**不再**因
  归属不同被拒（`execution_target_mismatch` 在 cloud master 的 `src` 与 `test` 中均零命中）；改归属端点整条
  删除、命中通用 404；模式收敛为 `enforce | off` 两态；跨进程止血整体下沉到 `risk_state` 的条件写
  （0 行 → 作废先写方这一次写 → 驱逐缓存 + 告警）与握手接管时的控制器驱逐。

不补登的后果是具体的，而且是本仓已经吃过亏的那一类：

1. **引用悬空**。2026-07-25 刚归档进 `interaction-risk-gating` 的「账号风险状态的写入者在任一时刻全局唯一」
   明文写着「每个账号在任一时刻 MUST 只归属一个 `executionTarget`（见 `same-account-parallel-safety`）」，
   而 `same-account-parallel-safety` 主 spec 里 `execution_target` 是 0 命中——引用指向一个不存在的约束。
2. **完全无登记**。被取代的那份 delta 已随归档删除（控制仓 `3f10bf8`），现网这套行为在 spec 层面**既无旧文
   也无新文**。此时任何人做「按 spec 回归」，都会照直觉把「非属主拒绝」当成应有行为写回来——那正是本次要
   消灭的形状。
3. **三条反直觉不变量只靠注释保护**：记账口**故意不设**归属闸（切换瞬间飞在半路的回执照记同一本账）、
   管理后台风控写**故意**账号级放行不看归属、以及「作废先写方」只作废**这一次写**而不是停摆这个写者。

本 change 是**纯补登**：不改任何 sub-repo 代码，只把 `origin/master` 上已逐条核实的行为写成 spec 增量。
**设计决策的原始论证已不可考**——`6b6b542` 的提交信息只记录了做什么、没有记录为什么这样取舍；本 change
不追认理由，只固化事实。

## What Changes

- 给 `same-account-parallel-safety` 补 8 条 `## ADDED Requirements`，覆盖已核实的现网行为：归属跟随当次连接
  （握手无条件改写、不再有归属类拒绝）、切换后驱逐并从库重建控制器、状态写带属主谓词且 0 行作废本次写、
  「作废先写方」不等于停摆该写者、归属只分裂写权不分裂计数账本、管理后台风控写为账号级且无改归属端点、
  归属在读侧仅为只读展示、条件写两态回滚闸。
- 给 `interaction-risk-gating` 出一条**窄 MODIFIED**：仅修正「账号风险状态的写入者在任一时刻全局唯一」中
  Scenario「归属变更不清零也不翻倍当日额度」的 **WHEN 句**——现网已无任何「显式改归属」入口，归属只由握手
  接管而变更。该需求其余正文与 Scenario 逐条核对后仍准确，原样保留。
- **不改任何 sub-repo 代码**。实装动作只有「逐条核对 spec 与代码一致」与「补三条已实装但无用例的测试」；
  核对出入一律**以代码为准改 spec**，不为凑 spec 改代码。

## Capabilities

### Modified Capabilities

- `same-account-parallel-safety`: 在现有 4 条（多节点共享单一控制器、按账号去重、记账串行化、同节点重连顶替）
  之外，新增账号归属跟随活跃连接这一整套约束，承接 `interaction-risk-gating` 已有的那条引用。
- `interaction-risk-gating`: 一处 WHEN 措辞订正，去掉已不可达的「显式改归属」触发条件。

## Impact

- Affected repos: `aidcp`（本 OpenSpec change，纯文档）+ `aidcp-cloud`（仅补 3 条测试，无行为改动）。
- **无部署**：所描述行为 2026-07-23 起已在 dev 运行（cloud `6b6b542`）。归档即把增量并入主 spec。
- 已知落差已在 `tasks.md` 登记、本 change 不处理：面板首页汇总调的是注册表上标 `@deprecated` 的可写口；
  告警 sink 绑定窗口内触发的驱逐告警只进日志不落库；条件写谓词跨属主读 `accounts`（拆库待裁决）。
