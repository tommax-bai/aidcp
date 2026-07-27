## Context

The Facebook router runs inside Chrome through `Runtime.evaluate` and returns a bounded wrapper that Rust decodes in two steps: the CDP `result.value` becomes `BrowserCommandResult`, then its tagged `output.value` becomes a command-specific Rust type. Today every exception, missing wrapper/value, unexpected output kind, and Serde field mismatch becomes the same static `cdp_error` message. Because `group_join` is conservatively treated as a write command, that pre-actuation loss of information is then surfaced as `native_effect_ambiguous`.

The ideal-shape router, Rust decision, and fake-CDP join tests pass, but the same current source and binary fail on the real `Tianxing Bai` group page. Direct sampling showed that isolated `consent_probe` and `join_probe` values can decode, so the failure must be localized across the complete command path rather than inferred from one sampled probe.

The real page also showed a current-layout scope mismatch: Facebook displayed the positive member control `已加入`, the router classified its text as `joined`, but marked it `inTargetScope: false`. Any scope repair must retain the existing load-bearing rule that unrelated recommendation controls are never eligible for target membership or actuation.

The Phase A binary (`sha256 63d2f83eb6f7dd55b502c0607997cf3836bf3d9a54d363dd9828847e93d596b6`) resolved the apparent contradiction. On the exact full `group_join(click=false)` path it reported `operationStage=readiness_probe`, `decodeStage=cdp_exception`, and `actualType=object`; there was no typed field path because the router never produced JSON. A separate content-free CDP classifier repeated the sequence three times and identified `TypeError`, assembled router line 13 column 55, reason `cannot_read_property`, token `querySelectorAll`. The source boundary is `all(selector, root)` receiving a null root while Facebook navigation temporarily has no `document.body`; `joinContext` passes that null `main` to `commentEditor(main)`. Both the installed binary and the unmodified current build reproduce the generic failure, while the diagnostic binary exposes the stage. No click or commit window was entered.

## Goals / Non-Goals

**Goals:**

- Make every Facebook bounded-result failure identify a finite operation stage and decode stage.
- Report the exact typed field path and JSON category for Serde mismatches without exposing values or page content.
- Reproduce the failure with a diagnostic-only Native binary against the exact open group page, then repair only the observed contract mismatch.
- Distinguish observation-only `group_join(click=false)` failures from commands that may actuate.
- Recognize the target group's real header member control while retaining fail-closed exact-target joining.
- Verify source behavior, built Native behavior, and real browser read behavior as separate evidence layers.

**Non-Goals:**

- Returning raw CDP results, evaluated JavaScript, selectors, DOM text, URLs, credentials, cookies, storage, or arbitrary Serde messages.
- Broad numeric/string coercion, compatibility fallbacks, retries, cooldowns, hidden knobs, or page-wide Join selection.
- Changing Cloud scheduling, risk state, database state, or Console behavior.
- Performing another real group join. The target is already joined; the live gate is read-only.
- Packaging, signing, installing, injecting, or releasing a desktop client.

## Decisions

### 1. Use a two-phase evidence gate

Phase A changes only diagnostics and tests. A Native binary built from that state is run with `group_join(click=false)` against the exact already-open target. The captured tuple is recorded before Phase B edits any router field or Rust type.

Phase B updates the producer/consumer contract only for the captured field and adds the captured JSON category to a regression fixture. If the failure is not a typed-field mismatch, the same rule applies to the actual captured stage (for example, wrapper or result-kind repair); no speculative compatibility branch is added.

This is preferred over inspecting a single raw probe because the full command includes navigation/reuse, page and consent gates, readiness probes, result construction, and output typing. A sampled probe can be valid while another operation in that path fails.

### 2. Extend the existing error record with a bounded diagnostic object

`EngineError` and the internal Native IPC v2 `ErrorRecord` gain an optional diagnostic with this finite shape:

- `operationStage`: an allowlisted static group-join stage such as `reuse_probe`, `action_gate_page_probe`, `action_gate_consent_probe`, `readiness_probe`, `join_click`, or `verification_probe`;
- `decodeStage`: one of `cdp_exception`, `cdp_wrapper`, `output_kind`, `output_value`, or `typed_value`;
- `expectedKind`: an allowlisted static router result kind when relevant;
- `fieldPath`: a bounded Serde path, capped before protocol serialization;
- `actualType`: one of `missing`, `null`, `boolean`, `number`, `string`, `array`, or `object`;
- for `cdp_exception` only, a finite exception class/reason, bounded source line/column, and an identifier-only token extracted from a recognized engine-generated message pattern.

The existing stable error code and static message remain unchanged. The TypeScript client copies the optional diagnostic into `NativePageEngineError.detail`; it does not reinterpret the result or turn failure into success. Existing clients remain compatible because the field is optional and output-only in protocol v2.

Only the path and JSON category are retained from typed decode errors. For evaluated exceptions, the raw exception description is never serialized; only recognized error classes/reasons and an ASCII JavaScript identifier from a fixed pattern may be retained. The raw Serde/exception message and offending value are deliberately excluded because they can contain arbitrary page text. `serde_path_to_error` is preferred to custom recursive decoders because it identifies nested struct/list paths while preserving strict `deny_unknown_fields` behavior.

### 3. Annotate errors at the group-join orchestration boundary

