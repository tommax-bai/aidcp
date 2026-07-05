## 1. OpenSpec

- [x] 1.1 Specify image generation usage recording semantics. <!-- control: proposal + llm-token-usage-stats spec delta added. -->
- [x] 1.2 Validate with `openspec validate record-image-generation-usage --strict`. <!-- passed locally. -->

## 2. Cloud Usage Recording

- [x] 2.1 Record each image generation provider attempt with account, `publish:ImageGenerator`, image provider, image model, calls, ok_calls, and zero token counts. <!-- aidcp-cloud feb24c3: ImageGeneratorRole usageRecorder writes publish:ImageGenerator rows through TokenUsageStore with 0 tokens. -->
- [x] 2.2 Ensure token billing price refresh target selection ignores zero-token image rows. <!-- aidcp-cloud feb24c3: existing HAVING SUM(total_tokens) > 0 covered by focused assertion. -->
- [x] 2.3 Add focused tests for image usage recording and price target filtering. <!-- validation: npx tsx --test test/publish-agent/image-generator.test.ts test/token-usage-store.test.ts passed (26 tests). -->

## 3. Console Usage Display

- [x] 3.1 Add/update usage labels and copy so image usage rows are readable and not presented as token consumption. <!-- aidcp-console f822b98: /usage shows image rows as model calls, cost not applicable, and labels publish:ImageGenerator as image model usage. -->
- [x] 3.2 Add focused console tests for the image usage label/copy. <!-- validation: npx vitest run src/types/usageLabels.test.ts passed (2 tests). -->

## 4. Closeout

- [x] 4.1 Run relevant cloud tests/build. <!-- validation: npx tsx --test focused tests passed; npm test passed (1354); npm run build passed. -->
- [x] 4.2 Run relevant console tests/build. <!-- validation: npx vitest run src/types/usageLabels.test.ts passed; npm test passed (50 passed, 1 skipped); npm run build passed; existing jsdom getComputedStyle and Vite chunk-size warnings only. -->
- [ ] 4.3 Commit and push control/cloud/console changes.
- [ ] 4.4 Deploy cloud and publish console if validation passes.
