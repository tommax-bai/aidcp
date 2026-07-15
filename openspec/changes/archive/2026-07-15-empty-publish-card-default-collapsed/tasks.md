## 1. 发布卡默认收展

- [x] 1.1 调整 `aidcp-edge` 发布卡收展投影，使空态在任何运行状态下都默认收起、手动打开时仍展开 <!-- aidcp-edge 90b9dcf -->
- [x] 1.2 同步渲染层注释，明确流程态强制展开、历史态与空态默认收起的规则 <!-- aidcp-edge 90b9dcf -->

## 2. 回归测试

- [x] 2.1 更新发布卡纯逻辑测试，覆盖停止态空态默认收起与手动展开 <!-- aidcp-edge 90b9dcf; targeted Electron tests 85/85 -->
- [x] 2.2 更新 Electron 渲染交互测试，覆盖未运行空态薄条、点击展开及真实流程自动展开 <!-- aidcp-edge 90b9dcf; targeted Electron tests 85/85 -->

## 3. 验证与交付

- [x] 3.1 运行相关 Electron 测试、`npm test` 与 `npm run typecheck` <!-- aidcp-edge: targeted 85/85; acceptance 19/19 with gated real-machine E2E skipped; full 1344/1344; typecheck passed -->
- [x] 3.2 提交并快进集成到 `aidcp-edge` `master`、推送远端，回写提交与验证说明 <!-- aidcp-edge 90b9dcf; fast-forwarded and pushed to origin/master; source-only, no desktop installer built or deployed -->
- [x] 3.3 运行 `openspec validate empty-publish-card-default-collapsed --strict` 并完成归档 <!-- strict validation passed; delta synced into edge-companion-ui baseline; archived 2026-07-15 -->
