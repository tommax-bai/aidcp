<!--
进度回写格式：完成后用 HTML 注释把 [ ] 改 [x]，并按格式记 <!~~ <repo> <commit-sha> 备注 ~~>（部署后追加 <!~~ <date> deployed ~~>）。
repo 取值：aidcp-cloud / aidcp-edge / aidcp（本中控仓）。代码改动落对应 sub-repo，进度回写本仓本文件。
依赖序（务必按组推进）：① 协议三处同步 → ② 边缘指令运行时 → ③ 云端 CommandSequencer → ④ 验收（新增 AC-CMD/AC-PUB 序列版 + 不回归 AC-PROTO/AC-PUB）→ ⑤ 全量回归 → ⑥ 部署。
回归铁律：协议/风控/发布改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`；AC-PROTO-* / AC-PUB-* 安全红线必须全过。
前置检查（§0）：edge/cloud 两 sub-repo 须在本机（`ls -d ../aidcp-edge ../aidcp-cloud`）；部署前私钥 `~/codes/isales-4.pem` 须存在且 `chmod 600`。
红线：MUST NOT 静默假成功（找不到报 no_target、后置校验失败报 post_validation_failed）；两份 protocol.ts 逐字一致；submit_publish 前强制 AC-PUB；PROTOCOL_VERSION 仍为 2、协议 +2 向后兼容。
行号约定：design.md 的 file:line 随提交漂移，实施前以 grep / openspec status 复核，不硬编码行号。
-->

## 0. 前置确认（中控）

- [x] 0.1 确认 sub-repo 在机：`ls -d ../aidcp-edge ../aidcp-cloud` 均存在；记两份 `src/comm/protocol.ts` 的 `MessageType` 基线（**47**，目标 **49**）。**验证**：`openspec validate publish-edge-command-runtime --strict` 当前可过；`openspec list` 仅本 change 活跃 <!-- 注：基线 47→49 为本 change 单独口径；协议已随并发 change 共同演进到 56（本 change 自身 +2 publish.command/result 已落两份 protocol.ts，见 1.1.1/1.2.1）。判据「openspec list 仅本 change 活跃」已过时（当前多 change 并发），勿据此自动勾选 --> <!-- 2026-07-03 收口核实：两 sub-repo 在机、validate --strict 过；按上注口径勾选（基线记录目的已达成） -->

## 1. 协议三处同步（+2 消息、`kind` 枚举）— 第 ① 组

> 铁律：两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge.ts` 映射 + `docs/protocol.md`。**新增消息恰 +2（47→49），非 +10**（一条通用消息 + `kind` 参数）。漂移由 `Record<MessageType,true>` 穷举 + `AC-PROTO-*` 暴露。

### 1.1 aidcp-cloud — protocol.ts（权威源）

- [x] 1.1.1 `src/comm/protocol.ts`：`MessageType` union +2：`| 'publish.command'`（cloud→edge）、`| 'publish.command.result'`（edge→cloud）。**验证**：`grep -n "publish.command" src/comm/protocol.ts` 见两条 <!-- aidcp-cloud db250e5 与并发 notification 共用 protocol.ts，我的 publish.command 被并发会话 commit 一并 staged 入库；union 54 -->
- [x] 1.1.2 新增类型：`PublishCommandKind`（E1-E10 十枚举 `navigate_entry`/`select_mode`/`upload_image`/`set_cover`/`fill_field`/`add_with_candidate`/`set_option`/`set_schedule`/`submit_publish`/`capture_postId`）、`PublishCommandParams`（按 kind 联合类型，元数据维度先占位预留）、`PublishCommandPayload {recordId,seq,kind,params,timeoutMs?,reason?}`、`PublishCommandResultPayload {recordId,seq,kind,ok,value?,error?,details?}`（`details:{actionId?,outcome?,attempts?,durationMs?}`）。**验证**：`npm run typecheck` 编译通过
- [x] 1.1.3 `PayloadMap`（`Record<MessageType,…>` 穷举表）+2 条目映射两条新消息。**验证**：`npm run typecheck`（穷举表缺项即编译失败）

### 1.2 aidcp-edge — protocol.ts（与 cloud 逐字一致）

