## 1. aidcp-edge - Product Semantics

- [x] 1.1 Reframe the daily summary, quota-window labels, completion summaries, and continuation timing as progress and plan completion.
- [x] 1.2 Rework quota-driven presence copy for running and resting sessions while preserving stale-evidence fallbacks.
- [x] 1.3 Separate assistance, waiting, completion, and genuine error visual severity in the title bar and environment rail.
<!-- aidcp-edge 254f885 Renderer semantics and severity implementation -->

## 2. aidcp-edge - Visual Treatment

- [x] 2.1 Replace red saturated metric and quota-window styling with green completion styling and calm near-complete styling.
- [x] 2.2 Update accessibility labels and hover text to use progress and plan language.
<!-- aidcp-edge 254f885 Completion colors and accessible progress labels -->

## 3. Verification

- [x] 3.1 Update pure view-logic, companion UI, and fleet-state regression tests for the new semantics and severity classes.
- [x] 3.2 Run focused Electron tests, the full edge test suite, acceptance tests, and typecheck.
- [x] 3.3 Validate the OpenSpec change strictly and record the landed edge commit in this checklist.
<!-- aidcp-edge 254f885 Focused 80/80, acceptance 16/16, full suite pass, typecheck pass; OpenSpec strict validation pass -->
