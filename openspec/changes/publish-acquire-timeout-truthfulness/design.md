## Context

发布下发必须先获得 edge task lease。`edge.task.acquired` 不只表示 WebSocket 在线，也表示 edge 已暂停普通浏览并让当前浏览原子动作收敛。现有 `PublishDispatcher` 将“没有在线 edge”和“已投递 acquire、但 45 秒内未收到 acquired”都映射为 `offline_requeued`，飞书因此把客户端仍在线的 CDP/浏览阻塞误报成“边缘离线”。

本次故障中，`note.open` 的拟人化点击由许多串行 CDP 输入事件组成；每个事件有自己的 CDP 超时，但整段点击及后续弹窗等待没有统一墙钟预算。它处于 `BrowseSession.activeOperationCount` 内，因此 task coordinator 会正确等待它结束，却可能等待超过 cloud 的 acquire 时限。

浏览原子动作不能通过 `Promise.race` 提前视为结束：若底层 CDP 输入仍在运行，提前把 `activeOperationCount` 归零会让发布和旧浏览并发改写同一页面，违反任务级单写约束。

## Goals / Non-Goals

**Goals:**

- 让发布通知准确区分真实无在线 edge 与“在线但浏览器接管未及时完成”。
- 保持 acquire 未确认时零业务发布命令、草稿留待审且本次授权作废的现有安全语义。
- 为 `note.open` 提供 30 秒整体墙钟预算、分阶段耗时日志和真实的 `open_timeout` 失败出口。
- 仅在 CDP 输入命令返回、报错或其已有超时后，在逐输入事件的安全检查点停止点击；然后由既有 `trackOperation` 释放接管等待者。

**Non-Goals:**

- 不在发布申请到达时强杀正在执行的 CDP 命令，也不改变任务优先级或 lease 的互斥模型。
- 不把 `note.open` 的超时当作发布失败，不自动重新批准或自动重发草稿。
- 不在本变更中改变 CDP 客户端单命令超时、重连策略或桌面安装包发布流程。

## Decisions

### 1. 用显式通知种类表达 acquire timeout

`PublishDispatcher` 增加 `acquire_timeout_requeued` 通知种类。只有 `EdgeTaskLeaseError.code === 'acquire_timeout'` 且发布序列尚未开始时使用它；没有解析到在线 edge 的路径仍使用 `offline_requeued`。两者都作废授权并保留待审草稿，差异只在真实原因和运营指引。

备选方案是给现有 `offline_requeued` 增加 message 字段。未采用，因为通知的业务语义由调用点决定，新增可枚举 kind 能让 dispatcher 测试和 server 文案穷尽分支，避免再把不同失败归为同类。

### 2. `note.open` 以安全检查点方式消耗整体预算

`BrowseSession` 对一次 `note.open` 建立 30 秒 deadline，并记录选卡、点击、弹窗等待、详情就绪、抽取/上报和长文阅读等阶段的耗时。弹窗及 DOM 等待只使用剩余预算；拟人化点击把 deadline 传入 CDP 输入循环，在每次发送下一条输入前检查。

如果 deadline 在详情上报前耗尽，edge 上报 `action.completed(open_note, ok:false, reason:'open_timeout')`；如果详情已经如实上报，则停止剩余的长文阅读而不撤销已交付的详情。无论哪种情况，函数只会在当前已发出的 CDP 调用返回或自身既有 10 秒命令超时后返回，确保 coordinator 得到的“已静止”状态真实。

备选方案是对整个函数 `Promise.race` 一个 30 秒 timer。未采用，因为它会遗留仍在执行的 CDP click promise，并让 coordinator 过早授予发布租约。

### 3. 观测以最终汇总日志为主

每次 `note.open` 在成功、正常失败或预算耗尽时输出总耗时和分阶段耗时；超时日志额外包含停止阶段与预算。这样能在分钟级 edge 日志中直接分辨 CDP 点击迟滞、modal 渲染慢或正文阅读占用，而不为每个鼠标事件制造高噪声日志。

## Risks / Trade-offs

- [单个已发送 CDP 命令最多仍可等待其 10 秒超时] → 30 秒整体预算为 45 秒 cloud acquire 留出余量，且检查在每个后续输入前进行。
- [极慢的正常页面可能收到 `open_timeout`] → 仅在未获得详情时报告失败；详情已上报后保留结果并跳过非必要阅读。阶段日志可据实调整预算。
- [通知新增分支遗漏 server 文案] → dispatcher 和 server 使用穷尽式 kind 分支，并增加针对 acquire timeout 的单测。

## Migration Plan

1. 先部署 cloud：新通知文案立即生效，已安装 edge 仍按现有行为运行，但不会再把 future acquire timeout 文案误报为离线。
2. 发布 edge 源码并通过桌面客户端的既有更新/发布流程分发后，`note.open` 才具备新的有界退出能力；本次不自动构建安装包。
3. 若 edge 行为异常，可回退 edge commit；cloud 回退仅影响通知准确性，不影响授权或发布安全闸。

## Open Questions

- 暂无。30 秒默认预算先以本次日志和 45 秒 cloud acquire 门限确定；后续根据阶段日志再决定是否需要环境级配置。
