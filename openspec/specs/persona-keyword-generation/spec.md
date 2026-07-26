# persona-keyword-generation Specification

## Purpose
TBD - created by archiving change edge-persona-keyword-generation. Update Purpose after archive.
## Requirements
### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 提供按维度选择关键词的人设向导——垂类（枚举快捷选 + 自定义自由文本）、兴趣（快捷标签多选 + 自由文本）、语气（枚举单选）与点赞倾向（正常 / 喜欢 / 更喜欢，默认正常）。点赞倾向 MUST 有真实输出映射：客户端 SHALL 以受控标记随 `keywordSelections` 发送，云端 SHALL 在生成兴趣关键词前剥离该标记，并把档位写入 `behavior_guidelines.like_affinity` 与匹配账号兴趣的 `like_principle`；MUST NOT 把内部标记写入身份或兴趣。除有明确映射的选择外，客户端 MUST NOT 提供对生成产物零影响的输入。

新版 Electron SHALL 经客户鉴权的环境级 HTTP 请求触发生成，主进程只提交由目标环境解析的 `envKey`、关键词、可选发言语言与 idempotency key；Cloud SHALL 由客户归属与持久绑定解析 `accountId`，请求体 MUST NOT 自报账号。旧版 Edge MAY 继续经运行中 core 发起 `persona.generate` WebSocket 请求，Cloud SHALL 从握手 session 取账号。两种入口 MUST 调用同一人设应用服务、共享按 `(accountId,idempotencyKey)` 的生成幂等、平台校验、输入上限、模型记账与失败语义。

HTTP 草稿生成 SHALL 使用足以覆盖 180 秒模型天花板的显式长超时；WebSocket 兼容入口继续使用 `timeoutMs ≥ 185s`。生成触发只要求 Cloud 能权威解析一个已存在账号，MUST NOT 要求目标环境此刻在线；无法解析持久绑定时 MUST 诚实拒绝且不调用模型。

#### Scenario: 停止环境通过客户鉴权触发生成

- **WHEN** 客户为自己拥有且已持久绑定账号的停止环境选定关键词与点赞倾向并点击生成
- **THEN** Electron 经具名 HTTP 桥提交 `envKey` 与受控输入，Cloud 解析绑定账号并生成草稿，MUST NOT 要求 core 在线

#### Scenario: 旧版运行中客户端继续兼容

- **WHEN** 旧版 Edge 在握手后发送 `persona.generate` WebSocket 请求
- **THEN** Cloud 仍从 session 账号处理并返回兼容响应，与 HTTP 入口使用相同生成规则

#### Scenario: 默认正常并在预览中可核对

- **WHEN** 客户首次打开人设向导且未主动调整点赞倾向
- **THEN** “正常”档被选中，预览摘要显示“点赞倾向：正常”，生成的人设以 `like_affinity=normal` 持久化

#### Scenario: 点赞倾向标记不污染人设兴趣

- **WHEN** Cloud 收到 `like_affinity:like_more` 或 `like_affinity:like_most` 受控标记
- **THEN** 生成器在构造身份/兴趣 prompt 前移除该标记，并只把其映射到 `behavior_guidelines`，MUST NOT 写入 identity、interests 或 seed keywords

#### Scenario: 绑定身份未知不触发付费生成

- **WHEN** 环境从未成功握手、绑定冲突、环境不归当前客户或账号行不存在
- **THEN** 客户 HTTP 入口 fail-closed 且不调用模型；旧 WS 入口仍要求握手 session 具有账号

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限或总条数超上限
- **THEN** Cloud 诚实拒绝并且绝不把超限内容喂进 prompt，Edge 透传失败原因

### Requirement: 云端生成经 JSON 序列化校验，生成失败硬 fail-closed 绝不回落默认人设

云端 SHALL 用登记进 role-catalog 的 persona 生成器角色调云端唯一文本大模型出口（按角色配模型、按 `accountId` 记账），输出 **JSON** → 经确定性序列化器转成 soul YAML → 过 `loadSoulFromValue` 结构校验。大模型超时 / 输出不可解析 / 校验不过时 MAY 修复重试 1–2 次；仍失败 MUST 诚实回 `generation_failed` / `persona_invalid`，该账号维持「缺人设」，MUST NOT 回落任何模板 / 默认人设、MUST NOT 静默返回半成品（守「绝不静默假成功」+「无默认人设」）。密钥 MUST 只在云端、只从启动期预载取。

