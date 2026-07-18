## ADDED Requirements

### Requirement: Windows Ads CLI launches preserve the driven browser's native visibility

When AIDCP Edge uses the bundled Ads CLI runtime on Windows, the CLI compatibility layer MUST launch the driven `SunBrowser` process with native window visibility enabled. A policy intended for non-interactive Ads CLI helper subprocesses MUST NOT propagate `windowsHide: true` to `SunBrowser`. The staged runtime patch MUST fail closed when the pinned vendor hook shape changes, rather than silently shipping a browser that CDP can drive but the operator cannot reveal.

#### Scenario: Windows launches a driven SunBrowser

- **WHEN** the bundled Ads CLI runtime spawns a command whose executable basename is `SunBrowser` or `SunBrowser.exe`
- **THEN** that spawn uses `windowsHide: false`
- **AND** the existing CDP parking and show controls can move and raise the native browser window

#### Scenario: Ads CLI hook shape changes

- **WHEN** runtime staging cannot find either the pinned original hook shape or the known patched shape
- **THEN** staging fails with an actionable compatibility error
- **AND** the build MUST NOT continue with an unverified hidden-window policy

