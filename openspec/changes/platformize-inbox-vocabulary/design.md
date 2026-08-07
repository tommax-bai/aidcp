# Design — 词汇批 6a：IM 族改名 `wechat_channels.inbox.*` + 应答族约定定案

## Context

视频号 IM 族是协议里最后一片带 `interaction` 前缀的消息（批 5 已把浏览互动义的 5 条改成平台段对象名并删旧名）。该族 15 条消息横跨 edge sidecar 运行时（`src/wechat-channels/`）与 automation 的 interactions 编排（send-orchestrator / offboarding-service），带三条 durable-outbox 往返链（sync / reply / offboard），批 7 为其 `.result`/`.ack` 命名留了显式豁免、约定本批定夺。四路探查（2026-08-07）已拿到全部发送点 / 处理点 / 陷阱的 `文件:行` 证据。

## Goals / Non-Goals

**Goals**：① 「interaction」一词从协议消息命名空间退役；② IM 族获得平台段（`wechat_channels`），与批 4/5 的编法 A 一致；③ `.result`/`.ack` 族约定定案并写进语法蓝图；④ 全部 typecheck 盲区逐点点名改，零静默失效。

**Non-Goals**：不改任何载荷结构、不改 outbox 语义、不改身份闸行为、不动 kernel、不动 native 引擎与 manifest digest、不改 TS 类型标识符（`Interaction*` 前缀的接口 / 类型名不上线缆，保留）、不动 api 仓（RBAC 键冻结）、不动 content 仓（零占用）。

## 1. 名表（15 旧 → 15 新，唯一权威）

平台段取值＝kernel `PlatformId` 枚举成员 `wechat_channels`（`platform-types.ts:17`）；域词 `inbox`＝视频号私域收件箱运行时（产品面即「收件箱」）。**纯前缀换名**：`interaction.` → `wechat_channels.inbox.`，尾段逐字保留。

| # | 旧名 | 新名 | 方向 |
| --- | --- | --- | --- |
| 1 | `interaction.auth.status` | `wechat_channels.inbox.auth.status` | edge → cloud（自发上报） |
| 2 | `interaction.sync.batch` | `wechat_channels.inbox.sync.batch` | edge → cloud（等 ack） |
| 3 | `interaction.sync.ack` | `wechat_channels.inbox.sync.ack` | cloud → edge |
| 4 | `interaction.sync.request` | `wechat_channels.inbox.sync.request` | cloud → edge |
| 5 | `interaction.reply.send` | `wechat_channels.inbox.reply.send` | cloud → edge |
| 6 | `interaction.reply.result` | `wechat_channels.inbox.reply.result` | edge → cloud（一型两用） |
| 7 | `interaction.reply.result.ack` | `wechat_channels.inbox.reply.result.ack` | cloud → edge |
| 8 | `interaction.reply.reconcile` | `wechat_channels.inbox.reply.reconcile` | cloud → edge |
| 9 | `interaction.reply.reconcile.result` | `wechat_channels.inbox.reply.reconcile.result` | edge → cloud |
| 10 | `interaction.auth.reopen` | `wechat_channels.inbox.auth.reopen` | cloud → edge |
| 11 | `interaction.browser.control` | `wechat_channels.inbox.browser.control` | cloud → edge |
| 12 | `interaction.runtime.controls` | `wechat_channels.inbox.runtime.controls` | cloud → edge |
| 13 | `interaction.offboard.command` | `wechat_channels.inbox.offboard.command` | cloud → edge |
| 14 | `interaction.offboard.result` | `wechat_channels.inbox.offboard.result` | edge → cloud（等 ack） |
| 15 | `interaction.offboard.ack` | `wechat_channels.inbox.offboard.ack` | cloud → edge |

`auth` / `browser` / `runtime` 三个子域是**收件箱运行时**的授权 / 浏览器显隐 / 开关面，不是收件箱内容操作——仍归同一前缀（同族同编码，规则四；该族物理上就是一个 driver / 一个 sidecar / 一个运行时）。

## 2. 决策：`.result`/`.ack` 转正为第三族约定（批 7 豁免的到期裁决）

