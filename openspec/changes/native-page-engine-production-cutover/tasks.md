## 1. Contract freeze and test harness

- [x] 1.1 Export the current Xiaohongshu browse, interaction, notification, profile, and publish command registry into a machine-readable migration manifest, including request, result, receipt, cancellation, and effect-semantics mappings.
  <!-- aidcp-edge 450cede: command-manifest.json plus registry/publish-kind parity tests; 3 manifest tests passed. No package or deployment. -->
- [x] 1.2 Add a Rust fixture harness that can replay selector-free command fixtures and compare normalized Native results with the frozen TypeScript contract expectations.
  <!-- aidcp-edge 450cede: selector-free JSON fixture replay includes search_result_ai, detail redaction, login precedence; cargo test --locked passed 23 tests. No live write validation. -->
- [x] 1.3 Define and test Native protocol v2 envelopes for engine/session lifecycle, task and command identity, deadlines, cancellation, effect phase, structured errors, and bounded diagnostics.
  <!-- aidcp-edge 450cede: protocol v2, long-lived client/session transport, capability digest, identity/deadline/effect validation; cargo clippy -D warnings, focused TS tests, and npm typecheck passed. Cancellation record is frozen; cooperative in-flight cancellation remains task 2.3. -->
- [x] 1.4 Add a deterministic fake HTTP/WebSocket CDP server covering target discovery, events, timeouts, disconnects, reconnects, and post-dispatch ambiguity.
  <!-- aidcp-edge 317cd47: fake CDP integration covers correlated execution, read reconnect, post-dispatch ambiguity/no replay, typed projections, and process cancellation; Rust suite passed 40 tests. No live write validation. -->

## 2. Native engine lifecycle and CDP ownership

- [x] 2.1 Replace the one-shot probe entry point with a long-lived supervised Native engine supporting health, session open/status/close, command execution, cancellation, and graceful shutdown.
  <!-- aidcp-edge 372936c: long-lived process/session, concurrent stdin while commands run, AbortSignal/cancel forwarding, graceful close/shutdown, and process-level cancellation test. cargo test/clippy and TS supervisor tests passed. -->
- [x] 2.2 Implement provider-neutral target discovery, attachment, required CDP domain enablement, event dispatch, bounded reconnect, and session restoration without replaying dispatched effects.
  <!-- aidcp-edge 317cd47: Native owns target refresh/domain setup and permits one read reconnect while dispatched writes become ambiguous; fake CDP tests passed. -->
- [x] 2.3 Enforce one active Xiaohongshu writer per browser session, task/command ownership, deadlines, cancellation safe points, and non-interruptible atomic regions.
  <!-- aidcp-edge 317cd47: runtime/session ownership, single active command, task switching, cancellation, deadlines, write dedupe, and no-replay behavior are enforced and tested. -->
- [x] 2.4 Enforce a CDP method allowlist and bounded/redacted Native diagnostics that exclude cookies, credentials, upload content, and unnecessary DOM text.
  <!-- aidcp-edge 317cd47: explicit CDP allowlist plus deny-unknown bounded command/result models reject generic and sensitive surfaces; Rust and protocol tests passed. -->

## 3. Native page model and interaction primitives

- [x] 3.1 Port page-state classification and URL compatibility for home, explore, `search_result_ai`, note detail, profile, notification, publish, login, error, and unknown states.
  <!-- aidcp-edge 372936c: encoded Native probe and typed projections cover every listed state; fixture/unit tests include search_result_ai compatibility, query redaction, login precedence, notification, creator publish, error, and unknown behavior. -->
