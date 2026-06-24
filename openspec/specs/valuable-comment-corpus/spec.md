# valuable-comment-corpus Specification

## Purpose
TBD - created by archiving change comment-like-on-detail. Update Purpose after archive.
## Requirements
### Requirement: Archive only confirmed-liked comments

The system SHALL persist a comment to the valuable-comment corpus ONLY after that comment's like is confirmed successful. Comments that were merely evaluated, abstained on, or failed to like (no-target, state-unchanged) SHALL NOT be archived.

#### Scenario: Confirmed like is archived
- **WHEN** a comment-like is post-verified successful
- **THEN** that comment is written to the corpus

#### Scenario: Unconfirmed likes are not archived
- **WHEN** the like was abstained, reported `no_target`, or did not register
- **THEN** nothing is written to the corpus

### Requirement: Correlation integrity for archived content

Because the like receipt carries no comment text, the system SHALL archive from the appraiser's correlated single-flight state (keyed by a request id holding the picked comment's anchor, text, and author), with an interleaving guard so that a subsequently opened note cannot cause the wrong comment to be archived.

#### Scenario: Archived content matches the liked comment
- **WHEN** a comment-like is confirmed and archived
- **THEN** the stored text and author are those of the comment that was actually liked, correlated by request id — not a later comment

### Requirement: Corpus rows keyed by topic with deduplication

Each archived row SHALL record at least the comment text, author, source note, topic/concept keys, value tags, score, and time. Topic keys SHALL come from the extracted concepts for the source note, with a deterministic fallback key (e.g., a note-title hash) when no concepts are available. Duplicate comments SHALL NOT create duplicate rows.

#### Scenario: Row carries topic keys
- **WHEN** a comment is archived for a note with extracted concepts
- **THEN** the row is keyed by those concepts and is retrievable by topic

#### Scenario: Fallback key when concepts are absent
- **WHEN** no concepts have been extracted for the source note at archive time
- **THEN** the row is stored under a deterministic fallback key rather than dropped or left unkeyed

#### Scenario: Duplicate comment is not re-stored
- **WHEN** the same comment would be archived again
- **THEN** the store keeps a single row (insert-or-ignore on a unique dedup key)

### Requirement: Bounded growth and stated PII posture

The corpus SHALL bound its growth via a retention cap (e.g., newest N rows per topic) and SHALL store other users' comment text and author handles under an explicitly stated retention / redaction posture.

#### Scenario: Retention cap evicts oldest per topic
- **WHEN** the number of rows for a topic exceeds the cap
- **THEN** the oldest rows for that topic are evicted so the corpus does not grow unbounded

### Requirement: Composer uses corpus as non-copied reference

When composing a comment on a related topic, the composer MAY retrieve corpus entries as reference material. Retrieval SHALL be optional: an empty or unavailable corpus SHALL leave the composer's behavior unchanged. Generated comments SHALL NOT reproduce a reference near-verbatim — an overlap guard SHALL rewrite once and, if the draft still overlaps a reference, SHALL skip publishing rather than ship a near-copy or loop.

#### Scenario: References injected as inspiration only
- **WHEN** relevant corpus entries exist for the topic being commented on
- **THEN** they are provided to the composer as reference (inspiration), not as text to copy

#### Scenario: Empty or unavailable corpus changes nothing
- **WHEN** the corpus has no relevant entries or the store is unavailable
- **THEN** the composer proceeds exactly as it would without the corpus

#### Scenario: Near-verbatim overlap is rewritten once then skipped
- **WHEN** a composed draft overlaps a reference near-verbatim
- **THEN** the draft is rewritten once; if it still overlaps, the comment is skipped (never published as a near-copy, and the guard never loops)

