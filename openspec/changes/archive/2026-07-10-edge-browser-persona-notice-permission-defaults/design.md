## Context

The edge desktop app already receives authoritative per-environment `auth`, `cloud`, and `personaBound` projections and already has a persona generate/persist bridge. The controlled AdsPower page runs in a separate Chrome process, so Electron's permission handler and renderer UI cannot directly surface state inside that page. Electron can, however, route a local stdin command to the correct edge child, and that child already owns the page CDP session.

AdsPower `user/create` accepts `fingerprint_config.location` values including `block`, while `location_switch='1'` independently keeps fingerprint location aligned with proxy IP. Existing profiles are intentionally protected by a narrow `user/update` wrapper that only changes proxy configuration.

## Goals / Non-Goals

**Goals:**

- Make unresolved persona setup visible in Electron, as a desktop notification, and inside the correct controlled browser page.
- Keep browser-page UI isolated, idempotent, removable, and resilient across top-frame navigation and CDP reconnect.
- Preserve the requested tone/content preference editor and custom interest inputs.
- Set new AdsPower profiles to deny geolocation prompts while preserving IP-based fingerprint location.

**Non-Goals:**

- Do not render the full persona wizard inside third-party pages.
- Do not add an edge-cloud protocol message or change persona persistence.
- Do not modify existing AdsPower profile fingerprints through the proxy-only `user/update` path.
- Do not auto-allow camera, microphone, geolocation, or other sensitive browser permissions.

## Decisions

**D1: Electron main synchronizes the browser-page reminder for every environment.** The main process already owns each child handle and receives all environment status updates, including environments that are not selected in the renderer. It derives an active/inactive reminder from `logged in + connected + !personaBound` and sends a local `browser.personaNotice` command to that environment's child. This avoids selected-environment leakage and does not expand the edge-cloud protocol.

**D2: The edge child injects an isolated Shadow DOM notice through CDP.** The core keeps the desired notice state and applies an idempotent `Runtime.evaluate` expression. It reapplies after top-frame navigation and CDP reconnect, removes the host when inactive, and exposes no site-facing data or selectors beyond one namespaced host. The notice only tells the operator to return to AIDCP Edge; the full editor remains in Electron.

**D3: Existing persona generation remains a flat keyword contract.** Tone, category title, selected interests, and custom interests are collected into the existing bounded `keywordSelections` array. This avoids cloud and protocol changes while preserving category context.

**D4: New AdsPower profiles use `location='block'` with `location_switch='1'`.** `location` controls the permission prompt default; `location_switch` controls the fingerprint's IP-derived location. Both are required. Existing profiles are left unchanged because broadening `user/update` would weaken the proxy-only write boundary.

**D5: Permission denials remain honest and visible.** Electron's own session denies permissions outside the small allowlist and emits a throttled notification. AdsPower handles the external browser's geolocation default at profile creation. Neither path reports successful authorization.

## Risks / Trade-offs

- [Injected UI could pollute page automation] -> Use a namespaced host with a closed visual boundary in Shadow DOM and avoid site classes, roles, or text in the light DOM.
- [Navigation removes the notice] -> Keep desired state in the edge child and reapply after top-frame navigation and CDP reconnect.
- [Repeated status updates spam stdin] -> Main caches the last desired reminder payload per environment and sends only state changes; core injection is idempotent.
- [Blocking geolocation changes a site feature] -> Limit the default to newly created profiles and preserve proxy-IP fingerprint location; future exceptions require an explicit, scoped policy.
- [Existing profiles continue to prompt] -> Document this migration boundary and avoid weakening `user/update`; operators can recreate or manually update profiles if needed.

## Migration Plan

No data migration is required. Build and publish a new edge desktop package. New profiles receive the AdsPower permission default; existing profiles are unchanged. Rollback is a package rollback plus reverting the edge commit; profiles already created with `location='block'` retain that AdsPower setting.

## Open Questions

None.
