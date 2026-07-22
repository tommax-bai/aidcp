## 1. Cloud reply composition

- [x] 1.1 Make `reply_polisher` use a role-specific generic creator prompt with short, friendly, non-merchant boundaries.
- [x] 1.2 Inject existing account contact info into `{{support_channel}}` only when the published template explicitly uses it.
- [x] 1.3 Protect every rendered support-channel line and fall back to the deterministic template when AI changes one.
- [x] 1.4 Replace merchant-oriented static preview fixtures with generic creator interaction examples.

## 2. Verification

- [x] 2.1 Add focused tests for prompt wording, contact precedence/fallback/no-read behavior, and protected-line fallback.
- [x] 2.2 Run focused Cloud tests, the full Cloud suite, typecheck, and strict OpenSpec validation.

<!-- Implementation: aidcp-cloud commit 0025f1e. Validation: focused reply tests 17/17, reply plus role-preview tests 45/45, post-rebase full Cloud suite 2792 tests (2784 pass, 8 environment-gated skip, 0 fail), npm run typecheck pass, and openspec validate --strict pass. Integration and dev deployment remain pending. -->

## 3. Delivery

- [ ] 3.1 Commit the Cloud and control-repo changes with validation evidence, then integrate and push their default branches.
- [ ] 3.2 Deploy the clean Cloud `master` revision to `dev` and verify service, health, logs, and unchanged configuration/contact row counts.
