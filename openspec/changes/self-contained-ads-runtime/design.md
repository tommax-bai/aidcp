# Design — Self-Contained AdsPower Runtime

> Reconciled on 2026-08-03 against current `aidcp-edge` `master`. This document describes the delivered source path, not the original July draft.

## 1. Authority boundaries

- `edge-desktop-packaging` owns installer contents, native dependency closure, architecture checks, signing, notarization, and packaged smoke gates.
- `edge-bundled-ads-runtime` owns runtime staging and lifecycle after the packaged template exists.
- `adspower-environment-provisioning` owns the `group/list` → `user/create` flow and structurally forbids `group/create`.
- The managed CLI's reported LocalAPI base is authoritative after service establishment. Renderer/settings values are diagnostic fallbacks only before that authority exists.

## 2. Build and staging

`scripts/stage-ads-runtime.mjs` installs the pinned AdsPower CLI into a build tree. The CLI is not retained as an application development dependency. `extraResources` and the existing packaging gates place the runtime outside `app.asar`; `resources/ads-runtime.json` is supplied as protected build input rather than committed with a real key.

At runtime, `stageAdsRuntimeIfNeeded()` selects the packaged template (or the build tree in development) and stages it under application `userData`. The stage stamp includes application version, package version, and full template content identity. A changed template is copied to a candidate directory, the previously managed daemon is stopped with the CLI contract, and directories are exchanged atomically. Failure restores or preserves the previous tree and returns an honest error.

The production CLI entry is the writable staged copy. Packaged/build/raw-module candidates exist only to locate a template or support development; absence of a usable managed entry is a hard failure, not permission to connect to an arbitrary LocalAPI responder.

## 3. Managed service, key, and base

`ensureAdsServiceOnce()` is a settle-cleared single-flight. On the first successful establishment in an Electron session it stages the template, performs the bounded registered-daemon reset, starts the managed CLI with the resolved key, and stores the CLI-reported base in `adsServiceBase`. Later calls re-check service health without repeating the session reset.

The key resolver uses `form > settings > AIDCP_ADS_API_KEY > packaged data`. Missing key material returns a visible failure. Once `adsServiceBase` exists, it wins over form/settings base values for main-process calls and core-child environment injection.

The runtime lifecycle does not probe or adopt an unrelated AdsPower desktop HTTP service. External port coexistence has no fallback-port guarantee in this change; an unresolved conflict fails visibly. On application quit, Edge first requests bounded core/browser shutdown and then stops the managed CLI daemon.

## 4. LocalAPI operations and environment creation

Metadata writes and management reads establish the service before using LocalAPI. Status/list reads use a cached-base fast path and clear/re-establish the service only after a transport failure; routine polling does not spawn `ads status` each time. Service establishment never downloads a browser kernel.

Environment creation resolves the exact pre-provisioned group name `aidcp` through `group/list` and sends its current id with `user/create`. A stale cached id may be re-resolved once only when AdsPower reports that group deleted/archived and a different current id is visible. Missing group, list failure, or unrelated create failure stops visibly. `group/create` is outside the write allowlist.

## 5. Browser and kernel lifecycle

The core provider and Electron inspection/reconciliation paths use V2 per-profile `active`, `start`, and `stop`. If V2 reports `Inactive`, an orphan browser is adopted only when the profile-scoped `DevToolsActivePort` port and browser path exactly match loopback `/json/version`; otherwise Edge calls V2 `start`. V2 stop retains CDP-dark confirmation.

Kernel ensure is single-flight per requested version. It first proves a pinned local executable is a non-empty regular file and executable on POSIX. Only a failed local proof consults `get-kernel-list`; catalogue reads use bounded retry and safe error classes, and download success requires the existing completed postcondition. Runtime progress uses the existing kernel preparation projection.

Renderer `routeStatus()` rejects an incoming parseable `updatedAt` older than the current environment status. Missing or invalid timestamps retain the compatibility path.

## 6. Cancelled and deferred scope

The following are not part of the delivered contract:

- shared-key seat/concurrency exit classification;
- broad disk-full, partial-download, cancellable-download, or automatic kernel-floating behavior;
- automatic coexistence with a separately managed AdsPower desktop service;
- an eager background service warm-up before a real operation;
- leaving the managed daemon running after application quit;
- the four real-machine backlog items cancelled on 2026-08-03 after more than three days without activity.

## 7. Validation boundary

Source and automated validation cover staging, service/base/key authority, environment service gating, V2 reconciliation, local-kernel proof, status ordering, package input, dependency closure, and architecture guards. They do not prove that a newly built installer currently succeeds on an operator machine. Cancelled real-machine tasks must not be reported as passed.
