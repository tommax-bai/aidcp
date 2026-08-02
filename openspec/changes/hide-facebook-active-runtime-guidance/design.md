## Context

Edge 的 `runtimeGuidanceView(status, nowMs, platform)` 目前先处理 Facebook `stopped`，随后依次返回首作、今日完成、普通运行、本轮/小时间隔等视图。renderer 根据该函数返回值显示或清空同一个 `#runtime-guidance` 容器。人设完成弹窗由独立的 `showPersonaGrowth()` 和 `#persona-growth` 管理，不属于这个容器。

本次只收回 Facebook 三类主动状态卡：首作寻找、首作生成、普通运行。顶部在场感、间隔/完成卡、人设完成弹窗和 XHS 必须继续走现有路径。

## Goals / Non-Goals

**Goals:**

- Facebook 首作 `searching`、首作 `generating` 和普通新鲜 `running` 不返回运行价值视图。
- Facebook 本轮间隔、小时间隔、今日完成和 `stopped` 既有规则保持明确且可回归。
- 平台切换时清除 Facebook 隐藏态残留，并让 XHS 立即恢复原卡。
- 人设完成弹窗及其全部文案、CTA、吉祥物、撒花和流光零改动。

**Non-Goals:**

- 不删除 `#runtime-guidance` DOM、样式、图标或吉祥物资源。
- 不修改 Cloud 首作状态、浏览配额、自动生成、待审或发布确认链路。
- 不改变顶部在场感、今日进展、发布卡或 XHS 页面。
- 不扩大隐藏范围到 Facebook 的本轮间隔、小时间隔或今日完成卡。

## Decisions

### 1. 在视图模型按平台与模式返回 `null`

保留现有 Facebook `stopped` 早返回；在 `firstPostGuidance()` 命中后仅对 Facebook 返回 `null`，在普通新鲜运行分支中也仅对 Facebook返回 `null`。这样 renderer 继续复用既有“无视图即清空并隐藏容器”的路径，平台切换不会留下旧 DOM。

不采用 CSS 平台类隐藏，因为 CSS 只能遮住元素，不能保证 progress/harvest 等动态子节点被清空，也会让测试和可访问树继续持有不应展示的卡片。

### 2. 不使用“Facebook 一律隐藏”的总闸门

闸门只放在 `first-post` 与 `running` 两个返回点。后续的 `day`、`session` 和 `hour` 判定继续执行，从机制上保证间隔与完成卡不受影响。

不采用函数入口处的 Facebook 总早返回，因为那会误删用户明确要求保留的间隔/完成状态。

### 3. 人设完成引导保持独立

不修改 `index.html`、`styles.css` 中的 `#persona-growth`，也不修改 `showPersonaGrowth()`、`projectFirstPostStart()` 或“开始找灵感”事件接线。首作状态仍可创建和投影，只是不再在 Facebook 主界面渲染首作运行价值卡。

### 4. 以纯逻辑和 DOM 两层回归锁定边界

纯逻辑测试覆盖 Facebook 首作两态、普通运行、间隔/完成保留以及 XHS 对照。Electron DOM 测试覆盖同一状态下的平台切换，确认容器被真实隐藏且今日进展、发布卡继续展示。

## Risks / Trade-offs

- [风险] 首作状态先于普通运行分支返回，若只改普通运行分支会漏掉 Facebook 首作卡。→ 在首作返回点单独加平台闸门，并覆盖 `searching`、`generating` 两态。
- [风险] 平台切换后旧卡子节点残留。→ 继续走 `renderRuntimeGuidance(null)` 的统一清空路径，并增加 FB/XHS 往返 DOM 测试。
- [风险] 误把 Facebook 间隔或今日完成也隐藏。→ 不设置全局 Facebook 早返回；为 `session`、`hour`、`day` 增加保留断言。
- [取舍] Facebook 主界面不再以大卡解释主动运行价值。→ 顶部真实状态和今日进展仍在，且这是本次明确的产品取舍。

## Migration Plan

这是纯 Edge renderer 展示变化，无数据迁移或服务部署。合并后由后续正常桌面客户端发布流程带出；本次不构建、不安装安装包。回滚只需还原 Edge 视图闸门与对应规格/测试。

## Open Questions

无。
