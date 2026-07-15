# Facebook feed 刷屏根因修复：良性 dialog 不整页重载 + 懒加载感知到底判据

## Why

真机灰度（dev、FB 号 Tianxing Bai `ads-k1ei3dbi`，2026-07-15）暴露一条长期卡点：**FB feed「页面一直刷新、永远下不去」**。CDP 只读取证定谳（`timeOrigin` 每 ~8s 重置 + `window` 标记被清 + 顶层 `frameNavigated` 无 `frameRequestedNavigation` script 标记 = 命令式整页导航）：

- **真根因不是 feed_exhausted、不是扫卡缺陷、不是 FB 自己重载**，而是边缘 `ensureFeed` 的 onTarget 判据里 `&& !dialogOpen` 这条守卫。FB 首页常驻**瞬时良性 `[role="dialog"]`**（聊天弹窗 / 加载态 / 通知提示，来了又走——单点探常为 0，但 scroll 命令那一刻常为 true）。旧判据把它当「不在 feed」→ **每条 scroll 命令开头都 `Page.navigate` 整页重载**（经 FB `fbsbx.com/maw_proxy_page` 重定向链回首页）→ feed 反复被钉回第一屏。
- 现有 `facebook-feed-continuity` spec 明文把「无打开的 dialog」写进 onTarget 条件——与真机行为冲突：FB **就地读不弹模态**，故 `dialogOpen` 对 FB 恒为良性浮层，这条守卫纯有害。
- 次生问题：`feed_exhausted → 立即 refresh` 的到底判据（旧「滚 2 次 0 新卡即到底」）在 FB 懒加载 + 虚拟化下容易误判——下一批还没渲染出来就判到底，加剧「一滚就换批回顶」。

## What Changes

1. **`ensureFeed` onTarget 去掉 `!dialogOpen`**：已在正确列表面（首页/搜索/群）且 feed 容器在场即为在目标，良性 `[role=dialog]` 绝不触发整页重载。真正的登录/验证码阻断仍由 `blockingReason` fail-closed 单独兜底（不受影响）。
2. **`scrollFeed` 到底判据改懒加载感知**：本轮 0 新卡时，只有「`scrollHeight` 不再增长（懒加载没在长）**且** 已接近底部（留约一屏余量）**且** 连续 2 轮确认」才诚实 `feed_exhausted`；否则继续下滚（单命令内有界 ≤8 轮、90s 预算内）。让 60 篇深度阈值（云端 `FEED_REFRESH_AFTER`，已存在）成为换批主路。
3. 新增 `FacebookFeedReader.scrollMetrics()` 探针（scrollY / scrollHeight / innerHeight）+ `ensureFeed` 导航决策诊断日志（导航决策此前不可观测）。

## Impact

- **Affected specs**: `facebook-feed-continuity`（MODIFIED 幂等断言的 dialog 条款 + ADDED 懒加载到底判据）。
- **Affected code**（edge `aidcp-edge`，已 land `fb8c5b3`）：`src/facebook/feed-reader.ts`（`ensureFeed` / 新 `scrollMetrics`）、`src/facebook/facebook-session.ts`（`scrollFeed` 到底判据 + 常量）。edge-only，无协议/云端改动。
- **验证**：真机修复后 26s，`timeOrigin` 恒定（零重载）、`scrollY` 3780→5066 持续下滚、`scrollHeight` 懒加载追加到 11394、`ensureFeed` 整页导航只剩启动 1 次、`feed_exhausted`=0；单测 3 新用例 + edge 全量 1342 全过。
- **生效边界**：客户端边缘代码，生效需重打客户端包（非云端部署）；出安装包按惯例默认不做，等显式发版。
- **不在本 change 内**：点赞仍 0（独立问题——内容相关性粗筛 `content_curator` 拒了越南语招工帖），见 backlog 簇 82。
