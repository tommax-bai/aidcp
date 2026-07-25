## Why

The Facebook Native-only cutover preserved command names but regressed several established runtime contracts: feed continuation can classify visible unreportable cards as empty or switch surfaces too early, blocker and consent handling is weaker, and write actions can target the wrong DOM scope or lose the existing uncertain-submit semantics. These gaps must be repaired before Native-only can be treated as behaviorally equivalent to the retired TypeScript page executor.

## What Changes

- Add an explicit Native Facebook parity contract covering browse lifecycle, target scoping, blocker/consent handling, and write-result honesty.
- Restore loading-aware feed settling, bounded continuation over visible unreportable cards, session cursor de-duplication, honest exhaustion, search/back continuity, and bounded SPA refresh verification.
- Restore blocker classification and consent policy enforcement before actions.
- Keep unsupported Facebook commands explicitly unsupported until a complete platform-specific implementation exists; do not inherit Xiaohongshu-only commands or infer capability from a generic command name.
- Move Facebook like, follow, comment, join, and publish choreography to bounded Native stages that use trusted CDP input where submission semantics require it, resolve the commanded target exactly, and verify the same target after acting.
- Preserve ambiguous-submit, pending-review, platform-rejection, and already-complete terminal reasons so Cloud does not retry an irreversible action whose outcome is unknown.
- Add parity tests derived from the retired TypeScript executor’s behavior tests, while retaining Native-only routing with no JavaScript fallback.

## Capabilities

### New Capabilities

- `native-facebook-behavior-parity`: Defines the behavioral and safety equivalence required of the Native-only Facebook page runtime.

### Modified Capabilities

None. This change restores already-specified Facebook behavior and does not alter Edge-Cloud protocol or product policy.

## Impact

- Edge Native Page Engine Rust runtime, embedded Facebook DOM router, TypeScript Native session adapter, manifests, and focused tests.
- Control-repo OpenSpec artifacts and validation.
- No Cloud protocol change, database migration, OL deployment, or desktop installer build.
