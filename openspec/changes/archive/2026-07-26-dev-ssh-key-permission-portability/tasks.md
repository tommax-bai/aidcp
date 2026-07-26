## 1. Contract and documentation

- [x] 1.1 Update the deployment-environments requirement so dev and ol check key existence/readability without requiring POSIX mode 600.
- [x] 1.2 Update the authoritative deployment and helper documentation with the target-specific rule.

## 2. Helper and validation

- [x] 2.1 Update `scripts/deploy-target` so both target checks are portable on Windows.
- [x] 2.2 Run strict OpenSpec validation and prove `scripts/deploy-target dev --check` passes before deployment.

<!-- Evidence (2026-07-18): `openspec validate dev-ssh-key-permission-portability --strict` passed. Git Bash `scripts/deploy-target dev --check` resolved target 121.89.85.150 and the expected key path, and passed using the existence/readability rule. -->

<!-- aidcp dc8bf33 台账补登（2026-07-26 第五次清账批）：本 change 的实体改动确在 origin/main
     —— scripts/deploy-target 的密钥判据从「POSIX 模式必须 600」放宽为「存在且可读」（Windows 上
     模式位不可靠，原判据在 Git Bash 下恒不过），连带 docs/deployment-environments.md 与
     scripts/README.md 同步。本批分诊按「无 sha 标注即 not_landed」暂缓过它一次：
     **判据没错，缺的是标注本身** —— 上面那段 Evidence 只写了验证动作、没留提交号，
     而对账链只认 `<!-- <repo> <sha> -->` 这一种形态（见 memory openspec-triage-and-realmachine-backlog）。 -->
