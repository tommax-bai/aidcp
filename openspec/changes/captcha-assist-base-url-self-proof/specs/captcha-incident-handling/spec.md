## ADDED Requirements

### Requirement: 协助链接的外部基址 MUST 被周期性自证，判死即不签发

协助链接的公开基址（`AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL`，回落 `AIDCP_PANEL_PUBLIC_BASE_URL`）是一条**进程内无法验证的声明**：它是否终结在本进程，由进程之外的 DNS / nginx / 安全组决定。云端 SHALL 周期性地**真的走一遍那条路**来自证，并在明确证伪时停止签发链接。

**探测方式**：匿名 `GET ${base}/api/captcha-assist/<probe-id>`，**MUST NOT 携带任何凭据**（无 Authorization、无 token）、**MUST NOT 跟随重定向**——基址是一个可能指向任意第三方主机的配置值，带凭据出去等于把密钥周期性送给陌生主机。

**判据（唯一）**：`status === 503 && body.error === 'captcha_assist_unavailable'` ⇒ 判死（`refuted`）。该字符串是本系统自己的签名，其含义是**「那个地址上没有协助服务，所以它铁定不是我」**。判死 MUST 经**连续 2 次**确认，以免单次抖动误伤。

**其余一切 MUST 归入 `unknown`、MUST NOT 行动**：401 / 404 / 200 / 5xx / HTML / Cloudflare 挑战页 / 传输失败 / 非 JSON / 我方以外的 JSON 信封。理由：只在**明确证伪**时行动——本机回环不通、出网被挡、对端是别的服务，都不足以判定基址是错的。

**周期性是机制本身，MUST NOT 退化为纯启动期检查**：2026-07-11 的域名割接发生时进程并未重启，只在启动期检查的机制在腐烂发生的那一刻**不在场**；启动期那一次只是周期的第一次执行。

**已知盲区（本次不覆盖，MUST 记录在案）**：当对端**也开着**协助服务时，探测返回 401 `missing_token` ⇒ **无判决力**。将来若要覆盖此分支而引入实例身份比对，主判别子 MUST 是每进程随机生成的 boot id，**MUST NOT 使用可被复制的 env 名**（`.env` 被照抄正是本病的形态；用一条不可验证的声明去校验另一条不可验证的声明，机制归零）。

#### Scenario: 基址指向没有协助服务的另一台实例（本次事故形态）
- **WHEN** 探针连续 2 次收到 `503 {"error":"captcha_assist_unavailable"}`
- **THEN** 结论 MUST 置为 `refuted`，并记录**对端 IP（socket remoteAddress）**以便当场看出解析落到了哪台机器

#### Scenario: 单次抖动不判死
- **WHEN** 探针第 1 次收到判死信号、第 2 次收到任何其它结果
- **THEN** 结论 MUST NOT 置为 `refuted`

#### Scenario: 基址正确时不误伤
- **WHEN** 探针收到 `401 {"error":"unauthorized","reason":"missing_token"}`（该地址上有协助服务）
- **THEN** 结论 MUST 为 `unknown`，链接照常签发

#### Scenario: 地址上是别的服务时不误伤
- **WHEN** 探针收到非我方 JSON 信封的应答（如 `404 {"detail":"Not Found"}`）、HTML、5xx 或传输失败
- **THEN** 结论 MUST 为 `unknown`，链接照常签发，MUST NOT 判死

#### Scenario: 探针自身故障绝不影响主流程
- **WHEN** 探针抛出异常或 reject
- **THEN** 异常 MUST 被吞进日志、结论保持上一态，MUST NOT 使进程退出、MUST NOT 阻塞启动、MUST NOT 影响验证码事故处理

### Requirement: 判死 MUST 只停按钮，MUST NOT 削弱验证码处置能力

基址自证判死的语义是「这条**外链**签不出来」，**不是**「协助能力没了」。系统 SHALL 把判死结论的读取点收敛到链接签发这一处。

判死结论 **MUST NOT** 参与「协助服务是否可用」的判定（即 `isAvailable()` 语义）。该判定另有两个消费者，把判死折进去会造成自残：一是创建 incident 的总闸——返回 null 会**连事故都不创建、不武装抓帧**，等于拿「配置错」惩罚「验证码处置」；二是面板 API 的注入判据，它在**构造期一次性求值**，塞入动态结论只会产生死代码，并制造「我以为加了闸」的假象。

判死时：incident **MUST** 仍然创建、抓帧 **MUST** 仍然武装、风控迁移与 edge 暂停闸 **MUST** 不受影响；P0 验证码告警卡 **MUST** 照发，仅**不渲染协助按钮**。

#### Scenario: 判死后事故处置链路完整
- **WHEN** 基址结论为 `refuted` 且 cloud 收到 `risk.captcha_detected`
- **THEN** cloud MUST 照常创建 incident、请求抓帧、迁移风控、暂停该 edge，仅协助链接为空

#### Scenario: 判死只落在链接签发处
- **WHEN** 基址结论为 `refuted`
- **THEN** 链接签发 MUST 返回空；面板 `/api/captcha-assist/*` 接口 MUST 仍正常服务已鉴权请求（已登录运营经 JWT 仍可处置）

## MODIFIED Requirements

### Requirement: Feishu 验证码告警必须提供受保护的云端处理入口

