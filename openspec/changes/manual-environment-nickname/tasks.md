## 1. 人工昵称数据与覆盖保护

- [x] 1.1 在 Edge 花名册归一、设置迁移/保存、环境 handle 与 fleet snapshot 中保留受限的 `nameSource: 'manual'` 标记，并覆盖旧设置兼容测试。 <!-- Edge: fleet normalize + renderer roster + main handle/snapshot preserve only exact manual source; legacy and forged-source tests pass -->
- [x] 1.2 将左栏显示名优先级改为人工昵称 → 平台真实昵称 → 环境名 → 尾号兜底，并补纯逻辑测试。 <!-- Edge: uiLogic.railDisplayName and fleet model carry manual priority; focused tests pass -->
- [x] 1.3 让 AdsPower 实时名回填和登录昵称自动改名在人工来源环境上跳过，同时保留非人工环境现有行为与诚实失败语义。 <!-- Edge: reconcileRosterNames + maybeRenameEnvToNickname fail closed for manual, including in-flight local overwrite guard -->

## 2. 双击编辑与视觉反馈

- [x] 2.1 将展开栏昵称双击动作改为就地编辑，支持 Enter/失焦提交、Escape 取消、空值拒绝，并避免双击同时触发浏览器显示/归位。 <!-- Edge: 220ms single/double gesture arbitration; Enter/blur/Escape/blank tests pass -->
- [x] 2.2 人工昵称提交后即时保存并如实提示成功/写盘失败；给人工昵称增加轻微差异色和来源提示。 <!-- Edge: immediate settings save, muted purple manual style/title, explicit non-persisted warning -->
- [x] 2.3 更新 Electron fleet renderer 测试，覆盖双击编辑、人工来源样式、持久化 payload、取消/空值和失败提示。 <!-- Edge focused suite 194/194 pass -->

## 3. 验证与收口

- [x] 3.1 运行相关 Edge focused tests 与 `npm run typecheck`，修复回归。 <!-- 194/194 focused Edge tests pass; npm run typecheck pass -->
- [x] 3.2 运行适用的 Edge 全量测试与 `openspec validate manual-environment-nickname --strict`，记录真实验证边界。 <!-- Edge full `npx tsx --test --test-reporter=dot test/**/*.test.ts` exit 0; OpenSpec strict pass. 未启动真实环境、未调用真实 AdsPower user/update、未构建安装包。 -->
- [x] 3.3 将 Edge 与 control 变更提交、rebase 后 fast-forward 推送默认分支；按 dev 部署规范发布运行时代码，不构建桌面安装包。 <!-- Edge `master` fast-forward pushed at `bf547da`; control artifacts commit `b881d27` plus this closeout record. Deployment deviation: change is Edge desktop-only; dev has no Edge service artifact, and publishing it requires an installer build explicitly out of scope, so no server deploy/package was performed. -->

## 4. 统一昵称解析与复现修复

- [x] 4.1 核对真实运行进程与本地设置，确认 `Tianxing Bai1` 未落盘的原因。 <!-- Electron dev process started 2026-07-19 21:21:53 +0800, before Edge commit `bf547da` at 21:42:07; settings still contained `k1ei3dbi -> Tianxing Bai` with no manual source. -->
- [x] 4.2 将左栏文字函数抽象为主进程与 renderer 共用、返回显示名与来源的统一环境昵称解析器，并保留兼容包装。 <!-- Edge: added process-neutral `renderer/environment-display-name.cjs`; uiLogic and main persona notice share it through the explicit CommonJS boundary finalized in task 6. -->
- [x] 4.3 把标题栏、互动/内容工作区、环境引导、人设浮层、桌面提醒与浏览器内人设横幅统一接到解析器；第三方参与者/作者昵称保持业务 DTO 原语义。 <!-- Edge: all current-environment anchors use the resolver; routeStatus also refuses to overwrite manual names with stale system heartbeats. -->
- [x] 4.4 增加统一优先级与各消费位置回归测试，运行 focused tests、typecheck、全量 Edge tests与 OpenSpec strict validation。 <!-- Edge focused display/persona suite 109/109 pass; `npm run typecheck` exit 0; full `tsx --test --test-reporter=dot test/**/*.test.ts` exit 0; OpenSpec strict pass. -->
- [x] 4.5 提交、rebase、快进推送 Edge/control 默认分支；记录当前旧进程需重启和未构建安装包的边界。 <!-- Edge `master` fast-forward pushed at `4b743db`; control artifacts are committed/pushed with this record. The Electron process started before the feature still requires restart; no installer was built and desktop source has no dev server artifact to deploy. -->