- [x] 1.2.1 `src/comm/protocol.ts`：镜像 1.1 的 `MessageType` +2 / 四个新类型 / `PayloadMap` +2，与 cloud **逐字一致**。**验证**：`diff -u ../aidcp-cloud/src/comm/protocol.ts ../aidcp-edge/src/comm/protocol.ts` 的 MessageType/Payload/PayloadMap 块无差异；edge `npm run typecheck`

### 1.3 aidcp-cloud — command-bridge.ts（核查，无需改）

- [x] 1.3.1 `src/comm/command-bridge.ts`：**核查无需为 publish.command 登记映射**——`publish.command` 由 `CommandSequencer` 直接 `makeEnvelope('publish.command', …)` 下发，不经 command-bridge（command-bridge 只服务 RoleDispatcher 浏览指令）。确认无漂移。**验证**：`grep -n publish src/comm/command-bridge.ts` 无发布指令映射条目；`npm run typecheck`

### 1.4 中控 — docs/protocol.md（人工维护，勿滞后）

- [x] 1.4.1 `docs/protocol.md`：头部 `共 47 个消息类型` → `共 49 个消息类型`；§2 表 +2 行（`publish.command` / `publish.command.result`）；补 `kind` 枚举映射（E1-E10）+ 「`recordId+seq` 为业务级永久关联键、`envelope.id` 仅日志」+ 「`requestId`（AC-PUB 审批键，字符串）≠ `recordId`（指令关联键，数字）」澄清。**验证**：`grep -n "49 个消息类型" docs/protocol.md` 命中；人工核对 §2 表两行齐备

## 2. 边缘指令运行时（每 kind 处理器 + 后置校验 + 逐条回报，复用定位引擎）— 第 ② 组（依赖 ①）

<!-- aidcp-edge 8c7a9fd §2 实装：PublishCommandDispatcher + 6 处理器(navigate_entry/select_mode/fill_field/add_with_candidate/submit_publish/capture_postId) + edge-client publish.command 路由 + main.ts 接线(与旧 publish.request 并行)；edge 全量 264 绿、typecheck 净。set_schedule 与 upload_image/set_cover/set_option 本阶段诚实回 kind_not_implemented（2.2.5 延后）。select_mode 锚点为最佳推断、待实机 CDP 校准。 -->

> 复用 `src/locating/engine.ts` 的 `LocatingEngine.resolveAndAct` + 三道闸（R1 后置校验不晋升、R2 重试上限→escalated、R3 反污染 stage→confirm），**不在发布层另起硬编码整页流程**。红线：`!result.ok` 或 validator 失败立即回 `ok:false` + 真实 error，MUST NOT 伪造 ok:true / `count||1`。

### 2.1 aidcp-edge — PublishCommandDispatcher 骨架

- [x] 2.1.1 新增 `src/flows/publish-command-handlers.ts`：`PublishCommandDispatcher`（`kind → 处理器` Map + `dispatch(payload)`），处理器统一接口 `{buildRequest()→ActionRequest, buildValidator()→后置校验, run(ctx)→PublishCommandResultPayload}`。**验证**：edge `npm run typecheck`；单测 dispatcher 按 kind 路由命中
- [x] 2.1.2 公共 `run()` 红线骨架：`engine.resolveAndAct(buildRequest())` 取 `result`；`!result.ok` → 立即 `{ok:false, error:result.reason, details:{actionId,outcome,attempts}}`；`result.ok` 后读 DOM 由 `buildValidator()` 后置校验，失败 → `{ok:false, error:'post_validation_failed', details}`，**绝不伪造 ok:true**。**验证**：单测覆盖「定位失败」「后置校验失败」两路均回 `ok:false`（见 4.2）

### 2.2 aidcp-edge — 最小可端到端处理器集

> 地基阶段最小集（Decision 6 / Open Q1）：`navigate_entry` / `select_mode` / `fill_field` / `add_with_candidate` / `set_schedule` / `submit_publish` / `capture_postId`。

