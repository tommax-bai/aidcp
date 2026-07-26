## Context

3a 已把五组 automation owner 的普通异步能力做成 route/client，但 §10.4 的 3b 三条残留都带状态机：

- restricted recovery 的外部契约要求写后 `normal`、真实 `changed` 与真实 Edge 恢复结果；api 模式
  当前却直接写 automation outbox 后立刻返回旧 `restricted`，并在命令尚未应用时恢复 Edge。
- 发布批准已有 `publish_approval_decision(pending_dispatch)`、同事务 `PublishApproved`
  outbox 和 target-filtered scan。进程内 `triggerPublishDispatchOnApprove` 只是低延迟加速器；
  但 `alreadyDecided=true` 的人工重批还承担清熔断，不能被当作普通重复事件吞掉。
- `panel.event` 已有 automation owner 的 outbox、topic cursor、轮询和 LISTEN，api 模式却直接连
  automation pool 回放。开放 read/ack 或 SSE 会重造 cursor 协议；仓内已有的
  config-mirror relay 证明 owner outbox 主动推送 api ingress 更窄。

现行 DEV 仍是 monolith，`:8093` 关闭；api/automation 提取仓的手写 `main()` 仍有其它 4a/4b
缺口。本 change 必须分开证明源码契约、loopback transport、单体零回归和真实三进程运行，不能相互替代。

## Goals / Non-Goals

**Goals:**

- restricted recovery 只由 automation `RiskController` 应用；只有写后真态为 `normal` 后才恢复
  该账号 Edge，并把 processing / applied / refused / failed / unknown 诚实交给客户调用方。
- 发布批准的持久 authority、低延迟 trigger 与真实平台下发结果保持三层分离；首写与人工重批语义分开。
- automation 经版本化 HTTP 访问 api 的授权 authority，不直连 api 授权表。
- panel event 的 outbox 回放、cursor 与 LISTEN 全留在 automation；api 只接收事件并在本进程 fanout。
- 沿用 target 隔离、revision CAS、有界内部 HTTP、at-least-once 和现有保留期，不新增 broker。

**Non-Goals:**

- 不把 trigger 受理写成 dispatching / submitted / published。
- 不把 `PublishDispatcher.dispatch()` 的分钟级 Promise 暴露成同步 HTTP 请求。
- 不补齐 4a 的完整 publish ledger、授权以外的 api authority、Facebook 素材三方法或拒绝后的素材释放。
- 不处理 4b 的 edge presence 通用镜像、`weekActiveMask()` 等同步热路径。
- 不提供浏览器级 panel event replay、client cursor、exactly-once 或 SSE。
- 不改 Edge↔Cloud protocol v2，不构建 Edge 安装包，不部署 OL。
- 不把本 change 写成已经完成 api/automation 独立 `main()` 或三进程上线。

## Decisions

### D1. 3b 是三条独立状态机，共享内部 HTTP 骨架但不做 mega-port

新增/扩展的契约按事实分开：

1. risk command：扩展既有 `risk-command-types/http/service`，不新增第二套风控写者。
2. publish approval authority：把既有进程内 `PublishApprovalInternalApi` 做成真实 HTTP，
   与短应答 `PublishDispatchTriggerPort` 分文件。
3. panel event：新增 `PanelEventDeliveryPort` / HTTP ingress 与 api 本地 fanout。

三者的重试、终态和属主不同。一个“api-automation bridge”大文件会让权限面随任一子域扩张，
也无法独立做 route/client parity 与 failure tests。

### D2. restricted recovery 继续走 durable command，但增加专用账号绑定结局

`RiskCommandPort` 增加：

- `submitRestrictedRecovery({envKey, accountId, reason, requestedBy}) → {commandId}`；
- `restrictedRecoveryOutcomeOf(commandId, envKey, accountId)`。

不能把它编码成 `submitSignal(operator_override_recover)`：该信号会从 warned/frozen 强制恢复，
而客户 recovery 只允许 restricted，二者安全语义不同。账号参数由 api 在客户 ownership 与
Facebook 平台校验后解析；outcome 查询必须同时匹配 `commandId + accountId + executionTarget`，
防止可枚举 command id 泄露别的账号结果。

recovery outcome 为五态：

