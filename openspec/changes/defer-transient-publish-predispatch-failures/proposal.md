## Why

发布指令序列器把「提交前失败」分了五档并逐档写明语义（`aidcp-cloud/src/publish-agent/command-sequencer.ts:76-84`），
其中 `failed_before_submit` 的注释是「提交前真失败——可安全烧待审重投」。**下发段没有照这份分档走。**

`publish-dispatcher.ts:825-859` 只对 `submitted_unconfirmed`（`:825`）与 `preempted`（`:839`）单独分支，
其余全部落进末尾的 `else`（`:849-859`）：写 `failed` 终态、`markApprovalProgress('consumed')` 消耗授权、
`recordSeqFailure()` 计入熔断。而那个 `else` 的注释写的是「序列中途失败（页面状态未知）」——
**它描述的情形和它实际接住的情形不是一回事。**

两层缺陷叠加，且都属「静默假失败」：

1. **外层——下发段不认分档。** 一个**已被序列器证明零派发**的失败，被当成「页面状态未知」处置。
   `classifyFailureOutcome`（`:370-383`）的三态优先级保证：走到 `failed_before_submit` 时
   `submitted || submitDispatchedNow` 必为假、`yield_timeout` 已被前置摘走——**提交点确定没跨过**。
2. **内层——`failed_before_submit` 本身是兜底返回值**（`:383` 的无条件 `return`）。
   结构性终局的原因（`content_too_long` / `all_images_failed` / `not_approved`）与
   可恢复的原因（提交前的导航抖动、页面未就绪、探测超时）**共用同一个值**，下发段拿到后无从分辨。

**代价不是理论值。** 熔断阈值默认 2（`publish-dispatcher.ts:154`）。同账号连撞两次提交前抖动，
该账号**整批已批准草稿**停止 drain，必须运营重新点批准才能清除。**一次网络抖动的代价是重审一批稿。**
且每次都白烧一份授权签名与已生成的正文/配图。

本 change 是 `docs/stop-or-continue.md` 判定规则的第一处落地：Q0（提交点已由序列器证明未跨过）→
Q2（重新加载后重来有没有可能不同）→ 分流。

## What Changes

- **拆掉内层兜底桶**：`failed_before_submit` 拆成两个终局值——**结构性提交前失败**（重来必然同样结果：
  正文超长、配图全败、未授权）与**可恢复提交前失败**（提交点确定未跨过，且重来有可能不同）。
  **MUST NOT 保留一个「其余全归它」的无条件返回**：未识别的提交前原因 MUST 以具名的「未识别」形态露出，
  并按可恢复处置（判据：无法证明重来结果相同），同时把原始原因串带进日志。
- **下发段按分档处置**：可恢复提交前失败复用 `preempted` 那条已验证的零副作用路径——
  保持 `pending_approval`、**保留授权签名**（不 `voidApprovalSignal`、不 `markApprovalProgress('consumed')`）、
  FB 素材 `release` 而非 `quarantine`、**不计熔断**、事件驱动重投。
- **重投必须有上限**：可恢复提交前失败的自动重投次数 SHALL 有界（默认 2，env 可配）。
  耗尽后落 `failed` 终态，且通知与日志 MUST 写「重试 N 次未成」而不是「做不到」。
  **恢复预算 MUST 只由失败消费**——被抢占重投与槽位等待重试不得递减该计数（它们各有自己的计数）。
- **熔断只计页面状态未知的那一档**：`recordSeqFailure` MUST NOT 被可恢复提交前失败触发。
  熔断守的是「连环烧稿」，而可恢复档根本不烧稿。
- **`submitted_unconfirmed` / `yield_timeout` 的处置一字不动**：跨过提交点（或证明不了没跨过）
  仍然绝不重投。本 change MUST NOT 放宽任何成功判据、MUST NOT 延长任何确认等待窗口。

## Capabilities

### Modified Capabilities

- `publish-dispatch-resilience`: 下发失败的副作用分界由两档（离线 / 序列失败）细化为三档
  （零副作用可恢复 / 零副作用结构性 / 页面状态未知），并明确熔断只计最后一档；
  新增可恢复档的有界自动重投与「未识别原因不得进兜底桶」。

## Impact

- **aidcp-cloud（唯一受影响仓）**
  - `src/publish-agent/command-sequencer.ts`：`PublishSequenceResult['outcome']` 增值；
    `classifyFailureOutcome` 的末位无条件 `return` 改为按原因分流 + 具名未识别档。
  - `src/publish-agent/publish-dispatcher.ts`：新增可恢复档分支（对齐 `:839-848` 的 `preempted` 样板）；
    `settleFacebookMedia` 的档位映射（`:547` 的联合类型）同步；熔断计数排除该档；重投计数与上限。
  - 测试：`test/publish-agent/` 增分档与重投上限断言；验收测试须证明 `AC-PUB-*` 未被削弱
    （未授权仍绝不发布、跨过提交点仍绝不重投）。
- **协议不变**：本 change 不新增 / 修改任何边云消息，不触碰协议四处同步的任何一处。
- **数据库不变**：`outcome` 是进程内联合类型，不落库枚举。
