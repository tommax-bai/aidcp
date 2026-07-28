## MODIFIED Requirements

### Requirement: Native Feed scanning preserves stateful continuation truth

The Native Facebook session SHALL distinguish canonical cards, visible unreportable articles, loading, explicit empty, and exhausted Feed states. It SHALL use loading-aware card-set settling, continue downward for up to the established bounded rounds when visible articles lack trusted permalinks, filter canonical identities already reported by that session, and report `feed_exhausted` only after the established no-growth, near-bottom, consecutive-confirmation evidence. It MUST NOT authorize or perform a Reels transition merely because the current viewport has no reportable permalink.

The bounded terminal taxonomy SHALL be identical for the startup Feed scan and for every Cloud-commanded Feed scroll. When a commanded scroll exhausts its bounded rounds without producing a reportable card, the Native session SHALL apply the same evidence ladder the startup scan applies before falling back to a bare no-target result: a confirmed home surface carrying physical card evidence, not loading and not blocked, SHALL be reported as the present-but-unreportable list state; an otherwise confirmed empty home SHALL be reported as the explicit empty list state. Only when neither ladder rung holds MAY the session return the loading / continuation-unconfirmed / no-target classification. A commanded scroll MUST NOT return a terminal result that leaves the account on the same viewport with no Cloud-consumable observation, because the sole remaining recovery would be the Cloud idle watchdog.

Loading-aware card-set settling SHALL treat a zero-card viewport as unsettled. The settle loop MAY return early only once it has observed at least one extractable card in a stable, non-loading sample; a viewport that is merely stable at zero cards SHALL keep polling until its bounded budget is spent, so that lazy-loaded batches have time to render between scrolls.

This requirement adds no new receipt reason code and no new protocol field: the present-but-unreportable and explicit-empty observations reuse the existing zero-card `page.cards` list states that Cloud already consumes.

#### Scenario: Visible unreportable first viewport continues in Feed

- **WHEN** the initial Facebook Feed viewport contains visible hydrated articles but no trusted canonical permalink and a later bounded viewport contains a canonical card
- **THEN** Native scrolls within Feed, reports the later card, and does not emit explicit empty or navigate to Reels

#### Scenario: Loading zero-card viewport is not empty

- **WHEN** no canonical card is currently extractable and the Feed has an accessibility loading signal
- **THEN** Native waits within the bounded settle budget and, if still loading at the deadline, returns a retryable loading/no-target result rather than an empty card batch

#### Scenario: Recycled cards are not reported as new

- **WHEN** virtualized Feed scrolling renders canonical post identities already reported in the same Native session
- **THEN** Native filters those identities and continues the bounded search for new cards

#### Scenario: Exhaustion requires bounded structural evidence

- **WHEN** a scroll command finds no new canonical cards
- **THEN** Native reports `feed_exhausted` only after document height stops growing, the page is near the bottom, and that state is confirmed in consecutive rounds

#### Scenario: Commanded scroll exhausting its rounds over physical cards reports present-but-unreportable

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, and the final observation is a confirmed home surface that still carries physical card evidence, is not loading, and is not login/captcha/consent blocked
- **THEN** Native reports a zero-card `page.cards` observation carrying the present-but-unreportable list state, exactly as the startup Feed scan does, and does not return a bare no-target receipt

#### Scenario: Commanded scroll exhausting its rounds over a confirmed empty home reports explicit empty

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, the final observation carries no physical card evidence, and the existing stable explicit-empty confirmation succeeds
- **THEN** Native reports a zero-card `page.cards` observation carrying the explicit empty list state and does not return a bare no-target receipt

#### Scenario: Blocked or non-home exhaustion keeps today's honest failure

- **WHEN** a commanded scroll exhausts its rounds while the final observation is loading, login-like, captcha-like, consent-blocked, off the home surface, or carries no physical card evidence and fails explicit-empty confirmation
- **THEN** Native returns the existing honest failure classification, reports neither present-but-unreportable nor explicit empty, and never transitions to Reels through this path

#### Scenario: Zero-card viewport is not settled by stability alone

- **WHEN** two consecutive settle samples of a non-loading viewport both extract zero cards
- **THEN** Native keeps polling until the bounded settle budget is spent instead of returning immediately, so a lazy-loaded batch arriving later in the budget is still observed

#### Scenario: A settled non-empty card set still returns early

- **WHEN** two consecutive settle samples of a non-loading viewport extract the same non-empty card set
- **THEN** Native returns that sample immediately without spending the remainder of the settle budget