- [x] 3.2 Port DOM-first locating with visibility, geometry, ambiguity rejection, bounded retry/escalation, post-action validation, and cache promotion only after repeated success.
  <!-- 2026-08-01 **整条显式弃守（用户裁定）**。不是收窄、不是延后：本 change 不再承担这条。 -->
  - **弃守的是「本 change 继续交付这件事」，不是抹掉已经做出来的东西。** 已落地且在生产上跑的部分
    如实记在这里，归档时**必须**按这个边界写规格，别多写也别少写：
    - **已实现**：三道闸编排（后置校验 / 有界重试与升级 / 反污染回写）落在
      `native/page-engine/src/locating.rs`，判据以窄接口暴露、可脱离浏览器断言；
      配套 `native/page-engine/tests/locating_gates.rs` **27 条脱机用例**。
      判定是**三态**（读到确实发生 / 读到确实没发生 / **读不出来**），读不出来绝不当成成功。
    - **生产覆盖面只有一条命令**：Facebook Reels 面点赞（`facebook/feed_like.rs`）。
      **其余命令面尚未接入** —— 这是本条弃守后留在场上的真实缺口，见下方「留在场上的」。
    - **从未实现、随本条一并弃守**：可见性 / 几何 / 歧义拒绝下沉到各平台的目标解析、
      匹配唯一性闸、动作前守卫层、模型兜底、语义 class 白名单。
    - **锚点暂存与晋升**：代码与 4 条用例都在（`locating.rs` 的暂存区 + 阈值晋升 + 失败即丢弃），
      但**生产上恒空转** —— 每个定位器都是编译进二进制的固定选择器，没有任何非确定性锚点来源，
      暂存区永远进不去东西。对应实装任务（拟人化 5.4 / 5.5）已于 2026-07-30 各自显式弃守。
      **代码不删**：它不产生危害，且一旦将来引入非确定性来源（模型给锚点 / 启发式选择器 /
      运行期学到的路径）就重新有意义；删了是净损失。
  - **⚠️ 归档红线**：本 change 是迁移主线，归档时它的 delta 会**并进主规格**。
    照原文归档 = 主规格声称系统具备上面「从未实现」那一列的能力，**把不打算做的事写成已上线保证**。
    这正是产物门禁 10.4 要求「归档前先收口未勾任务」防的那类风险。**规格只能写「已实现」那一列。**
  - **留在场上的**（弃守本条不等于这件事消失，只是不再由本 change 记账）：
    三道闸目前只覆盖一条命令。要推广到其余命令面，须另立 change —— 那是**覆盖面工作**，
    不是架构工作，因为可替换的缝与桩都已就位（见拟人化 7.17 的结论）。
- [x] 3.3 Implement Native pointer, wheel, keyboard, text, and file-input primitives with current humanization bounds and cancellation-safe atomic actions.
  <!-- Partial 2026-07-27, aidcp-edge 745b754: shared text input now preserves per-Unicode-scalar pacing, cancellation, and deadlines; captcha text uses bounded real keyDown/keyUp pairs with Shift cleanup. The broader pointer/wheel/file primitive task remains open. -->
  <!-- Partial 2026-07-28, aidcp-edge 02313f1: Facebook Feed and comment lazy-load wheel input now preserves the existing 650 px +/-20% distance across 8-15 frames with 16-60 ms inter-frame delays, an interior acceleration/deceleration peak, exact total distance, and cancellation/deadline checks. Rust unit/fake-CDP/full suites, clippy -D warnings, Edge acceptance/full tests, and typecheck passed. Pointer and file-input coverage remain open; no package, deployment, or live-account validation was performed. -->
  <!-- 承接边界登记（2026-07-30，由 restore-native-actuation-humanization-and-locating 的 5.8 回写；本条仍不勾） -->
  - **文件输入（file-input）这一半不在那条 change 内**，勿因其拟人化原语落地就把本条整条勾掉：
    那条 change 承接的是指针 / 滚轮 / 键盘 / 文本四类原语的拟人化边界，**file-input 原语仍属本 change**。
  <!-- 收口（2026-08-01，实读现状后勾选；本条无新增代码改动，是「读出来它已经成立」而非「改到成立」） -->
  - **file-input 两平台都已落地且同源**：小红书 `native/page-engine/src/engine.rs` 的 `PublishUploadImage` 分支、
    Facebook `native/page-engine/src/facebook/publish.rs` 的同名分支。两者**共用同一个** `validate_publish_file`
    （`engine.rs`，扩展名白名单 jpg/jpeg/png/webp + 绝对路径 + 是普通文件 + 元数据可读，任一不满足即
    `InvalidRequest`「授权发布图不可用」），不存在两份各自漂移的校验。
  - **「cancellation-safe atomic」如何成立**：附件写入是**单次 `DOM.setFileInputFiles`**，
    没有可被打断的中间态 —— 原子性来自调用本身，不是靠额外的守卫。
  - **「humanization bounds」在本原语上不适用，如实记而不是假装满足**：`setFileInputFiles` 不是用户手势，
    CDP 上也没有第二条拟人路径可选（选文件对话框不可驱动）。**这一格是空的，不是漏的。**
  - **上传后的校验是有界且诚实的**：小红书 `verify_uploaded_preview` 5s 上限 / 250ms 轮询，
    超时回 `Ambiguous` 而非成功；Facebook 侧 `verify_facebook_uploaded_preview` 走命令死线。
  - ⚠️ **判据强度另有归属，别读成本条已覆盖**：该校验只认「该序号位存在预览图」，
    **不能把预览与本次上传绑定**（上一次残留的预览同样满足）。这条已登记在
    `native/page-engine/command-postconditions.json` 的 `publish_upload_image`（状态 `below_bar`），
    由 change `extend-native-postcondition-coverage` 的 3.2 承接。**本条勾的是原语已落地，不是判据已达标。**
