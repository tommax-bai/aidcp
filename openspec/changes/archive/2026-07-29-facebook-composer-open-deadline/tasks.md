## 1. OpenSpec 与并行协调

- [x] 1.1 补齐 proposal / design / `facebook-post-publish` delta，固化首页安全门、40 秒 composer deadline、生产字段护栏与“不泛化 cloud 自动重投”边界；`openspec validate facebook-composer-open-deadline --strict` 通过。 <!-- aidcp: 2026-07-16 strict pass；代码实现前契约已就绪 -->
- [x] 1.2 运行 `scripts/task-preflight`，从最新 edge/cloud 默认分支创建匹配 worktree；核对 `fb-publish-fill-deadline` 对 `platform-profile.ts` 与同 capability 的落地顺序，集成/归档串行。 <!-- preflight 全绿；edge worktree 基于 origin/master 239c44c，cloud worktree 基于 origin/master 6a609ff；fill budget 已在默认分支，当前 change 叠加其既有 timeoutMs/resultSlackMs 机制，归档仍按落地序串行 -->

## 2. aidcp-edge — 首页门与 composer deadline

- [x] 2.1 在 `src/facebook/publish-executor.ts` 增加只读页面状态分类；`navigate_entry` 在小于 cloud 30 秒窗口的有界 deadline 内确认首页路由、主结构和无阻断态，同域旧小组/详情页不得冒充成功，并输出脱敏阶段日志。 <!-- edge worktree: 20s bounded readiness；复用 classifyFacebookSurface；日志仅含 stage/surface/path/attempts/elapsedMs -->
- [x] 2.2 将 `openComposer()` 改为使用 `payload.timeoutMs` 的总 deadline：每轮先重验首页语境，再有界等待入口（最多 20 秒）、单击一次并用剩余预算等待编辑器；保留 `no_target` / `post_validate_failed` 诚实结果，不重复点击、不自动重跑整序列。 <!-- edge worktree: 同一 DOM 快照读取首页状态与入口坐标；定向测试通过 -->
- [x] 2.3 修复目标护栏读取 `params.optionKind` / `params.optionValue`；个人时间线允许继续，其他显式目标 `unsupported_target`，测试不再使用生产不会产生的 `params.value` 授权形状。 <!-- edge worktree: canonical params only；冲突旧 value 不绕过 -->
- [x] 2.4 扩展 `test/facebook/publish-executor.test.ts`：覆盖入口晚渲染、预算耗尽、旧小组页同文案不点、导航后首页才点、登录/checkpoint/阻断 dialog、编辑器晚出现/不出现、生产目标参数与不支持目标。 <!-- 2026-07-16 latest rebased master: 定向 26/26 pass；typecheck pass -->

## 3. aidcp-cloud — Facebook 单步预算

- [x] 3.1 在 `src/publish-agent/platform-profile.ts` 仅为 Facebook `select_mode` 下发 `timeoutMs=40_000`；小红书命令计划不携带该预算，既有 fill budget 与命令顺序不变。 <!-- cloud worktree: Facebook-only constant layered on existing timeoutMs contract；no protocol edits -->
- [x] 3.2 增加/更新 publish-agent 单测，坐实 Facebook `select_mode` 40 秒、cloud 等待 `40s + resultSlackMs(8s)`、XHS 零回归与协议消息零变更。 <!-- 2026-07-16: command-sequencer + fill-budget 37/37 pass；typecheck pass -->

## 4. 验证

- [x] 4.1 aidcp-edge 先跑相关 Facebook publish 定向测试，再跑 `npm run test:acceptance`、`npm test`、`npm run typecheck`；全部通过且无协议漂移。 <!-- 2026-07-16 latest rebased master: targeted 26/26；acceptance 22/22 + gated E2E skip；full 1536/1536；typecheck pass；protocol count 90 -->
- [x] 4.2 aidcp-cloud 先跑发布相关 acceptance，再跑定向测试、`npm test`、`npm run typecheck`；全部通过且安全套件保持绿色。 <!-- 2026-07-16 latest rebased master: targeted 37/37；acceptance 54/54 + gated E2E skip；full 2302 pass / 6 existing gated skips；typecheck pass；protocol count 90 -->
- [x] 4.3 再次运行 `openspec validate facebook-composer-open-deadline --strict`，检查 artifacts 与实际实现一致。 <!-- 2026-07-16 strict pass after implementation -->

## 5. 集成、dev 部署与运行时边界

- [x] 5.1 edge/cloud 分别提交、推送 change 分支，记录 commit SHA 与验证结果；rebase 最新默认分支后串行 fast-forward land，绝不 force-push。 <!-- change branch: edge 401706b / cloud ee595c1 已推；rebase 最新 origin/master 后 full test + typecheck 重验，串行 FF land 并推 master：edge d9e6948（1536/1536），cloud 0392748（2302 pass / 6 existing skips）；未 force-push -->
- [x] 5.2 更新本 tasks 记录 edge/cloud/default-branch commit、偏差、部署说明；控制 repo 仅提交本 change 路径，保留并绕开 canonical checkout 其他未关联改动。 <!-- edge master d9e6948；cloud master 0392748；无协议变更、无 cloud 整序列自动重投；control 仅暂存本 change 路径，其他未关联文件保持未暂存 -->
- [x] 5.3 运行 `scripts/deploy-target dev --check`；从干净 cloud `master` 按备份、rsync 排除 secrets/deps/git、重启 `aidcp-cloud.service` 的安全顺序部署 dev。 <!-- target check pass；以 cloud master 0392748 的 git archive 快照部署；备份 cloud.bak.20260716-190017.tar.gz + .env.bak.20260716-190017；checksum dry-run 确认远端仅 3 个本 change 文件内容不同后精确 rsync，依赖清单未变；19:00:46 CST 重启成功 -->
- [x] 5.4 验证 dev cloud service、NRestarts、8787/8090/8088、health、PostgreSQL、飞书 WS 与无关 `isales*` 服务；失败则按备份回滚。 <!-- aidcp-cloud active，NRestarts=0；8787/8090/8091/8088 listening；panel/client-auth/Nginx health 均 ok；PostgreSQL select 1；Feishu WS onReady；isales-api/engine/scheduler/worker 均 active；启动后无 error/fatal/failed 日志 -->
- [ ] 5.5 不构建 edge 桌面安装包。使用明确更新后的 edge 做非提交 composer 探针；真实发布验收只在用户另行批准的新且不重复草稿上执行，确认浏览闭环忙时先落个人首页、只开一次 composer、最多发布一次且不落小组。未获真实发布授权时如实留待验收，不宣称已做。 <!-- 未构建安装包、未执行真实发布。当前本机 Electron 开发实例的 dist 构建时间为 18:51，早于 edge master d9e6948 的 18:53 提交，且另有并行 edge 测试进程；为避免抢占/覆盖其他会话，未重启旧实例或另起冲突 runtime。待明确更新后的 edge runtime 可安全接管 Tianxing Bai 时执行非提交探针。 -->
