## Why

First live `/comment <昵称> --join` (change `facebook-manual-join-comment`, deployed dev 2026-07-10) exposed a real-machine defect in the underlying group-join observation (`facebook-group-join-and-commenting`): the edge join-executor's Join-button classifier matched **only English + Chinese** labels via exact match (`/^(join|join group|加入小组|加入社团|加入群组)$/`). A Vietnamese target group's Join button reads **"Tham gia nhóm"**, which matched nothing, so the edge reported `mainCtaText: null` / `joinButton.found=false`. The cloud judgment role — which is multilingual and was ready to classify — never received the button text, so it correctly **fail-closed** (`ambiguous_skip`) and the account parked on the group page without joining. This also violated the design rule that "the edge MUST NOT decide the join gate; the cloud role decides" — the edge was swallowing the CTA before the cloud could judge it.

## What Changes

- Replace the edge join-executor's EN/ZH exact-match Join-button classifier with a **multilingual contains-match** over shared keyword lists (English, Chinese, Vietnamese, Spanish, Portuguese, Indonesian, Thai, French, German, Korean, …) for join / joined / pending, checking joined/pending before join so "đã tham gia" (joined) is not misread as join.
- Extract `classifyCtaLabel()` as the single source of truth (unit-tested); the in-page observation IIFE interpolates the same keyword lists so classification and click-target detection stay consistent.
- Harden header/text extraction: broaden heading selectors and fall back to the `[role="main"]` region text and `document.title`, so the raw Join label reaches the cloud judge even when a specific heading node isn't found.
- Preserve fail-closed safety: an unrecognized label still yields no join classification (no click); only recognized Join buttons produce clickable coordinates. The gate decision stays in the cloud.

## Capabilities

### New Capabilities

- `facebook-group-join-observe-i18n`: the edge group-join observation recognizes Join/Joined/Pending buttons across locales (not only EN/ZH), reports the real CTA text/coordinates to the cloud judge, and never silently drops a non-EN/ZH Join button — while keeping the fail-closed gate decision in the cloud.

## Impact

- Affected repos: `aidcp-edge` (`src/facebook/join-executor.ts` classifier + observation IIFE + header extraction; tests) and `aidcp` (this OpenSpec change). NO cloud change (the multilingual cloud judge already handles the CTA text once it receives it). NO protocol change.
- Deployment: edge-only, no ECS service — the operator machine must pull/rebuild the local edge (Electron client) for the fix to take effect; then re-run `/comment <昵称> --join`.
- Real-machine acceptance rolls into `docs/real-machine-acceptance-backlog.md` 簇 32 (the join now progresses past observation on a non-EN/ZH group).
