## 1. Protocol and control contract

- [x] 1.1 Add `identity.read_current`, `identity.read_self_profile`, and correlated `identity.observed` payloads to the synchronized Cloud/Edge protocol types and command routing; remove the self-capture `direct` field from `profile.open`.
- [x] 1.2 Update `docs/protocol.md` with the fixed side effects, platform strategy, capability negotiation, result correlation, and version-skew rejection contract.

<!-- Evidence: aidcp-cloud bbe0052; aidcp-edge 785244d; aidcp control 0a87371. Protocol v2 acceptance passed in both repos. Deployment is tracked in 4.5; no contract deviations. -->

## 2. Cloud platform orchestration

- [x] 2.1 Add an exhaustive `identityCapture` strategy to every Cloud `PlatformRegistryEntry`, with Xiaohongshu self-profile, Facebook current-page, and WeChat Channels unsupported declarations.
- [x] 2.2 Change startup nickname enrichment to generate a capture id, send the platform-selected identity command, and complete only from matching `identity.observed` results.
- [x] 2.3 Gate each identity command on negotiated Edge support; remove legacy `self.profile.capture → profile.open{direct}` and ensure Facebook current-page completion sends no Feed restore.
- [x] 2.4 Add focused Cloud tests for platform exhaustiveness, command selection, capability skew, result correlation, empty nickname honesty, and strategy-specific restore behavior.

<!-- Evidence: aidcp-cloud bbe0052. Focused identity/acceptance tests passed; post-rebase full suite 3321 passed, 10 skipped, 0 failed; typecheck passed. DEV deployment is tracked in 4.5; no deviations. -->

## 3. Edge and Native execution

- [x] 3.1 Add exact semantic page-command capabilities to browser drivers/hello and route the new Cloud commands and result without a JavaScript fallback; reject legacy `profile.open{direct}` before execution.
- [x] 3.2 Split Native startup bootstrap, runtime current-page identity, and bound self-profile identity commands; declare exact per-adapter command sets in the manifest and platform support matrix.
- [x] 3.3 Implement Facebook current-page identity with a hard no-navigation contract and reject self-profile/ordinary profile commands before CDP dispatch.
- [x] 3.4 Implement Xiaohongshu bound self-profile identity without caller-supplied target identity and return the correlated identity observation.
- [x] 3.5 Add focused TypeScript/Rust/fake-CDP tests for manifest-driver agreement, platform mismatch rejection, zero-navigation Facebook reads, canonical Xiaohongshu self navigation, legacy-direct rejection, and typed observations.

<!-- Evidence: aidcp-edge 785244d. TypeScript full suite 2285 passed; typecheck passed; Rust 52 tests passed; fmt and Clippy passed. Unsigned darwin-arm64 Native artifact and desktop build input verified. No installer or real-account acceptance was performed; x86_64-apple-darwin remains uninstalled. No implementation deviations. -->

## 4. Validation, integration, and DEV delivery

- [x] 4.1 Run Cloud focused acceptance, full tests, and typecheck; record concise evidence.
- [x] 4.2 Run Edge focused acceptance, full tests, typecheck, Native Rust tests/Clippy, and Native/package-input verification; record the installer and real-account validation boundary.
- [x] 4.3 Run `openspec validate platform-specific-identity-commands --strict` and update all completed task evidence.
- [x] 4.4 Commit, rebase, fast-forward integrate, and push control/Edge/Cloud changes through their eligible default branches without force.
- [x] 4.5 Deploy the integrated Cloud default branch to DEV only, verify service/listener/health/Feishu/PostgreSQL, and report that installed Edge clients remain unchanged until a separate package/release.
  <!-- 2026-08-01 23:48 dev 已跑主干头 `aidcp-cloud c0de08b` 并逐项验过。
       **部署动作不是本 change 做的**——是 `split-cloud-automation-production-runtime` 那条流部的；
       本条勾的是「已部署 + 健康检查逐项通过」，如实记清是谁部的。 -->
  - **逐项实测**：服务 `active`、`NRestarts=0`；**8787 与 127.0.0.1:8090 双端口监听**；
    外部真实 WebSocket 握手成功；飞书长连接已建立（`WSClient onReady`）；PG 锚点缓存已就绪；
    三道 schema 契约门全过（content `0069` / automation `0106` / api `0105`）；
    本次启动**零失败行**；同机 isales 四个服务全程 `active`、未受影响。
  - **Edge 客户端未变**：本轮未打任何安装包、未发版，装机客户端保持原样。
  - ⚠️ **今晚这条一度不可能完成**：主干在 dev 上连着三次启动失败（自举名单漏一条流 →
    载荷键集多两个键 → DB 检查点表 CHECK 约束不认新流名），dev 停了约一小时。
    属主流在 23:44–23:48 三个提交修掉（`a0ee197` / `1fa71d2` / **`c0de08b` 补迁移 0106**）。
    **失败形态值得记住：进程 `active`、日志在滚，但端口从未监听** —— 闸在 `server.start()` 之前，
    所以 `systemctl is-active` 在那三次里全是绿的。**healthcheck 必须验端口 + 真握手。**
    完整时间线见 `docs/handoff-2026-08-02-round9.md`。

<!-- Validation: aidcp-cloud bbe0052 and aidcp-edge 785244d passed the checks recorded above; control 0a87371 passed strict OpenSpec validation. All three feature branches were rebased, fast-forward integrated, and pushed to their eligible defaults without force; DEV delivery remains pending. -->
