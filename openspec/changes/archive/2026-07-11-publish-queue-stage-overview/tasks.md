## 1. Console Implementation

- [x] 1.1 Replace the content page queue snapshot raw-first view with a compact stage overview derived from existing snapshot keys. <!-- aidcp-console 8abc963: ContentPage derives five display stages from existing snapshot keys; API unchanged. -->
- [x] 1.2 Preserve a collapsed raw-field diagnostic view for full snapshot visibility. <!-- aidcp-console 8abc963: raw snapshot entries remain available under "原始字段". -->
- [x] 1.3 Add responsive CSS for the stage strip and compact metadata/fact chips. <!-- aidcp-console 8abc963: app.css adds active-draft panel, five-stage strip, and mobile horizontal stage flow. -->

## 2. Validation

- [x] 2.1 Add a content page regression test for a running reference-rewrite snapshot that checks stage summary and raw fallback. <!-- aidcp-console 8abc963: ContentPage.test.tsx covers running reference rewrite snapshot summary plus unknown raw field. -->
- [x] 2.2 Run the relevant console test suite and build/typecheck. <!-- aidcp-console: npm test passed 56/57 with 1 skipped; npm run build passed. Existing jsdom getComputedStyle warnings only. -->
- [x] 2.3 Run `openspec validate publish-queue-stage-overview --strict`. <!-- aidcp: passed. -->

## 3. Closeout

- [x] 3.1 Commit and push the console/control changes. <!-- aidcp-console 8abc963 pushed to master; aidcp c215d2b pushed to main. -->
- [x] 3.2 Publish the rebuilt console static assets to the default `dev` target and verify the deployed page is reachable. <!-- dev target verified by scripts/deploy-target dev --check; backup /opt/aidcp/console.bak.20260707-182348.tar.gz; rsynced dist to /opt/aidcp/console; https://aidcp.tommax.cc/ 200 and references assets/index-8kPw_Iiw.js + assets/index-U4uGWRub.css; deployed CSS/JS contain publish-queue-stage and 原始字段. -->
