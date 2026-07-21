## Context

Electron 当前的 `pub-card` 只投影一条 `publish` 与一条 `lastPublish`，以 `flow / submitted / last / empty` 四态在运行首页展开或收起。Cloud 管理端已经能用 `buildPublishLifecycle` 把编排器运行、待审 `publish_log` 和最近终态投影成八阶段生命周期；客户鉴权域也已有按 `envKey` 解析账号、列出委派任务和按任务版本取消的基础能力，但没有一个最小披露、精确绑定当前环境的发布队列接口。

这次变更跨 Cloud 客户鉴权服务、Edge Electron main/preload 和 renderer。客户界面必须既能看到多个并行内容，又不能把内部 `accountId`、snapshot、角色事实或管理端能力泄漏出去；取消写还必须绑定当前所选环境和页面看到的任务版本。普通队列读取不能依赖浏览器、引擎或自动化 WebSocket 在线。

## Goals / Non-Goals

**Goals:**

- 为明确的小红书环境提供环境级发布摘要、尚未开跑任务、活跃生命周期和最近终态。
- 用客户可理解的四阶段与状态文案表达真实进度，同时保留 Cloud 八阶段作为服务端证据来源。
- 允许客户逐条取消 `queued / planning / deferred` 发布任务，并诚实区分立即取消与安全收口。
- 在同一 Electron 主窗口复用内容工作区页面栈；环境切换和迟到回包不得泄漏上一账号内容。
- 保持所有客户数据读写走 customer-auth HTTP，renderer 只通过窄 IPC 传本地 `envId` 与任务选择。

**Non-Goals:**

- 不取消已经进入待审、平台下发、定时或已提交平台的生命周期记录。
- 不增加队列优先级调整、拖拽排序、精确队列名次或批量取消。
- 不改变内部 Console 队列、发布编排顺序、发布状态落库或平台确认逻辑。
- 不增加数据库迁移、协议 v2 命令、`ol` 部署或桌面安装包；默认分支集成和 Cloud `dev` 部署由客户在初始隔离交付后另行授权。

## Decisions

### 1. 新增环境级客户队列 DTO，而不是复用内部面板回包

Cloud 提供：

- `GET /environments/:envKey/publish-queue`
- `POST /environments/:envKey/publish-queue/tasks/:taskId/cancel`，body 为 `{version}`

每次请求先用 customer token 回库校验客户启用态与环境归属，再由 `envKey` 解析唯一账号。服务端内部复用 `buildPublishLifecycle` 与 `DelegatedTaskService`，但输出重新映射为白名单 DTO。响应不含 `accountId`、snapshot、stage facts、claim token、内部错误、任意跨账号统计或管理端字段。

直接调用 `/api/content/queue` 被否决：该接口属于面板鉴权域、包含全局账号与内部生命周期细节，并且不能表达客户精确环境写边界。继续只扩展 `/overview` 也被否决：overview 是首页轻量数据，承载分页/多项状态与取消版本会让职责继续膨胀。

### 2. 服务端按账号过滤后再做客户投影

读取端同时取得编排器状态、该账号待审与最近发布记录，以及该账号发布动作族的委派任务。生命周期先按既有显式证据构建，再只保留目标账号的 active/recent；任务只保留 `publish_post / publish_from_inspiration / generate_candidates` 中 `queued / planning / deferred` 的条目。

队列 DTO 分成 `tasks`、`active` 与 `recent`，避免把尚未开跑的委派伪装成已经开始的生命周期阶段。摘要计数分别来自这三个明确集合；列表顺序仅用于展示，不描述为精确队列名次。

### 3. 客户主列表压缩为四阶段，但不重新推断完成状态

八阶段映射为客户心智模型：

1. `开始创作`：触发与选题。
2. `正文与配图`：正文生成、文本质检、视觉策划、出图复核和成稿封装。
3. `你来确认`：人工审批。
4. `发布结果`：平台下发与公开确认。

