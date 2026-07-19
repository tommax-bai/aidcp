## 1. Edge renderer fix

- [x] 1.1 Update publish-plan controls in place without rebuilding the full draft detail.
  <!-- aidcp-edge 323c98d; mode changes retain the existing draft title/body/gallery DOM. -->
- [x] 1.2 Preserve the review container scroll position across publish-mode and datetime interactions, including the next animation frame.
  <!-- aidcp-edge 323c98d; pointer/mouse/keyboard capture plus synchronous and animation-frame restoration is scoped to the review panel. -->

## 2. Regression validation

- [x] 2.1 Add companion UI coverage for stable DOM identity and scroll position after scheduled-mode and datetime interactions.
  <!-- aidcp-edge 323c98d; companion/content-workspace suite passed 82/82 including simulated native scroll-to-zero behavior. -->
- [x] 2.2 Run focused Electron tests, acceptance, full Edge tests, typecheck, and syntax checks without packaging Electron.
  <!-- Focused regression 1/1, companion/content workspace 82/82, acceptance 25/25, full Edge 1835/1835, typecheck and node --check passed. No Electron package built. -->

## 3. Integration

- [x] 3.1 Run strict OpenSpec validation, integrate and push with repository helpers, and archive the completed change.
  <!-- Strict validation passed. scripts/land-change reran acceptance 25/25, full Edge 1835/1835 and typecheck, then confirmed aidcp-edge 323c98d on origin/master. Canonical master was fast-forwarded to concurrent descendant 319ef31 after verifying no overlap with preserved local changes. No Cloud deployment or Electron package was required. -->
