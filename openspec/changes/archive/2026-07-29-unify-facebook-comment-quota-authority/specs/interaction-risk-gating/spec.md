## ADDED Requirements

### Requirement: Facebook comment quota accounting and target de-duplication have separate authorities

For Facebook comments, Cloud SHALL use the durable `risk_counters` ledger and the account's effective `RiskController` as the only hard safety-quota count and decision authority for minute, hour and day windows. Cloud MUST NOT derive a hard safety quota from `risk_interactions`, a feature-local environment variable, or another hidden counter.

`risk_interactions` SHALL remain a same-account, same-target, same-action de-duplication ledger. A confirmed or `verification_ambiguous` comment submission MAY create the de-duplication fact because retry could duplicate a real platform write, but that fact MUST NOT independently reduce or veto the visible safety quota.

#### Scenario: Visible comment safety quota is authoritative

- **WHEN** an automatic Facebook comment is considered and the account's effective `RiskController.explain('comment')` allows it
- **THEN** no hidden Facebook-specific daily cap derived from `risk_interactions` or an environment variable may reject it

#### Scenario: De-duplication does not become quota accounting

- **WHEN** a prior Facebook comment submission created a `risk_interactions` row for its target
- **THEN** Cloud MUST use that row only to prevent another comment on the same target
- **AND** minute, hour and day usage MUST come from the idempotent `risk_counters` accounting path

#### Scenario: Ambiguous submission consumes safety usage without becoming success

- **WHEN** Facebook reports `verification_ambiguous` after the comment submit action was dispatched
- **THEN** Cloud SHALL count one consumed comment through the durable risk-accounting funnel and SHALL retain the target de-duplication fact
- **AND** every result and terminal surface MUST remain non-success and MUST NOT claim that the comment is live
