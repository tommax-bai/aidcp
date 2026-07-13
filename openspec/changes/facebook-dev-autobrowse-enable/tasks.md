## 1. Edge Spawn Policy

- [x] 1.1 Add a pure, tested policy that resolves Facebook browse mode from platform and resolved cloud environment. <!-- 2026-07-13: `fleet.facebookBrowseModeFor` permits only Facebook + dev; focused Electron policy tests pass. -->
- [x] 1.2 Inject the policy result into every final core child environment after cloud selection and inherited environment merging. <!-- 2026-07-13: final `spawnEnv` receives the derived mode after `resolvedCloudKey`; focused Electron policy tests pass. -->

## 2. Verification And Integration

- [x] 2.1 Run focused Electron policy tests, Edge acceptance tests, full Edge tests, and type checking. <!-- 2026-07-13: focused Electron 26/26; acceptance 16/16 (one intentional E2E skip); full Edge 1110/1110; `npm run typecheck` PASS. -->
- [x] 2.2 Rebase, integrate, and push the Edge change to `master` without touching the dirty release checkout. <!-- 2026-07-13: edge commit `5e23261` rebased cleanly on `origin/master` and fast-forward pushed `de89150..5e23261`; dirty local release checkout was not touched. -->
- [ ] 2.3 Restart the local development Edge client and record an honest real-profile observation for the enabled Facebook fleet, including the activity/presence projection and account-scoped today totals. <!-- 2026-07-13: before the UI fix, `ads-k1ei3dbi` truthfully advanced cloud today views 1→5 while the client had no Facebook activity projection. The new desktop client was restarted but remains idle by design; a resumed real profile is still needed to observe the rendered projection without fabricating another real like. -->
- [x] 2.4 Emit structured Facebook UI events at confirmed session/read/like boundaries; keep failed or shadow actions uncounted and prevent legacy-like double counting. <!-- 2026-07-13: edge commit `bce5a1b`; focused UI/Facebook tests 38/38, acceptance 16/16 (one gated E2E skip), full Edge tests, and typecheck pass. -->

## 3. Change Record

- [ ] 3.1 Update this task record with commits, validation, and the real-machine outcome; validate the OpenSpec change strictly.
