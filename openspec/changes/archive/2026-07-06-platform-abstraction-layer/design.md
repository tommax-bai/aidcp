## Context

aidcp 的 cloud/edge/runtime 文档已经把系统定位为云端重编排、边缘轻执行：云端保有 EventBus、RiskController、角色决策和协议翻译，边缘保有 CDP、DOM-first locating、humanize、浏览器 provider 与页面原子操作。当前实现仍把这些能力默认投向小红书页面，导致平台边界主要靠文件名和调用约定隐式维持。

Facebook 首版只需要定向评论，但长期目标是多平台全功能。平台抽象不能从 Facebook 评论窄场景反推，否则接口会被评论流程塑形；应从现有唯一全功能平台 xhs 提取平台能力域，并保持 xhs 行为逐位不变。

## Goals / Non-Goals

**Goals:**
- Define a platform-neutral runtime boundary and driver contract for edge page-specific behavior.
- Extract existing xhs behavior into an xhs driver without changing xhs behavior, protocol message counts, risk semantics, or deployment flow.
- Make `accounts.platform` the cloud-side routing and validation source of truth.
- Keep shared runtime foundations single-source and explicitly prevent per-platform copies of CDP, locating, humanize, anti-detection, risk, protocol, and browser provider code.
- Add registry/profile wiring so future platform implementations can declare capability subsets.

**Non-Goals:**
- Implement Facebook login, probes, page operations, or scheduled comments.
- Redesign the event bus or split it per platform.
- Add a protocol v3 or platform-specific protocol message names.
- Change xhs comment approval, publish approval, browse loop behavior, or risk quotas.
- Deploy production cloud as part of this refactor before sibling-repo validation is green.

## Decisions

- Introduce `PlatformDriver` on edge with capability domains: identity, overlay detection, browse, comment, publish, interact, and patrol.
  - Rationale: capabilities match the existing xhs full-function surface and allow Facebook to implement only browse/comment later.
  - Alternative considered: add `if platform === 'facebook'` branches inside current browse modules. That is faster for a single feature but creates duplicated platform assumptions across the runtime.
- Extract the interface from xhs, not from Facebook.
  - Rationale: xhs is the only complete implementation today, so it reveals the actual full surface: browsing, publishing, interaction, profile traversal, notification patrol, identity, and overlays.
  - Alternative considered: define a minimal comment-only interface. That would underfit future publish/patrol work and force a second abstraction pass.
- Use a cloud `PLATFORM_REGISTRY` plus platform profiles rather than per-platform orchestrator forks.
  - Rationale: cloud orchestration must keep risk, pacing, account routing, and prompt parameterization centralized; platform data belongs in registry entries.
  - Alternative considered: run separate xhs and fb schedulers with separate account stores. That would fragment cooldown/risk accounting and make cross-platform operations harder to audit.
- Keep protocol semantics platform-neutral.
  - Rationale: existing commands already describe intent such as browse/open/comment/publish. Platform-specific DOM details belong below the driver boundary.
  - Alternative considered: add `facebook.*` protocol messages. That would leak platform concepts into every synchronized protocol definition and raise drift risk.
- Validate edge platform against `accounts.platform` at cloud handshake/task routing.
  - Rationale: running an xhs edge against a Facebook account is configuration corruption and must fail honestly before actions.
  - Alternative considered: trust operator env only. That is too weak once multiple AdsPower profiles and accounts are online.
- Treat Change 0 as behavior-preserving and archive only after xhs zero-regression.
  - Rationale: later Facebook probes depend on a stable abstraction. Mixing extraction and Facebook behavior would make regressions ambiguous.

## Risks / Trade-offs

- [Risk] The driver interface becomes too broad or too abstract. -> Mitigation: extract only from concrete xhs call sites and capability domains already present; keep optional domains for future platforms.
- [Risk] xhs regression from moving files and wiring. -> Mitigation: preserve public behavior, run edge/cloud acceptance before full tests and typecheck, and keep protocol counts unchanged.
- [Risk] Shared foundations are accidentally copied into `src/xhs` or later `src/fb`. -> Mitigation: add review/acceptance checks that CDP, locating, humanize, anti-detection, and browser-provider code remain in shared modules.
- [Risk] Account platform validation blocks existing default accounts. -> Mitigation: default existing seeded rows to `xiaohongshu` and provide explicit, honest errors for mismatches.
- [Risk] EventBus platform scoping is overbuilt prematurely. -> Mitigation: Change 0 only introduces registry capability metadata; role registration remains behaviorally unchanged for xhs.

## Migration Plan

1. Create OpenSpec artifacts in the control repo.
2. Open same-name worktrees only for sibling repos that need code (`aidcp-edge`, `aidcp-cloud`).
3. Implement edge interface and xhs driver extraction behind default platform `xiaohongshu`.
4. Implement cloud registry/profile/account platform accessors and handshake validation.
5. Run xhs acceptance suites first, then full tests and typecheck in edge and cloud.
6. Commit sibling repos, update `tasks.md` with commit SHAs and validation notes, then validate the OpenSpec change.
7. No production deployment is required for a spec-only proposal; runtime deployment follows the normal safe path only after code lands and default-branch integration is complete.

## Open Questions

- Whether edge hello already has a suitable `app`/metadata field for platform, or requires a synchronized type-only extension.
- Whether console needs to expose platform selection in this change or can continue relying on existing account rows until Facebook account onboarding.