当远程协助 incident 可用时，Feishu 验证码 / 未知阻断告警卡 SHALL 包含一个“去处理”入口，指向该 incident 的云端协助页。入口 MUST 使用正常 console JWT 鉴权或短期签名 token；签名 token MUST 只授权读取、刷新和提交该 incident 的协助动作，MUST NOT 授权账号启停、风控状态写入、发布审批或其它管理操作。Feishu 卡 MUST NOT 直接承载验证码截图或“已解决”按钮。

**系统 MUST NOT 签发一个自己已经知道会失败的链接。** 当外部基址自证判死时，卡片 MUST NOT 渲染协助按钮——发一个长得像正常按钮、点下去必然报错的入口，是「静默假成功」的字面形态。

**卡片对“为什么没有按钮” MUST 诚实归因，MUST NOT 混用同一套文案。** 无按钮至少有两个语义完全不同的原因，二态布尔量承载不了：一是**压根没配协助**（基址缺失 / 协助未启用），二是**基址自证判死**（基址指向了没有协助服务的地址）。系统 SHALL 用三态（`available` / `not_configured` / `refuted`）分别给出文案：`not_configured` MUST 保持既有原文（零回归）；`refuted` MUST 说明协助链接已停用及其原因（含探测到的对端 IP）。用「没配」的文案去解释「配错」，或反之，MUST 视为凭空归因。

两种无按钮情形下，卡片 MUST 保留远程桌面处置文案（机器标签 / 远程地址），使运营始终有一条可执行路径。

#### Scenario: 告警卡展示去处理入口
- **WHEN** cloud 为验证码 incident 发送 Feishu 告警卡且 assist 已启用、基址未被判死
- **THEN** 卡片包含指向该 incident 的受保护 action URL，卡片正文仍说明可远程桌面兜底

#### Scenario: token 作用域受限
- **WHEN** 操作者使用 Feishu action URL 打开协助页
- **THEN** cloud 只允许该 token 访问对应 incident 的截图、刷新和点击接口，MUST NOT 接受该 token 调用账号风险或调度管理接口

#### Scenario: 基址判死时不发按钮且诚实说明
- **WHEN** cloud 发送验证码告警卡且外部基址结论为 `refuted`
- **THEN** 卡片 MUST NOT 含协助按钮，正文 MUST 说明「协助链接已停用：该基址上没有协助服务（对端 IP）」并保留远程桌面处置文案

#### Scenario: 未配置协助时文案不得改口
- **WHEN** cloud 发送验证码告警卡且协助从未配置（基址缺失或未启用）
- **THEN** 卡片文案 MUST 保持既有的远程桌面兜底原文，MUST NOT 声称基址被判死

### Requirement: 验证码告警必须创建可远程协助的 incident

云端收到 `risk.captcha_detected` 后，除既有风控迁移、edge 暂停和 Feishu 告警外，还 SHALL 为该次阻断创建或更新一个远程协助 incident。incident MUST 绑定真实 `edgeId`、`accountId`、`kind`、首次检测 URL、创建时间、过期时间和当前处理状态；若缺少 `edgeId` 或无法定位在线 edge，系统 MUST 诚实标记该 incident 不可远程协助，并保留远程桌面处置文案。incident MUST NOT 让 cloud 新开浏览器处理平台验证码。

incident 标识符 SHALL 携带签发环境标签前缀，使一条链接在**任何**接收方（含另一套环境）都能被分诊——该前缀在 503 / 401 / 404 三条错误路径上都可读，包括协助服务根本未被注入、因而无从验签的那条路。

**前缀是自证的、任何人都可伪造**：它 MUST NOT 用于任何授权判定，MUST 只用于写文案与日志分诊。接收方渲染签发方标签时 MUST 只在命中硬编码白名单前缀时渲染，**MUST NOT 回显未知前缀原文**（标识符来自 URL 路径＝调用方可控输入）。错误文案 MAY 声明「不是我」（本地判据），**MUST NOT 声明「正主是谁」**——正主的唯一信息源是持链接者递来的输入，据其渲染跳转等于自造开放重定向钓鱼面。

#### Scenario: 验证码创建远程协助 incident
- **WHEN** cloud 收到 `risk.captcha_detected{edgeId:'edge-1', accountId:'acc-1', kind:'captcha'}`
- **THEN** cloud 创建一个绑定 `edge-1` 与 `acc-1` 的 open incident，并继续执行既有 restricted、pause edge、Feishu 告警流程

#### Scenario: 无 edge 归属时不可远程协助
- **WHEN** cloud 收到无法定位 `edgeId` 或对应 edge 不在线的验证码上报
- **THEN** incident 状态 MUST 诚实显示不可远程协助，MUST NOT 广播截图或点击命令到其它 edge

#### Scenario: 跨环境错投的链接可被接收方分诊
- **WHEN** 一条由 A 环境签发的协助链接被 B 环境的面板接收，且 B 未启用协助（503）或不认识该 incident（404）
- **THEN** 应答 MUST 说明「本实例不认识/未启用」，MUST NOT 只回一个无上下文的机器码

#### Scenario: 伪造前缀不得被回显或采信
- **WHEN** 请求携带一个不在白名单内的伪造前缀标识符
- **THEN** 系统 MUST NOT 回显该前缀原文、MUST NOT 据其做任何授权或路由判定
