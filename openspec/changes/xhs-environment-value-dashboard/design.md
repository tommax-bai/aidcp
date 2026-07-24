## Context

The Edge shell currently has two first-level surfaces for one selected Xiaohongshu environment:

1. `legacy-workspace`, which owns environment presence, runtime guidance, daily progress and lifecycle controls;
2. `content-workspace`, whose `home` page owns the customer-value dashboard designed in the July 22 prototype.

The value dashboard is already connected to environment-scoped customer-auth data, process-message projection, honest empty states and shared lifecycle actions. The problem is information architecture rather than missing widgets: customers land on the older runtime surface and must deliberately open “小红书内容 / 内容首页” before they can see the product's value.

The newly implemented schedule entry exposed this mismatch because it was placed on `legacy-workspace` by itself. The correction must compose the full dashboard and the schedule at the environment level without duplicating controllers or weakening platform/env isolation.

## Goals / Non-Goals

**Goals:**

- Make the full value dashboard the default body of a selected Xiaohongshu environment.
- Keep the existing environment rail, identity, blocking notices and authoritative lifecycle state.
- Reuse one copy of every dashboard DOM node and controller.
- Keep “精选灵感” and “我的内容” as deeper pages that return to the environment dashboard.
- Place account schedule in the dashboard as a secondary, compact, account-level module.
- Preserve all independently designed loading, empty, error and content states.
- Preserve a 255px desktop ceiling for the expanded work panel, use a compact idle frame, and keep supported-width overflow guarantees.

**Non-Goals:**

- Do not redesign the July 22 dashboard, replace its copy or reduce its sections to summary cards.
- Do not create a new Cloud endpoint, database table, protocol command or renderer-owned business state.
- Do not alter Facebook, WeChat Channels or unknown-platform environment homes.
- Do not build or release an Edge installer.

## Decisions

### 1. The environment workspace owns the value-home DOM

The single `content-home-view` DOM subtree will move from `content-workspace` into a Xiaohongshu-only dashboard container inside `legacy-workspace`. The existing IDs are retained so the established content-home controller, work-process renderer, editor transitions and tests keep one source of truth.

Alternative: automatically open `content-workspace/home` whenever an environment is selected. This would preserve the visual result but not fix the information architecture: the page would still be a separate content destination with a second “内容首页” level and ambiguous back/close behavior.

Alternative: duplicate a compact dashboard in `legacy-workspace`. This would create two caches, two task timelines and two lifecycle projections, and would inevitably drift.

### 2. Xiaohongshu replaces the old body; other platforms keep it

When the selected platform is exactly `xiaohongshu`, the renderer shows the environment dashboard and suppresses the old presence/runtime-guidance/daily-summary body that duplicates work state and metrics. Environment-level blocking notices, login guidance and failure evidence remain available above the dashboard.

For Facebook, WeChat Channels and unknown platforms, the new dashboard is absent and the existing environment home remains unchanged. A platform/env request epoch continues to discard late Xiaohongshu responses after a switch.

### 3. Deep content navigation remains a workspace, without a second home

`content-workspace` keeps the existing curated library, inspiration detail, create confirmation, draft list, review and editor surfaces. Its first-level navigation becomes “精选灵感 / 我的内容”; there is no “内容首页” tab.

Dashboard actions open the corresponding deep page. Closing or backing out of a root deep page returns to the selected environment dashboard and restores its scroll position. Nested page back behavior remains within the existing content page stack.

### 4. Schedule is composed, not promoted above the dashboard

The existing environment-scoped schedule entry is moved into the dashboard near the value overview, before the work panel. It keeps its fixed customer-auth path, honest current/next/empty/error states and environment schedule detail page.

Returning from schedule restores the dashboard and its scroll position. Schedule loading or failure cannot hide or block the other dashboard sections.

### 5. Existing data and lifecycle ownership stay unchanged

The content-home controller continues to compose curated content, drafts, tasks and daily usage from customer-auth HTTP. Events only invalidate/refetch. The schedule controller remains independent of browser/core/WebSocket state.

Runtime-detail buttons delegate the existing browser and lifecycle controls. The first-environment start guide targets the visible dashboard lifecycle action while preserving the shared guide owner and the existing save-before-start behavior.

### 6. Layout follows the prototype's reading order

The primary order is:

1. value overview;
2. compact account schedule;
3. AI work panel and real-time process;
4. featured inspiration lineage;
5. reference content and customer content;
6. expandable runtime details.

The dashboard uses the existing content-home responsive styles inside the environment content width. At narrow widths, summaries and paired sections stack without horizontal overflow. The AI work panel retains its desktop 255px maximum and same-size completed process text.

### 7. Content evidence remains visual-first

