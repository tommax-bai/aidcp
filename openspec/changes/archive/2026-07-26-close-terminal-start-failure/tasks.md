## 1. Contract and preconditions

- [x] 1.1 Revalidate the current Edge terminal-error projection, hidden close route, externally occupied no-handle invariant, and complete proposal/design/spec/tasks with strict OpenSpec validation before implementation.
  <!-- repo=aidcp evidence=renderer error excludes close; lifecycle error requires enabled intent; occupied branch rejects before browser acquire validation=openspec validate close-terminal-start-failure --strict passed deviation=none -->

## 2. Edge lifecycle implementation

- [x] 2.1 Keep terminal `automationState=error` closeable in the Electron renderer while preserving “启动” as explicit retry and “浏览器” as the stopped-state auxiliary action.
  <!-- repo=aidcp-edge evidence=renderFab treats every non-stopped automation state, including error, as closeable; closed presence preserves main-process truthful text deviation=none -->
- [x] 2.2 Make no-child close after `envInUseThisRun` settle only the local automation intent, clear the local failure, and skip external profile close confirmation/stop without changing generic abnormal-exit confirmation.
  <!-- repo=aidcp-edge evidence=stopAutomation narrow externallyOccupiedBeforeAcquire branch clears local unconfirmed state/failure and returns before confirmOwnedProfileClosedFromShell; generic path unchanged deviation=none -->

## 3. Regression coverage

- [x] 3.1 Add renderer tests proving terminal error shows “启动 + 关闭”, routes close through `edge:close`, and leaves stopped/browser-error auxiliary behavior unchanged.
  <!-- repo=aidcp-edge validation=renderer-smoke+companion-ui focused tests passed evidence=terminal error lifecycle close and external-occupancy presence assertions deviation=none -->
- [x] 3.2 Add main-process lifecycle contract coverage proving occupied-before-acquire close clears local state and skips external close confirmation while non-occupied failures retain confirmation.
  <!-- repo=aidcp-edge validation=lifecycle-contract focused test passed evidence=occupied return precedes generic confirm; generic confirm assertion retained deviation=none -->

## 4. Validation and integration

- [x] 4.1 Install isolated Edge worktree dependencies, run focused Electron tests, then the Edge full test suite and typecheck.
  <!-- repo=aidcp-edge validation=npm ci --prefer-offline; post-rebase focused Electron 218/218; full npm test 2043/2043; npm run typecheck passed evidence=first full run exposed stale presence reuse, narrowed to structured closeScope, final latest-master rerun green deviation=real external AdsPower session not touched by design; installer not built -->
- [x] 4.2 Commit the Edge change with explicit pathspecs, fetch/rebase onto latest `origin/master`, rerun required validation, fast-forward integrate to the clean canonical checkout, and push `master` without building an installer.
  <!-- repo=aidcp-edge commit=f5b625a155d20d97040ddcfc24713e8cd87a96cb integration=fast-forwarded clean canonical master and pushed origin/master validation=focused Electron 218/218; full npm test 2043/2043; npm run typecheck passed deviation=installer not built; no cloud or protocol change -->
- [x] 4.3 Record repo/commit/validation/deviation evidence in this task file, run strict OpenSpec validation, commit with explicit pathspecs, fetch/rebase onto latest `origin/main`, fast-forward integrate to the canonical control checkout while preserving unrelated untracked files, and push `main`.
  <!-- repo=aidcp commit=7bf1b9e94a3654f2c954c771e4c80dce8b5863a2 integration=fast-forward canonical main and push origin/main validation=openspec validate close-terminal-start-failure --strict passed deviation=canonical untracked output/ and tmp/ preserved; change remains active for later archive -->
