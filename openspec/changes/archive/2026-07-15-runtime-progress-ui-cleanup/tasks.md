## 1. Renderer implementation

- [x] 1.1 将七段浏览循环移入运行价值卡，默认收起，并用“查看 / 收起运行步骤”入口控制显示。
- [x] 1.2 将今日进展圆形箭头改为“展开 / 收起 + 方向箭头”的轻量 disclosure 控件。
- [x] 1.3 补齐窄窗口、hover、focus 与 reduced-motion 下的样式边界。

## 2. Verification

- [x] 2.1 更新 Electron companion UI 测试，覆盖运行步骤默认收起、按需展开、真实阶段点亮和今日进展按钮状态。
- [x] 2.2 运行相关 Electron UI 测试、renderer smoke 测试与 `npm run typecheck`。
- [x] 2.3 复核最终差异，并运行 `openspec validate runtime-progress-ui-cleanup --strict`。

## 3. Closeout

- [x] 3.1 提交并按串行集成流程快进到 `aidcp-edge/master`，推送远端。
  <!-- aidcp-edge ca2fb76；已由 land-change 依次通过 test:acceptance、全量 npm test、typecheck，并快进推送 origin/master；纯桌面源码改动，未构建安装包。 -->
- [x] 3.2 回写 Edge 提交 SHA 与验证说明；提交并推送控制仓 OpenSpec 记录。
  <!-- 控制仓完成 strict validate 后归档；不涉及 ECS 部署。 -->
