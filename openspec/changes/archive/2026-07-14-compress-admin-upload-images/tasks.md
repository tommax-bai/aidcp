## 1. Console compression utility

- [x] 1.1 Add a browser-side image upload compression helper with 600KB skip threshold, no crop/stretch, safe fallbacks, and no GIF frame-dropping.
  <!-- aidcp-console 29d8e9f: src/utils/imageUploadCompression.ts; client-side only, no new dependencies. -->
- [x] 1.2 Add unit coverage for skip, compression, and fallback behavior.
  <!-- aidcp-console 29d8e9f: src/utils/imageUploadCompression.test.ts. -->

## 2. Facebook publish media upload UI

- [x] 2.1 Integrate the helper into the Facebook publish media upload queue before Base64 upload.
  <!-- aidcp-console 29d8e9f: src/components/FacebookSearchConfig.tsx now queues processed File objects. -->
- [x] 2.2 Show upload-size feedback for compressed files in the pending queue and update operator copy.
  <!-- aidcp-console 29d8e9f: pending tags show original -> compressed size; upload copy documents >600KB compression. -->
- [x] 2.3 Add component coverage proving uploaded payloads use the processed file and small files remain unchanged.
  <!-- aidcp-console 29d8e9f: src/components/FacebookSearchConfig.test.tsx. -->

## 3. Validation and closeout

- [x] 3.1 Run relevant console tests and typecheck.
  <!-- npm test -- src/utils/imageUploadCompression.test.ts src/components/FacebookSearchConfig.test.tsx; npm run typecheck; npm run build. -->
- [x] 3.2 Validate the OpenSpec change strictly and record final status.
  <!-- openspec validate compress-admin-upload-images --strict. Dev deploy: aidcp-console 29d8e9f dist deployed to 121.89.85.150:/opt/aidcp/console on 2026-07-13; backup console.bak.20260713-193205.tar.gz; HTTP 8088 root/public 200; /api/health 200; bundle assets/index-BRmuciUr.js contains upload compression copy. -->

## 4. JPEG-only compression follow-up

- [x] 4.1 Update OpenSpec artifacts to require all accepted upload images to convert to compressed JPEG and reject files that cannot be converted smaller.
  <!-- proposal/design/spec updated: 600KB is now JPEG target, not skip threshold; decode/encode/no-smaller failures are rejected. -->
- [x] 4.2 Update the console compression helper and Facebook publish media upload UI to queue only JPEG outputs and reject conversion failures.
  <!-- aidcp-console 2d43980: prepareImageForUpload returns ok/reject result; Facebook upload queue stores only image/jpeg File outputs. -->
- [x] 4.3 Update tests for PNG/GIF/JPEG-to-JPEG conversion, rejection behavior, and uploaded payload filenames/content types.
  <!-- aidcp-console 2d43980: utility and component tests updated for JPEG filenames/content types and rejection behavior. -->
- [x] 4.4 Re-run console validation, OpenSpec validation, commit/push, and deploy the dev console static release.
  <!-- npm test -- src/utils/imageUploadCompression.test.ts src/components/FacebookSearchConfig.test.tsx; npm run typecheck; npm run build; openspec validate compress-admin-upload-images --strict. Dev deploy: aidcp-console 2d43980 dist deployed to 121.89.85.150:/opt/aidcp/console on 2026-07-14; backup console.bak.20260714-034849.tar.gz; HTTP 8088 root/public 200; /api/health 200; bundle assets/index-B0CYrwUy.js contains JPEG-only policy. -->
