## 1. Contract and safety tests

- [x] 1.1 Add renderer coverage for authenticated multi-environment default enrollment, no automatic start, persistent manual exclusion, explicit re-add, incomplete-result safety, and unauthenticated zero regression. <!-- aidcp-edge 9bd8601; focused Electron set passed 118/118 -->
- [x] 1.2 Add main-process coverage for customer-scoped exclusion normalization, identity reset, authoritative envKey filtering, and trusted `assignmentScoped` projection. <!-- aidcp-edge 9bd8601; client-env-scope structural contract included in focused 118/118 -->

## 2. Edge implementation

- [x] 2.1 Add additive customer-owned roster exclusion settings with load/save normalization, identity alignment, renderer owner-write rejection, and authoritative scope filtering. <!-- aidcp-edge 9bd8601 -->
- [x] 2.2 Reconcile complete authenticated profile results into the roster by default, persist once, preserve manual exclusions, and keep failure/truncation/empty results non-mutating. <!-- aidcp-edge 9bd8601 -->
- [x] 2.3 Update join/remove messaging and interaction so manual removal records an exclusion, explicit join clears it, and default enrollment never starts or interrupts environments. <!-- aidcp-edge 9bd8601 -->

## 3. Validation and integration

- [x] 3.1 Run focused Electron tests and `npm run typecheck` in the Edge worktree; resolve all failures. <!-- focused 118/118; acceptance 24/24; typecheck passed -->
- [x] 3.2 Run the full Edge test suite, rebase on latest `origin/master`, rerun required validation, commit, and fast-forward integrate/push `master` without building an installer. <!-- rebased cleanly and pushed aidcp-edge master 9bd8601. Full suite reached 1753/1754: only pre-existing Windows/NTFS POSIX-mode assertion customer-auth-security.test.ts:67 failed (stat 0666 vs expected 0600), independently reproduced with this untouched file. Full file set excluding that Windows-inexpressible test passed 1750/1750. No installer built. -->
- [x] 3.3 Mark tasks with repository commit and validation evidence, run `openspec validate default-assigned-environments-in-roster --strict`, then commit and push the control-repo change. <!-- strict validation passed before archive; control commit recorded after archive -->
