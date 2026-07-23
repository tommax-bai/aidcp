## Why

The customer-facing value dashboard designed for Xiaohongshu was implemented behind a separate “内容首页”, while selecting a Xiaohongshu environment still lands on the older runtime-oriented page. This hides the product's core value and makes the newly added schedule card look like the whole redesign, instead of one part of an account-level workspace.

## What Changes

- Make the full value dashboard the primary landing view when a customer selects a Xiaohongshu environment.
- Keep the established dashboard structure together: value summary, compact AI work panel, live work process, featured inspiration lineage, reference content, customer content, honest empty/error states and expandable runtime details.
- Integrate the account schedule as a compact dashboard section instead of presenting it as the only new environment-home experience.
- Preserve the July 22 prototype's visual-first content hierarchy: prominent source/output covers, visible engagement evidence, clear lineage actions, portrait reference cards and a purposeful idle work state instead of compressing the dashboard into administrative data rows.
- Remove “内容首页” as a second first-level destination. “精选灵感” and “我的内容” remain deeper content views and return to the environment dashboard.
- Reuse the existing environment lifecycle, browser controls, customer-auth reads, request-epoch isolation, new-user start guide and content controllers; do not create duplicate running or content state.
- Preserve the existing legacy environment landing experience for Facebook, WeChat Channels and unknown platforms.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `client-xhs-content-value-home`: Move the Xiaohongshu value home from the separate content workspace to the selected environment's primary landing view and define its relationship with deeper content pages and the account schedule.
- `edge-companion-ui`: Make the full dashboard, its lifecycle controls and responsive height/overflow rules part of the Xiaohongshu environment workspace while retaining strict platform isolation.

## Impact

- Edge renderer structure, navigation, styles and focused static/controller tests.
- Existing `content-home` controller and customer-auth endpoints are reused; no new Cloud API, protocol v2 change, database migration or risk/publish behavior is introduced.
- The existing account-schedule controller remains environment-scoped and is composed into the dashboard.
- Edge source delivery does not build or install a desktop package.
