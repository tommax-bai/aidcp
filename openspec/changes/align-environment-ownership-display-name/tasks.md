## 1. Console 环境归属显示

- [x] 1.1 对齐 `ClientEnvironmentView` 与 Cloud 环境注册表已有的环境名和绑定账号显示投影，同时保留滚动发布缺字段兼容。
  <!-- aidcp-console: environmentName/account.displayName are optional additive fields on the registry view, so an older Cloud still falls back without crashing. -->
- [x] 1.2 增加环境归属显示名辅助函数，已绑定环境消费 `account.displayName`，未绑定环境回落 `environmentName/label/envKey`。
  <!-- aidcp-console: environmentOwnershipDisplayName consumes only Cloud account.displayName for bound accounts; environment-only fallbacks remain display-only. -->
- [x] 1.3 将环境归属待分配和已分配列表统一改用该辅助函数，保持 scope 保存载荷及 `envKey` 归属逻辑不变。
  <!-- aidcp-console: both tables render 显示昵称 through the envKey-indexed registry map; add/save code still carries the original label/platform/envKey fields. -->
- [x] 1.4 补 focused tests，覆盖人工别名覆盖旧环境备注、已分配行按 `envKey` join，以及未挂载/旧 DTO 回落。
  <!-- aidcp-console: ClientUsersPage + accountDisplay focused run passed 18/18; typecheck passed. -->

## 2. 验证与交付

- [x] 2.1 在 Console worktree 运行 focused tests、全量测试、typecheck 和 build，记录真实通过范围。
  <!-- aidcp-console: focused 18/18, full 300 passed + 1 skipped, typecheck and production build passed. The repository has no lockfile, so npm ci was impossible; dependencies were installed physically with npm install --no-package-lock --prefer-offline and no manifest was changed. -->
- [x] 2.2 运行 `openspec validate align-environment-ownership-display-name --strict` 并核对仅 Console 运行时受影响。
  <!-- Strict validation passes. Source diff is confined to aidcp-console types/page/tests; Cloud and Edge already provide the authoritative alias write and display projection. -->
- [x] 2.3 提交后 fetch/rebase 最新 `origin/master`，通过 `land-change` fast-forward 推送 Console 默认分支。
  <!-- aidcp-console eda6a43: rebased/up-to-date with origin/master; land-change reran full 300 passed + 1 skipped and typecheck, then fast-forward pushed master without force and cleaned the worktree. -->
- [x] 2.4 按部署规范从干净 Console 默认分支发布到 `dev`，验证静态站点与服务健康，不触碰 `ol` 或 Edge 安装包。
  <!-- DEV 121.89.85.150: deploy-target check passed; clean console master eda6a43 built and was backed up at /opt/aidcp/console.bak.20260729-195622.tar.gz. Dist synced without deletion; local/remote SHA-256 matched for index, CSS and assets/index-wrCxsmR6.js. Nginx active, local/public Console and JS returned 200, Panel health returned {"ok":true}, and all 4 running isales services remained untouched. OL, Cloud, Edge and installers were not changed. -->
- [x] 2.5 回写提交、验证、部署与偏差证据，提交并推送 control 变更后归档。
  <!-- Evidence recorded above. Console eda6a43 and control 0db63716 were fast-forward pushed to their default branches; the only deviation was physical npm install without a lockfile, with no manifest change. Change is ready for archive. -->
