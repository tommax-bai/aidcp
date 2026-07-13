## Context

`edge.task.acquire` 目前由 cloud 在固定时限内等待 `acquired`。edge 为了让正在执行的普通浏览原子动作收敛，会延后授予租约；若 cloud 已超时，迟到的 `acquired` 会被忽略，edge 却继续持有租约直到自然过期。排期评论的顶层异常处理没有区分这一阶段，因而把尚未开始的任务描述成已选中笔记、发布未确认。

该修复跨 cloud、edge 与协议文档；保持“已取得租约后的命令、提交与风控”不变，并兼容旧 edge 对新增可选字段的忽略行为。

## Goals / Non-Goals

**Goals:**

- 让等待 acquire 在 edge 本地和 cloud 两端均有上限，并能取消陈旧排队申请。
- 让 cloud acquire 超时后主动释放，且迟到 acquired 仍会被收敛。
- 让排期评论在未开始页面操作时以人可理解、可审计的方式说明真实状态。
- 用单元测试覆盖时序竞争和结果卡文案。

**Non-Goals:**

- 不抢杀已经获得租约并开始执行业务命令的任务。
- 不改变普通浏览的原子动作安全边界、评论候选选择、评论提交或风控记账。
- 不把 edge acquire 超时解释成浏览器关闭、账号离线或评论发布失败。

## Decisions

### 1. Cloud 下发本地 acquire 等待时长，edge 自己计时

`edge.task.acquire` 增加可选 `acquireTimeoutMs`。cloud 将自己实际使用的 acquire timeout 一同发送；edge 从收到申请开始以本机计时器限制排队等待，并在超时时移除尚未获授的申请、返回已释放状态。用持续时间而非绝对时间，避免云边机器时钟偏差。

备选方案是只在 cloud 超时后丢弃 Promise，或使用固定 edge 常量。前者仍会遗留无主租约，后者会随 cloud 配置漂移，因此不采用。

### 2. 超时即发送 release，并保留短暂取消墓碑处理迟到 acquired

Cloud 的 acquire timeout 会从等待表移除申请、记录该 `taskId/edgeId` 已取消，并向 edge 发送 `edge.task.release`。`release` 已能处理 edge 的排队项与当前项，故不引入新的消息类型。若随后到达同一 task/edge 的 `acquired`，cloud 再次发送 release，直到收到 released 或墓碑过期。

备选方案是增加独立 cancel 消息。复用幂等 release 能减少协议面，并覆盖“已经授予但 acquired 回执到达太晚”的竞态。

### 3. 只把明确的租约接管错误映射为“未开始”

排期评论调度器识别 `EdgeTaskLeaseError` 的 acquire/连接失败；该分支产出 `not_started` 结果，回执明确“未搜索、未选中笔记、未发布”。其他在已进入评论流程后的错误仍保留既有失败语义，避免把真实选择或提交失败误标为未开始。

### 4. 旧 edge 的兼容和部署顺序

字段为可选，因此先部署 cloud 时旧 edge 仍能接收协议；但旧 edge 无本地上限，cloud 的主动 release 仍会清理它。部署新 edge 后，超时将同时由 edge 和 cloud 保护。服务端先部署到 dev，桌面 edge 随后经常规客户端发布路径获得更新；本次不构建安装包。

## Risks / Trade-offs

- [release 与 acquired 乱序或丢失] → 复用同一连接的有序发送；cloud 墓碑在迟到 acquired 时重发 release，edge 的重复 release 幂等。
- [edge 本地计时器误释放刚好可授予的任务] → 仅影响尚未 acquired 的队列项；cloud 同一时限内也不会下发业务命令。
- [把中途失败误说成未开始] → 仅 `EdgeTaskLeaseError` 使用 `not_started`，其它异常沿用已有 post-failed 语义。
- [旧版本 edge 不理解字段] → 字段可选，cloud 的主动 release 是独立的兼容保护。

## Migration Plan

1. 同步 cloud/edge 协议定义、协议文档和单元测试。
2. 部署 cloud 到 dev，确认 acquire timeout 立即发出 release 且排期结果卡不再声称已选中。
3. 发布 edge 代码后验证排队 acquire 在本地时限内终止。
4. 若出现回归，回滚 cloud/edge 到前一提交；旧的 4 分钟 lease expiry 仍是最后安全网。

## Open Questions

- 无。现有 `edge.task.release` 已具有处理 queued/active task 的幂等语义。
