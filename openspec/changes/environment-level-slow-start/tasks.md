## 1. Cloud environment fact source

- [x] 1.1 Add the additive `client_environments.slow_start_since` schema self-heal and a re-runnable one-time initialization marker that cannot re-enable an explicitly disabled environment on restart.
- [x] 1.2 Add env-scoped ownership-checked slow-start read/write store methods that align enabled timestamps to the Shanghai operating-day boundary and never modify account fields.
- [x] 1.3 Add and refresh a synchronous environment-binding slow-start mirror for the risk hot path, including explicit ambiguous-account diagnostics instead of arbitrary row selection.
- [x] 1.4 Update environment registration/rebinding so old and new account lookups observe the committed environment setting on their next call without restart.

## 2. Cloud risk and customer API integration

- [x] 2.1 Compose the nurture provider from environment slow-start state plus existing account platform/created-at data, and remove `accounts.slow_start_since` from active clamp selection.
- [x] 2.2 Change env-scoped GET/PUT routes to write the environment directly, preserve strict request validation and ownership, and return configured-but-unbound projections without leaking account identity or quotas.
- [x] 2.3 Keep bound-environment GET/PUT and `ui.snapshot` projections sourced from the same controller anchor and retain global-disable/platform-eligibility honesty.
- [x] 2.4 Add store, route, risk, rebind, migration, ambiguity, natural-day, and no-account-field-write regression tests. <!-- focused cloud: 93/93 pass; typecheck pass -->

## 3. Edge environment presentation

- [x] 3.1 Render `binding_unknown` plus explicit `state` as an operable environment configuration, preserving checked/off truth while withholding unconfirmed binding and quota claims.
- [x] 3.2 Update slow-start copy to state that the setting belongs to the selected environment and that an unbound environment applies it after account login.
- [x] 3.3 Add renderer/UI logic/API tests for unbound active/off environments, pending/error isolation, source precedence, and bound-account behavior remaining compatible. <!-- focused edge: 107/107 pass; typecheck pass -->

## 4. Validation and integration

- [x] 4.1 Run focused cloud and edge slow-start/store/customer-auth tests, then both repositories' acceptance suites, full tests, and typechecks. <!-- cloud focused 93/93, acceptance 56/56, full exit 0, typecheck pass; edge focused 107/107, acceptance 24/24, full exit 0, typecheck pass -->
- [x] 4.2 Run `openspec validate environment-level-slow-start --strict`, record repo commit SHAs and validation evidence in this checklist, and commit/push the control, cloud, and edge branches. <!-- strict pass; cloud a8bb2e3; edge 7e80ce2; control artifacts 8e8d1e0 plus this evidence commit -->
- [x] 4.3 Rebase and fast-forward integrate clean validated commits into the latest default branches without overwriting unrelated work. <!-- task-preflight pass; cloud a8bb2e3 ff master; edge rebased onto latest master then 7e80ce2 ff master; control 8e8d1e0 plus this evidence commit will ff main -->

## 5. Dev deployment and honest acceptance

- [x] 5.1 Read the deployment guide, run `scripts/deploy-target dev --check`, confirm the shared-database boundary, back up the cloud target, and deploy only from a clean eligible default checkout. <!-- additive-only shared-schema change; backup=/opt/aidcp/cloud.bak.20260718-100647.tar.gz env=/opt/aidcp/cloud.env.bak.20260718-100647; clean cloud master a8bb2e3 -->
- [x] 5.2 Verify the AIDCP service, listeners, health, Feishu, PostgreSQL, migration count/duplicate-binding diagnostics, and confirm unrelated `isales` services were not touched. <!-- dev active NRestarts=0; 8787/8090/8091/8088/5432; local+public health ok; PG select 1; columns=2 initialized=22 pending=0 env-enabled=1 duplicates=0; Feishu onReady; four isales units remained active; deployed source hashes match master -->
- [x] 5.3 If an exclusive non-OL Facebook test environment is available, verify enable → account rebind → new account inherits / old account releases without restart; otherwise record the gated real-machine item in `docs/real-machine-acceptance-backlog.md` and do not claim it ran. <!-- no exclusive target was designated; real rebind was not run; recorded as backlog 103.9-103.11 -->
