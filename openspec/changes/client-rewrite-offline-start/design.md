## Context

`curated-envkey-account-binding` 已将边缘握手中的环境账号事实持久化，并让客户端精选内容读走统一的归属与绑定解析器。其 D5 同时把 `POST /curated-contents/:id/create-post` 与通用 `POST /delegated-tasks/draft` 都视为“不可逆或具备发布能力的写”，在创建任务前调用 `resolveEdgeIdForAccount` 做活会话佐证。

这两个入口的实际语义并不相同。精选内容 `create-post` 由服务端固定构造 `approvalMode: review` 的任务；任务先在云端生成洗稿成品并落为 `pending_approval`，此时没有浏览器动作。只有审批后的平台下发才需要活边缘。当前前置因此阻断了本可离线完成的生成阶段。

## Goals / Non-Goals

**Goals:**

- 已归属且持久绑定有效的环境在浏览器未启动时也能发起精选内容洗稿。
- 洗稿任务始终绑定到云端解析出的账号并保留人工审批。
- 平台发布仍只在存在可定向的活边缘时发生。
- 未绑定、跨客户争用、悬空账号和查询失败继续 fail-closed。

**Non-Goals:**

- 不放宽通用客户端委托任务创建入口的在线佐证。
- 不允许客户端提交 `accountId`、`approvalMode` 或其它字段改变洗稿任务目标与审批模式。
- 不改变最终审批、发布下发、风险配额或成功判定。
- 不新增绑定回填、数据迁移、协议字段或 Edge 代码。

## Decisions

### D1：只从精选内容洗稿入口移除创建时活体佐证

`create-post` 继续先用 `resolveBoundAccountForEnv(userId, envKey)` 完成客户归属、唯一绑定、账号存在性和跨客户争用检查；解析成功后直接以该 `accountId` 调用服务端固定形状的 `createDraft`。不再调用 `attestLiveBinding`。

该入口只创建 `review` 任务，在线状态并不参与生成阶段。相比把离线状态特判为可重试或在 Edge 自动启动浏览器，直接移除附带前置能保持阶段边界清晰，也不会制造浏览器副作用。

### D2：通用建任务入口与最终下发闸保持不变

`POST /delegated-tasks/draft` 仍接受更广的发布类意图，继续要求活会话佐证。本 change 不把用户对“洗稿”的授权扩张到所有客户端委托。

发布链仍以账号解析活边缘并定向下发；没有收件人时诚实等待或失败，绝不广播或把持久绑定当执行端地址。洗稿成功回执只表示任务已入队，后续 `pending_approval` 只表示候审稿已落库，二者都不是平台发布成功。

### D3：回归测试拆开“离线洗稿可创建”与“通用发布任务离线拒绝”

原测试把两者绑定为同一个离线拒绝结论。修改后同一 fixture SHALL 断言：精选内容 `create-post` 返回创建回执且任务落在持久绑定账号；通用 `/delegated-tasks/draft` 仍返回 `binding_unverified`。这样可防止未来误把放宽范围扩到通用入口。

## Risks / Trade-offs

- **持久绑定可能陈旧，洗稿会为该环境上一次账号生成候审稿** → 继续执行每次请求的客户归属、账号存在性与跨客户争用检查；产物只进入人审，不产生平台副作用；下一次握手会更新绑定。
- **开发者把“入队成功”误读成“离线也能发布”** → 规范、注释和测试明确区分生成、候审、审批与最终下发；发布执行端解析不变。
- **在线闸被误删到通用委托入口** → 保留 `attestLiveBinding` 及通用入口离线 409 测试。

## Migration Plan

1. 更新契约并严格验证 OpenSpec。
2. 在 cloud feature worktree 修改路由与聚焦测试，运行 acceptance、全量测试和 typecheck。
3. 快进集成到 `aidcp-cloud/master` 并推送。
4. 按开发规范部署到 `dev`，检查服务、监听与健康状态；异常时回滚到部署前备份/前一提交。

## Open Questions

无。
