## ADDED Requirements

### Requirement: Facebook page-scroll pacing uses one slower bounded policy

Cloud SHALL use one Facebook platform page-scroll floor for the existing shared `page.scroll` outlet. At normal tempo, the floor's center SHALL be 11,000 milliseconds for both Feed and Reels; warned and restricted states SHALL continue to scale that center through the existing Cloud-owned `effectiveTempo`, and any larger existing card-derived floor SHALL still win. The shared outlet's existing scope, including Facebook search and recovery scrolls, SHALL remain unchanged rather than introducing a second list-surface state solely for pacing.

Edge SHALL apply the wider distribution only to Facebook `page.scroll`: a multiplicative lognormal sample with `sigma=0.30`, centered at the Cloud-provided `dwellMs`, reflected into `0.55x..1.90x` of that center and capped at 60,000 milliseconds. Reflection MUST be used instead of hard clipping, and non-Facebook `page.scroll`, detail dwell, think delays, action gating, and gesture physics MUST retain their existing timing behavior.

The Edge wait SHALL remain the positive difference between the sampled target and time already elapsed since the content-batch anchor. An inline-read remainder SHALL be combined by maximum, not addition. The pacing wait MUST remain abortable and outside the Native page-operation execution budget; this change MUST NOT enlarge the established 15-second Reel identity hydration, 18-second post-input reserve, 180-second `page_scroll` execution, 200/240-second idle recovery, 3,600-second session end, or 5-second quiesce windows.

#### Scenario: Feed and Reels share the 11-second normal center

- **WHEN** Cloud emits an admitted Facebook Feed or Reels `page.scroll` at normal tempo and no larger card-derived floor applies
- **THEN** it supplies `dwellMs=11000` through the same shared scroll outlet

#### Scenario: Risk tempo scales before Edge jitter

- **WHEN** the same Facebook scroll is emitted under warned or restricted pacing
- **THEN** Cloud first increases the 11-second center with its existing `effectiveTempo`, and Edge jitters that already-scaled center without multiplying tempo again

#### Scenario: Facebook jitter is wider and bounded without wall clipping

- **WHEN** Edge receives a Facebook `page.scroll` with positive `dwellMs`
- **THEN** its sampled target uses `sigma=0.30`, reflects into `0.55x..1.90x` of the center, never exceeds 60 seconds, and does not accumulate samples at a hard-clipped boundary

#### Scenario: Existing elapsed time still satisfies the target

- **WHEN** Cloud evaluation and page observation have already consumed all or part of the sampled Facebook target
- **THEN** Edge waits only the remaining positive difference, combines any inline-read remainder by maximum, and waits zero when the target is already satisfied

#### Scenario: Other timing behavior is unchanged

- **WHEN** Edge handles a non-Facebook scroll, detail dwell, think delay, action gate, or scrolling gesture
- **THEN** it uses the pre-existing timing and motion rules rather than the Facebook page-scroll distribution

#### Scenario: Existing timeout budgets remain independent

- **WHEN** a bounded Facebook pacing wait precedes a Native Reel or Feed scroll
- **THEN** the wait remains abortable, the Native page-operation timeout begins independently afterward, and none of the established hydration, input-reserve, execution, idle, session-end, or quiesce windows is enlarged
