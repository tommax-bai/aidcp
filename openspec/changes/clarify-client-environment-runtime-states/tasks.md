## 1. Main-process queue projection

- [x] 1.1 Add current pending-position lookup to the serial browser launch queue and cover priority/FIFO changes with focused tests
- [x] 1.2 Project optional structured `queueStage` and `queuePosition` from the authoritative launch/slot schedulers without parsing status text

## 2. Environment rail state model

- [x] 2.1 Derive short primary labels, state kinds, rail groups and full reason details from the independent lifecycle axes
- [x] 2.2 Rename automation `ready` user-facing copy to `待任务` and distinguish browser-ready `待任务` from browser-closed `待机中`
- [x] 2.3 Reuse the existing rail framework to render the expanded groups, structured `#N` position and stable within-group order
- [x] 2.4 Extend the existing status dots with solid/hollow running, starting, queued and standby semantics while preserving platform and selection colors

## 3. Batch-start truth and verification

- [x] 3.1 Count batch-start completion only for running automation or connected browser-ready `待任务` environments
- [x] 3.2 Add focused pure-logic, scheduler and jsdom rail regressions for labels, groups, dots, queue positions and progress <!-- focused scheduler/ui/jsdom after rebase: 169/169 pass -->
- [x] 3.3 Run Edge focused tests, acceptance tests, full tests and typecheck <!-- aidcp-edge 47bf3c0ab6a3; focused scheduler/ui/jsdom after rebase 169/169 pass; health/renderer focused 275/275 pass; acceptance 28/28 pass with real-machine E2E gate skipped; full suite after rebase exit 0; typecheck pass -->

## 4. Contract closeout

- [x] 4.1 Record implementation commits and validation evidence in this checklist <!-- implementation: aidcp-edge 47bf3c0ab6a3 -->
- [x] 4.2 Run `openspec validate clarify-client-environment-runtime-states --strict` <!-- pass -->

## 5. Rapid close/start regression follow-up

- [x] 5.1 Add per-environment lifecycle generations and cancel or invalidate stale preparation, launch, wake and retry work
- [x] 5.2 Serialize a new start request behind an in-flight user close without reusing the closing core
- [x] 5.3 Bind execution-stage truth to the current lifecycle generation and clear it at structured idle/standby/close boundaries
- [x] 5.4 Distinguish authoritative FIFO membership from `start_queue_full` retry state in status and logs
- [x] 5.5 Add focused queue, lifecycle-generation, rapid close/start and rail truth regressions <!-- focused queue/lifecycle/rail/log truth: 206/206 pass -->
- [x] 5.6 Run Edge focused tests, acceptance tests, full tests and typecheck <!-- acceptance: 28/28; full: 2149/2149; typecheck: pass -->
- [x] 5.7 Record follow-up implementation commits and validation evidence <!-- implementation: aidcp-edge 61ce7fc; focused: 206/206; acceptance: 28/28; full: 2149/2149; typecheck: pass -->
- [x] 5.8 Run `openspec validate clarify-client-environment-runtime-states --strict` <!-- pass -->
