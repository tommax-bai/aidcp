## Context

Cloud currently expresses both ordinary author-profile browsing and startup-time self-identity refresh through `profile.open`. The optional `direct` field changes the command from “open the current content author” into “navigate by account id”, and the receiving platform adapter decides what `direct` means. Cloud's platform registry already states that Facebook does not support author-profile visits, but `NicknameEnricher` bypasses that capability and emits the shared command directly.

Before Native cutover, the Facebook JavaScript executor special-cased `profile.open{direct:true}` into an in-place identity read. The Native Facebook adapter instead implemented the command's literal profile-navigation shape and visited `profile.php?id=<self>`. The session platform check passed because Facebook broadly declared `profile_open` support. The current adapter manifest contains only an adapter version, so neither Edge nor Cloud can prove exact semantic command coverage.

The architectural constraints remain: Cloud owns platform selection and orchestration; Edge/Native owns typed atomic page execution and verification; commands cannot contain selectors, JavaScript, raw CDP, or caller-defined recovery programs; Native-only platforms have no JavaScript fallback.

## Goals / Non-Goals

**Goals:**

- Give each page command one cross-platform side-effect contract.
- Make every platform explicitly choose its self-identity capture strategy.
- Keep self-identity observations out of the social author-profile event path.
- Reject unsupported platform-command combinations before browser/CDP effects.
- Make Cloud/Edge version skew safe without reviving `profile.open{direct}`.
- Force a future `PlatformId` to declare its strategy and exact executor support.

**Non-Goals:**

- Build a generic workflow DSL or allow Cloud to send navigation-policy knobs.
- Add Facebook author-profile browsing.
- Change startup capture timing, nickname persistence rules, risk, pacing, publishing, or browser-provider behavior.
- Package, sign, release, or perform real-account acceptance in this source change.

## Decisions

### 1. Separate business intent, platform strategy, and page command

The Cloud domain event becomes self-identity refresh intent rather than a profile-navigation intent. The Cloud platform registry maps that intent to one exhaustive `IdentityCaptureStrategy`:

```ts
type IdentityCaptureStrategy =
  | { supported: true; command: 'identity.read_current'; restore: 'none' }
  | { supported: true; command: 'identity.read_self_profile'; restore: 'feed' }
  | { supported: false; reason: string };
```

Xiaohongshu selects `identity.read_self_profile`; Facebook selects `identity.read_current`; WeChat Channels declares unsupported because its identity comes from the interaction-auth runtime. There is no missing-platform or unknown-platform default.

This strategy lives with the existing Cloud `PlatformRegistryEntry`, which already owns platform orchestration capability truth. A separate switch in `NicknameEnricher` or `RoleDispatcher` would create a second source of truth.

Alternative considered: keep `profile.open` and branch on `accountPlatform`. This repairs the observed line but preserves a command whose page effect changes by platform, so a later adapter can repeat the same regression.

### 2. Use fixed-effect commands, not platform-namespaced commands or mode flags

The runtime commands are:

- `identity.bootstrap`: Edge-to-Native startup-only operation. It MAY guide a blank/non-platform tab to the platform home page but MUST NOT navigate to a profile.
- `identity.read_current`: Cloud-to-Edge runtime operation. It MUST NOT call `Page.navigate`, reload, history navigation, or open a profile.
- `identity.read_self_profile`: Cloud-to-Edge runtime operation. It MAY navigate only to the canonical self-profile derived from the session-bound account. It accepts no caller-supplied account/author id.
- `profile.open`: ordinary author-profile browsing only. Its `direct` field is removed and it is gated by the platform's `profile_visit` capability.

The Native snake-case command kinds mirror these semantics. A platform name is not embedded in the command because the Native session is already platform-bound; fixed effects plus an exact support matrix provide isolation without duplicating schemas for every platform.

Alternative considered: `facebook.identity.read` and `xiaohongshu.profile.open`. Namespacing is explicit but makes identical semantic operations separate protocol types, spreads platform switches through callers, and grows linearly with every new platform.

Alternative considered: `identity.capture{mode}`. A mode flag recreates the current `direct` problem by making the caller responsible for selecting a safety-sensitive page effect.

### 3. Return a correlated self-identity observation

Both runtime identity commands return `identity.observed`, containing:

