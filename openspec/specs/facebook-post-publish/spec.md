# facebook-post-publish Specification

## Purpose
TBD - created by archiving change facebook-post-publish. Update Purpose after archive.
## Requirements
### Requirement: Facebook 发帖图片素材池按账号管理

系统 SHALL 为 Facebook 账号提供独立的发帖图片素材池。运营在控制台按账号批量上传图片后，cloud MUST 校验图片类型与大小、通过可注入 `ObjectStore` 转存到 OSS 稳定公网 URL，并把图片写入该账号的素材池。素材池 MUST 记录图片组、组内顺序、状态、原文件名、内容类型、字节数、sha256、OSS URL、可选素材说明、创建/更新时间。素材池写入 MUST 先确认账号存在且 `accounts.platform === 'facebook'`，MUST NOT 为不存在账号、退役账号、或非 Facebook 账号创建素材。上传失败、OSS 未配置、类型非法、大小超限时 MUST 诚实拒绝，MUST NOT 写入假 URL 或本地临时路径。

#### Scenario: Facebook 账号批量上传图片成功
- **WHEN** 运营在控制台为一个已存在的 Facebook 账号批量上传 3 张合法图片，且 OSS 上传能力就绪
- **THEN** cloud SHALL 把 3 张图片转存为 OSS 稳定公网 URL，并为该账号写入 3 个默认单图图片组，状态均为 `available`

#### Scenario: 非 Facebook 账号不能写入 FB 发帖素材
- **WHEN** 运营请求为一个 `accounts.platform='xiaohongshu'` 的账号上传 Facebook 发帖图片
- **THEN** API SHALL 返回拒绝原因（如 `platform_not_supported`），MUST NOT 写入任何素材行或 OSS 假记录

#### Scenario: OSS 上传失败不写假素材
- **WHEN** 某张图片校验通过但 OSS `put` 失败或未配置
- **THEN** 该图片 SHALL 不进入素材池，API SHALL 如实返回失败项与原因，MUST NOT 存储本地临时路径、占位 URL、或伪造 OSS URL

### Requirement: Facebook 草稿从账号素材池锁定图片组

Facebook 发帖草稿生成时，系统 SHALL 从该账号素材池选择下一组 `available` 图片组并原子锁定为 `reserved`，把该组 OSS URL 按顺序写入 `publish_log.images`，并记录 `reserved_record_id`。素材不足时 MUST fail-closed：不生成可发布草稿、不调用 edge、不改走纯文字发布、不复用已用素材。草稿被人审拒绝或在提交前失败时，系统 SHALL 将对应图片组释放回 `available`；提交已发生但确认不明时 SHALL 标记 `quarantine`；服务端确认发布成功后 SHALL 标记 `used` 并记录 `used_record_id`。状态转换 MUST 与发布记录保持一致，MUST NOT 静默重复消费同一图片组。

#### Scenario: 生成 FB 草稿时锁定下一组图片
- **WHEN** 某 Facebook 账号有至少一组 `available` 图片，排期或手动发布触发草稿生成
- **THEN** 系统 SHALL 原子锁定排序最靠前的可用图片组为 `reserved`，把该组图片 URL 写入 `publish_log.images`，并把 `reserved_record_id` 指向该草稿

#### Scenario: 素材不足不生成可发布草稿
- **WHEN** 某 Facebook 账号没有 `available` 图片组
- **THEN** 发布触发 SHALL fail-closed 并返回“图片素材不足”类原因，MUST NOT 生成可提交草稿、MUST NOT 发布纯文字、MUST NOT 复用 `used` / `reserved` / `quarantine` 素材

#### Scenario: 人审拒绝释放素材
- **WHEN** 一个使用素材池图片的 Facebook 草稿在人审中被拒绝，且尚未下发提交
- **THEN** 该草稿关联图片组 SHALL 从 `reserved` 释放回 `available`，并清除 `reserved_record_id`

#### Scenario: 提交后确认不明隔离素材
- **WHEN** edge 已可能点击 Facebook Post，但没有取得可靠服务端确认
- **THEN** 关联图片组 SHALL 标记为 `quarantine`，MUST NOT 自动释放为可用，也 MUST NOT 自动重试该草稿

### Requirement: Facebook 个人主页发帖执行器支持宽窄布局且独立于 XHS