## 5. 昵称数据即时更新与失败回滚

- [x] 5.1 增加昵称专用的窄 IPC，使主进程仅在写盘成功后提交内存花名册，失败恢复旧 settings 并返回真实原因。 <!-- Edge: preload exposes only `saveEnvironmentNickname`; main `fleet:setManualNickname` snapshots settings, restores on write failure, and syncs handles only after success. -->
- [x] 5.2 renderer 在第一次等待前乐观更新昵称并标记 pending；成功确认人工来源，失败恢复原昵称、来源和当前环境身份锚点。 <!-- Edge: env-scoped pending resists stale fleet/status snapshots; rail/title/workspace/persona/guide anchors redraw optimistically and rollback together. -->
- [x] 5.3 更新回归测试，覆盖 pending、成功收敛、失败回滚、窄 IPC 与本地非 Cloud 边界，并完成 focused、typecheck、全量和 OpenSpec strict 验证。 <!-- Edge focused fleet/IPC/scope suite 69/69 pass; `npm run typecheck` exit 0; full `tsx --test --test-reporter=dot test/**/*.test.ts` exit 0; OpenSpec strict pass. -->
- [x] 5.4 提交、rebase、快进推送 Edge/control 默认分支；记录源码仍需重启加载且未构建安装包的边界。 <!-- Edge rebased onto `d950e7f`, revalidated, then `master` fast-forward pushed at `ebdacf2`; control artifacts are committed/pushed with this record. Existing Electron processes still require restart to load source; no installer was built and no Cloud deployment applies. -->

## 6. Electron CommonJS 启动边界回归修复

- [x] 6.1 使用项目 Electron 31.7.7 内置 Node 20.18.0、且不经过 `tsx` loader，复现 `persona-notice.cjs` 同步加载共享 `.js` 解析器时的 `ERR_REQUIRE_ESM`。 <!-- Edge feature worktree: native Electron process exited 1 at `require('./src/electron/persona-notice.cjs')`; stack points to `renderer/environment-display-name.js` under root `type: module`. -->
- [x] 6.2 将共享解析器改为明确的 `.cjs` 边界，同步更新 main、renderer、HTML 与测试引用，不修改根目录 `type`，不把主进程启动链改为异步。 <!-- Edge: renamed the shared UMD resolver to `renderer/environment-display-name.cjs`; persona notice, uiLogic, index.html and renderer harnesses now reference that explicit boundary. The same native Electron command exits 0 and prints `persona-notice-load-ok`. -->
- [x] 6.3 增加 Electron 内置 Node 无 loader 启动冒烟，并完成 focused、typecheck、全量 Edge tests 与 OpenSpec strict 验证。 <!-- Edge: persona notice test spawns the Electron executable with `ELECTRON_RUN_AS_NODE=1` and empty `NODE_OPTIONS`, verifies Electron 31 / Node 20 and sync load; 294 focused tests pass; `npm run typecheck` exit 0; full `tsx --test --test-reporter=dot test/**/*.test.ts` exit 0. OpenSpec strict pass. -->
- [x] 6.4 提交、rebase、复验并快进推送 Edge/control 默认分支；保持未构建安装包、无 Cloud/dev 部署的真实边界。 <!-- Edge `master` remained current after fetch/rebase, native Electron smoke + 294 focused tests + typecheck passed again, then fast-forward pushed at `70ee1ec`; control artifacts are committed/pushed with this closeout record. Desktop source has no dev server artifact, so no Cloud/dev deployment applies; no installer was built. -->