- the Cloud-generated `captureId`, echoed unchanged;
- the session-bound `accountId`;
- optional verified `nickname`;
- `source: current_page | self_profile`;
- `pageEffect: none | navigated_self_profile`.

`NicknameEnricher` accepts an observation only when `captureId` and `accountId` match the active capture. Empty nicknames remain honest no-write results. `profile.detail` remains reserved for ordinary author-profile browsing and cannot complete a self-identity capture.

Cloud sends Feed restoration only after a matching self-profile observation (or an effect-aware recovery path for that command). A current-page observation has `pageEffect=none` and emits no `back`, `scroll`, or refresh command.

Alternative considered: continue using `profile.detail` with `authorId===accountId`. That identity check is safe for persistence but leaves an unrelated social event able to complete the startup capture and cannot correlate late results to the exact capture attempt.

### 4. Negotiate exact command support and enforce it twice

Each Edge browser platform driver declares the semantic page-command capabilities it can route. The Native manifest declares the exact command kinds implemented by each adapter, not only `adapterVersion`. Edge advertises a Cloud capability only when the driver declaration and Native manifest agree.

Cloud sends a runtime identity command only when:

1. the account platform selects that command in the registry; and
2. the connected Edge advertises the matching versioned semantic capability.

Native then independently checks the session platform's command allowlist before CDP dispatch. Facebook does not list `identity_read_self_profile` or ordinary `profile_open`; Xiaohongshu does not silently inherit Facebook current-page semantics.

This is a safety gate, not a fallback. A new Cloud connected to an old Edge skips the optional second capture with an observable `identity_capture_command_unavailable`; it never sends legacy `profile.open{direct}`. A new Edge receiving the legacy `direct` field rejects it before Native dispatch instead of dropping the field.

### 5. Keep the implementation exhaustive but narrow

This change adds only the self-identity strategy to the platform registry. It does not introduce a universal command-plan table for every feature. The reusable rule is: when the same business intent requires different observable page effects, introduce separate fixed-effect commands and an exhaustive typed platform strategy at the real consumer.

Cross-repo contract tests cover:

- protocol type parity and message routing;
- every `PlatformId` has an identity-capture strategy;
- Cloud sends only the selected negotiated command;
- Facebook current-page identity produces zero navigation calls;
- Facebook rejects self-profile and ordinary profile commands before CDP;
- Xiaohongshu self-profile identity uses only the session-bound account;
- current-page completion sends no Feed restore;
- self-profile completion restores Feed;
- legacy `profile.open{direct}` is rejected, never reinterpreted.

## Risks / Trade-offs

- [Adding protocol messages creates Cloud/Edge version skew] → Negotiate versioned semantic capabilities; new Cloud skips optional secondary capture on old Edge and never falls back to the ambiguous command.
- [Xiaohongshu self-profile capture currently depends on `profile.detail`] → Add the dedicated observation output before switching Cloud, then remove only the self-capture use of `profile.detail`.
- [Manifest command lists can drift from Rust support code] → Generate or validate the manifest list against the same Native support matrix and fail package verification on mismatch.
- [A broad rename of NicknameEnricher could enlarge the change] → Keep the class/file name if necessary; change its event and command contract first. Rename only when tests prove it is mechanical.
- [Removing `direct` may expose old senders] → Reject the field explicitly before CDP and surface a version/capability error; do not reinterpret it as ordinary author browsing.

## Migration Plan

1. Add protocol types, fixed-effect Native commands, dedicated observation output, adapter command declarations, and negative tests without switching Cloud.
2. Add Edge capability advertisement only when the Native manifest proves the matching command.
3. Add the exhaustive Cloud strategy and result handling; switch Facebook to current-page read and Xiaohongshu to self-profile read.
4. Stop emitting `self.profile.capture`, stop consuming `profile.detail` for self capture, and remove `direct` from the active protocol and Native params.
5. Run focused acceptance, full tests, typecheck, Rust tests/Clippy, Native verification, and strict OpenSpec validation.
6. Integrate Edge before Cloud so a deployed Cloud can negotiate the new commands. Deploy Cloud to DEV only from its clean default checkout after both repos land; an installed Edge package remains a separate release gate.

Rollback before desktop release is a source revert of both default branches. After release, rollback uses the previous verified installer plus the matching Cloud revision. At no point does rollback enable a JavaScript fallback.

## Open Questions

None. The observed Facebook navigation and the existing platform registry provide enough evidence to choose the fixed-effect command model.
