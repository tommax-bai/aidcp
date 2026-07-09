## Context

The edge desktop client is single-account by construction. `src/electron/main.cjs` holds a single `edgeProcess` and `spawn(process.execPath, [dist/main.js], {env})` (`main.cjs:614`) pins that one child to one AdsPower profile via `AIDCP_ADS_USER_ID`; a single `status` object (`main.cjs:210`) and single `settings.adsProfileId` model the sole account; a single-instance lock (`main.cjs:1103`) refuses a second app instance with an explicit "multi-account not supported" dialog. The core (`src/main.ts`) is a linear one-environment assembly (provider → browser → one CDP session → one `EdgeClient`/WS → one browse session → watchers) with no module-level singletons.

Three seams make multi-environment cheap:

1. **The shell already spawns the core as a child process.** Multi-env = turning the `edgeProcess` scalar into a keyed set of children, one per environment.
2. **The cloud already routes many edges concurrently**, keyed by `edgeId` in a per-connection map (`aidcp-cloud/src/comm/ws-server.ts:127`), with a fully isolated per-connection runtime (private bus + dispatcher + per-account risk). Nothing keys by machine/IP. Shipped in `multi-account-node-support`. One physical client opening N connections with N distinct `edgeId`s looks like N independent edges — **no cloud change** for the standard case.
3. **AdsPower is a natural per-environment isolation unit**: each profile self-manages its port/user-data-dir/fingerprint/IP and returns a dynamic debug port, so N profiles get N distinct CDP ports with zero allocation logic (unlike self-mode's fixed 9222 + SingletonLock).

The N-environment process-fan-out already exists as a CLI: `scripts/launch-multinode.ts` spawns N supervised core children with per-slot frozen env and bounded respawn. The work is to lift that model into the shell — but an adversarial review found the CLI is **not** a copy-paste source (see Decisions).

Constraints (repo invariants): `edgeId` must be unique-per-environment AND stable-across-restart (it is both node identity and cloud downlink routing address); `MUST NOT silently fake success` / never fall back to self; identity is read from login, never launcher-assigned; account risk/quota is single-written per account in the cloud; the client is headful (human login/captcha), so per-environment RAM (~1GB) is unavoidable.

## Goals / Non-Goals

**Goals:**
- Run a handful (2–4, up to a small N) of AdsPower environments concurrently from one desktop client, each fully isolated (own process, browser, CDP, cloud connection, unique stable `edgeId`).
- Reuse the core (`src/main.ts` and the locating/browse/publish/watch stack) verbatim as the per-environment worker — zero risk to the tested single-env path.
- Keep the right-hand companion view identical in content and interaction; add only a fleet rail + per-env routing.
- Crash isolation: one environment's failure (browser crash, identity-halt, captcha wedge, respawn give-up) never affects siblings.
- Honest per-environment surfacing: a failing environment shows its own honest failure, never aggregated away.

**Non-Goals:**
- No in-process multiplexing of environments (rejected below).
- No cloud structural change for the standard one-env=one-account case.
- No console change; no cloud `listEdges()` endpoint / edge-liveness badge in this scope.
- No dense grid / virtualized "dozens of environments" view — physically out of reach at ~1GB each on one machine.
- No shared cross-process AdsPower rate-limit gateway or max-concurrent cap beyond serial stagger (scale-phase).
- No change to publish approval boundary (approval stays in Feishu; the shell shows a read-only projection).

## Decisions

**D1 — Process-per-environment supervisor in the shell (NOT in-process multi-context).**
The Electron main process becomes a supervisor over `Map<envId, EnvHandle>`, one OS child per environment; the core runs verbatim as the worker body. *Alternative considered: an in-process `EnvironmentManager` instantiating N `EnvironmentRunner`s in one Node process.* Rejected: it must rebuild OS fault isolation in software (per-runner async fences on every entry point, banned `process.exit`, uncaught/unhandledRejection handlers, a heap/handle watchdog) around the most safety-critical code in the repo (honest-shutdown / identity-halt / in-flight-publish-fail), to save only ~200MB×(N−1) of Node runtime — the dominant ~1GB/env is the external AdsPower Chrome, identical in both models. A single event-loop stall or one leak would also take down all N. The OS process boundary gives crash isolation for free and directly satisfies the "per-env failure must not abort siblings" invariant. The one advantage the in-process model claimed — a shared 1req/s AdsPower throttle — is recoverable later via a supervisor-owned gateway without sacrificing isolation.

**D2 — `edgeId = ads-<profileId>`, injected and verified; never the hostname fallback.**
`deriveEdgeId` already yields `ads-<profileId>` per AdsPower profile (unique + stable). The supervisor MUST build a per-env frozen env with `AIDCP_ADS_USER_ID` set (and delete `AIDCP_ACCOUNT_ID` so identity is read from login, delete `AIDCP_CDP_PORT`/`AIDCP_CHROME_PROFILE` since AdsPower is dynamic), and MUST refuse to spawn if an environment would reach the `host-<hostname>` fallback (`edge-id.ts:54`) or duplicate an already-running `edgeId`. A duplicate `edgeId` makes the cloud reconnect-evict a sibling — the root cause of 互踢/串号. Enforced at add-time (block double-claim of a profile/account) AND spawn-time.

**D3 — Staggered serial launch (≥1.1s) — new work, not lifted.**
Verified: `launch-multinode.ts:225` does `plans.forEach(spawnNode)` — all children hit AdsPower `browser/start` in the same tick, each thinking it owns its own per-process throttle, collectively breaching the shared ~1req/s local API. The supervisor MUST serialize starts/relogins/stops through a ≥1.1s stagger queue. A full cross-process gateway is deferred; serial stagger covers the 2–4 env case.

**D4 — Non-detached children + graceful stop-all + restart reconciliation.**
`launch-multinode.ts:185` uses `detached:true`, correct for a CLI but wrong for a desktop supervisor: detached children survive an Electron crash as orphaned Chromes, and on restart the supervisor double-spawns the same profile → duplicate `edgeId` → cloud eviction + RAM pileup. Children are non-detached and die with the app after a graceful stop-all on quit; on startup the supervisor reconciles against AdsPower `browser/active` before spawning a profile that may already be running.

**D5 — Namespace image temp dirs per profile/pid (fix a live latent bug).**
`sweepImageTempDirs` (`src/main.ts:79`) deletes every `aidcp-img-*` dir in the shared tmpdir at boot, and uploads are `mkdtemp(tmpdir(),'aidcp-img-')` (`image-uploader.ts:176`) with no per-pid/profile namespace. With multiple children (respawn is the common case), one child's startup sweep wipes a sibling's in-flight upload → corrupt/partial publish — bordering the never-fake-success red line. Namespace temp dirs per envId/pid (or scope the boot sweep to the child's own dir). Same bug exists in `launch-multinode` and is fixed alongside.

**D6 — Per-environment isolation of shell-scoped state.**
`edgeProcess` → `Map<envId, EnvHandle>`; single `status` → keyed status map; single `settings.adsProfileId` → environment list (backward-compatible: a legacy value seeds a one-element list). Each child gets its own `createUiEventStream()` + `mergeStats()` instance (already pure per-stdout factories) so interleaved stdouts stay attributed; browser-parking stdin control and persisted UI state (`ui-state.json`) are keyed by `envId`. The two broadcast choke points (`updateStatus`/`broadcastActivity`) and the preload IPC surface carry an `envId` routing key. The single-instance lock is kept but its dialog rationale is rewritten (one supervisor per machine hosting N environments, real isolation now provided).

**D7 — Fleet UI: collapsible environment rail + unchanged companion view (approved mock).**
Left rail lists environments; each row = one child process = one profile = one account. Default collapsed to a ~56px icon strip where the avatar is quiet (light bg + brand-color glyph) and status is carried by an **avatar status-ring** (green running / amber attention / red error / blue launching / grey offline / dark-yellow stale), attention items pulse, and a pending-attention count badge sits on the expand toggle; expand for names/status/grouping. The right main area is the **existing companion view unchanged in content and interaction**, scoped to the selected environment (its status/activity/publish/quota projections keyed by `envId`). A guided attention flow queues logged-out/captcha/error environments and steps the operator through headful login one window at a time. Vanilla JS, no framework/build — additive around the existing single-env `render`. *Alternatives considered: tabbed multiplexer (hides non-active status — fatal when the job is watching for captchas across N) and dense grid (no persistent per-env log; and out of reach at ~1GB/env).*

**D8 — RAM-ceiling admission + same-account warning.**
Start-all pre-checks projected live-count × ~1GB against machine RAM and holds/warns before over-committing (rather than surfacing as flaky envs). When two environments resolve to the same account, warn (cloud merges risk/quota and routes publish/UI to the earliest edge — the design assumes env = distinct account).

## Risks / Trade-offs

- [Resource cost is linear and unavoidable — ~1GB RAM + a CPU-heavy renderer per headful env; headless is not an option for interaction accounts] → cap the addressable range at a handful; RAM-ceiling admission on start-all; document sizing.
- [AdsPower ~1req/s is a shared per-machine limit with no cross-process budget] → serial staggered spawn/stop now; a supervisor-owned throttled gateway deferred to scale phase and flagged.
- [`edgeId` collision (double-add, hostname fallback, self-mode dir reuse) collapses the fleet toward one live edge] → add-time double-claim guard + spawn-time identity assertion + refuse hostname fallback.
- [Renderer refactor (single global view → keyed roster) could regress the proven single-env UI] → keep the existing `render` as the per-panel primitive and wrap it additively; ship 2-env first.
- [Supervisor (Electron main) is a single point of failure for fleet UI/control] → a running worker's cloud work continues independently of the shell; respawn resumes on restart; non-detached + reconciliation prevents orphans.
- [Settings migration (single → list) could lose the existing selection or double-launch] → backward-compat load seeds a one-element list via the existing DEFAULT_SETTINGS spread; test the legacy path.
- [Honest per-env failure could be aggregated away in the keyed-status refactor] → each environment surfaces its own failure in its own row; never collapse a failing env into a fleet summary.

## Migration Plan

Phased; each phase is independently shippable.

- **Phase 0 (de-risk, zero new code):** run 2 AdsPower profiles via the existing `scripts/launch-multinode.ts` CLI on the real operator machine. Validate RAM headroom, real AdsPower ~1req/s behavior under simultaneous start, distinct headful windows, and the cloud holding two isolated runtimes — and deliberately reproduce the temp-dir crossfire. Quantifies the sharp edges before touching the shell.
- **Phase 1 (MVP — edge shell only, 2–4 envs):** `Map<envId,EnvHandle>`; settings single→list with back-compat; per-child `createUiEventStream()`+`mergeStats()`; `envId` through the two broadcast choke points + IPC; additive fleet rail + per-env routing of the unchanged companion view; serial staggered spawn; keep the single-instance lock (rewrite dialog); reuse `respawn-policy.ts`; namespace temp dirs (D5); non-detached + graceful stop-all (D4). Zero cloud/console change.
- **Phase 2 (headful payoff + robustness):** guided attention/login flow; RAM-ceiling pre-check; terminal give-up state after bounded respawn; restart reconciliation via `browser/active`; add-time duplicate profile/account/edgeId guards; same-account warning.
- **Phase 3 (scale, only if demanded — out of this change's committed scope):** extract shared `src/supervise` spawn loop for CLI/shell parity; max-concurrent cap; supervisor-owned throttled AdsPower gateway (children attach to a supplied debug port instead of launching); cloud `listEdges()` endpoint + wire the console's already-built-but-dead edge-liveness badge.

Rollback: the change is edge-shell-local and additive; a legacy single-profile install still loads (one-element list). Reverting the shell to the single `edgeProcess` path leaves the core and cloud untouched.

## Open Questions

- Persist the rail collapse/expand state and the last-selected environment across restarts (settings) — assumed yes; confirm placement (user settings vs UI state file).
- Should start-all auto-stagger order prioritize environments flagged for attention or previously-running, or preserve roster order? Default: roster order.
- Auto-expand-on-attention for the collapsed rail (peek open when an environment needs attention) — proposed as a Phase 2 nicety; confirm whether in scope.
- Exact RAM-ceiling default and per-environment estimate (OPERATOR.md states ~1GB) — confirm on the target operator machine during Phase 0.
