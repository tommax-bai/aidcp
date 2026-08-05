## MODIFIED Requirements

### Requirement: Native Facebook reaction vocabulary has one shared owner

The Native Facebook router SHALL maintain the observed zh-CN, zh-TW, English, Spanish, Vietnamese, and French Like/reaction label families in one capability-neutral internal semantics module assembled before Feed Like and Reels. Feed Like and Reels MUST consume that shared vocabulary and positive-state classifier, while the shared module MUST NOT own card identity, active-video association, action-rail geometry, target uniqueness, actuation, or verification choreography. Production TypeScript, caller input, and package resources MUST NOT supply or override the vocabulary.

#### Scenario: Bare simplified-Chinese Reel Like with count is accepted

- **WHEN** the commanded canonical Reel has one active video and exactly one associated right-rail control whose `aria-label` is `赞` and whose rendered body is a numeric reaction count
- **THEN** Reels resolves that control as neutral, freshly activates that same element at most once, and binds verification to the same Reel and marker

#### Scenario: Retained Like locales use the same Reel evidence

- **WHEN** an otherwise identical primary control uses a retained zh-TW, English, Spanish, Vietnamese, or French Like label
- **THEN** Reels applies the same geometry, uniqueness, commit-count, and same-target verification requirements

#### Scenario: French Reel Like is recognized exactly

- **WHEN** the canonical active Reel has exactly one geometrically associated right-rail control labeled `J’aime` or `J'aime`
- **THEN** Reels classifies it as the neutral Like target without matching unrelated French free text

#### Scenario: Numeric Feed summary remains a decoy

- **WHEN** a Feed card contains a reaction summary with a supported reaction-word label and numeric body
- **THEN** the summary alone is not classified as the post Like action and receives no click

#### Scenario: Localized Like does not prove selected state

- **WHEN** the resolved Reel control still exposes only its neutral label and numeric count after activation
- **THEN** verification remains unconfirmed until the same marked control exposes an established selected attribute or remove/unlike witness

#### Scenario: French reaction picker preserves positive verification

- **WHEN** a neutral French Reel Like activation opens a unique associated reaction picker
- **THEN** only the exact `J’aime` picker item is eligible for the bounded fallback commit and success still requires a fresh positive selected-state witness on the marked Reel control
