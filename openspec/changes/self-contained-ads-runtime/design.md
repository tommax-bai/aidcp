# Design — Self-Contained Bundled AdsPower CLI Runtime

> Scope: aidcp-edge, macOS this round. Decision: **hard switch** (always the bundled runtime, no external-mode fallback). Produced from a 4-lens design + adversarial review; the review's six revisions and one empirical pin are folded in below. Line numbers in the source drift; **anchor by function name**, not line.

## Constraints (authoritative)

- Red line: **never silently fake success** — every failure returns honest `{ok:false,error}`; no bare `fetch failed` reaching the user.
- Never touch同机 isales. Do not regress the shipped packaged-spawn cwd/asar (ENOTDIR) fix. The baked key lives in a **data file**, never hardcoded in a `.cjs`.
- Empirically verified on the dev machine (treat as given):
  - `adspower-browser@2.1.0` ships **native** `sqlite/{arm64,mac,x64,ia32,linux}/node_sqlite3.node`; the service (`cwd/lib/main.min.js`) does `require("./node_sqlite3.node")`. → **native module present** → must live outside asar.
  - The LocalAPI does **not** key-check per request (`/api/v1/group/list` returns data with no auth header; a wrong key only hit the 1 req/s throttle). The key authenticates `ads start` against AdsPower cloud only. → injecting the baked key into the core is harmless even when adopting a daemon started under a different key.
  - The CLI resolves its writable `BASE_DIR` from its **entry path** (`__dirname`-relative `cwd/`), not `process.cwd()` → `runCli` passing no cwd is safe (inherits a valid parent cwd), and staging a writable copy works.
  - A fresh (unwarmed) install tree ≈ 31 MB; the dev tree is 57 MB only because its `cwd/` is runtime-warmed.

## 1. Overview

1. **Ships in the installer (~+31 MB):** a read-only self-contained nested copy of `adspower-browser@2.1.0` at `Contents/Resources/adspower-browser`, plus `Contents/Resources/ads-runtime.json` (baked shared key).
2. **Downloads once, on first browser launch only (~735 MB):** the SunBrowser kernel into `~/.adspowerCli`. Never in the installer.
3. **Cold operator machine, zero input:** launch → first-run stages the template to `userData/ads-runtime/` (writable) → service-ensure starts our CLI (`ads start -k <baked key>`), binds a port, we **adopt whatever port `status` reports** → (first launch only) kernel-ensure downloads with a determinate bar → fingerprint browser opens.
4. **Create-env on a cold machine:** service-ensure only (seconds, no kernel), then `group/create` against the actually-bound port.
5. Honest failure throughout: missing runtime / missing key / unreachable service / seat-ceiling / kernel-download-failure each surface a specific `{ok,error}`.

## 2. Packaging

### 2.1 Dependency — devDependency (not production)
Add `adspower-browser@2.1.0` to **devDependencies** in `aidcp-edge/package.json`. electron-builder packs only production `dependencies` into `app.asar`, so a devDependency is never asar-packed (no `files` negation needed), while `electron .` still resolves `node_modules/adspower-browser/cli/index.js` in dev. Run `npm install --package-lock-only` after (CI `npm ci` fails on lockfile drift).