压缩只改变标签和聚合显示；每一阶段的状态仍由 Cloud 明确 lifecycle 投影决定。`submitted` 保持“平台确认中”，只有 `published` 显示“已发布”。缺少证据时显示未知，不从 snapshot 字段、时间或列表位置推断成功。

### 4. 取消写绑定精确环境、任务和版本

取消路由先解析当前 `envKey` 的账号，再读取 `taskId` 并断言：任务属于该账号、属于发布动作族、当前状态为 `queued / planning / deferred`，且 body `version` 与任务当前版本相同。随后复用 `DelegatedTaskService.cancel`：

- `queued / deferred` 返回终态 `cancelled` 或有既有成功数时的 `partially_completed`。
- `planning` 返回 `cancelRequested=true`，客户端显示“取消中”直至后续读取出现终态。

客户端不做乐观删除。版本冲突返回 409 并刷新；其它失败保留任务。取消成功或请求受理后立即重新读取完整队列，Cloud 回包是唯一真态。

### 5. Electron main 持有会话并暴露两个窄 IPC

Renderer 调用 `publishQueueGet(envId)` 与 `publishQueueCancel({envId, taskId, version})`。Main 从本地环境句柄解析真实 `profileId/envKey`，构造固定 customer-auth 路径并持有 token；renderer 不能提交 URL、鉴权头、`accountId` 或任意 envKey。

队列控制器按 `envId + requestEpoch` 丢弃迟到响应。选中环境、打开队列、窗口聚焦和有界轮询会刷新；自动化事件只使数据失效并触发 HTTP 重读，不把 WS payload 写进客户数据模型。首次失败显示不可用；已有成功值刷新失败时保留缓存并显示最后更新时间。

### 6. 首页摘要与全页队列采用两层交互

小红书首页把原文案改为“发布进度”。有待确认内容时自动展开最需要处理的一条并保留既有“查看稿件”动作；只有系统处理中时显示紧凑摘要；无活跃内容时显示最近真实发布或“暂无进行中”。点击摘要进入内容工作区的发布队列页。

全页按“需要你处理”“系统处理中”“最近完成”分区。任务卡的取消按钮只出现在可取消状态，二次确认包含准确标题或动作名；单卡请求期间只锁该卡。窄屏下动作换行，不产生页面横向溢出。切换到非小红书环境时关闭队列页并回运行首页。

## Risks / Trade-offs

- [Risk] 全局编排器状态与账号发布记录读取瞬间不一致。 → 分离 tasks/active/recent，不跨集合乐观合并；每次响应带 `asOf` 并由下一次 HTTP 刷新收敛。
- [Risk] 一条 planning 任务取消后仍短暂运行。 → 显示“取消中”，禁止重复取消，只有终态证据才移入最近完成。
- [Risk] 页面把内部八阶段压缩后失去细节。 → 主列表保持四阶段，当前阶段另显示 Cloud 提供的具体摘要与可证实进度；不展示原始诊断。
- [Risk] 同一客户拥有多个环境时用任务 id 取消错环境任务。 → 新取消路由按请求路径的精确 envKey 解析账号并校验任务账号，不复用“该客户任意环境可达”作为充分条件。
- [Risk] XHS 门禁判断缺失时误显示队列。 → 平台未知或非 `xiaohongshu` 一律隐藏入口、不请求接口并关闭残留页。

## Migration Plan

1. 在 feature worktree 中先增加 Cloud 加性接口与测试；旧 Edge 不调用，不影响现有客户接口。
2. 增加 Edge main/preload IPC、renderer 页面与测试；Cloud 不可用时呈现明确失败，不回落内部面板。
3. 运行 Cloud/Edge 聚焦测试、typecheck 和 OpenSpec strict validation，在各自 feature 分支提交但不合并默认分支。
4. 获准集成后，先合 Cloud 并部署 dev，再交付 Edge 默认分支源码；回滚 Edge 可恢复旧单卡，回滚 Cloud 时新版 Edge 显示队列不可用，不影响自动化主链。桌面安装包仍需独立的显式发布请求。

## Open Questions

None.
