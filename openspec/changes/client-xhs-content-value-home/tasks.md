## 1. Cloud draft refinement foundation

- [x] 1.1 Add execution-target-scoped `publish_draft_refinement_jobs` storage, claim/recovery transitions, and store tests.
  <!-- aidcp-cloud worktree: added 0057 schema + DraftRefinementStore; focused test 3/3 pass. -->
- [x] 1.2 Add pending-draft atomic refinement CAS that validates account, pending status, expected version, allowed scope fields, generated image completeness, audit metadata, and write-back preview.
  <!-- aidcp-cloud worktree: refineDraft scope/selection/account/version transaction; 23 focused tests pass and typecheck pass. -->
- [x] 1.3 Implement text/image refinement worker with safe structured prompts, object-store relocation, white-listed progress messages, target isolation, and unit tests for all five scopes.
  <!-- aidcp-cloud worktree: DraftRefinementWorker implemented; all 5 scopes + partial image failure covered; 16 focused tests and typecheck pass. -->
- [x] 1.4 Add environment-scoped direct edit, refinement-create, and refinement-read customer-auth routes with strict DTO validation, ownership checks, minimal responses, and route tests.
  <!-- aidcp-cloud worktree: PATCH/edit + POST/refine + GET/refinement routes; 3 focused customer-auth tests pass and typecheck pass. -->
- [x] 1.5 Extend the customer content projections only with the minimal source linkage and active refinement data needed by the value homepage; test null/unknown and cross-account isolation.
  <!-- aidcp-cloud worktree: sourceCuratedId + target/account-scoped latest refinement summaries; store 3/3 and focused route tests pass. -->

## 2. Edge customer data plane

- [x] 2.1 Add fixed main/preload IPC for pending-draft edit and refinement create/read; keep envKey/token/accountId out of renderer input and add IPC security tests.
  <!-- aidcp-edge worktree: fixed edit/refine/read IPC with main-side path, method, env, account, and field allowlists; workspace/security tests 37/37 pass. -->
- [x] 2.2 Extend `ContentWorkspace` state/loaders with request epochs, bounded polling, stale response rejection, section-level loading/error/empty/content states, and refresh invalidation.
  <!-- aidcp-edge worktree: home/list/detail/refinement epochs plus 1.8s active, 5s active-queue, and 20s idle polling; stale and empty/error projections covered by focused tests. -->
- [x] 2.3 Add content-home navigation and current-account projections for value summary, featured source-to-draft relationship, reference content, my content, and expandable runtime details.
  <!-- aidcp-edge worktree: source linkage uses only Cloud sourceCuratedId; runtime details expose authoritative daily metrics and use an em dash for unknown values. -->

## 3. Edge value-first UI and interactions

- [x] 3.1 Implement the content-home markup and responsive styles by reusing the accepted client visual language; keep the desktop work panel at 240px including padding/border and eliminate horizontal overflow.
  <!-- Production renderer visual fixture: 1280px viewport measured 240px work panel and zero horizontal overflow; 640px viewport collapsed to one column with zero overflow. -->
- [x] 3.2 Implement the factual work-process timeline with same-size completed rows, stage-complete labels, one current stage, bounded collapse, reduced-motion support, restrained shimmer, and character-by-character output.
  <!-- Production renderer measurement: completed/current status and body are both 11.5px; one mascot, one current row, 28ms typing, 4.8s shimmer, and reduced-motion overrides. -->
- [x] 3.3 Implement direct draft editing and five-scope instruction controls, including selected-text and selected-image capture, in-flight locking, version-conflict refresh, job progress, success refresh, and no-auto-publish boundary.
  <!-- aidcp-edge companion regression 83/83 pass, including direct edit, body refinement, mutation lock, exact selection, progress, conflict/error truth, and no publish side effect. -->
- [x] 3.4 Connect content-home start/close/browser actions to the existing selected-environment controls and preserve the real first-environment start-button guide, skip behavior, confirmation, and platform gating.
  <!-- Runtime controls reuse existing selected-environment actions; fleet 84/84 pass, including exact first-environment start-button handoff and XHS gating. -->

## 4. Validation and delivery

- [x] 4.1 Run focused Cloud store/worker/customer-auth tests, publish safety acceptance tests, full Cloud tests, and typecheck; record bounded evidence.
  <!-- Cloud: focused refinement/store/routes 29 pass; acceptance 68/68; final integration run 2901 pass, 8 gated skips, 0 fail; typecheck pass. -->
- [x] 4.2 Run focused Edge content-workspace/IPC/fleet tests, publish safety acceptance tests, full Edge tests, renderer syntax checks, and typecheck; record bounded evidence.
  <!-- Edge: workspace/security 37/37, fleet 84/84, companion 83/83; acceptance 29/29; final integration run 2248/2248; renderer/main/preload syntax and typecheck pass. -->
- [x] 4.3 Perform browser/Electron visual acceptance for content, empty, stopped, first-start guide, running, editing, refinement progress, failure, and narrow-window states; confirm no horizontal overflow or fake success.
  <!-- Browser production-renderer acceptance covered content, empty/stopped, running/refinement, editing, runtime-detail expansion, and 640px narrow states; fleet/companion regressions covered first-start guide and failed mutation truth. -->
- [x] 4.4 Run `openspec validate client-xhs-content-value-home --strict`, update task evidence with repo SHAs and deviations, then integrate/push Cloud and Edge through the documented fast-forward workflow.
  <!-- Strict validation pass; Cloud master 313eba2992d0031ff833da9b0ae6fda6c8a6c82a and Edge master a742611e4972443f3a519f1a4f6703ef669909a6 were rebased, fully revalidated, ff-pushed, and synced to clean canonical checkouts. No protocol, risk, or auto-publish deviation; Edge installer intentionally not built. -->
- [ ] 4.5 Deploy the integrated Cloud revision to `dev` from the canonical checkout with backup, health/readiness/log verification, and rollback evidence; record that Edge source delivery does not produce an installer.
