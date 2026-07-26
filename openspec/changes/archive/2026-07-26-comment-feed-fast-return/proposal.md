## Why

Manual `/comment` tasks currently keep the browser on the target detail page while the edge waits for platform confirmation. Operators need an explicit fast-return mode for feed-oriented runs where releasing the browser back to the platform home page is more important than obtaining a platform-confirmed terminal result.

## What Changes

- Add a trailing `/comment <nickname> --feed` switch, composable with the existing comment switches.
- Carry the switch only through the manual single-comment path; automatic schedules and commands without `--feed` retain current confirmation behavior.
- After the comment submit action is dispatched, wait 500 ms, skip result detection/waiting, navigate directly to the platform home page, and close the commit window.
- Report the write honestly as submitted-but-unconfirmed so upstream deduplication prevents automatic retry while receipts do not imply platform-confirmed success.
- Apply the same contract to the Xiaohongshu and Facebook comment executors.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `comment-search-command`: Add the manual `--feed` fast-return switch and its honest submitted-unconfirmed outcome contract.
- `facebook-scheduled-comment`: Apply manual `--feed` fast-return behavior to Facebook targeted comments without weakening pre-submit safety gates.

## Impact

- Control/spec: comment command and platform comment lifecycle requirements.
- Cloud: Feishu/delegated-command parsing, task constraints, scheduler and edge-command payload propagation, terminal receipt semantics.
- Edge: shared protocol payload plus Xiaohongshu and Facebook post-submit branches and home navigation.
- Tests: command parsing/propagation, protocol behavior, both platform executors, and no-regression coverage for default confirmation mode.
