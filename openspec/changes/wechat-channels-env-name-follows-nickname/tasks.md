## 1. aidcp-edge 身份事件桥

- [x] 1.1 在视频号运行时订阅认证状态，仅对当前会话已验证匹配且昵称非空的身份发出结构化 `identity` UI 事件。 <!-- aidcp-edge: `wechat-channels/companion-ui.ts` + runtime auth listener -->
- [x] 1.2 Electron 主进程按当前环境平台记录真实昵称来源，并继续复用既有 AdsPower 改名链。 <!-- aidcp-edge: source=`wechat_channels` for verified video-account identity; existing `maybeRenameEnvToNickname` retained -->

## 2. 回归验证

- [x] 2.1 增加视频号身份事件测试，覆盖已验证身份、未验证身份和空昵称门槛。 <!-- `companion-ui.test.ts`: 3/3 pass -->
- [x] 2.2 增加 Electron 身份来源/改名触发相关回归断言，并运行 focused tests 与 `npm run typecheck`。 <!-- focused Edge tests 71/71 pass; typecheck pass -->
- [x] 2.3 运行适用的 Edge 全量测试并确认无协议、风险或发布安全回归。 <!-- `npx tsx --test --test-reporter=dot test/**/*.test.ts`: exit 0 -->

## 3. 收口

- [x] 3.1 运行 `openspec validate wechat-channels-env-name-follows-nickname --strict`，在本文件记录 Edge commit、验证结果和未做真机/安装包验证的边界。 <!-- Edge commit `71dd3de`; focused 71/71, full Edge exit 0, typecheck pass; OpenSpec strict pass. 未启动“tom白”、未调用真实 AdsPower `user/update`、未构建安装包。 -->
- [x] 3.2 将 control 与 Edge 变更分别提交、rebase 后 fast-forward 推送到默认分支；不构建 Edge 安装包、不做真实账号写验证。 <!-- Edge `master` fast-forward pushed at `71dd3de`; control artifacts rebased and `main` fast-forward pushed at `8d1a34e`, followed by this closeout record. -->
