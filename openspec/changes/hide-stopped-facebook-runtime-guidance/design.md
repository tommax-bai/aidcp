## Context

运行价值视图目前只接收环境状态，并在判断新鲜运行态之前优先处理 `dailyUsage.firstPost` 和今日完成窗口。环境停止后这些字段仍可能作为最后一次真实快照保留，因此 Facebook 环境会继续显示获得感卡片。选中环境的平台由 renderer 的 fleet 上下文权威提供，不应从发布数据或缓存内容反推；“未启动”则已有四轴生命周期中的 `automationState=stopped` 定义及旧字段兼容投影。

## Goals / Non-Goals

**Goals:**

- 选中 Facebook 环境明确未启动时，运行价值卡在任何缓存成果分支之前被隐藏。
- 用结构化自动化状态区分未启动与启动中、排队、待任务、待机、暂停和异常。
- 平台切换后立即按新环境重算，且保持小红书和普通 HTTP 数据卡片不变。

**Non-Goals:**

- 不清空或改写 `dailyUsage`、首帖引导、浏览窗口或今日成果数据。
- 不改变自动化/浏览器生命周期、环境栏状态映射、今日进展或内容发布卡。
- 不新增 Cloud/Edge 协议字段，不构建桌面安装包。

## Decisions

### 1. 将选中环境平台作为纯视图上下文传入运行价值判定

renderer 在调用 `runtimeGuidanceView` 时传入 `selectedEnvPlatform()`。视图函数不从 `publish`、账号名称或缓存指标猜平台；未知平台继续沿用现有行为。

备选方案是在 status 内复制 platform。该方案会制造第二个平台来源，并在 fleet 切换时增加陈旧状态风险，因此不采用。

### 2. 在所有缓存成果分支之前执行 Facebook 未启动闸门

`runtimeGuidanceView` 先通过既有生命周期兼容投影取得 `automationState`。只有 `platform=facebook && automationState=stopped` 才直接返回空视图，并清理由 renderer 负责的既有 DOM 内容。闸门必须早于 `firstPostGuidance`、今日完成和间隔成果分支，否则最后一次快照仍会把卡片重新显示。

备选方案只隐藏首帖进度，仍会泄漏今日完成或间隔卡；只在 CSS 上隐藏则会保留错误的可访问树和陈旧 DOM，因此均不采用。

### 3. 不扩大“未启动”的边界

`starting`、`waiting_resource`、`ready`、`running`、`paused`、`pausing`、`stopping` 和 `error` 不命中本次平台闸门；它们仍由现有证据规则决定是否展示。旧状态没有 `automationState` 时复用当前 `edge/session/coreState` 兼容映射，避免同一界面的“未启动”判据出现两套实现。

## Risks / Trade-offs

- [平台切换残留上一环境卡片] → fleet 切换已触发完整 `render`；补充 Facebook 与小红书双向切换 DOM 回归。
- [把冷待机或暂停错当未启动] → 只匹配标准化后的精确 `stopped`，测试锁定 `ready + browser closed` 与 `paused` 不被平台闸门吞掉。
- [缓存成果被隐藏后用户误以为数据丢失] → 仅隐藏运行价值卡，不删除数据；今日进展与发布摘要继续使用原有 HTTP 真源展示。

## Migration Plan

1. 在 Edge 隔离 worktree 中增加平台感知的纯视图闸门和 focused tests。
2. 运行 renderer 语法检查、focused Electron/UI 测试、完整测试与 typecheck。
3. 严格校验 OpenSpec，重放到最新默认分支后快进集成并推送。
4. 回滚时回退 Edge 与控制仓各自单一提交；没有数据、协议或服务端迁移。

## Open Questions

无。
