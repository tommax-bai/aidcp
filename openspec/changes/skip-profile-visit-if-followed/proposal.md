## Why

笔记详情页本身就带"是否已关注"的标记（作者区 `.author-wrapper .follow-button` 文案 `已关注/互关`）。当作者**已被关注**时，系统当前仍会在互动后照常 `AuthorEvaluator → profile.open → 浏览主页 → FollowAgent → follow`，最后才在 `interaction.follow` 命中 `already_followed`（良性 no-op）。这等于**为已关注的作者白跑一次主页导航 + 主页深读 + 关注尝试**——既浪费往返，也不拟人（真人不会反复点进已关注者的主页去再关注一次）。

详情页的关注态在 `note.open` 时即可读到（与 `executeFollow` 用的是同一选择器），完全可以**提前**短路掉整条主页子链。

## What Changes

- **edge**：`note.open`（`openCard` → `reportNoteDetail`）时，探测笔记 modal 作者区关注按钮状态（文案 `已关注/互关` 或 `aria-pressed='true'`，复用 `executeFollow` 的检测口径），在 `NoteDetailPayload` 上带回 `authorFollowed: boolean`。
- **协议（三处同步，不新增消息类型→消息总数仍 44）**：`NoteDetailPayload` 增可选 `authorFollowed?: boolean`（edge/cloud 两份 `protocol.ts` 逐字一致 + `docs/protocol.md`）。
- **cloud**：`NoteData` 增 `authorFollowed?: boolean`，`updateNoteData` 从 `note.detail` 透传；`AuthorEvaluator.onInteractionCompleted` 在取到 `noteData` 后**提前判定**：若 `authorFollowed===true`，直接 `emit profile.skipped`（reason `already_followed`）并返回，**不调 LLM、不进主页、不浏览、不发起关注**。
- **保留兜底**：detail 未能读到关注态（modal 无按钮/布局变体）时 `authorFollowed` 缺省 falsy → 走原流程；最后一步 `interaction.follow` 的 `already_followed` no-op（已实现）仍作为兜底。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `author-profile-visit`: 新增「已关注作者不进主页」要求——`note.detail` 携带 `authorFollowed`；当其为真时 `AuthorEvaluator` SHALL 跳过主页子链（skipped/already_followed），不 `profile.open`/不浏览/不关注。

## Impact

- **edge（aidcp-edge）**：`src/browse/browse-session.ts`（`openCard` 探测关注态 + `NoteDetailPayload.authorFollowed`）；`src/comm/protocol.ts`（`NoteDetailPayload.authorFollowed`）。
- **cloud（aidcp-cloud）**：`src/comm/protocol.ts`（同上，逐字一致）；`src/orchestrator/role-dispatcher.ts`（`NoteData.authorFollowed` + `updateNoteData`）；`src/agents/author-evaluator.ts`（提前 skip 闸）。
- **docs**：`docs/protocol.md`（`NoteDetailPayload.authorFollowed` 说明）。
- **风险面**：纯增量字段（向后兼容，旧 edge 不带即 falsy→原流程）；不改互动/深读链；不破坏「未互动不进主页」既有语义；与 `interaction.follow already_followed` no-op 兜底叠加，双保险。AC-PROTO 消息总数不变（仅加字段）。