### 2.2 Reproducible nested staging tree (new build step)
`scripts/stage-ads-runtime.mjs`:
1. clean `build/ads-prefix`, `build/ads-runtime`.
2. with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`, `PLAYWRIGHT_BROWSERS_PATH=0`, `npm_config_ignore_scripts=true`: `npm install --global --prefix build/ads-prefix adspower-browser@2.1.0` (fresh, **unwarmed** `cwd/`).
3. copy the package dir → `build/ads-runtime/adspower-browser`. POSIX source `build/ads-prefix/lib/node_modules/adspower-browser`; win32 `build/ads-prefix/node_modules/adspower-browser` (the one Windows-specific line — the seam).

Ship the **full all-arch `sqlite/`** (~8 MB; the CLI picks arch at runtime from `process.arch`, correct on both arm64/x64 dmg). Do **not** pre-run `ads start` at build time (keeps a network fetch out of the build; userData staging handles first-run `cwd` writes). playwright-core is used by the CLI only as a CDP client — its browser download is suppressed and not needed (SunBrowser is the kernel).

`scripts/verify-ads-runtime-staged.mjs` (reuse the asar-extract probe): assert on the built `.app` that `adspower-browser` is **absent** from `app.asar` and **present** at `Contents/Resources/adspower-browser/{cli,cwd,sqlite,node_modules}`.

### 2.3 electron-builder config — top-level `extraResources` (shared mac+win)
```
"extraResources": [
  { "from": "build/ads-runtime/adspower-browser", "to": "adspower-browser" },
  { "from": "resources/ads-runtime.json",          "to": "ads-runtime.json" }
]
```
`to` is relative to `Contents/Resources`. Wire staging into the build scripts before electron-builder: new `build:ads-runtime` script, prepended in `electron:build` / `electron:build:mac` / `electron:build:win`.

### 2.4 resolveCliEntry parity (candidate order after this change)
`resolveCliEntry({resourcesPath, appRoot, userDataPath})`:
0. `userDataPath/ads-runtime/adspower-browser/cli/index.js` — **NEW**, staged writable copy (packaged runtime after first-run staging).
1. `resourcesPath/adspower-browser/cli/index.js` — packaged template (pre-staging fallback).
2. `resourcesPath/app.asar.unpacked/node_modules/adspower-browser/cli/index.js` — unused (we reject asarUnpack); keep for safety.
3. `appRoot/node_modules/adspower-browser/cli/index.js` — dev hit (devDependency).
4. `require.resolve('adspower-browser')` — dev fallback.

### 2.5 Signing
Native `.node` present, but the app is **unsigned** (`mac.identity=null`) → hardened-runtime library validation is not enforced → native `.node` loads for internal distribution. Real-machine gate: verify on a **quarantined/translocated** build (from DMG/Downloads), not a locally-built `.app`. Signing + `disable-library-validation` entitlement is a future seam, not built now.

### 2.6 Windows local development seam
Windows installer packaging remains deferred, but local development SHALL use the same patched runtime tree as packaging. `stage-ads-runtime.mjs` invokes `npm-cli.js` through the current build-time Node executable instead of spawning `npm.cmd` directly, which avoids `spawnSync npm.cmd EINVAL` on Node 24. `resolveCliEntry` prefers `build/ads-runtime/adspower-browser/cli/index.js` before a raw `node_modules` package so Electron always runs the compatibility-patched tree. Runtime execution remains unchanged: Electron launches the CLI through its own `process.execPath` with `ELECTRON_RUN_AS_NODE=1`.

## 3. Runtime lifecycle (hard-switch)

Split today's welded `ensureAdsRuntimeAndKernel` into **two independent single-flights**; remove the external-mode branch.

### 3.1 `ensureAdsServiceOnce()` — service ensure
State: `unresolved → staging → resolving-cli → starting-runtime → ready(base) | failed`.
1. Reset the module base inside the singleton runner (one writer).
2. **Stage template → userData (NEW).** `stageAdsRuntimeIfNeeded()` idempotently copies `Contents/Resources/adspower-browser` → `userData/ads-runtime/adspower-browser` when absent or **stale**. **Staleness marker (critique gap b1):** write a stamp file next to the staged tree recording `{ appVersion, adspowerBrowserVersion }`; on launch, mismatch → wipe + re-stage (prevents an app upgrade's patched runtime being shadowed by the old staged copy). Copy failure → honest `{ok:false,error:'指纹浏览器运行时暂存失败'}`. Dev builds skip staging (candidates 3/4 resolve).
3. Resolve CLI via `resolveCliEntry`. Null → honest hard-stop `{ok:false,error:'未随包指纹浏览器运行时'}` + `surfaceFailure`, MUST NOT start core. **Remove** the old external-probe short-circuit (`return {mode:'external'}`) and the `mode:'none'` "proceed anyway".
4. `adsRuntime.ensureRuntime({cliEntry, execPath:process.execPath, apiKey:resolveAdsApiKey()})`: run `ads status`; **already running → reuse** (`alreadyRunning`, the no-double-start guarantee); else `ads start -k <key>` + poll `status`.
5. **Authoritative base** = the port `ads status` actually reported (`parseRuntimePort`, never hardcoded 50325). Rename `embeddedAdsApiBase` → `adsServiceBase`.
6. Failure → honest `{ok,error}` + `surfaceFailure`, MUST NOT start core.

**Foreign-50325 (closes P0-B honestly):** no HTTP-probe-and-adopt. `ads status` reads shared `~/.adspowerCli` state: our daemon / a compatible global CLI → adopt its reported port; a foreign desktop AdsPower squatting 50325 → our `ads start` takes a fallback port (e.g. 50326), `parseRuntimePort` reads it back → we run **our own keyed service**, never ride the foreign one. Empirical pin: since the LocalAPI is not per-request key-checked, adopting a differently-keyed daemon (dev machine) is safe.

### 3.2 One base authority (P0-A — load-bearing)
Today `adsServiceBase` feeds only the core spawn env; `resolveAdsOpts` **ignores it**, so every main-process create/status/proxy/delete/reconcile hits 50325 regardless of the bound port. **Fix** in `resolveAdsOpts`:
```
const apiBase = (o.apiBase && String(o.apiBase).trim())  // form value first
             || adsServiceBase                            // NEW: managed/adopted base wins
             || settings.adsApiBase
             || undefined;                                // CLI default only if nothing resolved
