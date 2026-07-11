## Why

Facebook 加群成败当前靠**多语词表**判「已加入/待审」（edge `classifyCtaLabel` + `MEMBER_CTA_LABELS`/`PENDING_CTA_LABELS`/`MEMBER_MEMBERSHIP_PHRASES`，云端裁判镜像同表）。词表覆盖不全 + 不对称，已致真机事故：加成功→按钮翻成词表没有的本地语「已加入」→边缘诚实但错误报 `join_failed`→云端**重复加群**（false-negative）。C1（[[facebook-locale-pin-en-us]] 界面钉英文）治新号，治不了存量号/登出态这条语言无关缝。本 change 是分层方案 L3：给加群成败校验补一个**语言无关的结构真值**——进群后是否出现可聚焦发帖/评论框——作为主判，词表降为只正向补充。

**零协议改动**：加群回执的观测走松类型通道（`ActionCompletedPayload.observation?: unknown` / `postObservation?: unknown`），补结构信号是 edge→cloud 观测内容 + 云端解析的改动，**不动两份 `protocol.ts` 的 parity 类型、不触 `AC-PROTO`、不需与协议类 change 串行**。因此能独立先上、快速消灭重复加群。加群「点击动作解耦」（clickToken）是另一条**触协议热点**的独立 change（[[见 facebook-join-actuation-decouple]]），与本 change 解耦、不绑定。

## What Changes

- **后置校验补结构主判**：判「加进去没」补一个语言无关信号——点击后群主体内出现**可聚焦发帖/评论输入框**（`[contenteditable][role="textbox"]` 这类成员态结构信号）。
- **防新的 false-positive（关键，两轮评审收紧）**：绝不用「裸 composer 存在」当已加入真值（公开组可能对非成员也渲染发帖框/「写点什么…」诱导框）：
  - **承重闸 = 点后单帧事实**：判 joined 要求点后观测**有可聚焦 composer 且群主体内无可见 Join CTA**（非成员点后 Join CTA 仍在→不判 joined）。这是对两次调用架构稳的单帧事实。
  - **跃迁佐证**：composer 跃迁用**同一次 `click=true` 导航内**的 pre/post 观测对（非另一次独立 observe 调用）；
  - **pending 先判**：pending/问卷先于 joined 判（Join→Pending + composer 判 pending）；
  - observe 期**裸 composer 不得**翻 `already_member`（仍需词表命中，或 composer + 无可见 Join CTA）。
  - **结构字段透传云端裁判**（接线要点）：结构字段 + 同调用 pre 观测喂给云端 `evaluatePostClick`（现只收 post 观测），否则云端仍按未知语种成员标签回 `failed`、重复加群不止。
- **词表降为只正向补充**：本地语成员/待审词表命中 = 正向加固；缺失**绝不否决**结构确认、**绝不**独自作为无跃迁时的成功依据。红线不动：结构跃迁与词表**都无**正向命中时 MUST NOT 报成功（不假成功）。
- **不做（YAGNI）**：不删多语词表（留作正向补充 + 云端裁判稳定网）、不给按钮上视觉、不引 FB 私有前端 JSON 当真值、不在本 change 里改点击动作定位（那是 clickToken change 的事）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-group-join-resilience`: 加群成败校验补「进群后可聚焦发帖/评论框」这一语言无关结构真值为主判（用**跃迁 + 成员可供性翻转**判据防非成员组假成功），多语词表降为只正向补充、绝不否决、绝不无信号假成功；observe 期裸 composer 不得翻 `already_member`。既有 resilience 红线（待审问卷不销毁、租约瞬态、退避分级等）不变。

## Impact

- 代码（**无协议 parity 改动**）：
  - edge `src/facebook/join-executor.ts`：观测采集群主体内「可聚焦发帖/评论框存在」（M3：子树判别群内发帖框 vs 无关输入框），写入 `observation`/`postObservation`（松类型通道，非 `protocol.ts` parity 字段）；后置校验改跃迁 + 可供性翻转主判。
  - cloud 加群裁判：解析观测结构字段主判成败；词表保留为正向补充 + drift-guard 不变。
- 部署：edge dev land + cloud dev（安全序列）。因无协议 parity 改动，`AC-PROTO` 不涉及；仍跑全量 `test` + `typecheck`。
- 真机验收：落 backlog 不阻塞码级（判定准确率门：结构主判消灭重复加群、composer 子树判别不误伤非成员组）。
- 依赖：无新增。
