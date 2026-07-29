## Context

视频号 Edge 当前把浏览器作为授权 sidecar：登录、身份校验和读取探测成功后，加密保存会话并关闭 AdsPower 浏览器，Connector 继续以 API-only 模式同步评论/私信。Cloud 已有 env/account 作用域的 `interaction.auth.reopen`，但该命令表示重新授权，成功后仍会关闭浏览器；Electron workspace 也只在 auth 失效或挑战时显示该入口。因而授权正常时既没有“临时打开浏览器”的契约，也没有受控回到后台的对称操作。

这项变更横跨 Edge、Cloud、Electron IPC/UI 和协议文档。实现必须保持 Cloud 编排、Edge 原子浏览器动作、customer ownership fail-closed、单一在线 Edge 定向及“受理不等于成功”的既有边界。

## Goals / Non-Goals

**Goals:**

- 允许客户在 `active + closed` 时打开当前视频号环境的可见 AdsPower 浏览器，并在 `active + open` 时受控关闭浏览器回到 API-only。
- 浏览器保持打开期间继续使用既有加密 API 会话，auth/capability 状态保持真实，不把“浏览器可见”误写成重新登录成功。
- 所有控制按客户 ownership、`envKey + accountId` 和唯一在线 Edge 定向；请求投递与 Edge 上报的执行真态分离。
- 环境暂停、停止或运行时销毁时收敛手动打开的 sidecar，避免遗留占用。

**Non-Goals:**

- 不把浏览器设为 always-on-top，也不承诺操作系统一定把窗口焦点抢到最前；“前台”表示打开可见的 headful 浏览器现场。
- 不改变首次授权、auth 失效、挑战或身份错配的重新授权流程。
- 不新增评论/私信读写权限，不改变 runtime controls、风控或写入成功判定。
- 不构建或发布 Electron 安装包。

## Decisions

### 1. 新增独立的 `interaction.browser.control`，不复用 `interaction.auth.reopen`

Cloud 向 Edge 下发一个 env/account-scoped 控制消息，payload 包含 `requestId`、`envKey`、`accountId`、`platform=wechat_channels`、`action=open|close` 和 `requestedAt`。Edge active-command routing 校验 scope 后交给 Connector；完成或失败后立即上报新的 `interaction.auth.status`，其中 `browserState` 才是执行真值。

备选方案是把 `auth.reopen(reason=user_requested)` 改成保持浏览器打开。该方案会把“重新建立授权”和“查看现有授权现场”混为一谈，也没有干净的关闭对称语义，因此不采用。

### 2. 客户 API 使用一个幂等的浏览器控制端点

Electron 通过具名 IPC 调用 `POST /environments/:envKey/interactions/browser`，body 为 `{action:"open"|"close"}`，并携既有幂等 header。Cloud 每次回库验证 enabled user、ownership 和权威 interaction binding，再只向该 account 的唯一在线 Edge 投递。成功响应只返回 `status=accepted` 与 `actionRequestId`；不得声称浏览器已经打开或关闭。

备选方案是 Electron 主进程直接调用本机 AdsPower API。该方案绕过运行该账号的 Edge core，无法维护 sidecar/CDP/auth 真态，也会破坏多机定向，因此不采用。

### 3. Edge auth coordinator 持有手动可见状态

Auth coordinator 增加显式 `browser_open` 状态和串行化的 `controlBrowser(action)`：

- `open` 只在有效 session、identity match 且 auth active 时调用 sidecar `open()`，完成后保持 `browser_open`，不执行授权交接后的自动关闭。
- `close` 在 `browser_open` 时调用 sidecar `close()`，完成后回到 `api_only_running`。
- 重复 open/close 为幂等；并发控制按单个 coordinator 串行，避免 open/close 与 reauth 互相踩踏。
- 首次授权及非手动 reauth 仍在验证成功后自动关闭。若 auth 在手动可见期间失效，重新授权完成后保留用户的可见意图，直到明确 close 或生命周期销毁。
- Connector stop/offboard/环境停止路径最终关闭 sidecar。

### 4. UI 只用后续 auth projection 宣告结果

Workspace 在 auth active 时按 `browserState` 显示：closed → “打开浏览器”，open → “转入后台”，opening/closing → 禁用按钮并显示进行中。点击后仅显示“已请求…等待 Edge 状态”；轮询拿到目标 `browserState` 后才显示完成态。auth 失效/挑战仍显示原“重新登录/处理验证”入口，两类动作不共用文案。

## Risks / Trade-offs

- [可见浏览器增加资源占用] → 由用户显式打开，并提供对称“转入后台”；pause/stop/offboard 强制收敛。
- [命令已投递但 Edge 执行失败] → API 只报告 accepted；Edge 上报 `browserState=unavailable` 或保持原状态，UI 不宣称成功。
- [打开浏览器时平台身份发生变化] → 现有身份校验和 API failure 路径继续 fail closed；浏览器控制本身不重绑 identity。
- [旧 Edge 不认识新消息] → Cloud 只向协商新 capability 的在线 Edge 暴露/投递控制；旧客户端 API 返回稳定的 upstream unavailable/unsupported，不回落到 auth.reopen。
- [并行 OpenSpec 变更也触及互动协议/UI] → 使用独立工作树、在集成前 rebase 最新默认分支，并串行合并协议热点。

## Migration Plan

1. 先同步 Cloud/Edge 协议类型、schema/fixtures 和 capability negotiation，再实现 Cloud customer API 与 Edge handler。
2. 实现 auth coordinator/sidecar 生命周期和 Electron IPC/UI，运行聚焦、acceptance、全量测试及 typecheck。
3. 分别提交并推送 Edge/Cloud 默认分支；同步 `docs/protocol.md` 和 OpenSpec evidence。
4. 从干净 Cloud `master` 快照部署 `dev`，验证服务、端口、健康、数据库以及新旧 Edge 的 fail-closed 行为。
5. Edge 不自动打包；真实客户端要获得按钮仍需后续显式桌面发版。

回滚时先回滚 Electron UI 暴露，再回滚 Cloud endpoint/command，最后回滚 Edge handler；未知命令保持 fail closed，数据库无 schema 迁移。

## Open Questions

- 无。当前交互采用“打开后保持可见，直到客户转入后台或环境生命周期结束”的明确语义。
