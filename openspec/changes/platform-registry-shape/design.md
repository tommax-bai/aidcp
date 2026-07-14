# Design — platform-registry-shape (C1a)

> cloud-only、additive、无协议、Facebook 表值=今天 ⇒ 零行为变化。核心：把「必须先开详情才能 like/comment」从事件订阅拓扑隐式硬编码，变成显式静态数据；控制流走静态表不走运行时推断。所有 `文件:行` 为 2026-07-14 HEAD 实核。

## 1. 治法：拓扑是上界，能力表是选择器

订阅拓扑（`interaction-appraiser-role.ts:63` 只订 `reading.done`；`comment-appraiser.ts:66` 只订 `interaction.completed`）保持不变——它是所有平台的最长路径。把「哪些站走哪几段」从订阅边移到**数据**（registry），不支持的段由角色走已有 else 分支如实短路（`deep-reader.ts:88-100`、`comment-reviewer.ts` 的短路点）。**不引入中央状态机、不新增 `content.ready` 事件。**

## 2. registry 目标形状（两个正交概念拆开）

`src/platform/registry.ts` 的 `PlatformRegistryEntry`（现 `capabilities: readonly PlatformCapability[]` @ :37）扩为：

```ts
export type Surface = 'feed' | 'detail';  // 语义=编排是否离开列表，不是页面形态；dialog/drawer/modal MUST NOT 进此 enum

export type NoteScopedAction =
  | 'read_content' | 'like' | 'collect' | 'comment' | 'comment_like'
  | 'browse_images' | 'scroll_comments';

export type OrchestrationCapability = 'browse' | 'feed_refresh';  // v1 只保留真消费者

type NoteSupport = { supported: true } | { supported: false; reason: string };

interface PlatformRegistryEntry {
  // ...既有 platform/app/displayName/comment/scheduler...
  noteActions: Record<NoteScopedAction, NoteSupport>;              // 概念1：动作是否支持（全覆盖 Record）
  noteSurfaces: Record<'read_content'|'like'|'comment', Surface>;  // 概念2：surface（只 3 键）
  capabilities: Record<OrchestrationCapability, NoteSupport>;      // 编排能力（只 2 个真消费者）
  pacing: { feedScrollDwellFloorMs?: number };
}
```

**为什么 supported 全覆盖 Record 而 surface 只 3 键**：全覆盖逼 typecheck 让 FB collect 显式 `{false,reason}`（治「数值巧合」）；surface 只对 read/like/comment 有意义，给 collect/browse_images 编造 surface 是假抽象。

## 3. 唯一消费者表（写进 spec 的 MUST）

| 声明 | 唯一消费者 | 治的旧病 |
|---|---|---|
| `noteActions[a].supported` | 新私有 `sendNoteScopedCommand()`（`role-dispatcher.ts`）——唯一拒绝点 + 审计 | FB collect 数值巧合不发；FB browse_images/scroll_comments 无效往返 + 无效 LLM |
| `noteSurfaces[k]` | 新纯函数 `resolveReadSurface/resolveCommentSurface`（新 `src/platform/surface.ts`），被 `sendNoteScopedCommand` + back/scroll 分流 + 迁移触发共用 | 「必须先开详情」从隐式拓扑变显式数据 |
| `capabilities.browse` | `role-dispatcher.ts:1008`（`.includes('browse')` → `.browse.supported`，同提交） | — |
| `capabilities.feed_refresh` | FeedScroller 构造（`role-dispatcher.ts:791` 附近） | FeedScroller 无平台闸 ⇒ FB 误发 refresh |
| `pacing.feedScrollDwellFloorMs` | `role-dispatcher.ts:679 facebookScrollDwellMs()` 泛化 | 消一处裸 `platform==='facebook'` 分支 |

## 4. v1 表值（阶段 0 = 逐位等于今天）

| `noteSurfaces` | XHS | FB 阶段 0 |
|---|---|---|
| read_content / like / comment | detail | **detail**（灰度目标 read/like→feed 由 C2 旗标翻转；本 change 不翻）|

| `noteActions` | XHS | FB |
|---|---|---|
| read_content/like/comment | ✓ | ✓ |
| collect | ✓ | `{false,'no_collect_concept'}` |
| comment_like/browse_images/scroll_comments | ✓ | `{false,'v1_unimplemented'}` |

| `capabilities` | XHS | FB |
|---|---|---|
| browse | ✓ | ✓ |
| feed_refresh | ✓ | **✓**（受控重新导航实现在 C2；本 change 只声明 supported） |

## 5. dispatcher 三件事（控制流走静态表）

- **(a) `observedSurface` 只审计不控制**：`SessionContext.observedSurface` 保留但不参与任何控制流；唯一用途=回声与静态期望不符时 warn。**MUST NOT** 用它选 back/scroll、触发迁移。
- **(b) back vs scroll 读静态表 + 迁移标志（race-free）**：
  ```
  if (session.currentNoteMigratedToDetail)            ⇒ back
  else if (resolveReadSurface(platform) === 'detail') ⇒ back
  else                                                ⇒ scroll   // feed
  ```
  `currentNoteMigratedToDetail` 由云端发迁移命令时置位（非 echo），每 note 重置。XHS：read=detail 且迁移结构不可达 ⇒ 恒 back ⇒ 逐位零回归（与事件到达顺序无关）。
- **(c) 深读短路注入闭包（全部 fail-open）**：照抄 `role-dispatcher.ts:803 isInteractionEligible` 的注入方式注入 `canBrowseImages()`/`canScrollComments()`/`canRefresh()`。**registry 查不到/异常 ⇒ 返回 true 按今天执行**，绝不默认 false 静默砍 XHS。角色短路必如实（`imagesBrowsed:0`+reason），MUST NOT 伪造；角色 MUST NOT import registry / 出现 `platform==='x'`。

> 评论迁移的**触发条件**（`resolveCommentSurface≠resolveReadSurface`）在本 change 声明；迁移的**执行**（回执驱动两步）在 C1b。阶段 0 FB comment=detail、read=detail ⇒ 相等 ⇒ 迁移结构性不可达 ⇒ 本 change 零行为。

## 6. 接第 N 平台 MUST NOT 改的清单（写进 spec）

改了下面任一项 = 抽象漏了，回来补抽象，别在角色里加 `if (platform==='x')`：协议 `MessageType` 集合与语义、`command-bridge` 映射表、`edge-client` 白名单、`event-bus/types.ts` 的 `RoleName` 穷举、`RiskController`/状态机、`risk/pacing.ts` 中心值算法、所有 L3 角色代码与事件翻译层。**接新平台只需**：registry 加 entry（typecheck 逼每格表态）+ `PlatformId` union 加成员 + edge 写 driver/session/执行器 + 真机探针 + 登记验收簇。

## 7. 不做

- ❌ `capabilities` 含 publish/group_join/targeted_comment/search（零消费者，违反唯一消费者铁律）。
- ❌ `noteSurfaces` 含 collect/browse_images/scroll_comments/comment_like（surface 从不被独立查询 = 假抽象）。
- ❌ 协议字段 / `command-bridge` 改动（在 C1b）。
- ❌ C4 的 follow/profile_visit/patrol/notification 能力词（延后，避免放大与并发的 rebase 面）。
