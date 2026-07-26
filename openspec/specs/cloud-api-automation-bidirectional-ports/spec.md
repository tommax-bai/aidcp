# cloud-api-automation-bidirectional-ports Specification

## Purpose
TBD - created by archiving change split-cloud-api-composition-root-3b. Update Purpose after archive.
## Requirements
### Requirement: 双向内部端口保持事实属主与数据库边界

api 与 automation 之间的 3b 能力 SHALL 通过具名内部 HTTP route/client 成对交付。每条 3b
服务端路径 SHALL 只调用该能力的事实属主实现；对应消费路径 MUST NOT 为这项能力直接查询对方表、
构造对方 store/controller、import 对方业务实现，或用本地空实现冒充远端成功。整个独立进程只连接
本服务属主数据库仍是 extracted `main()` 与 4a/4b 闭合后的运行时验收门，MUST NOT 由本 change
的 source-mode 接线推断为已经成立。

#### Scenario: api 调用 automation 属主能力
- **WHEN** api 提交 restricted recovery 命令、读取其结局或消费 automation 面板事实
- **THEN** 请求经 automation 内部端口执行，该 API-side 3b 路径不使用本地 automation pool/store 或 `RiskController`

#### Scenario: automation 调用 api 属主能力
- **WHEN** automation 读取/推进发布授权 authority、触发批准后下发，或向 api 投递面板事件
- **THEN** 请求经 api 内部端口执行，该 automation-side 3b 路径不使用本地 API approval store/pool、不直接读写授权表或面板进程内状态

#### Scenario: 远端端口没有就绪
- **WHEN** 必需的 base URL、route、owner 实现或本地 ingress 缺失
- **THEN** 调用以具名不可用错误失败并留下可观测状态，MUST NOT 回落为跨库直连、进程内假实现、零值或成功

### Requirement: 内部请求按版本、目标与关联标识 fail-closed

3b 的跨进程请求 SHALL 使用服务端与客户端共用的版本化契约。涉及 durable command、authority revision 或 outbox delivery 的请求 MUST 携带稳定关联标识；`executionTarget` SHALL 来自服务端注入的 `dev|ol` 运行配置并由接收端与本地目标核对，MUST NOT 由外部客户、面板或 Edge 任意选择。

#### Scenario: 版本受支持且目标匹配
- **WHEN** 调用方发送受支持的 contract version、服务端注入的本地 target 与合法关联标识
- **THEN** 接收端按该版本处理请求，并在响应、日志和持久结局中保留足以关联本次调用的标识

#### Scenario: 版本未知
- **WHEN** 接收端收到未知或缺失的必需 contract version
- **THEN** 接收端在执行任何 owner 写入、Edge 恢复、发布触发或事件 fanout 之前拒绝请求并返回稳定错误

#### Scenario: 目标缺失或不匹配
- **WHEN** 请求的 target 缺失、非法或与接收进程的 `AIDCP_DEPLOY_ENV` 不一致
- **THEN** 接收端 fail-closed 拒绝请求，MUST NOT 改用默认 target、跨 target 查找结局或应用副作用

#### Scenario: approval 内部调用凭据缺失或错误
- **WHEN** 调用方访问 approval authority、decision writer、schedule approval writer 或 dispatch trigger 时未携带匹配的内部 Bearer 凭据
- **THEN** 接收端在读取授权或执行任何写入、熔断清除与 scan 唤醒之前返回稳定的 unauthorized 错误
- **AND** target、revision 与 loopback 来源 MUST NOT 被当作调用方鉴权的替代品

### Requirement: 传输失败不得改变领域结局

内部 HTTP 的 accepted、applied 与 terminal 语义 SHALL 按端口分别定义；连接失败、超时、坏响应、owner 抛错和未知结局 MUST 保持可辨，MUST NOT 被转换为领域成功。通用 transport MUST NOT 自行增加无契约依据的 retry、fallback、兼容分支或默认值；可靠补偿 SHALL 由既有 outbox、authority ledger、pending scan 或具名结果查询承担。

