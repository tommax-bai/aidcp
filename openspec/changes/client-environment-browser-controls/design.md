## Context

左侧环境栏的窗口显示动作经 renderer → preload → Electron main → core stdin 路由。主进程当前在指令写入成功后拼接一段无法证明系统前台结果的长提示，三个 renderer 入口再直接展示。单环境“浏览器”按钮的关闭态路径则在 IPC handler 内等待 browser-absent core 完成 Cloud 握手，导致一次可能较慢的控制链占住按钮调用且缺少点击后的即时受理状态。

环境栏已有 `fleet:startAll` 和未展示的 `fleet:stopAll`；后者是暂停意图，只处理 `automationIntent=enabled`，不等价于单环境“关闭”所调用的 `stopAutomation()`。

## Goals / Non-Goals

**Goals:**

- 成功的窗口前置 / 归位不再展示解释性文案，失败仍有明确反馈。
- 批量关闭与单环境关闭复用同一真语义，并受 renderer 当前平台筛选和 main 实时句柄求交集双重约束。
- 关闭态“打开浏览器”在网络或核心握手前先投影处理中状态，IPC 立即返回；后台链最终仍以真实状态更新成功或失败。
- 保持 envId 路由、浏览器槽位、身份绑定和外部占用保护不变。

**Non-Goals:**

- 不把“全部关闭”改成删除环境、退出客户端或停止 AdsPower daemon。
- 不修改“全部暂停”内部语义，不绕过槽位 / 内存 / 身份闸。
- 不声称窗口已被操作系统真正置顶，不构建或发布安装包。

## Decisions

### 1. 增加独立 `fleet:closeAll`，不复用 `fleet:stopAll`

renderer 把当前筛选后的 envId 列表传给主进程；主进程再次通过实时句柄表求交集并逐个调用 `stopAutomation()`。这样批量操作与单环境关闭共享停止意图、重启定时器清理、浏览器关闭确认和外部占用保护。复用 `stopAllEnvs()` 的替代方案会把关闭退化成暂停，用户随后看到“恢复”而非“启动 / 浏览器”，语义错误。

### 2. 浏览器打开改为“立即受理、后台收敛”

主进程在开始任何可能等待客户接口 / Cloud 握手的 await 前写入 `starting` 与“正在打开浏览器”状态，同时保持自动化意图为 `stopped`，然后异步执行 browser-absent core bootstrap；bootstrap 成功后再调用既有 `wakeColdStandby()`。IPC 立即返回当前状态，renderer 同时在 await 前禁用按钮并显示处理中标签。失败由既有状态 / 错误投影回滚，不伪造浏览器就绪。

将整条启动链继续 `await` 的替代方案虽然调用结构简单，但会复现点击无响应；直接跳过 core / binding 启动真实浏览器则破坏身份和槽位边界。

### 3. 成功静默，失败可见

`sendBrowserParkingCommand()` 成功仅返回 `{ ok: true }`。环境栏、引导流和设置页收到成功时清空各自临时消息；失败时保留目标环境和真实错误。这样删掉用户指定的冗余文案，同时不把“指令已写入”包装成“窗口已置顶”。

## Risks / Trade-offs

- [批量关闭目标在点击后变化] → renderer 仅声明请求范围，main 以处理时实时句柄求交集，移除或伪造 envId 不会扩大范围。
- [异步打开后用户立即关闭] → 后台 continuation 在唤醒前重新检查 `handle`、`stopRequested`、`automationIntent` 和 child 归属；既有取消闸优先。
- [成功静默让用户误以为未执行] → 行的 shown 相位与真实状态仍更新；只有说明段落被移除，失败始终展示。
- [批量关闭不是瞬时完成] → 回执仅报告已受理目标数，逐环境状态继续显示关闭中 / 已关闭 / 未确认，不宣称全部已完成。
