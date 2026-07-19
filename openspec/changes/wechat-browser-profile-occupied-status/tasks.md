## 1. Contract and preconditions

- [x] 1.1 Revalidate on current default branches that valid stored sessions already bypass the browser, AdsPower occupancy is currently a plain Error, auth remains `authenticating`, and Cloud persists `reasonCode` without an enum-constrained database column.
  <!-- repo=aidcp+aidcp-edge+aidcp-cloud commit=aidcp:pending,aidcp-edge:cd09dd5,aidcp-cloud:5405652 evidence=auth-session valid stored-session bypass; provider apiV2 plain Error; browser_opening maps authenticating; migration 0039 reason_code TEXT deviation=none -->
- [x] 1.2 Complete proposal, design, capability deltas, and strict OpenSpec validation before business-code implementation.
  <!-- repo=aidcp commit=pending validation=openspec validate wechat-browser-profile-occupied-status --strict passed deviation=none -->

## 2. Edge provider and auth state

- [x] 2.1 Add a narrowly matched `BrowserProfileInUseError` for AdsPower V2 start rejection, with local-only masked owner hint and no raw owner leakage or provider fallback.
  <!-- repo=aidcp-edge commit=cd09dd5 evidence=browser-provider exact start-path matcher and masked BrowserProfileInUseError deviation=none -->
- [x] 2.2 Map the typed provider error to `reauth_required + browserState=unavailable + INTERACTION_BROWSER_PROFILE_IN_USE`, preserve API-only success behavior, and keep writes fail-closed.
  <!-- repo=aidcp-edge commit=cd09dd5 evidence=auth coordinator absorbs typed occupancy; stored-session API-only path retained deviation=none -->
- [x] 2.3 Add focused provider/auth tests for valid-session bypass, occupied classification and masking, non-occupied failures, occupied terminal state, and successful explicit retry after release.
  <!-- repo=aidcp-edge commit=cd09dd5 validation=focused Edge interaction/provider tests 106/106 passed deviation=none -->

## 3. Edge protocol and customer workspace

- [x] 3.1 Add `INTERACTION_BROWSER_PROFILE_IN_USE` to Edge interaction error/auth enums and strict payload validation.
  <!-- repo=aidcp-edge commit=cd09dd5 evidence=protocol type and strict validator synchronized deviation=none -->
- [x] 3.2 Render the occupied status and guidance in the Edge interaction workspace, relabel the existing action as “重试打开浏览器”, and keep accepted distinct from active.
  <!-- repo=aidcp-edge commit=cd09dd5 evidence=occupied badge/guidance/retry rendering; accepted fixture remains occupied deviation=none -->
- [x] 3.3 Add focused protocol/workspace tests proving the occupied copy, unavailable browser state, retry action, and absence of raw owner data.
  <!-- repo=aidcp-edge commit=cd09dd5 validation=focused workspace/contract tests passed deviation=none -->

## 4. Cloud acceptance and projection

- [x] 4.1 Add the new reason code to Cloud protocol/types and strict contract parsing while leaving the existing text persistence schema unchanged.
  <!-- repo=aidcp-cloud commit=5405652 evidence=protocol/domain unions and strict allowlists updated; no migration deviation=none -->
- [x] 4.2 Add Cloud contract/store/customer-API tests proving the reason survives ingest, persistence, and projection, while an invented enum is rejected.
  <!-- repo=aidcp-cloud commit=5405652 validation=focused Cloud tests 10/10; PostgreSQL round-trip test added but local DB-gated deviation=none -->

## 5. Control contract synchronization

- [x] 5.1 Update `docs/protocol.md`, frozen interaction JSON Schemas, README, and fixtures for the new reason code and occupied status semantics.
  <!-- repo=aidcp commit=pending evidence=protocol, common/ws schemas, README and occupied fixture synchronized deviation=none -->
- [x] 5.2 Run contract/schema fixture validation and record any real-machine occupancy validation that remains open without claiming it was executed.
  <!-- repo=aidcp commit=pending validation=check-jsonschema metaschema+WS fixtures passed evidence=real-machine backlog cluster 107 deviation=real AdsPower occupancy not executed -->

## 6. Validation, integration, and dev rollout

- [x] 6.1 Run focused Edge tests, Edge acceptance/full tests, and Edge typecheck.
  <!-- repo=aidcp-edge commit=cd09dd5 validation=focused 106/106; acceptance exit 0; full exit 0; typecheck exit 0 deviation=none -->
- [x] 6.2 Run focused Cloud tests, Cloud acceptance/full tests, and Cloud typecheck.
  <!-- repo=aidcp-cloud commit=5405652 validation=focused 10/10; acceptance exit 0; full exit 0; typecheck exit 0 deviation=PostgreSQL integration remains DB-gated -->
- [ ] 6.3 Rebase/integrate by fast-forward onto latest eligible default branches, push Cloud before Edge, and preserve unrelated concurrent commits.
- [ ] 6.4 Deploy Cloud to `dev` after `deploy-target dev --check`, then verify service, listener, health route, Feishu path, and PostgreSQL connectivity; do not build an Edge installer.
- [ ] 6.5 Record pushed commit SHAs, validation/deployment evidence and deviations in this task file, then run `openspec validate wechat-browser-profile-occupied-status --strict`.
