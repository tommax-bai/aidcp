## Why

词汇蓝图批 7（`docs/edge-command-grammar.md` §6.2「非平台域词汇收口」、§6.3 批次表，2026-08-07 用户据实立项）：非平台域 14 条消息里四类不齐——验证码同一主题两个家（检测在 `risk.*`、协助在 `captcha.*`）、应答命名三套约定并存、`ui.snapshot` 名词形读不出方向、identity 两条不平行。纯内部词汇、不碰浏览热区，与批 5 并行开发、集成串行（批 5 先落）。

前置核实（2026-08-07，两仓 + kernel 全量触点探查）：

- **kernel 传输豁免名单零命中**（`captcha.assist.*` 保留不动、`edge.task.acquire/release` 是请求名不在本批）——**批 7 不需要出 kernel 新版本**（批 6 改 `edge.task.*`→`task.*` 时才会命中，届时再出）。
- **无 `risk.` 前缀整族判断**：消费端是逐条 `case`，两仓零 `startsWith('risk')`；平台段闸只认平台词，`risk`/`captcha` 都不是平台段。唯一静默退化点是 edge `host-assembly-guard.test.ts:278-282` 的 4 条源码正则闸——`doesNotMatch` 两条改名后**恒真通过（闸失效无人察觉）**，必须同批改正则。
- **`ui.snapshot` 无应答无配对**：单向 cloud→edge 推送、不留 pending、按投递数重排下一跳——改动词形没有配对方要一起改，是四子项里最干净的一条。
- **应答约定的存量盘点**：`identity.observed` / `edge.task.acquired` / `edge.task.released` 已是「过去分词/过去式事实形」；三套约定里真正的孤例只有 `state.report`（名词形）。`.result` / `.ack` 后缀族（IM/发布的留痕写外发流程应答）是另一族惯例，批 6 整族改名时定夺，本批显式豁免记录。
- **能力串与消息名脱钩**：`identity_read_current_v1` 等握手协商串改了即破坏与已发布客户端的能力协商，明确不改、加注释坐实脱钩。
- **nativeKind 不改**（`identity_read_current` 等引擎内部表示，批 4 先例）。

## What Changes

- **5 条消息改名，总数 103 不变**（名表见 design §1）：
  `risk.captcha_detected`→`captcha.detected`、`risk.captcha_cleared`→`captcha.cleared`（验证码归一家，与 `captcha.assist.*` 三段子族同顶层域）；
  `state.report`→`state.observed`（应答约定归一，与 `identity.observed` 同形）；
  `ui.snapshot`→`ui.push_snapshot`（动词形，方向可读）；
  `identity.read_current`→`identity.read_current_page`（与 `read_self_profile` 平行：动词＋地点宾语）。
- **应答命名族约定定案并写进蓝图**：请求＝祈使动词（`read` / `acquire` / `update`），edge→cloud 应答与自发事实上报＝过去分词/过去式事实形（`observed` / `acquired` / `released` / `detected` / `cleared`）。显式豁免：`ping`/`pong`（传输惯例）、`.result`/`.ack` 族（留痕写外发应答，批 6 域）、`captcha.assist.*` 子族（蓝图裁定保留）。
- 内部事件名随消息名走防错位：`state.report.arrived`→`state.observed.arrived`（`identity.observed.arrived` 本就同形不动）。
- 两份登记表 52 条计数不变、2 键改名（`ui.push_snapshot`、`identity.read_current_page`）；edge 白名单 2 处、bridge 2 case、平台能力表 `identityCapture.command`、ws-server 数据面剥离闸与验证码暂停 bypass 名单成员随改。
- manifest `identity.read_current` 条目 `edgeTypes[]` 改名（receipts `identity.observed` 不动；`state.report` 是否在 manifest receipts 实装时 grep 核）→ 重建重钉 capabilityDigest 五位点（含生产常量）。
- 测试专项：host-assembly-guard 4 条正则、core-log-severity 日志串断言、protocol-contract 穷举表（计数断言值不变、键逐条换）。
- `docs/protocol.md`、`docs/edge-command-grammar.md` §6.2 批 7 小节按落地名定稿。
- **BREAKING（内部协议，预期内）**：并入批 1–5 同一个未出包切换窗口（dev 车队已停摆待装机，不新增停摆面）。`ui.push_snapshot` / `identity.read_current_page` 旧客户端 fail-closed 拒收在执行前；`captcha.detected` 等 edge→cloud 方向为新客户端发新名，旧云端不存在（云端先部署）。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities

本批全部改名语义零变，无手写语义 delta；机械改名 delta（grep 实测 12 个 capability：captcha-incident-handling、account-identity-resolution、alert-manual-resolution、browser-cold-standby、client-customer-auth、edge-companion-ui、edge-control-plane-presence、facebook-identity、persona-keyword-generation、platform-page-command-routing、platform-runtime-abstraction、platform-search-activity）在集成期脚本化生成、归档前对当时最新 spec 文本重生成一遍。**同形异义红线**：`identity_read_current_v1` 等能力串不改；`identity_bootstrap`（本地握手，非云端命令）不改；nativeKind（`identity_read_current` / `identity_observation` / `state_read`）不改；`edge.task.acquire/release/acquired/released` 全家不动（前缀改名是批 6）。

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`、`src/client/{edge-client,operation-registry,command-diagnostics}.ts`、`src/native-page-engine/{command-mapper,browse-session}.ts`（captcha 上报点 + state.report 发送点 + identity 分派）、`src/browse/captcha-assist.ts`（cleared 第二发送点 + 5 处纪律注释）、`src/main.ts`（state.report 冷待机作答点等）、`native/page-engine/command-manifest.json` + digest 五位点、约 10 个测试文件（含 host-assembly-guard 正则、core-log-severity 日志串）。
- `aidcp-automation`：`src/comm/{protocol,handler,command-bridge,operation-registry,ui-snapshot,ws-server}.ts`、`src/event-bus/types.ts`（arrived 事件名）、`src/orchestrator/role-dispatcher.ts`（identity 分派 + state.report.arrived 接线）、`src/platform/registry.ts`（identityCapture）、`src/agents/nickname-enricher.ts`、约 12 个测试文件。
- 控制仓：`docs/protocol.md`、`docs/edge-command-grammar.md`、spec delta 机械批。
- **并行注意**：与批 5（`objectify-interaction-vocabulary`）并行开发、集成串行、批 5 先落后本批 rebase；两批改的是两份 protocol.ts 的不同行、登记表不同键，rebase 冲突面小但必须走「fetch + rebase + 全量重跑」纪律。`restore-native-facebook-residual-parity` / `blocking-overlay-dom-capture` 在飞，同前。
- **不出包不算完**：并入既有出包窗口；真机验收项并入 backlog 出包簇（登记前 grep 最大簇号）。
