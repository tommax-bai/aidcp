## Context

Facebook work depends on `platform-abstraction-layer`: the edge must already be able to select a platform driver and cloud must validate account platform routing. This change is the first Facebook-specific runtime slice, but it intentionally stops before scheduled commenting. Its purpose is to prove that a Facebook AdsPower profile can be attached, identified, kept logged in, and safely classified when Facebook redirects to login/checkpoint states.

External review affects scope. Meta's official Pages API can support Page comment management with app/page permissions, but the planned target includes operator-specified pages and groups, and current Groups API capabilities cannot be treated as a reliable official posting/commenting path. Open-source Facebook automation projects mostly wrap Playwright/Puppeteer, internal GraphQL doc IDs, or brittle selectors; they are useful for reconnaissance patterns, not as a core aidcp dependency.

## Goals / Non-Goals

**Goals:**
- Add Facebook browser startup and tab selection support through the existing browser-provider/CDP boundary.
- Add storage-safe probes that summarize cookies/storage/indexedDB key shapes without logging raw secrets.
- Add read-only page structure probes for Page, Group, and post URLs.
- Add comment editor probes that verify controlled-editor input behavior without posting by default.
- Add URL/location-based checkpoint and login-wall detection.
- Implement minimal Facebook driver `readIdentity` and `detectOverlay` after probe evidence confirms stable signals.
- Define Phase-0 gates that must pass before `facebook-scheduled-comment`.

**Non-Goals:**
- Build scheduled commenting, LLM composition, validators, or cron.
- Automate credential entry, 2FA, device confirmation, or checkpoint solving.
- Store Facebook cookies/tokens in git, docs, logs, OpenSpec tasks, or durable memory.
- Replace aidcp's CDP/LocatingEngine stack with Playwright/Puppeteer.
- Depend on Facebook internal GraphQL doc IDs for core runtime behavior.

## Decisions

- Put probes before driver behavior.
  - Rationale: Facebook DOM, editor state, and checkpoint transitions are high drift and high risk; implementation without evidence would encode guesses.
  - Alternative considered: implement a driver directly and iterate during scheduled-comment work. That would mix feasibility failures with automation bugs.
- Keep probes storage-safe by reporting counts, origins, length buckets, token-like markers, and key/name hashes only.
  - Rationale: cookies/localStorage/IndexedDB are credentials or session material, and the 2026-07-06 live probe showed storage key names can themselves contain account-scoped or HMAC-like fragments. The useful engineering question is whether state persists and roughly what shape it has, not the secret value or raw key/name.
  - Alternative considered: dump storage snapshots to reproduce sessions. That violates the repo's secret-handling boundary and is unnecessary with AdsPower profile persistence.
- Use AdsPower profile persistence as the login/session strategy.
  - Rationale: existing anti-detection architecture already treats one account as one profile/fingerprint/IP. That is closer to real user behavior than exporting/importing storage.
  - Alternative considered: CDP export/import of cookies and storage. Keep it as diagnostic tooling only, not the first production path.
- Detect Facebook blocking by URL/location plus page text, not DOM masks alone.
  - Rationale: Facebook often moves the whole page to `/checkpoint` or a login route; an overlay-only detector will miss the highest-value stop signal.
  - Alternative considered: extend generic overlay selectors only. That would not catch full-page redirects.
- Use official/open-source research as reference only.
  - Rationale: Playwright/Puppeteer locators inform robust interaction strategy, but aidcp already owns CDP, humanization, and risk controls. Small Facebook bot repos often include password automation, internal GraphQL ids, or unverified anti-ban claims that should not enter core dependencies.

## Phase-0 Gates

- F1: On a disposable Facebook account and test target, the probe can distinguish local optimistic comment rendering from a server-confirmed posted comment. If not, later code MUST NOT report `commented`.
- F2: Login/checkpoint/temporarily blocked states are detected via URL/location and produce honest stop outcomes.
- F3: A disposable AdsPower Facebook profile can run at realistic low frequency for several days without immediate checkpoint caused by the CDP/provider setup.

## Risks / Trade-offs

- [Risk] Facebook page structure changes between probe and implementation. -> Mitigation: record multiple selector candidates and prefer semantic/user-visible signals; keep probes runnable as regression tools.
- [Risk] Probe logs leak session secrets. -> Mitigation: redact values by design and add tests/grep checks for forbidden raw storage dumps.
- [Risk] A probe accidentally posts. -> Mitigation: default all probes to read-only; require explicit env flag plus target URL and disposable account for gated post probes.
- [Risk] API/open-source paths appear faster. -> Mitigation: treat official Page API as a separate future capability and reject internal GraphQL doc IDs as core runtime dependencies.
- [Risk] Multi-day F3 slows delivery. -> Mitigation: allow Change 1 code to merge with F3 marked as required before Change 2 starts, not necessarily before every local unit test.

## Migration Plan

1. Depend on `platform-abstraction-layer` being implemented and xhs validated.
2. Open `aidcp-edge` worktree for `facebook-browser-env-and-login`; open cloud only if probe reporting/account validation needs code.
3. Add probe scripts and minimal fb driver skeleton.
4. Run local tests/typecheck, then run read-only probes on a logged-in disposable AdsPower Facebook profile.
5. Run gated posting/verification probe only with explicit operator confirmation, disposable account, and test target.
6. Record Phase-0 results in `tasks.md` with no secrets.
7. Validate OpenSpec and stop; do not proceed to scheduled commenting until gates pass.

## Open Questions

- Whether Facebook identity should use `c_user`/profile links, account switcher data, or another stable non-secret signal as primary.
- Whether Page targets and Group targets need separate URL templates in the first implementation.
- Whether official Pages API should become a separate future path for Pages owned by the operator.
