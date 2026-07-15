# Tasks: persona-wizard-mascot-theme

> 代码仅在 `../aidcp-edge.wt/persona-wizard-mascot-theme`（同名分支）开发；控制仓只新增本 change 目录并记录结果。默认不构建 Electron 安装包。

## 1. 规范与隔离

- [x] 1.1 完成任务准入检查，确认 canonical checkout 保持默认分支。
- [x] 1.2 建立 `aidcp-edge` 独立 worktree，并读取现有人设向导、平台渲染与回归测试。
- [x] 1.3 `openspec validate persona-wizard-mascot-theme --strict` 通过。

## 2. 人设浮层视觉落地

- [x] 2.1 在 `.persona-pop` 增加吉祥物局部色彩令牌，更新步骤、卡片、选中态、focus 与 CTA；不影响全局组件。
- [x] 2.2 降低选择项字重并调整文字、边框、背景层级。
- [x] 2.3 用 CSS 几何线条绘制未选项与自定义入口的加号，移除对字体 `+` 字形的依赖。
- [x] 2.4 保持小红书 / Facebook 平台徽标、头像和文案由当前环境平台动态决定。

## 3. 验证与收口

- [x] 3.1 补充人设浮层平台与视觉契约回归测试。
- [x] 3.2 运行聚焦测试、`npm test` 与 `npm run typecheck`。
- [x] 3.3 fetch + rebase 最新 `origin/master`，串行 fast-forward 集成并推送；不 force push。
- [x] 3.4 回写代码提交、验证结果与发布边界；运行 OpenSpec 严格校验。

## 实施记录

- 代码：`aidcp-edge` `af3f17b` （已 fast-forward 推送至 `origin/master`）。
- 聚焦回归：`fleet-console.test.ts` 37/37 通过。
- 安全验收：19 通过，1 个需 `AIDCP_E2E=1` 的真机联调门禁项跳过。
- 全量回归：1339/1339 通过；`npm run typecheck` 通过。
- 发布边界：本次是 Edge Electron 渲染层源码变更，无云端/协议/数据变更；按开发规范不自动构建或发布安装包。
