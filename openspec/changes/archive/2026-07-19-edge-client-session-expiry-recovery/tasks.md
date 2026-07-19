## 1. Specification and implementation

- [x] 1.1 Add startup and local-expiry scenarios to the customer session lifecycle contract.
- [x] 1.2 Refresh near-expiry restored sessions before authenticated startup proceeds.
- [x] 1.3 Route periodic and protected-request local expiry through the existing login-gate invalidation path.
<!-- aidcp-edge worktree edge-client-session-expiry-recovery: src/electron/main.cjs -->

## 2. Verification and delivery

- [x] 2.1 Add focused regression coverage for startup ordering, periodic expiry, and protected-request expiry.
- [x] 2.2 Run focused Electron tests and `npm run typecheck` in the isolated Edge worktree.
<!-- 31 focused Electron tests passed; full Edge suite 1828/1828 passed; typecheck passed. -->
- [x] 2.3 Run `openspec validate edge-client-session-expiry-recovery --strict`.
<!-- OpenSpec 1.3.1 strict validation passed on 2026-07-19. -->
- [x] 2.4 Commit, integrate with `land-change`, deploy dev as required, and record verification evidence.
<!-- aidcp-edge 62abc2621b47d35ff97fe16f1a8274b556b6cf00 fast-forwarded and pushed to origin/master. Edge has no server-side dev deployment for this source-only Electron change; the already-running local dev process was intentionally not restarted because customer-session invalidation stops all environment processes. The canonical dev checkout will use the fix on the next safe client restart. -->
