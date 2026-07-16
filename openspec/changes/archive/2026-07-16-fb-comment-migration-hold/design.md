# Design

## Context

真机（2026-07-16 dev, FB account 61591753702668）现象：自动热帖评论时"弹一下群帖地址又秒回首页、已批准评论被丢"。经 edge/cloud 双侧代码 + 真机日志坐实，两个**正交**根因：

1. **迁移在途窗口无保护（云端）**。FB 就地读 → 评论要两步迁移到 permalink。现行 `comment-interaction` 规范要求 `comment.approved` 终局**先解除评论支线暂停态再下发迁移**（否则迁移/评论命令被自己设的暂停扣住）。这一解除使迁移在途期间浏览主循环照发 `page.scroll`；迁移落地前后那条 scroll 跑边缘 `ensureFeed`，当前 surface=`group_post` 不在可滚动列表白名单 → 整页把浏览器拽回首页。
2. **详情探测窗口偏紧（边缘）**。`post-reader` 探测窗 `2500 + 14×700 ≈ 12.3s`，而 FB 详情正文水合实测 7–12s；慢一拍即 `open_failed`、丢评论。**这是当日那次掉评论的直接原因**。

## Goals / Non-Goals

- **Goals**：迁移在途期间不被并发 browse 命令离页；慢水合详情页有足够时间；两者都**有界 + 诚实失败**、零 XHS 回归。
- **Non-Goals**：不动 `EdgeTaskCoordinator` / `edge-task-lease-client` 那套边缘租约（与并行 change `browser-slot-scheduling` 文件隔离）；不引入新的通用"离页行程租约"抽象（YAGNI——现有机制够用）；不改协议 / 风控。

## Decisions

### D1 云端：以 `pendingMigration` 为迁移在途闸，而非延长 `commentInflight`

**选型**：在统一命令出口 `sendCommand` 增加一道基于 `pendingMigration != null` 的抑制闸——迁移在途期间扣住一切会离页的 browse/互动命令，仅放行本评论支线自己的迁移 `open_note{purpose:'navigate'}` 与后续 `comment`（新判据 `isCommentSublineCommand`）。

**为何用 `pendingMigration` 而非延长 `commentInflight`**：`pendingMigration` 在**迁移下发前置位、且已在所有终局（落地回执 / `migrateSent=false` / reset / suppression / preempt）清空**。以它为闸 → 抑制窗口生命周期天然正确、**零"漏清终局导致 commentInflight 永真、账号被钉死"风险**。延长 `commentInflight` 则需在每个终局补清、易漏一处成活锁（该标志现仅一处清）。观察行为等价，取更安全者。

**为何放行 `open_note{purpose:navigate}` 与 `comment`**：它们**是**迁移支线本身、是暂停要保护的对象；不放行会被自己设的闸扣住、静默丢弃（等价于旧代码"先解除再下发"要规避的问题，改由白名单豁免解决）。这两个 action 语义上专属评论支线（navigate-purpose open 仅迁移用、comment 仅评论支线用），故判据无需再按 noteId 收窄。

**覆盖窗口**：`pendingMigration` 覆盖迁移 navigate 窗口（下发→落地回执）。第二步 `comment` 在落地回执处**同步**下发（`pendingMigration` 已清），紧接其后；成功案例实测评论在此同步点即发出，不留可被 scroll 插入的缝。评论在边缘执行期由既有 `commentHandler`（写者跟踪）承接，非本闸职责。

### D2 边缘：放宽详情探测窗口 14→22 轮

`post-reader` `surfaceProbeRounds` 14→22（`2500 + 22×700 ≈ 17.9s`），覆盖 FB 详情水合上界 12s + 余量。仍有界、远在命令超时 90s 内；**诚实失败语义不变**——超窗仍如实 `open_failed`。这是纯常量放宽，无控制流改动。

## Risks / Trade-offs

- **抑制闸泄漏 → 会话钉死**：靠 `pendingMigration` 生命周期已闭合（D1）规避；回归测试断言"迁移终局即解除抑制"。
- **探测窗放宽 → 单条慢帖多占约 6s**：可接受（远小于命令超时；迁移本就是低频的热帖评论）；不改并发。
- **与 `browser-slot-scheduling` 并行**：文件级隔离（本 change 只碰 `role-dispatcher.ts` + `post-reader.ts`；对方碰 `EdgeTaskCoordinator`/`edge-task-lease-client`/`main.ts`/`connection-runtime.ts`/`content-scheduler.ts`），集成前 rebase 最新 master 再 ff。

## Migration / Rollout

- 云端随 dev 部署即生效。边缘随本地客户端重跑生效（属本地 dev 运行，非出安装包）。
- 真机验收（热帖评论不再"闪回首页"、慢详情页评论发出）收拢到 `docs/real-machine-acceptance-backlog.md`。
