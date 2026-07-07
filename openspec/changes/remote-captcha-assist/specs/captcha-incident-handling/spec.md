## ADDED Requirements

### Requirement: 验证码告警必须创建可远程协助的 incident

云端收到 `risk.captcha_detected` 后，除既有风控迁移、edge 暂停和 Feishu 告警外，还 SHALL 为该次阻断创建或更新一个远程协助 incident。incident MUST 绑定真实 `edgeId`、`accountId`、`kind`、首次检测 URL、创建时间、过期时间和当前处理状态；若缺少 `edgeId` 或无法定位在线 edge，系统 MUST 诚实标记该 incident 不可远程协助，并保留远程桌面处置文案。incident MUST NOT 让 cloud 新开浏览器处理平台验证码。

#### Scenario: 验证码创建远程协助 incident
- **WHEN** cloud 收到 `risk.captcha_detected{edgeId:'edge-1', accountId:'acc-1', kind:'captcha'}`
- **THEN** cloud 创建一个绑定 `edge-1` 与 `acc-1` 的 open incident，并继续执行既有 restricted、pause edge、Feishu 告警流程

#### Scenario: 无 edge 归属时不可远程协助
- **WHEN** cloud 收到无法定位 `edgeId` 或对应 edge 不在线的验证码上报
- **THEN** incident 状态 MUST 诚实显示不可远程协助，MUST NOT 广播截图或点击命令到其它 edge

### Requirement: Feishu 验证码告警必须提供受保护的云端处理入口

当远程协助 incident 可用时，Feishu 验证码 / 未知阻断告警卡 SHALL 包含一个“去处理”入口，指向该 incident 的云端协助页。入口 MUST 使用正常 console JWT 鉴权或短期签名 token；签名 token MUST 只授权读取、刷新和提交该 incident 的协助动作，MUST NOT 授权账号启停、风控状态写入、发布审批或其它管理操作。Feishu 卡 MUST NOT 直接承载验证码截图或“已解决”按钮。

#### Scenario: 告警卡展示去处理入口
- **WHEN** cloud 为验证码 incident 发送 Feishu 告警卡且 assist 已启用
- **THEN** 卡片包含指向该 incident 的受保护 action URL，卡片正文仍说明可远程桌面兜底

#### Scenario: token 作用域受限
- **WHEN** 操作者使用 Feishu action URL 打开协助页
- **THEN** cloud 只允许该 token 访问对应 incident 的截图、刷新和点击接口，MUST NOT 接受该 token 调用账号风险或调度管理接口

### Requirement: 云端协助页必须只展示 edge 捕获的现场截图

协助页 SHALL 通过 cloud 请求原 edge 捕获当前阻断遮罩截图，并展示该截图供人工点击。截图 MUST 来源于原 edge 的原浏览器会话，MUST 包含截图时间、过期状态和坐标映射信息；cloud MUST NOT 使用另一个浏览器访问平台页面来生成截图。截图数据 MUST 短期保存并受大小限制，MUST NOT 写入普通日志或长期暴露在 Feishu 消息中。

#### Scenario: 请求现场截图
- **WHEN** 操作者打开可用 incident 的协助页并请求刷新截图
- **THEN** cloud 向该 incident 绑定的 edge 发送截图请求，edge 从当前原浏览器捕获阻断遮罩截图并返回 snapshot id 与坐标映射

#### Scenario: 截图过期
- **WHEN** 协助页持有的 snapshot 已超过有效期
- **THEN** 页面 MUST 要求刷新截图后再提交点击，cloud MUST NOT 将过期 snapshot 的点击当作有效操作

### Requirement: 人工点击必须由原 edge 注入原浏览器并绑定 snapshot

协助页提交点击时，cloud SHALL 将点击序列作为归一化坐标发送给该 incident 绑定的原 edge；edge MUST 校验 incident、snapshot、当前阻断态和坐标边界后，将坐标映射回当前浏览器视口并派发真实输入事件。cloud MUST NOT 在自身环境执行点击，MUST NOT 将点击命令广播到多个 edge，MUST NOT 用 DOM 状态篡改替代用户输入。

#### Scenario: 有效点击序列派发到原 edge
- **WHEN** 操作者基于最新 snapshot 提交两个图片点位和一个验证按钮点位
- **THEN** cloud 只向绑定 edge 发送点击命令，edge 将这些点映射到原浏览器并通过输入事件执行

#### Scenario: stale snapshot 拒绝点击
- **WHEN** 操作者基于已过期或已被替换的 snapshot 提交点击
- **THEN** cloud 或 edge MUST 拒绝该点击并返回 `stale_snapshot`，MUST NOT 盲目点击当前页面

#### Scenario: edge 当前不在阻断态
- **WHEN** edge 收到 assist 点击命令但 fresh probe 显示当前已无 captcha/unknown 阻断
- **THEN** edge MUST 不执行点击，并发送或保持 `risk.captcha_cleared` 的正常清除路径

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `risk.captcha_cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `risk.captcha_cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

#### Scenario: 点击后仍被阻断
- **WHEN** edge 执行 assist 点击序列后 fresh probe 仍显示 captcha/unknown
- **THEN** edge 返回 still_blocked，cloud 保持该 edge 暂停并向协助页展示新的处理状态

#### Scenario: 手动解决告警不恢复 edge
- **WHEN** 操作者在告警列表中手动解决对应 captcha 告警但 edge 尚未发送 `risk.captcha_cleared`
- **THEN** cloud MUST 只闭合告警日志行，MUST NOT 将 incident 标记 cleared，MUST NOT resume 该 edge

### Requirement: 暂停期间只允许 captcha assist 恢复命令穿透

当某 edge 因验证码处于暂停态时，cloud 传输层 SHALL 继续阻止普通浏览、互动、发布页面动作等命令下发；但 SHALL 允许该 edge 绑定 incident 的截图与人工点击协助命令穿透暂停闸。穿透白名单 MUST 精确限定为 captcha assist 恢复路径与既有 `session.end` / 纯 UI 状态消息，MUST NOT 泛化为所有控制命令。

#### Scenario: 普通命令仍被暂停闸拦截
- **WHEN** edge `edge-1` 处于 captcha 暂停态且 cloud 尝试下发 `browse.next`
- **THEN** 该普通浏览命令仍被暂停闸拦截

#### Scenario: assist capture 可穿透暂停闸
- **WHEN** edge `edge-1` 处于 captcha 暂停态且操作者请求刷新协助截图
- **THEN** cloud 可向 `edge-1` 下发该 incident 的 `captcha.assist.capture` 命令

### Requirement: 远程协助必须可审计且短期留存

系统 SHALL 记录远程协助 incident 的关键审计事件，包括创建、截图刷新、点击提交、edge 结果、清除、过期和失败；审计记录 MUST 包含操作者来源、incident id、edge/account 归属、时间和结果，但 MUST NOT 把截图二进制、平台 cookie、验证码答案推断或敏感 token 写入普通日志。截图和签名 token MUST 有短期过期策略。

#### Scenario: 记录点击审计
- **WHEN** 操作者提交一次远程协助点击
- **THEN** cloud 记录该 incident 的点击审计事件与结果状态，但不记录截图二进制或签名 token 明文

#### Scenario: incident 过期
- **WHEN** incident 超过有效期且未清除
- **THEN** cloud 将其标记 expired，协助页显示需重新触发或远程桌面处理，MUST NOT 继续接受旧 token 的点击请求
