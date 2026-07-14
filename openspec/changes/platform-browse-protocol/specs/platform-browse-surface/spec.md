## ADDED Requirements

### Requirement: Surface and purpose ride existing messages as optional fields

The protocol MUST carry read surface and open purpose as optional fields on the existing note-open message and MUST carry a derived note id and an independent observation packet as optional fields on the existing action-completed message. No new message type may be introduced and the active-command allowlist MUST NOT change. Every field MUST default to today's behavior so that any mix of old and new edge and cloud is byte-for-byte equivalent to today.

#### Scenario: Old edge and old cloud are unchanged

- **WHEN** a note-open command omits surface and purpose and an action-completed receipt omits note id and observation
- **THEN** the behavior is identical to before this change
- **AND** the message-type count and the two protocol enumerations are unchanged

### Requirement: Action receipts derive their note id from the acted-upon DOM

An action-completed receipt's note id MUST be derived from the actual acted-upon article's DOM as a canonical post id, and MUST NOT be copied from the command payload. When the receipt carries no note id, a detail-context receipt falls back to the session's current note id (today's behavior), while a feed-surface receipt with no note id MUST be refused for accounting rather than attributed to the current note. A navigate-purpose open MUST NOT report a decision note.detail and MUST NOT overwrite real reaction counts with zero.

#### Scenario: Feed-surface receipt without a derived note id is refused

- **WHEN** the connected edge declares feed-surface targeting and returns an action receipt with no derived note id
- **THEN** the cloud refuses to account the action and audits it
- **AND** it does not attribute the action to the session's current note

### Requirement: Interaction attribution is arbitrated by independent witness

The cloud MUST arbitrate interaction attribution by comparing the receipt's independent observation (author, leading text, reaction text) against the selected feed card field by field, not by comparing a note id to itself. A witness mismatch MUST yield a target-mismatch outcome that refuses to write interaction lineage and increments a grayscale rollback counter, while risk still counts the real occurrence. A stale no-target MUST be treated as an expired snapshot: the post id leaves the session candidates and cards are rescanned and reselected, and it MUST NOT be counted as an interaction-quota failure.

#### Scenario: Independent witness catches a wrong-card like in shadow

- **WHEN** a shadow like receipt's observed author and leading text do not match the selected card
- **THEN** the cloud records target-mismatch and refuses to write lineage
- **AND** it does not treat a returned note id equal to the command as proof of correctness

### Requirement: Comment migration is receipt-driven and fail-closed

When the comment surface differs from the read surface, the cloud MUST migrate to detail in two receipt-driven steps: emit a navigate-purpose open, wait for its action-completed with a detail-surface observation and matching note id, and only then emit the comment. If the navigate step fails, the cloud MUST NOT emit the comment and MUST report the approved-not-delivered comment to the operator. When the comment surface equals the read surface, migration MUST be structurally unreachable and no extra open is emitted.

#### Scenario: Navigate failure does not send the approved comment elsewhere

- **WHEN** the navigate-purpose open for an approved comment fails to land on the target detail
- **THEN** the comment is not emitted on the current page
- **AND** the approved-not-delivered comment is reported to the operator

### Requirement: Exhausted feed self-heals and approvals do not scroll the account away

An exhausted-feed receipt MUST be mapped immediately to a refresh so the session does not fall idle into the watchdog nudge loop. While a human approval is in flight, idle nudges MUST be suppressed by a session flag set by the approval gate and gated in the dispatcher's idle-nudge translation, without reusing the pause-clock mechanism, so the account is not scrolled off the target while waiting.

#### Scenario: In-flight approval is not nudged off target

- **WHEN** an idle nudge fires while a comment approval is awaiting the operator
- **THEN** the nudge is not translated into a scroll
- **AND** the account remains on the target rather than being scrolled away

## MODIFIED Requirements

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 复用现有平台无关命令语义。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达通用动作；除非新增真实通用语义，否则 `docs/protocol.md` 的消息计数与两端 protocol 枚举 SHALL 保持不变。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 作为既有消息上的**平台无关 optional 字段扩展**承载，不新增消息类型、不改变消息计数。

#### Scenario: 平台抽象不改变协议计数
- **WHEN** 完成 xhs driver 提取并运行协议契约验收
- **THEN** 两端 protocol 枚举和 `docs/protocol.md` 计数保持 Change 0 前一致，AC-PROTO 类检查通过

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 两端 protocol 的 `MessageType` 枚举与计数不变，AC-PROTO 全绿
- **AND** 这些字段的语义不以任何平台名命名、缺省时逐位等于今天