```
Every write path awaits `ensureAdsServiceOnce()` first (§3.4), so `adsServiceBase` is populated by then. `buildAdsProviderEnv` already reads it — unify to the renamed var. One base for the main process + all N core children.

### 3.3 Two single-flights (fleet dedup)
- `ensureAdsServiceOnce()` — dedups concurrent service starts; **cleared on settle** so a later call re-probes freshness (the daemon can die between env starts). **Read-IPC fast path (critique gap b4):** once `adsServiceBase` is set, `ads:status`/`ads:listProfiles` read it **directly** and only re-ensure on an actual `fetch failed` — do NOT re-run `ads status` as a subprocess on every settings-panel poll.
- `ensureKernelOnce()` — dedups concurrent kernel downloads; `kernelDownloaded` short-circuits when present → N concurrent env starts trigger at most one download.

### 3.4 Wiring points (by function name)
- `startAdsPowerFlow`: replace the single ensure with `await ensureAdsServiceOnce()` **then** `await ensureKernelOnce()`, both before the cancel-gate + `startEdge`. Bail honestly on either failure.
- `ads:createEnv`: **add `await ensureAdsServiceOnce()` at the top**, before `resolveAdsOpts`. Service only, **no kernel**. On `!ok` return `{ok:false,error:'指纹浏览器运行时未就绪：<cause>',retryable:true}`.
- `ads:updateEnvProxy`, `ads:deleteEnv`: add `await ensureAdsServiceOnce()` before `resolveAdsOpts`. Metadata, no kernel.
- `reconcileRunningProfiles` (at whenReady): run after service-ensure so it targets the managed base; stays best-effort.
- `ads:status` / `ads:listProfiles` read IPC: use the cached-base fast path (§3.3); ensure only on cold/fetch-failed; a failure returns an honest object, never crashes the panel.

### 3.5 Start / stop ownership
- **START: eager service, lazy kernel.** After `createWindow` at whenReady, a **non-blocking** `void ensureAdsServiceOnce()` warm-up (idempotent; makes reconcile + panel + first action instant; failures swallowed until a real action needs it). Kernel stays fully lazy (first launch only). whenReady still does not auto-start operating.
- **STOP: do NOT `ads stop`.** `gracefulStopAllAndQuit` SIGTERMs core children (each does honest `browser/stop`), waits bounded, quits — and MUST NOT stop the CLI daemon (machine-shared singleton; killing it yanks all browsers, drops locks, races per-child stop, fights other CLI instances). Leaving it idle makes the next launch instant (status-reuse + `reconcileRunningProfiles` adopts already-running profiles). `openAdsClient` ('open -a AdsPower Global') becomes dead code under hard switch → **delete it**.

### 3.6 Kernel gating
Metadata (create-env/proxy/delete) → service only, never kernel. First browser launch → kernel via `ensureKernelOnce` after service-ensure, before `startEdge`, driven by `adsFingerprint.DEFAULT_KERNEL` with the existing determinate progress UI. One kernel serves all profiles.

#### 3.6.1 Installed-kernel proof before cloud catalogue

The cloud `get-kernel-list` endpoint is download discovery, not a prerequisite for executing a kernel already present on disk. Before calling it, `kernelDownloaded` SHALL check the pinned Chrome kernel's platform-specific executable under `~/.adspowerCli/chrome_<version>` and accept it only when the sentinel is a non-empty regular file and executable on POSIX. Unsupported kernel types or invalid version path components do not use this shortcut.

If the local proof succeeds, launch proceeds without any catalogue request; a later `browser-profile/start` failure remains the honest runtime postcondition. If the proof fails, the existing catalogue/download flow remains authoritative. Its terminal error SHALL distinguish throttling, timeout, network/TLS transport failure, an empty valid list, malformed output, and a non-zero CLI exit without exposing raw vendor output or credentials.

This intentionally permits an already-installed pinned kernel to keep working if the catalogue is temporarily unreachable or later delists that version. A missing kernel still fails closed when it cannot be discovered/downloaded.

### 3.7 V2 browser lifecycle and lost-registry reconciliation

The bundled `adspower-browser@2.1.0` CLI exposes browser lifecycle through the V2 profile contract. Both lifecycle owners SHALL use the same contract against the authoritative `adsServiceBase`:

- core provider: `GET /api/v2/browser-profile/active?profile_id=...`, `POST /api/v2/browser-profile/start`, and `POST /api/v2/browser-profile/stop`;
- Electron inspection/reconciliation: the same per-profile `active` and `start` calls, with reconciliation bounded to the known environment roster rather than the legacy global `/api/v1/browser/local-active` list.

The V2 registry is authoritative for normally managed sessions, but the daemon can restart while a SunBrowser child remains alive. In that state V2 truthfully reports `Inactive` even though CDP is still serving. Before starting a duplicate, both paths inspect only the profile-scoped cache directories under `~/.adspowerCli/source/cache/<profile_id>_*`, read `DevToolsActivePort`, and accept an orphan candidate only when all of these checks pass:

1. the port is a valid loopback TCP port and the second line is a `/devtools/browser/<opaque-id>` path;
2. `http://127.0.0.1:<port>/json/version` is reachable within a short timeout;
3. its `webSocketDebuggerUrl` is loopback, uses the same port, and has the exact same browser path.

