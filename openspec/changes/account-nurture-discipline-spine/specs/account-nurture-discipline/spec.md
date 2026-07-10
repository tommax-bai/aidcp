## ADDED Requirements

### Requirement: Account-age cold-start quota clamp with min semantics stacking over risk backoff

The system SHALL compute a per-account nurture-day from `created_at` at decision time (no maturity field, no per-account maturity state machine). While an account's age is inside the cold-start window (default 7 days), each action's daily effective quota SHALL be `min(cold-start-band quota for that nurture-day, existing risk-scaled quota for the current risk status)`. The `min` clamp MUST guarantee that the age ramp and the risk backoff (`warned` / `restricted`) both stay in force and neither silently overrides the other. Once the account graduates past the cold-start window, effective quotas SHALL fall back exactly to the existing three-tier risk-scaled behavior. The ramp SHALL default on and be env-gated so it can be A/B tested and instantly rolled back. Wiring the cold-start ramp MUST NOT relax any existing risk backoff.

#### Scenario: Day 1 account is clamped to the cold-start band
- **WHEN** a Facebook or xiaohongshu account whose `created_at` is today requests its daily effective quotas at `normal` risk status
- **THEN** each action's effective quota is the cold-start Day-1 band value, not the full `normal` allotment
- **AND** the account is never handed the full `normal` view/like/comment/follow/publish caps on Day 1

#### Scenario: Warned young account takes the min of both limits
- **WHEN** an account is inside the cold-start window AND its risk status is `warned`
- **THEN** each action's effective quota is `min(cold-start-band value, warned-scaled value)`
- **AND** both the age ramp and the warned backoff remain in force (whichever is lower wins, neither is bypassed)

#### Scenario: Graduated account is unchanged
- **WHEN** an account's age is past the cold-start window
- **THEN** its effective quotas equal the existing risk-scaled three-tier values with no cold-start clamp applied

#### Scenario: Ramp knob off yields zero regression
- **WHEN** the cold-start ramp env knob is disabled
- **THEN** `effectiveQuotas()` returns exactly the pre-change risk-scaled values for every account and risk status

### Requirement: Facebook uses a more conservative cold-start curve than xiaohongshu

The system SHALL select the cold-start curve by account platform, and the Facebook curve SHALL be strictly more conservative than the xiaohongshu curve. On Facebook, days 1–3 SHALL permit browse plus at most minimal likes with no comments and no publishing; comments SHALL open no earlier than day 3; publishing and group-join SHALL open no earlier than day 5. Selecting the Facebook curve MUST NOT alter the xiaohongshu curve.

#### Scenario: Facebook Day 1 is browse plus minimal likes only
- **WHEN** a Facebook account on nurture-day 1 requests its effective quotas
- **THEN** browse is allowed and likes are capped to a minimal band
- **AND** the comment and publish effective quotas are zero for that day

#### Scenario: Facebook Day 5 opens publish and group-join
- **WHEN** a Facebook account reaches nurture-day 5
- **THEN** a small publish/group-join allotment is permitted while remaining below the graduated `normal` caps

#### Scenario: Xiaohongshu curve is unchanged
- **WHEN** an xiaohongshu account requests its cold-start quotas after this change
- **THEN** its cold-start curve is identical to the pre-change xiaohongshu behavior

### Requirement: Facebook accounts have a daily online-minutes budget

Facebook accounts SHALL support a configurable daily cumulative online-minutes ceiling (spanning roughly 0.5–6 hours). When an account reaches its ceiling for the day, the system MUST NOT auto-continue the current session or open a new session for that account until the next day, reusing the existing daily online budget and active-window machinery. Facebook SHALL ship with a non-zero default daily window. Login state is persisted by the browser profile and the system MUST NOT proactively log the account out, so the low-logout nurture property is satisfied naturally.

#### Scenario: Facebook account hits its daily online ceiling
- **WHEN** a Facebook account's cumulative online minutes for the day reach the configured ceiling
- **THEN** the system does not auto-continue or open a new session for that account for the remainder of the day

#### Scenario: Within budget the account keeps running
- **WHEN** a Facebook account is still under its daily online-minutes ceiling and inside its active window
- **THEN** session continuation proceeds normally

#### Scenario: Missing ceiling falls back to a safe default
- **WHEN** a Facebook account has no explicitly configured daily online ceiling
- **THEN** the system applies the non-zero safe default window rather than treating the budget as unlimited

### Requirement: Untrusted egress warns but never blocks

On Facebook session start the system SHALL obtain the session's real exit IP and geo by having the edge report it via the existing fingerprint WebRTC = proxy probe, and MUST NOT leak the operator's real-machine IP. When the egress matches a risk feature (mainland-China range, datacenter/hosting range, or the same subnet as the real machine), the system SHALL raise an operations alert to the management console but MUST NOT block, delay, or downgrade any action (honoring the approved v1 decision of no hard gate). If egress detection fails, the system SHALL record the egress as unknown and MUST NOT silently treat it as clean.

#### Scenario: Egress in a China or datacenter range warns without gating
- **WHEN** a Facebook session starts with an exit IP in a mainland-China or datacenter range
- **THEN** an operations alert is raised
- **AND** no browse/like/comment/publish action is blocked, delayed, or downgraded as a result

#### Scenario: Clean residential egress raises no alert
- **WHEN** a Facebook session starts with a clean residential exit IP that matches no risk feature
- **THEN** no egress alert is raised and the session proceeds normally

#### Scenario: Detection failure is reported as unknown
- **WHEN** the egress probe fails to determine the exit IP or geo
- **THEN** the egress is recorded as unknown
- **AND** the system does not assert the egress is clean
