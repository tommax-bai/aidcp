## Context

The Facebook Edge reader currently treats `[role="feed"]` and top-level `[role="article"]` elements as the only feed representation. Live CDP comparison across local AdsPower environments showed a second, locale-independent structure: the page contains hydrated story-message nodes and author headings inside ordinary div containers, while `role="feed"` is absent and the only `role="article"` nodes are empty shells. The browser therefore has readable posts but the current surface probe and card scan both return zero.

Card detection is used at two points: the initial/scroll feed scan that emits `page.cards`, and later in-feed target resolution for deep reading and natural interaction. Fixing only the first point would report cards that later commands cannot resolve. The shared path must also preserve the existing canonical post identity boundary: some lightweight cards expose only photo or video resource IDs, which are not reliable post IDs.

## Goals / Non-Goals

**Goals:**

- Detect the semantic and lightweight layouts using locale-neutral DOM structure.
- Share top-level card discovery and closest-card lookup across feed scanning and in-feed target resolution.
- Keep the existing canonical post URL whitelist as the identity gate for reporting and acting.
- Preserve all semantic-layout behavior and fail-closed safety checks.

**Non-Goals:**

- Treating arbitrary photo/video `fbid` values as post identities.
- Adding localized text selectors or account-specific selectors.
- Changing cloud pacing, quotas, protocol payloads, risk state, or Facebook write authorization.
- Claiming compatibility for unrelated detail-page or composer layouts.

## Decisions

### Use a shared injectable feed-layout helper

`post-identity.ts` will expose one self-contained browser-side helper string used by both `feed-reader.ts` and the existing target helpers. It will provide top-level-card discovery and closest-card lookup. This prevents the scan and action paths from drifting.

The semantic path remains first and unchanged when a real `[role="feed"]` exists. The fallback path runs only when that semantic container is absent.

Alternative considered: duplicate a fallback selector in each executor. Rejected because a card could then be reported by one definition but unresolved or attributed to another card by a different definition.

### Discover lightweight cards from story-message anchors and structural boundaries

The fallback starts from visible story-message nodes (`data-ad-comet-preview`, `data-ad-preview`, or `data-ad-rendering-role="story_message"`) inside the main document region. For each seed it chooses the smallest visible ancestor that contains the seed and at least one linked author heading; multiple headings are valid for location/co-author headers. Results are deduplicated and nested results are reduced to top-level card roots.

This uses stable accessibility/data attributes and containment rather than language-specific labels such as Vietnamese or Chinese menu text.

Alternative considered: CSS class chains or localized timestamps. Rejected because class names are generated and the observed timestamp link is obfuscated and not a reliable permalink.

### Separate surface recognition from reportable identity

A structurally valid lightweight card is enough to establish that the current home/search page is a feed surface. A card is reportable or actionable only when the existing canonical-post parser finds a whitelisted post-shaped URL within that exact card. Thus a feed made solely of ambiguous photo/video cards remains on-page and continues bounded scrolling, but it does not fabricate `page.cards` or action targets.

Alternative considered: promoting any `photo/?fbid=` or video resource ID to a post ID. Rejected because those identifiers can name media rather than the enclosing post and would violate attribution guarantees.

### Preserve exact-card scoping for reads and actions

Existing target-helper names remain available to callers, but their implementation delegates to the multi-layout helper. Canonical identity links, message extraction, expand controls, observations, and action buttons remain scoped to the resolved card. The fallback must not broaden a target into the page or a neighboring post.

## Risks / Trade-offs

- **[Facebook changes the fallback data attributes]** → Keep multiple observed story-message attributes, semantic-first behavior, bounded no-target handling, and CDP diagnostics so unknown layouts fail closed.
- **[A story-message node in a non-feed region resembles a card]** → Activate fallback only without a semantic feed, require the expected home/search surface plus a visible message and one linked author heading, and still require canonical identity before reporting or acting.
- **[Some real lightweight posts lack canonical links]** → Skip them honestly and continue scrolling; do not weaken identity to raise counts.
- **[Shared helper changes affect interaction targeting]** → Add fixture tests for both layouts and retain exact-card identity/containment checks before any read or action.

## Migration Plan

1. Deploy the Edge source update to `dev`; no data or protocol migration is required.
2. Validate both fixture layouts, then use CDP against the two local AdsPower profiles to confirm structural detection and canonical-card extraction without performing Facebook interactions.
3. Roll back the Edge commit if semantic-layout regression or cross-card attribution is observed.

## Open Questions

None for this scoped change. Additional Facebook layouts should be captured as separate fixtures before extending the detector.
