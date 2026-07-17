## ADDED Requirements

### Requirement: Facebook 打开发帖框必须使用下发预算内的有界等待

cloud SHALL 仅为 Facebook `select_mode` 下发 `timeoutMs=40_000`，edge SHALL 将该值作为“等待首页发帖入口 + 点击后等待 composer 编辑器”的总 deadline。edge MUST 在 deadline 内以有界轮询容忍入口渐进渲染，入口出现后 SHALL 立即继续，MUST NOT 使用一次性快照或固定长睡眠代替就绪判断。入口等待阶段 MUST 不超过 20 秒，点击后 SHALL 使用总 deadline 的剩余预算等待编辑器。

cloud 等待 `publish.command.result` 的窗口 SHALL 为下发预算加既有结果余量，使 edge 必须先于 cloud 收敛。小红书 `select_mode` MUST NOT 因本要求携带 Facebook 预算，其既有等待语义 MUST 保持不变。

deadline 内始终没有可点击入口时 edge MUST 诚实返回 `no_target`；入口已点击但编辑器未在剩余预算内出现时 MUST 诚实返回 `post_validate_failed`。两种情况均 MUST NOT 假成功、MUST NOT继续上传、填写或提交。

#### Scenario: 首页入口晚渲染后成功打开 composer
- **WHEN** Facebook 已确认处于个人首页，发帖入口在前几轮探测中不存在、随后在 20 秒入口窗口内出现
- **THEN** edge SHALL 在入口出现后点击一次，并在总 40 秒 deadline 内确认编辑器出现后返回 `ok:true`

#### Scenario: 入口预算耗尽时诚实失败
- **WHEN** Facebook 个人首页在入口等待窗口内始终没有可见发帖入口
- **THEN** edge SHALL 返回 `ok:false,error:'no_target'`，MUST NOT 点击其他相似控件，MUST NOT继续后续发布指令

#### Scenario: 点击后编辑器未出现
- **WHEN** edge 已点击经确认的首页发帖入口，但编辑器未在总 deadline 剩余预算内出现
- **THEN** edge SHALL 返回 `ok:false,error:'post_validate_failed'`，MUST NOT 把点击动作本身当作成功

#### Scenario: Cloud 等待窗口覆盖 edge 预算
- **WHEN** cloud 下发 Facebook `select_mode.timeoutMs=40_000`
- **THEN** cloud SHALL 等待 40 秒预算加既有 8 秒结果余量，MUST NOT 在 edge 正常等待期间以默认 30 秒提前超时

#### Scenario: 小红书发布计划不受影响
- **WHEN** cloud 构建小红书发布命令计划
- **THEN** 小红书 `select_mode` MUST NOT 携带 Facebook 的 40 秒预算，既有单指令等待行为 MUST 保持不变

### Requirement: Facebook 发帖入口只允许在已确认的个人首页语境中点击

edge 在查找或点击 Facebook 发帖入口之前 MUST 确认当前 pathname 为个人首页形态，并确认页面主结构已经就绪且不存在非 composer 的可见阻断 dialog/modal。该校验 MUST 在 `select_mode` 内重新执行，MUST NOT 只信任上一条 `navigate_entry` 的成功回执。

小组页、帖子详情页、个人资料页或其他同域页面即使出现 `write something`、`create post` 或等价文案，MUST NOT 被当作个人时间线发帖入口。首页语境在等待期间丢失时 edge MUST 停止并诚实失败。

#### Scenario: 小组页同文案入口不得点击
- **WHEN** 浏览器仍停在 `/groups/...`，页面存在可见 `write something` 控件
- **THEN** edge MUST NOT 点击该控件，MUST 返回首页未确认类失败而不是继续发布

#### Scenario: 从小组页真正落到首页后才点击
- **WHEN** `navigate_entry` 开始时浏览器位于小组页，随后 pathname 与页面主结构均确认落到个人首页，发帖入口晚渲染出现
- **THEN** edge SHALL 只在首页确认之后点击入口，MUST NOT 在旧小组页或导航过渡期点击

#### Scenario: 等待期间离开首页
- **WHEN** `select_mode` 等待入口期间 pathname 变为帖子详情、小组或登录/检查点页面
- **THEN** edge SHALL 立即停止入口点击并诚实失败，MUST NOT 继续消费相似文案控件

### Requirement: Facebook 首页导航必须以后置页面分类确认落地

`navigate_entry` 发送 Facebook 首页导航后 SHALL 在有界窗口内轮询后置页面状态。成功 MUST 同时满足 Facebook 正式域名、个人首页 pathname、页面不再加载且存在可见主区域或可复用 composer 编辑器，并排除登录、checkpoint、凭据输入和非 composer 阻断 dialog/modal。仅 hostname 相同 MUST NOT 构成导航成功。

导航未落地、登录/检查点或阻断弹层 MUST 按可区分原因诚实失败。日志 SHALL 记录阶段、pathname、分类、耗时和尝试数，MUST NOT 记录 URL query、正文、cookie、token 或账号秘密。

#### Scenario: 同域旧页面不能冒充首页成功
- **WHEN** `Page.navigate` 已发送但页面仍停留在同为 `facebook.com` 的小组或 permalink pathname
- **THEN** `navigate_entry` MUST NOT 返回 `ok:true`，SHALL 继续有界等待并在耗尽后返回首页未落地原因

#### Scenario: 首页结构完成后导航成功
- **WHEN** 页面 pathname 为 `/` 或 `/home.php`、主区域可见且不存在阻断态
- **THEN** `navigate_entry` SHALL 返回 `ok:true`，允许后续 `select_mode` 独立执行

#### Scenario: 登录或检查点页面诚实分类
- **WHEN** 导航结果落在 login、checkpoint、recover 或凭据输入页面
- **THEN** edge SHALL 返回对应登录/检查点失败原因，MUST NOT 把它折叠成首页成功或 composer `no_target`

#### Scenario: 阻断 dialog 不被穿透
- **WHEN** 首页路由上存在不包含 composer 编辑器的可见阻断 dialog/modal
- **THEN** edge SHALL 返回阻断类失败，MUST NOT 尝试点击 dialog 后方的发帖入口

### Requirement: Facebook 发布目标护栏必须读取生产规范字段

Facebook `select_mode` 的目标护栏 SHALL 读取 cloud 真实下发的 `params.optionKind` 与 `params.optionValue`。显式目标值只有 `facebook_personal_timeline` 可被接受；任何其他显式目标值 MUST 返回 `unsupported_target`。edge MUST NOT 以测试专用或旧形状的 `params.value` 代替规范目标字段作授权判断。

#### Scenario: 生产参数形状允许个人时间线
- **WHEN** edge 收到 `{optionKind:'target',optionValue:'facebook_personal_timeline'}`
- **THEN** 目标护栏 SHALL 允许继续执行首页确认与 composer 打开

#### Scenario: 不支持的生产目标被拒绝
- **WHEN** edge 收到 `{optionKind:'target',optionValue:'facebook_group'}` 或其他非个人时间线显式目标
- **THEN** edge SHALL 返回 `ok:false,error:'unsupported_target'`，MUST NOT 导航、查找或点击发帖入口

#### Scenario: 旧 value 字段不得绕过护栏
- **WHEN** `params.value` 与规范 `optionValue` 冲突或只提供 `params.value`
- **THEN** edge MUST 以规范字段为准，MUST NOT 因测试构造的旧字段错误授权一个不支持的发布目标