Candidate discovery is bounded and profile-prefixed; it MUST NOT scan unrelated user directories or trust a port alone. A validated candidate is adopted in place, logged as lost-registry recovery, and no V2 `start` is sent. If no candidate validates, launch proceeds through V2 `start`. Stop always uses V2 `stop` and retains the existing CDP-dark confirmation; an unconfirmed close remains an honest failure.

## 4. Key config + first-run UX

### 4.1 Baked rotatable key
Ship `resources/ads-runtime.json` = `{ "adsApiKey": "<baked shared internal key>", "version": 1 }` via extraResources. **Not** seeded into `settings.json` (a fleet rotation would be shadowed by a stale per-machine copy) and **not** in a `.cjs`.

One memoized `resolveBakedAdsRuntimeConfig()` next to `loadSettings`, reading packaged `process.resourcesPath/ads-runtime.json` then dev `app.getAppPath()/resources/ads-runtime.json`. `resolveAdsApiKey(formKey)` precedence: **form > settings.adsApiKey > env AIDCP_ADS_API_KEY > baked default**. Route the three call sites through it: `resolveAdsOpts`, `buildAdsProviderEnv` (so the core gets the key even with zero operator input), `ensureRuntime`. Result: unattended `ads start -k <baked>`.

Honest failure preserved: missing/malformed file AND no settings/env → resolver returns `''` → `ensureRuntime`'s existing honest "运行时未在跑且缺少 AdsPower api-key" → `surfaceFailure`.

Rotation (no source edit): fleet-wide = edit `ads-runtime.json`, bump `version`, ship a new installer; per-machine/emergency = operator types a key in Advanced settings (wins at tier 2). Copy fix: the API-Key placeholder "…必填" is now false → "留空即用随包默认凭据；仅在需要覆盖时填写".

### 4.2 First-run progress (revision: no create-progress IPC)
**Critique revision a1 — cut the `ads:createProgress` IPC channel.** create-env runs service-ensure only (no kernel) → there is no percent to stream for a few-second daemon start. Instead: set a **static** "正在启动指纹浏览器运行时…" line before the `await`, and clear it after. The **determinate 735 MB bar lives only on the launch path**, which already has `kernelPrep`. No new preload surface, no renderer subscription.

- Launch: runtime phase (presence "正在准备指纹浏览器运行时…", no percent) → kernel phase (determinate "正在下载浏览器内核（约 750MB，仅首次）… N%") via the existing `kernelPrep` bar.
- Create-env: static status line + honest retryable error on failure.

