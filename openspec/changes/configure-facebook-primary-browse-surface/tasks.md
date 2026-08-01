## 1. Cloud surface authority

- [x] 1.1 Add the environment primary-surface and audit migration, seed all existing Facebook environments to Reels, and register schema ownership/capability requirements.
- [x] 1.2 Extend the Facebook operation-policy store with surface projection, account resolution, independent CAS writes, immutable audit, and no operation-revision mutation.
- [x] 1.3 Persist the selected/default Reels surface atomically during Facebook environment provisioning and return it in provisioning truth.
- [x] 1.4 Add customer-auth read/write support for the environment surface while preserving existing operation-mode and Console writes.
- [x] 1.5 Add focused migration, store, provisioning, and customer API tests for Reels defaults, Feed override, stale revision, ownership/platform rejection, audit, and operation-progress isolation.

<!-- 1.x: aidcp-cloud e61b8da; focused 188 pass, acceptance 184 pass, full 4064 pass/11 gated skips, typecheck pass; no deployment; no deviation. -->

## 2. Cloud browse arbitration

- [x] 2.1 Pin the authoritative primary surface for each Facebook browse session without changing operation-mode arbitration.
- [x] 2.2 Intercept Reels-primary Feed batches and confirmed empty/unreportable observations before evaluation/accounting, then authorize `facebook_reels_primary` through the existing Reels entry state machine.
- [x] 2.3 Preserve Feed-primary evaluation and evidence-based Reels fallback behavior.
- [x] 2.4 Add focused dispatcher tests across persona, slow-start, rule, and consumption modes, including non-empty/empty Feed suppression and reportable-Reel confirmation.

<!-- 2.x: aidcp-cloud e61b8da; dispatcher coverage is included in focused/full results above; no deployment; no deviation. -->

## 3. Edge client and Reels execution

- [x] 3.1 Extend provisioning and customer operation-policy contracts with the independent primary surface, defaulting Facebook creation to Reels.
- [x] 3.2 Replace the existing-environment four switch-like mode rows with one four-option selector and add a separate Feed/Reels control to creation and edit views.
- [x] 3.3 Route `facebook_reels_primary` to the existing `enterReels()` executor and preserve its route/card postconditions and honest pending/failure receipts.
- [x] 3.4 Add focused Edge tests for creation defaults, read/write normalization, independent mode/surface edits, UI control wiring, and configured-primary Reels entry.

<!-- 3.x: aidcp-edge 8290b5e; focused 176 pass, full 2902 pass/1 gated skip, typecheck and JS syntax checks pass; no package or deployment; no deviation. -->

## 4. Contracts and validation

- [x] 4.1 Synchronize Cloud/Edge payload types, command reason documentation, and protocol acceptance coverage.
- [x] 4.2 Run Cloud focused acceptance tests and typecheck, then Edge focused tests and typecheck; serialize any load-sensitive Native retry.
- [ ] 4.3 Run `openspec validate configure-facebook-primary-browse-surface --strict`, record commits and validation evidence, and stop before packaging or deployment.

<!-- 4.1-4.2: aidcp-cloud e61b8da and aidcp-edge 8290b5e; protocol docs updated in control; no Native retry was needed; no package or deployment. -->