- [x] 3.4 Define bounded structured models for feed cards, search results, note details, profiles, notifications, interaction receipts, and publish receipts.
  <!-- aidcp-edge 804aadc: deny-unknown Rust command/result types cover the complete frozen command manifest; card/note/profile/notification/action/publish projections apply explicit text/list/URL/ID bounds. cargo test and clippy -D warnings passed. Command behavior remains sections 4-6. -->
- [x] 3.5 Restore Native Facebook comment and Xiaohongshu search text entry to one humanized `Input.insertText` call per Unicode scalar, with pre-submit cancellation/deadline checks, exact readback, and cleanup before any failed commit.
  <!-- aidcp-edge 745b754: Facebook comment includes approved group-code suffix in its Cloud-equivalent length-aware ceiling, commit-window cleanup, and no Enter after pre-submit failure; Xiaohongshu search preserves pointer focus, a 700 ms submit floor, and Enter text '\r'. -->
- [x] 3.6 Replace Native captcha text `Input.insertText` with validated visible-ASCII real keyDown/keyUp pairs, real Shift wrapping, bounded dwell/RTT compensation, and best-effort key release after dispatch failure.
  <!-- aidcp-edge 745b754: captcha text is 1..24 visible ASCII, produces zero Input.insertText calls, and reports post-point/type failures no earlier than dispatched. -->
- [x] 3.7 Add fake-CDP event-sequence regressions for Native Facebook comment, Xiaohongshu search, and captcha text input.
  <!-- aidcp-edge 745b754: tests assert per-scalar input, zero captcha insertText, Shift/key release, deadline cleanup/no Enter, commit-window rejection cleanup/no Enter, and group-code-aware comment timing; full Rust 111/111 and focused TypeScript passed. -->
- [x] 3.8 Bind every Native text sequence to its exact target before clearing or typing: Facebook publish/comment require exact editor focus and editor-local selection, Xiaohongshu search requires the visible input instance plus active-target verification, and captcha text requires the frozen `editable` / `opaque` / `none` focus tiers. Fake CDP tests must reject writes to an unfocused target.
  <!-- aidcp-edge 5e66ef4: all four Native text paths now fail with zero character dispatch when focus cannot be proven; fake CDP models focus ownership instead of auto-appending every input event. Rust 115/115, Native focused TypeScript 136/136, Edge full 2435 pass / 1 skip, and production boundary checks passed. -->

## 4. Browse, search, note, profile, and notification commands

- [x] 4.1 Implement feed scan, `browse.next`, bounded scroll, page scroll, and feed refresh with honest exhaustion and movement evidence.
  <!-- aidcp-edge 317cd47: encoded Native router implements feed extraction/scroll/refresh with bounded movement and typed empty/exhausted outcomes; focused router tests and full Edge suite passed. -->
