## MODIFIED Requirements

### Requirement: 并发启动 / 停止 MUST 错峰串行以避开 AdsPower 本地 API 限频

外壳对 AdsPower 本地 API 的生命周期调用（`browser/start` / `browser/stop` / `browser/active`）SHALL 经一条外壳级串行队列**错峰下发**（相邻调用间隔 ≥ 1.1s），使「全部启动」/「全部停止」/ 逐环境启停 / 重登不会在同一时刻突发多次而触碰 AdsPower ~1req/s 的本机限频。

**启动 SHALL 进一步串行到「起完一个再起下一个」**：队列一次只放行一个环境的浏览器启动，等它**真正起来**（浏览器就绪 + 云端连接建立）或**诚实失败**之后，才放行下一个。MUST NOT 仅靠固定间隔就并发拉起多个环境的冷启。某一环境的启动失败 MUST NOT 阻塞队列中其余环境。

#### Scenario: 全部启动逐个完成
- **WHEN** 运维点「全部启动」拉起 N 个离线环境
- **THEN** 外壳一次只启动一个，等它就绪或失败后再启动下一个，界面如实呈现「k/N 已就绪 · 正在启动第 k+1 个」

#### Scenario: 单环境启动失败不阻塞队列
- **WHEN** 队列中某环境启动失败（如分身未登录致诚实非零退出）
- **THEN** 该环境如实进入错误态，队列继续放行其余环境的启动，互不牵连

### Requirement: 全部启动 MUST 做内存上限预检、超限诚实拦阻而非拖垮

每个有界面（headful）环境约占 ~700MB 内存（可配估值）。外壳 SHALL 在**每一次会打开浏览器的动作**之前预检「预计在跑数 × 单环境内存估值」是否超过本机可用内存——**不只是「全部启动」**：单环境启动、冷待机唤醒、崩溃重起、手动任务临时启动，**全部 MUST 经过同一道准入闸，任何路径 MUST NOT 绕过**。

预计超限 SHALL **诚实拦阻**（提示并暂缓 / 让运维确认），MUST NOT 直接超额拉起而致换页抖动 / OOM 把某环境浏览器杀掉、再让它看起来像「莫名其妙的不稳定」。

#### Scenario: 预计超限时诚实拦阻
- **WHEN** 任一开浏览器路径（全部启动 / 单启 / 唤醒 / 重起 / 手动任务）预计在跑数 × 单环境估值超过本机可用内存
- **THEN** 外壳诚实拦阻并说明内存不足，MUST NOT 无提示地超额拉起

#### Scenario: 唤醒路径不得绕过准入
- **WHEN** a cold-standby wake would push memory past the admission ceiling
- **THEN** the wake is refused honestly with a memory reason, and MUST NOT proceed on the grounds that it is "only a wake"

## ADDED Requirements

### Requirement: 浏览器槽位池 SHALL 按内存封顶、并以 1:2 限制可设账号数

外壳 SHALL 维护一个**浏览器槽位池**，槽位上限 = ⌊可用内存 ÷ 单环境内存估值⌋（估值默认 700MB，均可配）。同时打开的浏览器数 MUST NOT 超过槽位上限。

单机**可设置账号数上限 SHALL 为槽位上限的 2 倍**（1:2）。超过该比例时外壳 SHALL 诚实告警，MUST NOT 静默接受。

槽位 SHALL **仅由冷待机自然释放**（长确定性等待 → 释放浏览器层）。外壳 MUST NOT 抢占、MUST NOT 踢掉正在运行的环境来腾槽位。

#### Scenario: 槽位满时诚实拒绝
- **WHEN** 一个开浏览器请求到来而槽位已满、且无环境可自然释放
- **THEN** 外壳诚实拒绝并说明槽位已满，MUST NOT 排队无限等待，MUST NOT 踢掉在跑环境

#### Scenario: 停泊释放的槽位可被他人取用
- **WHEN** an environment enters cold standby and releases its browser
- **THEN** its slot returns to the pool and the next queued browser-opening action may take it

#### Scenario: 账号数超过 1:2 时告警
- **WHEN** 运维配置的账号数超过槽位上限的 2 倍
- **THEN** 外壳如实告警存在永远排不上的风险，MUST NOT 静默接受

