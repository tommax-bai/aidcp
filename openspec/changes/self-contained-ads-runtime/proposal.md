# Self-Contained Bundled AdsPower CLI Runtime (edge desktop, macOS-first)

## Why

The edge desktop client silently hard-depends on an **externally installed and running AdsPower desktop client** to provide the fingerprint-browser LocalAPI on `127.0.0.1:50325`. On an operator machine this surfaces as: some accounts work while AdsPower is open, then "新建环境" fails with `本地指纹浏览器服务不可达(group/create): fetch failed` the moment AdsPower is closed. Two gaps, both坐实 in code:

- **Packaging gap** — the installer bundles **no** fingerprint-browser runtime. The embedded-runtime orchestration (`src/electron/ads-runtime.cjs`, from the deferred change `edge-bundled-adspower-cli-runtime`) exists but is **dormant**: `adspower-browser` is not a dependency, there is no `extraResources`/`asarUnpack`, and `resolveCliEntry` never finds a CLI → it falls back to "connect to whatever is on 50325." No API key is bundled either.
- **Interaction gap** — `ads:createEnv` calls `group/create` directly with **no** runtime-ensure (only the browse/launch path ensures the runtime), so a cold LocalAPI fails with a raw, non-actionable `fetch failed`.

The intended self-contained model is now **proven feasible**: AdsPower ships an official MIT-licensed CLI (`adspower-browser@2.1.0`) that runs the LocalAPI service standalone (no desktop client), downloads its own fingerprint kernel (SunBrowser), and drives real fingerprint browsers. This was verified against a **live standalone CLI running on the dev machine** (`node .../adspower-browser/cwd/lib/main.min.js` on 50325 serving profile `k1e0ero8`, kernel in `~/.adspowerCli/chrome_148`, no desktop client). Bundling this CLI makes every operator machine work out of the box.

## What Changes

- **New** — the installer ships a **read-only template** of the AdsPower CLI runtime (`adspower-browser@2.1.0`: `cli/ + cwd/ + sqlite/ (all-arch prebuilt `node_sqlite3.node`) + nested `node_modules/` incl. `playwright-core`) at `Contents/Resources/adspower-browser` (~31 MB), plus a `Contents/Resources/ads-runtime.json` holding a **baked, rotatable shared internal API key**. Native `.node` forces `extraResources` (a `.node` cannot `dlopen` from inside `app.asar`), which lands exactly at `resolveCliEntry`'s primary candidate.
- **New** — first-run **staging** of the template to `userData/ads-runtime/adspower-browser` (writable), because under macOS App Translocation a quarantined unsigned `.app`'s `Resources` dir is read-only and the CLI writes into its own `cwd/`.
- **Modified** — **hard switch**: the runtime-ensure always drives **our** bundled CLI (`ads status` → reuse if already running, else `ads start -k <baked key>`), and the old `mode:'external'` HTTP-adopt and `mode:'none'` "proceed anyway" branches are **removed**. A missing bundled runtime is an honest hard-stop, not a reason to try 50325.
- **Modified** — **one base authority**: `resolveAdsOpts` prefers the actually-bound service base (`adsServiceBase`, renamed from `embeddedAdsApiBase`), closing a real split-brain where every main-process read/write ignored the resolved port and fired at 50325.
- **Modified** — **create-env (and proxy/delete/reconcile/status read IPC) ensure the service first** (metadata-only, **never** the 735 MB kernel download), fixing the cold-start `fetch failed`. Only the **first browser launch** gates on the kernel.
- **Modified** — a single `resolveAdsApiKey` resolver (precedence: form > settings > env > baked default) feeds `resolveAdsOpts`, `buildAdsProviderEnv` (so the core child gets the key even with zero operator input), and `ensureRuntime` → unattended cold start.
- **Modified** — honest, actionable errors replace the raw `fetch failed`; minimal failure taxonomy for the shared-key seat/concurrency ceiling and kernel-download failures (stalled-vs-errored, disk-full, partial-file) without tripping the crash-loop give-up.
- **Empirically pinned** — the LocalAPI does **not** check the key per request (`/api/v1/group/list` returns real data with no auth header); the key only authenticates `ads start` against AdsPower cloud. So injecting the baked key into the core is harmless even when adopting a daemon started under a different key.

## Capabilities

### New Capabilities
- `edge-bundled-ads-runtime`: the desktop client bundles, stages, starts, and self-heals its own AdsPower fingerprint-browser runtime — no external AdsPower client required. Covers: packaging (extraResources + native-module-outside-asar), first-run userData staging (translocation seam), hard-switch service-ensure with reuse, baked rotatable key, split service-ensure vs kernel-ensure with kernel gated only at first launch, one base authority, leave-daemon-on-quit, and honest failure taxonomy.

### Modified Capabilities
- `adspower-environment-provisioning`: environment creation and other LocalAPI write/read operations SHALL ensure the bundled runtime service is ready before calling the LocalAPI (never silently hitting a cold/foreign port), and creation MUST NOT trigger the kernel download.
- `edge-desktop-packaging`: the macOS installer SHALL bundle the AdsPower CLI runtime template via `extraResources` (native `.node` outside `app.asar`) and its baked-key config, with a build-time staging step and an asar-absence verification.

## Impact

- **aidcp-edge** (all code): `package.json` (devDependency `adspower-browser@2.1.0` + top-level `extraResources` + staging build step); new `scripts/stage-ads-runtime.mjs` + `scripts/verify-ads-runtime-staged.mjs`; new `resources/ads-runtime.json`; `src/electron/ads-runtime.cjs` (resolveCliEntry +userData candidate; ensure/kernel error taxonomy; keep the sqlite native-module comment — it is correct); `src/electron/main.cjs` (split ensures; base-authority fix in `resolveAdsOpts`; `resolveAdsApiKey`; ensure-gating on create-env/proxy/delete/reconcile/status IPC; whenReady service warm-up; leave-daemon-on-quit; delete dead `openAdsClient`); `src/electron/ads-local-api.cjs` (default base); `src/electron/preload.cjs` + renderer (create-progress line + copy fixes); `test/electron/lifecycle-contract.test.ts` (add a runCli-cwd / CLI-writable-dir contract test alongside the existing asar-cwd guard); `docs/release-desktop.md` (staging + translocated smoke test).
- **Distribution**: installer grows ~+31 MB (CLI template). Each operator machine downloads the ~735 MB SunBrowser kernel **once** to `~/.adspowerCli` on first browser launch (not in the installer).
- **Licensing**: `adspower-browser` is MIT — redistribution/bundling is permitted.
- **Migration**: hard switch. Machines with an external desktop AdsPower or a global CLI on 50325 are handled by `ads status` reuse / CLI fallback-port, not by riding the foreign service.
- **Platforms**: macOS this round; the staging script has a single OS-normalize line and userData target as the Windows seam (Windows deferred).
- **Red lines**: never silently fake success (every failure returns honest `{ok,error}`); never touch同机 isales; do not regress the shipped packaged-spawn cwd/asar fix; the baked key lives in a data file, never hardcoded in a `.cjs`.

## Open Decisions (need the user)

1. **Baked key seat/concurrency ceiling.** The chosen shared key's concurrent-open ceiling sizes the seat-handling work: if it comfortably exceeds expected concurrent operators, the seat taxonomy is low-risk; if tight, it will bite routinely. Need the actual number/plan.
2. **Kernel-delisted policy** (only if `chrome_148` ever leaves AdsPower's list): fail-honest + require app upgrade (fingerprint-stable) vs auto-float to newest same-major (self-healing but shifts fingerprint). Recommendation: fail-honest + pinned.