#### Scenario: 响应在副作用后丢失
- **WHEN** owner 已接受或应用请求，但调用方未收到 HTTP 响应
- **THEN** 调用方保持结果未知或按稳定关联标识重读/重投，MUST NOT 猜测成功；重复由该端口声明的幂等、CAS 或 at-least-once 语义吸收

#### Scenario: owner 明确拒绝
- **WHEN** owner 返回 refused、revision conflict、target mismatch 或其他稳定业务拒因
- **THEN** client 原样保留该拒因，MUST NOT 将其改写为网络失败、空结果或成功

#### Scenario: owner 或网络暂时不可用
- **WHEN** 内部 route 超时、断连、返回坏响应或处理抛错
- **THEN** 调用方保留 durable work/cursor 或返回具名不可用，MUST NOT 触发本应等待 owner 真态的 Edge 恢复、发布成功或 cursor 前进

### Requirement: restricted recovery 只以 automation 写后真态终结

restricted recovery 的提交与结局读取 SHALL 由版本化 api→automation 端口承载。提交结果 MUST 带稳定 `commandId`；结局 SHALL 区分 `processing`、`applied`、`refused`、`failed` 与 `unknown`，并按同一 target、同一环境与同一账号读取。只有 automation 单写者真正应用命令、回读账号为 `normal`，并先可靠落下领域 `applied` 结局后，才可恢复对应 Edge。

#### Scenario: 命令尚在处理
- **WHEN** api 已提交 recovery 命令，但 automation 尚未产生 terminal 写后真态
- **THEN** 内部端口返回同一 `commandId` 的 `processing`，api 不把旧 `restricted` 或 `changed:false` 当作完成

#### Scenario: 命令应用成功
- **WHEN** automation 单写者应用命令并回读到该账号为 `normal`
- **THEN** automation 记录 `applied` 写后真态并恢复该账号对应 Edge，api 后续查询取得相同 terminal 结局

#### Scenario: 命令被拒绝或失败
- **WHEN** owner 拒绝 recovery、应用抛错或无法确认结局
- **THEN** 结局分别保持 `refused`、`failed` 或 `unknown`，Edge 维持 restricted，MUST NOT 因 transport 已受理而提前恢复

#### Scenario: 跨环境、跨账号或跨目标查询
- **WHEN** 调用方用另一环境、另一账号或另一 execution target 查询既有 `commandId`
- **THEN** owner 拒绝或返回不可见，MUST NOT 泄露或应用原命令结局

### Requirement: 发布授权 authority 经 revision CAS 访问

automation 对 api 属主 publish approval authority 的 read、list、void 与 progress 操作 SHALL 经真实内部 HTTP 端口执行。所有状态推进 MUST 携带期望 revision 并由 api owner 以 CAS 判定；冲突 SHALL 返回当前真态或稳定冲突原因，MUST NOT 以最后写入者覆盖既有决定。

#### Scenario: revision 匹配时推进
- **WHEN** automation 以当前 revision 提交合法 progress 或 void 操作
- **THEN** api owner 以该授权 revision 原子推进 dispatch state 并返回写后真态
- **AND** progress 写不冒充一轮新授权；只有旧轮次作废后的新决定才取得下一 revision

#### Scenario: revision 已变化
- **WHEN** automation 使用陈旧 revision 推进 authority
- **THEN** api owner 拒绝本次推进并返回稳定冲突证据，不覆盖更新后的批准、拒绝、作废或进度

#### Scenario: authority 读取失败
- **WHEN** api owner 不可达或 authority 查询失败
- **THEN** automation 将本次判定保持为未知/不可用，MUST NOT 将其解释成未批准、已批准、空列表或可继续发布

### Requirement: 批准后触发是低延迟加速器而非发布结局

api→automation 的批准后触发端口 SHALL 区分首写 `decision_recorded` 与人工重批 `human_reconfirm`，并以短应答返回是否受理唤醒/去重。成功响应只表示 automation 已接受触发信号，MUST NOT 表示已 dispatch、已提交平台或已发布；持久授权记录、事务型 `PublishApproved` outbox 与按 target 过滤的 pending scan SHALL 继续承担不丢任务和重启补偿。

