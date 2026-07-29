## 1. Native Facebook foreground authority

- [x] 1.1 Gate the common Facebook `page_scroll` foreground activation on exact `reason = idle_recover_nudge`.
- [x] 1.2 Remove the Feed recovery-control path's independent foreground activation while preserving its fresh coordinate probe, single trusted pointer sequence, and home-surface postcondition.

## 2. Regression coverage

- [x] 2.1 Add fake-CDP coverage proving routine Feed/Reels scrolls emit zero foreground calls and watchdog scroll emits exactly one call before input.
- [x] 2.2 Cover ordinary no-target and Feed recovery-control paths so neither can independently foreground or duplicate the watchdog activation.

## 3. Contract documentation

- [x] 3.1 Update `docs/protocol.md` to state that only Facebook `page.scroll{reason:"idle_recover_nudge"}` may foreground the exact target and that other automatic scrolls remain background-only.

## 4. Validation

- [x] 4.1 Run focused Native Facebook fake-CDP regressions. <!-- aidcp-edge focused fake-CDP: 41/41 passed; foreground subset: 3/3 passed -->
- [x] 4.2 Run the required Edge acceptance/full tests and typecheck. <!-- aidcp-edge aaa7afb: acceptance 31/31; full TypeScript 2709 passed with 1 gated skip; typecheck passed. Native fmt/clippy and fake-CDP 41/41 passed. The full Rust gate still has 3 unrelated publish-deadline failures after 132 passes; a representative failure was reproduced on the unmodified canonical baseline. -->
- [x] 4.3 Run `openspec validate limit-facebook-scroll-foreground-to-watchdog --strict`. <!-- aidcp control: strict validation passed -->

## 5. Delivery

- [x] 5.1 Commit, rebase, fast-forward integrate, and push the Edge change to `master`. <!-- aidcp-edge aaa7afb; rebased onto 2459214; integrated and pushed by scripts/land-change -->
- [ ] 5.2 Record Edge commit/validation and the no-installer delivery boundary, then commit and push the control change to `main`.
