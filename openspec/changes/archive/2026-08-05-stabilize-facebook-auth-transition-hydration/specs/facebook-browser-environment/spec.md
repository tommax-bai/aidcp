## ADDED Requirements

### Requirement: Facebook authentication checkpoints SHALL receive bounded structural hydration

When Facebook navigates to a checkpoint document during authentication, Edge SHALL allow that exact document up to 15 seconds to hydrate into a supported authentication signal before classifying an otherwise unknown checkpoint as terminal. This classification SHALL NOT depend on whether the preceding step was login submission, TOTP, or another supported transition. During this window Native SHALL only re-probe structure and MUST NOT replay any preceding action. Explicit credential/code rejection, human verification, restriction or account-lock evidence, ambiguous supported-warning structure, and unsafe action targets SHALL retain their existing fail-closed behavior without gaining action authority from elapsed time.

#### Scenario: TOTP Continue reaches an incomplete checkpoint
- **WHEN** Native has confirmed the TOTP submit action and the newly navigated checkpoint is less than 15 seconds old but has not hydrated a supported structure
- **THEN** Edge SHALL keep the authentication transition pending and re-probe without replaying TOTP entry or submit
- **AND** it MUST NOT report `unsupported_facebook_checkpoint` solely from the checkpoint path during that window

#### Scenario: Automation warning independently hydrates within the window
- **WHEN** any authentication checkpoint stabilizes within 15 seconds as “We suspect automated behavior on your account” with one unique visible topmost `Dismiss` control in the supported scope
- **THEN** Native SHALL emit `automation_warning_dismiss` with a fresh signal id and exact bound target
- **AND** the coordinator SHALL dispatch the existing `facebook_auth_dismiss_warning` action at most once and verify disappearance or document change before continuing
- **AND** this action SHALL NOT require evidence that TOTP or any other particular step preceded the warning page

#### Scenario: Unknown checkpoint remains after the window
- **WHEN** the exact checkpoint document reaches 15 seconds without a supported signal or stable authenticated identity
- **THEN** Edge SHALL fail closed with the safe unsupported-checkpoint reason and SHALL NOT start account-scoped work

#### Scenario: Explicit blocker appears during hydration
- **WHEN** the checkpoint exposes human verification, rejected authentication, restriction/account-lock evidence, ambiguous warning structure, or an unsafe Dismiss target before 15 seconds elapse
- **THEN** Native SHALL preserve the corresponding terminal or blocked result and MUST NOT click or extend action authority because the hydration budget remains
