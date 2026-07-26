## Why

3a 已交付 automation → api 的第一批单向异步端口，但 api 独立进程仍有三条不能靠普通 CRUD
包装解决的跨域残留：客户解除受限必须等 automation 单写者给出写后真态，批准后的发布触发必须同时保留
持久授权补偿与人工重批清熔断语义，面板实时事件仍由 api 直接读取 automation 的 outbox。若不先成对
收口这三条，两个仓可以各自编译通过，真实分进程后却会出现提前恢复 Edge、批准已落库但触发丢失，
或 api 继续持有 automation 数据库连接。

## What Changes

- 为 restricted-only 恢复补齐跨进程命令与结局契约：api 只提交命令并按账号回读；
  automation 在 `RiskController` 真正应用后才恢复 Edge，并返回可区分的 applied / refused /
  processing / failed / unknown 结果。客户接口快速收敛时继续返回写后 `200`；尚未收敛时返回
  `202 + commandId`，由同环境、同账号鉴权的结果端点继续回读，绝不以旧 `restricted +
  changed:false` 冒充成功。
- 建立 api → automation 的短应答发布触发端口，明确区分首写
  `decision_recorded` 与人工重批 `human_reconfirm`。受理只表示唤醒/去重，不表示
  dispatch、submit 或 publish 成功；`publish_approval_decision`、事务型
  `PublishApproved` outbox 与 target-filtered pending scan 继续承担不丢任务。
- 把既有 publish approval authority 的 read/list/void/progress 接口实现为真实内部 HTTP，
  所有状态推进带 revision CAS；automation 不再直接打开 api 授权表。
- 把 `PanelEventReplay` 与 outbox cursor 留在 automation，逐条 await 推送到 api 的内部 HTTP
  ingress；api 使用本地 fanout 服务面板 WebSocket，不再读取/监听 automation 数据库。
- 保留既有 `panel.event` topic、consumer 名、游标、顺序、at-least-once、轮询与 LISTEN
  语义。浏览器断线仍只接未来帧，不在本 change 引入客户端回放或 exactly-once。
- 更新共享 kernel/transport、归属仓源码与精确 pin，并用直接 HTTP、outbox/cursor、审批补偿、
  客户恢复和 WebSocket loopback 测试证明契约。
- 本 change 不补齐 4a 的完整 publish ledger / Facebook 素材端口，不处理 4b 的同步镜像、
  edge presence 通用端口或剩余 api/automation `main()` 缺口，也不以源码/单体测试声称三进程上线。

## Capabilities

### New Capabilities

- `cloud-api-automation-bidirectional-ports`: api/automation 双向内部端口、可靠投递、版本/target
  隔离及运行验收边界。

### Modified Capabilities

- `client-customer-auth`: restricted recovery 在跨进程异步命令尚未终结时增加诚实的 202/poll
  形态，终结后仍返回 automation 写后真态与真实 Edge 恢复结果。
- `edge-companion-ui`: 解除受限按钮保持 pending，遇 202 时按命令回读而不是本地清除
  `restricted`，只在 Cloud 返回写后 `normal` 后更新界面。
- `publish-dispatch-resilience`: 把低延迟 trigger 与 durable approval ledger/scan 分开，
  并保留人工重批清熔断而自动批准不得清熔断的语义。

## Impact

- Control：新增本 OpenSpec change，交付后更新 `docs/cloud-composition-root-trisection.md` §10
  与 `scripts/sync-split-repos` 的共享成员清单。
- Cloud：修改风险命令、授权 authority、发布 dispatcher、事件 outbox bridge、api/automation
  内部 API 与组合根接线；可能新增 automation owner migration 以持久化 recovery 结局细节。
- Shared packages：`aidcp-kernel` / `aidcp-transport` 新增或扩展双向契约。
- Derived services：`aidcp-api` / `aidcp-automation` 接入相应 client/server；`aidcp-content`
  只更新确有消费的精确 pin，不新增直达 automation 的批准触发。
- Edge：只调整客户解除受限的 202/poll 源码与测试；不改 Edge↔Cloud 协议 v2，不构建安装包。
- Deployment：开发完成后先部署 DEV 单体证明零回归。只有后续独立 api/automation 进程实际启动、
  8093/8094 可达并完成断链补投探针，才能声明本批跨进程运行验收；OL 不在范围内。
