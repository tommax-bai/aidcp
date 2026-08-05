## Why

Cloud→Edge 的「可下发命令登记表」是**两份手工维护的副本**，分别在：

- `aidcp-edge/src/client/operation-registry.ts` 的 `CLOUD_OPERATION_REGISTRY`
- `aidcp-cloud/src/comm/operation-registry.ts` 的 `AUTOMATION_OPERATION_REGISTRY`

两份除类型名外逐行相同，**只差两条**——边缘那份有 `identity.read_current` / `identity.read_self_profile`，云端那份没有。于是云端每次要发这两条命令，都在自己的出口闸（`src/comm/ws-server.ts` 的 `pushToEdges`）被判 `operation_unclassified` 拒绝下发、返回投递数 0。

**这条漂移现有闸门一个都抓不到**：两份都写成 `satisfies Partial<Record<MessageType, …>>`，`Partial` 意味着缺 key 不是类型错误；`scripts/protocol-parity` 只对 `protocol.ts` 做逐字对账，不看这张表；两仓各自的 typecheck 与验收用例也都只看自己那一份。CLAUDE.md §2 已就同类形态记过两次代价（主动命令路由白名单、`action.completed` 动作名口径），这是同一族的第三处。

2026-08-05 生产实测坐实它长期为真、且两个环境都中：

- OL：`identity.read_current` 近三天 37 次尝试、37 次 `sent=0`、37 次「本人昵称采集超时（edge 静默 ~20s）」，**零成功**；
- dev：同批 14 次尝试全数超时，出口日志另见 `identity.read_self_profile` 6 次被拒；
- 与 2026-08-05 的 OL 上线**无关**——上线前该路径同样从未成功，只是失败说法是 `identity_capture_command_unavailable`。

**代价不在昵称**。昵称有别的来源（系统建号时即知其注册名），今日新建 20 个账号 20 个有昵称、其中仅 5 个手动设置，所以这条通道全废也看不出来——它是一处**沉默缺陷**。真正的代价在第二个消费方：边缘 `src/client/identity-command-gate.ts` 把这两条命令放进**身份救援放行清单**。当运行期身份落到「不知道浏览器里登着谁」的终局时，节点拒绝一切代表该账号的动作，只放行少数几条读 / 收尾 / 救援命令，而这两条之所以在清单里，正因为它们是**唯一能问出「现在到底登着谁」、把这个终局解开的事实来源**（该文件原话：「拦掉等于把灯关了」）。云端发不出去 ⇒ 那盏灯在云端这一侧本来就没接上：**一旦有节点落入该终局，它结构上不可能靠这条通道自救**。

（2026-08-05 实测 OL 当前无节点卡在该终局；日志中 35 条 `reels_identity_unresolved` 是 Reels 翻页的另一回事，已核。所以这是**隐患**，不是正在烧的火。）

## What Changes

- 云端登记表补上 `identity.read_current` / `identity.read_self_profile` 两条，分类与边缘逐字一致（`page_automation`）。
- 新增**跨仓对表闸** `scripts/operation-registry-parity`（控制仓），比对 `aidcp-edge` / `aidcp-cloud` / `aidcp-automation` 三方的 Cloud→Edge 登记表：**键集合 MUST 相同，且同名键的描述符四个字段 MUST 逐字相同**。不一致即 exit 1 并打印差集与差异字段。
- 该闸 MUST 落在控制仓而非任一子仓：判据需要同时打开两个仓的文件，单仓视角结构上做不到——与 `scripts/protocol-parity` 同一理由、同一形态。
- 参与方少于两份时 MUST exit 1（「没得比」MUST NOT 被读成「比过了，一致」），与 `protocol-parity` 口径一致。

**明确不做**：不把两份表改成穷举 `Record<MessageType, …>`。96 个消息类型里只有 46 条是 Cloud→Edge 命令，其余 50 条是边缘上报或应答；强行穷举要为它们逐条写「不是命令」，把一张读得懂的命令表变成噪音表，且真正的判据（两份是否一致）它依然抓不到——那正是本 change 要补的闸。

## Capabilities

### Modified Capabilities

- `client-core-browser-executor-separation`: 在既有「每项操作 MUST 由集中式注册表显式分类」之下补一条约束——当该注册表以多份副本存在时，副本间 MUST 一致，且不一致 MUST 由机械手段可检出。原有的分类词表、`operation_unclassified` fail-closed 判据、页面准入链，全部不变。

## Impact

- `aidcp-cloud/src/comm/operation-registry.ts`：+2 条登记。
- `aidcp/scripts/operation-registry-parity`：新增（控制仓，无构建链，Python 3，与 `protocol-parity` 同形）。
- `aidcp-automation/src/comm/operation-registry.ts`：派生物，经 `scripts/sync-split-repos --apply` 同步，MUST NOT 手改。
- `aidcp/scripts/land-change`：接入上述对表闸（没人跑的闸不是闸）。
- **`aidcp-edge/src/client/edge-client.ts`：实装中实测发现的第二道堵点。** 云端补齐登记表后 `sent=1`，但边缘仍静默 20s——`EdgeClient` 的 onMessage 主动命令路由白名单里同样没有这两条，信封落到「其他主动消息暂忽略」被静默丢弃，`command-mapper` 的映射与 `browse-session` 的回报分支因此永不可达。正是 CLAUDE.md §2 点名的第 4 处同步点。同仓补一条**反向结构断言**：以登记表为事实源逐条去路由源码找分派点（原有的是手抄清单，对「漏抄」结构上是瞎的）。
- 不改协议 v2（不新增 / 删除 MessageType，两份 `protocol.ts` 不动）、不改数据库 schema、不改风控状态机。
- 部署：默认 `dev`。OL 需用户明确要求方走发布分支。
