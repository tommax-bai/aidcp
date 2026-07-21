## Why

客户端获得感卡片的普通运行态同时展示价值文案、三段流程和浏览进度，其中“正在查看第 N 条”与进度区重复，“持续判断中 / 持续筛选中”又没有新增可验证结果。三列动态流程因此放大了系统机制，却削弱了用户对真实进展和实际收获的感知。

## What Changes

- 普通运行态不再展示“浏览与互动 / 判断匹配度 / 继续寻找灵感”三段流程列。
- 普通运行态继续展示价值标题、价值说明和真实浏览进度，并仅在存在真实灵感记录时补充结果摘要。
- 自然间隔、今日完成和首帖创作继续保留三段流程，因为这些状态存在真实阶段切换或需要解释后续动作。
- 收紧运行态卡片移除流程列后的垂直节奏、分隔与结果信息层级，同时保持窄屏、减少动态偏好和既有客户端视觉语言。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `runtime-value-guidance`: 将普通运行态从三段机制流程改为以真实进度和已记录灵感结果为中心；其他具有阶段意义的状态继续保留流程。

## Impact

- `aidcp-edge/src/electron/renderer/ui-logic.js`：调整运行态获得感视图模型。
- `aidcp-edge/src/electron/renderer/renderer.js` 与 `styles.css`：按运行态条件隐藏流程并优化紧凑布局及结果摘要。
- `aidcp-edge/test/electron/`：更新纯逻辑和 DOM/CSS 回归覆盖。
- 不改变 Cloud/Edge 协议、运行节奏、浏览动作、数据来源或依赖。
