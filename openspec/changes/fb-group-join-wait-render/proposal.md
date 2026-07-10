## Why

Live `/comment <昵称> --join` on dev kept returning `ambiguous_skip` even after `facebook-group-join-observe-i18n` shipped. Connecting to the operator's browser via CDP found the real root cause: the edge observed the group at a **fixed 2.5s settle**, but the Facebook group page renders its header + Join button only **~7 seconds** in (measured: at 2.5s `document.readyState=loading` with 0 action nodes; the Join button "加入小组" appears at ~6988ms). So the edge saw an empty/loading page → reported a null CTA → the cloud judge fail-closed. This was never a locale problem (the account's FB UI is Chinese, "加入小组", already matched); it is a **timing** problem, made worse by Facebook's unstable network where a fixed settle is never right.

## What Changes

- Replace the fixed post-navigation settle in the edge group-join observation with a **readiness poll**: after navigating, re-observe every `pollMs` until a DECISIVE signal renders — the Join button is found, or an already-member / login / captcha / questionnaire / pending / any-classified-CTA signal — or a bounded `readyTimeoutMs` (default 12s) elapses as a fail-closed backstop. This adapts to unstable network (slow loads wait, fast loads proceed immediately) instead of guessing a duration.
- Report `actionNodeCount` and `documentReady` in the observation (and audit) so a timeout is diagnosable (were we still loading?) — exactly the signal that pinpointed this issue.
- Handle the cookie-consent and login/captcha overlays every poll iteration (they can appear at any time). On timeout with no decisive signal, return the last observation honestly to the cloud judge — never a fake success.

## Capabilities

### New Capabilities

- `fb-group-join-wait-render`: the edge group-join observation waits for the group page to actually render a decisive signal (bounded, network-tolerant) before reporting to the cloud judge, instead of observing after a fixed delay.

## Impact

- Affected repos: `aidcp-edge` (`src/facebook/join-executor.ts`: `observeUntilReady` poll + `isDecisiveObservation` + observation `actionNodeCount`/`documentReady`; tests) and `aidcp` (this OpenSpec change). NO cloud change, NO protocol change.
- Deployment: edge-only, no ECS service — the operator pulls/rebuilds the local Electron client, then re-runs `/comment <昵称> --join`. Verified on the live browser: once loaded, observe yields the Join button ("加入小组") with click coordinates; the ~7s render falls inside the poll window.
- Complements `facebook-group-join-observe-i18n` (multilingual CTA matching) — together the edge observes the group reliably across locales AND slow/unstable loads.
- Real-machine confirmation rolls into `docs/real-machine-acceptance-backlog.md` 簇 32.
