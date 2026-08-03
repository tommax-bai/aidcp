# Self-Contained AdsPower Runtime

## Why

The Edge desktop originally depended on a separately installed AdsPower desktop service. A cold LocalAPI call could therefore fail before the client had established its own runtime. The delivered source now ships and manages an AdsPower CLI runtime, but this change's artifacts still described deleted `group/create` behavior, speculative fallback-port and seat handling, obsolete packaging choices, and an inaccurate task ledger.

This reconciliation records only behavior present in the current `aidcp-edge` source. Packaging, signing, notarization, and packaged dependency closure remain authoritative in the existing `edge-desktop-packaging` baseline rather than being duplicated here.

## What Changes

- Stage the build-produced AdsPower CLI template into application `userData` using content identity, an atomic replacement, and rollback on failure.
- Manage the CLI through its own status/start/stop contract. Reset a registered daemon at most once per successful Electron session, use the CLI-reported LocalAPI base as the runtime authority, and stop the managed daemon after browser/core shutdown on application quit.
- Resolve one API key for runtime start, main-process requests, and core children with precedence `form > settings > environment > packaged data`.
- Ensure the CLI service before LocalAPI operations; keep metadata operations independent of the browser-kernel download. Cached status reads retry through service ensure only after a transport failure.
- Preserve the current environment-creation contract: resolve the pre-provisioned `aidcp` group through `group/list`, then call `user/create`; never call `group/create`.
- Use the V2 per-profile browser lifecycle and adopt a registry-lost browser only after exact loopback CDP path and port verification.
- Prove an installed pinned kernel from its local executable before consulting the cloud catalogue, and reject older timestamped renderer status snapshots.
- Keep the Windows development staging path that invokes npm through the current build-time Node and runs the staged CLI with Electron's Node.

## Capabilities

### New Capabilities

- `edge-bundled-ads-runtime`: staging, service ownership, key/base authority, service-versus-kernel gating, V2 lifecycle reconciliation, installed-kernel proof, and monotonic runtime status.

### Modified Capabilities

- `adspower-environment-provisioning`: LocalAPI operations establish the managed service first and environment creation uses the already-authoritative pre-provisioned group contract.

## Scope Boundaries

- `edge-desktop-packaging` remains the authority for what enters the installer and for signing/notarization/package gates; this change does not create a second packaging contract.
- No shared-key seat/concurrency taxonomy, broad disk-full/partial-download recovery model, automatic kernel-version floating, or external AdsPower desktop coexistence/fallback-port guarantee is included.
- The managed CLI is not adopted from an arbitrary HTTP responder. A port or daemon conflict that the managed CLI cannot resolve fails visibly.
- The four old real-machine backlog items were last active on 2026-07-30. On 2026-08-03 the user cancelled every real-machine acceptance item inactive for more than three days. Cancellation is not acceptance evidence.

## Evidence and Delivery Boundary

- Core source commits include `12bac1d` (service/base/key authority), `c3586e4` (bundled runtime staging), `1f36bb4` (Windows staging), `e67fac4` (V2 lifecycle), and `1e09769` (installed-kernel and status ordering).
- Later source corrections include `c86bd94` (pre-provisioned group), `9569fec` (content-identity refresh and managed-daemon stop), `680b188`/`f4c1323` (packaged runtime gates), and `b8c9b83` (runtime kept out of development dependencies).
- This cleanup changes control/OpenSpec artifacts only. It does not modify Edge source, build or install a desktop package, deploy anything, or claim current real-machine acceptance.
