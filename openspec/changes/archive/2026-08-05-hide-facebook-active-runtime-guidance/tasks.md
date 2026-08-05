## 1. Regression Contract

- [x] 1.1 Add pure view-model coverage for hidden Facebook `first-post` searching/generating and ordinary `running` cards.
- [x] 1.2 Add boundary coverage proving Facebook session/hour/day cards, the persona-complete dialog, and XHS first-post/running cards remain unchanged.
- [x] 1.3 Add Electron DOM coverage for Facebook card removal, retained top presence/data cards, and platform-switch cleanup.

## 2. Edge Implementation

- [x] 2.1 Gate only Facebook `first-post` and ordinary `running` returns in `runtimeGuidanceView()` while preserving existing `stopped`, interval, completion, presence, and non-Facebook paths.
- [x] 2.2 Verify the implementation does not modify persona-complete markup, styles, animation, CTA wiring, Cloud contracts, or runtime actions.

## 3. Validation and Delivery Record

- [x] 3.1 Run the focused Edge UI logic and companion/fleet Electron tests.
- [x] 3.2 Run Edge typecheck.
- [x] 3.3 Run strict OpenSpec validation.
- [x] 3.4 Record the Edge commit SHA, validation evidence, and no-package/no-install/no-deployment boundary in this task file.

<!-- Delivery: aidcp-edge commit 8ba51c9. Focused ui-logic/companion-ui/fleet-console tests passed (251 cases, exit 0); `npm run typecheck` passed; `openspec validate hide-facebook-active-runtime-guidance --strict` passed. Source-only delivery: no desktop package, installation, DEV/OL deployment, browser restart, or live-account action was performed. No protocol, Cloud, persona-complete markup/style/CTA, runtime action, XHS, interval, or completion behavior was changed. -->
