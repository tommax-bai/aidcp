## Context

`docs/data/batch34-composition-root-survey.json` 在 3a 之前记录了 api 六组、automation 五组同步依赖。
以 `aidcp-cloud@67941e4`、3a/3b artifacts 和当前 `server.ts` 重新逐条对账后，这 11 组仍是
独立组合根的真实缺口，但原 A3 的四个方法里只有三个是同步读：`resumeEdgesForAccount` 会删除
automation 进程内 `pausedEdges`，必须移出镜像清单。3a/3b 交付的是异步 owner HTTP、
受限恢复、审批/触发与 `panel.event` delivery，不与剩余同步读重叠。

需要明确剔除的相邻项包括：3a 四类限频面板 facade、FB 面板与群路由，3b restricted recovery、
approval authority/trigger、panel event fanout，以及已经存在的 role-model-selection 镜像。
这些都不得再次包装成 4b 的“镜像”。4a 的发布台账、授权台账、互动写入闸、回复策略、人设写服务
等异步 authority 端口也不在本 change；`resumeEdgesForAccount` 作为 api → automation 的反向副作用
命令由 4a 增加 target/auth/idempotency/result-unknown 契约，4b 只以 census 保证它没有混入 snapshot。

约束如下：

- 这些调用点是同步的，部分位于每次 Edge 下发、调度判定或角色选择的热路径，不能在调用点发 HTTP。
- api 与 automation 最终使用各自属主数据库；不得把另一属主的 pool 注入本进程，也不得创建跨库事务。
- `event_outbox` 属 automation，现有 topic cursor 已按 `(consumer, execution_target, topic)` 隔离；
  `config_mirror_version` 属 api，已有 automation transactional outbox → api bump sink。
- DEV 当前仍是未设置 `AIDCP_SERVICE` 的 monolith。单体本地对象直连不是跨进程验收证据。
- `dev` / `ol` 长期共享 PostgreSQL；所有持久 cursor、projection 和 outbox 行必须显式过滤
  `execution_target`。

## Goals / Non-Goals

**Goals:**

- 给 11 组同步依赖逐项确定 owner、消费进程、传输形态、本地同步读形态与失败语义。
- 用 owner snapshot 作为自愈承重面，用 cursor 防回退/重复；automation 动态事实使用本域
  `event_outbox` 加速传播。
- 让 api/automation 只读本进程内存或本属主数据库里的投影，并在第一次装载、陈旧、断链和恢复时
  给出可测试的 ready/unknown/fail-closed 结果。
- 保持外部 HTTP/WS DTO 的既有业务含义；需要表达 unknown 时扩展诚实的可选状态，
  不把 unavailable 压成 0、false、空数组或“未配置”。
- 让 Cloud 事实源、kernel/transport 派生包及 api/automation 组合根可分别验证。

**Non-Goals:**

- 不实现 4a 的异步 authority 端口，不重复 3a/3b 的 owner routes 或 panel event delivery。
- 不改变账号、配置、发布、风险或 Edge presence 的写权归属。
- 不以本地 presence 镜像执行 `resumeEdgesForAccount` 或任何其它有副作用的 automation 命令。
- 不让 api/automation 直连对方数据库，不以共享 PostgreSQL 暂时存在为理由保留跨属主 SQL。
- 不新增“镜像失败时继续用代码默认值”的兼容开关；回滚到 monolith 是部署回滚，不是语义回落。
- 不在此 change 启动 OL、不制作 Edge installer，也不把源码路由测试写成三进程运行证据。

## Decisions

### D1. 11 组 remaining inventory 逐项裁决

