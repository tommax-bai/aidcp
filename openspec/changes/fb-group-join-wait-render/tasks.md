# Tasks — fb-group-join-wait-render

## 1. aidcp-edge — readiness poll

- [x] 1.1 Replace the fixed post-navigation settle in `joinGroup` with `observeUntilReady`: poll every `pollMs` until a decisive signal (Join button found / member / login / captcha / questionnaire / pending / classified CTA) or `readyTimeoutMs` (default 12s) backstop; handle consent/blocking overlays each iteration. <!-- aidcp-edge 5ac6206/a6f0f3f: src/facebook/join-executor.ts observeUntilReady + isDecisiveObservation -->
- [x] 1.2 Report `actionNodeCount` + `documentReady` in the observation (IIFE + type + publicObservation) for audit diagnosability. <!-- aidcp-edge a6f0f3f -->
- [x] 1.3 Timeout returns the last observation honestly (cloud fail-closes); never a fabricated success. <!-- aidcp-edge a6f0f3f: observeUntilReady returns lastObs on cap; no ok fabricated -->

## 2. Tests + verification

- [x] 2.1 Unit tests: waits past "still loading" (empty) observations then finds + clicks Join; timeout with empty → honest no_button (click) / observation_only; existing decisive-first tests unaffected. <!-- aidcp-edge a6f0f3f: test/facebook/join-executor.test.ts, 3 new tests -->
- [x] 2.2 `npm test` (910) + `npm run typecheck` green. <!-- aidcp-edge a6f0f3f -->
- [x] 2.3 Live-browser validation via CDP: measured Join button ("加入小组") renders ~6988ms (readyState=loading + 0 nodes at 2.5s); on a loaded page observe yields joinButton found + coords (x1120,y268) → the poll window (12s) covers it. <!-- 2026-07-10 CDP probe against operator's AdsPower browser (debug_port dynamic) -->

## 3. Rollout

- [ ] 3.1 Land edge branch → `master` (done: a6f0f3f); land control change → `main`.
- [ ] 3.2 Operator pulls/rebuilds the local Electron edge (`npm run build:dist && npm run electron:dev`), re-runs `/comment <昵称> --join` on the target group, confirms it now clicks Join (server-verified) or gives an honest gated/pending outcome — no longer ambiguous_skip from a premature observation. Log under `docs/real-machine-acceptance-backlog.md` 簇 32.

## 4. Closeout

- [ ] 4.1 `openspec validate fb-group-join-wait-render --strict`.
- [ ] 4.2 Archive after operator rebuild + real-machine confirmation.
