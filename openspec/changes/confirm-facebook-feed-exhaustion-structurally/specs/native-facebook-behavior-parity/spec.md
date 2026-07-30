## MODIFIED Requirements

### Requirement: Native Feed scanning preserves stateful continuation truth

The Native Facebook session SHALL distinguish validated cards, visible unreportable articles, loading, explicit empty, and exhausted Feed states. A validated Feed identity SHALL be projected from the declared identity kind: absent or `permalink` kind requires the existing Facebook content-URL validation and uses the canonical Facebook post identity extracted by the existing permalink parser; explicit `content_ref` kind requires the existing exact `aidcp:facebook-group-feed-post:v1:<64 lowercase hex>` format and retains its type in the identity key. Native MUST NOT infer the identity kind from the value's shape. A malformed or kind/value-mismatched card has no validated identity.

Native SHALL use that same typed projection for `page.cards` output, session seen deduplication, settle/bottom-confirmation identity vectors, and the command-local non-empty-feed witness. It SHALL report an unseen validated identity, including `content_ref`, before it may classify the viewport as exhausted. Only after the current observation contains no unseen validated card may Native consider the five-sample confirmation. The session seen set SHALL use the typed identity key, so a previously reported card is filtered consistently without a permalink-only side path. Existing `content_ref` capability and lifetime limits remain unchanged: it is session-scoped, list-surface/document-generation-bound, not persisted, not navigable, and not eligible for cross-session deduplication.

Native SHALL use loading-aware card-set settling, continue downward for up to the established bounded rounds when visible articles lack a validated identity, filter validated identities already reported by that session, and report a previously non-empty canonical home Feed as `feed_exhausted` only after the fixed five-sample no-growth, near-bottom, same-document, no-new-card confirmation evidence. Near-bottom SHALL mean no more than one actual scrolling-container viewport of remaining distance; exact mathematical bottom is not required, and a nested feed scroller SHALL use its own client height rather than the browser-window height. It MUST NOT authorize or perform a Reels transition merely because the current viewport has no reportable permalink.

The fixed confirmation samples SHALL occur at `t=0 / 5 / 7.5 / 10 / 12.5s`. Every sample SHALL remain on the same canonical home URL, the same non-zero document time origin, and the same document generation; keep `document_age_ms` from moving backward relative to the immediately preceding sample; remain non-loading and near-bottom using the actual scroll viewport; grow no more than 100px relative to the initial sample (`>100px` invalidates); and retain the same ordered validated Feed identity vector. Only the fifth valid structural sample SHALL confirm exhaustion. The adapter MAY retain `explicit_end` as bounded observation and diagnostic evidence, but a missing or unstable marker MUST NOT block structurally confirmed exhaustion only when the commanded list context began on home and this command observed a validated identity on the same home URL and document time origin. A `content_ref` may establish that witness only inside the command, URL, and document-time-origin window that observed it; a later command or replacement document MUST NOT inherit it. Marker-free structural confirmation MUST NOT extend to search/group contexts or to a search/group command redirected to home before confirmation.

The bounded terminal taxonomy SHALL be identical for the startup Feed scan and for every Cloud-commanded Feed scroll. When a commanded scroll exhausts its bounded rounds without producing a reportable card, the Native session SHALL apply the same evidence ladder the startup scan applies before falling back to a bare no-target result: a confirmed home surface carrying physical card evidence, not loading and not blocked, SHALL be reported as the present-but-unreportable list state; an otherwise confirmed empty home SHALL be reported as the explicit empty list state. Only when neither ladder rung holds MAY the session return the loading / continuation-unconfirmed / no-target classification. A commanded scroll MUST NOT return a terminal result that leaves the account on the same viewport with no Cloud-consumable observation, because the sole remaining recovery would be the Cloud idle watchdog.

Loading-aware card-set settling SHALL treat a zero-card viewport as unsettled. The settle loop MAY return early only once it has observed at least one extractable card in a stable, non-loading sample; a viewport that is merely stable at zero cards SHALL keep polling until its bounded budget is spent, so that lazy-loaded batches have time to render between scrolls.

This requirement adds no new receipt reason code and no new protocol field: structurally confirmed exhaustion reuses `feed_exhausted`, while the present-but-unreportable and explicit-empty observations reuse the existing zero-card `page.cards` list states that Cloud already consumes.

#### Scenario: Visible unreportable first viewport continues in Feed

- **WHEN** the initial Facebook Feed viewport contains visible hydrated articles but no trusted canonical permalink and a later bounded viewport contains a canonical card
- **THEN** Native scrolls within Feed, reports the later card, and does not emit explicit empty or navigate to Reels

