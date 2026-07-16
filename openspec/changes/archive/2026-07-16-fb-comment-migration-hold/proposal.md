## Why

Facebook 的自动 feed-inline 热帖评论（命中人设、自动批准）真机上偶发**"弹一下群帖地址又秒回首页、已批准评论被静默丢弃"**（2026-07-16 dev，account 61591753702668，当日 6 次授权丢 1）。两个独立根因叠加：

1. **暂停态在迁移开始前就解除了**。Facebook 是"就地读"（帖子在 feed 内联读，浏览器不离页），要评论必须两步迁移到帖子 permalink 详情页。现行 `comment-interaction` 规范要求 `comment.approved` 终局**先解除暂停态再下发迁移命令**（避免迁移/评论命令被自己设的暂停态扣住）。但这一解除让**整个迁移在途窗口失去保护**：浏览主循环照发 `page.scroll`，迁移落地后那条排队的 scroll 跑 `ensureFeed`，发现当前是单条群帖详情页（不在可滚动列表白名单）→ 整页把浏览器拽回首页，迁移拿不到详情、`open_failed`。

2. **详情页水合慢于探测窗口**。边缘详情探测窗口约 10s（`settleMs 2500 + surfaceProbeRounds 14 × pollMs 700`），而 Facebook 详情正文水合实测 7–12s；慢一拍即误报 `open_failed`、丢掉已批准评论。这是当日那次掉评论的**直接**原因。

小红书（读评同为详情面、迁移结构性不可达）不受影响，本变更零回归。

## What Changes

- **暂停态持续到两步迁移终局（云端）**：当评论 surface ≠ 读 surface（Facebook）时，`comment.approved` **不再**在下发迁移前解除暂停态；暂停态从评估一直持续到两步迁移的终局（`comment.done`），期间统一命令出口继续扣住一切会离页的浏览/互动命令。
- **迁移支线命令豁免自身暂停（云端）**：本评论支线自己的迁移 `open_note{purpose:'navigate'}` 与随后的 `comment` 命令 MUST 豁免该暂停态（它们本就是暂停要保护的对象），不被自己设的暂停扣住。其余离页命令（`page.scroll` / 换帖 `open_note` / `refresh` / feed 续滚 / stale-target 重扫）在整个迁移窗口内保持被抑制。
- **看门狗时钟恢复时机不变**：仍在终局（`comment.done` / `comment.skipped`）恢复，与暂停态解除耦合于同一终局点。小红书路径（读评 surface 相等、迁移不可达）行为完全不变。
- **放宽 Facebook 详情探测窗口（边缘）**：把详情 article 水合探测窗口从约 10s 放宽到约 15–17s（`surfaceProbeRounds` 14→约 22），给慢水合的详情页足够时间；仍有界，远在命令超时 90s 内。诚实失败语义不变——超窗仍如实 `open_failed`。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `comment-interaction`：评论支线在途暂停态的**解除时机**由"`comment.approved` 终局先解除再下发迁移"改为"持续到两步迁移终局才解除，迁移/评论命令豁免自身暂停"。读评 surface 相等的平台（小红书）不受影响。

## Impact

- **云端** `aidcp-cloud/src/orchestrator/role-dispatcher.ts`：`comment.approved` 处理器暂停态解除时机 + `sendCommand` 暂停闸的支线命令豁免判据。不触及 `EdgeTaskCoordinator` / `edge-task-lease-client` / 风控 / 协议（与并行 change `browser-slot-scheduling` 文件隔离，无冲突）。
- **边缘** `aidcp-edge/src/facebook/post-reader.ts`：详情探测窗口常量。
- **无协议改动、无风控改动、无依赖变更**。安全红线：迁移仍 fail-closed（未落地绝不在当前页发评论）；暂停窗口有界（评论支线生命周期，终局必解除）；绝不静默假成功。
- 验收：桩测（迁移在途 scroll 被抑制、支线命令放行、终局解除暂停）+ 真机（热帖评论不再"闪回首页"、慢详情页评论能发出）——真机项收拢到 `docs/real-machine-acceptance-backlog.md`。
