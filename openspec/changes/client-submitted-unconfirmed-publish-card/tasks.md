## 1. Edge 发布卡实现

- [x] 1.1 在 `publishView` 中增加独立 `submitted` 卡片投影，使本次标题、编号和相对时间优先于旧 `lastPublish`，并保持未确认文案与第四节点未完成。
- [x] 1.2 调整发布卡收展与渲染状态处理，使 `submitted` 自动展开且不影响 `pending/approved/published/rejected/failed` 既有行为。

## 2. 验证与契约

- [x] 2.1 扩充 Electron `ui-logic` 聚焦测试，覆盖 submitted 有旧历史、无历史、收展状态及 published 转换。
- [x] 2.2 在独立 Edge worktree 安装实体依赖，运行聚焦测试与 `npm run typecheck`。 <!-- entity node_modules via npm ci --prefer-offline; ui-logic 53/53; companion-ui 69/69; typecheck passed -->
- [x] 2.3 运行 `openspec validate client-submitted-unconfirmed-publish-card --strict` 并记录验证结果。 <!-- valid; git diff --check passed in control and edge worktrees -->

## 3. 集成收口

- [ ] 3.1 提交并推送 Edge 与控制仓同名分支，串行快进/挑选精确提交集成到各自默认分支并复验。
- [ ] 3.2 在本文件记录仓库、commit SHA、验证结果及“未构建客户端安装包”的交付边界。