- [x] 4.2 Implement search input, keyword submission, search URL compatibility, filters, and `search_result_ai` result extraction.
  <!-- aidcp-edge 317cd47: Native search route applies keyword/sort/time filters and accepts both search URL forms; fixture and focused routing tests passed. -->
- [x] 4.3 Implement exact-target note open/close, note detail extraction, image browsing, comment scrolling, source restoration, and error-page recovery.
  <!-- aidcp-edge 317cd47: note routes bind note identity, preserve source navigation, and return bounded typed detail/traversal evidence; Rust/TS suites passed. -->
- [x] 4.4 Implement exact-target profile open and notification open/browse/back-home flows.
  <!-- aidcp-edge 317cd47: profile and notification routes use high-level commands with exact profile binding and page-kind postchecks; full Edge suite passed. -->
- [x] 4.5 Implement captcha-assistance capture/click page operations and allowlisted legacy plan steps while keeping authorization and envelope routing in Edge.
  <!-- aidcp-edge 317cd47: bounded screenshot ring, coordinate click, text entry/readback, and allowlisted plan execution are Native; authorization/Cloud envelopes remain Edge-owned. -->
- [ ] 4.6 Add deterministic Native contract tests for every command and page-state transition in this section.

## 5. Interaction commands and effect honesty

- [x] 5.1 Implement exact-target note like and collect with precondition checks, post-action state verification, and idempotent receipts.
  <!-- aidcp-edge 317cd47: Native action router binds current note, recognizes already-satisfied state, verifies changed state, and returns effect-phase receipts; focused tests passed. -->
- [x] 5.2 Implement exact-target follow from note/profile contexts with identity binding and post-action verification.
  <!-- aidcp-edge 317cd47: follow is bound to the requested author/profile and confirms terminal state before success; typed route and full Edge tests passed. -->
- [x] 5.3 Implement approved comment and comment-like commands with target binding, fill/readback/submit validation, and no implicit publish.
  <!-- aidcp-edge 317cd47: comment routes require exact note/comment binding, verify editor readback, and do not expose a generic submit surface; full Edge tests passed. -->
- [x] 5.4 Add crash, disconnect, timeout, cancellation, and duplicate-command tests proving `not_started`, `dispatched`, `confirmed`, and `ambiguous` are never upgraded to false success.
  <!-- aidcp-edge 317cd47: effect, fake-CDP, process-protocol, and TypeScript supervisor tests cover these boundaries; Rust 40, focused 33, and rebased full Edge 2235 tests passed. -->

## 6. Publish commands and safety invariants

- [x] 6.1 Implement publish-entry navigation, mode selection, field filling, topic/candidate insertion, and option setting with readback validation.
  <!-- aidcp-edge 317cd47: all retained atomic publish setup commands route to Native and require field/mode/options postchecks; router and manifest tests passed. -->
- [x] 6.2 Implement image upload and cover selection with explicit file validation, bounded diagnostics, and no file-content leakage over IPC.
  <!-- aidcp-edge 317cd47: Edge downloads bounded HTTPS images to temporary files; Native sets file inputs and selects only an already-confirmed upload index. No file content crosses IPC. -->
- [x] 6.3 Implement scheduled-publish controls with exact target-time evidence and explicit timezone handling.
  <!-- aidcp-edge 317cd47: schedule setup/readback and scheduled capture require exact target time; focused exact-evidence tests passed. -->
- [x] 6.4 Implement submit, post-id capture, scheduled capture, and reconciliation with `ambiguous` handling that forbids blind resubmission.
  <!-- aidcp-edge 317cd47: submit/capture/reconcile are atomic Native commands with independent evidence and no write replay after dispatch; Rust effect tests passed. -->
- [ ] 6.5 Port the existing publish safety and integrity fixtures into Native acceptance tests.
- [x] 6.6 Implement the legacy whole-publish transaction through the same Native primitives or retire its registration and callers under an explicit protocol-compatible migration; no JavaScript whole-publish path may remain packaged.
  <!-- aidcp-edge 317cd47: obsolete publish.request handler is unregistered; retained publish.command atoms route only to Native, with tombstone metadata preserved for protocol compatibility. -->

## 7. Edge direct production integration

