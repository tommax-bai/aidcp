## ADDED Requirements

### Requirement: 视频号只替换当前环境右侧 workspace

Electron 客户端 SHALL 保持现有全局标题栏与左侧环境栏；当前环境 platform=`wechat_channels` 时，只在右侧渲染 InteractionWorkspace。MUST NOT 新增永久第二侧栏、替换环境栏或展示 browse/like/collect/follow/publish 的无意义零指标。XHS/Facebook 继续使用既有 workspace。

#### Scenario: 切换到视频号保留应用壳
- **WHEN** 用户从 XHS/FB 环境切换到 wechat_channels 环境
- **THEN** 左侧环境栏与标题栏保持位置/功能，右侧原子切成互动队列与详情

#### Scenario: 切回旧平台零回归
- **WHEN** 用户从视频号环境切回 XHS/Facebook
- **THEN** 原工作区恢复且不残留视频号 tabs、thread 或写按钮

### Requirement: 环境切换必须取消旧请求并校验 envKey

列表、详情、auth/sync 状态与所有写回包 SHALL 绑定当前 `envKey`。切换环境 MUST 取消可取消请求并丢弃迟到回包；新环境加载中显示自身 loading/unknown，MUST NOT 复用旧账号数据。最终文本草稿 MUST 绑定原 env/job，不能静默移到新环境。

#### Scenario: A 的迟到回包不覆盖 B
- **WHEN** 用户快速 A→B 切换且 A 的详情响应后到
- **THEN** renderer 校验 envKey 后丢弃 A 响应，B 页面不闪现 A 的昵称/私信/动作

### Requirement: 视频号 workspace 必须保留当前环境生命周期控制

InteractionWorkspace SHALL 在顶部提供当前视频号环境可见的生命周期控件，并与 XHS 使用同一状态矩阵和判定优先级。会话为 paused 时 SHALL 优先同时显示“恢复”和独立的“关闭”；其余核心为 stopped/warning 时 SHALL 只显示“启动”；其余 starting/running 时 SHALL 只显示“暂停”。“暂停” MUST 保留当前浏览器/会话；“关闭” MUST 仅在暂停态可见且可执行，关闭完成后 SHALL 按主进程回传真态回到“启动”。所有动作 MUST 复用既有单环境 lifecycle IPC 并携当前 `envKey`；MUST NOT 调用 fleet 全部启动、把显示浏览器/重新登录冒充启动、操作其他环境、清除登录凭证或触发 offboard。

#### Scenario: 离线视频号环境可以就地启动
- **WHEN** 用户选中 edge=stopped 的 wechat_channels 环境并点击“启动”
- **THEN** 客户端只向该环境的单环境启动 IPC 传递当前 envKey，其他环境保持原状态

#### Scenario: 生命周期状态切换使用同一入口
- **WHEN** 当前视频号环境从 running 进入 paused，或从 paused 恢复运行
- **THEN** 按钮依次显示“暂停”“恢复”“暂停”，每次动作都绑定当前 envKey 且以主进程回传真态刷新

#### Scenario: 暂停后可以显式关闭当前环境
- **WHEN** 当前视频号环境为 paused
- **THEN** workspace 同时显示“恢复”和“关闭”；点击“关闭”只调用当前 envKey 的单环境关闭 IPC，完成后显示“启动”，且其他环境、登录凭证和 offboard 状态保持不变

#### Scenario: 非暂停态不暴露关闭入口
- **WHEN** 当前视频号环境为 starting、running、stopped 或 warning
- **THEN** “关闭”入口不可见且 handler 拒绝执行，用户必须先暂停当前环境才能显式关闭

### Requirement: 开发者详情必须跨 workspace 保持可见

设置中的“显示开发者详情”开关 SHALL 继续控制共享的当前环境原始日志面板，默认隐藏和持久化语义 SHALL 保持不变。该面板 MUST 位于 XHS/Facebook legacy workspace 与视频号 InteractionWorkspace 的互斥切换之外；开关启用后切换到 `wechat_channels` MUST 继续显示当前选中 `envKey` 的日志，MUST NOT 因 legacy workspace 隐藏而消失或展示其他环境日志。

#### Scenario: 视频号环境显示已启用的开发者详情
- **WHEN** 用户已启用“显示开发者详情”并从 XHS/Facebook 切换到视频号环境
- **THEN** InteractionWorkspace 与开发者详情同时可见，日志内容切换到当前视频号 envKey 的分桶；切回其他环境时同一面板继续显示对应环境日志

### Requirement: 互动 workspace 必须呈现真实队列与发送状态

InteractionWorkspace SHALL 提供横向 `待处理/评论/私信/已回复` 视图、分页列表、thread 详情、模板/AI 差异、风险、final text 与 ignore/escalate/regenerate/approve/send 动作。`queued`、`sending`、`ambiguous`、`sent`、`failed` MUST 有不同文案/视觉；只有 sent 可显示平台确认成功，ambiguous 必须显示待核验。

