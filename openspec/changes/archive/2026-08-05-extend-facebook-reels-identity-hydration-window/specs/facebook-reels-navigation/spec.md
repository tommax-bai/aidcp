## MODIFIED Requirements

### Requirement: Per-method movement proof

Every navigation method SHALL be followed by bounded observation against the pre-navigation canonical route when present and the stable active-video element/content identity. Viewport coordinates MUST NOT form the active-video identity because transition animation moves the existing element. Input dispatch alone MUST NOT be reported as navigation success. Any observed active-video transition SHALL suppress later writes; external success still requires a canonical post-transition Reel card. After an active-video transition is observed, Edge SHALL allow up to 15 seconds for that canonical identity and card to hydrate.

#### Scenario: All methods leave identity unchanged
- **WHEN** all methods permitted for the resolved axis leave the original route and video identity unchanged
- **THEN** the driver SHALL return no next Reel and the session SHALL emit one honest post-dispatch failure receipt

#### Scenario: A prior method moves late
- **WHEN** the active-video identity changes before a fallback write is dispatched
- **THEN** the driver SHALL suppress that fallback and verify the moved-to Reel without another input

#### Scenario: Existing video moves during transition animation
- **WHEN** the same video element changes viewport coordinates but canonical route and stable video identity remain unchanged
- **THEN** the driver SHALL continue bounded verification and MUST NOT treat coordinate movement alone as a new Reel

#### Scenario: Video changes before route hydration
- **WHEN** a distinct active video is proven while canonical Reel identity is temporarily absent
- **THEN** the driver SHALL suppress all later inputs and wait up to 15 seconds for canonical identity
- **AND** if identity does not hydrate within that window, it SHALL return an ambiguous failure and MUST NOT report or deduplicate a fabricated Reel
