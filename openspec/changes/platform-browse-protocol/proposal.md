## Why

C1a（`platform-registry-shape`）把「动作是否支持 / 在哪个 surface 执行」变成了静态声明，但真正让 Facebook 在信息流就地读/赞、让评论在需要时才迁移进详情页，还差三件云端+协议的事：

- **协议要能承载 surface/purpose，且回执要能自证目标**：今天 `action.completed` 不带 noteId，归属靠「like 总在 note.detail 之后、`currentNoteId` 即被互动」的假设（`src/comm/handler.ts:409-410`）。一旦互动可能发生在信息流就地，这个假设失效，会串账。
- **评论迁移需要一个不破坏「调度器是唯一命令式接线点」的机制**：审批通过后若要「先开详情页再评论」，必须回执驱动、fail-closed，navigate 没到目标就绝不发评论。
- **信息流刷不动时要能自愈**：FB 信息流到底/被接管后若不映射为 refresh，会转 idle、触发 240s 看门狗循环；人审在途时若 idle nudge 把账号滚离目标，会破坏审批时序。

本变更加 4 个 optional 协议字段（**0 新消息类型、白名单 0 改动、MessageType 计数不变**）+ 云端归账仲裁（独立见证驱动，非 noteId 同义反复）+ 回执驱动两步评论迁移 + `feed_exhausted→refresh` 映射 + 审批期抑制 idle nudge。**Facebook 表值仍等于今天（不下发 `surface:'feed'`）⇒ 阶段 0 零行为变化。**

## What Changes

- 两份 `src/comm/protocol.ts`（逐字一致）加 4 个 optional 字段：`NoteOpenPayload.surface?:'feed'|'detail'`、`NoteOpenPayload.purpose?:'read'|'navigate'`、`ActionCompletedPayload.noteId?:string`（**MUST 从被点 article DOM 重新派生规范 postId，MUST NOT 复制命令 payload**）、`ActionCompletedPayload.observation?:{surface?;listKey?;author?;textPreviewHead?;reactionText?;articleIndex?}`（独立见证包）。全 optional、缺省=今天。
- `src/comm/command-bridge.ts`：**映射表零改动**（无新动作），只改 `open_note`/`scroll` 的 payload 构造透传 `surface`/`purpose`。
- `src/comm/handler.ts` 归账仲裁：回执带 noteId 时用它、缺省时 XHS 逐位回落 `currentNoteId`、feed-surface 缺 noteId 则拒记账；独立见证（`observation` 与选中卡逐字段）不符 ⇒ `target_mismatch` + 拒写血缘 + 灰度回滚计数（风控仍按真实发生计数）；`no_target(stale)` ⇒ 快照过期重驱、不计配额失败。
- 评论迁移**回执驱动两步**（dispatcher）：`open_note{purpose:'navigate'}` → 等其 `action.completed{ok, observation.surface:'detail', noteId 匹配}` → 才发 `comment`；任一步失败 ⇒ 不发 comment + 显式回报操作员（飞书）。触发条件（`resolveCommentSurface≠resolveReadSurface`）由 C1a 声明，阶段 0 FB 相等 ⇒ 不触发。
- `feed_exhausted` 回执 ⇒ 云端立即映射为 refresh。
- 审批在途抑制 idle nudge（平台无关机制：session flag 由审批闸置、dispatcher 的 idle_nudge 翻译器门控，**不复用 `pauseClock`**——它不冻 idle）。
- `observedSurface` 仅审计（回声与静态期望不符则 warn）。

## Capabilities

### Modified Capabilities

- `platform-runtime-abstraction`: `surface`/`purpose` 与派生 `noteId`/`observation` 是平台无关的 optional 字段扩展，不引入以平台名命名的消息类型、不改变消息计数。
- `command-pacing`: 「离开一条内容前保证停留达标」的锚点从「详情页 `navigation.back`」推广到「详情页返回**或** feed 内联读完后的下一条 `page.scroll`」；feed 停留新增第三锚点（内联读，边缘本地 read floor，锚点 `inlineReadStartedAt`），三锚点取 max、MUST NOT 相加。XHS 既有 scenario 原样保留。

### New Capabilities

- `platform-browse-surface`（延续 C1a）：新增协议承载 surface/purpose、独立见证归账仲裁、回执驱动两步评论迁移、`feed_exhausted→refresh`、审批期 idle-nudge 抑制等编排契约。

## Impact

- 协议四处同步：`aidcp-edge/src/comm/protocol.ts` + `aidcp-cloud/src/comm/protocol.ts`（逐字一致，MessageType 枚举不动 ⇒ AC-PROTO 全绿）+ `aidcp-cloud/src/comm/command-bridge.ts`（payload 构造透传）+ `aidcp-edge/src/client/edge-client.ts:487-529` **白名单零改动**（`note.open`/`page.scroll`/`interaction.like`/`interaction.comment` 均已在内；tasks.md 记「已核对无新增主动命令类型」）+ 附 `docs/protocol.md` 补两行。
- 云端：`aidcp-cloud/src/comm/handler.ts`（归账仲裁）、`aidcp-cloud/src/orchestrator/role-dispatcher.ts`（🔴 热点：回执驱动迁移、feed_exhausted→refresh、idle nudge 门控、observedSurface 仅审计）。
- **撞车规避**：`facebook-join-actuation-decouple`（0/24 deferred，也动 protocol.ts 加 clickToken）⇒ **C1b 先走**（纯 optional 字段、不动枚举），join-decouple 起手 rebase。`facebook-post-publish`/`edge-environment-platform-select` 对 `platform-runtime-abstraction` 都只 ADD、不同 header ⇒ 归档顺序固定即可。`humanize-interaction-prompts` MODIFY 的是 comment-interaction/interaction-appraisal，本 change 一条不碰。
- edge、console、数据库、`ol` 部署不受影响；FB 表值=今天 ⇒ 阶段 0 零行为。