edge SHALL 提供 Facebook 发帖执行器，负责个人主页/首页 composer 的打开、聚焦、正文逐字输入、图片上传、提交与确认。该执行器 MUST 使用 Facebook driver 的 `publish` 能力装配，MUST NOT 调用 XHS 发布 URL、XHS 发布 tab、XHS 标题/话题/封面处理器。执行器 MUST 覆盖宽屏与窄屏桌面布局，以结构定位和可见性判断为主，MUST NOT 依赖固定坐标或宽屏专属导航。正文输入 MUST 使用逐字符的拟人化键盘节奏，MUST NOT 通过一次性整段粘贴或一次性 `Input.insertText` 灌入正文。当前页面的 dialog 消失或明确正向提交提示 SHALL 表示用户可见的“已提交”；只有从当前页面取得稳定帖子 ID/permalink 才能表示“已发布”。正常发布链路 MUST NOT 通过刷新页面获得该结论。提交前失败、页面已提交但链接缺失、以及已取得链接 MUST 区分上报。

#### Scenario: 宽屏 composer 可打开并输入
- **WHEN** Facebook edge 在 `1365x900` desktop viewport 收到 no-submit composer probe
- **THEN** 执行器 SHALL 打开 composer、聚焦正文编辑器、逐字输入并清空测试文本，且不提交任何内容

#### Scenario: 窄屏 composer 可打开并输入
- **WHEN** Facebook edge 在 `430x932` 或 `768x900` desktop viewport 收到 no-submit composer probe
- **THEN** 执行器 SHALL 通过结构定位完成 composer 打开、聚焦、逐字输入、清空，MUST NOT 依赖宽屏导航或固定坐标

### Requirement: Facebook 发帖真实提交受显式探针门禁保护

Facebook 发帖真实提交 SHALL 在 no-submit composer 和媒体探针通过后才能启用。真实写入探针 MUST 仅允许在操作员自有 disposable Facebook 账号/目标上运行，并要求显式环境门禁；成功判定 MUST 是 reload/server confirmation，而不是按钮点击或乐观 DOM。探针输出 MUST 只包含状态、计数、哈希和原因码，MUST NOT 输出 raw cookie、raw token、raw 评论/正文秘密或未脱敏账号敏感信息。

#### Scenario: 无门禁时真实提交被阻止
- **WHEN** 运行 Facebook real-submit probe 但缺少任一显式门禁或 disposable 确认
- **THEN** probe SHALL 在提交前停止并返回 blocked reason，MUST NOT 点击 Post

#### Scenario: 真实提交以服务端确认为成功
- **WHEN** gated real-submit probe 在 disposable 目标上执行并点击 Post
- **THEN** 只有 reload/server confirmation 或稳定 permalink 证据出现时才判成功；否则 SHALL 返回未确认状态，MUST NOT 把点击动作本身当成功

#### Scenario: 探针输出脱敏
- **WHEN** probe 输出结果
- **THEN** 结果 SHALL 只含布尔值、数量、哈希、状态和原因码，MUST NOT 输出 raw token、cookie、正文全文或账号敏感字段

### Requirement: 控制台提供 Facebook 发帖素材管理

控制台 SHALL 在 Facebook 账号配置中提供发帖素材管理入口，展示可用/已锁定/已使用/停用/隔离图片组数量，并支持批量上传、缩略图预览、排序、素材说明、停用与删除。写操作 MUST 非乐观：只有服务端写入成功并回读真态后，前端才显示成功状态。非 Facebook 账号 MUST NOT 展示该入口。删除/停用已 `reserved` 或 `quarantine` 的图片组 MUST 有明确限制或确认文案，MUST NOT 静默破坏在途草稿。

#### Scenario: Facebook 账号显示素材管理入口
- **WHEN** 账号列表中的某账号 `platform === 'facebook'`
- **THEN** 控制台 SHALL 在 FB 配置中显示发帖素材管理入口，并展示素材池状态汇总

#### Scenario: 非 Facebook 账号不显示素材入口
- **WHEN** 账号平台不是 Facebook
- **THEN** 控制台 SHALL 不展示 Facebook 发帖素材入口，避免把素材写入错误平台

#### Scenario: 上传成功后回读真态
- **WHEN** 运营上传图片并服务端写入成功
- **THEN** 控制台 SHALL 依据服务端返回的素材列表/状态刷新展示，MUST NOT 在请求未完成时乐观宣称已入库

### Requirement: Facebook 打开发帖框必须使用下发预算内的有界等待

cloud SHALL 仅为 Facebook `select_mode` 下发 `timeoutMs=40_000`，edge SHALL 将该值作为“等待首页发帖入口 + 点击后等待 composer 编辑器”的总 deadline。edge MUST 在 deadline 内以有界轮询容忍入口渐进渲染，入口出现后 SHALL 立即继续，MUST NOT 使用一次性快照或固定长睡眠代替就绪判断。入口等待阶段 MUST 不超过 20 秒，点击后 SHALL 使用总 deadline 的剩余预算等待编辑器。

