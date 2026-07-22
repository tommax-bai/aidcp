## Context

Edge 已有同窗页栈 `ContentWorkspace`，能够读取当前小红书账号的精选灵感、发布队列和待审稿；运行首页已有当前环境的“浏览器/启动”控制以及只针对首个新建环境的一次性启动提示。Cloud 已提供环境归属范围内的 customer-auth HTTP、待审稿 `contentVersion`、发布阶段投影和精选来源数据，但内容工作区仍以灵感列表为首页，稿件写能力只有审批与删图，过程展示也只有四阶段结果，无法表达正在执行的客户可理解工作。

本变更跨 Edge、Cloud 和数据库。客户端数据仍走 customer-auth HTTP，浏览器/自动化 WebSocket 只负责外部平台执行。用户要求的“thinking 感”实现为经过设计、可审计的工作过程摘要，不暴露模型隐藏推理、原始 prompt、密钥、内部诊断或其它账号数据。

## Goals / Non-Goals

**Goals:**

- 让小红书客户进入内容工作区后先看到赞藏价值证据、来源灵感和由其产生的内容，而不是内部功能目录。
- 在固定不超过 255px 的工作面板中连续呈现真实任务阶段；新内容逐字出现，完成项保持同字号上移并有界收起。
- 支持待审稿直接编辑及整篇、正文、全部图片、单图、选中文字五种 AI 调整范围。
- 所有读取和写入均绑定当前授权环境，由 Cloud 解析账号；写入遵守待审状态、版本 CAS、执行目标和不自动发布边界。
- 复用真实环境启动/浏览器控制和现有首次环境提示，不建立第二套运行状态。

**Non-Goals:**

- 不展示模型原始 chain-of-thought、prompt、token、provider 诊断或后台日志。
- 不改变平台发布审批、风险控制、配额、边云 protocol v2 或 AdsPower 生命周期。
- 不把 `submitted` 描述为已发布，不因发起调整而自动批准或发布。
- 不在视频号、Facebook 或平台未知环境展示小红书内容首页。
- 本次不构建或发布 Edge 安装包。

## Decisions

### 1. 在现有 ContentWorkspace 页栈增加 home，而不是重做主壳

标题栏的“小红书内容”入口改为打开 `home`。页内保留“内容首页 / 灵感库 / 我的内容”导航；灵感列表、详情、参考创作确认、发布队列和稿件审核继续复用现有页面与 DOM/事件链。关闭内容工作区仍回到运行首页，环境栏、账号身份、今日进展和生命周期按钮不被复制。

备选方案是在运行首页直接重排所有旧卡片，但会把 Facebook/视频号的主工作区一起耦合进来，也更容易破坏既有环境状态。独立的小红书内容首页能够严格平台门禁并渐进迁移。

### 2. 首页由多个 customer-auth 真态拼接，事件只负责失效

首页并行读取现有精选汇总、精选列表、发布队列和待审稿列表，并为每次环境切换递增 request epoch。Cloud DTO 增加最小的 `sourceCuratedId`/来源摘要，仅用于把同账号的精选条目与参照草稿关联；不得返回 `accountId`、原始 sourceReference、模型诊断或审批凭据。

自动化事件、窗口聚焦和发布预览事件只触发节流重读，不能直接修改已确认计数。首次任一来源失败时，该分区显示失败/未知；已有缓存时保留内容并标注正在刷新，不把失败伪装成 0。

### 3. 空态保留有内容时的页面骨架

首页始终保留价值概览、工作面板、“最值得看的灵感”“值得参考的内容”“我的内容”和折叠运行详情。每个分区独立处理 loading/empty/error/content。零内容时不生成假卡片、假赞藏、假草稿或假任务；环境停止只改变环境内动作可用性，客户自有内容仍可读取。

工作面板桌面态高度固定为 240px（含 padding 和边框），窄窗口改为内容自适应但不得横向溢出。按钮行和“不自动发布”边界并入紧凑底部栏，不再额外占一整行大留白。

### 4. 工作过程只投影可审计事实

Cloud 调整任务保存一个有序、白名单化的过程消息流：`计划`、`判断`、`生成`、`检查`、`确认`。每条包含序号、阶段、状态、客户可理解摘要和时间，但客户端不展示时间。当前项显示“计划中/判断中/生成中/检查中/确认中”，完成后保留对应“完成”阶段名；新消息在 Edge 逐字显示，旧消息保持同字号上移，超过可视条数折叠到“收起过程”。

非调整类发布任务继续使用 Cloud 四阶段投影生成确定性摘要；缺少阶段证据时显示“等待系统确认”，不得按等待时间猜测。动画遵守 `prefers-reduced-motion`，流光速度有界且只作用于当前状态文字。

