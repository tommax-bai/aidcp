## ADDED Requirements

### Requirement: Facebook Reel follows appear truthfully in activity and today's progress

When Cloud supplies `dailyUsage.follow` for a Facebook account, the client SHALL render the follow total, applicable quota, saturation, and window progress in the existing “今日进展” surface exactly as it renders other supplied actions. The client MUST NOT hide the follow row merely because the selected platform is Facebook. A newly verified Reel follow SHALL also emit one structured local follow activity with one fallback `follows` increment; Cloud daily usage SHALL remain the authoritative total when refreshed.

#### Scenario: Cloud supplies Facebook follow usage
- **WHEN** a Facebook environment receives daily usage with `follow` totals and quotas
- **THEN** “今日进展” displays the 关注 item and its real total/quota/window values
- **AND** the unsupported Facebook 收藏 item remains absent

#### Scenario: New Reel follow is immediately visible
- **WHEN** the Facebook Reel executor reports `ok:true` for a newly verified follow
- **THEN** the activity stream adds one human-readable Reel follow entry with a distinct 关注 marker
- **AND** the local fallback follow total increments once until Cloud refreshes the authoritative total

#### Scenario: No-op and failure do not look successful
- **WHEN** a Reel follow returns `already_followed`, shadow, no-target, ambiguous-target, state-unchanged, verify-indeterminate, or another failure
- **THEN** the client adds neither a successful follow activity nor a follow fallback increment

#### Scenario: Edge version lacks Reel follow activity support
- **WHEN** Cloud daily usage includes Facebook follow but the installed Edge predates structured Reel follow events
- **THEN** the existing generic daily-usage renderer still displays the authoritative follow total
- **AND** Cloud does not send automatic follow commands unless that Edge declared `facebook_reel_follow_v1`
