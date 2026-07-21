## 1. 运行态视图模型

- [x] 1.1 调整 Edge 运行态获得感视图模型，不再返回三段流程，并仅用 `inspirationSummary` 的真实正数结果补充进度元信息。
- [x] 1.2 调整 renderer 进度元信息的结果状态标记，保证普通进度与真实收获使用不同但克制的视觉语义。

## 2. 样式与交互回归

- [x] 2.1 优化运行态移除流程后的分隔、垂直留白、结果色和窄屏表现，保留其他状态的三等分流程及减少动态行为。
- [x] 2.2 更新纯逻辑与 Electron DOM/CSS 测试，覆盖运行态无流程、真实结果、无结果不推断，以及间隔/完成/首帖流程不退化。

## 3. 验证与交付

- [x] 3.1 在 Edge 独立 worktree 运行聚焦测试和 `npm run typecheck`，记录结果与任何偏差。
  <!-- aidcp-edge commit c808000: ui-logic 55/55 and companion-ui 73/73 passed with dot reporter; npm run typecheck passed; wide and 430px Electron renders were visually checked. -->
- [x] 3.2 运行 `openspec validate simplify-running-guidance-flow --strict`，回写实现提交与验证证据，并按 ff-only 规范集成和推送。
  <!-- aidcp-edge c808000 was rebased onto origin/master, passed acceptance 28/28, full suite 2127/2127, and typecheck; scripts/land-change ff-only pushed and synchronized origin/master. No Edge installer or dev deployment was requested. -->