- `processing`：命令存在，automation 尚未给出终局；
- `applied`：带写后 state、`changed` 和 Edge resume 的真实结果；
- `refused`：消费时真态已不是 restricted，带稳定 refusal 与写后 state，不重试、不堵主题；
- `failed`：明确不可应用或终局落地失败，带可读 reason；
- `unknown`：本 target / 本账号查无命令，与 processing 分开。

automation consumer 必须读取 `recoverRestricted()` 的返回值。命令与结局同时绑定
`envKey + accountId + executionTarget`；同账号的另一个环境也不能借 command id 读到结局。
旧行若缺 `envKey`，客户 poll fail-closed 为 `unknown`。

只有 `accepted=true` 且写后 `status=normal`，并且领域 `applied` 已可靠落账后，才能领取
`resume pending → claimed` 并调用 `resumeEdgesForAccount`。warned/frozen 的竞态拒绝落 `refused`
并正常推进 cursor，不能 throw 后永久毒住 `risk.command`。Edge resume 自身若失败，风险状态仍是
applied；结局必须同时保留正常写后态与稳定的 `edge_resume_failed`。若 resume 已领取但回执落账失败，
at-least-once 重放不得把第二次幂等返回的 0 冒充第一次真实数量，也不得重复恢复；以稳定
`edge_resume_result_unknown` 收口。

automation owner migration 为 `risk_command_outcome` 增加 recovery 结果字段与 `refused` 终态；
增加 `env_key`、`applying` 与 resume 阶段；不把结果塞进 `reason` 字符串。客户可见
reason/resumeError 只用稳定公共枚举，原始 PG/controller/Edge 错误只留服务端日志。
现有 signal/quota outcome 形状保持兼容。

### D3. 客户 recovery 用 200/202 + account-scoped poll 保持写后诚实

客户 POST 仍只接受空对象与路径 `envKey`。api 完成 ownership/platform/account 解析后：

- 当前 normal：不提交命令，直接 200 返回幂等写后真态、`changed=false`；
- 当前 warned/frozen：409，逐位不改；
- 当前 restricted：提交 recovery command，并在一个固定、有界窗口内读取结局；
- 窗口内 applied：200 返回现有写后真态与 Edge resume 结果；
- 仍 processing：202 返回 `envKey + commandId + state=processing`，绝不返回旧 restricted
  作为成功；
- refused / failed / unknown：分别映射为可区分的 409 / 503 / 404。

新增同环境路径的 recovery outcome GET。它重新执行客户 JWT、环境 ownership、Facebook 平台与
账号绑定检查，再调用 account-scoped outcome；不能只凭 commandId 查询。

Edge 主进程对 202 使用固定有界 poll，renderer 保持按钮 pending 与 `账号受限`。只有 200 且同
`envKey`、写后 `normal` 才清除限制；轮询耗尽或断线显示“已受理但尚未确认”，不伪装失败，也不本地解锁。
这是由异步命令与现有写后真态契约共同要求的 observed need，不增加可调 retry knob。

### D4. 发布 trigger 只承诺受理；durable approval 仍是承重通道

`PublishDispatchTriggerPort.triggerApproved` 接收：

```ts
{
  requestId: string;
  revision: number;
  executionTarget: 'dev' | 'ol';
  kind: 'decision_recorded' | 'human_reconfirm';
}
```

响应只含 `{accepted:true, disposition:'queued'|'duplicate'}`。route 必须验证
`publish-<recordId>`、target 与当前活跃授权 revision；不匹配时具名拒绝。它只启动/唤醒 dispatcher，
不等待分钟级 `dispatch()`，也不返回任何平台结果。

- `decision_recorded` 来源是 api owner 的事务型 `PublishApproved` outbox relay，按
  `(requestId,revision)` 可重复投递；dispatcher 与授权复核负责幂等。
- `human_reconfirm` 只来自已通过操作员鉴权、且 `alreadyDecided=true` 的人工重复批准；
  必须再次进入 `humanApproval` 路径以清熔断并 kick drain，不能被首写 revision 去重吞掉。
- schedule auto approve 只能产生 `decision_recorded`，不得取得 `human_reconfirm` 权力。

