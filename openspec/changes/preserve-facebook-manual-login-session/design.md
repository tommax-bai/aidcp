## Context

Facebook startup already attaches CDP, installs browser foreground control, and creates the Native runtime before first-login reconciliation. The defect is one transition: after the credential-fill grace expires, Native classifies empty fields as a fatal blocked state, the host exits, and Electron applies the ordinary crash-respawn policy even though the AdsPower browser remains Active.

## Goals / Non-Goals

**Goals:**

- Preserve the same core, browser, CDP session, and browser slot while the operator completes Facebook login.
- Stop automatic auth mutations once manual login is required.
- Resume only after the existing stable-identity gate succeeds.
- Keep the exact reason durable in Electron status and keep existing browser foreground control usable.

**Non-Goals:**

- Generalizing every fatal exit into a new termination taxonomy.
- Automating CAPTCHA, checkpoints, passwords, or manual form completion.
- Changing Cloud protocol, proxy authority, browser takeover, or packaging.

## Decisions

### 1. Use one explicit Native signal

Native will emit `manual_login_required` with reason `credential_fill_unavailable` after the existing grace period. Other blocked or unknown auth states keep their current fail-closed behavior. This avoids a reason-string allowlist and keeps the change limited to the observed condition.

### 2. Wait in the existing startup process

The TypeScript coordinator will return `manual_required` rather than `failed`. The startup host will send one local `lifecycle.auth_required` IPC message, stop auth actions, and use the existing in-place identity reader in an unbounded manual mode. It will not call `provider.launch`, reattach CDP, or connect Cloud before identity succeeds.

### 3. Resume on stable identity only

The manual wait performs read-only identity probes. Once a stable identity is observed, the existing identity decision, account binding, UI account event, and Cloud startup continue unchanged. The existing account event clears the manual reason in Electron; no separate recovery protocol is introduced.

### 4. Reuse existing browser control and close ownership

Electron stores the manual reason on the current child generation, marks the browser as blocked-but-controlled, releases only the serial launch wait, and leaves the browser slot occupied. “Show browser” continues through the already-installed parking control. An explicit pause/close interrupts the manual wait and uses the owned AdsPower close-and-confirm path before process exit.

## Risks / Trade-offs

- **A user never completes login** → The browser continues to occupy one explicit slot until the user closes it; the serial launch queue is released immediately so unrelated starts are not head-of-line blocked.
- **The operator logs into a different account** → The existing stable-identity and binding decision fails closed; this change does not weaken identity authority.
- **The browser loses control while waiting** → Existing CDP failure handling remains authoritative; the manual state does not manufacture recovery success.
