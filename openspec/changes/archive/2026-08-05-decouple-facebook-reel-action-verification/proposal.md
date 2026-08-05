## Why

Facebook may replace Reel action controls after a successful click or a neighboring action. The current Edge router can freshly resolve the control, but the Native Like and Follow verification loops turn the first transient unreadable probe into an immediate `verify_indeterminate`. A dispatched click can therefore become terminal before the replacement control becomes readable on the same canonical Reel.

## What Changes

- Keep the current fresh Like and Follow control resolution as the verification authority instead of reintroducing a dependency on the pre-click DOM element.
- Use the existing bounded verification window for transient same-Reel re-render gaps; a genuinely moved, missing, ambiguous, or mismatched Reel remains an ambiguous non-success.
- Preserve the existing independent `interaction.like` and `interaction.follow` commands, receipts, cadence, risk gates, budgets, cooldowns, and confirmed-success accounting.
- Do not add an action collection, batch, pending state machine, protocol field, retry, fallback action, or compatibility path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-like-policy`: Confirm a Reel like from a fresh same-Reel selected-state witness after DOM replacement.
- `facebook-reels-follow-policy`: Confirm a Reel follow from a fresh same-Reel and same-author state witness after transient DOM replacement.
- `native-facebook-capability-runtime`: Preserve canonical target identity across verification without making the original DOM node an authority.

## Impact

- Edge Native Facebook Reel Like/Follow bounded verification loops and focused router/Native regression tests.
- No Cloud, Console, protocol v2, database, policy, deployment, or installed-client mutation in the source implementation itself.
