## Why

词汇蓝图批 6 的 IM 半边（`docs/edge-command-grammar.md` §6.2「IM 族、发布与收尾」行、§6.3 批次表）：视频号 IM 族整体改名，「interaction」一词从协议消息命名空间整体退役（批 5 已删其浏览互动义，本批删其 IM 义，一词一义恢复）；同时兑现批 7 立下的到期约定——`.result`/`.ack` 应答族的命名约定在本批定夺。

前置核实（2026-08-07，四路并行探查，修正蓝图两处滞后）：

- **IM 族实为 15 条、非蓝图行写的 10 条**（蓝图行漏计 `interaction.auth.status` 与嵌套应答）：8 条 cloud→edge、7 条 edge→cloud。以两份 protocol.ts 穷举（`:146-161`）为准。
- **平台段取值＝`wechat_channels`**（kernel `platform-types.ts:17` 权威枚举 `'xiaohongshu' | 'facebook' | 'wechat_channels'`），蓝图行文的 `wechat.` 是简写；批 4/5 已确立「平台段以代码枚举为准」（`xiaohongshu` 非 `xhs`），本批同理。
- **本批不命中 kernel**：kernel 内全部 `interaction` 字面均为冻结值（能力串常量、outbox topic `interaction.audit_event`、DB 表名注释、`interaction_inbox_only` 原因码），无协议消息名；transport-gate 豁免表零 IM 成员。**kernel 不出版本**（批 6 的 kernel 出版压力全在另半边 change）。
- **云端 command-bridge 零占用**：`wechat_channels` 在 bridge 三张表里刻意为空映射（视频号无浏览器驱动动作），IM 族走 send-orchestrator / offboarding-service / automation-main 直发，不经 bridge——动作关联键三表（action-key-parity 闸）本批零改动。
- **`interaction.reply.send` 身份闸豁免已是结构性的**：手抄救援清单 `IDENTITY_RESCUE_OPERATIONS` 已删除，豁免由说明书类别（`platform_api_automation`，`identity: 'bound_account'`）推导。改名只换登记表键名、豁免集合成员不变，不存在「静默扩」的通道（交接线头 4 就此收口）。

## What Changes

- **15 条 `interaction.*` → `wechat_channels.inbox.*` 纯前缀换名**（名表见 design §1）；内部结构（`sync.batch` / `reply.result.ack` / `offboard.command` 等尾段）逐字保留。协议消息 107 条计数不变；两份操作登记表 10 个 IM 键换名、计数不变。直接切换：旧名从两份协议穷举表直接删，无别名、无墓碑。
- **`.result`/`.ack` 应答约定定案（批 7 显式豁免的到期日）**：正式转正为第三族约定——「留痕写 durable-outbox 往返族」（请求可带历史名词尾段，应答＝`.result`，出箱确认＝`.ack`），与「请求＝祈使动词 / 应答＝过去分词事实形」两族并立，写进 `docs/edge-command-grammar.md` 族约定表。裁定依据（design §2）：三条 `.ack` 全是 cloud→edge 方向（过去分词规则语义不适用）、`reply.result` 一型两用（fire-and-forget 与 correlated request 共用）、嵌套结构被 edge-client 前缀匹配依赖——超出前缀换名的重构在 8 类 typecheck 盲区面前零收益纯风险。
- **同形异义全部不动（sed 红线，design §4 全单）**：握手能力串（`interaction_inbox_v1` 等 6 条）、edge 驱动能力串（`interaction.comment.read` / `interaction.dm.*`）、api 仓 RBAC 权限键（`interaction.config.*` 等，持久化于角色目录 JSON）、outbox topic（`interaction.audit_event`）、EventBus 事件名（`interaction.occurred/completed/skipped`）、DB 表名、`interaction_inbox_only` 原因码、Electron IPC 通道名（`interaction.auth.request` / `interaction.workspace`）、全部 `Interaction*` TS 类型标识符（不上线缆，批 5 载荷接口保留同例）。
- **测试 fixture 双仓同步**：`wechat-channels-interaction/v1/ws/` 21 份 JSON fixture 及文件名→消息名对照表在 aidcp-automation 与 aidcp-cloud 两仓逐字同步改（fixture 目录随语义改名 `wechat-channels-inbox/`）。
- `docs/protocol.md` §2 表与 IM 载荷节、`docs/edge-command-grammar.md` 批 6 行随改同步。
- **BREAKING（内部协议，预期内）**：并入批 1–5+7 既有的未出包切换窗口（dev 车队已停摆待装机，本批不新增停摆面）；切换窗口内旧客户端对新名 fail-closed 拒收在执行前。视频号 IM 真机验收并入既有真机簇（backlog 登记）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

全部为机械改名 delta（纯名字提及，语义零变，集成期按当时最新 spec 文本生成）：

- `wechat-channels-interaction`: IM 族 15 条消息名全量换 `wechat_channels.inbox.*` 前缀（11 处提及）
- `console-panel-api`: 3 处消息名提及随改
- `edge-companion-ui`: 1 处提及随改
- `interaction-risk-gating`: 1 处提及随改
- `interaction-test-data-reset`: 1 处提及随改
- `wechat-channels-browser-foreground-control`: 1 处提及随改
- `wechat-send-failure-semantics`: 1 处提及随改

（`.result`/`.ack` 族约定定案落 `docs/edge-command-grammar.md`，语法蓝图非运行时 spec，无独立 capability delta。）

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`（union `:146-161` + PayloadMap `:2167-2181`）、`src/wechat-channels/{runtime,protocol-validation,sync-common,connector}.ts`、`src/client/{edge-client,operation-registry,command-diagnostics}.ts`（含 `:1016-1023` 前缀匹配与 `:279` 裸串比较）、`src/electron/renderer/renderer.js:2588`、测试约 8 文件（protocol-contract 15 名穷举表、edge-client 白名单 22 处等）。**不动 native 引擎与 manifest**（IM 族无 nativeKind，零 digest 重钉）。
- `aidcp-automation`：`src/comm/{protocol,handler,ws-server,operation-registry}.ts`（handler 5 入口 case + 4 处 ack 构造 + 6 处中文错误串；ws-server `:394-395` 验证码暂停旁路集）、`src/interactions/{send-orchestrator,offboarding-service}.ts`、`src/automation-main.ts:1735`、`src/automation-edge-access.ts:316`（`interaction.offboard.` 前缀匹配）、fixture 21 份 + 对照表 + 测试约 7 文件。
- `aidcp-cloud`（集成测试仓）：fixture 21 份 + `contract-fixtures.test.ts` 对照表 + `send-orchestrator.test.ts` 等 3 文件，与 automation 逐字同步。
- 控制仓：`docs/protocol.md`、`docs/edge-command-grammar.md`、spec 机械 delta 7 份。
- **并行注意**：与批 6 另半边 change（`platformize-publish-navigation-vocabulary`，发布段化 + back/close + task.* + kernel v0.1.4）并行开发、**集成串行、本批先落**（两批同碰两份 protocol.ts、登记表、edge-client 白名单、command-diagnostics、renderer、protocol-contract 测试等热区，后落批 rebase；本批不碰 manifest digest，无双重重钉问题）。
- **不出包不算完**：并入既有未出包窗口（真机簇 148/149/152/153 同包），真机验收项登记 backlog。
