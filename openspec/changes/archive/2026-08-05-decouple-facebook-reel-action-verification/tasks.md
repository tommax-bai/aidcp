## 1. Fresh Reel Verification

- [x] 1.1 Prove the existing Reel Like verifier reads a replacement Like control on the same canonical Reel without requiring the pre-click DOM node to survive
- [x] 1.2 Keep transient same-Reel Like probe failures inside the existing bounded verification window while preserving immediate ambiguity for an observed different Reel
- [x] 1.3 Keep transient same-Reel Follow probe failures inside the existing bounded verification window while preserving immediate ambiguity for an observed different Reel or author

## 2. Regression Coverage

- [x] 2.1 Add router regression coverage for a replaced Like DOM node on the same Reel and for lost canonical Reel identity
- [x] 2.2 Add Native regression coverage for bounded Like and Follow recovery without a second action dispatch

## 3. Validation And Delivery Evidence

- [x] 3.1 Run focused router and Native page-engine tests plus the Native capability validation gate
- [x] 3.2 Run Edge typecheck and strict OpenSpec validation
- [x] 3.3 Record repository SHA, validations, source-only delivery boundary, and any deviations in this checklist

### Delivery Evidence

- Edge implementation: `aidcp-edge` `7c12c95406419b43dd544679954feab1f81440e4`, fast-forwarded and pushed to `origin/master`.
- Router contract: `npx tsx --test test/native-page-engine/facebook-router-contract.test.ts` — 109 passed.
- Native capability gate: `npm run gate:native` — format, Clippy with warnings denied, and locked full Native tests passed.
- Edge typecheck: `npm run typecheck` — passed.
- Control contract: `openspec validate decouple-facebook-reel-action-verification --strict` — passed.
- Delivery boundary: source only; no Edge installer was built or installed, no real-account write acceptance was run, and no Cloud/Console/runtime deployment was required.
- Deviation: the current Edge router already freshly resolved the Like control, so no router implementation edit was necessary; regression coverage was added and the remaining immediate-terminal behavior was removed only from the bounded Native Like/Follow verification loops.
