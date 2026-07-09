## ADDED Requirements

### Requirement: Facebook comments are composed after reading the target post and its discussion

Facebook automatic comment composition SHALL happen AFTER the target post is opened, using the post's caption (when present) and a bounded sample of other people's comments as context. The composer MUST write in the same language as the post/comment content (the local content language), and MUST NOT default to the interface language when it differs. The comment SHALL respond to the actual discussion rather than being written blind from a keyword alone. The edge MUST report the caption and comment samples honestly (empty when a photo post has no caption; never fabricated). The deterministic relevance check SHALL treat the keyword plus the post caption and comments as the relevance context.

#### Scenario: Comment matches the content language, not the UI language
- **WHEN** a target post and its comments are in a non-Chinese language (e.g. Spanish) while the account's Facebook interface language is Chinese
- **THEN** the composed comment is written in the content language (Spanish), not Chinese

#### Scenario: Compose reads the post before writing
- **WHEN** an automatic Facebook comment is composed
- **THEN** the post is opened and its caption + other-people comments are read first, and the composer receives them as context (it is not written blind from the keyword alone)

#### Scenario: Photo post with no caption still composes from the discussion
- **WHEN** the target is a photo post with no text caption
- **THEN** the edge reports an empty caption (never fabricated) and the composer grounds the comment in the other-people comments and persona

### Requirement: Shadow mode is a read-only browse that never submits

Shadow mode SHALL perform the read-only steps needed to compose (search and open the target post to read its caption and comments) and run composition + validators, but MUST NOT submit a comment, record risk/cooldown, dedupe as posted, or report `commented`. It MUST NOT dispatch the comment-submit command.

#### Scenario: Shadow browses read-only but never submits
- **WHEN** shadow mode runs for a Facebook account
- **THEN** it may dispatch search and open (read-only) to read the post, composes and validates a candidate, and audits `shadow_ok` — but never dispatches the comment-submit command and never records success