- [x] 7.1 Add a selector-free TypeScript Native supervisor/facade that validates protocol v2, version compatibility, lifecycle, bounds, and child-process failures.
  <!-- aidcp-edge 450cede + 372936c: selector-free long-lived facade validates ready manifest/protocol, identities, bounded records/results, lifecycle, timeouts, exits, malformed output, stable errors, cancellation, and effect truth; focused TS tests and npm typecheck passed. Production routing remains tasks 7.2-7.5. -->
- [x] 7.2 Start Native only after task admission, provider resolution, account/environment binding, and browser startup; keep browser lifecycle and Cloud transport owned by Edge.
  <!-- aidcp-edge 317cd47: main starts the required Native runtime only inside the admitted Xiaohongshu browser lifecycle; Edge retains provider, lease, account, and WebSocket ownership. -->
- [x] 7.3 Route the full Xiaohongshu browse/search/note/profile/notification/interaction registry directly to Native with no shadow invocation and no JavaScript fallback.
  <!-- aidcp-edge 317cd47: command manifest parity and direct-routing tests prove every retained Xiaohongshu route is Native-only and the legacy browse executor is absent from main. -->
- [x] 7.4 Route the full Xiaohongshu publish registry directly to Native with no shadow invocation and no JavaScript fallback.
  <!-- aidcp-edge 317cd47: every retained publish.command kind maps to one typed Native command; publish.request is retired and no JavaScript fallback is registered. -->
- [x] 7.5 Map Native results, effect phases, cancellation, and failures to the existing Cloud protocol and task-coordinator receipts without changing Cloud contracts.
  <!-- aidcp-edge 317cd47: Native browse/publish facades emit the existing page/action/publish receipts and preserve correlation, cancellation, and effect truth; acceptance 29/29 passed. -->
- [x] 7.6 Add integration tests proving Native failure is scoped to the owning task/session and non-Xiaohongshu browser providers and flows remain isolated.
  <!-- aidcp-edge 317cd47: supervisor ownership/failure tests and direct-routing isolation checks passed; full Edge suite kept Facebook and other platform tests green. -->

## 8. Customer package removal and Native artifact delivery

- [x] 8.1 Split any genuinely shared selector-free DTOs/utilities away from legacy Xiaohongshu page-rule modules so production Edge code has no runtime import path to them.
  <!-- aidcp-edge 317cd47: browse quiesce types moved to a selector-free module; Facebook no longer imports the legacy Xiaohongshu browse implementation. -->
- [x] 8.2 Remove the legacy Xiaohongshu page-understanding/action modules from production build inputs and add a build-time import-graph gate that fails on reintroduction.
  <!-- aidcp-edge 317cd47: build:dist keeps only the static main graph and fails on forbidden legacy modules/markers; production check reported reachable=109, removed=31. -->
- [x] 8.3 Build and stage architecture-matched Native artifacts with a manifest containing protocol version, platform, architecture, and artifact hash.
  <!-- aidcp-edge 228e3e9 + 317cd47 + 87cd1ab: locked host build stages outside ASAR with engine/protocol/adapter versions, capability digest, platform, arch, executable, and SHA-256; darwin-arm64 worktree b919422... and canonical recovery 952ce40... artifacts verified locally. No installer was built. -->
- [x] 8.4 Package Native outside ASAR, resolve it from `process.resourcesPath`, and add installed-artifact startup/health/command/shutdown smoke tests.
  <!-- aidcp-edge d7e178f + 317cd47 + 87cd1ab: extraResources, startup checks, afterPack smoke, and Electron dev/OL verify-or-rebuild bootstrap are wired and contract-tested; rustup resolves the crate-pinned toolchain when Cargo is absent from PATH. Final installer execution remains release gate 9.3. -->
