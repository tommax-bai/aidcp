## ADDED Requirements

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
