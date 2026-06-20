## ADDED Requirements

### Requirement: 写操作只经拥有该写的进程内对象，绝不 raw UPDATE，绝不乐观假成功

来自管理后台的所有写操作 SHALL 只经过已经拥有该写的进程内对象（风控 controller / 调度器 / 共享命令闭包 / 共享审批写回），MUST NOT 用 raw SQL UPDATE 绕过这些所有者，MUST NOT 报告乐观成功。每个写 SHALL 返回写后真态（如 `getState()` 写回、`{written}`/`{alreadyDecided}`、真实下发边缘数），且拒绝/无效 SHALL 与成功**可区分地**呈现。

#### Scenario: 写后回真态
- **WHEN** 任一面板写操作完成
- **THEN** 接口返回从所有者对象读回的写后真实状态，而非提交即返回的乐观「ok」

#### Scenario: 绝不 raw UPDATE 风控
- **WHEN** 面板需要改风控状态或档位
- **THEN** 改动经风控 controller 进行，面板层不持有也不使用对风控状态表的 raw UPDATE 能力

### Requirement: 风控 STATUS 改动经 applySignal 且限于枚举化运营信号种类

风控**状态**（normal/warned/restricted/frozen）改动 SHALL 经 `RiskController.applySignal`，且 MUST 限于一组枚举的、命名的运营信号种类（如 `manual_restrict` / `manual_freeze` / `operator_override_recover`）；接口 MUST 拒绝枚举外的种类。状态机是约束图而非 setter：时间门控的或非法的迁移 SHALL 被拒绝，且该拒绝 MUST 经 `getState()` 写回**作为「refused」**清晰呈现，绝不静默 no-op 成「ok」。`operator_override_recover`（绕过恢复窗口）MUST 要求审计理由。

#### Scenario: 非法迁移渲染为 refused
- **WHEN** 运营发起一个被恢复窗口时间门控拒绝的状态迁移
- **THEN** 接口返回 `getState()` 写回并把结果标为「refused」，状态未变，绝不报成功

#### Scenario: 枚举外种类被拒
- **WHEN** 状态写请求带了枚举集合之外的信号种类
- **THEN** 接口拒绝该请求，不调用 `applySignal`

### Requirement: 风控 QUOTA-TIER 改动经新 setQuotaLevel，controller 保持唯一写者

风控**档位**（conservative/normal/aggressive，`quotaLevel` 字段）改动 SHALL 经一个新的一等方法 `RiskController.setQuotaLevel(level)`，它 MUST 在 controller 内部完成「改 + 持久（`saveState`）+ emit」，使 controller 保持对风控状态的唯一写者。MUST NOT 用 `applySignal` 改档位（状态机从不触碰 `quotaLevel`，那样会静默无事发生），MUST NOT 从面板对 `quotaLevel` 做 raw UPDATE。

#### Scenario: 档位经 controller 单写
- **WHEN** 运营从面板改账号档位
- **THEN** 改动经 `RiskController.setQuotaLevel` 完成内部改+持久+emit，并返回写回的新档位

#### Scenario: 不借 applySignal 改档位
- **WHEN** 收到改档位请求
- **THEN** 系统调用 `setQuotaLevel` 而非 `applySignal`，避免「选了档位却什么都没变、也不报错」的静默无效

### Requirement: 每账号风控写串行化，无丢更新

`RiskController` SHALL 为每账号维护一个内部 async mutation 队列，使「迁移 + 持久」与「setQuotaLevel + 持久」原子。**所有**写者——live `record()` 触发的 `applySignal`、验证码协调器、新的 Web 状态/档位写——MUST 经该队列。并发的手动写与 live 写 MUST NOT 互相覆盖（无 lost update）。

#### Scenario: 并发手动写与 live 写串行
- **WHEN** 一个手动 `applySignal` 与一个 live `quota_exceeded` `applySignal` 几乎同时到达同一账号
- **THEN** 二者经 mutation 队列串行组合，最终状态是合法串行结果，无一方的 `saveState` 覆盖另一方

### Requirement: 发布审批写回经唯一共享函数、first-writer-wins、共享逐字节契约

Web 发布审批 SHALL 与飞书审批调用**同一个** `writeApprovalSignal(requestId, approved, payload)`，写**逐字节一致**的 `/tmp/aidcp-publish-approve-<requestId>.json`（AC-PUB-*），用卡铸造时的同一个 `requestId`。写 MUST 是 first-writer-wins 的原子写（temp + rename，`O_EXCL`）：第二个决定（Web vs 飞书 vs 重复点击）MUST 快速失败、接口返回 `{alreadyDecided:<approved>}`。接口 SHALL 返回 `{written:true}` 或 `{alreadyDecided}`，MUST NOT 返回 `{published:true}`（edge 对文件的动作才是真相）。系统 MUST NOT 接 `publish-executor.ts` 那条缺 `requestId`、属未激活 `activate-publish-pipeline` 的审批分支。

#### Scenario: 二次决定不覆盖首个
- **WHEN** 一个 `requestId` 已被飞书审批写定，随后 Web 又对同一 `requestId` 提交一个决定
- **THEN** 第二次写快速失败，接口返回 `{alreadyDecided}` 携首个决定值，信号文件不被覆盖

#### Scenario: 返回 written 而非 published
- **WHEN** Web 审批成功写出信号文件
- **THEN** 接口返回 `{written:true}`，绝不返回 `{published:true}`（是否真的发布由 edge 读取信号后决定）

### Requirement: pause/resume/dispatch 复用共享命令闭包并回报真实结果

账号 pause/resume（及 V1 的 dispatch start/stop）SHALL 复用一组共享 `CommandActions` 闭包，飞书命令路由与面板 `POST /api/accounts/:id/command`（及 `/dispatch`）共用同一实现。pause/resume 的运营暂停态 MUST durable（经 `accounts.status`），与传输层 `pausedEdges`（验证码硬停）保持区分。接口 MUST 回报真实结果——真实下发到几个在线 edge、或为何未下发的原因，绝不乐观假成功。

#### Scenario: 暂停回报真实下发事实
- **WHEN** 运营从面板暂停一个账号且其边缘当前不在线
- **THEN** 接口诚实返回「已记录暂停意图、当前 0 个在线 edge 收到」，而非假报已生效

#### Scenario: 运营暂停与验证码硬停区分
- **WHEN** 一个账号被运营暂停（`accounts.status`）
- **THEN** 该暂停与传输层 `pausedEdges` 验证码门控相互独立，二者不互相覆盖语义
