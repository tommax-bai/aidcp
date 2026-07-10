## Context

The Electron companion already captures core stdout/stderr, updates a shared status object, writes developer logs, and surfaces abnormal exits through a system notification. The status object currently keeps only a generic `lastMessage` for the exit, so the actionable stderr cause can be visible in logs but absent from the main client window after the notification disappears.

The change is local to the desktop shell and renderer. The edge core should continue to fail honestly and return non-zero on provider or identity failures.

## Goals / Non-Goals

**Goals:**
- Preserve the last actionable abnormal-exit reason in renderer state.
- Show that reason in the companion window whenever the edge process is in an attention state.
- Keep developer logs as the full-fidelity source while presenting a concise operator-facing summary in the main UI.
- Clear the stored failure when a fresh run starts or the user intentionally pauses/stops/restarts.

**Non-Goals:**
- Change AdsPower provider behavior or introduce a fallback provider.
- Change cloud protocol, edge identity rules, or deployment behavior.
- Parse every possible stack trace into a custom recovery guide.

## Decisions

- Store a new optional UI-state field for the latest edge failure detail.
  - Rationale: renderer status is already the contract between Electron main and UI; adding an optional field keeps backward compatibility.
  - Alternative considered: only append to the activity stream. That would still scroll away and would not clearly bind the failure to the current health state.
- Derive the detail from recent stderr/error lines and the abnormal-exit code.
  - Rationale: core errors already contain honest provider failures such as AdsPower API denial; the shell should reuse that cause rather than duplicate provider-specific logic.
  - Alternative considered: inspect AdsPower API responses directly in Electron main. That would split lifecycle ownership and violate the existing boundary where the core owns browser provider lifecycle.
- Render the detail inside the existing health/details surface and the presence copy path.
  - Rationale: operators already inspect the companion window for health. A separate modal would be another dismissible surface and could recreate the original problem.

## Risks / Trade-offs

- [Risk] Raw stack trace lines could make the main UI noisy. -> Mitigation: keep the concise error line in the visible failure detail and leave full stack traces in developer details.
- [Risk] Stale failures could remain visible after a successful restart. -> Mitigation: clear the field on fresh start, intentional stop/pause, and running status updates.
- [Risk] Some failures may not include stderr before exit. -> Mitigation: fall back to the existing exit-code message so the client still shows a persistent failure state.