- [x] 8.5 Extend CI packaging and nested signing/notarization to the Native artifact for supported macOS architectures and Windows x64; fail packaging when a required artifact is missing or incompatible. <!-- 2026-07-31 用户裁定「不打客户端安装包；需要打一次客户端才能验证的功能一律不做」，本条是打包链本身（CI 打包 + 嵌套签名公证），显式弃守。**不是已验证无问题，是不打算验。** 将来若决定出安装包，本条须先回到待办。 -->
- [x] 8.6 Add final ASAR/resources leakage scans for legacy module paths, representative selectors/rules, source maps, debug fixtures, and unredacted diagnostics.
  <!-- aidcp-edge 317cd47: final ASAR scanner accepts a clean Native facade fixture and rejects legacy paths/markers/maps; production dist reports legacy_xhs=absent and source_maps=absent. -->

## 9. Validation, evidence, and release gate

- [x] 9.1 Run Rust formatting, unit/integration/acceptance tests, clippy, and release builds for every locally supported target; record unsupported cross-target checks truthfully.
  <!-- 2026-08-01 实跑（`aidcp-edge` master `fcb1fd2` 工作树，`native/page-engine/`；工具链 1.97.1-aarch64-apple-darwin，
       该 toolchain 不在默认 PATH，需 `export PATH="$HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/bin:$PATH"`）：
       · `cargo fmt --check` 通过
       · `cargo clippy --all-targets -- -D warnings` 通过（无告警）
       · `RUST_TEST_THREADS=1 cargo test --locked` **350 例通过 / 0 失败**（跨全部单测 + 集成 + fake-CDP 套件）
       · `cargo build --release --locked` 通过
       **跨目标一栏如实记：本机 `rustup target list --installed` 只有 `aarch64-apple-darwin` 一个目标，
       所以「every locally supported target」在这台机器上就等于这一个。Windows / x86_64 等目标
       未安装 std，本地无法构建，本条不对它们作任何断言** —— 与 9.3 弃守的跨架构 CI 证据是同一个缺口的两面，
       别把「本地全绿」读成「全平台全绿」。 -->
- [x] 9.2 Run physical Edge dependency installation, focused tests, required safety acceptance suites, full tests, typecheck, and production build.
  <!-- aidcp-edge 317cd47: physical npm tree; focused 33/33, acceptance 29/29, rebased full 2235/2235, typecheck, build:dist, Rust 40/40, rustfmt, and clippy -D warnings passed. No live or packaged-app validation. -->
- [x] 9.3 Run package-input graph checks, packaged smoke tests, signature verification, and leakage scans for locally produced artifacts; record Windows and alternate-architecture CI evidence separately. <!-- 2026-07-31 用户裁定「不打客户端安装包；需要打一次客户端才能验证的功能一律不做」，本条的打包态冒烟 / 签名验证 / 跨架构 CI 证据三项都以出包为前置，显式弃守。**注意仍然成立、且已在做的是另一件事**：打包输入图检查与泄漏扫描的**本地构建那一半**由 `npm run build:dist` 覆盖（生产剪枝 + 分片禁入表），那一半不依赖出包、继续有效。**不是已验证无问题，是不打算验。** 将来若决定出安装包，本条须先回到待办。 -->
> **9.4 / 9.5 已移出本清单（2026-07-31 用户裁定）** —— 授权范围内的小红书只读实况矩阵与写 / 动作验收
> 已收拢到 `docs/real-machine-acceptance-backlog.md` **簇 125**（125.1 / 125.2），不再计入本 change
> 的任务数、不再阻塞归档。簇 125 与簇 122 / 123 共用同一台机器与分身，一次真机 session 连着验。
> **口径不变**：登记 ≠ 已验证；小红书侧自 Native 迁移以来真机零覆盖。

- [x] 9.6 Update this checklist with repository commits, validation evidence, deviations, and package availability; run `openspec validate native-page-engine-production-cutover --strict`.
  <!-- aidcp control + aidcp-edge 317cd47: checklist records completed source gates and explicitly leaves cache/humanization completeness, all-command fixtures, cross-target package/signature, live read/write, and installer release unchecked. Strict validation passed. -->
- [x] 9.7 Integrate and push the clean control and Edge changes under the repository workflow. Build or publish a customer installer only after separate explicit release authorization.
  <!-- aidcp-edge master 317cd47 pushed after fast-forward; this control evidence commit is the final fast-forward input for main. No customer installer was built or published. -->
