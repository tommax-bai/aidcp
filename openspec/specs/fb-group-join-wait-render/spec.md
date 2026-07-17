# fb-group-join-wait-render Specification

## Purpose
TBD - created by archiving change fb-group-join-wait-render. Update Purpose after archive.
## Requirements
### Requirement: The edge waits for the group page to render a decisive signal before judging, bounded and network-tolerant

The edge group-join observation SHALL NOT decide from a single observation taken after a fixed post-navigation delay. After navigating to the group, it MUST poll — re-observing at a bounded interval — until a DECISIVE signal is present (the Join button is found and clickable, OR an already-member / login-required / captcha / questionnaire / pending / any classified membership CTA signal), OR a bounded readiness timeout elapses. This makes observation tolerant of Facebook's variable render/network timing (a page that renders its header + Join button several seconds after navigation is observed once it is actually there). On timeout with no decisive signal, the edge MUST return the last observation honestly (the cloud role decides, fail-closed) and MUST NOT report a fabricated success. Cookie-consent and login/captcha overlays MUST be handled on each poll iteration since they can appear at any time.

#### Scenario: Join button that renders after the fixed-delay window is still observed
- **WHEN** the group page renders its header and Join button several seconds after navigation (longer than any fixed settle)
- **THEN** the edge keeps polling and observes the Join button once it renders, reporting it (with coordinates) to the cloud judge — rather than reporting an empty/no-CTA observation from a premature single look

#### Scenario: Timeout with no decisive signal is honest, never fake success
- **WHEN** the readiness timeout elapses and no decisive signal (Join button / member / login / captcha / questionnaire / pending / classified CTA) has appeared
- **THEN** the edge returns the last observation to the cloud judge (which fail-closes) and MUST NOT report `ok`/joined

#### Scenario: A decisive blocking or membership signal short-circuits the wait
- **WHEN** a login/captcha overlay, an already-member signal, or a questionnaire/pending gate is observed during polling
- **THEN** the edge returns immediately with that honest outcome without waiting out the full timeout

### Requirement: The observation reports render-readiness diagnostics

The edge group-join observation SHALL include the count of visible action nodes and the document ready state, so that a no-CTA or timeout outcome recorded in the join audit is diagnosable (distinguishing "page was still loading" from "page loaded but genuinely no Join affordance").

#### Scenario: Audit shows loading state on a no-CTA observation
- **WHEN** an observation reports no Join CTA
- **THEN** the recorded observation includes the visible action-node count and document ready state, so an operator can tell whether the page had finished rendering

### Requirement: The click pass SHALL reuse the target group page the observe pass already established, instead of reloading it

Facebook group-join is **two edge invocations against the same group URL** — an observe-only pass, then a `click=true` pass — because the cloud deliberately **releases the edge task lease between them** so the browser is not held during the pre-click LLM judge. The edge MUST NOT let that two-pass protocol cost two full page loads: on the `click=true` pass, when the browser is **already sitting on the target group page**, the edge SHALL skip navigation (and its post-navigation settle) and proceed directly to the readiness poll and the click.

- **The observe pass SHALL ALWAYS navigate — it MUST NOT reuse the current page under any condition.** This is load-bearing and NOT an oversight: the observe pass is the flow's **only** page-establishment and **only** fault-recovery mechanism. If both passes could reuse, a page stuck in a bad state *at the target URL* would make every retry skip navigation, re-observe the same bad page, and report `not_ready` forever — a livelock that ends only when the attempt counter marks the membership permanently `failed`. Keeping the observe pass unconditional guarantees every logical join attempt begins with one clean load, so `not_ready` retries always recover.
- **The on-target predicate SHALL be strict, and its failure direction SHALL be "navigate".** The edge SHALL treat the browser as on-target ONLY when the current URL's origin equals the canonical desktop origin AND its path is exactly the canonical group root path (a trailing slash tolerated). Query and fragment MUST be ignored (a group root carrying `?ref=…` is still the group root). Any other surface — a mobile-host variant of the same group (a different DOM the observation script is not written for), a group sub-surface such as `/about` or a post permalink, an unparseable or unavailable URL, or any doubt whatsoever — MUST evaluate to not-on-target and therefore navigate. The predicate MUST NOT be derived by canonicalizing the *current* URL, since canonicalization collapses exactly the distinctions that make reuse unsafe.
- **Readiness remains the sole authority and SHALL NOT be skipped.** Skipping navigation SHALL skip only the load, never the readiness poll: an already-hydrated target page satisfies the poll on its first iteration (that is the saved round), while a bad-state page polls out to `not_ready` and hands recovery to the observe pass. Every existing gate — consent overlay, login, captcha, questionnaire, pending, scope resolution, the member-signal contradiction guard — SHALL keep its position and semantics, so reuse introduces no new silent-success surface.
- The click pass SHALL keep its pre-click hydration settle regardless of whether it navigated.

#### Scenario: The click pass reuses the page the observe pass just established
- **WHEN** the observe pass has navigated to the group root and returned `observation_only`, the lease is released for the pre-click judge and reacquired, and the `click=true` pass finds the browser still on that exact group root
- **THEN** the edge does NOT navigate, runs the readiness poll (which is satisfied immediately on the already-hydrated page), and clicks Join — the group page is fully loaded exactly ONCE for the whole join

#### Scenario: The observe pass always reloads, so a bad-state page can never livelock
- **WHEN** the page is stuck in a bad state at the target group URL and the click pass reuses it, observes nothing decisive, and reports `not_ready`
- **THEN** the cloud retries after its transient backoff and the retry's observe pass navigates unconditionally, replacing the bad page with a clean load — the flow recovers instead of re-observing the bad page forever

#### Scenario: Anything but the exact group root makes the click pass navigate
- **WHEN** the `click=true` pass finds the browser on a mobile-host variant of the group, on a group sub-surface such as `/about` or a post permalink, on an unrelated page because another task took the browser during the lease gap, or on a URL that cannot be read or parsed
- **THEN** the edge navigates to the canonical group root exactly as it does today, and no reuse occurs

#### Scenario: A group root carrying tracking query parameters still counts as on-target
- **WHEN** the `click=true` pass finds the browser on the target group root with a query string or fragment appended (for example a `ref` parameter added by Facebook)
- **THEN** the edge treats it as on-target and reuses the page, because query and fragment do not change which surface is loaded

