## 1. Audit and shared prompt builders

- [x] 1.1 Record the complete role-catalog-to-preview audit and confirm every current unavailable role has a real runtime model call and prompt source.
- [x] 1.2 Extract/export shared pure prompt builders for interaction reply roles, the independent Facebook group join judge, and the live Facebook comment composer without changing runtime prompt text.
- [x] 1.3 Extract/export shared text-instruction builders for cover-form sensing, visual reference analysis, and visual fidelity audit without changing runtime requests.

## 2. Prompt preview coverage

- [x] 2.1 Add faithful preview builders for the three interaction roles using minimal labeled example inputs.
- [x] 2.2 Add faithful preview coverage for the independent Facebook group join judge, the newly cataloged Facebook comment composer, and `publish:CoverCardWriter`.
- [x] 2.3 Add faithful text-instruction previews for `publish:CoverFormSensor`, `publish:VisualReferenceAnalyzer`, and `publish:VisualFidelityAuditor`, with honest vision/multi-stage notes.
- [x] 2.4 Update the prompt provider routing so interaction and vision roles do not fall through to the wrong group or receive false persona annotations.

## 3. Verification

- [x] 3.1 Add targeted tests for all nine audited gaps, runtime/preview shared builders, account-selection honesty, and render-failure degradation.
- [x] 3.2 Add a catalog-level completeness regression test for all non-browse live model roles.
- [x] 3.3 Run focused prompt/role tests, relevant interaction and visual-role tests, full cloud tests, and cloud typecheck.
- [x] 3.4 Make the console render `personaSource:none` as “does not use persona,” clarify the account-selection hint, then run focused role-page tests, build, and typecheck.

## 4. Delivery

- [ ] 4.1 Update this task list with repo commit SHA, validations, deployment evidence, and deviations; run `openspec validate wechat-role-prompt-preview --strict`.
- [ ] 4.2 Commit and push the control/cloud/console branches, rebase and fast-forward integrate the validated application changes to `master`, then push without force.
- [ ] 4.3 Deploy the integrated cloud and console changes to `dev` from eligible clean canonical checkouts after `scripts/deploy-target dev --check`; verify service, listener, health, Feishu, PostgreSQL, and authenticated prompt responses for the repaired roles.
