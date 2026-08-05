# Design — scope-risk-reconcile-to-owned-accounts

## D1 归属读用哪一口

对账器需要「这个账号归谁驱动」。系统里已经有唯一权威：`accounts.execution_target`，由 api 单写，automation 侧经窄读口 `AccountOwnershipPort` 取值——风控条件写的属主谓词用的就是它（`server.ts` 的 `ownershipPort.resolveExecutionTarget`）。

**MUST 复用同一口，MUST NOT 在对账器里另起一套读法**。两份读法漂开的现形方式不是报错，而是「条件写认为账号是我的、对账认为不是」，于是偏差检出与写权保护对不上，且没有任何机械手段会提醒。

对账器本身只接一个窄函数依赖 `ownerTargetFor(accountId) => 'dev' | 'ol' | null`，不认识 `AccountOwnershipPort` 这个类型——单测因此可以完全脱库。

## D2 三态怎么落

`resolveExecutionTarget` 是三态读（本 target / 另一 target / 读不到）。三态 MUST NOT 压成两态：

| 归属读结果 | 处置 | 理由 |
| --- | --- | --- |
| 等于本 target | 对账 | 唯一「内存与库结构上应当相等」的情形 |
| 等于另一 target | 跳过，计入 `skippedForeign` | 共用账本 + 只跟本进程记账的内存 ⇒ 不可能相等，判为偏差就是噪音 |
| 读不到 / 读失败 | 跳过，计入 `skippedUnknown` | 「未知」不等于「是我的」。按本 target 处理 = 把今天这批误报原样留下；且没有归属行 ⇒ 没有任何 target 在驱动它 ⇒ 也没人在写它的计数 |

读失败 MUST NOT 中断整轮对账（一个账号读不到不该让其余账号失去这道保护），但 MUST 计数。

## D3 防「过滤器把对账做成死代码」

这是本 change 自己最危险的失效模式：过滤条件写错（例如归属口未注入、target 常量拼错、三态判断反了），结果是**一条告警都不发**——而「一条告警都不发」和「一切正常」在现有信号面上完全一样。已有判例：同批加的守卫只覆盖作者在治的那条道，另半边全绿 6 天无人发现。

两道措施：

1. 每轮产出四个计数（`materialized` / `reconciled` / `skippedForeign` / `skippedUnknown`），`runOnce` 的返回值携带，不只打日志。
2. `materialized > 0 && reconciled === 0` 时**响亮记录一次**（warn 级，带四个计数）。这是「闸恒假」的现形通道。

不做告警升级（P 级告警）：这一形态的后果是可恢复的观测缺失，不是不可逆的对外写入；按加闸准入判据，记档即可，不配再加一条会自己刷屏的 P 级告警。

## D4 归属未注入时怎么办（fail-open 还是 fail-closed）

装配处可能拿不到归属读口（`ownershipMode === 'off'`：`AIDCP_RISK_OWNERSHIP_ENFORCE=false` 秒级回滚闸，或 api 直连口缺席）。此时：

**保持改动前行为——不过滤、全量对账。** 理由：归属强制本身已被关掉，此时系统退回「无谓词 upsert」的历史形态，跨 target 保护整体不生效；对账器单方面把自己关成静默，只会在保护最弱的时候再摘掉一层观测。装配处 MUST 在启动日志里写明对账是「按归属过滤」还是「全量（归属口缺席）」，让这两种形态在运行时可分辨。

## D5 告警的来源标注

`raiseRiskAlert` 是 automation 段风控告警的唯一收口。在它一处把本进程 `executionTarget` 拼进 detail 前缀，覆盖是结构性的，不依赖逐个告警点接线。

**不加 `alerts` 表的列**：那要一次迁移 + 面板读写两端跟进，而 dev / ol 共库，迁移期两侧版本不齐时新列会是空值——收益（列表可按 target 过滤）不抵这条路的代价。detail 前缀能立刻解决「看卡片分不清是谁报的」这个实际问题；真需要结构化过滤时再单独立项。
