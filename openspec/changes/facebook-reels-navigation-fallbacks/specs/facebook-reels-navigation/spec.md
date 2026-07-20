## ADDED Requirements

### Requirement: Ordered trusted-input navigation
The Facebook Reels driver SHALL attempt forward navigation in this order: trusted ArrowDown input, one trusted downward wheel gesture, then the scoped next-control click. It SHALL stop the ladder as soon as a method proves movement and SHALL NOT execute later writes after success.

#### Scenario: ArrowDown moves to the next Reel
- **WHEN** ArrowDown changes the canonical Reel route or active-video identity
- **THEN** the driver SHALL report the new Reel and SHALL NOT send wheel or button input

#### Scenario: Wheel is the first successful method
- **WHEN** ArrowDown leaves the Reel unchanged and the subsequent wheel gesture changes route or video identity
- **THEN** the driver SHALL report the new Reel and SHALL NOT click the next control

#### Scenario: Button is the first successful method
- **WHEN** ArrowDown and wheel both leave the Reel unchanged and the scoped next-control click changes route or video identity
- **THEN** the driver SHALL report the new Reel

### Requirement: Randomized bounded wheel gesture
The wheel fallback SHALL send exactly one positive integer delta selected from the inclusive range 70 through 100 pixels for that attempt. The driver MUST use trusted CDP mouse-wheel input and MUST NOT use DOM `scrollBy` as the fallback.

#### Scenario: Lower random boundary
- **WHEN** the injected random source selects its lower boundary
- **THEN** the emitted downward wheel delta SHALL be 70 pixels

#### Scenario: Upper random boundary
- **WHEN** the injected random source approaches or reaches its upper boundary
- **THEN** the emitted downward wheel delta SHALL not exceed 100 pixels

### Requirement: Per-method movement proof
Every navigation method SHALL be followed by bounded observation against the pre-navigation canonical route and stable active-video element/content identity. Viewport coordinates MUST NOT form the active-video identity because transition animation moves the existing element. Input dispatch alone MUST NOT be reported as navigation success.

#### Scenario: All methods leave identity unchanged
- **WHEN** ArrowDown, wheel, and the final button click all leave the original route and video identity unchanged
- **THEN** the driver SHALL return no next Reel and the session SHALL report the existing truthful `scroll/no_target` outcome

#### Scenario: A prior method moves late
- **WHEN** the Reel identity changes before a fallback write is dispatched
- **THEN** the driver SHALL report the changed Reel and SHALL NOT dispatch that fallback write

#### Scenario: Existing video moves during transition animation
- **WHEN** the same video element changes viewport coordinates but the canonical route and stable video identity remain unchanged
- **THEN** the driver SHALL continue bounded verification and MUST NOT treat the coordinate movement alone as a new Reel

#### Scenario: Video changes before route hydration
- **WHEN** a distinct active video is proven while the canonical Reel route temporarily remains unchanged
- **THEN** the session SHALL admit it using route-plus-video identity rather than reject it as a duplicate post URL

### Requirement: Fail-closed button fallback
The button fallback SHALL exclude page-header controls, scope candidates to the far-right navigation rail within the active video's middle vertical band, and prefer a unique semantic next-control label. It SHALL accept the first-Reel layout where the previous control is disabled and only one enabled next control remains, but MUST NOT click an ambiguous or unknown single control.

#### Scenario: First Reel with disabled previous control
- **WHEN** the header contains unrelated 40px controls, the previous Reel control is disabled, and one enabled semantically labeled next control exists in the navigation rail
- **THEN** the driver SHALL select only that next control

#### Scenario: Ambiguous next controls
- **WHEN** multiple credible next controls remain after semantic and structural scoping
- **THEN** the driver SHALL perform zero button clicks and SHALL return no next Reel
