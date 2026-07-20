## 1. Edge 发布卡实现

- [x] 1.1 在 `publishView` 中增加独立 `submitted` 卡片投影，使本次标题、编号和相对时间优先于旧 `lastPublish`，并保持未确认文案与第四节点未完成。
- [x] 1.2 调整发布卡收展与渲染状态处理，使 `submitted` 自动展开且不影响 `pending/approved/published/rejected/failed` 既有行为。

## 2. 验证与契约

- [x] 2.1 扩充 Electron `ui-logic` 聚焦测试，覆盖 submitted 有旧历史、无历史、收展状态及 published 转换。
- [x] 2.2 在独立 Edge worktree 安装实体依赖，运行聚焦测试与 `npm run typecheck`。 <!-- entity node_modules via npm ci --prefer-offline; ui-logic 53/53; companion-ui 69/69; typecheck passed -->
- [x] 2.3 运行 `openspec validate client-submitted-unconfirmed-publish-card --strict` 并记录验证结果。 <!-- valid; git diff --check passed in control and edge worktrees -->

## 3. 集成收口

- [x] 3.1 提交并推送 Edge 与控制仓同名分支，串行快进/挑选精确提交集成到各自默认分支并复验。 <!-- feature: edge fb8ee0d, control 45b58bf; integrated: edge master a0ecff9, control main 91df893; both feature branches pushed, edge master pushed -->
- [x] 3.2 在本文件记录仓库、commit SHA、验证结果及“未构建客户端安装包”的交付边界。 <!-- edge canonical verification: ui-logic 53/53, companion-ui 69/69, npm run typecheck passed; OpenSpec strict valid; source-only delivery, no Electron installer/package build or release -->

## 4. 重启恢复补全

- [x] 4.1 复盘实际运行链路并确认缺口：新版客户端过滤自动化 WebSocket 的发布业务数据，重启后本地仅有旧 `lastPublish`。
- [x] 4.2 修订 proposal/design/spec，把登录、重启、切换环境后的 customer-auth HTTP 恢复纳入 submitted 卡片契约，并明确不恢复 WebSocket 业务数据。
- [x] 4.3 复核 Cloud 环境 overview 的归属校验、submitted/lastPublished 分离查询与安全 DTO 测试。 <!-- Cloud focused: client-auth + publish store + ui-snapshot 86/86 passed; response omits accountId and keeps current submitted separate from last published -->
- [x] 4.4 复核 Edge overview IPC、首次未知态、旧历史 + submitted 恢复、失效刷新与并发保护测试。 <!-- Added restart regression using Tmax-shaped old local history + #160 submitted HTTP overview; Edge focused 202/202 passed -->

## 5. 补充验证与交付

- [x] 5.1 运行 Cloud/Edge 聚焦测试、相关 acceptance/full suite 与两仓 `npm run typecheck`。 <!-- focused cloud 86/86, edge 202/202; acceptance cloud 60/60, edge 26/26; both full suites exit 0; both typechecks passed -->
- [ ] 5.2 运行 `openspec validate client-submitted-unconfirmed-publish-card --strict`，提交并推送三仓同名分支，串行集成到最新默认分支。
- [ ] 5.3 确认依赖的 Cloud overview 已部署到 dev，验证服务、HTTP 鉴权边界与目标账号数据；不构建 Edge 安装包。