### 4.3 Error messages (honest + actionable)
- Launch path already actionable (`edgeFailurePatch` + `surfaceFailure`; retry via 启动) — unchanged.
- create-env `fetch failed` is **designed out** by the ensure gate; on prep failure return `指纹浏览器运行时未就绪：<cause>` (retryable). Defense-in-depth: a genuine post-ready `/不可达|fetch failed/` remaps to "指纹浏览器服务连接中断，请重试" (raw cause stays in the edge log; don't leak the `group/create` endpoint). Genuine `code!==0` API errors keep honest messages.
- Kernel catalogue failures expose only a safe class and retry guidance (for example `ECONNRESET` → "无法连接 AdsPower 内核服务，请检查网络后重试"). Raw stdout/stderr remains diagnostic return data and MUST NOT be copied into renderer logs because the vendor runtime may include credentials in its own diagnostics.

### 4.4 Monotonic renderer status projection

`status:update` pushes and lifecycle IPC return values can arrive in different orders. `routeStatus` SHALL compare parseable per-environment `updatedAt` values before replacing state or recording `lastMessage`; an older response is ignored. Missing/unparseable timestamps retain compatibility behavior. This prevents a queue-admission snapshot from overwriting newer "正在启动" progress while preserving genuine later re-entry into the queue.

## 5. Failure handling (must-handle → requirements)

**Top 3 (impact × likelihood on a fresh machine):**
1. **P0-A base split-brain (CRITICAL)** → one base authority (§3.2) + ensure-before-every-write (§3.4). Without it the feature mis-wires the instant 50325 is occupied.
2. **Shared-key seat/concurrency ceiling (HIGH).** **Critique revision a2:** classify a concurrency/seat rejection distinctly from "service unreachable", show "并发/席位已满：该密钥同时可开环境数已达上限，请错峰或联系管理员扩容", and — because a seat rejection happens at **`browser/start` inside the core** (core exits non-zero) — the fix belongs in the **core exit-code contract + supervisor exit classification**, NOT a main.cjs string-matcher: a seat-ceiling exit must be a **non-crash exit code** that does **not** count toward the 5-strike give-up. (A seat rejection at `ads start` ensure-time never spawns a core, so it can't trip the give-up anyway.)
3. **First-run 735 MB kernel download failure/partial (HIGH).** Keep the existing honest-only-on-`completed` contract; add: (a) distinguish **stalled/timeout** from **errored** (the 30-min hard timeout can expire on a slow-but-alive link); (b) **disk-full** → "磁盘空间不足（内核约需 ~1GB 可用）"; (c) **partial-file** — `kernelDownloaded` trusts the `is_downloaded` flag; add a size/sentinel check or surface the launch-time failure honestly rather than as a generic core crash. **Critique revision a3 — defer cancellable download** (a mid-download leak finishes the kernel you need anyway; benign for an internal tool).

**Folded in:** P0-B hard-switch honesty (no foreign adopt); P0-C baked key seam; **P1-B runtime dies mid-session** — a core seeing repeated LocalAPI `fetch failed` exits non-zero (honest) so the respawn path re-runs `ensureAdsServiceOnce` and re-derives the base; operator sees "指纹浏览器服务已中断，正在重启运行时…" (supervisor-side live base re-broadcast deferred — exit-and-respawn suffices); P1-C quit orphan → leave daemon (§3.5), cores still confirm browser death; writability under translocation → first-run staging (§3.1) + translocated smoke test.

## 6. Contract tests (critique revision b3)
Extend `test/electron/lifecycle-contract.test.ts` (source-assertion pattern) with a guard that the CLI `runCli` spawn resolves its writable dir from the **entry path** (not `process.cwd()`) and never inherits a stale cwd — a future CLI bump switching to `process.cwd()` would silently reintroduce the packaged-only failure this repo has shipped three times. Keep the existing asar-cwd guard.

## 7. Scope (YAGNI)

**IN:** devDependency + nested staging script + top-level extraResources (CLI tree + `ads-runtime.json`) + asar-absence verify; resolveCliEntry userData candidate + first-run staging with version stamp; split ensures + remove external/none branches (hard switch); `adsServiceBase` into `resolveAdsOpts` + ensure-gating on createEnv/proxy/delete/reconcile/status IPC (fast-path read); V2 per-profile browser start/active/stop in the core and Electron paths; bounded, validated lost-registry CDP adoption; baked rotatable key + single resolver + 3-call-site unification + copy fixes; static create-status line + honest error remap; seat classification as **core exit-code contract** (no give-up trip); kernel stalled-vs-errored + disk-full + partial-file check; eager service warm-up; leave-daemon-on-quit; delete dead `openAdsClient`; runCli-cwd contract test.

**DEFERRED:** Windows packaging (seam only); CLI/kernel self-update (pin CLI 2.1.0 + kernel `chrome_148`); per-operator keys; richer seat-quota UX (queueing/backoff); supervisor live-core base re-broadcast; per-arch sqlite trimming; userData rotatable-key tier; signing/notarization + `disable-library-validation`; cancellable kernel download; `ads stop` on quit.

## 8. Open decisions (need the user)
1. Baked key seat/concurrency **ceiling** (sizes the seat work — low-risk if comfortably above expected concurrent operators).
2. Kernel-delisted policy (only if `chrome_148` leaves the list): recommend **fail-honest + pinned**.