#### Scenario: 生成成功回草稿

- **WHEN** 大模型输出经序列化 + `loadSoulFromValue` 校验通过
- **THEN** 云端回 `persona.generate` 响应，携草稿 soul YAML 与身份摘要；该草稿此刻 MUST NOT 落库

#### Scenario: 生成失败诚实拒绝不兜底

- **WHEN** 大模型超时或输出经重试仍不可解析 / 校验不过
- **THEN** 云端回 `generation_failed` / `persona_invalid`，账号维持「缺人设」，MUST NOT 回落任何模板 / 默认人设、MUST NOT 假成功

### Requirement: 生成调用幂等，重连或重试不产生双份付费

`persona.generate` MUST 幂等：云端对同一 idempotency key 的重复请求 MUST 命中缓存结果、MUST NOT 重复调大模型、MUST NOT 重复记账。仅 `persona.persist` 成功 SHALL 翻转账号「已绑人设」状态；`persona.generate` 本身 MUST NOT 改变绑定状态。

#### Scenario: 同幂等键命中缓存

- **WHEN** 同一 idempotency key 的 `persona.generate` 请求重复到达（客户端重发 / 网络重投）
- **THEN** 云端返回缓存的首次生成结果，MUST NOT 再次调用大模型、MUST NOT 二次记账

#### Scenario: 长在途遇自动重连不双计费

- **WHEN** 生成在 ≥185s 在途窗口内遭遇边缘自动重连（挂起请求被 reject）、客户端据幂等键重试
- **THEN** 幂等去重护住，MUST NOT 产生双份付费调用；账号绑定状态在 `persona.persist` 成功前保持不变

### Requirement: 草稿经客户确认后走现有已校验写入通道落库，边缘不本地判成功

客户确认草稿后，新版 Electron SHALL 经客户鉴权环境级 HTTP 请求提交目标 `envKey` 与确认后的 soul YAML；Cloud MUST 复核当前客户归属并解析持久绑定账号。旧版 Edge MAY 继续发送 `persona.persist` WebSocket 请求，Cloud 从握手 session 取账号。两种入口 MUST 复用同一人设应用服务与现有人设单写通道（soul 校验 + 外键守护 + 写库成功才刷内存镜像 + 绑定即热加载唤醒在线节点 + 首次绑定引导 + 诚实回执），MUST NOT 新造绕过校验的写路径。

Edge MUST 在请求发出前展示保存中状态，仅在 Cloud 成功回执后显示已保存/已更新；失败时 MUST 保留原人设与草稿并呈现真实 `reason`，MUST NOT 本地判成功。HTTP 保存不要求目标环境在线，成功回执只代表人设已持久化与热加载，MUST NOT 冒充浏览器已启动或首作已完成。

#### Scenario: 停止环境确认落库并绑定

- **WHEN** 客户在停止环境中确认合法草稿
- **THEN** Cloud 解析绑定账号、落 `persona_config`、刷新镜像并返回成功真态，目标 core 无需在线

#### Scenario: 保存失败保留原人设

- **WHEN** 归属/绑定在确认前变化，或 soul 非法、持久化失败
- **THEN** Edge 显示真实失败并保留原人设与可重试草稿，MUST NOT 显示成功

#### Scenario: 旧版 WebSocket 保存继续兼容

- **WHEN** 旧版 Edge 经 `persona.persist` 提交确认草稿
- **THEN** Cloud 继续从 session 账号调用同一单写服务并返回兼容回执

#### Scenario: 账号行缺失优雅回诚实失败

- **WHEN** 任一入口命中账号外键守护或权威绑定无法解析
- **THEN** Cloud 返回可区分的诚实失败、不落库、不刷镜像，向导可在账号身份落定后重试

#### Scenario: 空或非法人设被拒不落库

