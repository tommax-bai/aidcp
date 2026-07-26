## 1. Deployment script repair

- [x] 1.1 Brace every deployment-script variable that is immediately followed by non-ASCII text.
- [x] 1.2 Add a focused source contract test for hazardous unbraced localized expansions.

<!-- Evidence: aidcp-cloud b4694df fixes all six matching expansions and adds the lexical regression test. No topology or fallback behavior changed. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused test, Bash syntax check, Cloud typecheck, and strict OpenSpec validation.
- [x] 2.2 Commit, rebase, fast-forward integrate, and push Cloud and control changes.
- [ ] 2.3 Deploy the integrated Cloud default branch to DEV with the three-process script and verify content, automation, API, ports, schema, PostgreSQL, Feishu, and unrelated-service isolation.

<!-- Validation: focused deployment contract 1/1, bash syntax and lexical scans, Cloud typecheck, and strict OpenSpec validation passed. Cloud b4694df and control 1fdb1fd were rebased, fast-forward integrated, and pushed without force. DEV deployment remains pending. -->

<!-- DEV attempt 2026-07-26: the repaired script completed backup, source sync, dependency install, capability probe, unit install, content health, and automation :8787 health. API then started :8091/:8094 but refused panel :8090 with `composition_dependency_unavailable: server` because the panel still requires automation-owned composition state. The script failed closed and automatically restored the monolith; aidcp-cloud.service is active/enabled with NRestarts=0 and :8787/:8090/:8091, schema gates, PostgreSQL, writer lock, outbox worker, reconciler, and Feishu healthy. Task 2.3 remains open: source segmentation does not yet prove a deployable three-process runtime. -->
