# Tasks

## 1. Contract and implementation

- [x] 1.1 补充吉祥物庆祝与首轮预期分段动效契约。
- [x] 1.2 将吉祥物峰值提高到 1.12，并让十粒撒花围绕吉祥物单次展开。
- [x] 1.3 在首段结束后延迟播放一次“20 条 → 1 条”整行聚焦动效。
- [x] 1.4 为两段动效补全 `prefers-reduced-motion` 静态降级。

## 2. Verification and delivery

- [x] 2.1 新增先失败后通过的 Electron 样式契约测试。 <!-- 新契约修复前失败，样式落地后通过 -->
- [x] 2.2 运行相关 Electron 测试、Edge 全量测试、typecheck 与 OpenSpec 严格校验。 <!-- 相关 132/132；全量 1364/1364；typecheck、diff check、OpenSpec strict 全过；Electron 实际渲染双时点检查无裁切 -->
- [x] 2.3 提交、快进合并并推送 Edge `master` 与控制仓 `main`；Edge 不构建安装包。 <!-- aidcp-edge 02c3d76 已推 origin/master；控制仓由本归档提交落 main；按规范不打安装包 -->
