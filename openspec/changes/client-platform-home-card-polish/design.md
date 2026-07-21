## Context

Electron 首页目前包含两个相邻的客户状态区：今日进展摘要和内容发布。今日进展已经按 Cloud 的平台投影动态隐藏不支持的指标，Facebook 还在卡内承载环境级慢启动；内容发布则有两套数据形态：小红书优先使用多任务发布队列快照，Facebook 使用单稿 `publish / lastPublish / publishPreview` 状态。现有小红书队列卡已完成视觉重做，Facebook 单稿回退仍使用旧式平铺卡，并沿用了“小红书笔记 / 发到飞书”的通用旧文案。

约束包括：不能把小红书队列能力映射到 Facebook；不能依据静态平台模板补齐用量指标；不能改变发布状态机、审批 RPC 或 Cloud 数据真源；平台切换后不得残留前一个平台的 class、文案或可操作入口。

## Goals / Non-Goals

**Goals:**

- 让今日进展与内容发布形成一致的“摘要表面 + 内层内容块 + 克制状态色”视觉语言。
- 让 Facebook 单稿发布卡使用平台真实的四阶段语义，并仅展示现有可用的稿件查看/审批入口。
- 保持小红书队列卡、左右切换、队列入口和已有状态映射不变。
- 覆盖平台切换、宽窄窗口和键盘焦点状态。

**Non-Goals:**

- 不给 Facebook 新增发布队列、多稿轮播、原生定时发布或队列取消能力。
- 不改变 Cloud API、发布状态、稿件审批协议、今日指标口径或慢启动逻辑。
- 不构建桌面安装包，也不做线上真账号发布验收。

## Decisions

### 1. 由现有选中环境的平台值驱动纯展示修饰符

渲染层在每次今日进展和发布卡渲染时写入 `data-platform`，并显式切换 `single-surface` / `queue-surface`。平台切换时复用现有整块重渲染路径，避免从前一环境残留队列导航或 Facebook 样式。

备选方案是从发布 payload 猜平台；该方案在空态或加载失败时没有可靠输入，也可能与选中环境错配，因此不采用。

### 2. 共用结构层级，不共用平台能力

今日进展沿用服务端投影决定的可见 KPI 与 Facebook 慢启动脚注，只增强外壳、标题区和指标容器的层次。小红书内容发布继续使用现有 `queue-surface`；Facebook 使用 `single-surface`，共用相同的柔和外壳、内层白卡、状态 pill、操作层级与响应式规则，但始终隐藏队列数量、轮播箭头和队列页入口。

备选方案是让两个平台都使用队列 carousel；这会把 Facebook 尚不存在的多稿队列表现成可用能力，因此不采用。

### 3. Facebook 单稿状态采用平台真实的四阶段映射

`publishView` 增加可选平台输入。Facebook 使用“准备内容 → 发布审批 → 提交平台 → 发布结果”，并分别映射 pending/reminded、approved、submitted、published；相关标题、元信息和脚注文案使用“内容 / Facebook”，不再显示“小红书笔记 / 发到飞书”。小红书及未识别平台继续保留原映射，避免影响既有回退路径。

### 4. 可操作入口由既有能力判定控制

Facebook 仅在 `publishDraftEntryAvailable(status)` 为真时显示“查看内容”，动作仍进入既有稿件审核页面；按钮不会因为新样式而被乐观显示。队列入口和左右箭头保持隐藏、禁用并从键盘序列中排除。

## Risks / Trade-offs

- [Risk] 平台切换残留 class 或按钮可见性 → 每次渲染先清理互斥表面 class，并在 Facebook 分支明确隐藏/禁用队列相关控件；增加切换回归测试。
- [Risk] Facebook 状态文案与后端状态漂移 → 只对现有 `publishView` 状态做显示映射，不引入新状态或推断发布成功。
- [Risk] 窄屏下 KPI 数量、慢启动脚注与发布阶段拥挤 → 继续使用动态 KPI flex 布局，Facebook 单稿阶段在窄屏改为纵向时间线，并做 430px 视觉验收。
- [Trade-off] Facebook 仍只有单稿摘要，视觉一致不代表功能等同；通过隐藏队列计数、轮播和队列入口明确保留差异。

## Migration Plan

1. 在 Edge 隔离 worktree 内实现展示修饰符、Facebook 文案/阶段映射和 CSS。
2. 运行 UI 逻辑与 Electron DOM 回归、完整测试、类型检查，并用本地 HTML/Electron 页面做宽窄窗口视觉验收。
3. 将 Edge 与控制仓 OpenSpec 记录分别 fast-forward 合入默认分支并推送。
4. 若回归失败，可回退 Edge 单一提交；无数据迁移、协议回滚或服务端部署步骤。

## Open Questions

- None.