cloud 等待 `facebook.publish.command.result` 的窗口 SHALL 为下发预算加既有结果余量，使 edge 必须先于 cloud 收敛。小红书 `select_mode` MUST NOT 因本要求携带 Facebook 预算，其既有等待语义 MUST 保持不变。

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

### Requirement: Facebook 候审链路不使用内容质量评分

Facebook 发布 SHALL NOT 调用内容质量评分 LLM，也 SHALL NOT 用固定高分、零分、`NaN` 或小红书评分结果冒充 Facebook 质量结论。系统 MUST 以显式 `not_applicable` 状态表示 Facebook 未评分，并 SHALL NOT 因 `qualityScore` 触发 `retry` 或 `abort`。

满足既有素材、发言语言与确定性处理要求后，Facebook 候选 SHALL 确定性进入 `manual_review`，继续沿用既有草稿落库、审批卡、人工授权和下发确认链。取消内容质量评分 MUST NOT 被解释为自动发布，MUST NOT 绕过人工审批或真实提交确认。

#### Scenario: Facebook 不调用两个质量模型

- **WHEN** 一轮 `platform='facebook'` 发布生成进入后处理和 admission 阶段
- **THEN** `publish:QualityScorer` 与 `publish:ApprovalGatekeeper` 的 LLM 调用次数 SHALL 均为 0
- **AND** 质量状态 SHALL 为 `not_applicable`、质量分 SHALL 为 `null`

#### Scenario: Facebook 不因质量分重试

- **WHEN** Facebook 正文、素材和既有确定性前置条件均有效
- **THEN** 系统 SHALL 产生 `manual_review` admission 并落一条 `pending_approval` 草稿
- **AND** MUST NOT 返回“内容质量不达标”或启动盲目重生成

#### Scenario: 不评分仍必须人工审批

- **WHEN** Facebook 候选已进入 `pending_approval`
- **THEN** 系统 SHALL 等待现有人工授权后才允许进入 edge 下发段
- **AND** 未授权时 MUST NOT 调用 Facebook 提交动作

#### Scenario: 小红书链路不受影响

- **WHEN** 发布平台为 `xiaohongshu`
- **THEN** 系统 SHALL 继续调用既有质量评分与 Gatekeeper，沿用原分数、降级公式、阈值和动作语义

### Requirement: 正文填写的单步预算随长度伸缩，且边缘必先于云端答复

逐字符输入是 O(正文长度) 的操作，MUST NOT 由云端用与长度无关的常数窗口去等它——否则云端先判失败、边缘仍在往活着的编辑器里写字，形成「记录已 failed、页面上却躺着半篇正文」的错位，并让恢复后的浏览循环与被放弃的打字循环共用同一个 CDP session。

cloud SHALL 按正文长度算出 Facebook `fill_field` 的执行预算，随指令下发（复用既有的 `PublishCommandPayload.timeoutMs`）。云端等待窗口 SHALL 为「下发预算 + 兜底余量」，使边缘**必定先答**；该 timer 的语义 SHALL 退化为「边缘真的失联」的兜底，MUST NOT 作为正常路径的收敛手段。指令**不带**预算时（小红书全路径）等待窗口 MUST 逐字节沿用既有常数窗口。

预算上限 MUST 严格小于边缘发布租约 TTL（安全比例 0.4），否则边缘会在打字途中单方面过期租约、恢复浏览循环去驱动半写的编辑器。

默认配置 SHALL 使用 20 秒固定开销、每字 250 毫秒和 400 秒预算上限，因此 Facebook 正文逐字输入硬上限为 1520 字；默认发布租约 SHALL 为 1000 秒，使填写预算继续不超过租约的 0.4。

edge SHALL 按下发预算自我掐表：预算耗尽即停止输入、清空编辑器、诚实回报，MUST NOT 继续写入已被上游放弃的编辑器；清场失败 MUST 如实上报，MUST NOT 谎报干净页。云端未下发预算时，edge SHALL 使用**小于**云端常数窗口的兜底预算，使旧云端配新边缘时仍是边缘先答。

逐字符的拟人化键盘节奏 MUST NOT 因本要求而改变。

#### Scenario: 长正文在下发预算内打完
- **WHEN** 云端为一篇 300 字正文下发按长度算出的 `fill_field` 预算
- **THEN** edge SHALL 在预算内逐字输完全文并通过全文校验
- **AND** cloud MUST NOT 在边缘答复之前判超时