#### Scenario: 首次批准触发
- **WHEN** api owner 首次持久化批准并调用 `decision_recorded` trigger
- **THEN** automation 受理一次低延迟唤醒，后续是否 dispatch 仍由 durable authority、target 与既有调度闸决定

#### Scenario: 人工重批触发
- **WHEN** 人工对同一活跃 revision 的既有批准再次明确确认并调用 `human_reconfirm` trigger
- **THEN** automation 可按既有契约清理对应熔断并重新唤醒，自动批准或重复网络投递 MUST NOT 冒充人工重批

#### Scenario: trigger 调用失败
- **WHEN** 批准已持久化但 trigger route 超时、断连或失败
- **THEN** 批准记录保持有效，事务型 outbox/pending scan 后续补偿；api MUST NOT 回滚已提交决定或声称 dispatch 已发生

#### Scenario: 重复 trigger
- **WHEN** 同一 request、revision 与 trigger kind 因超时或重试被再次投递
- **THEN** automation 按稳定键去重或幂等唤醒，不创建第二份授权、不把一次批准解释成多次平台提交

### Requirement: 面板事件由 automation 主动推入 api 本地 fanout

`event_outbox`、`event_outbox_topic_cursor`、`PanelEventReplay` 及其轮询/LISTEN 生命周期 SHALL 留在 automation。automation SHALL 逐条 await 内部 HTTP sink，把 `panel.event` 投递给 api ingress；api SHALL 使用 api-owned 本地 fanout 实现 kernel `EventFanoutPort.onAny` 并由 panel WebSocket 订阅。api MUST NOT 读取或监听 automation outbox，也 MUST NOT 搬入 automation `EventBus` 或向 panel 暴露其写能力。

#### Scenario: 已连接面板收到远端事件
- **WHEN** automation 将一条合法 `panel.event` 写入 outbox，relay 调用 api ingress，且已有通过鉴权的 panel WebSocket
- **THEN** api 本地 fanout 以原始 event、data 与 origin timestamp 广播该帧，automation 在 ingress 成功应答后才推进 cursor

#### Scenario: api ingress 不可达
- **WHEN** HTTP sink 连接失败、超时、返回坏响应或 ingress 抛错
- **THEN** `PanelEventReplay` 的 handler 抛错，automation cursor 停在该 outbox id 之前并告警，下一轮从该条重放

#### Scenario: api 没有已认证浏览器
- **WHEN** api ingress 正常接收事件但当前没有已认证 WebSocket 客户端
- **THEN** 本地 fanout 完成本次进程级投递并响应成功，automation 可推进 cursor；系统 MUST NOT 将它描述成浏览器已收到或为未来浏览器建立隐式 backlog

#### Scenario: 本地订阅者异常
- **WHEN** 一个 panel fanout 订阅者抛错或一个 WebSocket 客户端不可发送
- **THEN** api 隔离并记录该本地失败，不让单个浏览器阻塞 automation 的共享 outbox cursor 或其他已认证客户端

### Requirement: 面板事件保留既有游标、顺序与 at-least-once 语义

3b SHALL 保留 `panel.event` topic、`panel-event-replay` consumer 名、按 `(consumer,target,topic)` 持久化的 cursor、按 outbox id 升序逐条处理、2 秒有界轮询承重与 LISTEN 通知加速。每次 HTTP delivery SHALL 携带由 target 与 outbox id 派生的稳定 `deliveryId`；该标识用于关联和可选去重，但本 change MUST NOT 宣称 exactly-once。

#### Scenario: 3b 切换到主动推
- **WHEN** 部署从 api 直读 outbox 切换为 automation 主动 push
- **THEN** automation 使用既有 `panel-event-replay` cursor 续接，MUST NOT 因改消费者名从 0 重放全部历史或越过尚未投递的行

#### Scenario: LISTEN 通知丢失
- **WHEN** PostgreSQL LISTEN 连接断开或通知在断线期间丢失
- **THEN** listener 有界退避重连，2 秒轮询保持不变并最终发现 outbox 行；通知失败只增加延迟、不改变投递语义