#### Scenario: HTTP accepted 不显示绿色成功
- **WHEN** send API 返回 job queued
- **THEN** UI 显示已进入发送队列/等待平台结果，MUST NOT 显示已回复成功

#### Scenario: 未配置模板仍继续显示收件箱
- **WHEN** 环境能同步但无有效 published reply config
- **THEN** 列表/详情可读并显示配置阻断卡，生成/发送禁用，MUST NOT 显示空成功态

### Requirement: 浏览器关闭是正常副状态而 reauth/challenge 是阻断

顶部状态 SHALL 区分 interaction auth 与 browser sidecar：auth active + browser closed 显示正常 API 同步；reauth_required/challenge_required 禁用写、保留历史并提供 reopen。网络/限流/schema disabled SHALL 各自使用可解释状态，MUST NOT 解析 Edge 日志猜测。

#### Scenario: API-only running 不告警
- **WHEN** auth active、最近同步成功且 browserState=closed
- **THEN** 标题显示互动托管/接口同步正常，辅助文字说明浏览器已关闭（正常）

#### Scenario: Challenge 保留历史并禁写
- **WHEN** auth status=challenge_required
- **THEN** 已同步 thread 仍可读，approve/send 禁用并提示在原浏览器处理

### Requirement: Renderer 必须经最小具名 IPC 访问 customer-auth API

renderer MUST NOT 持有 JWT/Cookie、访问平台接口、记录完整 DM 或获得任意 URL fetch。preload SHALL 只暴露冻结路径对应的具名 IPC；Electron main 校验 method/path/body，并复用现有 client auth session。Cloud 仍作最终 enabled user/env ownership/CAS 检查。

#### Scenario: Renderer 不能构造任意请求
- **WHEN** renderer 尝试传入任意 URL 或非冻结 method/path
- **THEN** preload/main 拒绝，MUST NOT 代发网络请求或泄漏 token

### Requirement: 环境删除必须显示 offboard 真态

视频号环境的显式删除/解绑 SHALL 先调用 customer-auth `DELETE /environments/:envKey`，再用 `GET /offboarding/:offboardId` 读取 Cloud/Edge 清理真态。`pending_edge|dispatched` MUST 显示“已撤权，等待本机/离线设备清理”，不能把本地 profile 删除、普通 logout、pause/close 或 HTTP 2xx 显示成凭证已删除。只有 `tombstoned|purged` 才可显示 Cloud 已完成对应阶段。

#### Scenario: Edge 离线时环境仍显示待清理
- **WHEN** 用户解绑环境而所属 Edge 离线
- **THEN** UI 立即停止该环境互动访问/写，保留 offboardId 与待清理状态，MUST NOT 显示“删除完成”或丢弃恢复入口

#### Scenario: 本地 profile 删除不冒充 offboard 完成
- **WHEN** 浏览器 profile 本地删除成功但 Cloud offboard 尚未收到 Edge cleared ack
- **THEN** UI 仍显示待凭证清理，MUST NOT 将本地动作映射为 tombstoned/purged

### Requirement: 互动 workspace 必须满足基线尺寸与无障碍

在 `820×720` SHALL 可完成列表选择、上下文查看、编辑、批准/发送/转人工；更窄窗口 SHALL 按基线折叠而不遮挡主动作。tabs、列表、编辑器和主要动作 MUST 键盘可达、focus 可见、状态不只靠颜色。

#### Scenario: 820×720 完成主流程
- **WHEN** 窗口为 820×720 且 thread 有待审草稿
- **THEN** 用户无需页面级横向滚动即可查看风险、编辑并执行主要动作

### Requirement: 单列互动布局必须提供主列整体滚动

当左侧环境栏使右侧 InteractionWorkspace 的 container 宽度进入单列布局时，Electron 客户端 SHALL 让右侧主列整体纵向滚动，MUST NOT 继续用宽屏固定高度加 `overflow:hidden` 裁掉列表下方的详情或共享开发者详情。是否折叠为单列 MUST 以右侧 workspace 的实际可用宽度为准；支持 container query 的客户端 MUST NOT 再被 viewport-only 断点提前覆盖。宽屏双列布局 MAY 保留列表/详情各自滚动，但任何布局都必须让当前 thread 详情可达。

#### Scenario: 820×720 环境栏展开后详情仍可达
- **WHEN** 窗口为 820×720、环境栏可见且 workspace container 宽度不超过 640px
- **THEN** 用户在右侧主列向下滚动可依次到达互动详情和开发者详情，MUST NOT 被只响应 viewport 宽度的断点裁切

#### Scenario: 窄 viewport 但右侧仍够宽时保持双栏
- **WHEN** viewport 不超过 700px，但 InteractionWorkspace 的实际可用宽度仍大于 640px
- **THEN** 收件箱保持列表/详情双栏，MUST NOT 因 viewport-only 兜底把消息列表拉成通栏；只有 workspace 自身进入单列阈值后才折叠