**裁定**：留痕写外发的 durable-outbox 往返族保留 `.result` / `.ack` 尾段，作为与「请求＝祈使动词」「edge→cloud 应答与自发事实上报＝过去分词事实形」并立的**第三族约定**写进 `docs/edge-command-grammar.md` 族约定表。适用成员：IM 族三条链、`publish.command.result`、`publish.approval_action.result` / `publish.draft_image_remove.result`、`captcha.assist.click_result`（assist 子族本就整体豁免）。

依据（探查坐实的三个结构事实，任一都足以否决「拉平成过去分词」）：

1. **三条 `.ack` 全是 cloud→edge 方向**（`sync.ack` / `reply.result.ack` / `offboard.ack`，均为「exact accepted/duplicate 后 Edge 才清 outbox」的出箱确认）。过去分词规则只约束 edge→cloud 应答，对 cloud→edge 确认语义不适用；强改会把方向语义改反。
2. **`interaction.reply.result` 一型两用**：`runtime.ts:244` fire-and-forget 发送与 `:258` correlated request（等 `.result.ack`）共用同一消息型。按「上报 vs 请求」拆名＝拆类型＋拆 outbox 重放路径，对 CLI 层清晰零收益。
3. **嵌套尾段是被依赖的结构**：`edge-client.ts:1019` 靠 `reply.result.` 带尾段前缀区分 `reply.result` 与 `reply.result.ack`（裸 `string` 入参，typecheck 不护）。保留尾段结构＝前缀匹配点全部机械换前缀即可，不引入新的区分逻辑。

**代价与接受理由**：`wechat_channels.inbox.reply.result.ack` 达 6 段，是全协议最长名。接受——名长是「平台段 + 真子族 + 往返链」三层真实结构的如实编码，规则里没有段数上限；捏短它的每种方案都要么丢结构（合并型）要么造新词（另立尾段），均劣于直白。

**同时定案**：`sync.request` / `offboard.command` 两个名词尾段请求名**保留历史形**，登记为本族约定的一部分（往返族的请求端允许名词尾段，与祈使族区分）——不借本批顺手「祈使化」，避免在 8 类盲区上扩大改动面（改一个字段名的收益撑不起 30+ 文件的二次过账）。

## 3. 静默失效点清单（typecheck 全程无感，逐处点名改）

| # | 位置 | 改法 |
| --- | --- | --- |
| 1 | edge `edge-client.ts:761-772` 主动命令白名单（10 条 `env.type ===` or-链） | 逐条换新名，对名表核 |
| 2 | edge `edge-client.ts:1016-1023` `interactionExtensionCapability` 前缀匹配（`:1019` `reply.result.` / `reply.reconcile`；`:1022` `offboard.`；入参裸 `string`） | 前缀换 `wechat_channels.inbox.` 形 |
| 3 | edge `command-diagnostics.ts:31+` `ACTIVE_COMMAND_TYPES`（untyped Set，`:72-81` 10 条）/ `:112-120` `FIXED_SUMMARIES`（`Record<string,…>` 键）/ `:279` `=== 'interaction.reply.send'` 裸串 | 三张结构逐条 |
| 4 | edge `protocol-validation.ts:25-39` 扁平名单数组 + `:571-585` switch 分派（**只改 switch 不改数组＝allowlist 静默全拒**） | 数组与 switch 成对改 |
| 5 | edge `renderer.js:2588` `'interaction.reply.send': '发送互动回复'` 纯 JS 键 | 换新名 |
| 6 | edge 中文错误串内嵌消息名：`sync-common.ts:26,28,31`、`connector.ts:153` | 随文改 |
| 7 | automation `handler.ts:1230,1242,1278,1298,1310,1333` 中文错误串内嵌消息名 | 随文改 |
| 8 | automation `ws-server.ts:394-395` 验证码暂停旁路集（`env.type ===` 链，漏改＝暂停开始吞 `runtime.controls`/`browser.control`） | 逐条换 |
| 9 | automation `automation-edge-access.ts:316` `startsWith('interaction.offboard.')` | 换新前缀 |
| 10 | edge `runtime.ts:318,337` offboard cleanup-only 守卫（`env.type ===` 链嵌布尔表达式） | 逐条换 |
| 11 | fixture：`wechat-channels-interaction/v1/ws/` 21 份 JSON `"type"` 字段 × automation/aidcp-cloud 两仓 + 两份 `contract-fixtures.test.ts` 文件名→消息名对照表 + `:94` `startsWith('interaction.')` | 目录改名 `wechat-channels-inbox/`，两仓逐字同步 |

