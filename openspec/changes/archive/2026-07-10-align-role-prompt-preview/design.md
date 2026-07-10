## Context

The role page reads its catalog and prompt preview from `aidcp-cloud`. The page itself only edits model, temperature, and thinking-mode settings; prompt text is read-only. The audit found three drift sources:

- Some active catalog roles are not previewable because they are not RoleDispatcher instances or are missing from publish preview builders.
- The publish preview note still describes a detached built-in persona even though production publishing now builds input with the target account persona and rejects unbound accounts.
- Category display labels are too narrow for the current publish role set, especially analysis, planning, classification, and judgment roles.

## Goals / Non-Goals

**Goals:**

- Make every active catalogued text LLM role return a faithful prompt preview, including command-style comment search roles and publish topic roles.
- Make publish prompt preview use account persona when an account is selected, and honestly mark sample fallback for unbound accounts.
- Update category display labels to describe the existing buckets without changing category keys or runtime model fallback.
- Keep prompt construction logic and runtime dispatch behavior unchanged.

**Non-Goals:**

- No prompt editing support.
- No database schema change.
- No role graph, event bus, edge protocol, risk-control, or production deployment behavior change.
- No migration of existing `category_config` rows or category IDs.

## Decisions

1. **Use preview adapters for command-style browse roles.**

   `CommentSearchTermGenerator` and `CommentTargetPicker` are command-style roles invoked by the comment scheduler rather than registered in `RoleDispatcher`. They already expose `previewPrompt()`, so the preview provider should receive lightweight preview instances alongside dispatcher roles instead of forcing them into the runtime dispatcher.

2. **Make publish preview builders accept a sample persona.**

   Publish roles already use `trigger.generateInput.soul` in production. The preview registry should keep using minimal legal sample inputs, but let the provider substitute the selected account soul into those sample inputs. If no account is selected, it uses the packaged sample soul. If the selected account lacks persona, it falls back to sample soul and marks the fallback honestly.

3. **Add missing topic preview builders.**

   `TopicGenerator` and `TopicEvaluator` already call `buildTopicGenerationPrompt` / `buildTopicEvaluationPrompt`; the preview registry should call those same builders with sample finalized content and sample candidates.

4. **Broaden category labels, not category keys.**

   Category IDs are part of model fallback. Moving roles between keys would change which category default model they inherit. This change only broadens Chinese display labels to match the mixed responsibilities already present in each bucket.

## Risks / Trade-offs

- **Risk: publish preview with account persona may be mistaken for live data.** → Keep explicit sample-data note and existing placeholder values; only persona changes.
- **Risk: command-style role preview instances may accidentally need LLM.** → Use their existing `previewPrompt()` path only and pass a dummy LLM that throws if called.
- **Risk: category label changes require cloud/console sync.** → Update both the cloud catalog and console local metadata in the same change; verify with typecheck/tests.
