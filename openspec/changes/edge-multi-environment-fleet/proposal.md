## Why

Today the edge desktop client is single-account by construction: the Electron shell spawns exactly one core child process (`src/electron/main.cjs` `edgeProcess`), pins it to one AdsPower profile via one `AIDCP_ADS_USER_ID`, holds one `settings`/`status` object, and a single-instance lock refuses a second app instance. An operator running N accounts must run N machines or juggle the CLI `scripts/launch-multinode.ts` with no UI. Operators need to run multiple environments (accounts) concurrently from one desktop client, monitor them at a glance, and reach each browser for headful login/captcha without losing track.

The path is cheap because the seams already exist: the shell already spawns the core as a **child process**; the cloud already routes many edges concurrently keyed by `edgeId` (shipped in `multi-account-node-support`); each AdsPower profile self-manages its own port/fingerprint/user-data-dir/IP and yields a dynamic debug port; and the core (`src/main.ts`) is already a self-contained one-environment unit. So multi-environment is primarily an **edge-shell** change: promote the single child into a keyed set of supervised children, one per environment, and grow the single-account UI into a fleet view — with the process boundary giving crash isolation for free.

## What Changes

- Promote the Electron shell from one `edgeProcess` scalar to a **per-environment supervised child-process registry** (`Map<envId, EnvHandle>`), one OS process per environment. Each child runs the existing single-env core verbatim as an isolated worker, pinned to one AdsPower profile with a **unique, stable `edgeId` (`ads-<profileId>`)**; the shell owns spawn/stop/pause/resume/respawn per environment. **BREAKING** (shell-internal): the single-instance lock is kept but re-scoped ("one supervisor per machine hosting N environments", no longer "one account per app").
- **Staggered serial launch** (≥1.1s spacing) for start/relogin/stop so concurrent AdsPower `browser/start|stop|active` calls never breach the shared ~1req/s local-API limit — this does NOT exist in `launch-multinode` today.
- **Non-detached children + graceful stop-all on quit + restart-time reconciliation** (`browser/active`) to prevent orphaned Chrome processes and double-spawn-on-restart (which would collide `edgeId` and evict a sibling in the cloud).
- **Per-environment isolation of shell-scoped state**: each child gets its own activity/stats parser (`createUiEventStream`/`mergeStats`), status projection, browser-parking control, and persisted UI state, keyed by `envId`; broadcast + IPC channels carry an `envId` routing key.
- **Image temp-dir crossfire fix**: namespace `aidcp-img-*` temp dirs per profile/pid (or scope the boot sweep to the child's own dir) so one child's startup cleanup cannot delete a sibling's in-flight upload — a latent `MUST NOT silent-fake-success` hazard present in `launch-multinode` today.
- **Identity safety**: spawn MUST inject a distinct stable per-env identity and refuse to launch if the environment would reach the `host-<hostname>` fallback or duplicate an already-running `edgeId`; the AdsPower env picker becomes **multi-select** and blocks double-claiming the same profile/account.
- **RAM-ceiling admission** on start-all (≈1GB per headful environment) with an honest hold/warn instead of silent thrash.
- **Fleet console UI**: a collapsible left **environment rail** (default collapsed to an icon strip; status carried by an avatar status-ring, attention items pulse, a pending-attention count badge; expand for the full list) plus an **attention/guided-login** flow for headful login/captcha across N windows. The right main area is the **existing companion view, unchanged in content and interaction**, simply scoped to the selected environment.
- **Same-account guard**: surface a warning when two environments resolve to the same account (the cloud merges risk/quota budget and routes publish/UI to the earliest edge).
- **No cloud change** for the standard case (one env = one distinct `edgeId` + one distinct account). Console `listEdges()`/edge-liveness badge is explicitly deferred to the scale phase.

## Capabilities

### New Capabilities

- `edge-multi-environment-supervisor`: The desktop shell supervises N per-environment child processes — per-env unique/stable identity and duplicate/fallback refusal, staggered serial AdsPower lifecycle, non-detached lifecycle with graceful stop-all and restart reconciliation, per-env respawn/give-up, per-env isolated temp dirs and shell state, RAM-ceiling admission, and same-account warning.
- `edge-fleet-console`: The desktop UI presents a fleet — a collapsible environment rail with status-ring signaling and attention-first ordering, a multi-select add-environment roster, a guided headful login/captcha flow across environments, and routing of the (unchanged) companion view to the selected environment.

### Modified Capabilities

- `edge-companion-ui`: The companion view's status/activity/publish/quota projections become keyed per environment and render the currently-selected environment; the view's own content and interactions are unchanged (no per-env approve buttons; publish approval stays in Feishu).
- `adspower-desktop-env-picker`: The AdsPower environment picker becomes multi-select — selecting a roster of environments to run concurrently (each a persisted, uniquely-claimed member) instead of choosing one profile to launch.

## Impact

- Affected repos: `aidcp-edge` (primary — Electron shell + renderer + a small shared supervisor module; the core `src/main.ts` and the locating/browse/publish/watch stack are reused verbatim). No `aidcp-cloud` structural change. No `aidcp-console` change in this scope.
- Edge areas: `src/electron/main.cjs` (process registry, staggered spawn, non-detached lifecycle, reconciliation, envId-keyed broadcast/IPC/status/settings), `src/electron/preload.cjs` (per-env IPC), `src/electron/renderer/` (fleet rail + per-env routing, additive around the existing `render`), `src/electron/ads-*` (multi-select picker), `src/main.ts` (temp-dir namespacing only), a reusable supervisor module shared with `scripts/launch-multinode.ts` (reusing `src/supervise/respawn-policy.ts`).
- Cloud dependency (unchanged, relied upon): edges are keyed by `edgeId` and routed independently (`multi-account-node-support`); risk/quota is single-written per account. The only hard invariant the edge must satisfy is a distinct, stable `edgeId` per environment.
- Operational impact: resource-bound to a handful of concurrent headful environments per machine (~1GB RAM each); a RAM-ceiling pre-check gates start-all. Settings schema migrates single `adsProfileId` → environment list with backward-compatible load.
- Out of scope (scale phase / future change): shared cross-process AdsPower rate-limit gateway, max-concurrent cap beyond serial stagger, `src/supervise` full extraction for CLI/shell parity, cloud `listEdges()` endpoint + console edge-liveness badge, and the dense grid/virtualized view for dozens of environments (physically out of reach on one machine).
