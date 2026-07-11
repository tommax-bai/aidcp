## ADDED Requirements

### Requirement: Scaled risk quotas must round upward

When cloud computes scaled window quotas for reduced risk states, it SHALL round scaled
quota values upward after multiplication. The scaling operation MUST still clamp negative
or non-finite effective outputs to zero, and a zero scaling factor MUST still produce zero.

`warned` accounts SHALL continue to use conservative baseline quotas scaled by `0.7` and
SHALL continue to pause publish actions. However, a positive baseline quota such as a
minute-window quota of `1` MUST NOT become `0` solely because of fractional scaling.

#### Scenario: warned keeps sparse interaction windows available

- **WHEN** an account is in `warned` and the conservative baseline minute quota for an
  interaction action is `1`
- **THEN** the effective minute quota for that action is `1`, not `0`
- **AND** `canDo(action)` is not rejected merely because `0 >= 0` on an empty minute
  window

#### Scenario: frozen scaling still stops all actions

- **WHEN** a quota window is scaled by factor `0`
- **THEN** the effective quota remains `0`