#### Scenario: Loading zero-card viewport is not empty

- **WHEN** no canonical card is currently extractable and the Feed has an accessibility loading signal
- **THEN** Native waits within the bounded settle budget and, if still loading at the deadline, returns a retryable loading/no-target result rather than an empty card batch

#### Scenario: Recycled cards are not reported as new

- **WHEN** virtualized Feed scrolling renders permalink or `content_ref` typed identities already reported in the same Native session
- **THEN** Native filters those identities and continues the bounded search for new cards

#### Scenario: A fresh validated content reference is reported before exhaustion

- **WHEN** a Feed probe contains a card explicitly typed as `content_ref`, its value passes the existing strict prefix-and-digest validator, and its typed identity is not in the session seen set
- **THEN** Native emits that card through the normal `page.cards` path, records the same typed key in session seen-state, and does not return `feed_exhausted` from that observation

#### Scenario: A seen content reference remains command-local non-empty evidence

- **WHEN** the same valid `content_ref` is observed again by a home scroll command on the same URL and non-zero document time origin after session deduplication filters it from new-card output
- **THEN** Native MAY use it in that command's validated identity vector and non-empty witness
- **AND THEN** Native reports exhaustion only if no unseen identity remains and the complete five-sample structural window succeeds

#### Scenario: Malformed or mismatched typed identity fails closed

- **WHEN** a card's declared kind and value disagree, or a declared `content_ref` fails the exact existing prefix, digest-length, or lowercase-hex validation
- **THEN** Native neither reports nor records that value, excludes it from structural identity vectors, and does not let it establish an exhaustion witness

#### Scenario: Home exhaustion requires the complete structural schedule

- **WHEN** a commanded scroll whose list context began on home has observed a validated Feed identity on the same home URL and document time origin and all five fixed samples retain that non-zero origin and URL, keep adjacent document age nondecreasing, remain non-loading and within one actual scroll viewport of the bottom, grow no more than 100px, and retain the same ordered validated identity vector
- **THEN** Native reports `feed_exhausted` only after the `t=12.5s` sample, whether or not `explicit_end` is present
- **AND THEN** Native does not report exhaustion after any of the first four samples

#### Scenario: Structural invalidation remains continuation

- **WHEN** loading, growth above 100px, any ordered validated-identity-vector change, navigation, document-time-origin change, a backward adjacent document-age reset, generation change, surface change, or departure from near-bottom occurs before the fifth sample
- **THEN** Native does not report `feed_exhausted` from that window and retains the existing bounded continuation or zero-card evidence path

#### Scenario: A content-reference witness cannot cross a command or document

- **WHEN** a valid `content_ref` was observed only by a prior command, another URL, or another document time origin and the current command has observed no validated identity in its current home document
- **THEN** Native does not reuse that witness and MUST NOT report marker-free `feed_exhausted`

#### Scenario: Commanded scroll exhausting its rounds over physical cards reports present-but-unreportable

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, and the final observation is a confirmed home surface that still carries physical card evidence, is not loading, and is not login/captcha/consent blocked
- **THEN** Native reports a zero-card `page.cards` observation carrying the present-but-unreportable list state, exactly as the startup Feed scan does, and does not return a bare no-target receipt

#### Scenario: Commanded scroll exhausting its rounds over a confirmed empty home reports explicit empty

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, the final observation carries no physical card evidence, and the existing stable explicit-empty confirmation succeeds
- **THEN** Native reports a zero-card `page.cards` observation carrying the explicit empty list state and does not return a bare no-target receipt

#### Scenario: Blocked or non-home exhaustion keeps today's honest failure

- **WHEN** a commanded scroll exhausts its rounds while the final observation is loading, login-like, captcha-like, consent-blocked, off the home surface, or carries no physical card evidence and fails explicit-empty confirmation
- **THEN** Native returns the existing honest failure classification, reports neither present-but-unreportable nor explicit empty, and never transitions to Reels through the marker-free home path

#### Scenario: Zero-card viewport is not settled by stability alone

- **WHEN** two consecutive settle samples of a non-loading viewport both extract zero cards
- **THEN** Native keeps polling until the bounded settle budget is spent instead of returning immediately, so a lazy-loaded batch arriving later in the budget is still observed

#### Scenario: A settled non-empty card set still returns early

- **WHEN** two consecutive settle samples of a non-loading viewport extract the same non-empty card set
- **THEN** Native returns that sample immediately without spending the remainder of the settle budget
