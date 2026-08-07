## RENAMED Requirements

- FROM: `### Requirement: 协议 v2 新增 interaction.comment 并三处同步`
- TO: `### Requirement: 协议 v2 新增 {platform}.note.comment 并三处同步`

## MODIFIED Requirements

### Requirement: 协议 v2 新增 {platform}.note.comment 并三处同步

系统 SHALL 新增 cloud→edge 消息 `{platform}.note.comment`（payload `CommentPayload{noteId, text, thinkMs?}`；词汇批 5 起评论命令带平台段＋对象段，`xiaohongshu.note.comment` / `facebook.note.comment` 两个变体）。
两份 `src/comm/protocol.ts`（edge / cloud）MUST 逐字一致新增该 `MessageType` 与 payload；`command-bridge.ts` MUST 加 `comment → {platform}.note.comment` 映射；
`EdgeCommand.action` 并集 MUST 加 `comment`；`docs/protocol.md` 头部计数与 §2 表 MUST 同步；两份 `protocol-contract.test.ts` 的 `ALL_MESSAGE_TYPES` 与计数断言 MUST 同步（历史立项时为 54 改 55，计数随后续词汇批演进）。

#### Scenario: 两份 protocol.ts 不漂移
- **WHEN** 新增 `{platform}.note.comment` 后运行 `npm run typecheck` 与 `npm run test:acceptance`
- **THEN** `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 计数断言 MUST 全过；任一处（两份 protocol.ts / command-bridge / docs / 两份 contract test）漏改 MUST 使构建失败

#### Scenario: 红线反例——单边新增消息（禁止）
- **WHEN** 仅在 cloud 侧 protocol.ts 新增 `{platform}.note.comment` 而未同步 edge 侧 / contract test 计数
- **THEN** MUST 视为违规、不予合入；协议三处 + 两份 contract test MUST 原子同步
