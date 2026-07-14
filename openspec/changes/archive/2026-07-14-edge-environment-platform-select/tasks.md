## 1. Edge desktop shell

- [x] 1.1 Store per-environment platform in the AdsPower remark (`plat`), with `normalizePlatform` + `parseRemark` fallback to xiaohongshu for legacy environments.
  <!-- aidcp-edge a2fac2a: ads-create-flow.cjs encodeRemark/parseRemark/normalizePlatform + createEnvironment(platform); ads-create-env-service.cjs threads platform. -->
- [x] 1.2 Surface each environment's platform on list (`normalizeProfile.platform` from remark).
  <!-- aidcp-edge a2fac2a: ads-local-api.cjs normalizeProfile parses remark -> platform (legacy -> xiaohongshu). -->
- [x] 1.3 Create-env UI platform selector (小红书/Facebook) threaded through IPC to the create flow; environment list shows a platform tag; selecting an environment syncs its platform into settings; manual-fill falls back to xiaohongshu.
  <!-- aidcp-edge a2fac2a: index.html #ads-platform select; renderer.js selectedPlatform + selectProfile(...,platform) + save/apply + list tag; main.cjs ads:createEnv passes platform. -->
- [x] 1.4 Inject `AIDCP_PLATFORM` from the selected environment platform at launch (`buildProviderEnv`), default xiaohongshu (zero-regression).
  <!-- aidcp-edge a2fac2a: main.cjs DEFAULT_SETTINGS.platform + buildProviderEnv injects AIDCP_PLATFORM=normalizePlatform(settings.platform). -->

## 2. Validation

- [x] 2.1 Add tests: remark platform round-trip + create-flow platform threading + normalizeProfile platform (legacy fallback).
  <!-- aidcp-edge a2fac2a: ads-create-flow.test.ts (+platform cases) + ads-local-api.test.ts (normalizeProfile platform). -->
- [x] 2.2 Run edge typecheck, acceptance, full test.
  <!-- aidcp-edge a2fac2a: typecheck clean; acceptance 13/13; full 665/665. -->
- [x] 2.3 Real-machine acceptance: create a Facebook environment, select it, launch, confirm the core opens facebook.com and reports hello.platform=facebook. <!-- 2026-07-14: the original GATE is now lifted — the Facebook edge driver has landed on aidcp-edge master (FB env/login/browse/publish all shipped in 2026-07). Per fleet convention the real-machine item is decoupled rather than blocking the archive: recorded as docs/real-machine-acceptance-backlog.md 簇 77 (77.1-77.4, incl. the legacy-environment zero-regression fallback). -->

## 3. Closeout

- [x] 3.1 Record commit SHAs + validation notes here. <!-- 2026-07-14: see §4 ledger correction — every sha in this file was rewritten from the dangling `f311ec5` to the real master commit `a2fac2a`. -->
- [x] 3.2 `openspec validate edge-environment-platform-select --strict`.
- [x] 3.3 Archive. <!-- 2026-07-14: the original "archive only after 2.3" gate is superseded by the fleet-wide rule that archiving is NOT gated on real-machine acceptance (real-machine items are decoupled to the backlog instead, see docs/real-machine-acceptance-backlog.md preamble). 2.3 lives on as 簇 77. -->

## 4. Ledger correction (2026-07-14)

- [x] 4.1 The sha this file originally recorded (`f311ec5`) is a **dangling commit contained by zero branches** — almost certainly an orphan left behind by a rebase. The equivalent commit on `origin/master` is **`a2fac2a`** ("Edge: per-environment platform selection at create + launch (facebook/xhs)", identical title and identical 8-file stat). Verified `a2fac2a` is an ancestor of `origin/master`, and master carries `normalizePlatform` / `encodeRemark(plat)` / `parseRemark` in `ads-create-flow.cjs`, the platform threading in `ads-create-env-service.cjs`, `normalizeProfile.platform` in `ads-local-api.cjs`, the `#ads-platform` selector in `index.html`, and the `AIDCP_PLATFORM` injection in `main.cjs` — plus both test files. Per the forward-port rule the acceptance criterion is "equivalent behavior on master + test coverage", not identical patch-id, so all shas above were rewritten to `a2fac2a`. <!-- control repo 2026-07-14 -->
- [x] 4.2 Lesson recorded: a task ledger that points at a sha which is not an ancestor of `origin/<default>` is worthless for reconciliation — future task records should be written **after** the push, from `git rev-parse` on the pushed branch, not from the local pre-rebase sha.
