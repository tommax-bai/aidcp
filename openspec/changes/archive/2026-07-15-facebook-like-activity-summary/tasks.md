## 1. Edge 活动流实现

- [x] 1.1 在 Facebook 会话中基于点赞成功见证生成作者与正文/标题摘要，并复用现有单行规范化和截断规则
- [x] 1.2 仅为 `ok:true` 点赞发射增强后的结构化 UI 事件，保持缺失字段降级、计数与失败/shadow 语义不变

## 2. 自动化测试

- [x] 2.1 覆盖作者 + 正文/标题、单字段、全缺失、空白规范化与截断的点赞活动文案
- [x] 2.2 运行 Facebook 聚焦测试、Edge 全量测试、acceptance 与 typecheck
  <!-- 2026-07-15: focused facebook-session 35/35; full Edge 1363/1363; acceptance 20/20; typecheck passed. Real-machine E2E remained gated and no real like was executed. -->

## 3. 集成与规范收口

- [x] 3.1 提交并通过安全集成流程推送 `aidcp-edge` 默认分支，不构建桌面安装包
  <!-- aidcp-edge bb00373: rebased onto latest origin/master, acceptance 20/20, full 1363/1363, typecheck passed, then fast-forward pushed to master. Source-only change; no installer build or runtime deployment. -->
- [x] 3.2 回写 Edge commit、验证与发布说明，并通过 `openspec validate facebook-like-activity-summary --strict`
  <!-- 2026-07-15: strict validation passed after recording edge commit, validation coverage, and the source-only/no-installer release boundary. -->
