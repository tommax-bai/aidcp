# Windows Ads CLI Browser Visibility

## Why

On Windows, the bundled Ads CLI runtime preloads a child-process compatibility hook that applies `windowsHide: true` to every descendant spawn. That policy also reaches the Ads CLI-launched `SunBrowser`, leaving its native top-level window non-visible even though the process, CDP target, and on-screen bounds are all healthy. The existing "show browser" path can move the CDP window and bring the page target forward, but it cannot make an OS-hidden native window visible.

The environment rail also handles every physical click as a phase transition (`select -> show -> park`). A double-click on an already-selected nickname can therefore send `show` and immediately send `park`, contradicting the operator's intent to reveal the browser.

## What Changes

- Patch the staged Ads CLI runtime at its compatibility boundary so a descendant command ending in `SunBrowser` / `SunBrowser.exe` is always spawned with `windowsHide: false`, while the existing Windows behavior for other Ads CLI helper subprocesses remains unchanged.
- Make staging fail honestly if the expected Ads CLI hook shape changes, so a future runtime upgrade cannot silently restore hidden browser windows.
- Treat a rapid second physical click as part of the same double-click gesture rather than another show/park phase transition.
- Make double-clicking the environment nickname an explicit show-only action; it never sends a park command.
- Add focused staging and Electron renderer regressions.

## Capabilities

- `pluggable-browser-provider`: Windows Ads CLI launches keep the driven `SunBrowser` native window operable and recoverable through the existing CDP show/parking channel.
- `edge-companion-ui`: nickname double-click is show-only and cannot immediately reverse into parking.

## Impact

- Code: `aidcp-edge/scripts/stage-ads-runtime.mjs`, a small staging patch helper, Electron renderer code, and focused tests.
- Runtime: a regenerated staged Ads CLI runtime and a restart are required for already-running hidden Windows browser processes.
- No cloud, protocol, risk, account identity, or deployment behavior changes.