trigger 不可达时，本次审批仍已真实落在 `pending_dispatch`；入口返回“已授权/待下发”而不是“发布失败”，
同时响亮记录 trigger failure。automation 的 pending scan 恢复该任务。没有 durable authority 行时，
任何 trigger 都不能下发。

### D5. publish approval authority HTTP 复用既有形状并补 revision CAS

api 内部 server 暴露七个窄方法：

- `getApproval`
- `listPendingDispatch`
- `voidApproval`
- `markDispatching`
- `markConsumed`
- `releaseToPending`
- `setBlockedReason`

所有状态写带 expected `revision`，owner store 用 requestId + active revision 条件更新；旧轮次命令
不能修改新授权。dispatch progress 只推进同一授权轮次的状态，不自增授权 revision；只有既有轮次作废后
重新作出的决定才取得下一 revision。合法无行/stale revision 与 owner/transport failure 必须区分；
list 失败不得返回空列表。

现有表的主键、活跃唯一索引和 outbox 唯一键仍以全局 `requestId` 为冲突域。DEV/OL 共库期若另一
target 已占同一 id，3b 的首写冲突读回只能查本地 target：本地无活跃行就以稳定错误 fail closed，
不得复用另一 target 的决定、revision 或据此发 `human_reconfirm`。把这些物理键改为 target-scoped
需要 `DROP INDEX` / 约束替换，按迁移纪律属于独立 contract change，不能伪装成 3b expand。

独立 automation 模式的 `PublishDispatcher` 经 HTTP client 复核授权、扫描与写进度；monolith/core
经同一 port 的本地 adapter。两种形态都不让 dispatcher 直接读写 approval store 或 api pool。

approval authority、decision writer、publish-card-exit 的 approval 写方法与 dispatch trigger 共享
`AIDCP_PUBLISH_APPROVAL_INTERNAL_TOKEN` Bearer 鉴权。独立 api/automation/content 模式缺 token
必须在装配这些端口时 fail fast；服务端以定长摘要比较，缺失或错误凭据统一返回
`internal_http_unauthorized`，不得把 target/revision 校验当成调用方鉴权，也不得记录 token。

完整 publish log 十方法和 Facebook media 三方法仍留 4a；因此本 change 只声称 approval authority
已跨进程，不声称独立 dispatcher 的全部反向依赖已经闭合。

### D6. panel event 采用 automation push，不开放 outbox read route

保留 topic `panel.event`、consumer `panel-event-replay` 与既有 topic cursor。把
`PanelEventReplay` 放在 automation，sink 改成可等待的
`PanelEventDeliveryHttpClient.deliver({deliveryId,event,data,originTs})`：

- `PanelEventSink` 支持 Promise，handler 必须 `await sink`；
- HTTP reject 时 cursor 停在失败 id 前，下一轮按序重投；
- `deliveryId=event_outbox:<target>:<id>` 只用于诊断，不承诺 exactly-once；
- API fanout 完成本地分发后返回 ack；无浏览器订阅也视为已消费，与现状一致；
- API fanout 后响应丢失或 cursor 更新前崩溃会重投，浏览器允许看到重复；
- 单 automation 实例按 outbox id 串行等待，连接存续期间保序；浏览器断线窗口不补。

api 新增 `PanelEventFanout`，对 panel WS 只暴露 kernel `EventFanoutPort.onAny`，对内部 ingress
暴露 delivery 方法；不复制 automation `EventBus`。`startApiInternalApi` 按 capability 独立注册，
不能因 config-mirror sink 缺席而把 panel ingress 和其它 owner route 一起关闭。

选择 push 而不是 read/ack：现有 `InternalHttpServer` 是缓冲式 POST request/response；read route
需要重新定义 cursor 所有权、read/ack、长轮询与断线续接，SSE 还会重写 HTTP 骨架。push 可逐字复用
`OutboxConsumer` 与 config-mirror relay 的失败不推进范式。

### D7. server-first、包同步与验收层次

先在 `aidcp-cloud` 事实源实现 contract、owner adapter 与直接 loopback tests，再同步：

1. `aidcp-kernel`：纯 types/ports；
2. `aidcp-transport`：共享 route/client；
3. `aidcp-api` / `aidcp-automation`：各自 owner/client 与聚焦组合根接线；
4. `aidcp-content`：排期免审的 approval caller token 接线与 transport pin；
5. `aidcp-edge`：customer recovery 202/poll source；
6. 只有真实 import 新共享成员的仓更新精确 pin。

