## MODIFIED Requirements

### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 在客户已登录、环境归属与账号绑定已由 Cloud 权威解析后提供人设向导：客户按维度选择关键词——**垂类（枚举快捷选 + 「自定义」自由文本兜底长尾，单选）、兴趣（少量高频标签多选 + 自由文本兜底长尾）、语气（枚举单选）**；并在“语气调性”面板下提供**点赞倾向（正常 / 喜欢 / 更喜欢，单选，默认正常）**。点赞倾向 MUST 有真实输出映射：客户端 SHALL 以受控标记随 `keywordSelections` 发送，云端 SHALL 在生成兴趣关键词前剥离该标记，并把档位写入人设 `behavior_guidelines.like_affinity` 与匹配账号兴趣的 `like_principle`；MUST NOT 把内部标记当作兴趣词或原样写入身份文案。除该有明确映射的点赞倾向外，客户端 MUST NOT 提供对生成产物零影响的互动偏好输入。

点击生成 SHALL 由 Electron 主进程经 customer-auth 窄接口发起；请求只携带 `envKey`、关键词勾选（含自由文本项与受控点赞倾向标记）及 idempotency key，Cloud MUST 从客户会话逐请求校验环境归属并解析权威 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。生成 MUST NOT 要求环境浏览器已启动、页面登录态在线、CDP 可用、浏览器槽位可用或 Edge 活 WS 会话存在。云端 MUST 对 `keywordSelections` 做轻量输入校验（单项长度上限 + 条数上限），超限诚实拒绝、绝不把超长/超量文本原样喂进生成 prompt。旧客户端仍经 Edge WS 发起时 SHALL 保持原协议兼容，且两条传输 MUST 复用同一生成领域方法、校验、幂等和记账。

#### Scenario: 浏览器关闭时触发生成

- **WHEN** 客户已登录且环境归属/绑定可信，在浏览器关闭、CDP 缺席或槽位为零时选定关键词与点赞倾向并点击生成
- **THEN** Electron 主进程经 customer-auth 请求携 `envKey`、关键词、受控标记与 idempotency key，Cloud 解析权威账号后生成，MUST NOT 启动浏览器或等待槽位

#### Scenario: 默认正常并在预览中可核对

- **WHEN** 客户首次打开人设初始化向导且未主动调整点赞倾向
- **THEN** “正常”档被选中，预览摘要显示“点赞倾向：正常”，生成的人设以 `like_affinity=normal` 持久化

#### Scenario: 点赞倾向标记不污染人设兴趣

- **WHEN** 云端收到 `like_affinity:like_more` 或 `like_affinity:like_most` 受控标记
- **THEN** 生成器在构造身份/兴趣 prompt 前移除该标记，并只把其映射到 `behavior_guidelines`，MUST NOT 把内部 token 写入 identity、interests 或 seed keywords

#### Scenario: 旧客户端无标记保持兼容

- **WHEN** 旧客户端的 `persona.generate` 请求没有点赞倾向标记
- **THEN** 云端按 `normal` 处理并生成合法人设，MUST NOT 因字段缺失拒绝请求

#### Scenario: 绑定未确立不触发

- **WHEN** 客户未登录、环境不属于该客户或 Cloud 无法权威解析账号绑定
- **THEN** 向导 MUST NOT 发起可落库的生成请求，仅可本地暂存选择，并 SHALL 显示可区分的客户鉴权/绑定拒因而非引导启动浏览器

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限或总条数超上限（含经自由文本注入的超量内容）
- **THEN** 云端诚实拒绝该次生成、MUST NOT 把超长/超量文本原样喂进 prompt，客户端显示真实失败原因

### Requirement: 云端下发已绑人设信号，边缘按 onboarding 三态渲染

Cloud SHALL 在客户鉴权环境状态中返回该环境绑定解析状态及账号“是否已绑人设”的权威结果。客户端 SHALL 按“绑定待解析 / 已解析且已绑 / 已解析且未绑”三态渲染；该真态来自客户拥有环境与账号绑定的服务端解析，MUST NOT 依赖浏览器、CDP、页面登录态或 Edge WS hello。为了避免 stale-true 泄漏，环境切换、客户切换或归属刷新时客户端 MUST 先清除上一账号投影，待目标环境的新权威响应重建。

浏览器无关 core 的 `ui.snapshot.personaBound` MAY 在兼容窗口继续下发，但只能作为同一权威结果的辅助同步，MUST NOT 成为新客户端判断人设绑定的唯一来源。旧客户端仍可按既有 WS 快照语义工作。

#### Scenario: 已绑人设且浏览器关闭时显示已设置

- **WHEN** 客户登录后获取一个绑定可信且此前已绑人设的环境状态，而该环境浏览器未启动
- **THEN** 客户鉴权响应返回已解析且 `personaBound=true`，客户端显示“已设置”并跳过向导，MUST NOT 要求启动环境

#### Scenario: 绑定待解析时中立态不谎称未设置

- **WHEN** 环境属于当前客户但 Cloud 尚未解析出可信账号绑定
- **THEN** 徽标显示中立“绑定待确认/状态加载中”，MUST NOT 谎称“未设置”，也 MUST NOT 把打开浏览器作为默认解析手段

#### Scenario: 切环境不泄漏旧账号已绑态

- **WHEN** 从一个已绑人设环境切换到另一个环境或客户 roster 发生变化
- **THEN** 客户端先清除旧 `personaBound` 投影，待目标环境权威响应后显示新状态，MUST NOT 把 stale true 泄漏给新账号

#### Scenario: 已解析且未绑时进入向导

- **WHEN** Cloud 已验证环境归属和账号绑定并确认该账号未绑人设
- **THEN** 客户端显示“未设置”并启用向导，浏览器关闭或槽位已满不得改变该判定

### Requirement: 生成 gate 判据不放宽但引导透明

新客户端的人设生成 gate SHALL 为“客户会话有效、环境归属通过、账号绑定已权威解析且 Cloud 请求通道可用”；判据 MUST NOT 包含 core 子进程存在、页面 `auth === logged in`、Edge WS 已连接、浏览器已启动、CDP 或槽位。未满足时客户端 MUST 禁止提交并分别显示客户登录、环境归属、绑定解析或 Cloud 可用性的真实前置，MUST NOT 提示“请先启动浏览器”。旧客户端在兼容窗口仍 MAY 使用既有 `auth && cloud` gate。

#### Scenario: 客户未登录时分态引导

- **WHEN** 客户会话无效
- **THEN** 生成按钮 disabled，提示客户登录，不得引导打开平台浏览器扫码

#### Scenario: 绑定已解析且 Cloud 可用时不看浏览器状态

- **WHEN** 客户会话有效、环境归属和绑定可信且 Cloud 请求通道可用，但浏览器关闭、CDP 缺席或 Edge WS 重连中
- **THEN** 生成按钮可用，提交不进入浏览器调度链

#### Scenario: Cloud 请求不可用时诚实失败

- **WHEN** 客户鉴权有效但 Cloud 人设接口不可达
- **THEN** 客户端显示 Cloud 请求失败/可重试状态，MUST NOT 把失败改写为“浏览器未启动”
