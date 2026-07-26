## Why

3b 已交付 publish approval authority、decision writer/trigger 与 panel event push，但 `automation`
组合根仍直接构造或调用多项 API 属主能力，因而独立进程仍会持有 API 数据库连接或在缺依赖时静默降级。
§10 的旧“automation 要 API 侧 11 条”发生在 3b 之前且漏过传递依赖，不能再作为实施清单。

## What Changes

- 重新逐调用点盘点 3b 后仍由 automation 真消费者调用的 API authority/command，只为自然异步的调用建立
  versioned internal HTTP port；API 保持 owner store、事务、校验与业务拒绝的唯一实现方。
- 把 `PublishDispatcher`、`ScheduledPublishReconciler` 与 scheduler 的传递消费者纳入 publish-log
  事实账：该组为 19 方法，而不是只统计 server 直接调用的 10 方法；API 本地
  `listPendingApprovalIds` / `pendingPublishPreviewForRecord` 不开放。稿件预览由 API owner 本地读取后，
  通过 API→automation `applyPublishUiUpdate` command 推送，automation 不反向逐条查询 API record。
- 补齐账号花名册取源，并在同一 change 把 Facebook `importTargets` / `replaceTargetScopes` 加回 3a
  刻意留空的运营面：scope 判否前可反向刷新 automation 本地账号投影，刷新失败、空结果或陈旧结果不得
  伪装成“无账号”或产生部分 scope 写。
- 把旧 4b 清单中误分类的 `resumeEdgesForAccount` 收回为最窄 API→automation 写命令：它删除
  automation 进程内 `pausedEdges`，返回真实 resumed count，并与 API-owned account-state resume 的
  先后顺序、部分成功和结果未知分开表达。
- 把 Facebook `importTargets` / `replaceTargetScopes` 正式定义为同方向的窄 automation commands，
  使用稳定 commandId、owner 去重/结果未知、version/target/Bearer，不能只因 AccountRoster 反向刷新
  已接通就沿用未鉴权 route。
- 把 `reconcileCleanupAdmissions` 的双属主循环移到 automation：API 只暴露 admission-ledger
  snapshot reconcile、pending claim 与 CAS receipt primitives；automation 本地读取/物化 offboard，
  任一网络边界都不持 owner 事务。
- 收窄通知出口为唯一结构化 `deliver`；chat resolution 与 bind 留在 API 本地。删除 automation
  无消费者的 `claimExecutionTarget`。
- 保留 `AccountPersona.persist` 的 API authority，并为 `AccountPersona.generate` 增加相邻的
  API→content `PersonaGeneratorPort`；content 独占生成角色/LLM，API 不复制 content 实现。
- 收口发布台账、账号归属与运行期账号命令、互动写入闸/审计/回复配置、账号人设、环境握手、Edge
  发布命令、配置类异步操作及通知投递等剩余直接调用；保留 content 与现有 3b approval 契约的独立边界。
- 所有新增 authority/command route 使用内部 Bearer 鉴权并绑定本地 `execution_target`；独立
  api/automation/content 缺少 URL、合法 target 或凭据时 fail fast/fail closed，不回落为跨属主
  数据库连接或本地复制 owner 实现。
- 读失败保持“未读成”而不是空/null/default；带副作用请求保留 CAS/幂等键与
  `result_unknown`，不得把响应丢失冒充失败、成功或安全重试。
- 采用两道独立门禁：source-derived scoped census 证明本 change 的 **20 组/55 slots**
  （automation→API 16/50、API→automation 3/4、API→content 1/1）闭合；independent-root
  blocker ledger 则持续枚举 4b 同步镜像以及 PersonaGenerator 之外的 content-owner 依赖。4a 只证明
  API authority scoped closure，不能把 scoped census 通过写成 full root 闭合或独立 boot。
- 源码、DEV monolith 与独立进程运行证据继续分层记录；blocker ledger 未清零且独立 units 未实际启动前，
  不声明三进程互通。

## Capabilities

### New Capabilities

- `cloud-automation-api-direct-ports`: automation 调用 API 属主 authority/command 的方法面、鉴权、
  target 隔离、CAS/未知结果、Facebook scope 写配对及分层验收契约。

### Modified Capabilities

无。现有产品行为、外部 API/协议与 3b publish approval 契约保持不变；本 change 新增的是内部组合根能力。

## Impact

- 主要事实源：`aidcp-cloud` 的 kernel contracts、API/automation/content owner adapters、
  internal HTTP transport、三端 composition wiring 与聚焦契约测试。
- 派生仓：`aidcp-kernel`、`aidcp-transport`、`aidcp-api`、`aidcp-automation`、`aidcp-content`；
  只有真实消费新端口的
  仓更新精确 package pin。`aidcp-automation` 继续使用本地 transport 源码，不安装第二份 transport。
- Control：`sync-split-repos` 成员清单、边界/属主门禁、§10 的 3b 后精确方法账与交付证据。
- 不改 Edge/Console 外部 DTO，不制作 Edge installer，不部署 OL，不在本 change 启动或声称完成三进程拓扑。
  4a 的交付边界是 API authority scoped closure；full root 仍受 4b mirror 与 content-owner blocker
  ledger 约束。