#### Scenario: 预算耗尽即停手清场
- **WHEN** 正文在下发预算内打不完
- **THEN** edge SHALL 停止输入、清空编辑器、回报 `fill_deadline_exceeded`（清不干净则标为 dirty）
- **AND** MUST NOT 提交，MUST NOT 让输入循环继续写入编辑器

#### Scenario: 正文超出可打完的上限
- **WHEN** 正文长度超出预算上限所能容纳的字符数
- **THEN** cloud SHALL 诚实 `failed`（`content_too_long`）
- **AND** MUST NOT 截断正文，MUST NOT 下发任何指令

#### Scenario: 默认 1520 字边界
- **WHEN** Facebook 正文按默认配置包含 1520 个 Unicode 码位
- **THEN** cloud SHALL 允许进入命令序列，并为正文填写下发 400 秒预算
- **AND** 1521 个 Unicode 码位 SHALL 以 `content_too_long` 在零下发状态诚实失败

#### Scenario: 小红书路径不受影响
- **WHEN** 发布平台为小红书
- **THEN** 指令 MUST NOT 携带执行预算，云端等待窗口 MUST 与既有常数窗口逐字节一致

### Requirement: 正文校验必须回读全文

「插入调用没报错」不等于「文本进去了」。正文校验 MUST 回读编辑器**全文**并确认其完整包含终稿正文；MUST NOT 以正文前缀片段作为接受判据——前缀探针会把「编辑器吞掉正文主体」判成成功，从而真的发出一篇被截断的帖子。

编辑器内出现超出终稿正文的额外内容（如打字途中被 typeahead 劫持插入）MUST 视为失败，MUST NOT 提交。

打字前 edge MUST 先清空编辑器并校验其为空：composer 会复用已存在的编辑区、而输入是在光标处**追加**，不清空即会把上一次失败留下的残稿与本篇拼接后发出。

聚焦不是最终成功判据，但 SHALL 是开始输入前的强制前置条件。edge MUST 将焦点绑定到本次唯一定位到的
编辑器，并确认 `document.activeElement` 正是该编辑器后，才允许派发清空或字符输入；MUST NOT 把
“坐标点击已完成”或“某个当前焦点的文本恰好为空”当作目标编辑器已聚焦。编辑器焦点不能确认时，
edge SHALL 诚实回报未开始并保持零字符派发。最终成功判据仍是目标编辑器的全文回读。

Facebook 在选择图片后可能保留旧 composer 并新建一代携带图片的前台 composer。edge SHALL 将文件
输入、图片预览、正文编辑器和提交按钮绑定到同一代前台 composer，MUST NOT 用 DOM 顺序中的第一个
dialog 作为目标。存在多个可见 composer 时，只有唯一位于最上层且包含唯一可见编辑器的 composer
可以成为当前目标；无法唯一确立时 SHALL 以 `ambiguous_target` 停手。

上传成功必须由当前 composer 内与本次文件名一致的新增 `blob:` 图片预览证明。页面头像、既有网络
图片、其他 dialog 或旧 composer 内的图片 MUST NOT 作为上传成功证据。上传引发 composer 换代时，
edge SHALL 在上传确认后重新绑定新一代前台 composer，再开始正文清场与输入。

逐字输入期间，edge SHALL 在每个字符派发前确认 `document.activeElement` 仍是本次绑定的编辑器。
焦点或目标身份漂移时 SHALL 在下一个字符前停止并回报 `composer_focus_lost`，MUST NOT 把剩余正文
继续写入任意当前焦点。失败清场只能作用于仍可确认的同一编辑器；目标归属不明时 MUST 如实标记脏页。

#### Scenario: 编辑器吞掉正文主体
- **WHEN** 编辑器只接受了正文的前若干字符，其余被静默丢弃
- **THEN** edge SHALL 回报 `content_not_accepted` 并清空编辑器
- **AND** MUST NOT 判成功、MUST NOT 提交

#### Scenario: composer 带着上一篇残稿
- **WHEN** 打开的 composer 内已存在上一次失败留下的正文
- **THEN** edge SHALL 先清空并校验为空再开始输入
- **AND** 清不干净则回报 `composer_not_clean`，MUST NOT 在残文之上追加、MUST NOT 开始打字

#### Scenario: 坐标点击没有把焦点交给目标编辑器
- **WHEN** edge 已点击编辑器坐标，但 `document.activeElement` 仍不是本次唯一定位到的编辑器
- **THEN** edge SHALL 对该编辑器执行有界的程序化聚焦并重新确认目标身份
- **AND** 仍不能确认时 SHALL 零字符失败，MUST NOT 向错误焦点逐字输入