- **WHEN** 确认提交的 soul 为空、超限或结构非法
- **THEN** Cloud 诚实拒绝，MUST NOT 落库、MUST NOT 刷镜像

### Requirement: 大模型与密钥留云端，边缘只做交互

大模型调用、密钥、校验、序列化、落库、记账 MUST 全部在云端。边缘 SHALL 只做三件事：收关键词勾选、显示云端返回的草稿、捕获客户确认。边缘 MUST NOT 嵌入大模型、MUST NOT 持有大模型密钥、MUST NOT 直连 PG、MUST NOT 复制 soul 序列化器 / 校验器。

#### Scenario: 边缘不承载生成能力

- **WHEN** 审视边缘在本流程的职责
- **THEN** 边缘只收勾选 / 显示草稿 / 回确认；大模型、密钥、校验、序列化、落库、记账均在云端，边缘无其一

### Requirement: 生成 prompt 内置每账号差异化，差异化落在 seed_keywords

云端生成 SHALL 在 prompt 内置每账号差异化（如每账号差异化种子 + 采样温度），使跨账号产物有区分度；差异化 MUST 重点作用于 `seed_keywords` / 搜索词这条被平台当同质信号的链路，而非仅 `identity` / `tone` 文案字段。

#### Scenario: 同垂类不同账号产物有区分

- **WHEN** 同一垂类的两个不同账号以相近关键词生成
- **THEN** 两者 `seed_keywords` 呈现差异化、MUST NOT 逐字雷同

### Requirement: 新增协议消息走边缘发起的请求响应，不经主动命令白名单，两份 protocol.ts 逐字同步

新增的 `persona.generate` / `persona.persist` 及其响应 MUST 设计为**边缘发起的请求/响应**，回包走 pending-id 命中路径，MUST NOT 依赖 cloud→edge 主动命令下发、MUST NOT 需要 onMessage 主动命令白名单放行（规避静默丢弃 footgun）、MUST NOT 改动 command-bridge 动作映射。edge 与 cloud 两份 `protocol.ts` 的消息类型 MUST 逐字一致，`docs/protocol.md` 计数与消息表 MUST 同步更新，AC-PROTO 漂移哨兵 MUST 通过。

#### Scenario: 回包走 pending-id 不触白名单

- **WHEN** 云端回 `persona.generate` / `persona.persist` 的响应
- **THEN** 边缘按 pending-id 命中处理，MUST NOT 经主动命令白名单，MUST NOT 落入「其他主动消息暂忽略」被静默丢弃

#### Scenario: 两份 protocol.ts 不漂移

- **WHEN** 运行协议漂移哨兵（AC-PROTO）
- **THEN** edge 与 cloud 两份 `protocol.ts` 的 `MessageType` 穷举一致、校验通过

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

### Requirement: 人设向导使用吉祥物功能色并保留多平台身份

Edge 客户端账号人设向导 SHALL 使用 AIDCP 吉祥物色系建立局部视觉层级：青绿蓝作为通用功能交互色，金黄作为待确认/待更新状态色，珊瑚色可作为小红书平台点缀。选择项文字 SHALL 与区块标题形成可辨层级，MUST NOT 依赖过重字重表达选中状态；选中状态 SHALL 主要由指示器、边框、浅底和文字颜色共同表达。

平台身份与功能交互色 MUST 正交：当前环境为 `xiaohongshu` 时，人设浮层 SHALL 显示“小红书”及其平台点缀；当前环境为 `facebook` 时 SHALL 显示“Facebook”及 Facebook 平台蓝。通用选择、步骤和 CTA MUST NOT 因平台切换而改变功能语义或被写死为单一平台样式。

未选内容项和自定义入口的加号 SHALL 使用不依赖字体字形基线的几何绘制，确保跨 PingFang、Microsoft YaHei、Segoe UI 等系统字体时保持视觉居中。

#### Scenario: Facebook 环境显示平台身份但沿用通用功能色

- **WHEN** 当前环境平台为 `facebook` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“Facebook”并使用 Facebook 平台蓝，而步骤、选择项和主 CTA 仍使用吉祥物青绿功能色

#### Scenario: 小红书环境显示小红书平台身份