### Requirement: 两个上限 SHALL 可在客户端设置里显式设定

**并发浏览器数上限**与**最大账号数上限** SHALL 都能在桌面客户端的设置页里直接设定，MUST NOT 只能经启动环境变量配置——分发出去的安装包里运营改不了环境变量。

取值优先级 SHALL 为 **界面设置 > 启动环境变量 > 按可用内存自动推算**。留空 / 0 SHALL 一律解释为「自动」，MUST NOT 被解释为「上限 0」（那等于整台机器停摆）。

界面 SHALL 如实呈现当前生效值**及其来源**（自动推算 / 启动参数 / 手动设定）与自动推算值；这两个数的算法 SHALL 只有一处权威（外壳主进程），渲染层只显示、MUST NOT 自行重算。

账号上限 SHALL 允许被设到槽位的 2 倍**之上**（1:2 是缺省比例、不是物理常数），但外壳 MUST 诚实告警「部分账号可能长期排不到槽位」，MUST NOT 静默接受。

设置改动 SHALL 立即对后续的开浏览器请求生效，MUST NOT 要求重启核心进程或整个应用才生效。

#### Scenario: 界面设定压过环境变量
- **WHEN** 设置里给定了并发上限，同时启动环境变量也给了一个不同的值
- **THEN** 以界面设定为准；界面同时如实说明「按内存自动推算会是多少」

#### Scenario: 留空即自动
- **WHEN** 两个上限在设置里留空
- **THEN** 并发上限 = ⌊可用内存 ÷ 单环境估值⌋、账号上限 = 2 × 并发上限，MUST NOT 被当成 0

#### Scenario: 账号上限设过 1:2 时诚实告警
- **WHEN** 运维把账号上限设到并发上限的 2 倍以上
- **THEN** 设置接受该值，同时如实告警部分账号可能长期排不到浏览器槽位

### Requirement: 串行启动队列 SHALL 覆盖全部开浏览器路径并按优先级放行

**所有会打开浏览器的动作** SHALL 经同一条串行启动队列：自动续场恢复、冷待机唤醒、崩溃后重起、手动任务临时启动、排期任务唤醒。队列 SHALL 一次只放行一个，且**内存准入闸位于队列内部**。

队列放行优先级 SHALL 为：**手动任务 > 带任务的唤醒 > 普通续场恢复**；同级 FIFO。

排队等待 SHALL 计入调用方的唤醒死线。若排队即可判定无法在死线内完成，队列 SHALL 让调用方**立即诚实失败**，MUST NOT 让它排到死线超时。

**定时唤醒 MUST NOT 零抖动齐发**：到点的多个环境经此队列**逐个**启动，MUST NOT 在同一时刻一起冷启。

#### Scenario: 零点羊群被队列拆开
- **WHEN** 多个账号的日配额在上海零点同时释放、唤醒定时器同刻到点
- **THEN** 队列逐个放行冷启（起完一个再起下一个），MUST NOT 同一秒并发拉起全部

#### Scenario: 手动任务插队但不踢人
- **WHEN** 一个手动任务需要浏览器而队列中已有等待项
- **THEN** 它被放到队首优先放行，但 MUST NOT 关闭或抢占任何正在运行的环境

### Requirement: 手动任务 SHALL 新开浏览器执行后关闭、绝不驱逐他人

手动任务在目标环境浏览器缺席时 SHALL：插到启动队列队首 → 启动浏览器 → 执行 → 执行完成后关闭该浏览器归还槽位。

手动任务 MUST NOT 通过驱逐 / 踢掉任何其他正在运行的环境来获取槽位。若内存或槽位确实不足以再开一个浏览器，手动任务 SHALL **诚实报告失败**，MUST NOT 静默排队、MUST NOT 假装已执行。

#### Scenario: 手动任务临时开关浏览器
- **WHEN** an operator triggers a manual task on a parked environment
- **THEN** a browser is launched at the head of the queue, the task runs, and the browser is closed afterwards, returning the slot

#### Scenario: 内存不足时手动任务诚实失败
- **WHEN** a manual task needs a browser but memory admission refuses
- **THEN** the manual task fails honestly with a memory reason, and no running environment is evicted