| # | 同步依赖与 owner → consumer | 4b 处置 | 未装载/陈旧语义 |
| --- | --- | --- | --- |
| A1 | automation `sessionConfigStore.weekActiveMask()` → api | `session_config_global` owner snapshot；既有 automation config-bump outbox 唤醒 api，api 本地保存全局周掩码 | 首装失败 api not-ready；陈旧保留最后好值并标 stale，不回落代码默认 |
| A2 | automation 排期自动化静态目录 → api | 将编译期静态表与纯查询实现提入 kernel；两进程引用同一构建产物 | 无网络、无陈旧态；kernel pin 不一致拒绝启动 |
| A3 | automation Edge presence 三读 `edgeCount` / `onlineEdgeCount` / `resolveEdgeIdForAccount` → api | runtime snapshot + `event_outbox` 变更通知；api 内存镜像提供同步计数/解析 | unknown/stale 时不得报 0 或“离线”；D5/preflight/offboard 均拒绝肯定动作 |
| A4 | automation publish in-flight ids → api | runtime snapshot + outbox 通知；按 recordId 集合原子替换 | unknown/stale 时 lifecycle 显式 unavailable，不能显示“批准但未动作” |
| A5 | automation captcha availability → api | 纳入 automation runtime snapshot；显式区分 disabled / available / unavailable / unknown | 启用但未装载时 api not-ready；disabled 是配置真态，不是 unknown |
| A6 | 每进程 config mirror health → api panel | api 本地 health 直接读；automation health 经 runtime snapshot 投影，聚合时保留 source `asOf` 和 delivery freshness | 传输陈旧时 automation 部分显示 unavailable，绝不沿用旧 `fresh` |
| B1 | api persona/binding/soul → automation | api owner 全量 snapshot；automation 原子替换本地查表镜像 | unknown ≠ unbound；安全入口在未装载/陈旧时停手 |
| B2 | api client environment automation gate + slow-start anchor → automation | api owner 全量 snapshot；automation 本域投影带 `fresh_until` | 缺行、unknown、陈旧均 fail-closed；不得当作允许下发或“无慢启动” |
| B3 | config freshness/stop-work ambient 实现 | 将无业务属主的判定运行时变成可在每进程实例化的共享实现；每个进程只安装自己的 refresher | 已声明有远端镜像却未安装 source 时 stale/not-ready；只在真实 monolith 本地权威模式允许 local-ready |
| B4 | api account identity/platform/createdAt/status → automation | 扩充现有 `automation_account_projection`；目标解析/状态字段是 gate，纯展示名允许最后好值但须暴露 stale | 昵称歧义、缺行或陈旧不选账号；暂停态 unknown 不得当 normal |
| B5 | api content schedule/hot lead/FB comment/FB join 配置 → automation | owner snapshot + `config_mirror_version` cursor；automation 本地配置镜像原子替换 | registry 中 gate 项陈旧停手；parameter 项保留最后好值并告警，首次装载一律 not-ready |

A1–A6 是 api 组合根缺的 automation 事实；B1–B5 是 automation 组合根缺的 api 事实或本地实现。
表中“snapshot”均指完整、可替换的事实集合，不是把远端 store 的每个同步方法逐个变成 HTTP。
`resumeEdgesForAccount` 不在 A3：它改变 automation 内存态并返回真实恢复数。4a 必须给它独立的
api → automation command，校验本地 target/Bearer，使用稳定 requestId 幂等，并在响应丢失时返回
`result_unknown`，不得从 presence 镜像推算或重放恢复。

### D2. 所有远端快照使用同一个带 target 的信封

kernel 定义不含 IO 的 `SyncReadSnapshotEnvelope<T>`：

```ts
interface SyncReadSnapshotEnvelope<T> {
  contractVersion: 1;
  executionTarget: 'dev' | 'ol';
  factScope: 'shared' | 'target';
  stream: SyncReadStream;
  cursor: string;
  asOf: number;
  freshUntil: number;
  complete: true;
  value: T;
}
```

`cursor` 是属主、fact scope、stream 内单调且不透明的十进制序列；消费方按契约的无符号整数比较并持久化，
不得做字符串字典序比较或从时间戳猜顺序。`executionTarget` 标识产生/消费快照的服务实例，
`factScope` 则区分事实本身是 DEV/OL 共享还是 target-specific。快照必须由属主在一致读边界内生成；
值与 cursor 不属于同一生成点时拒绝响应。
空集合只有在 owner 明确给出 `complete:true` 且该 stream 允许空稳态时才可应用。