### 5. 稿件写入分直接编辑与持久 AI 调整两条路径

直接编辑使用 `PATCH /environments/:envKey/publish-drafts/:recordId`，请求只允许 `title/content/topics/expectedVersion`，Cloud 校验环境归属、账号、`pending_approval` 和版本后调用稿件单写并回写后真态。

AI 调整使用：

- `POST /environments/:envKey/publish-drafts/:recordId/refinements` 创建任务；
- `GET /environments/:envKey/publish-drafts/:recordId/refinements/:jobId` 读取状态与过程；
- 请求包含 `expectedVersion`、`scope`、不超过 1000 字的 `instruction`，以及范围所需的精确选择快照。

范围 DTO：

- `whole`：允许生成标题、正文、话题和整组配图；
- `body`：只允许正文变化；
- `images`：只允许整组图片变化；
- `selected_image`：必须带当前图片 URL，只替换该位置；
- `selected_text`：必须带 UTF-16 `start/end` 和选中文字，Cloud 在当前版本上核对完全一致，只替换该片段。

客户端只提交 envId 对应的本地环境和所见版本；main 固定路径并注入 envKey/token，renderer 不能提交 URL、token 或 `accountId`。

### 6. 调整任务持久化、按 execution_target 领取并一次 CAS 落稿

Cloud 新增 `publish_draft_refinement_jobs`：包含 job id、`execution_target`、account/record、expected version、scope/selection、instruction、状态、过程 JSON、结果版本、错误和时间戳。创建时注入当前 `AIDCP_DEPLOY_ENV`；缺失或非法目标时 worker 禁用。worker 使用 `FOR UPDATE SKIP LOCKED` 领取本目标任务，重启后可恢复 queued，执行中超时任务按明确恢复规则失败，不跨 dev/ol 扫描。

文本由统一 LLM 出口按专用角色生成结构化 JSON；图片由现有路由 ImageProvider 生成，并沿用对象存储转存。图片生成失败不得复用旧图假称完成；整篇/图片范围在所需结果不完整时不落部分稿。最终通过新的领域方法在一个事务中校验账号、状态和 expected version，并一次写入允许变化的字段、`content_version + 1` 与审计信息。写入成功后推送新的 publish preview，使旧审批版本自然失效。

### 7. 首次启动引导指向真实生命周期按钮

继续复用 `firstEnvironmentStartGuideEnvId` 和 `#session-fab`：只有首个真实环境完成创建、进入权威花名册、当前所见动作确为 `start` 时展示提示和有限光环。内容首页环境停止 CTA 只调用同一个 `session-fab`，不复制启动 IPC；点击真实启动、切换环境、状态变化、主动关闭提示时结束。浏览器按钮在环境未运行时继续按现有规则禁用或作为登录入口呈现，不能用内容页局部状态擅自启用。

## Risks / Trade-offs

- **[多来源首页瞬时不一致]** → 各分区独立标记 as-of/刷新态，不跨来源乐观计算；环境 epoch 丢弃迟到回包。
- **[过程内容被误认为模型原始推理]** → 只存白名单阶段和动作摘要，文案明确是工作过程，不落 raw prompt/response。
- **[生成完成时稿件已被另一端编辑]** → 最终单事务 CAS；冲突任务失败并返回当前版本，绝不覆盖新稿。
- **[整篇调整产生部分图片成功]** → 所需图片未全部生成时不落稿；旧稿保持原样并显示失败原因。
- **[任务重启后重复生图]** → job claim/attempt 持久化；执行中恢复采用失败待重试或人工重发，不在未知提交后自动重跑。
- **[首页卡片过多重新变成科技控制台]** → 只保留价值证据、当前工作、精选和内容四类信息；详细运行数据默认折叠。
- **[首启提示与内容首页 CTA 重复]** → CTA 委托现有按钮，提示状态只有一个所有者；测试覆盖真实点击、跳过和环境切换。

## Migration Plan

1. Cloud 先以加性表、store/worker 和 customer-auth 端点落地；旧 Edge 不调用，不影响现有发布链。
2. 在 `dev` 对 customer-auth 归属、版本冲突、文字/图片范围和 worker execution target 做验证；失败时关闭 worker 开关即可保留旧稿件链路。
3. Edge 再切换小红书内容入口并接入新端点；Cloud 不支持时首页仍可读现有灵感/队列，调整区域显示明确不可用，不回落 panel API。
4. Edge 源码合并不等于客户端已安装；安装包另行显式发布。回滚 Edge 恢复旧灵感页，Cloud 加性表和端点可保留；回滚 Cloud 时新版 Edge保持只读并如实报错。

## Open Questions

- 无阻塞问题；真实客户端安装包中的像素级验收与模型/图片成本数据在发布阶段单独评估。
