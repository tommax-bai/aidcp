## ADDED Requirements

### Requirement: 首页状态卡统一层级并保持平台能力真实

Electron 首页的“今日进展”和“内容发布” SHALL 在小红书与 Facebook 环境中使用一致的客户级表面、内层内容卡、状态标签、间距、悬停、键盘焦点和窄窗口响应式语言。视觉一致 MUST NOT 被解释为功能等同：今日进展的可见指标 SHALL 继续完全由当前环境的权威平台投影决定；Facebook 慢启动脚注 SHALL 只在其既有真实条件下显示；平台切换 MUST 清除上一平台的视觉修饰、文案和操作入口。

#### Scenario: Facebook 今日进展使用共享视觉但保留真实指标
- **WHEN** 客户选择一个 Cloud 投影为 Facebook 的环境
- **THEN** 今日进展 SHALL 使用共享卡片层级并只呈现该投影实际提供的 Facebook 指标，MUST NOT 补画小红书收藏等不存在的指标
- **AND** Facebook 慢启动脚注仍 SHALL 按既有环境级真态显示

#### Scenario: 切换平台不残留前一平台状态
- **WHEN** 客户在小红书与 Facebook 环境之间切换
- **THEN** 今日进展与内容发布 SHALL 立即切换到当前平台的表面修饰、文案与可用操作，MUST NOT 残留前一平台的 class、队列导航或指标格

### Requirement: Facebook 内容发布卡使用单稿语义而非小红书队列语义

Facebook 环境的内容发布卡 SHALL 使用与小红书队列卡一致的视觉层级，但 MUST 只投影当前环境既有的单稿 `publish / lastPublish / publishPreview` 真态。其阶段 SHALL 表达“准备内容、发布审批、提交平台、发布结果”，并按 pending/reminded、approved、submitted、published 等既有状态推进；页面 MUST NOT 显示小红书队列数量、左右切稿、“查看全部进度”或定时发布能力。稿件查看入口 SHALL 仅在既有可审批稿件能力判定为可用时出现，并继续调用既有审批链路。

#### Scenario: Facebook 待审批内容显示单稿状态
- **WHEN** 当前 Facebook 环境有一条 `pending` 或 `reminded` 稿件且稿件预览可用
- **THEN** 内容发布卡 SHALL 显示 Facebook 单稿的待审批状态和“查看内容”入口
- **AND** “发布审批”为当前阶段，“提交平台”和“发布结果”为未完成阶段
- **AND** 队列数量、左右切稿和“查看全部进度” MUST NOT 出现

#### Scenario: Facebook 已审批内容等待提交
- **WHEN** 当前 Facebook 环境的稿件状态为 `approved`
- **THEN** 内容发布卡 SHALL 将“准备内容”和“发布审批”显示为已完成，将“提交平台”显示为当前阶段，并以无需重复操作的真实文案说明后续处理

#### Scenario: Facebook 已提交但结果未确认
- **WHEN** 当前 Facebook 环境的稿件状态为 `submitted`
- **THEN** 内容发布卡 SHALL 显示已提交 Facebook、正在确认公开结果，MUST NOT 将其显示为已发布

#### Scenario: Facebook 空态和窄窗口保持可读
- **WHEN** 当前 Facebook 环境没有进行中稿件和发布历史，或窗口宽度不超过 430px
- **THEN** 空态 SHALL 继续按既有规则默认收起并可展开，展开后的平台文案与阶段语义 SHALL 保持正确
- **AND** 窄窗口中阶段、脚注与合法操作 MUST NOT 横向溢出或被左右轮播控件遮挡
