## 1. OpenSpec and Worktree Setup

- [x] 1.1 Validate the proposal, design, spec deltas, and task plan with `openspec validate client-delegation-popover --strict` before implementation. <!-- 2026-07-15: strict validation passed before edge implementation -->
- [x] 1.2 Create a clean `aidcp-edge` worktree and matching `codex/client-delegation-popover` branch from the latest `master`. <!-- edge worktree /Users/baitianxing/codes/aidcp-edge.wt/client-delegation-popover at bc6e570 -->

## 2. Renderer Structure and Visual Design

- [x] 2.1 Move the delegated-task card out of the main document flow, add the accessible inline-SVG trigger at the far right of the presence row, and restructure the existing form/list as an anchored popover.
- [x] 2.2 Add trigger hover/open/focus/active-task states plus responsive popover width, viewport-bounded height, anchored arrow, internal scrolling, and reduced-motion-compatible styling. <!-- browser QA: 780x900 => 430px popover; 420x720 => 386px, exact trigger alignment and in-viewport bounds -->

## 3. Popover Interaction and Environment Safety

- [x] 3.1 Implement centralized open/close/toggle behavior with synchronized `hidden`/`aria-expanded`, open-time refresh, close-button, repeated-trigger, outside-click, Escape, and focus-return handling.
- [x] 3.2 Close the popover when the selected environment changes and update the trigger's active-task indicator/accessibility text only from the current environment's real task projection.
- [x] 3.3 Preserve existing delegated draft, structured confirmation, platform capability gate, honest progress, pause/resume/cancel, and low-frequency refresh behavior without API or protocol changes. <!-- renderer-only change; focused regression keeps confirmation, honest progress, and Facebook gate green -->

## 4. Verification and Closeout

- [x] 4.1 Extend `companion-ui.test.ts` for default no-layout occupancy, trigger placement, open/close paths, focus/accessibility state, active-task indication, environment-switch closure, and existing confirmation/progress continuity. <!-- focused delegated suite: 6/6 pass -->
- [x] 4.2 Run the focused companion UI test, full `npm test`, and `npm run typecheck` in the `aidcp-edge` worktree. <!-- final code: focused 6/6; companion UI 54/54; full 1357/1357; typecheck pass; git diff --check pass -->
- [x] 4.3 Commit the edge change, fast-forward it into clean `aidcp-edge/master`, and push `origin/master` without building an installer. <!-- aidcp-edge 3d2e663; rebased onto cb9aeba; fast-forward master; pushed origin/master; no installer built -->
- [x] 4.4 Record edge commit/validation/push notes in this task file and pass final `openspec validate client-delegation-popover --strict`. <!-- edge 3d2e663; browser QA 780x900 + 420x720; focused 6/6; companion UI 54/54; pre-rebase full 1357/1357; post-rebase full 1360/1360; typecheck + diff check pass; strict pass; renderer-only, no protocol/API/deploy/package change -->