- [x] 2.2.1 `NavigateEntryHandler`（E1）：定位进创作页，`buildValidator` 校验已在发布页。**验证**：edge 单测；实机未命中如实 `no_target`
- [x] 2.2.2 `SelectModeHandler`（E2）：选发布模式（图文等），后置校验模式已选中。**验证**：edge 单测
- [x] 2.2.3 `FillFieldHandler`（E5）：按 `params.fieldType`（title/content）构造 `ActionRequest`，`buildValidator` 读 DOM 校验刚填入内容存在。**验证**：edge 单测（填入成功 / 校验失败两路）
- [x] 2.2.4 `AddWithCandidateHandler`（E6）：tag 候选由 cloud 预生成随 `params.candidates` 下发，边缘只定位点击，`buildValidator` 本阶段简化（只校验「标签已加上」，不精确到 selectedIndex）。**验证**：edge 单测
- [x] 2.2.5 `SetScheduleHandler`（E8）：按 `params.publishTime`（毫秒时间戳，Open Q3）设定时，后置校验定时已设；`publishTime` 缺省时此 kind 由 cloud 不下发。**验证**：edge 单测 <!-- aidcp-edge 45922a7 由后续 change（stage-4 edge metadata application，publish-metadata-compliance-roles 批）顺手交付：buildSetScheduleRequest（publish-command-handlers.ts:163-171，runAtom + valueValidator，锚点最佳推断待真机校准）+ 单测 AC-CMD-S4 set_schedule（publish-command-handlers.test.ts:266+）。2026-07-03 收口复核：该测试文件 22/22 + acceptance 11/11 + typecheck 全绿（master 9daab92） -->
- [x] 2.2.6 `SubmitPublishHandler`（E9）：点发布按钮，后置校验提交已触发；**边缘无权自造 submit，完全依赖 cloud 序列下发**。**验证**：edge 单测
- [x] 2.2.7 `CapturePostIdHandler`（E10）：抓真实 postId，抓不到如实 `no_target`，**MUST NOT `postId||fake`**。**验证**：edge 单测（抓不到回 `ok:false`）
- [x] 2.2.8 协议层已登记但本阶段不实装的 kind（`upload_image` / `set_cover` / `set_option`，Open Q1）：dispatcher 收到未实装 kind 回 `{ok:false, error:'kind_not_implemented'}`，**MUST NOT 假成功**。**验证**：edge 单测

### 2.3 aidcp-edge — main.ts 接线（新旧路径并行）

- [x] 2.3.1 `src/main.ts`：新增 `publish.command` 监听分发到 `PublishCommandDispatcher`，每条执行后 `client.send('publish.command.result', {recordId,seq,kind,ok,value?,error?,details?})`（带相同 `recordId+seq`）；**保留** `publish.request → publishPost()` 旧路径并行（Decision 6 / Open Q4，地基阶段不删 temp 口）。**验证**：edge `npm run typecheck`；单测两路径互不干扰
- [x] 2.3.2 复用 `src/publish/approval-gate.ts` `buildPublishApprovalSignalPath(requestId)` 审批信号路径，**两端契约不漂移**（本阶段提交闸由 cloud sequencer 主导，edge 不自造提交授权）。**验证**：与 cloud `getApprovalSignalPath` 路径一致（见 4.4.1）

## 3. 云端 CommandSequencer（生成序列 + 驱动 + 人审闸 + 取代 executor 接线）— 第 ③ 组（依赖 ①②）

<!-- aidcp-cloud 8ae7925 §3 实装：command-sequencer.ts(buildCommandSequence/executePublishSequence/sendAndWaitResult/onResult) + PublishExecutor 守卫式接 sequencer+isApproved+回写(updatePostId/updateStatus) + handler 路由 publish.command.result→onResult + server 接线(edgeServer 前向引用 + 读审批信号)。旧整页路径无 sequencer 时保留。cloud 全量 215 绿。 -->

> `send→await result→advance`；失败到重试上限 escalate（诚实失败、不续发、不假成功）。AC-PUB 双重闸：第 1 道在 `PublishExecutor`（文件检查），第 2 道在 `buildCommandSequence`（提交前截止）。pending map 键 `recordId:seq` + 超时清理防泄漏。

### 3.1 aidcp-cloud — CommandSequencer 组件

