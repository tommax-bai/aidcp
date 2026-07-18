## 1. Specification

- [x] 1.1 Add OpenSpec delta for default dev/ol client-auth URL resolution.

## 2. Implementation

- [x] 2.1 Add a single dev/ol default client-auth URL mapping in edge.
- [x] 2.2 Make the login gate enabled by default for resolved dev/ol cloud environments while preserving explicit URL overrides.
- [x] 2.3 Update desktop build workflow/package scripts/docs so dev and ol builds bake client-auth defaults consistently.
- [x] 2.4 Add or update focused tests for dev and ol default login URL behavior.

## 3. Validation

- [x] 3.1 Run focused Electron tests covering cloud env and client-auth behavior.
  <!-- validation: npx tsx --test test/electron/client-auth-defaults.test.ts; npx tsx --test test/electron/cloud-env-selector.test.ts -->
- [x] 3.2 Run `npm run typecheck` in `aidcp-edge`.
  <!-- validation: npm run typecheck -->
- [x] 3.3 Run `openspec validate default-client-auth-by-env --strict`.
  <!-- validation: openspec validate default-client-auth-by-env --strict -->
- [x] 3.4 Commit and push the edge implementation and OpenSpec change.
  <!-- edge: 37d14e2 pushed to aidcp-edge/master; control: recorded in this OpenSpec commit -->
