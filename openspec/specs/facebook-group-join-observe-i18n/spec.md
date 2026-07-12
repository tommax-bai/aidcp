# facebook-group-join-observe-i18n Specification

## Purpose
TBD - created by archiving change facebook-group-join-observe-i18n. Update Purpose after archive.
## Requirements
### Requirement: The edge reports Join-button state across locales, never swallowing a non-EN/ZH Join button

The edge group-join observation SHALL recognize the group's primary membership call-to-action (Join / Joined / Pending) across locales, not only English and Chinese. It MUST classify by matching the button label against a multilingual keyword set, checking the joined and pending senses before the join sense so a "joined" label that contains the join verb (e.g. Vietnamese "Đã tham gia" which contains "tham gia") is classified as joined, not join. The pending sense MUST recognize the **cancel-request button form**, not only pending state words: on an already-pending group the primary control reads a cancel-request label (e.g. Chinese 「取消请求」), which MUST be classified as pending so `pendingRequest` is set true and the state is reported honestly. Pending keyword coverage MUST include the cancel-request forms for the locales the system already covers (the recognizer already carries English `cancel request`, Vietnamese `hủy yêu cầu`, Spanish `cancelar solicitud`, Indonesian `batalkan permintaan`, French `annuler la demande`; the Chinese cancel-request form MUST be present alongside them). Keywords MUST be specific phrases, never bare words that would collide with page chrome (a bare 「取消」/"cancel" is forbidden). Coverage MUST NOT be expanded to locales the system does not otherwise cover — the fix closes proven gaps within covered locales, it does not build an N-language dictionary. When a Join button is recognized, the observation MUST report its real text and clickable coordinates so a subsequent instructed click can target it. The observation MUST report the real CTA label/context to the cloud judge (including in the header text fallback) rather than reporting null for an unrecognized-locale button — the gate decision belongs to the cloud role, not the edge.

#### Scenario: Vietnamese Join button is recognized and reported
- **WHEN** the edge observes a group whose Join button reads "Tham gia nhóm" (Vietnamese)
- **THEN** the observation classifies it as a join CTA, reports the button text and coordinates, and does NOT report a null CTA that would force the cloud to fail-closed

#### Scenario: A "joined" label containing the join verb is not misread as join
- **WHEN** the observed primary CTA reads "Đã tham gia" (joined) or another locale's joined/leave label
- **THEN** it is classified as an already-member signal, never as an instant-join CTA

#### Scenario: Chinese cancel-request button is recognized as pending
- **WHEN** the account has already requested to join and the group's own primary control reads 「取消请求」(cancel request)
- **THEN** the observation classifies it as pending, sets `pendingRequest` true, and reports the pending state honestly (it is NOT left unclassified and mis-reported as not-yet-requested)

#### Scenario: A bare "cancel" word never triggers pending misclassification
- **WHEN** the page contains an unrelated bare 「取消」/"cancel" control that is not a join-request cancel
- **THEN** it does NOT cause a pending classification, because only specific cancel-request phrases (not the bare word) are in the keyword set

#### Scenario: Unrecognized label stays fail-closed, decided by the cloud
- **WHEN** the primary CTA label matches no known join/joined/pending keyword in any covered locale
- **THEN** the edge does not classify it as join (no clickable join target is fabricated) and the raw label is still surfaced to the cloud judge (via CTA/header text), which decides fail-closed by default

### Requirement: Header/text extraction degrades gracefully so the judge still gets context

The edge group-join observation SHALL extract the group header text robustly: when a primary heading node is not found, it MUST fall back to the main content region text and then to the document title, so the cloud judge receives the group name and visible CTA text rather than an empty observation.

#### Scenario: Missing heading node still yields header context
- **WHEN** the primary heading selector matches nothing on the group page
- **THEN** the observation's header text falls back to the main-region text (which includes the CTA label) or the document title, and is not reported as empty

