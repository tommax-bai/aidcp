## Context

`admin-environment-lifecycle-management` 已把环境删除实现为 Cloud 创建 durable request、Edge 通过客户鉴权 HTTP poll/claim、Edge 调本机 AdsPower、outbox 回执、Cloud 软删除的异步状态机。该链路适合“只有客户机器能访问 AdsPower”的前提，但当前产品决定把 AdsPower API Key 放在云端，由 Cloud 直接访问 AdsPower API；继续保留 Edge 领取和回执只会增加版本、在线状态和页面进度负担。

AdsPower 官方端点仍是 Local API（`/api/v1/user/delete`），不是托管互联网 API。Cloud 直调的运行前提是 Cloud 进程能访问一个由服务端配置的 AdsPower API 地址，且该 AdsPower 实例以匹配 API Key 运行。密钥属于服务端凭据，浏览器只能看到掩码状态。

## Goals / Non-Goals

**Goals:**

- 管理员精确确认一个 envKey 后，由 Cloud 直接调用 AdsPower 删除，并在确认成功后收口 AIDCP 环境。
- 删除失败、不确定或配置缺失时保留环境与真实错误，不把 HTTP 接收或超时当成功。
- 复用现有 AES-256-GCM 凭据库保存 AdsPower API Key，在设置页展示掩码并支持热更新。
- 删除远程执行链不再依赖 Edge 在线、版本、installation、maintenance poll/claim/result 或 outbox。
- 保留逐环境确认、调度 fail-closed、账号数据不随环境删除、环境软删除审计等安全边界。

**Non-Goals:**

- 不在本变更中安装、升级或托管 AdsPower Global；运行环境必须另行提供 Cloud 可达的 Local API。
- 不开放浏览器提交 AdsPower API base，不提供任意 AdsPower 端点代理，不增加批量删除。
- 不改变桌面客户端本地二次确认删除，不构建 Edge 安装包。
- 不硬删除账号、风控、人设、内容或历史数据；“在 AIDCP 删除”指环境退出有效注册/调度投影并保留审计软删除行。

## Decisions

### 1. Panel 删除端点同步编排 AdsPower 与 Cloud 收口

`POST /api/environments/:envKey/deletion` 继续校验内部 JWT、完整 envKey 确认和幂等键。Cloud 先在短事务中锁定环境、建立/复用删除审计并置 `deleting`，提交后在事务外调用 AdsPower；成功再以第二个短事务写 `deleted`、`result_kind=deleted` 并移出有效环境投影。AdsPower 失败则写 `delete_failed` 与脱敏错误，AIDCP 环境记录不进入 deleted。

不用长数据库事务包住外部 HTTP，避免网络等待占用行锁/连接。端点成功返回 200 与 `state=deleted`；缺密钥/不可达/鉴权或业务失败返回可辨认非 2xx 与写后失败状态，不再用 202 表示排队。

备选“AdsPower 成功后才首次写数据库”被拒：并发重复提交可能发出多次删除，也无法在调用中冻结新调度。备选保留 Edge 兜底被拒：会重新引入双执行者和真实来源不清。

### 2. 幂等重试只接受同一服务端 AdsPower API 的确定证据

单 envKey 同时只允许一个 `deleting` 请求；相同幂等键复用审计。若 `user/delete` 成功但 Cloud 终态写入失败，重试可能收到“不存在”。Cloud 不按错误字符串直接判成功，而是调用 AdsPower profile 查询：只有查询完整成功并明确找不到 envKey，才记录 `already_missing` 并收口；查询失败、截断或响应不符合契约仍是失败/未知。

这保留跨 HTTP/数据库非原子边界的可恢复性，同时避免把错误机器或不可达服务的“查不到”伪装成删除。

### 3. Cloud AdsPower 客户端是窄接口、带超时、节流和脱敏

新增 Cloud 内部客户端只暴露 `deleteProfile(envKey)` 与 `profileExists(envKey)`，写面只允许 `POST /api/v1/user/delete`，body 固定 `{ user_ids: [envKey] }`。默认 base 为 `http://local.adspower.net:50325`，仅服务端 `ADS_API_BASE` 可覆盖；请求带 `Authorization: Bearer <key>`，key、Authorization 和请求体不写日志。所有响应必须是 JSON 且 `code===0` 才算业务成功；请求有界超时并遵守 AdsPower 每秒限制。

