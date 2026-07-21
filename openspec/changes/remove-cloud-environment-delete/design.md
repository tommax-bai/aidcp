## Context

`cloud-direct-adspower-environment-delete` 已把管理后台删除改为 Cloud 直调 AdsPower Local API，并在 Cloud/Console/Edge 默认分支及 dev 落地。但 AdsPower 没有可由 Cloud 直接访问的托管删除 API；官方 CLI 也只是独立启动本机 runtime，再暴露 localhost Local API。产品现决定不在 Cloud/ECS 托管该 runtime，并取消管理后台删除环境能力。

当前代码中 Cloud 拥有 AdsPower 删除客户端、环境删除编排与 Panel 写路由，凭据注册表包含 AdsPower API Key；Console 环境页拥有删除确认/进度交互，设置页会展示该凭据。Edge 的旧 maintenance 远程执行链已经停止。历史数据库仍可能包含删除申请、失败或 deleted 审计行。

## Goals / Non-Goals

**Goals:**

- 让管理后台环境管理成为只读资产视图，不再出现或接受删除操作。
- 删除 Cloud 的 AdsPower 出口与 AdsPower Key 可配置面，保证旧页面或直接 HTTP 调用也不能触发删除。
- 保留历史 lifecycle/删除审计和既有 deleted 真态，不做数据复活或破坏性清理。
- 保留桌面客户端本地、逐环境二次确认删除能力。

**Non-Goals:**

- 不恢复 Edge maintenance poll/claim/result、outbox 或 Cloud→Edge 删除命令。
- 不安装或托管 AdsPower CLI/runtime，不寻找非公开 AdsPower 云端端点。
- 不硬删除历史凭据行、删除申请或环境审计数据。
- 不改变环境清单、账号环境摘要、桌面本地创建/改代理/改名/删除行为。

## Decisions

### 1. 删除 Panel 写路由，而不是保留一个永远失败的 Cloud 删除实现

Cloud 不再注册 `POST /api/environments/:envKey/deletion`，并删除其 AdsPower 编排依赖。旧 Console 或直接调用会收到非成功路由结果，且不得创建删除审计、改变 lifecycle 或请求 AdsPower。

保留路由并返回“功能关闭”被拒：这仍会让调用方认为删除是可配置能力，并留下未来误启用的写面。恢复 202/Edge 等待链也被拒：用户取消的是云端管理删除，不是要求换回异步执行者。

### 2. Console 完全移除删除交互，历史状态仍只读展示

环境页删除按钮、影响查询、确认弹窗、提交/重试和删除成功文案全部移除。环境列表、筛选、账号深链和历史 lifecycle 展示继续保留；旧 `deleting`、`delete_failed`、`deleted` 行只按服务端真态展示，不提供重新执行入口。

只禁用按钮被拒：禁用控件仍暗示能力存在，也容易被旧状态条件重新开启。

### 3. AdsPower 凭据从允许列表和设置目录移除，密文历史行保持惰性

Cloud 凭据注册表不再注册 `provider=adspower, field=api_key`，配置 GET 不返回该项，PUT 对该 provider/field 按未知凭据拒绝。Console 不再渲染浏览器服务凭据分组或 AdsPower 生效文案。

不主动删除数据库中可能已存在的加密密文行：删除秘密属于额外破坏性动作，且不影响能力关闭；无注册项、无运行时读取者时它是惰性历史数据。若未来需要清理，应另做带备份和行数断言的运维任务。

### 4. 历史 schema 与 Edge 退休状态保持不变

删除请求表、lifecycle 列和软删除行继续保留，以确保历史审计、旧 deleted 真态及部署回滚安全。Edge maintenance poller 不恢复，Cloud customer-auth maintenance 路由也不恢复。本次无需 Edge 代码或安装包。

### 5. 先部署 Cloud 再部署 Console

Cloud 先关闭写路由与运行时出口，确保旧缓存页面即使提交也不会删除；Console 随后移除入口。验证使用不存在的哨兵 envKey 和路由检查，只证明无写面，不触发真实 AdsPower 或数据库删除。

## Risks / Trade-offs

- [旧 Console 静态资源仍短暂显示删除按钮] → 先部署 Cloud，使提交必然非成功且零副作用，再部署并校验新静态资源。
- [历史 `deleting` / `delete_failed` 状态无法在后台重试] → 只读保留并明确不提供动作；不擅自改写为 active/deleted。
- [数据库残留加密 AdsPower Key] → 无注册项和读取者，运行时不可用；如需物理清理另行备份后处理。
- [未来误把桌面本地删除一起移除] → 聚焦 Edge 回归测试确认本地二次确认 `user/delete` 仍在，且本次不改 Edge 源码。

## Migration Plan

1. Cloud 删除 AdsPower 客户端、凭据注册、Panel 删除路由与相关测试，保留数据库 schema。
2. Console 删除环境删除交互、API 类型和 AdsPower 设置项，更新聚焦测试。
3. 运行 Cloud/Console 聚焦测试、全量门禁、typecheck/build 与 OpenSpec strict validation。
4. 串行集成 Cloud、Console、control repo；先部署 Cloud 后部署 Console。
5. dev 验证环境读取正常、删除路由非成功且无新增删除行、页面无删除按钮、设置页无 AdsPower Key。
6. 回滚时可恢复上一版 Cloud/Console；历史 deleted 环境和审计始终不自动复活。

## Open Questions

- None.