## 4. 同形异义不改（sed 红线）

- **握手能力串**（wire 值，改了断线上客户端协商）：`interaction_inbox_v1` / `interaction_reply_recovery_v1` / `interaction_offboarding_v1` / `interaction_runtime_controls_v1` / `interaction_browser_control_v1` / `interaction_test_data_reset_v1`（protocol.ts:304-309、kernel `interaction-types.ts:4-9`、edge `wechat-channels/driver.ts` 等）。批 7 已立先例：握手协商串与消息名脱钩。
- **edge 驱动能力串**（`PlatformCapability`，带点、长得最像消息名）：`interaction.comment.read` / `interaction.comment.reply` / `interaction.dm.read` / `interaction.dm.send_text` / `interaction.dm.send_image`（`platform/driver.ts:23-27`）。
- **api 仓 RBAC 权限键**（持久化于角色目录 JSON）：`interaction.config.view/.edit/.publish/.preview`、`interaction.dm.view_full`、`interaction.audit.view`。
- **outbox topic 值**：`interaction.audit_event`（kernel `interaction-audit-outbox.ts:32`、automation topic roster）。
- **EventBus 事件名**：`interaction.occurred` / `interaction.completed` / `interaction.skipped`（云端进程内事件，改了断浏览闭环）。
- **Electron IPC / 客户 HTTP 通道名**：`interaction.auth.request` / `interaction.workspace`（edge `operation-registry.ts:99-100`，`CLIENT_OPERATION_REGISTRY`，非协议消息；`interaction.auth.request` 尤其易被误当 `auth.status` 的配对请求）。
- **TS 类型标识符**：`InteractionMessageType`（协议 `:312`，载荷字段类型 text/image/unknown）、`InteractionPlatform`、各 `Interaction*Payload` 等——不上线缆，批 5 载荷接口保留同例。
- **原因码 / DB**：`interaction_inbox_only`（kernel 调度目录）、`interaction_*` 全部表名、`INTERACTION_BROWSER_PROFILE_IN_USE` 等 reason code。
- **automation 内部模块 / 目录名**：`src/interactions/`、`InteractionRuntimeControlsDelivery` 等标识符不改。

## 5. 验证与变异纪律

- 四道集成复验：protocol-parity（两份 protocol.ts 逐字节）+ operation-registry-parity（两份登记表键集与描述符）+ action-key-parity（本批零改动、跑通即证未误伤）+ 两仓 typecheck。
- 仓内：protocol-contract 穷举表（15 名整表换新）、edge-client 白名单路由回归断言、contract-fixtures 对照表两仓一致。
- **变异纪律（先 commit 再变异）**：全绿 → commit → 变异（① 白名单删一条→路由测试必红；② protocol-validation 数组删一条→validation 测试必红；③ fixture 对照表改一个文件名→contract-fixtures 必红）→ 复原回绿。
- aidcp-cloud 集成仓测试跑其 `test/interactions/` 桶确认 fixture 同步。

## Risks / Trade-offs

- [两批并行同碰热区] → 集成串行、本批先落；后落批 rebase（批 5+7 实证流程）。热区清单：两份 protocol.ts、两份登记表、edge-client、command-diagnostics、renderer.js、protocol-contract 测试。
- [前缀匹配点裸 string，改漏无编译错] → §3 清单逐条点名 + 变异验证覆盖三类代表点。
- [fixture 双仓漂移] → 同一批内两仓逐字同步 + contract-fixtures 对照表断言；集成仓测试作最终闸。
- [切换窗口旧客户端] → 与批 1–5+7 同一未出包窗口，新名 fail-closed 拒收在执行前，无重复对外写入风险。

## Migration Plan

worktree 并行开发（edge / automation 各一）→ 双仓测试 + typecheck → 串行集成（本批先落）→ 四道 parity → dev 部署（沿批 5 安全序列）→ tasks.md 回写 → 真机项登记 backlog → archive。回滚＝revert 两仓提交 + dev 重部署（无 kernel、无 DB、无 digest，回滚面最小）。

## Open Questions

（无——`.result`/`.ack` 裁决即本批交付物之一，已在 §2 定案。）
