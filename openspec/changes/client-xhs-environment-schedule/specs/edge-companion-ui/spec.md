## ADDED Requirements

### Requirement: 环境主页排期入口 SHALL 绑定当前小红书环境

Edge SHALL 在选中小红书环境的 `legacy-workspace` 中、实时工作说明之后与今日进展之前渲染紧凑排期入口。Renderer SHALL 仅调用具名 `environment-schedule:get(envId)` IPC；main SHALL 由本地 envId 解析 profileId 并调用固定 env-scoped customer-auth 路径，Renderer MUST NOT 传 URL、token、envKey 或 accountId。

#### Scenario: 小红书环境加载入口
- **WHEN** 当前选中环境平台明确为小红书且 main 暴露排期 IPC
- **THEN** Edge 读取当前环境排期，并在环境主页渲染今天时段数与当前/下一时段

#### Scenario: 缺少平台或 IPC
- **WHEN** 当前平台未知、不是小红书或 main 未暴露排期 IPC
- **THEN** 入口保持隐藏且 Renderer 不发任何排期请求

### Requirement: 环境排期详情 SHALL 复用现有环境状态与控制

排期详情 SHALL 作为环境主页二级页展示，不得进入或改变内容工作区导航。详情中的启动、浏览器与实时过程入口 SHALL 委托现有当前环境生命周期和状态源；环境启动、关闭、切换及今日用量变化 SHALL 同步反映，排期页面 MUST NOT 自行假定操作成功。

#### Scenario: 从未启动环境查看排期
- **WHEN** 客户打开一个未启动小红书环境的排期详情
- **THEN** 周排期仍可查看，页面展示真实“启动当前环境”动作并复用现有启动按钮逻辑

#### Scenario: 内容工作区保持独立
- **WHEN** 客户打开或关闭环境排期详情
- **THEN** 内容工作区的内容首页、灵感库、我的内容及其状态均不被改写

### Requirement: 排期 UI SHALL 保持紧凑、响应式与可访问

环境主页入口高度 SHALL 控制在 64–72px 范围内。详情在正常宽度以日期条、时间段列表和今日结果区呈现，在窄窗口改为单列且不得造成文档横向溢出。当前、待开始、已结束、未启动和错误状态 MUST 同时使用文字与非颜色线索；动效 MUST 支持 reduced-motion。

#### Scenario: 窄窗口查看排期
- **WHEN** 客户在窄窗口打开环境主页或排期详情
- **THEN** 入口文案可收敛、日期条可在自身容器滚动、详情转为单列，页面主体不横向溢出

#### Scenario: 减少动态效果
- **WHEN** 系统启用 reduced-motion
- **THEN** 当前时段的呼吸或流光动画停止，但文字状态和边框标识仍完整可辨
