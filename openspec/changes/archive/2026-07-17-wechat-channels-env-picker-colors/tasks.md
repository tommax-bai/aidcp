## 1. 视频号环境标签配色

- [x] 1.1 在 Edge renderer 中为 `plat-wechat_channels` 环境平台标签增加复用 `--plat-wechat` 的绿色文字与浅绿背景，保持选中蓝和状态色不变。 <!-- aidcp-edge worktree: `.env-plat.plat-wechat_channels` 使用 `var(--plat-wechat)` + `#e7f8ef` -->
- [x] 1.2 增加 Electron renderer CSS 契约测试，覆盖视频号标签类名与绿色变量连接。 <!-- targeted `fleet-console.test.ts` 41/41 pass -->

## 2. 验证与收口

- [x] 2.1 运行相关测试、Edge 全量测试与 typecheck；运行 `openspec validate wechat-channels-env-picker-colors --strict`。 <!-- targeted 41/41；acceptance 22/22；full 1521/1521；typecheck pass；OpenSpec strict valid -->
- [x] 2.2 提交 Edge 分支、fast-forward 集成并推送默认分支；同步任务证据并提交推送控制仓 OpenSpec 变更，不构建桌面安装包。 <!-- aidcp-edge 481fa20 已 ff push origin/master；控制仓以本任务证据提交；未运行 electron:build*，无 runtime deploy -->
