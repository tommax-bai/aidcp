## ADDED Requirements

### Requirement: Facebook initial feed continues past visible unreportable cards

When initial Facebook feed settling finds zero reportable cards, the Edge SHALL distinguish a genuinely empty, loading, blocked, or unknown homepage from a homepage that contains visible structural cards without trustworthy post identities. If the empty-state probe returns `cards_ready`, the Edge MUST treat the current cards as skipped and immediately run the existing bounded, humanized, lazy-load-aware feed continuation until it finds at least one reportable card or reaches an honest bounded terminal result. It MUST NOT remain idle on the same viewport waiting only for a later Cloud watchdog nudge.

The initial continuation MUST emit `page.cards` only for cards with canonical identities. Because no Cloud command initiated this bootstrap recovery, a bounded failure MUST remain an Edge diagnostic and MUST NOT emit an unsolicited `action.completed` receipt. Confirmed empty, loading, login, captcha, and unknown states SHALL preserve their existing fail-closed behavior.

#### Scenario: Unreportable first card is skipped and a later card starts the loop
- **WHEN** the homepage first viewport contains a visible lightweight media or video card with no accepted post identity, and a bounded downward scroll reveals a card with a canonical permalink
- **THEN** the Edge skips the first card, scrolls downward without reloading the page, and emits `page.cards` for the later canonical card

#### Scenario: Consecutive unreportable cards do not create fake observations
- **WHEN** every card found within the bounded continuation exposes only media resource ids or non-post links
- **THEN** the Edge emits no `page.cards` and no unsolicited `action.completed`, records an honest bounded diagnostic, and never fabricates a target

#### Scenario: Explicit empty feed remains Cloud-authorized Reels fallback
- **WHEN** the homepage contains no structural cards and satisfies the existing stable explicit-empty evidence
- **THEN** the Edge reports the confirmed empty observation and waits for Cloud authorization instead of scrolling as though an unreportable card existed
