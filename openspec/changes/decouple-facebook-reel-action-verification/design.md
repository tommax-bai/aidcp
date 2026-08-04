## Context

Facebook can replace a Reel action control after the click or while a neighboring action is running. The current Edge router already resolves the current Like or Follow control on every verification probe. The Native loops, however, terminate immediately when one probe reports that the fresh control is missing or ambiguous. Both behaviors can return `verify_indeterminate` before the canonical Reel's replacement control becomes readable.

Like and Follow already remain separate page commands with separate receipts. Cloud already selects and dispatches them independently. This change therefore belongs only to Edge's capability-owned post-dispatch verification; it does not require a new action collection, command envelope, scheduler, or lifecycle state.

## Goals / Non-Goals

**Goals:**

- Verify Like and Follow from a freshly resolved control on the same canonical Reel.
- Use the existing bounded verification window to tolerate transient same-Reel re-render gaps.
- Preserve fail-closed accounting: only a positive same-Reel final-state witness returns success.
- Keep all Cloud cadence, risk, budget, cooldown, command, and receipt behavior unchanged.

**Non-Goals:**

- No action collection, batch command, combined receipt, or pending-action state machine.
- No concurrent Native page writes and no change to the single-active-command invariant.
- No replay, retry, alternate actuation path, compatibility branch, or new timeout setting.
- No Cloud, Console, protocol, database, policy, deployment, package, or installed-client change.

## Decisions

### Fresh same-Reel state is the verification authority

After the existing one-time commit, the capability will keep using its current canonical Reel locator and read the state of the current Like or Follow control. A pre-click node is not terminal verification authority.

This keeps verification bound to the business object that matters—the same canonical Reel and, for Follow, the same unique author—while allowing Facebook to replace internal DOM nodes. Keeping the original node as terminal authority was rejected because DOM identity is not Reel identity.

### Existing verification windows absorb transient unreadability

A same-Reel `target_not_found` or `ambiguous_target` probe will remain inside the current bounded verification loop. A later fresh positive state can confirm success. If the latest state is still unreadable when the existing deadline expires, the result remains ambiguous non-success. An observed different canonical Reel or author still terminates as ambiguous immediately.

Adding retries or a second action attempt was rejected: the write may already have happened, so only observation may repeat.

### Keep Like and Follow independent

No combined action model is introduced. Each existing command commits at most once, observes its own final state, and emits its own existing receipt. The Native single-writer rule remains intact.

Changing Native execution concurrency was rejected because it expands the scheduling and safety model without being required to correct stale-node verification.

## Risks / Trade-offs

- [A same-Reel replacement control is briefly absent through the deadline] → Return the existing ambiguous non-success and do not replay or count success.
- [The page advances to another Reel during verification] → Compare the fresh canonical Reel identity and fail ambiguous immediately.
- [Follow author association changes or becomes non-unique] → Require the existing unique author-bound locator and fail closed.
- [Source validation passes but installed behavior is unchanged] → Report source validation separately; packaging and real-account acceptance remain out of scope.

## Migration Plan

1. Update Edge's Like and Follow bounded verification loops and focused regressions.
2. Run focused router and Native tests, Native capability gates, Edge typecheck, and strict OpenSpec validation.
3. Integrate the Edge source change through the normal branch flow. No data migration or Cloud deployment is required.
4. Roll back by reverting the Edge commit; no persistent state or protocol migration is involved.

## Open Questions

None.
