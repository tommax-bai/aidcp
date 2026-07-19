## Context

The existing reply preview accepts only operator-entered simulation fields. Console initializes `videoTitle`, `userName`, and `userMessage` as empty strings, converts them to `null`, and Cloud correctly applies published/draft fallbacks. Cloud already stores the real inbound message, participant name, and source title, but the internal reply-configuration API does not expose a scoped projection for preview selection.

The change crosses Cloud and Console, must preserve the preview permission boundary, and must not turn a read-only preview into a sync or reply-job action.

## Goals / Non-Goals

**Goals:**

- Allow an operator to choose a recent real inbound interaction as preview input.
- Populate the existing preview request fields from a read-only, account-scoped Cloud projection.
- Prefer the most recent real interaction when one exists while retaining an explicit manual simulation mode.
- Preserve the existing deterministic renderer, risk review, and no-side-effect preview behavior.

**Non-Goals:**

- Re-render or mutate an existing reply job.
- Trigger Edge synchronization or fetch platform data during preview.
- Change `account_name`, `support_channel`, template fallback semantics, or send behavior.
- Add a database migration or WebSocket protocol field.

## Decisions

### Add a dedicated read-only preview-context endpoint

Cloud will expose `GET /api/accounts/:accountId/reply-preview-contexts?channel=<comment|dm>&limit=<n>` under `interaction.config.preview`. It returns only fields needed by the existing preview input: thread/message identifiers for UI selection, channel, message type, inbound text, participant display name, source title, and inbound timestamp.

This is preferred over reusing the customer interaction API because Console authenticates through the panel API and must not impersonate a customer session. It is preferred over adding a thread identifier to `POST reply-preview` because the selected values should remain visible and editable before preview, and the existing preview renderer contract can remain stable.

### Query the latest inbound message directly

The store projection will join each interaction thread to its latest inbound message and scope every read by both `accountId` and the account's authoritative interaction `envKey`. It will not reuse the general interaction list projection because that projection's preview text may be the latest message in either direction.

### Keep DM content separately gated

Comment contexts require `interaction.config.preview`. DM contexts additionally require `interaction.dm.view_full`, matching the existing preview permission boundary. The endpoint will not return platform external IDs, attachment bodies, outbound text, or send-attempt data.

### Select the newest real context by default

When the preview panel loads and recent contexts exist, Console will select the newest context and copy its values into the existing preview form. The operator can select another context or switch to manual simulation. If no context is available, Console remains in manual mode and explains that no stored interaction can be selected.

The preview POST remains unchanged; it receives exactly the values displayed in the form. This avoids a hidden second read and makes stale input visible rather than silently substituting newer content.

## Risks / Trade-offs

- **Stored context can become stale after selection** → Preview sends the visibly populated snapshot; changing selection or reloading contexts refreshes it.
- **A real comment can still lack a source title** → The selector labels the missing title honestly and the existing configured fallback still applies.
- **Loading real DM text expands sensitive data exposure** → Require `interaction.dm.view_full` in addition to preview permission and return inbound text only.
- **Accounts without an active environment binding have no contexts** → Return an empty list and keep manual preview available.

## Migration Plan

1. Deploy Cloud endpoint and store projection first; the old Console remains compatible.
2. Deploy Console source selector after Cloud validation.
3. Rollback is independent: reverting Console restores manual preview; reverting Cloud after Console causes a bounded context-load error while manual preview remains available.

No data migration is required.

## Open Questions

None.
