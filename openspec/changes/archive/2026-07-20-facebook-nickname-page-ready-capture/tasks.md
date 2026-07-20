## 1. Facebook Identity Readiness

- [x] 1.1 Add a bounded, navigation-permission-aware Facebook startup bootstrap from unknown tabs to the consumer home page while preserving stable-id fallback.
- [x] 1.2 Capture visible profile-anchor text and accept it only after exact self-id or `/me` binding, with generic-shell cleaning.
- [x] 1.3 Enable the bootstrap only for Facebook initial startup identity reads and explicitly disable navigation for runtime/direct nickname reads.

## 2. Regression Coverage

- [x] 2.1 Add focused identity tests for `about:blank` bootstrap/readiness, navigation-disabled reads, localized visible-text extraction, and other-id rejection.
- [x] 2.2 Add startup/direct-profile regression coverage proving Facebook initial reads opt in while XHS AdsPower and `profile.open{direct}` remain navigation-free.

## 3. Validation and Delivery

- [x] 3.1 Run focused Facebook identity/session tests, Edge acceptance, the full Edge test suite, and typecheck.
  <!-- aidcp-edge after rebase: focused 31 identity/policy + 1 direct-profile passed; acceptance 25 passed; full 1927 passed; typecheck passed. -->
- [x] 3.2 Record the Edge commit and validation evidence, run strict OpenSpec validation, and integrate/push the completed change through the canonical default branches.
  <!-- aidcp-edge: ecf40de integrated and pushed to master. aidcp control: strict validation passed; change artifacts committed and pushed through main. No protocol, Cloud, deployment, or installer change. -->