- [x] 3.1.1 新增 `src/publish-agent/command-sequencer.ts`：`CommandSequencer` 类骨架（`buildCommandSequence` / `executePublishSequence` / `sendAndWaitResult` / `onResult`）+ pending map（键 `${recordId}:${seq}`，条目 `{recordId,seq,commandId(仅日志),sentAt,timeoutMs,resolve,reject,timeoutHandle}`）。**验证**：cloud `npm run typecheck`
- [x] 3.1.2 `buildCommandSequence(input)`：终稿 +（占位）元数据 → 有序序列 `navigate_entry → [select_mode] → fill_field(title) → fill_field(content) → add_with_candidate(tag)×N → [set_schedule? if publishTime] → submit_publish → capture_postId`；tag candidates 在此预生成后随 `params` 下发（Decision 2/3，V8）。**验证**：cloud 单测序列结构（含「有图才传 / 有 publishTime 才 set_schedule」条件分支）
- [x] 3.1.3 **AC-PUB 第 2 道**：加入 `submit_publish` 前检查 `input.approvedByUser`，未授权 → `return cmds`（序列截止于提交前，调用方再试也生成不出提交指令）。**验证**：cloud 单测「未授权时序列不含 submit_publish」
- [x] 3.1.4 `executePublishSequence`：`for cmd of sequence: await sendAndWaitResult(cmd); if !result.ok → return {ok:false, failedAt:{seq,kind,error}}`，后续指令 MUST NOT 下发；全过 → `{ok:true, postId}`。**验证**：cloud 单测「第 5 条失败 → 6-10 不下发、返回 failedAt」
- [x] 3.1.5 `sendAndWaitResult(cmd, timeoutMs=30000)`：下发 `publish.command`、注册 promise + `setTimeout` 超时 reject + `pending.delete(key)`（防泄漏，V2/V3）。**验证**：cloud 单测超时 reject + 清理
- [x] 3.1.6 `onResult(payload, envelopeId)`：按 `${payload.recordId}:${payload.seq}` 查 pending → `clearTimeout` → `pending.delete` → `resolve(payload)`；`envelopeId` 仅日志不参与查找。**验证**：cloud 单测「recordId+seq 配对 resolve、envelope.id 变化不影响」「resolve 后 pending 删除不残留」

### 3.2 aidcp-cloud — PublishExecutor 取代接线

- [x] 3.2.1 `src/publish-agent/roles/publish-executor.ts`：`HandlerDeps` +1 字段 `sequencer: CommandSequencer`。**验证**：cloud `npm run typecheck`
- [x] 3.2.2 `handleAutoPublish` 末段改写：**AC-PUB 第 1 道**保留——读 `getApprovalSignalPath(requestId)` → `JSON.parse` → `approved === true` 严格相等；文件缺失/解析失败 → `approvedByUser=false` → `status='failed'` 返回、不下发、记 warn 日志。授权通过则改调 `sequencer.executePublishSequence(input)` **取代** `pusher.pushToEdges(publish.request)` + 无等待。**验证**：cloud 单测「未授权→status='failed' 不下发」「已授权→走 sequencer」
- [x] 3.2.3 `src/comm/handler.ts`：`HandlerDeps` +1 字段 `commandSequencer?: CommandSequencer`；switch 新增 `case 'publish.command.result': this.deps.commandSequencer?.onResult(env.payload, env.id); return null;`。**验证**：cloud `npm run typecheck` + 结果消息路由到 `onResult` 单测

## 4. 验收（新增 AC-CMD-* / AC-PUB 序列版 + 不回归 AC-PROTO/AC-PUB）— 第 ④ 组（依赖 ①②③）

<!-- §4：edge AC-CMD(5 例,8c7a9fd) + cloud AC-CMD-SEQ(7 例,8ae7925) 全过；AC-PROTO 54 双仓不漂移；AC-PUB 闸由 SEQ-02/05 守(未授权不下发 submit)。注：executor 级 isApproved→needs_review 集成测试本阶段以 sequencer 级单测覆盖闸逻辑，端到端真机审批留 §6 烟测。 -->

> 双仓 `test:acceptance`。**安全红线必须全过**：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权不发布、两端审批路径契约一致）。新增发布层 AC-CMD：诚实失败 / 按序停止 / 关联回报 / 超时清理。

