## Why

aidcp 当前运行时仍隐含只有小红书一个平台，但账号表已经有 `platform` 字段，且后续 Facebook 与更多平台会发展出完整的发帖、互动、巡视能力。继续在现有路径里硬塞平台分支会把 protocol、风控、定位、拟人化、账号和部署安全网推向多份实现，后续维护成本和封号风险都会放大。

## What Changes

- Add an explicit platform runtime abstraction that separates platform-neutral infrastructure from page-specific platform drivers.
- Extract the existing xhs behavior into the first `PlatformDriver` implementation without changing xhs runtime behavior.
- Introduce a platform profile/registry layer for platform terminology, limits, scheduler hooks, and capability declarations.
- Require edge startup to declare its runtime platform and cloud to validate it against `accounts.platform`.
- Keep shared foundations single-source: protocol v2 semantics, RiskController, command pacing, CDP attachment, locating gates, humanize, anti-detection, browser provider, and event bus.
- Do not add Facebook comment automation in this change; this is a behavior-preserving refactor that gates later Facebook work.

## Capabilities

### New Capabilities

- `platform-runtime-abstraction`: Defines platform driver selection, capability registration, shared-core boundaries, platform profile registry, and platform/account handshake validation.

### Modified Capabilities

- `accounts-master-data`: `accounts.platform` becomes the runtime source of truth for account platform routing and edge/cloud platform mismatch rejection.

## Impact

- Affected repos: `aidcp-edge`, `aidcp-cloud`, control repo docs/specs.
- Edge areas: `src/platform/*`, xhs driver extraction from current browse/flow implementations, `main.ts` startup selection, edge hello metadata.
- Cloud areas: account store platform accessors, platform profile registry, platform runtime registry, comment agent prompt inputs, scheduler routing, handshake/account validation.
- Protocol: no new protocol message type expected; hello metadata may carry platform/app value through existing envelope shape if supported, otherwise synchronized type-only extension without bumping message semantics.
- Validation gate: xhs acceptance tests, full tests, typecheck, and protocol drift checks must pass with behavior unchanged before any Facebook work starts.
