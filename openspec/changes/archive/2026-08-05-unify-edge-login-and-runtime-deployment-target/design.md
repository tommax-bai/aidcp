## Context

Electron currently resolves two Cloud transports through different precedence chains. `resolveCloudUrl()` prefers the saved Cloud selector and can rebind a running core, while `resolveClientAuthBase()` prefers explicit and baked absolute customer-auth URLs. An OL package can therefore authenticate, refresh tokens, load ownership, and write customer data through OL while its automation core is rebound to DEV. The saved session and the only durable local Cloud-mutation cursor are also target-less.

Settings are loaded before startup authentication and the login renderer already has a main-process IPC bridge, so target selection can happen before credentials are submitted without a Cloud protocol change. DEV and OL endpoint pairs already exist in one Edge mapping.

## Goals / Non-Goals

**Goals:**

- Make one main-process-owned deployment target the authority for every official Cloud endpoint used by a desktop session.
- Choose that target on the login gate and require a new target-scoped login before any target transition becomes active.
- Prevent tokens, credential prefill, ownership projections, pending Cloud mutations, or automation receipts from crossing targets.
- Remove absolute customer-auth URL baking while keeping existing signed-package entry points usable.
- Preserve honest distinction between selected/authenticated target and confirmed automation connection.

**Non-Goals:**

- Changing Cloud protocols, Cloud deployment topology, account credentials, or DEV/OL databases.
- Hot-switching a live authenticated session between targets.
- Exposing arbitrary URL fields to ordinary customers.
- Packaging, signing, installing, deploying, or performing real-account actions in this change session.

## Decisions

### D1 — Persist one target key; derive an endpoint tuple

Persist `deploymentTarget: 'dev' | 'ol'`. A main-process target catalog resolves `{ customerAuthBaseUrl, automationWebSocketUrl }`. Official request paths never accept a renderer-provided URL and never resolve the two transports independently.

The existing `cloudEnvKey`, `cloudUrlCustom`, and `clientAuthUrl` settings become legacy migration inputs, not ongoing authorities. Standalone core development can still use its existing command-line URL, but Electron official-target operation always injects the catalog WebSocket URL. A paired custom target may exist only behind an explicit developer gate and is labelled `custom`; it cannot be selected from the customer login page.

Alternative rejected: only lower the baked URL precedence. That would leave tokens and durable local work target-less and preserve unsafe in-session partial switching.

### D2 — Target selection is part of login

The login page offers DEV and OL before submitting credentials. The login IPC carries only the enum target plus credentials. Electron validates and durably saves the target, resolves the tuple, then calls `/login`. A write failure blocks login so the running session cannot disagree with restart behavior.

Changing target while authenticated is an explicit transition: stop/revoke automation authority, clear the old target session and projections, close the main window, and return to the login gate. The new target is not active until login and ownership refresh succeed. The old `cloud:restartAll` partial-transport action is removed from customer UI.

Alternative rejected: hot-rebind WebSocket and retain login. A token, visible roster, and control binding issued by one target cannot authorize another target.

### D3 — Bind local authority and replay state to target

Session and encrypted credential records carry `deploymentTarget`; target-less or mismatched records are not restored. Credentials are cleared on target change rather than copied between targets. In-memory visible environment IDs, platform/control projections, and customer-scoped exclusions are cleared before the next login.

Pending Cloud mutations carry their originating target and replay only when it equals the authenticated target. A legacy record is migrated only when its old data endpoint maps unambiguously to DEV or OL; otherwise it remains non-replayable and is reported rather than guessed.

Physical AdsPower roster configuration remains local and is not deleted. It is filtered again by the newly authenticated target's ownership response.

### D4 — Package metadata can preselect, never route by URL

`aidcpCloudDefaultEnv` may remain as a non-secret first-run/preselection default so existing DEV and OL package entry points retain expected UX. `aidcpClientAuthUrl` and related build inputs/checks are removed. Runtime ignores legacy baked absolute URL metadata except for bounded migration classification; it is never an active route authority.

If a future universal package is desired, it can omit the default key and use OL as the product default without changing endpoint resolution.

### D5 — Status labels name their evidence

Login and main-window target labels describe the selected/authenticated deployment target. An automation activity names DEV/OL only after the core confirms connection; waiting-slot copy says `自动化通道已连接 <target>，等待浏览器槽位`. No label promotes a saved target to an actual connection receipt.

## Risks / Trade-offs

- **[Upgrade forces a login]** → Target-less session and credential records are deliberately rejected once; the login page preserves a clear selected target and explains the need to log in again.
- **[Target switch interrupts active work]** → The switch is unavailable as a hot action; it stops engines through the existing authenticated-session invalidation path before returning to login.
- **[Legacy pending mutation target is ambiguous]** → Never replay an ambiguous entry. Keep it visible with a stable reason and require target-specific recovery rather than guessing.
- **[Build scripts or docs still expect an auth URL]** → Remove the input and mounted-ASAR assertion together, then test that official packages contain a valid default target and no active absolute auth override.
- **[OL is selected accidentally]** → Default to DEV when no persisted/package target exists, require explicit OL selection, and show the selected target on the login button and authenticated header.

## Migration Plan

1. Add target normalization and compatibility reads. Prefer persisted `deploymentTarget`, then a persisted official legacy key, then the baked default key, otherwise the development default.
2. Introduce target-scoped session/prefill/mutation shapes. Reject target-less credentials and sessions; classify only unambiguous legacy mutation endpoints.
3. Move target choice to login and replace authenticated selector/rebind controls with a logout-to-switch action.
4. Remove active baked/explicit absolute URL precedence and package/workflow injection, then update release verification and docs.
5. Run focused Electron tests, full Edge tests, typecheck, and strict OpenSpec validation. Do not package or deploy.

Rollback re-enables the previous resolver and UI only before a new target-scoped session is relied on. Target fields are additive and can be ignored by an older build, but any rollback must sign the user out to avoid interpreting a token under the wrong resolver.

## Open Questions

None. Product decisions are fixed to login-time DEV/OL selection, paired official endpoints, logout-to-switch, and no customer-visible custom URL entry.
