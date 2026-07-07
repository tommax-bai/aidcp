## 1. Edge desktop shell

- [x] 1.1 Store per-environment platform in the AdsPower remark (`plat`), with `normalizePlatform` + `parseRemark` fallback to xiaohongshu for legacy environments.
  <!-- aidcp-edge f311ec5: ads-create-flow.cjs encodeRemark/parseRemark/normalizePlatform + createEnvironment(platform); ads-create-env-service.cjs threads platform. -->
- [x] 1.2 Surface each environment's platform on list (`normalizeProfile.platform` from remark).
  <!-- aidcp-edge f311ec5: ads-local-api.cjs normalizeProfile parses remark -> platform (legacy -> xiaohongshu). -->
- [x] 1.3 Create-env UI platform selector (小红书/Facebook) threaded through IPC to the create flow; environment list shows a platform tag; selecting an environment syncs its platform into settings; manual-fill falls back to xiaohongshu.
  <!-- aidcp-edge f311ec5: index.html #ads-platform select; renderer.js selectedPlatform + selectProfile(...,platform) + save/apply + list tag; main.cjs ads:createEnv passes platform. -->
- [x] 1.4 Inject `AIDCP_PLATFORM` from the selected environment platform at launch (`buildProviderEnv`), default xiaohongshu (zero-regression).
  <!-- aidcp-edge f311ec5: main.cjs DEFAULT_SETTINGS.platform + buildProviderEnv injects AIDCP_PLATFORM=normalizePlatform(settings.platform). -->

## 2. Validation

- [x] 2.1 Add tests: remark platform round-trip + create-flow platform threading + normalizeProfile platform (legacy fallback).
  <!-- aidcp-edge f311ec5: ads-create-flow.test.ts (+platform cases) + ads-local-api.test.ts (normalizeProfile platform). -->
- [x] 2.2 Run edge typecheck, acceptance, full test.
  <!-- aidcp-edge f311ec5: typecheck clean; acceptance 13/13; full 665/665. -->
- [ ] 2.3 Real-machine acceptance: create a Facebook environment, select it, launch, confirm the core opens facebook.com and reports hello.platform=facebook. GATED on the Facebook edge driver landing on aidcp-edge master (facebook-browser-env-and-login). Record to the real-machine backlog until then.

## 3. Closeout

- [ ] 3.1 Record commit SHAs + validation notes here (done above).
- [ ] 3.2 `openspec validate edge-environment-platform-select --strict`.
- [ ] 3.3 Archive only after 2.3 real-machine acceptance passes (needs the Facebook edge driver on master).