`aidcp-automation` 继续使用本地 transport 源码，不安装第二份 transport 包。`sync-split-repos`
对受管源/pin/migration 做机械对账，手写 `main()` 只报告不覆盖。

验收分层：

- unit/direct HTTP/outbox/WS loopback：证明方法面、错误、cursor、CAS 与本地 fanout；
- DEV monolith：证明现役服务零回归，8093/8094 不因本批验收被额外打开；
- 独立 api/automation runtime：只有后续所有 4a/4b 启动依赖也闭合并实际启动后，才做
  8093/8094、断链积压/恢复补投、真实客户 recovery 和 panel WS 探针。

3b 完成后若 4b 仍使 panel 启动失败，部署保持 monolith并记录具体缺口，不重复一次已知会失败的
三进程切换来换取“尝试过”的表面证据。

## Risks / Trade-offs

- [recovery 已应用但 HTTP/ack 丢失] → command id + account-scoped outcome 提供续查；UI 保持 pending，
  不把网络失败改写为业务失败。
- [recovery 消费时状态已变化] → controller 返回值驱动 `refused`；不按提交前读态推断，也不堵主题。
- [outcome 写失败导致 recovery 重放] → `recoverRestricted` 对 normal 幂等；重放仍以最新写后真态落结局，
  测试明确不允许再次扩大权限或恢复 warned/frozen。
- [trigger 被误读为发布成功] → DTO 不含业务状态；验收源码守卫禁止 accepted/queued 映射为
  dispatching/submitted/published。
- [人工重批被去重吞掉] → 独立 `human_reconfirm` kind，并测试自动批准无权清熔断。
- [旧 revision 写坏新授权] → 七个 authority 写方法全部 CAS；stale 明确拒绝。
- [另一 target 的全局 requestId 唯一键挡住本地首写] → 冲突后只读本地 target；无本地行即稳定
  fail closed，绝不跨 target 复用授权。解除该 liveness gap 需要独立 contract migration，不在 3b
  或 DEV-only 部署中偷跑。
- [panel API 断链导致 outbox 积压] → handler await HTTP，cursor 不前进；轮询承重、LISTEN 加速，
  backlog/stats 保留可观测。
- [慢/离线浏览器期待历史补发] → 明确维持 live-only；需要客户端续传时另立 API inbox/cursor change。
- [api/automation 提取仓全量仍红] → 运行聚焦切片与事实源全量门禁，逐项记录既有 main 缺口；
  不用 3b 局部通过冒充两仓可独立启动。

## Migration Plan

1. 建立 3b 多仓隔离 worktree，记录 3a 后的 source/pin/migration/测试基线。
2. 在事实源先实现 risk recovery outcome、approval authority/trigger 与 panel event push，
   运行 focused、acceptance、全量、typecheck 与边界/属主门禁。
3. 发布 kernel/transport，更新 api/automation/content/edge 等真实消费者与精确 pin；运行各仓聚焦
   与可用全量门禁，再按依赖顺序串行 rebase、fast-forward 集成并推送默认分支。
4. 从干净 Cloud 默认分支部署 DEV monolith，验证现役 8787/8090/客户 API/Feishu/owner schema
   与 PostgreSQL；不额外开放内部 listener。
5. 运行八仓最终同步对账，分别记录受管成员/pin/migration 与预期 hand-written root 差异，
   回写 §10 与 tasks。

回滚按依赖逆序恢复 consumer pin 与 owner route。automation migration 只做 nullable additive columns /
check 扩展，不删除历史 outcome；旧代码可忽略新列。若 DEV 单体回归失败，回滚 Cloud 默认分支与服务；
Edge 未打包，无安装客户端回滚动作。

## Open Questions

无待拍板问题。三条核心选择已由当前代码与既有产品契约约束：recovery 必须异步可续查、approval
trigger 不是发布结果、panel event cursor 留 automation。剩余完整 publish/content authority 与同步镜像
明确留 4a/4b；approval 物理唯一键的 target-scoped contract migration 是已知后续工作，不属于 3b。