The primitive decoder owns `decodeStage`, `expectedKind`, `fieldPath`, and `actualType`; the group-join caller adds `operationStage` as the error crosses each awaited boundary. This keeps generic Facebook decoding reusable while showing which invocation failed.

The initial reuse optimization currently discards a probe error with `.ok()`. It will remain a best-effort optimization, but any discarded diagnostic must be emitted once as a bounded stderr diagnostic tagged `reuse_probe`; it must not expose the payload or falsely fail a navigation that can proceed safely.

Alternative considered: encode operation names inside every decoder function. That duplicates orchestration context and cannot distinguish readiness from verification when both use `join_probe`.

### 4. Correct effect intent without inferring whether a click happened

`group_join(click=false)` is observation-only and therefore must not be classified as a may-write command. A diagnostic/decode failure for that command is `not_started`, not ambiguous.

For `click=true`, the existing conservative failure classification remains until the orchestration has explicit evidence that no actuation boundary was crossed. This change will not guess a click phase from elapsed time or from a parse failure. Successful and business-result paths keep their existing explicit phases.

### 5. Repair the observed null-root exception at its source

`joinContext` already treats a missing `main` as unresolved scope during navigation, but it still calls `commentEditor(main)`. JavaScript default parameters do not replace an explicit `null`, so `commentEditor` forwards null to `all`, which invokes `root.querySelectorAll` and throws before a bounded observation exists.

The repair is to make `commentEditor` return no editor for a null root. This preserves existing readiness behavior: a loading/null-body page yields `composerPresent=false`, unresolved scope, and the Rust readiness loop continues within its existing bound. It adds no retry, delay, coercion, or success path.

Alternative considered: make `all` silently replace every falsy root with `document`. That would widen every scoped query page-wide and could re-admit unrelated controls, so it is rejected.

### 6. Repair the real current-group header scope narrowly

Bounded inspection resolved the scope mismatch. The unique target `h1` and `已加入` control share a compact header ancestor, but that ancestor contains target-owned links such as `/groups/1611255345558924/members/` while the page path uses the vanity id `/groups/tuyendung.dongvan`. The old literal id comparison treated the numeric id as a foreign group and stopped the heading region before it reached the sibling action control.

The resolver learns one numeric alias only from a `/groups/<numeric-id>/members` link found below `main` in an ancestor of the unique target heading, and only while every group reference in that ancestor is either the URL id or that one numeric candidate. It never learns an alias from `main`, where recommendation cards live. Subsequent foreign-reference guards compare against that small alias set.

The scope repair may admit a header action candidate only when:

- the page URL yields the exact current group id/slug;
- one target `h1`/level-1 heading is positively resolved;
- a unique common header/action container relates that heading to the candidate;
- the container/candidate is not owned by a different-group navigation reference or suggestion card; and
- contradictory in-scope Join evidence still prevents an `already_member` verdict.

The real vanity-plus-numeric-members fixture and a main-level recommendation `/members` decoy pass together with all existing suggestion-rail fixtures. No page-wide fallback or label-only membership inference is introduced.

### 7. Keep delivery layers explicit

The Edge worktree produces source commits and a locally built Native binary for focused and real read-only validation. Integration lands through the default Edge branch after rebase and tests. Updating `/Applications/AIDCP.app`, building an installer, signing, notarizing, or releasing remains a separate explicitly authorized operation.

## Risks / Trade-offs

- [A field path includes untrusted map keys] → Limit diagnostics to strict typed structures, cap the path length, and test that raw values/text never appear.
- [The diagnostic protocol addition drifts between Rust and TypeScript] → Add serialization/client fixtures for present and absent diagnostics.
- [The reuse probe is intentionally swallowed] → Emit only its bounded diagnostic to stderr and continue the existing safe navigation path.
- [The header ancestor expands into recommendations] → Require unique target-heading ownership and keep foreign-reference and suggestion exclusions as narrowing guards; run all existing adversarial scope tests.
- [The already-joined live page no longer exercises the pre-join CTA] → Use it only for decode and positive member-scope readback; rely on existing fake-CDP actuation tests and do not perform another real join.
- [Source validation is mistaken for delivered-client validation] → Record binary hashes and explicitly state that the installed AIDCP artifact is unchanged.

## Migration Plan

1. Create isolated control and Edge worktrees from current default branches.
2. Implement and test the bounded diagnostics only.
3. Build the Native binary and capture the exact real `group_join(click=false)` diagnostic on the open target page.
4. Record the captured stage/path/type in this design and `tasks.md`.
5. Implement the observed field-contract repair, effect-intent correction, and narrow header scope repair.
6. Run focused router/client/Rust/fake-CDP tests, Rust formatting/lints, Edge acceptance/full/typecheck, and strict OpenSpec validation.
7. Rebase and fast-forward integrate/push the control and Edge changes. Do not package or install.

Rollback is a normal revert of the two source commits; no data or deployment migration is involved.

## Open Questions

- Resolved: there is no incompatible typed field. The failure is the readiness `join_probe` throwing when `commentEditor` receives the transient null `document.body`; the fixed boundary is the nullable editor root.
- Resolved: the target heading and `已加入` are siblings under a compact header ancestor; a target-owned numeric `/members` link was incorrectly treated as foreign to the vanity URL. The numeric alias is admitted only inside a non-main unique-heading ancestor with no third group identity.
