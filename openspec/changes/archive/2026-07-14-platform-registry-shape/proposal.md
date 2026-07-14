## Why

云端浏览闭环只有一套，小红书与 Facebook 共用同一批角色和同一个调度器。「必须先打开详情页才能点赞/评论」这个假设不是一处可读的开关，而是被**事件订阅拓扑隐式焊死**的（点赞的唯一上游是详情页数据到达，评论的唯一上游是点赞已完成）。Facebook 只能靠「做不了就诚实回 `capability_unsupported` 然后硬推进」绕过。三个具体病灶：

- **能力声明基本没被消费**：`src/platform/registry.ts` 的 `capabilities` 在云端只有一个读点（`src/orchestrator/role-dispatcher.ts:1008` 的 `.includes('browse')`），`interact`/`notification`/`patrol`/`join` 四个能力词零读点——「声明了没人读」。
- **Facebook collect 靠数值巧合不发**：`command-bridge` 无平台拦截，实际不发只因 `interaction-appraiser-role.ts` 要求 `collectCount>=likeCount×ratio && likeCount>0` 而 FB `collectCount` 恒 0；任何阈值调整都会让它漏出去。
- **平台差异散落在 dispatcher 的裸 `platform==='facebook'` 分支**（`facebookScrollDwellMs` 等），且循环闭合（back vs scroll）与评论迁移触发若靠运行时推断会引入时序竞态。

本变更把「平台差异」收进一个**薄声明层**：动作是否支持（`noteActions`）与动作在哪个 surface 执行（`noteSurfaces`）两个正交概念拆开，每个声明字段**点名唯一消费者**，并把循环闭合/迁移触发从「运行时推断」改为「查静态表」。**全 additive、Facebook 表值等于今天 ⇒ 零行为变化**，只解锁后续 C1b（协议）与 C2（edge 就地互动）。

## What Changes

- `src/platform/registry.ts` 的 `PlatformRegistryEntry` 从 `capabilities: readonly PlatformCapability[]` 扩为：
  - `noteActions: Record<NoteScopedAction, {supported:true}|{supported:false;reason}>`（7 个 note-scoped 动作全覆盖，typecheck 逼每格表态，杜绝「靠数值巧合不发」）；
  - `noteSurfaces: Record<'read_content'|'like'|'comment', 'feed'|'detail'>`（只对「离不离开列表是真问题」的 3 个动作建模）；
  - `capabilities: Record<'browse'|'feed_refresh', {supported:true}|{supported:false;reason}>`（v1 只保留两个真消费者，砍掉零读点能力词）。
- `role-dispatcher.ts:1008` 会话启动闸从 `.includes('browse')` 迁移到 `.browse.supported`（同提交，避免形状迁移把 XHS 挡在门外）。
- 新纯函数文件 `src/platform/surface.ts`：`resolveReadSurface(platform)` / `resolveCommentSurface(platform)`。
- dispatcher 循环闭合 back vs scroll、评论迁移触发**改读静态表**（`resolveReadSurface`/`resolveCommentSurface`），不读运行时 `observedSurface`；新增每 note 重置的 `currentNoteMigratedToDetail` 标志（由云端发迁移命令时置位，非 echo）。
- 新私有 `sendNoteScopedCommand()`（包在 `sendCommand` 外）：`noteActions[a].supported===false ⇒ 根本不下发 + 审计 reason`，成为 collect 等不支持动作的**唯一显式拒绝点**。
- `feed_refresh` 能力闸接入 FeedScroller 构造；`facebookScrollDwellMs` 泛化为 `pacing.feedScrollDwellFloorMs` 消费者。
- 深读短路注入闭包（照抄 `isInteractionEligible` 的注入方式）：`canBrowseImages()`/`canScrollComments()`/`canRefresh()`，**全部 fail-open**（registry 查不到/异常 ⇒ 返回 true 按今天执行，绝不默认 false 静默砍 XHS）。角色据此走已有 else 分支如实短路，带 reason，绝不伪造。

不新增协议消息类型、不动 `command-bridge` 映射表、不动 edge。

## Capabilities

### New Capabilities

- `platform-browse-surface`: The cloud declares per-platform which note-scoped actions are supported and on which surface (feed vs detail) each is performed, with every declared field having exactly one consumer, and drives loop closure and comment migration from that static table rather than runtime inference.

## Impact

- Cloud platform registry + new surface helpers: `aidcp-cloud/src/platform/registry.ts`, `aidcp-cloud/src/platform/surface.ts`（新）。
- Cloud dispatcher: `aidcp-cloud/src/orchestrator/role-dispatcher.ts`（🔴 热点，与 `facebook-dev-autobrowse-enable`/`facebook-post-publish` 串行）——启动闸 Record 迁移、静态 back/scroll 分流、`currentNoteMigratedToDetail`、`sendNoteScopedCommand`、`feed_refresh` 闸、深读短路注入。
- Cloud deep-read roles: `aidcp-cloud/src/agents/deep-reader.ts`、`aidcp-cloud/src/agents/comment-reviewer.ts`（消费注入闭包如实短路，fail-open）。
- 协议、edge、console、数据库、`ol` 部署**不受影响**。阶段 0 行为：Facebook 表值=今天 ⇒ 唯一可观测差异是修 bug（collect 显式拒绝审计 / 不误发 refresh / 不下发 browse_images+scroll_comments）。
