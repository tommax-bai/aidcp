## ADDED Requirements

### Requirement: Confirmed Reels navigation SHALL retain Reels surface ownership while the first card is late
After the browser confirms a Facebook Reels route, Edge MUST NOT continue to treat the page as Feed solely because the first active Reel card is not readable within the initial settle budget.

#### Scenario: Reels route is ready before its semantic card
- **WHEN** the fallback navigation reaches a canonical Reels route but no trustworthy active card is readable before the initial deadline
- **THEN** Edge SHALL retain pending Reels ownership, report an honest non-success terminal, and count no view

#### Scenario: Pending Reels recovery reports the current card before advancing
- **WHEN** a subsequent recovery command arrives while Reels ownership is pending and the current active card becomes readable
- **THEN** Edge SHALL report that current card, confirm Reels ownership, and MUST NOT advance past it first

#### Scenario: Pending Reels recovery never navigates to Feed
- **WHEN** a recovery scroll arrives while the browser is on a confirmed pending Reels route
- **THEN** Edge SHALL use the Reels reader and MUST NOT call Feed navigation recovery