不把通用 AdsPower 代理端点暴露给 Panel，也不复用 Edge CJS 模块，避免 Cloud 获得 `user/create/update` 或浏览器生命周期写能力。

### 4. AdsPower API Key 复用平台凭据表并按请求热读取

在凭据注册表增加 `provider=adspower, field=api_key`，env 回退为 `ADS_API_KEY`/`ADSPOWER_API_KEY`，归入“浏览器服务 API Key”分组。数据库仍经 `AIDCP_CRED_KEY` 加密；GET 只返回 `configured/source/maskedHint/restartRequired=false`，PUT 仍要求整段重输。

删除调用每次通过 `CredentialStore.getSecretForRuntime()` 读取当前数据库值并回退 env，因此保存后下一次删除立即生效。设置页按每项 `restartRequired` 生成提示，不再把所有凭据一律描述为“重启 Cloud 后生效”。

### 5. 删除 UI 只表达直接结果

环境页提交期间显示“正在从 AdsPower 删除”。成功提示“AdsPower 已删除，AIDCP 环境已移除”并刷新列表；失败保留弹窗/环境，显示 Cloud 返回的可读原因。列表兼容旧库里已有的 `waiting_edge` 记录，但不再产生新 waiting 状态；可以把旧状态显示为“旧删除请求，需重试”，不继续承诺客户端推进。

设置页沿用统一凭据卡片，只增加 AdsPower 项和按项生效提示，明文输入保存成功后立即清空。

### 6. 移除远程删除的 Edge maintenance 执行链

Cloud 停止挂载 `/environment-maintenance/poll|claim|result`；Edge 停止启动 maintenance poller，不再因 Cloud 删除申请调用 AdsPower 或写 outbox。旧客户端更新 Cloud 后得到 404/不支持并停止该轮，不影响浏览、发布和普通客户 HTTP 数据面。已有 maintenance 数据表与列先保留，避免破坏性迁移；它们仅作为历史审计/兼容字段，不再承担执行职责。

## Risks / Trade-offs

- [Cloud 所在机器没有可达 AdsPower Local API] → 删除明确失败并保留 AIDCP 环境；部署验收必须探测配置的 base，不能仅凭 API Key 已保存宣称可用。
- [AdsPower 删除成功后 Cloud 终态写失败] → 重试通过同一 AdsPower API 的完整 profile 查询证明不存在后收敛为 `already_missing`。
- [请求超时而 AdsPower 实际已执行] → 先查询目标是否仍存在；无法获得确定查询结果时保持失败/未知且继续阻断该环境，绝不恢复为成功或 active。
- [Cloud 持有高权限 AdsPower Key] → AES-GCM 加密落库、JWT 守护写入口、明文不回传不日志、客户端只允许 delete/list 两个窄操作。
- [旧 waiting_edge 数据不会自动推进] → Console 标成旧请求需人工重试；新 POST 接管并转为 deleting，不依赖旧 Edge 回执。
- [Cloud 直调形成单点] → 这是换取简单链路的明确代价；失败可重试且 AIDCP 不先删，不引入 Edge fallback 双写者。

## Migration Plan

1. 先部署 Cloud：注册 AdsPower 凭据、增加窄客户端和直接删除编排；保留旧表结构但停止产生 waiting_edge。
2. 部署 Console：设置页展示 AdsPower Key，环境页使用直接成功/失败文案；对旧 waiting_edge 显示需重试。
3. 合入 Edge 源码移除 maintenance poller；不构建安装包，已安装旧客户端对新 Cloud 的 maintenance 404 只影响已废弃链路。
4. 在 dev 配置/核对 `AIDCP_CRED_KEY`、AdsPower API base 与加密保存的 Key；用只读 profile 查询验证可达性。真实删除只对明确授权的一次性环境执行，本变更自动测试全部使用假 AdsPower。
5. 回滚时恢复上一版 Cloud/Console；已成功 deleted 的环境保持审计终态，不自动恢复。若只回滚 Console，旧页面可能显示兼容状态但不会改变 Cloud 真实结果。

## Open Questions

- dev/ol 各自由哪台 AdsPower Global 实例向 Cloud 提供可达 Local API，以及网络白名单/隧道地址，需要在部署验收时按目标确认；代码不猜测或自动暴露本地端口。
