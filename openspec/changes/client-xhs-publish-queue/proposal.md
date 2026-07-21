## Why

小红书客户当前只能在运行首页看到一条当前稿件或上一条发布记录，无法查看同一环境中并行排队、生成、待确认和平台确认中的全部内容，也无法从客户界面安全取消错误任务。客户端需要一个环境隔离、状态诚实、可取消的发布队列，让客户不依赖管理后台即可知道每条内容正在发生什么。

## What Changes

- 将小红书运行首页现有“发布过的 AI 写好的笔记”入口升级为紧凑的“发布进度”摘要，展示活跃数量、待确认数量和最需要处理的一条内容。
- 在现有 Electron 主窗口内容工作区内新增“发布队列”页面，分离需要客户处理、系统处理中和最近完成的内容，并以客户可理解的四阶段进度呈现 Cloud 的真实生命周期。
- 在客户鉴权域新增按 `envKey` 隔离的发布队列只读投影，合并尚未开跑的发布委托、活跃发布生命周期和最近终态，但不暴露 `accountId`、原始 snapshot 或内部诊断。
- 为仍可取消的发布委托提供逐条取消和二次确认；请求携带任务当前 `version`，并区分立即“已取消”与工作器安全收口中的“取消中”。
- 保留既有稿件审核中的发布/取消语义；进入平台下发、已提交或定时等待公开的内容不冒充可撤回。
- 只在平台明确为小红书的已选环境展示和读取队列；切换环境时清除旧页面与请求代次，普通数据读写继续走客户 HTTP，与浏览器和自动化引擎生命周期解耦。
- 初始实现先停留在隔离 feature worktree 供评审；客户随后明确授权集成，因此本轮继续合入并推送默认分支、部署 Cloud 到 `dev`。Edge 只交付默认分支源码，不构建或发布桌面安装包。
- 将客户阶段“你来确认”精修为更明确但不带内部流程感的“发布确认”，并为待确认、已确认等状态提供阶段专属文案；重做桌面横向与窄屏纵向步骤连接线，使线段只连接相邻圆点、不穿过文案，也不在首尾留下悬空短线。
- 为首页展开态发布卡增加克制的左右切换：多条进行中内容可在卡内逐条查看，左右按钮贴近卡片两侧、默认弱化且在 hover / 键盘聚焦时加深；单条内容不显示切换控件，切换环境时复位且不改变 Cloud 队列顺序或状态真相。

## Capabilities

### New Capabilities

- `client-publish-queue`: Defines the XHS client publish-summary entry, full-page environment-scoped queue, truthful customer lifecycle projection, cancellation interaction, and terminal-history separation.

### Modified Capabilities

- `client-customer-auth`: Adds an environment-owned minimum-disclosure publish-queue read contract and concurrency-safe cancellation receipt in the customer token domain.
- `edge-companion-ui`: Replaces the XHS single-record publish-history dock with a compact queue summary and navigates to the in-app publish queue while preserving existing draft review behavior.

## Impact

- `aidcp-cloud`: customer-auth publish-queue projection, lifecycle/task DTO mapping, environment/platform ownership checks, cancellation response shaping, and focused route/service tests.
- `aidcp-edge`: Electron main/preload customer HTTP bridge, renderer queue controller, home summary, full-page queue and confirmation UI, responsive styles, and focused renderer/IPC tests.
- `aidcp`: OpenSpec contracts and implementation checklist.
- No database migration, protocol-v2 command, internal Console behavior, risk-state writer, publish execution, or platform confirmation semantics change.
