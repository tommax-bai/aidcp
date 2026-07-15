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

### Requirement: 互动 workspace 必须满足基线尺寸与无障碍

在 `820×720` SHALL 可完成列表选择、上下文查看、编辑、批准/发送/转人工；更窄窗口 SHALL 按基线折叠而不遮挡主动作。tabs、列表、编辑器和主要动作 MUST 键盘可达、focus 可见、状态不只靠颜色。

#### Scenario: 820×720 完成主流程
- **WHEN** 窗口为 820×720 且 thread 有待审草稿
- **THEN** 用户无需页面级横向滚动即可查看风险、编辑并执行主要动作
