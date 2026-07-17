## MODIFIED Requirements

### Requirement: 视频号工作区必须提供互动读取设置与三层真态

InteractionWorkspace SHALL 在当前环境顶部提供“收取互动”总开关、评论收取开关和私信收取开关，并分别展示 Cloud stored 意图、Edge application status 与 effective read capability。切换 MUST 通过具名 IPC 调用客户 read-controls API、携 expectedVersion 并在回包 envKey 不匹配时丢弃；pending/冲突/失败期间 MUST 保持诚实 busy 或错误状态，MUST NOT 本地先改成已生效。

读取开关的可编辑性 SHALL 只由「这次写入本身能不能被受理」决定，判据 SHALL 限于：授权态 active、已取到 Cloud stored 真态（因而有 expectedVersion 可携）、当前数据不是 stale、具名 IPC 通道存在。该环境**核心子进程的在线状态**（`connectivity`）MUST NOT 参与该判定——这次写入由客户端主进程直发 Cloud HTTP，链路上不存在该核心子进程；Cloud 在无 Edge 在线时 SHALL 按 CAS 正常落库并回报 `edgeDelivery.status=deferred`，Edge 下次连接时经欢迎信封的 runtime-controls 快照收敛。客户端 MUST NOT 因为该环境未启动、已停止或核心子进程离线，在本地拦下一次 Cloud 完全能够受理的写入；此类本地拦截 MUST NOT 被呈现为该能力不可用。

授权态 `status` 与浏览器现场 `browserState` MUST 保持正交：`status=active` 且 `browserState=closed`（后台 API-only 运行）SHALL 继续视为可编辑，MUST NOT 被合并成单一“是不是起着”的判定。

保存结果 SHALL 按 Cloud 回包的 `edgeDelivery` 如实分档，并在读取设置区**持久可见**，MUST NOT 只写入会被后续任意动作清空的一次性通知位：`enqueued` SHALL 表述为已保存并已下发本机；`deferred` SHALL 表述为已保存、待该环境下次连接后生效，并指明需要启动该环境。两者 MUST NOT 表述为已生效或已应用；只有 Edge 回报的 applicationStatus 与 storedVersion 一致时才 MAY 表述为本机已应用。

#### Scenario: 总开关同时更新两个读取渠道
- **WHEN** 客户在当前视频号环境打开“收取互动”
- **THEN** 客户端提交两个 read=true 与当前 storedVersion，收到 Cloud 真态后刷新；写字段没有入口也没有请求字段

#### Scenario: 环境已停止时读取开关仍可编辑并真的写入 Cloud
- **WHEN** 当前视频号环境的核心子进程未启动或已停止（connectivity 不为 connected），而 status=active、stored 已取到且数据不是 stale
- **THEN** 三个读取开关 SHALL 可编辑，切换 SHALL 真的携 expectedVersion 发出 read-controls 请求
- **AND** MUST NOT 因 connectivity 在本地拦下该请求或把开关禁用

#### Scenario: 离线保存必须显示待生效而不是已生效
- **WHEN** 上述写入被 Cloud 受理并回 `edgeDelivery.status=deferred`
- **THEN** 读取设置区 SHALL 持久显示已保存、待该环境下次连接后生效，并指明需要启动该环境
- **AND** MUST NOT 显示“本机已应用”“已生效”或任何等价措辞
- **AND** 该呈现 MUST NOT 因客户随后进行其他操作而消失

#### Scenario: 已下发本机与延后下发可区分
- **WHEN** 同一写入被 Cloud 受理并回 `edgeDelivery.status=enqueued`
- **THEN** 呈现 SHALL 表述为已保存并已下发本机，与 deferred 的措辞可区分
- **AND** 在 Edge 回报同一版本前 MUST NOT 表述为已应用

#### Scenario: 浏览器已关闭的后台运行环境保持可编辑
- **WHEN** 环境 status=active 且 browserState=closed（含冷待机：浏览器已关、核心仍在线）
- **THEN** 读取开关 SHALL 保持可编辑
- **AND** status 与 browserState MUST NOT 被合并成单一可编辑判定

#### Scenario: 授权失效或数据 stale 仍然拦截
- **WHEN** status 非 active，或当前显示的是上次成功数据（stale，storedVersion 可能已落后）
- **THEN** 读取开关 SHALL 保持禁用并显示对应原因，避免携过期 expectedVersion 发起 CAS

#### Scenario: Cloud 已保存但 Edge 尚未应用
- **WHEN** stored read 已开启而 applicationStatus=pending
- **THEN** 页面显示“已保存，等待本机应用”，MUST NOT 显示“同步正常”

#### Scenario: Edge 已应用但平台读取能力不可用
- **WHEN** stored/applied 均就绪但 commentsRead 或 dmRead effective capability=false
- **THEN** 对应渠道显示“平台能力未就绪”并给出登录/probe 处理提示，另一渠道 MAY 独立正常
