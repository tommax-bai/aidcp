# Tasks

> 本 change 覆盖 3 条评审发现：**H2**（登录态降级即终局、无退避无恢复）、**M3**（探针把限流/抖动/零发帖统统报成「接口改版」）、**M2**（端点熔断只有开、没有关，且被非 schema 原因触发）。
>
> 拥有的文件：`src/wechat-channels/auth-session.ts`、`src/wechat-channels/feature-flags.ts`、`src/wechat-channels/probes/black-box-probe.ts`（+ `api-client.ts` 两处 throw 的错误类别，见 proposal 协调项）。
> **禁止触碰**：`src/comm/protocol.ts`（热点文件，本 change 不新增任何协议枚举）、`src/wechat-channels/runtime.ts`（归并行 change `wechat-edge-runtime-honesty`）。

## 0. 前置

- [x] 1.1 在当前 aidcp-edge master 上重验本 change 每条发现的前提是否仍成立（文件/行号可能已漂移，按行为而非行号核对）。任一条已被他人修复或已失去前提 → 在本文件如实登记「已失效 + 依据」并跳过，**绝不为了勾选而重复实装**。 <!-- aidcp-edge 3a70981 Revalidated H2/M3/M2 on clean master 0d38116; all premises still held. -->
  - H2 核对点：`auth-session.ts` 的 `markApiFailure` 中 `rate_limited` / `schema_changed` / `permission_denied` / `transient_network` 四支是否仍**只做一次 transition 到 `degraded`、不安排任何重试或退避**；`degraded` 是否仍让 `WechatCapabilityState.effective()` 全线翻 false。
  - M3 核对点：`auth-session.ts` 中 probe 未通过是否仍**一律**转 `degraded` + `WECHAT_SCHEMA_CHANGED`；`black-box-probe.ts` 的 `probeEnabledReads` 是否仍返回裸 boolean、真实原因是否仍只写进 `ProbeResult.reasonCode` 而无人读；零发帖账号（`listPosts` 成功但 `items` 为空）是否仍走 `NO_READ_PROBE_SCOPE` → 返回 false → 降级。
  - M2 核对点：`feature-flags.ts` 的 `WechatEndpointCircuitBreaker` 是否仍**只有 `open()` 没有任何关闭/复位/过期**；`api-client.ts` 中「HTTP 200 但非 JSON」与「响应超限」是否仍抛 `schema_changed`（即仍会经 `onSchemaChanged` 打开熔断器）。
- [x] 1.2 `git -C /Users/baitianxing/codes/aidcp-edge branch --show-current` 必须为 `master`；开发在 `../aidcp-edge.wt/wechat-edge-auth-recoverable` worktree 内进行。 <!-- aidcp-edge 3a70981 Canonical stayed on master; isolated worktree was created and cleaned after landing. -->

## 1. aidcp-edge — 探针原因诚实分类（M3）

- [x] 2.1 在 `probes/black-box-probe.ts` 定义 `WechatProbeOutcome`，取值仅两种：`{ ok: true }` 或 `{ ok: false; reasonCode: InteractionAuthReasonCode }`；`reasonCode` 只取 `protocol.ts` 既有的 8 个枚举值之一，**不得新增枚举**。 <!-- aidcp-edge 3a70981 Added the typed outcome without modifying protocol.ts. -->
- [x] 2.2 `probeEnabledReads` 返回类型由 `Promise<boolean>` 改为 `Promise<WechatProbeOutcome>`；捕获到的错误按类别映射：`rate_limited→WECHAT_RATE_LIMITED`、`transient_network→INTERACTION_UPSTREAM_UNAVAILABLE`、`permission_denied→WECHAT_PERMISSION_DENIED`、`schema_changed→WECHAT_SCHEMA_CHANGED`、`auth_expired→WECHAT_AUTH_REQUIRED`、`challenge_required→WECHAT_CHALLENGE_REQUIRED`、`identity_mismatch→WECHAT_IDENTITY_MISMATCH`；无法归类的未知错误 → `INTERACTION_UPSTREAM_UNAVAILABLE`（**MUST NOT** 回落到 `WECHAT_SCHEMA_CHANGED`）。既有的 `ProbeResult` 证据记录保持不变。 <!-- aidcp-edge 3a70981 Preserved evidence rows and mapped every known category plus unknown fallback. -->
- [x] 2.3 零可探范围改判：`probeComments` 中 `listPosts` 成功但无可用 postId 时，返回 `{ ok: true }`（授权链路健康），**不** `markProbePassed('commentsRead')`（fail-closed：commentList 未验证过，能力保持关闭），`ProbeResult` 仍记 `status:'gated'` + `NO_READ_PROBE_SCOPE`。 <!-- aidcp-edge 3a70981 Zero-post auth stays healthy while commentsRead remains gated. -->
- [x] 2.4 同步 `auth-session.ts` 中 `WechatAuthCoordinatorOptions.probeEnabledReads` 的类型；两处调用点（`initialize()` 与 `runBrowserAuthentication()`）改为：`ok:true` 继续既有成功路径；`ok:false` 时用 **outcome 携带的 reasonCode** 降级，而非硬编码 `WECHAT_SCHEMA_CHANGED`。 <!-- aidcp-edge 3a70981 Both call sites consume the structured reason. -->
- [x] 2.5 不动 `probeDm` 的「零会话即 markProbePassed」既有行为（与本 change 的 fail-closed 取向不一致，但不属本批发现，**不在本 change 内顺手改**）；如实登记为待评估项，见 6.2。 <!-- aidcp-edge 3a70981 Behavior intentionally unchanged; follow-up recorded as backlog 96.3. -->

