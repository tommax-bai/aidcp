# Tasks

## 1. Contract and implementation

- [x] 1.1 补充首作庆祝慢节奏与横向流光契约。
- [x] 1.2 将吉祥物改为延迟 260ms、持续 1400ms 的单次放大归位。
- [x] 1.3 将撒花改为约 300ms 后启动、持续 1250ms 的错峰单次展开。
- [x] 1.4 移除预期文字弹跳，改为 1980ms 后启动、持续 1700ms 的横向流光。
- [x] 1.5 保持 `prefers-reduced-motion` 静态降级。

## 2. Verification and delivery

- [x] 2.1 新增先失败后通过的 Electron 样式契约测试。
- [x] 2.2 运行实际渲染检查、相关 Electron 测试、Edge 全量测试、typecheck 与 OpenSpec 严格校验。
- [x] 2.3 提交、快进合并并推送 Edge `master` 与控制仓 `main`；Edge 提交 `21a1675`，不构建安装包。