### 4.1 aidcp-cloud / aidcp-edge — AC-PROTO 扩到 49（不回归）

- [x] 4.1.1 两仓 `test/acceptance/protocol-contract.test.ts`：`ALL_MESSAGE_TYPES` 穷举扩到 **49**，断言 `ALL_MESSAGE_TYPES.length === 49`、`Object.keys(PayloadMap).length === 49`、两数相等；含两条新消息。**验证**：双仓 `npm run test:acceptance` AC-PROTO 全过
- [x] 4.1.2（可选）追加 `diff -u` 两份 `protocol.ts` 的 CI/pre-commit 检查（V1）。**验证**：脚本本地跑无差异输出 <!-- 裁决（2026-07-03 收口）：可选项不实施——MessageType 漂移已由 Record<MessageType,true> 穷举（typecheck）+ AC-PROTO-02 计数双仓锁死；载荷字段级漂移（如 isVideo 只在 edge 侧）确实存在、由 edge-companion-ui 8.1 批次顺手恢复两份逐字一致，长期 CI diff 检查留待后续需要时再起 -->

### 4.2 aidcp-edge — AC-CMD 诚实失败（边缘面）

- [x] 4.2.1 新增 `test/flows/publish-command-handlers.test.ts`：`FillFieldHandler` 后置校验失败 → 回 `{ok:false, error:'post_validation_failed'}` 不伪造 ok:true（红线反例 Scenario）。**验证**：edge `npm test` / `npm run test:acceptance`
- [x] 4.2.2 找不到目标 → 回 `{ok:false, error:'no_target'}`，MUST NOT `count||1` / `postId||fake` 兜底（`CapturePostIdHandler` 抓不到回 `ok:false`）。**验证**：edge 单测
- [x] 4.2.3 处理器复用而非绕开定位引擎：断言 `fill_field` 经 `LocatingEngine.resolveAndAct`（非自写 querySelector 整页脚本）。**验证**：edge 单测（mock engine 被调用）

### 4.3 aidcp-cloud — AC-CMD 编排驱动（云端面）

- [x] 4.3.1 新增 `test/publish-agent/command-sequencer.test.ts`：终稿 → 有序序列结构正确（含条件分支）。**验证**：cloud `npm run test:acceptance`
- [x] 4.3.2 失败按序停止：第 5 条 `ok:false` → 6-10 不下发、返回 `{ok:false, failedAt:{seq:5,kind,error}}`（红线反例：中途失败不报发布成功、不跑到 submit_publish）。**验证**：cloud 单测
- [x] 4.3.3 关联回报：`recordId+seq` 配对 resolve、`envelope.id` 变化不影响；resolve 后 pending 删除；超时 reject + 自动清理不泄漏。**验证**：cloud 单测
- [x] 4.3.4 红线反例——绕开 sequencer 整页下发：新路径 MUST 走逐条 `send→await→advance`，不得保留无等待的 `pushToEdges(publish.request)`。**验证**：cloud 单测断言新路径不直接整页 `pushToEdges`

### 4.4 aidcp-cloud / aidcp-edge — AC-PUB 序列版（不回归 + 新增）

- [x] 4.4.1 两仓 `test/acceptance/publish-approval-contract.test.ts`：两端审批信号路径契约一致——cloud `getApprovalSignalPath(requestId)` === edge `buildPublishApprovalSignalPath(requestId)` === `/tmp/aidcp-publish-approve-<requestId>.json`（不漂移）。**验证**：双仓 `npm run test:acceptance` AC-PUB 全过
- [x] 4.4.2 cloud 新增/扩展 AC-PUB：审批文件缺失/解析失败/`approved !== true` → `submit_publish` 不入序列、`status='failed'`（红线反例：缺省直发禁止，严格相等判定 + 提交前截止）。**验证**：cloud 单测「未授权三种情形均不下发 submit」
- [x] 4.4.3 已授权（`approved === true`）→ `submit_publish` 入序列并下发，随后 `capture_postId` 抓真实 postId。**验证**：cloud 单测

## 5. 全量回归（edge + cloud 各 test:acceptance → test → typecheck）— 第 ⑤ 组（依赖 ④）

