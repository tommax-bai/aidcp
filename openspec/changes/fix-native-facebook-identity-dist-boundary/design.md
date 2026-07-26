## Context

The production Edge distribution intentionally keeps TypeScript orchestration while removing migrated Facebook page executors and their injected JavaScript rule bundles. The pruning script verifies that boundary after TypeScript compilation. Native browse orchestration now needs canonical Reel and Feed-video identities, but it imports them from `facebook/post-identity`, whose unrelated DOM helper exports depend on `facebook/cta-labels`. TypeScript emits the whole module dependency chain, so a pure helper import makes the forbidden legacy bundle reachable.

## Goals / Non-Goals

**Goals:**

- Give Native orchestration a dependency-safe source for canonical Facebook post identities.
- Preserve one implementation for each identity classifier and the existing public exports used by remaining development modules.
- Make the production-dist verification catch future dependency regressions.

**Non-Goals:**

- Change post identity formats, Facebook DOM targeting, action verification, or protocol contracts.
- Remove all remaining development-only TypeScript Facebook executors.
- Package, sign, or release a desktop installer.

## Decisions

1. Move self-contained identity functions and their injectable `POST_IDENTITY_JS` string into a pure module with no page-rule imports. The existing mixed module imports and re-exports those symbols before composing its legacy DOM helper strings. This avoids duplicate implementations and preserves existing imports.
2. Point Native browse orchestration directly at the pure module. Re-export compatibility is deliberately not used there because importing the mixed façade would keep the forbidden transitive dependency.
3. Verify the boundary at the built-distribution level, not only with a source-import assertion. The production pruner is the authoritative graph check because TypeScript emit and runtime reachability are what determine shipped files.

Alternatives considered:

- Duplicating the two presentation classifiers in the Native session was rejected because their canonicalization behavior could drift.
- Allowlisting `cta-labels.js` in production was rejected because it would weaken the Native-only cutover gate instead of fixing the dependency.
- Moving all legacy DOM helpers at once was rejected as unnecessary scope and higher regression risk.

## Risks / Trade-offs

- [Compatibility façade accidentally becomes the Native import again] → Keep the Native import explicit and cover the built distribution with the existing pruning gate.
- [Moving exports changes legacy consumers] → Preserve the same named exports from `facebook/post-identity` and run focused identity/session tests plus typecheck.
- [Production `dist` remains partially generated after a failed build] → Re-run the complete production build and verification after integration; do not treat the earlier partial output as a valid artifact.

## Migration Plan

1. Add the pure identity module and compatibility re-exports.
2. Switch the Native browse-session import.
3. Run focused tests, typecheck, full Edge tests, and production-dist build/verification.
4. Integrate through the isolated worktrees and rebuild the canonical local development artifacts.

Rollback is the two-module refactor commit; no data, protocol, or server migration is involved.

## Open Questions

None.