替代方案是只传 `updatedAt` 或 payload hash。时间戳存在同毫秒并发与时钟回拨，hash 不能表达事件顺序，
都无法证明断链后的缺口，因此不采用。

### D3. api-owner 事实采用“全量 owner snapshot → automation 本域投影”

B1/B2/B4/B5 由 api internal server 提供按 stream 的全量快照。这些 persona/account/environment/config
事实与投影内容是 DEV/OL 共享业务数据，MUST NOT 为它们新增 target-scoped 业务 revision 或复制两份内容。
persona、account status、client-environment gate/slow-start 与四张配置均复用现有
`config_mirror_version`/owner version；4a 落地后的写路径 census 负责把仍未 bump 的相关 mutation
接到现有 key，同一 owner 事务推进，不创建第二套 revision 表。

automation 先在内存/临时表校验完整信封，再用单事务原子替换共享本域投影内容；每个 automation
消费实例自己的 applied cursor/readiness/health 则按 target 分开记录。应用失败不推进实例 cursor；
旧投影保留但该实例继续按原 `fresh_until` 老化。周期性全量拉取是承重与自愈通道，因此即使通知丢失、
进程停机或中间 revision 未消费，也能由下一份完整快照收敛。

不为 api 域另造一套通用事件总线。账号等低基数事实已有全量 snapshot 判例，
四张配置已有 `config_mirror_version`；强行复制 automation `event_outbox` 会增加 inbox/outbox/清理
三套表，却不比完整快照更能自愈。

### D4. automation-owner 动态事实采用“runtime snapshot 承重 + event_outbox 加速”

A1/A3/A4/A5/A6 的 owner adapter 在 automation 进程内生成完整 runtime snapshot。A1 的共享 durable
配置更新继续使用现有 config-bump transactional outbox；A3/A4/A5/A6 在真实状态变化后写
`sync_read.changed` 事件，事件只携带 stream、generation 与 target，不复制整份易变快照。

api 启动或重连时总是先拉完整 snapshot，再恢复既有 outbox topic replay。通知只是提前触发下一次拉取；
即使状态变化与事件写入无法组成数据库事务，周期快照仍会修复。每条 outbox 事件只有在 api 已成功应用
不低于其 generation 的快照并返回 ack 后才推进 source cursor；失败保留 cursor，沿用现有有界轮询 +
LISTEN 唤醒机制。

替代方案是只重放 delta。Edge 连接与 dispatcher in-flight 是内存事实，崩溃时无法从历史 delta
可靠重建；全量 snapshot 必须是承重面。

### D5. snapshot 应用是原子、幂等且不回退的

每个消费实例的 `(target, stream)` 状态至少包含 `appliedCursor`、payload digest、owner `asOf`、
本地 `lastObservedAt`、`freshUntil`、`lastAppliedAt`、`lastError`。大于当前 cursor 的完整快照才可
原子替换 payload。相同 cursor 有两种不同处理：

- 通过当前已鉴权 owner fetch 新取得、payload digest 与当前一致且 `asOf` 前进的 observation，
  SHALL 只更新 `lastObservedAt/freshUntil`，不替换值或 cursor；这对应“权威可达且事实未变”。
- outbox/HTTP 重试得到的历史 envelope（`asOf` 未前进），或相同 cursor 却 payload 漂移，
  MUST NOT 续鲜；前者幂等 already-applied，后者标 invalid。

小于当前 cursor 的快照拒绝但不清值。跨 target、未知 contractVersion、非法 cursor、
`complete !== true` 或结构校验失败均不应用、也不续鲜。

断链恢复顺序固定为：

1. 本地镜像进入 recovering，保留最后好值但不延长 `freshUntil`；
2. 直接向 owner 拉一份新 observation；
3. 原子应用新 cursor，或对相同 cursor 的一致 payload 只续本实例 freshness；
4. 从持久 cursor 恢复 outbox replay；
5. 只有全部 required gate streams fresh 才把进程置 ready。

