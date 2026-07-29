## ADDED Requirements

### Requirement: Native Facebook projects proven Reel presentation once

The Native Facebook browse session SHALL project exactly one `reel_view` companion activity with `statsDelta.views=1` when a `page_cards` result reports `listKind:'reels'`, exactly one card, and an exact HTTPS `www.facebook.com/reel/<id>` identity with no query or fragment. Reserved discovery-route values such as `hashtag`, `audio`, `music`, or `topics` are not Reel identities. The sentence SHALL use only reported title and author metadata with the existing bounded human-readable fallback. The session MUST NOT project activity from scroll intent, an unchanged or repeated canonical identity, an empty batch, a multi-card Reels batch, or an uncanonical identity.

#### Scenario: New single-card Reel becomes one read activity
- **WHEN** Native reports a single-card Reels batch for a canonical Reel not previously projected in the session
- **THEN** Edge forwards the cards to Cloud and emits one `reel_view` activity with one local fallback view increment

#### Scenario: Repeated or ambiguous Reel does not duplicate activity
- **WHEN** Native reports a previously projected canonical Reel, more than one Reel card, or a card without canonical Facebook identity
- **THEN** Edge does not emit another Reel read activity or fallback view increment

### Requirement: Native Facebook projects only strict single Feed video evidence

The Native Facebook browse session SHALL project exactly one `feed_video_view` companion activity with `statsDelta.views=1` when a `page_cards` result reports `listKind:'feed'` and contains exactly one card explicitly marked `isVideo:true` whose note identity satisfies the strict canonical Facebook Feed-video boundary. Other non-video cards MAY coexist in the batch. A batch with zero or multiple video cards, a Reel identity, an uncanonical identity, or a card without the explicit video witness MUST NOT produce a Feed-video activity.

#### Scenario: Unique canonical Feed video becomes one read activity
- **WHEN** a Native Feed batch contains exactly one explicit canonical Feed video and zero or more non-video cards
- **THEN** Edge forwards the cards to Cloud and emits one `feed_video_view` activity with one local fallback view increment

#### Scenario: Ordinary or ambiguous Feed does not gain new counting semantics
- **WHEN** a Native Feed batch contains only non-video cards, multiple video cards, a Reel-shaped video identity, or an uncanonical video identity
- **THEN** Edge emits no Feed-video activity and no local fallback view increment for that batch

### Requirement: Native presentation projection deduplicates detail activity without suppressing data

The Native Facebook browse session SHALL retain canonical identities projected from Reel and Feed-video presentations for the lifetime of that session. A later `note_detail` for one of those identities MUST still be reported to Cloud, but MUST NOT emit a duplicate `note_open` activity or another local fallback view increment. A detail with no matching presentation witness SHALL preserve the existing `note_open` activity and fallback view behavior.

#### Scenario: Later detail for projected content remains data-only locally
- **WHEN** Native reports `note_detail` for a canonical identity already projected from Reel or Feed video cards
- **THEN** Edge forwards the detail to Cloud and emits no duplicate local read activity or fallback view increment

#### Scenario: Unmatched detail preserves existing read activity
- **WHEN** Native reports `note_detail` whose canonical identity was not projected from cards in this session
- **THEN** Edge forwards the detail to Cloud and emits the existing `note_open` activity with one local fallback view increment
