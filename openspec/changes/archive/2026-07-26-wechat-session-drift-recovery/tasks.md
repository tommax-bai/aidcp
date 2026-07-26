## 1. Contract and admission

- [x] 1.1 Reproduce the failure with read-only evidence and distinguish browser login, encrypted API session, Cloud auth projection, and renderer cache.
  <!-- evidence=HTTP 200 platform code 300334 on authData/postList/dmHistory; live browser cookies drifted; Cloud audit active+closed while renderer retained login_required -->
- [x] 1.2 Validate the OpenSpec change strictly before implementation.
  <!-- validation=openspec validate wechat-session-drift-recovery --strict passed -->

## 2. Edge runtime recovery

- [x] 2.1 Preserve safe HTTP/platform metadata on `WechatChannelsError` and classify only business code `300334` as `auth_expired`.
  <!-- evidence=error metadata preserved; exact 300334 classification covered; adjacent 300335 remains platform_rejected -->
- [x] 2.2 Reuse the existing auth-expired browser sidecar flow to recapture and verify the session; keep unrelated platform rejects from opening the browser.
  <!-- evidence=runtime auth_expired recaptures through existing sidecar and returns api_only_running; platform_rejected keeps sidecar closed -->
- [x] 2.3 Add safe scheduled-sync diagnostics with endpoint, HTTP status and platform code, excluding credentials and raw payloads.
  <!-- evidence=scheduled log emits only safe code/endpoint/http_status/platform_code tokens; secret-bearing message is excluded -->
- [x] 2.4 Add focused unit tests for classification, recovery routing and log redaction.
  <!-- evidence=focused WeChat and renderer suite passed 72/72, then the final four boundary tests passed; full gate passed all 1807 tests -->

## 3. Edge client convergence

- [x] 3.1 Keep the visible connected interaction workspace polling independently of current auth/read state.
- [x] 3.2 Render reported `closed` honestly and reserve “未回报” for a missing browser-state report.
- [x] 3.3 Add renderer tests covering stale `login_required` convergence, disabled reads and browser-state labels.
  <!-- evidence=renderer tests converge login_required to active, continue with both reads disabled, and distinguish closed/background/missing -->

## 4. Validation and delivery

- [x] 4.1 Run focused WeChat and renderer tests.
  <!-- evidence=focused suite passed; targeted final boundary rerun passed 4/4 -->
- [x] 4.2 Run Edge acceptance, full tests and typecheck.
  <!-- evidence=land-change gate passed acceptance 25/25, full 1807/1807, and typecheck -->
- [x] 4.3 Rebase, fast-forward integrate and push Edge master without force; do not build an installer.
  <!-- evidence=aidcp-edge commit 5c9a887 pushed to origin/master; local build:dist passed; no installer built -->
- [x] 4.4 Record pushed commit and validation evidence, validate OpenSpec strictly, then commit and push control main.
  <!-- evidence=Edge commit and gate results recorded above; openspec strict validation passed before control commit -->
