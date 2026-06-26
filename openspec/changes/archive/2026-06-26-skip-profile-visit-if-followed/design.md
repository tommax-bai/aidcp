## Context

互动后主页子链：`interaction.completed` → `AuthorEvaluator.onInteractionCompleted`（`author-evaluator.ts:44`，取 `getNoteData` → LLM 判 visit/skip）→ `profile.worth_visiting` → `ProfileOpener` → `profile.open` → 边缘进主页 → `profile.detail` → `ProfileBrowser` → `FollowAgent` → `follow`。

实测：对**已关注**作者，这条链照跑，末端 `interaction.follow` 命中 `already_followed`（已改为良性 no-op，见 follow-already-followed-truthful-report）。但整条主页导航 + 深读 + 关注尝试都是冗余。

关键事实（已核实）：
- 笔记 modal 作者区有关注按钮，`executeFollow` 用选择器 `.author-wrapper .follow-button`（+ 主页变体）判 `已关注/互关/aria-pressed`（`browse-session.ts:820-828`）。`note.open`/`openCard` 在 `:668` 构造 `NoteDetailPayload` 上报——此刻即可读到该状态。
- `AuthorEvaluator` 以 `getNoteData(noteId)` 取 `NoteData`（`author-evaluator.ts:45`），故 `NoteData.authorFollowed` 可作为闸的输入。
- `NoteDetailPayload`（`protocol.ts:459`）当前仅 noteId/title/content/author/authorId/likeCount/collectCount。加可选字段不改消息类型集合（AC-PROTO 总数仍 44）。

## Goals / Non-Goals

**Goals:**
- 详情页已关注 → 跳过整条主页子链（不 profile.open/不浏览/不关注），省往返、更拟人。
- 增量、向后兼容；detail 读不到关注态时安全回退到原流程。

**Non-Goals:**
- 不改「仅互动后才评估进主页」既有触发语义（本闸在该触发之后、LLM 之前）。
- 不引入云端持久化"已关注关系"投影（仍靠平台实时信号；本次只用 detail 当下的按钮态）。
- 不动 `interaction.follow already_followed` no-op 兜底（保留为 detail 信号缺失时的双保险）。
- 不改主页深读/采集逻辑本身。

## Decisions

### D1：在 note.detail 携带 authorFollowed（edge 探测，云端单写状态来自平台实时态）
edge `openCard` 在上报 `note.detail` 前，对 modal 作者区跑一次轻量探测（复用 `executeFollow` 的选择器与 `已关注/互关/aria-pressed` 判定），置 `NoteDetailPayload.authorFollowed`。
- **为何**：关注态是平台**当下真实**信号（边缘只读取上报，不臆造/不持久化），符合「follow 只依据平台真实信号」。在 note.open 时读，能在主页子链启动**之前**就拿到。
- **缺省**：探测不到（无按钮/布局变体/异常）→ 不置或置 false（falsy）→ 原流程。

### D2：协议加可选字段（三处同步，消息类型不变）
`NoteDetailPayload.authorFollowed?: boolean`，edge/cloud 两份 `protocol.ts` 逐字一致 + `docs/protocol.md`。
- **为何**：协议 v2 铁律；加可选字段不改 `MessageType` 穷举（AC-PROTO-02 仍 44），但两份定义须保持一致。

### D3：AuthorEvaluator 提前 skip 闸
`onInteractionCompleted` 取到 `noteData` 后、构造 prompt 之前：`if (noteData.authorFollowed === true) { emit profile.skipped(reason:'already_followed'); return; }`。
- **为何**：最早、最省的短路点——跳过 LLM 判定 + 全部主页子链。位置在「note_data_unavailable / author_unknown」校验之后、LLM 之前，保持既有 skip 语义一致。
- `NoteData.authorFollowed` 由 `updateNoteData` 从 `note.detail` 透传。

## Risks / Trade-offs

- [modal 关注按钮不稳定/布局变体读不到 → 漏判] → 安全回退原流程 + 末端 already_followed no-op 兜底，最坏退化为现状（不会更差）。
- [已关注但仍想浏览主页（拟人多样性）] → 用户明确要求已关注就不进主页；如需保留偶发主页浏览，可后续按概率放行（本次不做）。
- [authorFollowed=true 误报（把未关注当已关注）→ 漏掉该关注的作者] → 检测口径与 executeFollow 完全一致（同选择器、同文案/aria 判定），executeFollow 本就据此决定不点击，故一致性有保证；真未关注时按钮文案为「关注」不会命中。
- [协议三处漂移] → 严格三处同步 + 两仓 `npm run typecheck` + AC-PROTO 全过。

## Migration Plan

1. 协议：edge+cloud `protocol.ts` 加 `NoteDetailPayload.authorFollowed?`（逐字一致）+ `docs/protocol.md`；两仓 `typecheck`。
2. edge：`openCard` 探测 + 回填 `authorFollowed`。
3. cloud：`NoteData.authorFollowed` + `updateNoteData` 透传 + `AuthorEvaluator` 提前 skip 闸。
4. 回归：两仓 `test:acceptance`（AC-PROTO 44 不漂移）→ `test`；补 AuthorEvaluator「authorFollowed→skip」单测、edge note.detail 带 authorFollowed 单测。
5. 部署：cloud 按 §5 上 ECS；edge 本地运行。回滚：还原各处，无数据迁移。

## Open Questions

- 是否对"互关"与"已关注"区别对待（目前一视同仁视作已关注、跳过）？
- 是否保留极低概率"已关注也偶尔逛主页"以增加多样性（本次 Non-Goal）。
