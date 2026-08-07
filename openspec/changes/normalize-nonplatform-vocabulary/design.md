# Design — 词汇批 7：非平台域词汇收口

## 1. 名表（5 改名，总数 103 不变，唯一权威）

| 旧名 | 新名 | 方向 | 依据 |
| --- | --- | --- | --- |
| `risk.captcha_detected` | `captcha.detected` | edge → cloud | 验证码归一家：名字不该编码「消费方拿它干什么」（当初进 `risk.` 正是这个错）；与 `captcha.assist.*` 同顶层域，grep 一个词得到一族一属主 |
| `risk.captcha_cleared` | `captcha.cleared` | edge → cloud | 同上；detected/cleared 配对语义不变 |
| `state.report` | `state.observed` | edge → cloud（按信封 id 关联应答） | 应答约定归一（§2）：三套约定里唯一的名词形孤例，向 `identity.observed` 靠齐 |
| `ui.snapshot` | `ui.push_snapshot` | cloud → edge | 名词形读起来像上报、实际是下行推送；动词形一眼定向。无应答无配对（前置核实），改名不牵连任何 pending 机制 |
| `identity.read_current` | `identity.read_current_page` | cloud → edge | 与 `identity.read_self_profile` 平行：动词＋地点宾语（current page / self profile 都是读取位置）；`read_current` 缺宾语 |

`identity.read_self_profile` 不动（已合规）。`captcha.assist.capture` / `.click` / `.click_result` / `.snapshot` 四条不动（蓝图裁定保留的真子族，其内部 `.result`/名词应答形记为显式豁免）。

## 2. 应答命名族约定（定案）

**请求＝祈使动词；edge→cloud 应答与自发事实上报＝过去分词/过去式事实形。**

- 存量合规：`identity.observed`、`edge.task.acquired`、`edge.task.released`、（本批后）`state.observed`、`captcha.detected`、`captcha.cleared`。
- 显式豁免（记录理由，防后人重开）：
  - `ping`/`pong`——传输层通用惯例，MUST NOT 被本语法强行规整（蓝图已裁）。
  - `.result` / `.ack` 后缀族（`interaction.reply.result`、`interaction.offboard.result`、`publish.approval_action.result`、各 `.ack`）——留痕写外发流程的 durable-outbox 应答惯例，属 IM/发布域，批 6 整族改名（`wechat.inbox.*`）时定夺，本批不动。
  - `captcha.assist.click_result` / `.snapshot`——assist 子族整体保留。
- `edge.task.acquired` / `released` 已合规、无需改；`edge.task.` 前缀冗余是批 6 的活（届时 kernel 豁免名单命中、需出 kernel 版本——本批不需要）。
- 落点：写进 `docs/edge-command-grammar.md` §6.2 批 7 小节 + 两份 `protocol.ts` 相应 prose；语法规格第 4 条（同族同编码）已覆盖执法面，不新增规格要求。

## 3. 连锁改动的批 7 特有位点（超出批 4/5 通用清单的部分）

- **host-assembly-guard 源码正则闸（edge `test/native-page-engine/host-assembly-guard.test.ts:278-282`）**：4 条 `/risk\.captcha_(detected|cleared)/` 正则。`assert.match(nativeSession, …)` 改名后响亮失败（好）；`assert.doesNotMatch(mainSource, …)` 改名后**恒真通过——闸静默失效**，必须同批换新名正则并确认仍在断言真实约束。
- **core-log-severity 日志串断言（edge `test/electron/core-log-severity.test.ts:57,77`）**：`'risk.captcha_detected 上报失败'` 等固定串，随发送点日志文本改。
- **ws-server 两张名单（automation `ws-server.ts:374,391`）**：数据面剥离闸与验证码暂停 bypass 名单都点名 `ui.snapshot`，随改。
- **事件名随消息名**：`handler.ts:919` `emit('state.report.arrived')` → `state.observed.arrived`；`event-bus/types.ts:180`、`role-dispatcher.ts:3062` 接线同步。`identity.observed.arrived` 不动。
- **captcha-assist 纪律注释（edge `captcha-assist.ts:117,201,717,830,876`）**：5 处「绝不发 risk.captcha_cleared」prose 随新名改，约束语义不变。
- **manifest**：`identity.read_current` 条目 `edgeTypes[]` 换新名；`receipts[]` 里的 `identity.observed` 与 `sessionControls` 的 `edge.task.acquired` 不动；**实装时 grep manifest 全部 5 个旧名**（`state.report` 是否在 receipts 探查未列，以 grep 为准）。改 manifest 即重建重钉 digest 五位点（生产常量 `native-page-engine-artifact.cjs:19` + 4 测试位点；反向绑定闸 `build-contract.test.ts:78-86` 会拦漏改）。
- **能力串脱钩注释**：`protocol.ts:24-25`（`identity_read_current_v1` 等）加一行「能力串与消息名刻意脱钩：握手协商串不随消息改名」。

## 4. 同形异义不改（sed 红线）

- 能力串：`identity_read_current_v1` / `identity_read_self_profile_v1`；本地 `identity_bootstrap`。
- nativeKind：`identity_read_current` / `identity_read_self_profile` / `identity_observation` / `state_read`（TS mapper 两张表的**右值**不动，左键随新名）。
- `edge.task.*` 全家（acquire/release/acquired/released + `EDGE_TASK_LANE`）——批 6。
- `captcha.assist.*` 四条及其 `captcha_assist_*` 内部标识。
- `browser.status` / `standby.decision`（与 `ui.push_snapshot` 邻近的 edge→cloud 遥测，非其应答）。
- CooldownKey / 告警冷却表等 `${edgeId}:` 前缀 key（`captcha-coordinator.ts:257`，与消息名无关）。

## 5. 切换窗口与部署形态

云端（automation）先部署：`captcha.detected`/`cleared`/`state.observed` 是 edge→cloud 上报，旧客户端仍发旧名——**旧名已从穷举表删除，云端对未知类型按既有 `unsupported_type` 路径处理**；这三条上报断档的实际后果＝验证码暂停/告警与问现状通道在旧客户端上失效至装机，而 dev 车队本就因批 1–4 停摆待出包，不新增停摆面。`ui.push_snapshot` / `identity.read_current_page` 下行命令旧客户端 fail-closed 拒收在执行前。并入同一个出包提请。

## 6. 风险登记

| 风险 | 处置 |
| --- | --- |
| `doesNotMatch` 正则闸静默失效 | §3 第一条：换名同批改正则并人工确认闸仍真实断言 |
| digest 五位点漏改 | 生产常量优先核；重建后五处一次换齐 |
| 与批 5 集成撞 protocol.ts | 开发并行、集成串行、批 5 先落；本批 rebase 后全量重跑 + parity 复验 |
| 机械 sed 撞能力串 / nativeKind / edge.task 家 | §4 清单逐文件改，不做仓级替换 |
| 事件名与消息名错位 | `state.report.arrived` 随消息名同批改，接线点逐一核 |
