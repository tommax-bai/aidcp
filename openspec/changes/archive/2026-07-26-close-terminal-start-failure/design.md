## Context

`lifecycleAxes()` 只会在本机自动化意图仍为 `enabled`、子进程已退出且存在终态失败时投影 `automationState=error`。当前 renderer 却把 `error` 当成“自动化不活跃”，于是主动作显示“启动”，次动作退化为“浏览器”，`edge:close` 无法从界面触发。

AdsPower profile 占用是一个更窄的失败形状：provider 在 `browser-profile/start` 阶段即拒绝请求，本机从未取得浏览器句柄。监督器已经把它分类为不可重起终局、禁止向占用端发送 stop 或强杀，但通用异常退出路径仍把浏览器状态标为未确认。若事后复用普通“无子进程关闭”确认，可能把外部占用误说成需要本机接管后关闭，违背既有不抢占边界。

## Goals / Non-Goals

**Goals:**

- 让终态自动化错误仍可显式关闭本机自动化意图，同时保留人工重试启动。
- 对启动前即被外部占用拒绝的环境，关闭时安全收敛为本机已停止，不触碰外部会话。
- 对其他可能遗留本机浏览器的异常继续执行既有关闭确认，不扩大“已关闭”的断言。
- 用聚焦测试锁定按钮路由、关闭 IPC 和占用终态的主进程分支。

**Non-Goals:**

- 不新增跨设备强制抢占、远端 stop 或 AdsPower Multi Device 行为。
- 不改变普通崩溃的自动重启预算、占用识别规则或失败详情内容。
- 不改变 Cloud、协议、数据库或客户数据面。
- 不构建或发布 Edge 安装包。

## Decisions

### 1. `automationState=error` 保持可关闭

renderer 将“是否显示关闭自动化”从“不是 `stopped` 且不是 `error`”改为“不是 `stopped`”。在当前状态推导顺序中，`error` 只可能出现在 `automationIntent=enabled`，因此该映射不会给已经停止的环境误加关闭动作。

错误态的主动作继续是“启动”，表达人工重试；次动作改为“关闭”，表达放弃本机启动意图并清除本轮错误。两者必须分别走 `edge:start` 与 `edge:close`，不得让“关闭”落到 `browser:open`。

未选择把错误态自动改成 `stopped`，因为那会在用户尚未处置时隐藏真实启动失败；也未选择只增加“忽略错误”按钮，因为关闭本机自动化意图才是已有、可审计的生命周期动作。

### 2. 外部占用终态按“从未取得本机浏览器”收敛

`stopAutomation()` 在无子进程分支识别 `envInUseThisRun=true`。该标志只由已验证的 `browser-profile/start` 占用拒绝设置，且每次新启动前复位；因此它足以证明本轮未取得本机浏览器句柄。

命中时监督器 SHALL：

- 将本机 `automationIntent` 置为 `stopped`，清理排队、重试和失败详情；
- 将本地浏览器执行状态收敛为关闭/无句柄；
- 显示“本机自动化已关闭，未触碰占用端浏览器”的诚实文案；
- 跳过 `confirmOwnedProfileClosedFromShell()`，不得根据外部 active 结果引导“恢复接管后再关”。

主进程 SHALL 仅在该窄分支写入结构化 `closeScope=local_automation_only`，renderer 只有命中该标志时才采用随本次关闭原子写入的 `presence.text`；普通关闭仍使用既有“已关闭浏览器”。否则无条件信任任意历史 `presence.text` 会把旧动作文本重新展示，而无条件回落“已关闭浏览器”又会覆盖“占用端未受影响”的真实范围。

未选择调用 AdsPower `browser/stop`，因为本轮从未拥有该 profile；也未选择保留红色错误直到外部释放，因为用户已经明确关闭的是本机自动化，而不是请求监控外部占用。

### 3. 其他异常继续走既有浏览器关闭确认

只有 `envInUseThisRun` 的窄分支跳过确认。普通崩溃、核心死亡或关闭状态不确定仍调用 `confirmOwnedProfileClosedFromShell()`；确认在跑、确认已关和无法确认三种结果保持既有诚实语义。

这避免了为解决一个“从未拿到句柄”的终态而削弱其他“可能留下本机浏览器”的安全边界。

## Risks / Trade-offs

- [占用分类误命中会跳过本机浏览器确认] → 继续复用现有窄分类器，仅在 `browser-profile/start` 的已验证占用句式命中；本变更不扩大分类面。
- [错误态关闭入口误用于已停止环境] → 依赖并测试 `automationState` 推导顺序；`stopped` 仍只显示浏览器辅助动作。
- [关闭后用户误以为远端浏览器也被关闭] → 成功文案明确“本机自动化已关闭、占用端未受影响”，renderer 只在结构化本机关闭范围下采用该文案，且监督器不发送 stop。
- [通用异常被一并静默清除] → 特判仅覆盖外部占用；其余错误继续通过本机 active 确认或保留无法确认失败。

## Migration Plan

1. 在 Edge worktree 完成 renderer、main 与聚焦测试。
2. 运行 Edge 聚焦测试、完整测试和 typecheck；不制作安装包。
3. 更新 OpenSpec 任务证据并严格校验，随后分别 fast-forward 集成 Edge `master` 与 control `main` 并推送。
4. 回滚只需回退 Edge 与 control 对应提交；无数据、协议或 Cloud 回滚。

## Open Questions

无。
