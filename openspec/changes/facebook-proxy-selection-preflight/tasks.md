## 1. Proxy preflight foundation

- [x] 1.1 Add a main-process-only AdsPower profile proxy reader that preserves credentials only for the caller while keeping existing renderer projections secret-free.
- [x] 1.2 Add a bounded HTTP/HTTPS/SOCKS5 Facebook proxy preflight module and direct production dependencies, with focused unit tests.

## 2. Electron lifecycle integration

- [x] 2.1 Add per-environment in-memory single-flight/TTL preflight state and trigger it after selecting an offline Facebook environment.
- [x] 2.2 Reuse fresh results in full start and cold-standby wake paths, blocking only confirmed proxy failures and reusing existing wake failure handling.
- [x] 2.3 Project safe preflight status into the existing proxy UI without overriding browser runtime evidence, and invalidate it after proxy edits.

## 3. Validation

- [x] 3.1 Add focused Electron lifecycle, renderer, security and AdsPower API tests for selection, reuse, failure, unknown and secret isolation.
- [x] 3.2 Run focused tests, Edge typecheck, desktop build-input verification, and `openspec validate facebook-proxy-selection-preflight --strict`; record commits and validation evidence.

<!--
Implementation evidence (not merged or deployed):
- aidcp-edge commit fe4d374 (codex/facebook-proxy-selection-preflight)
- focused proxy/API/runtime tests: 38 passed
- lifecycle/slot/control-plane/fleet/renderer regression selection: 241 passed
- post-queue-refactor proxy + cold-standby + slot selection: 43 passed
- npm run typecheck: passed
- npm run verify:desktop-build-input: passed
- live one-shot module probe: all six supplied proxies reached Facebook when configured as HTTP; the currently stored HTTPS type for proxy 1 failed as expected
- npm audit --omit=dev: one pre-existing high finding in jsdom -> form-data@4.0.5; new proxy agents are not in the finding path
- no installer build, deployment, archive, or default-branch integration performed
-->
