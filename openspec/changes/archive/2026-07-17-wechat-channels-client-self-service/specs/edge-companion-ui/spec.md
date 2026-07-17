## ADDED Requirements

### Requirement: 视频号工作区必须提供互动读取设置与三层真态

InteractionWorkspace SHALL 在当前环境顶部提供“收取互动”总开关、评论收取开关和私信收取开关，并分别展示 Cloud stored 意图、Edge application status 与 effective read capability。切换 MUST 通过具名 IPC 调用客户 read-controls API、携 expectedVersion 并在回包 envKey 不匹配时丢弃；pending/冲突/失败期间 MUST 保持诚实 busy 或错误状态，MUST NOT 本地先改成已生效。

#### Scenario: 总开关同时更新两个读取渠道
- **WHEN** 客户在当前视频号环境打开“收取互动”
- **THEN** 客户端提交两个 read=true 与当前 storedVersion，收到 Cloud 真态后刷新；写字段没有入口也没有请求字段

#### Scenario: Cloud 已保存但 Edge 尚未应用
- **WHEN** stored read 已开启而 applicationStatus=pending
- **THEN** 页面显示“已保存，等待本机应用”，MUST NOT 显示“同步正常”

#### Scenario: Edge 已应用但平台读取能力不可用
- **WHEN** stored/applied 均就绪但 commentsRead 或 dmRead effective capability=false
- **THEN** 对应渠道显示“平台能力未就绪”并给出登录/probe 处理提示，另一渠道 MAY 独立正常

### Requirement: 互动空态必须区分未开启与确实无消息

页面 SHALL 只有在对应 read stored=true、applicationStatus=applied、effective capability=true 且存在成功数据时间时显示“当前没有评论互动/私信会话”或“同步正常”。读取关闭、待应用、能力不可用、auth 阻断和 Cloud stale MUST 各自显示原因与可执行入口；局部刷新在读取关闭时 MUST NOT 冒充会带来新数据。

#### Scenario: 两个读取开关都关闭
- **WHEN** 当前账号 commentsReadEnabled=false 且 dmReadEnabled=false
- **THEN** 顶部显示“互动收取已关闭”，空态引导开启收取，MUST NOT 显示“评论/私信同步正常”

#### Scenario: 已启用渠道真实空结果
- **WHEN** 对应渠道三层门禁均通过且最近同步成功但 items 为空
- **THEN** 页面才显示该渠道当前没有互动，并保留数据时间

### Requirement: 非平台发送动作不得被发送 capability 静默拦截

renderer SHALL 将通用可写门禁与 channel send capability 分离。保存最终文字、重新生成、忽略、转人工和批准 MUST NOT 仅因 commentsReply/dmSendText=false 而被本地拦截；只有“发送回复”按钮 SHALL 在对应发送 capability=false 时禁用。任何禁用动作 MUST 显示可读原因，handler 与按钮状态 MUST 一致，MUST NOT 出现看似可点但点击无反应。

#### Scenario: 只读账号仍可整理收件箱
- **WHEN** 评论读取可用但 commentsReply=false
- **THEN** 客户仍可忽略或转人工，并可在有有效 published config 时编辑/重新生成/批准；发送回复明确禁用并解释原因

#### Scenario: auth 或 Cloud stale 继续阻断所有修改
- **WHEN** auth 非 active 或当前数据为 stale
- **THEN** 草稿与队列修改仍全部禁用并显示对应阻断原因

### Requirement: 回复配置缺失必须有可达引导

工作区 SHALL 展示 replyConfig 的 missing/draft_only/published 真态。missing 或 draft_only 时 SHALL 保留历史收件箱，显示“回复设置”入口及管理后台准确路径，依赖 published 配置的动作禁用；published 时显示版本。客户端 MUST NOT 自行构造默认模板、发布配置或调用 internal API。

#### Scenario: 配置缺失时从空错误变为可处理引导
- **WHEN** replyConfig.status=missing
- **THEN** 页面说明“先在管理后台的账号-回复设置初始化并发布”，提供可达说明入口，收取开关仍可独立使用

### Requirement: 新互动必须有 env-scoped 未读标记与去重通知

客户端 SHALL 使用 customer API 的 `unread` 字段渲染列表未读标记并更新当前环境角标。首次成功加载 SHALL 只建立基线，不为历史项弹通知；后续加载发现新的 unread messageId 时 SHALL 通过具名 IPC 发一次系统通知并按 envKey/messageId 去重。切换环境 MUST NOT 串用 seen 集合或由迟到回包更新另一环境角标。

#### Scenario: 首次打开已有历史未读不刷屏
- **WHEN** 客户首次进入环境且列表含多条 unread=true 历史项
- **THEN** 列表与角标显示未读，但不弹系统通知

#### Scenario: 后续收到一条新评论只通知一次
- **WHEN** 同一环境后续刷新首次出现新的 unread messageId，之后多次返回同一项
- **THEN** 系统通知恰好一次且环境角标保持真实计数

#### Scenario: 环境 A 的迟到响应不更新环境 B
- **WHEN** 用户从 A 切到 B 后 A 的互动列表响应才返回
- **THEN** B 的列表、角标和系统通知均不使用 A 的数据
