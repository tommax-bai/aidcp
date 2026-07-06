## 1. OpenSpec

- [x] 1.1 Create proposal, design, and `panel-curated-content` spec delta for the站内图片预览行为. <!-- aidcp control repo: proposal/design/spec delta drafted before implementation -->
- [x] 1.2 Validate the change with `openspec validate curated-note-image-lightbox --strict`. <!-- 2026-07-06 valid before console implementation -->

## 2. Console Implementation

- [x] 2.1 Update `CuratedContentPage` so `ReferenceImageStrip` renders preview buttons instead of original-image links and opens the shared image preview modal at the clicked index. <!-- aidcp-console worktree codex/curated-note-image-lightbox: ReferenceImageStrip now uses preview buttons + shared imagePreview modal -->
- [x] 2.2 Cover the查看笔记详情 image click path with a page test, including multi-image switching and no original-image link/download target. <!-- npx vitest run src/pages/CuratedContentPage.test.tsx: 9/9 passed; jsdom emitted existing getComputedStyle warnings -->

## 3. Validation And Release

- [x] 3.1 Run focused console test, `npm run typecheck`, and `npm run build` in `aidcp-console`. <!-- aidcp-console worktree: focused CuratedContentPage test 9/9 passed; npm test 51 passed/1 skipped; npm run typecheck passed; npm run build passed with existing Vite chunk warning -->
- [x] 3.2 Commit and push the control repo OpenSpec artifacts and console implementation. <!-- aidcp-console 6cc6392 pushed to origin/master; aidcp control OpenSpec artifacts recorded in this commit -->
- [x] 3.3 Publish the console static build through the documented production path and record validation/deployment notes. <!-- 2026-07-06 11:16 CST: built from aidcp-console master 6cc6392; deployed dist to ECS /opt/aidcp/console after backup /opt/aidcp/backups/aidcp-console-20260706-111659.tgz; served assets/index-UyoZXzgT.js + assets/index-DE24oKv5.css; health 8088 root 200, JS asset 200, /api/version ok through 8088 and 8090, ports 8088/8787/8090 listening, aidcp-cloud.service active; bundle contains preview button label -->
