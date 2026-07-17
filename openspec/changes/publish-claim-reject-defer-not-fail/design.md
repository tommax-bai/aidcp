## Context

见 proposal 的四步链路。核心事实两条：

1. **死条件**：`executors.ts:133` 的 `outcome.result === 'blocked' && /…|already_running/` 里，后三个分支永不可达——`already_running` / `publish_capacity` / `publish_busy` 由 `tryClaim` 产出，被 `doTrigger` 包成 `{ status:'skipped', failureReason }`、再由 `triggerDelegated` 包成 `{ result:'triggered' }`（`publish-scheduler.ts:504-514` + `:399-418`）。`blocked` 只由人设未绑 / 风控产出。
2. **热重试**：落到 `{ kind:'failed', retryable:true }` → `worker.ts:258-260` `nextEligibleAt = now + 1_000`；NL 发帖默认 `maxAttempts=2` → 约 2 秒烧光。

约束：`publish-scheduler.ts` 是热点文件（历史上被两个 change 争用），须按 CLAUDE.md §7 串行。

## Goals / Non-Goals

**Goals:**

- 撞车 / 到帽 → 延后重试，帖子最终发出去，而不是 2 秒后报失败。
- 判定基于机器可读形状，不靠中文文案正则。
- 清掉死条件，别让下一个人照着它推理。

**Non-Goals:**

- 不改 `delegated-terminal-failure-reason` 已落地的原因透出（那条负责「说清楚」，本条负责「别走到那」）。
- 不动风控 / 配额语义（`risk_*` 今天已正确走 deferred，保持）。
- 不改 `externalBusy` 的既有粗筛。

## Decisions

### D1：形状从 scheduler 给，而不是委托层猜

倾向让 `tryClaim` 拒绝走 union 里**已存在但目前无人产出**的 `{ result: 'skipped'; reason }`，或在 `triggered` 上带机器可读的 `claimReject?: 'already_running' | 'publish_capacity' | …`。

理由：今天 `executors.ts:133` 对 `outcome.reason` 做子串匹配，而 `triggered` 分支的 `failureReason` 是**中文句**（`已有一轮发帖编排在运行中，本次未触发（already_running）`）。靠文案匹配天然易碎——措辞一改就静默失效，且**两端都是裸 string、typecheck 抓不到**（CLAUDE.md §2 点名的同类盲区）。

**否决**：只在委托层把正则改成匹配 `status === 'skipped' && /already_running/`。能修好当下，但把易碎的文案耦合原样留着，且 `result:'skipped'` 这个 union 变体继续无人产出、继续误导读代码的人。

### D2：退避间隔按「等的是什么」

撞车等的是另一轮编排跑完（分钟级，`terminalWaitMs` 默认 4 分钟量级）。沿用风控那支的 60s 量级即可，`now + 1_000` 只是空转。

### D3：`duplicate_source` 与账号在途帽一并纳入

`tryClaim` 的四个拒绝码（`already_running` / `duplicate_source` / `publish_capacity` / 并发已满）性质相同——都是「等一会儿就能做」。proposal 里逐条列出，勿只修 `already_running`。

## Risks / Trade-offs

- **[改成 deferred 后任务拖到 deadline 才失败，反而更晚才告诉运营]** → 可接受且更诚实：deadline 终态现在会发卡并带原因（`delegated-terminal-failure-reason` 已落 `b5a3302`）。且大多数撞车会在几分钟内让开、帖子真发出去。
- **[误把结构性失败归成延后 → 无限拖到 deadline]** → spec 已写负向回归（人设未绑仍须诚实判不可重试失败）。判定用**枚举白名单**，不是「非 blocked 即延后」的补集。
- **[热点文件冲突]** → 动工前 `openspec list` 复核 `publish-trigger-and-apply` 是否仍活跃；在飞则串行等待。
