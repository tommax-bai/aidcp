## ADDED Requirements

### Requirement: French Reel Follow controls preserve author-bound action honesty

The Edge SHALL classify the exact French `Suivre <author>` label as an unfollowed Reel control and the exact French `Suivi(e) <author>` or `Ne plus suivre <author>` label as an already-followed control. Every French control MUST remain bound to the canonical active Reel and exactly one nearby visible author using the existing geometry, uniqueness, fresh-resolution, trusted-input, and same-Reel verification gates. French free text, an authorless control, control disappearance, or a state on another Reel MUST NOT authorize or confirm a Follow.

#### Scenario: French Follow is associated with the exact author

- **WHEN** the canonical active Reel exposes one `Suivre <author>` control and exactly one nearby visible author text equal to `<author>`
- **THEN** Edge resolves that control as the only eligible neutral Follow target

#### Scenario: French already-followed state is a no-op

- **WHEN** the unique author-bound control is `Suivi(e) <author>` or `Ne plus suivre <author>` before dispatch
- **THEN** Edge reports the established already-followed success and sends no click

#### Scenario: French post-state remains same-Reel verified

- **WHEN** Edge dispatches one trusted click to a unique `Suivre <author>` control
- **THEN** it confirms success only after a fresh probe resolves `Suivi(e) <author>` or `Ne plus suivre <author>` for the same canonical Reel, video key, and author

#### Scenario: Authorless or ambiguous French controls fail closed

- **WHEN** a French Follow-state control omits its author association or more than one credible French control or author witness exists
- **THEN** Edge reports not-found, ambiguous, or unconfirmed according to the existing lifecycle and sends no replacement click
