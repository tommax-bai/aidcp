## 1. Edge client behavior

- [x] 1.1 Restrict the top-level Cloud mismatch predicate to environments with a known non-empty `connectedCloudKey`, while preserving explicit rebind pending behavior. <!-- aidcp-edge 5673188 -->
- [x] 1.2 Add focused regression coverage for unknown startup Cloud versus a known actual/target mismatch. <!-- aidcp-edge 5673188; cloud-env-selector 15/15 -->

## 2. Validation and closeout

- [x] 2.1 Run the focused Cloud selector tests and Edge typecheck in the isolated worktree. <!-- `npx tsx --test test/electron/cloud-env-selector.test.ts`: 15/15; `npm run typecheck`: pass -->
- [x] 2.2 Record implementation evidence and validate `cloud-startup-rebind-status` with OpenSpec strict mode. <!-- `openspec validate cloud-startup-rebind-status --strict`: valid -->
