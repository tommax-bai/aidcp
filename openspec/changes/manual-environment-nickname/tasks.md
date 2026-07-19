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
