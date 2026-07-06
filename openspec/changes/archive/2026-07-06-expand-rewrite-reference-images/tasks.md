## 1. Cloud Implementation

- [x] 1.1 Add a shared reference-image limit for参照洗稿 generation and replace the scheduler/prompt/provider hard-coded 3-image caps.
- [x] 1.2 Preserve invalid URL filtering and existing no-image / text-only semantics.

## 2. Tests

- [x] 2.1 Update scheduler, image prompt composer, image generator, and publish executor tests to cover the 9-image cap and audit count.
- [x] 2.2 Run focused cloud tests for the touched publish-agent modules. <!-- repo=aidcp-cloud; validation="npm test"; result="passed 1393 tests after rebasing onto origin/master" -->

## 3. Validation and Closeout

- [x] 3.1 Run cloud typecheck and relevant full validation if dependencies are available. <!-- repo=aidcp-cloud; validation="npm test; npm run typecheck"; result="passed" -->
- [x] 3.2 Validate `expand-rewrite-reference-images` with OpenSpec strict mode. <!-- repo=aidcp; validation="openspec validate expand-rewrite-reference-images --strict"; result="passed" -->
- [x] 3.3 Commit and push the control/cloud changes, then deploy cloud to `dev` and verify runtime health. <!-- repo=aidcp-cloud; commit=155ce52481c649b852797f9f3e4d722357c6cd85; pushed=origin/master; deploy=dev 121.89.85.150; backup=/opt/aidcp/cloud.bak.20260706-221000.tar.gz and /opt/aidcp/cloud.env.bak.20260706-221000; validation="service active, 8787/8090 listening, /api/health ok, PG select 1, Feishu WSClient onReady, REFERENCE_IMAGE_MAX_COUNT=9 on ECS, isales services active" -->
