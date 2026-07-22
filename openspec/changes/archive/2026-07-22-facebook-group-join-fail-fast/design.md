## Context

当前加群在 `timeout`、`no_observation`、`nav_error`、`lease_unavailable`、`not_ready`、`post_not_confirmed_slow` 等执行失败上调用 `markTransientRetry`：membership 回到 `assigned`，写入 2–8 分钟抖动冷却且抵消尝试次数。`currentAssignment` 在冷却期隐藏该行，而 `claimNext` 只要看见任意 `assigned/joining` 行就拒绝新认领，造成真实目标仍充足却返回 `no_targets`。

用户已明确否定这层自动恢复：页面打不开就是本次失败，直接提示，不需要冷却或隐式重试。

## Goals / Non-Goals

**Goals:**

- 尚未加入阶段的页面、网络、渲染和任务租约失败立即进入 `failed` 终态。
- 审计和人工回执保留原始原因；`nav_error` 显示“打开群页失败”，绝不转成 `no_targets`。
- 终态失败不占用账号的 `assigned/joining` 单飞位，下一次触发可认领其它目标。
- 删除不再使用的分钟级抖动、`markTransientRetry` 接口及相关测试假设。

**Non-Goals:**

- 不改变登录、验证码/检查点的账号暂停与长退避。
- 不改变已加入群的评论覆盖冷却、成员离开确认或 RiskController 配额。
- 不改变 Edge、协议、Console、目标范围或全局一群一账号约束。

## Decisions

### 1. 执行瞬态直接写 `failed`，不删除 membership

调度器继续识别现有执行失败集合，但统一调用 `markOutcome(accountId, groupUrl, 'failed', reason)` 并写审计，reason 不再追加 `:transient_retry`。保留失败 membership 能留下真实目标事实并防止池式命令反复撞同一坏群；由于其状态不再是 `assigned/joining`，不会阻塞账号下一次认领其它群。

备选“删除失败 membership”会让排序稳定的候选在下一次命令中再次选中同一群，形成无冷却热循环，故不采用。显式 `/comment --join=<url>` 已能由人工意图重置本账号的非 joined 终态，可作为有意识的重试入口。

### 2. 账号级阻断保持现状

`login_required`、`blocked_by_captcha` 仍调用账号暂停和 `markRetryableFailure`。它们描述的是账号整体不可执行，不是某个群页面失败；保留该边界避免绕过登录/验证码安全状态。

### 3. 回执使用本次真实 outcome

手动加群评论仍由 `joinOnlyReceipt` 映射本次结果。`nav_error` 直接返回“打开群页失败；未评论”；其它执行原因带诊断值返回“加群未成功”。只有在本次确实未认领任何候选时才能返回 `no_targets`。

## Risks / Trade-offs

- [偶发网络失败会把一个本可加入的群留为 `failed`] → 这是用户选择的 fail-fast 取舍；审计保留原因，显式 URL 可人工重试。
- [旧版本已写入的短冷却行可能跨越滚动发布] → 该冷却上限 8 分钟且不会再新增；部署后验证 dev 不存在未来生效的执行瞬态冷却行。
- [把账号级阻断误归为普通执行失败] → 保持 `isAccountTransient` 分支优先，并用聚焦测试冻结暂停/长退避不变。

## Migration Plan

1. 部署 Cloud 代码，无 schema 迁移。
2. 启动后查询 `assigned/joining` 且 `cooldown_until > now()` 的行；若为旧网络瞬态，仅报告并等待既有上限自然结束，不做无授权数据删除。
3. 用测试和 dev 只读状态验证：导航失败写 `failed`、无未来冷却、下一次 claim 可选其它群、回执不出现 `no_targets`。
4. 回滚为上一 Cloud revision；数据库中的 `failed` 行是真实失败事实，无需反向伪造成可重试。

## Open Questions

无。
