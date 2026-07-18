## 1. Contract and documentation

- [x] 1.1 Update the deployment-environments requirement so dev and ol check key existence/readability without requiring POSIX mode 600.
- [x] 1.2 Update the authoritative deployment and helper documentation with the target-specific rule.

## 2. Helper and validation

- [x] 2.1 Update `scripts/deploy-target` so both target checks are portable on Windows.
- [x] 2.2 Run strict OpenSpec validation and prove `scripts/deploy-target dev --check` passes before deployment.

<!-- Evidence (2026-07-18): `openspec validate dev-ssh-key-permission-portability --strict` passed. Git Bash `scripts/deploy-target dev --check` resolved target 121.89.85.150 and the expected key path, and passed using the existence/readability rule. -->