- **WHEN** 当前环境平台为 `xiaohongshu` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“小红书”并使用珊瑚平台点缀，MUST NOT 残留 Facebook 文案或平台类

#### Scenario: 加号跨字体保持居中

- **WHEN** 未选内容项或自定义入口在任一受支持系统字体栈下渲染
- **THEN** 加号由几何线条居中绘制，不依赖 `+` 字符的字形基线

### Requirement: 已绑账号可查看当前人设并经确认流程整体调整

人设向导 SHALL 同时支持首次绑定与已绑账号调整。已绑账号打开时 SHALL 先看到当前真实人设摘要和完整定义入口；点击调整后 MAY 以当前人设可精确反向映射的语气、语言、内容标签与点赞倾向预填选择，并生成一份新的完整草稿。确认动作 SHALL 明示会整体替换当前人设；只生成或预览 MUST NOT 修改现有人设。

#### Scenario: 已绑账号生成新草稿不影响当前人设

- **WHEN** 客户为已绑账号点击调整并生成一份新草稿但尚未确认
- **THEN** 当前 `persona_config` 与运行时人设保持不变，界面同时保留当前摘要与待确认草稿语义

#### Scenario: 确认后整体替换

- **WHEN** 客户核对新草稿后点击确认且 Cloud 保存成功
- **THEN** 账号人设整体替换为新 soul，后续运行即时使用新人设

### Requirement: 人设向导仅为 Facebook 显示受控发言语言
Electron 人设向导 SHALL 在“语气调性”下为当前平台明确为 Facebook 的环境显示“发言语言”单选，提供中文、英文、越南语；小红书与视频号 MUST NOT 显示该设置或发送其值。语言选择 SHALL 独立于自由关键词和点赞倾向，MUST NOT 编码进 `keywordSelections`。

#### Scenario: Facebook 环境要求选择语言
- **WHEN** 用户打开 Facebook 环境的人设初始化或更新向导
- **THEN** 向导显示中文/英文/越南语单选，未选择时禁止生成并给出明确提示

#### Scenario: 小红书不显示或发送语言
- **WHEN** 用户打开小红书环境的人设向导并生成草稿
- **THEN** 向导不显示发言语言，`persona.generate` 不携带 `writingLanguage`，现有关键词行为保持不变

#### Scenario: 切换环境不串语言选择
- **WHEN** 用户从一个已选越南语的 Facebook 环境切换到另一个环境
- **THEN** 向导从目标环境的 Cloud 权威快照回显或显示待选择，MUST NOT 沿用上一环境的越南语 DOM 状态

### Requirement: persona 请求以独立字段传递并回显写作语言
Edge 与 Cloud 的 `persona.generate` 请求 SHALL 以独立 `writingLanguage` 字段传递 Facebook 选择；Cloud 生成器 SHALL 在模型结果通过后确定性写入 soul。Cloud UI snapshot SHALL 以可选 `personaWritingLanguage` 回显账号真态，Edge MUST NOT 本地推断已保存值。

#### Scenario: 生成结果确定性包含语言
- **WHEN** Cloud 收到合法 Facebook `writingLanguage=en` 并成功生成人设
- **THEN** 返回的 soul 草稿包含 `writing_language: en`，该值不是模型自由输出

#### Scenario: 存量缺字段回显待补充
- **WHEN** Cloud 读取到已绑定但无 `writing_language` 的 Facebook 人设
- **THEN** snapshot 显式投影缺失状态，Edge 显示语言待补充，MUST NOT 默认勾选中文

### Requirement: 内容偏好最多选择二十四项并在超限点击处原位反馈

Electron 人设向导 SHALL 把用户可见的内容偏好限制为最多 24 个，并在内容偏好标题常驻展示 `已选 n/24`。该业务计数 MUST 只包含内容偏好区域内已选的预设与自定义项，MUST NOT 把语气、发言语言、点赞倾向或内部派生分类名计入客户的 24 个名额。