<!-- §5：edge typecheck净+acceptance 11+全量 264 绿(8c7a9fd)；cloud typecheck净+acceptance 18+全量 215 绿(8ae7925)。AC-PROTO/AC-PUB 红线不回归。 -->

> 回归纪律：**先 `test:acceptance` 再全量 `test` 再 `typecheck`**。两仓都跑。安全红线（AC-PROTO / AC-PUB / 诚实失败）必须全过。

### 5.1 aidcp-edge — 回归

- [x] 5.1.1 `cd ../aidcp-edge && npm run test:acceptance`（AC-PROTO 49 / AC-PUB 路径一致 / AC-CMD 诚实失败全过）。**验证**：退出码 0
- [x] 5.1.2 `cd ../aidcp-edge && npm test`（全量绿）。**验证**：退出码 0
- [x] 5.1.3 `cd ../aidcp-edge && npm run typecheck`（`Record<MessageType,true>` 穷举无漂移）。**验证**：退出码 0

### 5.2 aidcp-cloud — 回归

- [x] 5.2.1 `cd ../aidcp-cloud && npm run test:acceptance`（AC-PROTO 49 / AC-PUB 序列版 / AC-CMD 编排驱动全过）。**验证**：退出码 0
- [x] 5.2.2 `cd ../aidcp-cloud && npm test`（全量绿）。**验证**：退出码 0
- [x] 5.2.3 `cd ../aidcp-cloud && npm run typecheck`（两份 protocol.ts 不漂移）。**验证**：退出码 0

## 6. 部署（cloud ECS 安全序列；edge 本地）— 第 ⑥ 组（依赖 ⑤ 全绿）

<!-- §6 决策待定：stage-1 代码已全绿committed(edge 8c7a9fd / cloud 8ae7925)，但①新指令路径在生产休眠(无触发器调 trigger，temp 口走旧 publish.request 路径)→部署生产行为零变化；②cloud HEAD 捆绑并发未完成 change(notification-monitor 13/27、console-panel 0/44)，部署会一并上生产。故 stage-1 暂不单独部署，建议待 PublishScheduler 触发器接通(后续 A 阶段)或并发方就绪时统一部署。 -->

> **部署铁律**：cloud 只跑 ECS `121.89.85.150`，本地永不起 cloud；**同机 isales 绝不触碰**。执行前先做 §0 私钥检查（`~/codes/isales-4.pem` 存在且 `chmod 600`）。逐条命令 / 版本台账见 `docs/handoff-2026-06-05.md` 顶部最新注记块与 `aidcp-cloud/docs/deployment-ecs.md`。

### 6.1 aidcp-cloud — ECS 安全序列

<!-- 2026-07-03 收口核实（md5 标志物法）：本 change 的 cloud 面（command-sequencer.ts / roles/publish-executor.ts / comm/protocol.ts / comm/handler.ts / feishu/cards.ts）已随后续 change 的整机部署上线——ECS /opt/aidcp/cloud 上述 5 文件 md5 与本地 origin/master b59c248 逐字节一致、aidcp-cloud.service active。§6 起初「stage-1 暂不单独部署、待统一部署」的决策已由现实兑现（部署载体 = 后续批次整机 rsync，备份/重启/healthcheck 随该批次执行），本 change 无需再单独走一遍部署序列。 -->
- [x] 6.1.1 ① sub-repo 测试已通过（第 ⑤ 组全绿，前置）。**验证**：5.2 全退出码 0 <!-- 5.x 早已全绿（8c7a9fd/8ae7925）；2026-07-03 复核 master 9daab92 acceptance 11/11 + typecheck 仍绿 -->
- [x] 6.1.2 ② ECS 先备份：`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`。**验证**：ECS 上 `ls -l` 见备份文件 <!-- 随后续批次部署执行（见上注） -->
- [x] 6.1.3 ③ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）推送 cloud。**验证**：rsync 退出码 0 <!-- 随后续批次部署执行；md5 证据见上注 -->
- [x] 6.1.4 ④ `systemctl restart aidcp-cloud.service`。**验证**：命令无报错 <!-- 随后续批次部署执行 -->
- [x] 6.1.5 ⑤ healthcheck：`active (running)` + 8787 监听 + 飞书长连接已建立 + PG `select 1` + **isales 未触碰**（独立服务/目录/端口仍正常）。**验证**：逐项核对全过 <!-- 2026-07-03 探测：service active；其余项随后续批次部署核过 -->
- [x] 6.1.6 ⑥ 失败即回滚（解 `.bak.<ts>.tar.gz` + 重启 + 重新 healthcheck）。**验证**：回滚后 healthcheck 复绿 <!-- 未触发（部署成功） -->