#### Scenario: 应答丢失导致重投
- **WHEN** api 已完成本地 fanout，但 HTTP 应答丢失或 automation 在 cursor 持久化前退出
- **THEN** 同一 `deliveryId` 可再次投递，顺序仍按 outbox id 推进；面板事件允许重复，MUST NOT 把 at-least-once 宣称为 exactly-once

#### Scenario: 提交可见性乱序
- **WHEN** 并发事务先分配较小 outbox id 但较晚提交
- **THEN** consumer 使用既有安全水位阻止 cursor 越过该较小 id，待其可见后仍按 id 升序投递

#### Scenario: 非法面板事件载荷
- **WHEN** replay 读到无法解码为 event/data 的观测行
- **THEN** 系统具名告警并按既有纯观测流策略跳过该行，MUST NOT 伪造帧或让单条坏载荷永久堵住实时事件主题

#### Scenario: 消费方长期离线
- **WHEN** api 长期不可达并超过既有未消费保留上限
- **THEN** pruner 按既有纯观测流策略具名告警被强制剪裁的数量，MUST NOT 将被剪事件声称为已送达或审计留存

### Requirement: 浏览器 WebSocket 继续是无续传的实时观察流

panel 对外事件面 SHALL 继续使用既有鉴权 WebSocket `/ws`、帧大小上限与慢消费者背压策略。本 change MUST NOT 新增 SSE、浏览器 ack、per-client cursor、断线 replay 或浏览器 exactly-once；浏览器断线期间的权威状态 SHALL 由既有 HTTP 读取重新收敛。

#### Scenario: 浏览器断线后重连
- **WHEN** 浏览器在若干事件期间断线并随后重新完成首帧鉴权
- **THEN** 它只接收重连后的未来帧，系统不回放已由进程级 cursor 消费的历史帧，也不声称断线窗口完整

#### Scenario: 慢消费者持续积压
- **WHEN** 某个 WebSocket 客户端发送缓冲持续超过既有阈值
- **THEN** api 按既有策略先跳帧、达到连续阈值后以 slow-consumer 原因断开；其他客户端与 automation relay 继续运行

#### Scenario: 需要客户端级续传
- **WHEN** 产品未来要求浏览器断线补帧或 exactly-once 展示
- **THEN** 该需求必须另行定义 API inbox、WebSocket frame cursor、保留期与客户端 ack，MUST NOT 通过本 change 的进程级 outbox cursor 暗示已经支持

### Requirement: 共享契约、派生仓与运行证据必须分别对账

3b 的 kernel 端口、HTTP route/client 和 wire envelope SHALL 各有单一定义并经精确 package pin 交付真实消费仓；route/client 往返、target/version 拒绝、CAS、outbox cursor、断链补投与 WebSocket fanout SHALL 有聚焦测试。源码、单体 DEV 与独立多进程运行证据 MUST 分开记录。

#### Scenario: 服务端与客户端契约漂移
- **WHEN** 任一侧改动 route、版本、请求字段、结果联合类型或错误码而未同步另一侧
- **THEN** 类型检查、直接 HTTP 契约测试、package export probe 或 `sync-split-repos --check` 至少一道失败并指出差异

#### Scenario: 单体 DEV 零回归
- **WHEN** 3b 源码测试通过并部署默认 monolith DEV
- **THEN** 验收只证明既有单体路径、schema、健康与外部行为零回归，MUST NOT 因 8093/8094 route 已写入源码而声称跨进程已通信

#### Scenario: 独立 api 与 automation 运行验收
- **WHEN** 独立 api/automation 进程使用目标一致的配置启动
- **THEN** 验收须同时证明 8093/8094 实际监听、双方 route 可达、api 无 automation 数据库连接、automation 无 api 数据库连接、断链时 cursor/ledger 保留、恢复后补投、真实 `/ws` 收到事件，并记录部署 SHA、target、健康与错误日志

#### Scenario: 只有 loopback 契约测试通过
- **WHEN** route/client、outbox 与 WebSocket loopback 测试通过但尚未启动独立服务
- **THEN** 交付记录只声明契约和源码路径可用，MUST NOT 声称三进程拓扑、真实部署或真实浏览器断链恢复已经验收