The environment move must not replace the July 22 content cards with compact administrative rows. The featured lineage keeps two substantial visual panes with a clear source-to-output relationship, engagement evidence and direct actions. The reference section keeps portrait-led cards so customers can recognize collected content before reading metadata; customer drafts remain compact because their status is the primary scan target.

When an upstream item has no usable image URL, the renderer uses a deterministic, low-saturation editorial cover derived from the item identity. It must not display a large flat gray block or imply that a real image was collected. The fallback is decoration, while title, source and engagement values remain the evidence.

The active and waiting work panel uses a stable 240px frame. When the environment is not started or no task exists, the panel contracts to a desktop frame no taller than 168px while retaining the real start/inspiration action, the non-publishing boundary and a compact preview of the stages that will appear after a task starts. The idle process preview changes from a large centered empty composition to a horizontal explanation so unused space does not push content evidence below the first screen. The account schedule remains a quiet entry row and must not visually outweigh the featured lineage or work panel.

### 8. Responsive hierarchy follows the environment content container

The dashboard is embedded beside the environment rail, so viewport media queries do not describe its actual usable width. The dashboard establishes an inline-size container and adapts the featured lineage and lower content grid from that container. At medium environment widths, the source and output panes stack in reading order and the reference/customer-content sections become full-width sections instead of shrinking all typography and evidence into desktop columns.

The responsive change preserves the same information architecture, a 240px active desktop frame and a no-taller-than-168px idle desktop frame. It increases the minimum readable size of customer-facing titles, body copy, evidence chips and actions, keeps empty-state panels visually commensurate with populated content, and only stacks the work panel at genuinely narrow content widths.

### 9. The prototype defines one visual state matrix

The July 22 HTML demo is not only a populated-page reference. Its populated, loading, empty, error, active, waiting and collapsed compositions define one state matrix for the environment dashboard. The renderer keeps the same section shells while data changes: a failed or empty lower section does not resize the whole page, a missing draft does not collapse the featured relationship, and a running process does not replace the stable 240px active work frame. An idle process is intentionally shorter because it contains no timeline and must leave room for the first value-evidence section in the initial viewport.

Featured status badges size to their text instead of stretching across the copy column. The source and output covers remain substantial, with enough central relationship space to explain provenance. Reference cards keep a portrait-led top-aligned reading rhythm and expose the truthful “可创作” or “已创作” state at scan level. Customer drafts remain compact status rows.

Reference and customer-content placeholders are section-specific 218px cards with restrained radial emphasis. Loading and continuing-search states use an accessible live indicator; idle states use a static neutral indicator; failures expose retry without being painted as empty data. Dynamic work states keep stage-specific wording such as “判断中...” and “判断完成”, use equal text sizing for current and completed rows, type only the current summary character by character, and distinguish waiting from running without showing elapsed time.

Visual validation uses the reported environment content width as well as narrow container widths. Review covers populated, mixed populated/empty, all-empty, loading/error, active, waiting and collapsed states; it compares section proportions and whitespace, not only the absence of overflow.

## Risks / Trade-offs

- **[Existing controller assumes content workspace is open]** → Separate “dashboard visible” from “deep workspace active” and add focused tests for initial selection, reload, switching and late responses.
- **[Old and new environment bodies both remain visible]** → Drive a single platform-derived workspace class and test the exact visible/hidden section set for Xiaohongshu versus other platforms.
- **[Back navigation loops between two homes]** → Remove the home tab and define dashboard as the sole root; root close always exits to it.
- **[Lifecycle guide points to a hidden legacy button]** → Keep the shared lifecycle button as command owner but make the dashboard proxy the visible guide target and test first-use start.
- **[Schedule failure degrades the whole dashboard]** → Keep its controller and failure state isolated; dashboard content requests and rendering proceed independently.
- **[Missing media makes the value page look broken]** → Render a clearly decorative deterministic cover fallback without fabricating a source image or engagement evidence.
- **[Viewport is wide while the embedded environment area is narrow]** → Use container queries owned by the Xiaohongshu dashboard and test the actual environment content width rather than relying on the outer Electron window.

## Migration Plan

1. Land the renderer-only move additively on Edge master; Cloud APIs are already compatible.
2. Validate focused navigation/platform/state tests, the full Edge suite and typecheck.
3. Visually inspect populated and empty dashboard states at desktop and narrow supported widths.
4. Merge/push Edge and control defaults. Do not build or install a desktop package without separate authorization.
5. Rollback is one Edge commit: restore `content-home-view` to `content-workspace` and the old home tab; no persisted data or Cloud rollback is involved.

## Open Questions

None. The user's clarification resolves the main information-architecture decision: the whole July 22 panel belongs to the selected Xiaohongshu environment home.
