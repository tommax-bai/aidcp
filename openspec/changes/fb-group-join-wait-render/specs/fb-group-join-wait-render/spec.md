## ADDED Requirements

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