当已经选择 24 个内容偏好后，客户点击第 25 个未选项时，客户端 MUST 保持原 24 个选择不变、MUST NOT 短暂提交或激活第 25 项；被点击的项 SHALL 原位显示可感知的红色拒绝态，内容偏好区域 SHALL 同时给出“最多选择 24 个内容偏好，请先取消一个再选择”的可访问文本提示。反馈 MUST NOT 只依赖颜色。任一已选项 SHALL 始终允许取消；取消后提示 SHALL 收敛并立即允许选择其他项。

#### Scenario: 第二十四个内容偏好正常选中

- **WHEN** 客户当前已选 23 个内容偏好并点击一个未选项
- **THEN** 该项正常选中，计数显示 `已选 24/24`，客户端不显示超限错误

#### Scenario: 第二十五次选择在触发项原位拒绝

- **WHEN** 客户已经选择 24 个内容偏好并点击另一个未选项
- **THEN** 已选集合仍为原 24 项，被点击项不进入选中态但显示短暂红色拒绝态，内容偏好区域显示“最多选择 24 个内容偏好，请先取消一个再选择”的文本提示

#### Scenario: 取消后可以替换选择

- **WHEN** 客户在超限反馈后取消任一已选内容偏好，再点击此前被拒绝的项
- **THEN** 计数先降为 `已选 23/24` 并清除超限提示，随后新项正常选中且计数恢复为 `已选 24/24`

#### Scenario: 语气语言和点赞倾向不占内容偏好名额

- **WHEN** 客户已选择语气、发言语言或点赞倾向，并已选择 23 个内容偏好
- **THEN** 客户仍可再选择一个内容偏好达到 `已选 24/24`，这些单选设置不减少内容偏好额度

### Requirement: 自定义内容偏好与预设项共用上限且超限不丢输入

自定义内容偏好 SHALL 与预设内容偏好共用 24 项业务上限。达到上限后确认一个新的自定义偏好时，客户端 MUST NOT 创建或激活该项、MUST NOT 清空客户输入；输入区域 SHALL 显示与预设第 25 项一致的红色拒绝态和可访问文本提示，并保留焦点或把焦点落回可修改的输入控件。取消既有内容偏好后，客户 SHALL 能以保留的输入再次确认。

#### Scenario: 满额时新增自定义偏好保留输入

- **WHEN** 客户已选择 24 个内容偏好，在任一分类输入新的自定义偏好并确认
- **THEN** 新项不创建，原输入文本保持不变，输入区域显示红色拒绝态与最多 24 个的文本提示

#### Scenario: 腾出名额后确认保留的自定义偏好

- **WHEN** 客户在自定义偏好被拒后取消一个既有偏好，并再次确认保留的自定义输入
- **THEN** 自定义项成功创建并选中，输入框清空，计数回到 `已选 24/24`

### Requirement: 用户选择上限与传输安全上限分层且两条生成入口一致

系统 SHALL 保留 `keywordSelections` 的单项长度与总条数纵深防御，但传输条数上限 MUST 足以容纳 24 个用户可见内容偏好及其派生分类名、语气和点赞倾向。Electron 主进程、Cloud customer-auth 生成领域服务与旧 WS 兼容入口 MUST 使用一致的 64 条传输上限和 40 字单项上限。一个包含不超过 24 个可见内容偏好的正常客户端请求 MUST NOT 仅因内部派生分类标签而被拒绝；超过传输安全边界的畸形或旧客户端请求 MUST 在调用模型前以具体容量原因诚实拒绝。

#### Scenario: 二十四个跨分类偏好展开后仍可生成

- **WHEN** 客户选择 24 个分属不同分类的内容偏好，renderer 将它们连同分类名、语气和点赞倾向展开为不超过 64 条 `keywordSelections`
- **THEN** Electron 主进程与 Cloud 均受理该结构并进入正常生成链路，MUST NOT 返回 `invalid_request` 或 `input_too_large`

#### Scenario: 超过传输安全边界在模型前被拒绝

- **WHEN** 畸形或旧客户端提交超过 64 条 `keywordSelections`，或任一项超过 40 字
- **THEN** Electron 或 Cloud 在模型调用前以 `input_too_large` 类具体原因拒绝，MUST NOT 调用人设生成模型，MUST NOT 把错误塌成无法行动的通用参数提示