## 2. aidcp-edge — 降级可恢复与有限退避（H2）

- [x] 3.1 在 `auth-session.ts` 内实现单实例恢复计时器：同一时刻最多一个恢复尝试在飞行中；`WechatAuthCoordinatorOptions` 新增可注入的退避参数与 `setTimeoutImpl`/`clearTimeoutImpl`（或复用既有 `sleepImpl`/`nowImpl` 风格），以便单测不靠真实时钟。 <!-- aidcp-edge 3a70981 Added one timer/flight with injectable backoff and clock hooks. -->
- [x] 3.2 `markApiFailure` 的四类降级各自带上恢复计划（初始间隔 → 指数退避 → 到达上限后按上限**持续**重试，恢复通道永不归零）： <!-- aidcp-edge 3a70981 Implemented category defaults, caps, retryAfterMs and capped continued retry. -->
  - `rate_limited`：初始间隔取 `error.retryAfterMs`（平台已给出就必须遵循），缺省 30s；上限 5min。
  - `transient_network`：初始 5s；上限 2min。
  - `permission_denied`：初始 5min；上限 30min。
  - `schema_changed`：初始 10min；上限 60min。
- [x] 3.3 恢复尝试的内容 = `api.getIdentity(session)` + `probeEnabledReads(session)`，**MUST NOT** 打开浏览器（沿用既有冻结契约「MUST NOT 自动反复打开浏览器」）。成功 → 回到 `api_only_running`（若 `manualBrowserVisible` 为真则回 `browser_open`）、重置退避、`identityMatches=true`。 <!-- aidcp-edge 3a70981 Recovery verifies identity and probes only; browser is never opened. -->
- [x] 3.4 恢复尝试失败时按新错误类别重新规划：仍是临时类 → 退避加倍后继续；升级为 `auth_expired`/`challenge_required`/`identity_mismatch` → 取消恢复计时器、走既有的浏览器重认证/终局路径（这三类本来就已有恢复入口，不重复造）。 <!-- aidcp-edge 3a70981 Temporary failures reschedule; structural failures cancel and hand off. -->
- [x] 3.5 生命周期收口：`clear()`、`disable()`、`reopen()`、以及任何一次成功认证 MUST 取消在飞行中的恢复计时器并重置退避；`disable()` 后 MUST NOT 再有恢复尝试（运营显式停用是有人工入口的终局态）。计时器不得阻止进程退出（`unref` 或等价处理）。 <!-- aidcp-edge 3a70981 Lifecycle generation cancellation and unref are enforced. -->
- [x] 3.6 `identity_mismatch` 保持不自动重试（结构上做不到：会话属于另一个账号），恢复入口仍是客户重新登录 —— 在代码注释里点明这是**唯一**没有自动恢复的失败类别（`disabled` 除外）。 <!-- aidcp-edge 3a70981 Identity mismatch waits for explicit customer re-login and is documented in code. -->

## 3. aidcp-edge — 端点熔断可复位（M2）

