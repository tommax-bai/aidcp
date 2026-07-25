## 1. Deployment script repair

- [x] 1.1 Brace every deployment-script variable that is immediately followed by non-ASCII text.
- [x] 1.2 Add a focused source contract test for hazardous unbraced localized expansions.

<!-- Evidence: aidcp-cloud b4694df fixes all six matching expansions and adds the lexical regression test. No topology or fallback behavior changed. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused test, Bash syntax check, Cloud typecheck, and strict OpenSpec validation.
- [x] 2.2 Commit, rebase, fast-forward integrate, and push Cloud and control changes.
- [ ] 2.3 Deploy the integrated Cloud default branch to DEV with the three-process script and verify content, automation, API, ports, schema, PostgreSQL, Feishu, and unrelated-service isolation.

<!-- Validation: focused deployment contract 1/1, bash syntax and lexical scans, Cloud typecheck, and strict OpenSpec validation passed. Cloud b4694df and control 1fdb1fd were rebased, fast-forward integrated, and pushed without force. DEV deployment remains pending. -->
