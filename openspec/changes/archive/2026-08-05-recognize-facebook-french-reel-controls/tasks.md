## 1. Native Facebook Semantics

- [x] 1.1 Extend the shared Native reaction classifier with anchored French neutral Like, reaction-picker, and positive-state vocabulary without weakening decoy guards.
- [x] 1.2 Extend the Native canonical-Reel Follow classifier with exact French neutral and already-followed tokens while retaining author and geometry witnesses.

## 2. Retained TypeScript Parity

- [x] 2.1 Align the TypeScript CTA reaction vocabulary with the Native French semantics.
- [x] 2.2 Align the TypeScript Reel Follow target parser with the Native French semantics.

## 3. Executable Evidence

- [x] 3.1 Add Native router contracts for French Like/Follow targets, positive states, decoys, and ambiguity safeguards.
- [x] 3.2 Add focused TypeScript unit coverage for French CTA and Reel Follow parsing.

## 4. Validation and Delivery Record

- [x] 4.1 Run the focused Native page-engine and TypeScript tests plus Edge typecheck using the repository-owned toolchain.
  <!-- aidcp-edge 07c2f6e: focused Facebook CTA/Reels/Native router contracts 144/144; reaction-count isolation 11/11; acceptance 39 passed with real-device E2E gated; pinned Rust 1.97.1 native gate passed; `npm run typecheck` passed. Full Edge suite has one unrelated baseline failure in `manual-environment-nickname-ipc.test.ts`; both that test and its renderer source are byte-identical to origin/master. -->
- [x] 4.2 Run `openspec validate recognize-facebook-french-reel-controls --strict` and record repository commit, validations, and package/live-acceptance boundaries.
  <!-- OpenSpec strict validation passed. Edge implementation commit: aidcp-edge 07c2f6e. No Edge installer was built or installed, no deployed runtime was changed, and no real Facebook Like/Follow write was used for acceptance. Installed 0.3.25 therefore remains unaffected until a separately authorized package/update. -->