- [x] 4.1 `feature-flags.ts` 的 `WechatEndpointCircuitBreaker`：`open()` 记录打开时刻；`isOpen()` / `capabilityAvailable()` 按 TTL 判定过期（默认 10min，构造参数可注入 + 可注入 `nowImpl` 供单测）。TTL 是**无需任何外部接线的兜底恢复通道**。 <!-- aidcp-edge 3a70981 Added default 10-minute TTL with injected clock. -->
- [x] 4.2 新增 `close(endpoint)` 与 `reset()`；`snapshot()` 只返回**当前仍未过期**的端点（不得把已过期的熔断当成仍在生效对外上报）。 <!-- aidcp-edge 3a70981 Added close/reset and filtered expired snapshot state. -->
- [x] 4.3 探针成功即复位：`black-box-probe.ts` 中某能力探针通过时，对该链路涉及的端点调用 `capabilityState.breaker.close(...)`（`WechatCapabilityState.breaker` 已是 public readonly，无需改 `runtime.ts`）。 <!-- aidcp-edge 3a70981 Successful post/comment/DM probes close only their observed endpoints. -->
- [x] 4.4 `api-client.ts` 两处改判为可重试的临时上游故障，使其不再经 `onSchemaChanged` 打开熔断器：① 「HTTP 200 但 body 非 JSON」（WAF 拦截页/平台故障页）→ `transient_network`、`retryable=true`；② `readLimitedText` 的两处「响应超限」→ `transient_network`、`retryable=true`。真正的 `schemaChanged()`（字段缺失/类型不符）行为不变，仍打开熔断。 <!-- aidcp-edge 3a70981 Non-JSON and both size-limit paths are transient; real schema drift remains unchanged. -->

## 4. aidcp-edge — 测试（补测克制：只覆盖关键行为）

- [x] 5.1 `test/wechat-channels/auth-session.test.ts`：注入假时钟，断言「一次 `rate_limited`（带 `retryAfterMs`）→ degraded → 按 retryAfterMs 安排恢复 → 恢复尝试成功 → 回到 `api_only_running` 且全程未开浏览器」。 <!-- aidcp-edge 3a70981 Added deterministic retry-after recovery coverage. -->
- [x] 5.2 同上：断言「`transient_network` 连续失败时退避递增且不超上限、恢复通道不停」，以及「`disable()` 后不再有恢复尝试」。 <!-- aidcp-edge 3a70981 Added capped persistent backoff and disable cancellation coverage. -->
- [x] 5.3 `test/wechat-channels/auth-session.test.ts`：断言「探针因限流失败 → 快照 reasonCode 为 `WECHAT_RATE_LIMITED`，**不是** `WECHAT_SCHEMA_CHANGED`」；「零发帖账号 → 授权态保持 `api_only_running`、不降级、`commentsRead` 能力保持 false」。 <!-- aidcp-edge 3a70981 Added honest reason and zero-post fail-closed coverage. -->
- [x] 5.4 `test/wechat-channels/contract-and-flags.test.ts`：断言「熔断 TTL 到期后 `capabilityAvailable` 自动回 true」与「探针成功即刻复位该端点」。 <!-- aidcp-edge 3a70981 Added TTL expiry, snapshot cleanup and probe-close coverage. -->
- [x] 5.5 `test/wechat-channels/api-client.test.ts`：断言「HTTP 200 返回 HTML → 抛 `transient_network` 且 `onSchemaChanged` **未**被调用」。 <!-- aidcp-edge 3a70981 Added HTML and response-limit classification regression coverage. -->
- [x] 5.6 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全绿。 <!-- aidcp-edge 3a70981 land-change rerun: acceptance 23/23, full 1664/1664, typecheck passed; gated real-machine E2E was not run. -->

## 5. 收口

- [x] 6.1 提交 + 推送 aidcp-edge master（集成前 rebase 到最新 master，遇 non-ff 一律 rebase 重来、绝不 force）。本 change 无云端改动、**不涉及 ECS 部署**；边缘为客户端代码，不在本 change 内出安装包。 <!-- aidcp-edge 3a70981 Fast-forward pushed to origin/master; no ECS deploy and no installer build. -->
- [x] 6.2 真机验收项登记到 `docs/real-machine-acceptance-backlog.md` 新簇（写入时取当前末尾簇号 +1，避免与并行 session 撞号）：① 真机限流/断网复现 → 确认收件箱能自愈、客户无需重扫码；② 零发帖新号接入 → 确认不再误报「接口改版」；③ 待评估：`probeDm` 零会话即判 probe passed 是否是 fail-closed 缺口（见 2.5）。 <!-- aidcp-edge 3a70981 Registered as backlog cluster 96 with all real-machine items explicitly open. -->
- [x] 6.3 `openspec validate wechat-edge-auth-recoverable --strict` 通过后归档。 <!-- aidcp-edge 3a70981 Strict OpenSpec validation passed before archive. -->

> 台账格式：每条 task 完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注。**sha 必须取自已推送的提交**（判据：`git merge-base --is-ancestor <sha> origin/master`），不得编造、不得填悬空提交。