### D6. ready、fresh、stale 与 unknown 不互相冒充

同步读 adapter 不返回裸默认值，而从本地镜像状态机读取：

- `uninitialized`：从未应用有效 owner snapshot；
- `ready`：已应用且 `now <= freshUntil`；
- `stale`：曾应用但已超过 owner 声明的新鲜期；
- `invalid`：收到目标、版本或结构不合法的快照，保留最后好值但按 stale 处理。

进程 HTTP listener 可以启动用于健康诊断，但业务 readiness 只有在该服务声明的全部 required stream
首装成功后才为 ready；D1 明确标为首装 blocker 的 parameter stream 也必须进入 required 集合。
安全闸的 `uninitialized/stale/invalid` 全部 fail-closed。非 required 参数镜像在曾成功装载后可继续用
最后好值并告警；从未装载不得用代码默认值冒充 owner 配置。

monolith 允许显式 `local-authority` adapter 直接读同进程对象，并把来源报告为 local；只有
`AIDCP_SERVICE` 未设且 owner/consumer 确实同进程时可用。独立进程缺 remote adapter 必须启动失败，
不得套用“未安装 freshness source = fresh”的历史回滚语义。

### D7. 新鲜度按字段语义分档，不按 DTO 是否有值分档

继续复用 `CONFIG_MIRRORS` 的 gate/parameter 判据和既有 stale 上限，不新增可随意放宽的 knobs。
Edge presence 的 `freshUntil` 由现有 heartbeat/lease 时限导出；runtime snapshot 其他成员使用 owner
已有状态有效期。owner 不得让 `freshUntil` 超过其事实本身的有效期；consumer 只有通过当前
authenticated owner fetch 得到更晚且一致的 observation 才能续本实例 freshness，不得以本地读或
历史 envelope 自行续租。

同一快照含展示与闸门字段时分别暴露状态：

- 展示名等 parameter 字段可显示最后好值并标 stale；
- account status、target resolution、environment gate、persona binding、schedule enable 等 gate
  字段在 stale/unknown 时拒绝动作；
- `0`、`false`、`[]`、`null` 只有在 owner 明确确认该业务值时才是值，不能兼任 unknown。

### D8. 配置健康是消费进程的事实，不是 owner 的全局结论

api 的健康投影只描述 api 本地镜像；automation 的健康投影只描述 automation 本地镜像。
api panel 聚合两份时同时展示 `sourceService`、source `asOf` 与 delivery state。
automation health snapshot 自己若陈旧，整段标 unavailable；不得继续显示其中旧条目的 `fresh`。

这避免当前 monolith 中一个 `ConfigMirrorRefresher.health()` 被误解为“三个服务都健康”。

### D9. target 隔离贯穿 source、transport、projection 与 cursor

owner route 必须从 server-injected deployment target 取 target，拒绝请求体覆盖。target-specific runtime
snapshot、async outbox、topic cursor、消费实例 readiness/health 与清理语句都包含 target 过滤。
消费方仅接受与自身 `AIDCP_DEPLOY_ENV` 相同的信封；缺失或非法 target 时 worker/consumer 不启动。

persona/account/environment/config 的 owner 事实、`config_mirror_version` 与投影内容继续是共享业务数据，
不得按 target 复制或过滤；它们的 envelope 标记 `factScope=shared`，但 dev/ol 消费实例各自维护
delivery cursor/readiness/health，任一实例的成功 observation 不得伪造另一实例的可达性。
Edge presence、in-flight、captcha runtime 与 automation health 标记 `factScope=target`，内容也不得串 target。

### D10. 派生与验收按 source → packages → composition roots 排序

公共 envelope、kernel 静态目录、local freshness/apply runtime 可与 4a 并行。B1/B2/B4 的 owner
写路径、`AccountRosterSourcePort`、`automation_account_projection` 以及 `server.ts` composition root
必须等待 4a landed 后先做 post-4a census，再由 4b 单写者修改；4a 移到 API notification exit 的
display-name consumer 必须从 B4 payload 删除，不能在并行分支重复实现。

