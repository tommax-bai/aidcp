# Codex command-output budget

This guide limits transcript growth without weakening validation. The hard per-tool retained-output ceiling is defined in `.codex/config.toml`; commands should normally stay well below it.

## Default budgets

| Command class | Retained output target | Keep |
| --- | ---: | --- |
| Discovery and status | 1,000-2,000 tokens | Relevant paths, state, counts, and the next routing fact |
| Focused test or typecheck | Up to 4,000 tokens | Command, exit status, concise result, failing names and primary error if any |
| Full test/build | Up to 4,000 tokens | Suite/count summary on success; bounded failure evidence on failure |
| Deploy/health/log inspection | Up to 4,000 tokens | Target, service/health state, timestamps, primary errors, and rollback evidence |
| Repeated polling | 1,000 tokens per poll | Only state changes and new bounded output |

## Success handling

- Keep the exact command and exit status.
- Keep duration when it helps identify a timeout or performance regression.
- Record a compact count summary such as suites/tests passed, typecheck success, health status, or matched rows.
- Do not retain routine progress bars, repeated warnings, dependency banners, complete passing-test names, or unchanged service logs.

## Failure-expansion ladder

1. Capture the failing check/test names, the primary error block, and no more than the final 120 relevant lines.
2. Narrow to the failing test file, package, service, time window, request/account identifier, or log pattern.
3. Rerun the narrow check and retain only evidence needed to identify the mechanism.
4. Expand another bounded slice only when the previous slice cannot distinguish plausible causes.
5. Preserve the exit status throughout. Truncated or filtered output never converts a failure or unknown result into success.

## Command selection

- Prefer `rg` and `rg --files` over broad recursive scans.
- Read targeted line ranges instead of whole large files.
- Run focused tests before full suites; avoid rerunning an unchanged full suite after a narrower check already isolates the problem.
- Use concise/native reporters when available. If a tool cannot summarize, rely on the configured retention ceiling and rerun focused slices.
- For `journalctl`, SSH, database, and deployment checks, constrain the service, time window, identifier, row count, or tail length before execution.
- For long-running work, keep the process in a background session and poll for bounded deltas instead of replaying the whole transcript.

## Honest validation boundary

Output limits are a context-control mechanism, not a validation shortcut. A completion note must still say which commands ran, whether they passed, what was not run, which target was checked, and whether any destructive or real-account action remained gated.