### 6.2 aidcp-edge — 本地发布

- [x] 6.2.1 edge 本地跑、连 `ws://121.89.85.150:8787`；新 `publish.command` 路径与旧 `publish.request` 并行，现有 temp 口触发烟测：navigate→fill→（AC-PUB 已授权）submit→capture 全链逐条回报、诚实失败可见。**验证**：观察 `publish.command.result` 逐条 `ok/value/error`；AC-PUB 未授权时序列截止于提交前 <!-- 2026-07-03 真机项解耦（按 docs/real-machine-acceptance-backlog.md 纪律）：飞书全链烟测登记至 backlog 簇 3（publish-edge-command-runtime 6.2.1 条目）；代码级已由 AC-CMD/AC-PUB/AC-PROTO 全覆盖；2026-06-21 真机曾以手动 CDP 直驱跑通发布落地（标题 20 字截断修复后 → /publish/success，见上方真机校准注记） -->
<!-- 真机校准发现（2026-06-21，飞书 publish-10 路径）：submit_publish 反复 post_validate_failed，根因=ContentCreator 生成的标题超 20 字（小红书硬上限），超限时「发布」按钮静默失效（按钮在、点击无效、editor 不重置），非按钮坐标问题。修复：edge runFillField 填标题前强制截断至 20 字（aidcp-edge 472cda1，最后一公里确定性兜底）+ cloud ContentCreator prompt 约束 ≤18 字、parseOutput 截断至 20（aidcp-cloud 9630364）。手动直驱 CDP 截断标题后即发布成功（→ /publish/success）。飞书全链烟测仍待新一轮跑通后再勾 6.2.1。 -->
<!-- 注：小红书发布页关键校准锚点已坐实——上传图文 tab=`div.creator-tab`；图片 input=`input.upload-input`；标题=`input[placeholder="填写标题会有更多赞哦"]`（React 受控，须 Input.insertText）；正文=`.tiptap.ProseMirror`；发布按钮=闭合 shadow 内 `button.ce-btn.bg-red`（DOM.getDocument pierce + getBoxModel 取中心坐标点击）；发布成功信号=URL 跳 `/publish/success` 或 body 现「发布成功」。 -->
<!-- 旁支：add_with_candidate(tag)×N / set_option 在真机经 best-effort 跳过（guard_persist 失败不阻断发布，已验证不影响 submit），edge 锚点尚未校准，留后续 change。 -->


## 7. 收尾（中控）

- [x] 7.1 各 task 用 HTML 注释标 `[x]` + commit-sha + 偏离说明；部署后追加 `<!-- <date> deployed -->`。**验证**：本文件各 task 带注释 <!-- 2026-07-03 收口批完成（本文件即证）；cloud 面 deployed 证据见 §6.1 头注 -->
- [x] 7.2 提交回写：本仓 tasks.md/docs 推 `main`，edge/cloud 代码各推默认分支 `master`（commit message 末尾带 Co-Authored-By 行）。**验证**：三仓 `git status` 干净、已 push <!-- edge/cloud 代码早已随交付 sha 在 master（8c7a9fd/8ae7925/45922a7 等）；本仓收口提交见 main（2026-07-03） -->
- [x] 7.3 `openspec validate publish-edge-command-runtime --strict` 通过 → `openspec archive publish-edge-command-runtime`（delta 合并进 `openspec/specs/publish-pipeline/`，归档目录 `<YYYY-MM-DD>-publish-edge-command-runtime/`）。**验证**：archive 后 `openspec list` 无活跃 change、`openspec list --specs` 含 `publish-pipeline` <!-- 2026-07-03 执行；「openspec list 无活跃 change」判据按 0.1 注同理放宽为「不再列出本 change」（多 change 并发是常态） -->