#### Scenario: 图片上传换代后旧 composer 仍留在 DOM
- **WHEN** 上传图片后 Facebook 保留旧 composer，并新建携带本次图片预览的前台 composer
- **THEN** edge SHALL 在新 composer 的编辑器内填写正文，旧 composer 保持不变
- **AND** 头像或旧 composer 的图片 MUST NOT 提前确认上传成功

#### Scenario: 逐字输入中途焦点漂移
- **WHEN** 已输入正文前缀后，页面把焦点移到另一个 composer 或页面控件
- **THEN** edge SHALL 在派发下一个字符前停止并回报 `composer_focus_lost`
- **AND** 剩余正文 MUST NOT 写入新焦点，失败结果的外层 `reasonCode` MUST NOT 为 `confirmed`

### Requirement: 正文长度在生成侧确定性收口，且越界不得截断或废稿

各平台正文长度区间 MUST 有唯一事实源，生成 prompt 里的长度要求与生成后的校验 MUST 读同一处；
MUST NOT 在两处各写一份数字——改一处而另一处照旧不会产生任何报错，症状只是「规则明明写着却不生效」。

云端 MUST 在内容生成后对正文长度做确定性判定，MUST NOT 只依赖 prompt 里的软提示。
长度判定 MUST 按码位计数，与边缘逐字输入循环及填写预算换算同口径。

判定结果 MUST 分三态，且三态的处置各不相同：

- 落在区间内 SHALL 直接采用。
- 越界但在容差内 SHALL 采用并记录偏离，MUST NOT 触发重写——为几个字重写等于给几乎每一篇多付一次
  模型调用，而后果只是篇幅偏离、完全可恢复。
- 越出容差 SHALL 带纠正说明重写，且重写 MUST 有上限。纠正说明 MUST 点名实测字数、目标区间与修改方向；
  不携带这三项的重试只是重掷一次骰子，期望值与首稿相同。

重写次数用尽后正文仍越出容差时，系统 SHALL 采用偏离较小的一稿并响亮记录，
**MUST NOT 中止发布管线**（长度区间是质量目标而非物理约束，为它废掉整篇稿子是过度加闸），
**MUST NOT 截断正文以「满足」区间**（截断产生残句，且会把「模型没有遵从要求」伪装成一次正常产出）。

`content_too_long` 仍 SHALL 作为下发前的诚实闸保留，但 MUST NOT 被当作长度问题的解法：
它在图片已生成、人工已审核之后才响。

#### Scenario: 正文略微超出区间
- **WHEN** 生成的正文越界幅度落在容差内
- **THEN** 系统 SHALL 采用该稿并记录实测长度与偏离
- **AND** MUST NOT 因此重新调用模型

#### Scenario: 正文长度离谱
- **WHEN** 生成的正文越出容差
- **THEN** 系统 SHALL 附带实测字数、目标区间与修改方向重写，且重写次数受上限约束
- **AND** 重写后合格则采用重写稿

#### Scenario: 重写后仍然越界
- **WHEN** 重写次数用尽而正文仍越出容差
- **THEN** 系统 SHALL 采用偏离较小的一稿并记录该事实
- **AND** MUST NOT 截断正文，MUST NOT 中止发布管线

### Requirement: 在途发布的诚实回执与页面写者在场是两件事

断连、暂停与执行器故障等回收路径 MUST 立即把全部在途发布诚实判失败并发出回执，
使云端与审批侧看到失败而非半成品。

但「回执已发出」MUST NOT 被读成「页面已经空出来」。发布 dispatch 仍在页面上按自身预算逐字输入，
只有它自己的收敛才证明写者离开。因此判定「普通浏览可否恢复」的探针 MUST 反映**页面写者在场**，
MUST NOT 读那张会被回收路径整表清空的回执登记。

两者混用的后果不是重复发帖（提交另有租约闸挡住），而是**两个写者短暂共用同一个页面**：
恢复导航把发布页导走，发布一侧看到的是自己写入的正文凭空消失。

写者在场计数 MUST 由 dispatch 自身的生命周期成对增减，且加计与其后必然执行的减计之间
MUST NOT 存在可抛出的语句——一次未配对的加计会让浏览永久冻结。

#### Scenario: 云端连接断开时正文仍在输入中
- **WHEN** 回收路径已为在途发布发出诚实失败回执，而 dispatch 仍在页面上逐字输入
- **THEN** 普通浏览 SHALL 保持封锁，直到该 dispatch 真正收敛
- **AND** dispatch 收敛后 SHALL 恢复浏览

