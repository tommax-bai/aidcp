# Tasks

- [x] 1.1 补充 `edge-fleet-console` 规格：运行价值说明必须包含探索进度卡，并覆盖运行中与场次间隔两种状态。
- [x] 2.1 在 `aidcp-edge` 独立 worktree 中实现运行中探索进度卡：文案层级、三段状态、动态进度条。
- [x] 2.2 在场次间隔状态保留同一区域，展示本轮成果已记录与等待继续。
- [x] 2.3 补充 `ui-logic` 与 renderer DOM 单测，覆盖运行中和场次间隔。
- [x] 3.1 运行 OpenSpec 严格校验和 aidcp-edge 相关测试。
- [x] 3.2 使用 worktree 复用依赖软链运行 `npm run electron:dev` 检查客户端效果。
- [x] 4.1 提交 OpenSpec 与 aidcp-edge worktree 改动。

- [x] 5.1 根据复核反馈补充规格：所有获得感卡片移除详细运行步骤入口，并统一连接线的状态语义与完整滑动行程。
- [x] 5.2 在 `aidcp-edge` 移除“查看 / 收起运行步骤”按钮、七段详细步骤 DOM、状态与样式，确保运行中、场次间隔、小时间隔和今日完成均不再渲染。
- [x] 5.3 修正三段流程连接线：运行中蓝色、自然间隔青色、今日完成绿色；圆点位置由线宽推导并完整覆盖横线后复位。
- [x] 5.4 更新 Electron companion UI 回归测试，覆盖入口彻底移除、各状态主题色和圆点完整行程。
- [x] 5.5 运行 Edge 相关测试、typecheck、视觉检查与 `openspec validate runtime-progress-card --strict`。
  <!-- aidcp-edge: focused companion UI 47/47, ui-logic 37/37, full npm test 1343/1343, typecheck passed; four-mode local renderer preview verified theme colors, no detail-step control, and full spark travel; OpenSpec strict validation passed. -->
- [x] 5.6 提交并推送 `aidcp-edge` 与 `aidcp` 默认分支，记录提交与验证结果；不构建桌面安装包。
  <!-- aidcp-edge c8d20a4 on master and origin/master; aidcp recorded in this closeout commit and pushed to main after strict validation. No desktop installer was built. -->

- [x] 6.1 根据第二轮视觉复核补充规格：连接器独立渲染、三阶段均衡展开、圆点圆心完整覆盖线段。
- [x] 6.2 在 `aidcp-edge` 将阶段伪元素连接线改为两个独立连接器，显式同步运行中、场次间隔、小时间隔和今日完成的连接状态与主题色。
  <!-- aidcp-edge 2740a10: renderer emits two explicit connectors and places flow state on connectors instead of step pseudo-elements. -->
- [x] 6.3 将三阶段布局改为五段网格，首阶段靠左、中间阶段居中、末阶段靠右，消除第三阶段右侧大留白并覆盖窄屏。
  <!-- Browser-rendered four-mode preview: flow width 1074px, both outer gaps measured 0px, connector widths 91.6px; running blue, session/hour teal, day green. -->
- [x] 6.4 将圆点动画改为连接器内 `left: 0% → 100%` 的圆心行程，并更新 DOM/CSS 回归断言验证两条连接器、四种主题和完整端点。
- [x] 6.5 运行四状态视觉检查、focused tests、Edge 全量测试、typecheck 与 OpenSpec strict validation。
  <!-- Post-rebase validation on aidcp-edge 2740a10: focused companion UI 47/47, full npm test 1347/1347, typecheck passed; OpenSpec strict validation passed. -->
- [x] 6.6 提交并推送 `aidcp-edge` 与 `aidcp` 默认分支；不构建桌面安装包。
  <!-- aidcp-edge 2740a10 on master and origin/master; aidcp recorded in this closeout commit and pushed to main after strict validation. No desktop installer was built. -->
