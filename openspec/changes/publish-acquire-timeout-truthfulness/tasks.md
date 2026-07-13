## 1. Specification and design

- [x] 1.1 Record the cloud/edge design, safe-boundary decision, and rollout order.
- [x] 1.2 Define truthful publish acquire-timeout notification and bounded `note.open` behavior.

## 2. Cloud notification accuracy

- [x] 2.1 Add an explicit publish dispatch notice for acquire timeout and classify `EdgeTaskLeaseError` before a sequence starts. <!-- aidcp-cloud master 76d5163 -->
- [x] 2.2 Render the new Feishu notification without the “edge offline” claim. <!-- aidcp-cloud master 76d5163 -->
- [x] 2.3 Add dispatcher regression coverage for acquire timeout requeue semantics. <!-- aidcp-cloud master 76d5163 -->

## 3. Edge bounded note opening

- [x] 3.1 Add a safe deadline check to the humanized card-click input path. <!-- aidcp-edge master de89150 -->
- [x] 3.2 Bound `note.open` phases by a 30-second wall-clock budget and log phase durations. <!-- aidcp-edge master de89150 -->
- [x] 3.3 Add regression coverage that an expired `note.open` reports an honest failure and allows task quiescence to continue. <!-- aidcp-edge master de89150 -->

## 4. Verification and delivery

- [x] 4.1 Run focused cloud and edge tests, acceptance suites, and typechecks. <!-- cloud/edge typecheck; full tests exit 0; cloud acceptance 47 pass; edge acceptance 16 pass -->
- [x] 4.2 Commit and push the sibling-repository changes; deploy cloud to `dev` and record deployment/validation evidence. <!-- cloud 76d5163 deployed dev: backup cloud.bak.20260713-134932.tar.gz, active/8787/8090/PG/Feishu/isales-scheduler green; edge de89150 pushed master, desktop package intentionally not built -->
- [x] 4.3 Validate this OpenSpec change strictly and update completion records. <!-- openspec validate publish-acquire-timeout-truthfulness --strict -->