事实源随后落 `aidcp-cloud` 并通过 loopback contract、断链恢复和 target acceptance；纯类型/静态目录
派生到 `aidcp-kernel`，HTTP/outbox adapter 派生到 `aidcp-transport`。`aidcp-api` pin 两包，
`aidcp-automation` 只 pin kernel 并继续使用本地 owner transport 源码，避免同一 transport 模块两份。

4b 完成必须同时满足：

- Cloud acceptance、全套测试、typecheck、boundary/sync census；
- kernel/transport 构建与 dist export 探针；
- api/automation 受管组合根严格 typecheck、启动/ready/failure 测试；
- console 总览/publish queue 与 Edge 客户发布队列的 unavailable UI/DTO 聚焦测试；
- DEV monolith 零回归且 split listeners 仍关闭；
- 独立 api/automation 在命名 target 上启动后，实际完成 bootstrap、event backlog replay、
  断链陈旧、恢复 ready 与 target 隔离探针。

若 4a 尚未让两个独立组合根完整启动，最后一项必须明确记录为 not_started/not_ready，
不能由 loopback HTTP 或 monolith 代替。

## Risks / Trade-offs

- [11 组一次落地面较大] → 以 D1 的 11 个 inventory 编号作为测试和任务矩阵，每项可独立验收，
  共享 envelope/runtime 先行，组合根最后串接。
- [owner 写漏现有 bump 导致投影不刷新] → 4a 后 owner 写路径覆盖静态 census；复用既有
  `config_mirror_version` key，测试要求每种相关 mutation 后共享 cursor 前进，不新增平行 revision。
- [runtime event 与内存状态非事务] → event 只作唤醒；完整 snapshot + generation 承重并自愈。
- [保留最后好值可能被误当新鲜] → value 与 state 分离；health/DTO 必须携带 stale/unknown，
  gate 读不因“有旧值”而放行。
- [ready gate 令依赖故障暴露为服务不可用] → 这是安全边界的有意结果；health 明确列出阻塞 stream，
  不增加伪默认或静默旁路。
- [共享内容与实例健康混在一张表] → projection payload/version 保持共享，实例 cursor/readiness/health
  单独 target-scoped；schema acceptance 同时证明“共享值一致”和“实例健康不串 target”。
- [4a/4b 并行修改同一热点] → 公共 contract/runtime 可并行，roster/persona/environment/account/root
  明确以 4a landed 为 barrier，4b post-4a census 后单写。

## Migration Plan

1. 并行完成 kernel envelope、静态目录、local freshness/apply runtime 与不触碰 4a 热点的
   automation runtime snapshot/outbox。
2. 等 4a landed，按新默认分支重跑 census；由 4b 单写者完成 B1/B2/B4 owner bump/roster/projection
   和两份 composition root，复用现有 owner version。
3. 若实例 cursor/readiness 需要新表，只做 expand-only、target-scoped 的消费状态迁移；共享业务事实、
   `config_mirror_version` 与 projection payload 不加 target 分片。核验 owner ledger 与 rollback 备份。
4. 派生并发布 kernel/transport，随后更新 api/automation 精确 pin；同步更新 console/Edge 加性 DTO/UI。
5. 先在 DEV monolith 验证零回归、health 与既有 listener 拓扑；不据此声明跨进程镜像已生效。
6. 4a/4b 组合根都 ready 后，在 DEV 启独立 api/automation：验证首次 bootstrap、outbox 积压、
   断链越过 freshUntil 后停手、恢复后 cursor 续跑及 dev/ol 隔离。
7. 回滚时先停独立 units 并回到已验证 monolith 版本；expand 表保留。不得通过关闭 ready/freshness
   判定或注入默认值来维持 split 进程。

## Open Questions

无阻塞问题。各 stream 的具体字段以 D1 的消费点最小集合为准；实现时不得为了“以后可能用”
把完整 owner row、密钥、连接信息或无消费者字段带入快照。
