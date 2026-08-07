## MODIFIED Requirements

### Requirement: 叙述式活动流取代原始日志作为主信息面
主界面 SHALL 以叙述式活动流为主信息面：每条为一句人话 + 相对时间戳、最新在上、带「刚刚更新 · N 秒前」新鲜度走字；原始日志 SHALL 收进「开发者详情」折叠区。活动流条目 MUST 源自真实核心事件，MUST NOT 编造或美化未发生的动作。

活动流 SHALL 覆盖**账号在该平台上真实做过的写动作**，MUST NOT 因某类动作由内部委托路径执行而使其对运营不可见。一个动作**做了但不显示**与**没做**在客户端上 MUST 可区分：凡执行器已对该动作作出终局判断（成功 / 待第三方批准 / 结构性失败），活动流 MUST 如实呈现该判断。

当 Facebook Reel 已被 Edge 证明为新的活动卡片并上报为 `listKind:'reels'` 时，活动流 MUST 同步新增且仅新增一条“读”分类记录。该记录 SHALL 使用“看了/浏览了”的呈现事实措辞，MUST NOT 宣称看完或深度阅读；作者或摘要缺失时 MUST 使用通用人话回退，MUST NOT 暴露 URL 或原始 id。若同一 Reel 随后因 `facebook.note.open` 上报详情，客户端 MUST 保留详情数据流但 MUST NOT 再新增第二条“读”记录或第二次本地浏览增量。

#### Scenario: 核心事件映射为人话条目
- **WHEN** 核心进程产生已映射的动作日志（如点赞成功 / 提取内容 / 评论发布成功）
- **THEN** 活动流顶部新增一条对应的人话句子并带时间戳，今日计数同步递增

#### Scenario: 无新事件时不造条目
- **WHEN** 核心进程一段时间无新日志
- **THEN** 活动流不新增条目，新鲜度戳如实增长（如「1 分钟前」），不出现任何伪造的「仍在活动」条目

#### Scenario: 未识别日志行不进活动流
- **WHEN** 核心进程输出映射表未覆盖的日志行
- **THEN** 该行仅出现在「开发者详情」原始日志中，活动流不展示半截技术行

#### Scenario: 新 Reel 呈现立即形成一条读记录
- **WHEN** Edge 确认切换到一个新的活动 Reel 并上报单卡 Reels 批次
- **THEN** “今天做了这些”新增一条“读”分类记录，优先显示实际摘要和作者
- **AND** 本地浏览回退计数只增加一次

#### Scenario: Reel 元数据缺失时诚实回退
- **WHEN** 新活动 Reel 缺少作者或摘要
- **THEN** 活动流显示有界的摘要级或通用“看了一个 Reel”文案
- **AND** 不显示 Reel URL、noteId 或其它机器标识

#### Scenario: 随后的详情上报不重复读记录
- **WHEN** 已产生 Reel 呈现记录的同一规范 Reel 随后上报 `note.detail`
- **THEN** 详情继续送达 Cloud 和内容评估链
- **AND** 客户端不新增第二条“读”记录、不重复增加本地浏览回退计数

#### Scenario: Reel 未切换时不造读记录
- **WHEN** Reel 导航失败、活动身份不变或命中已见身份而未上报新单卡批次
- **THEN** 活动流不新增 Reel “读”记录

### Requirement: UI 事件解析结构化优先、字符串兜底且状态形状兼容
主进程 SHALL 经独立可单测模块解析核心输出为带类型 UI 事件：`[ui-event] {json}` 结构化行优先采用，既有中文日志行经映射表兜底；status 对象 MUST 保持既有字段形状向后兼容（新增 presence / publish 字段不删旧字段），既有计数递增行为不变。

中文日志兜底映射表 SHALL 被视为**小红书浏览会话专属**：其规则措辞只由小红书会话与仅小红书生效的启动块打印，Facebook 会话 MUST NOT 依赖该表产出任何活动条目或在场感。Facebook 打印的日志 MUST NOT 误命中该表中语义不符的规则；当某条 Facebook 日志会命中一条描述小红书专属行为的规则（如把「就地读」误述为「顺路去作者主页看看」）时，该 Facebook 日志措辞 MUST 被改到不再命中，MUST NOT 保留一条会对运营说谎的叙述。

#### Scenario: 结构化事件行直接采用
- **WHEN** 核心输出带 `[ui-event]` 前缀的合法 JSON 行
- **THEN** 解析结果直接驱动活动流 / 在场感 / 发布卡，不再走字符串匹配

#### Scenario: 旧日志行兜底映射保持计数行为
- **WHEN** 核心仅输出既有中文日志行（无结构化事件）
- **THEN** 活动流与计数仍按映射表工作，与改版前的计数行为一致

#### Scenario: 渲染器收到旧形状 status 不崩溃
- **WHEN** status 推送缺失新增的 presence / publish 字段
- **THEN** 渲染器按待命态安全降级渲染，不抛错、不白屏

#### Scenario: Facebook confirmed browse actions produce structured desktop events
- **WHEN** a Facebook child has actually started its enabled browse session, successfully reported `note.detail`, or confirmed `action.completed` for a like
- **THEN** it emits a structured UI event that updates the activity stream and presence projection for that child
- **AND** a successful `note.detail` contributes exactly one local view fallback increment and a confirmed like contributes exactly one local like fallback increment
- **AND** shadow, failed, already-liked, or no-target paths MUST NOT produce a success increment

#### Scenario: Facebook read activity identifies the opened content without raw identifiers
- **WHEN** a Facebook `note.detail` has a readable author nickname and post body
- **THEN** its desktop activity and presence text show bounded, whitespace-normalized author and leading-content excerpts
- **AND** when either field is unavailable, the text MUST degrade to an honest generic description and MUST NOT show a permalink or raw note ID

#### Scenario: Facebook 就地读的日志不得被叙述成跳转作者主页
- **WHEN** Facebook 就地身份读取（`identity.read_current`，不离开当前页）产生核心日志（词汇批 4 后 FB 会话结构上收不到任何作者主页命令，历史 `profile.open` 就地读形态由此取代）
- **THEN** 该核心日志 MUST NOT 命中中文兜底表中描述「顺路去作者主页看看」的跳转规则
- **AND** 客户端 MUST NOT 呈现任何声称已跳转作者主页的在场感文案

### Requirement: 同一条开帖在两条路径上的叙述必须一致

`facebook.note.open` 经浏览路径与经评论路径（按 permalink 开帖）SHALL 产出**同一套**「读」叙述与同一次本地浏览兜底增量，MUST NOT 因执行路径不同而一路可见、一路隐形。

当评论路径开帖成功读到内容、但评论框始终催不出来（回非成功以便云端换下一个候选）时，客户端 MUST NOT 产出「读失败」条目——帖子确实打开并读到了，该情形 SHALL 沉默，MUST NOT 把一次成功的阅读叙述成失败。

#### Scenario: 评论路径开帖产出与浏览路径一致的读条目
- **WHEN** 评论路径按 permalink 开帖并成功上报帖子详情
- **THEN** 活动流新增一条与浏览路径措辞一致的「读」条目
- **AND** 贡献且只贡献一次本地浏览兜底增量

#### Scenario: 开帖成功但评论框没找到不叙述为读失败
- **WHEN** 评论路径开帖成功、读到正文，但评论框未就绪，回 `editor_not_found`
- **THEN** 活动流 MUST NOT 新增「读失败」条目

### Requirement: 开发者详情展示安全且阶段诚实的引擎命令诊断

客户端 SHALL 在“开发者详情”中为当前环境展示 Cloud 主动下发到 Edge 的命令诊断。每条诊断 SHALL 包含接收时间、命令类型、当前可证明阶段、安全摘要和短关联标识，并 MUST 明确区分已收到、已拒绝、已交给执行器及 Edge 接收层能够直接观测的步骤结果。`received` 或 `dispatched` MUST NOT 被表述为命令已经执行成功、业务已经完成或平台已经确认。

命令摘要 MUST 由逐命令字段白名单生成。`facebook.reels.scroll{reason:'facebook_reels_primary'}` 与 `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}` SHALL 使用“进入 Reels”命令名称，并分别使用固定的主入口或 Feed 结束回退摘要；其它滚动命令（`{platform}.{feed|search}.scroll` 及不携 Reels 入口 reason 的 `facebook.reels.scroll`）SHALL 保留“页面滚动 / 滚动当前页面”。正文、标题、评论、私信、搜索词、群聊码、Cookie、Token、二维码、截图内容、完整 URL、浏览器调试地址、账号身份字段、任务永久键和原始 payload MUST NOT 进入命令诊断事件、renderer 状态或可见诊断行。文本字段只可展示有界字符数，URL 只可展示是否存在，安全枚举和有界计数可按需展示。未知命令或新增 payload 字段 MUST 默认不展示内容。

诊断 SHALL 仅保存在 Edge 本机内存中，按环境隔离并具有数量与时间双重上限；它 MUST NOT 进入普通活动流、Cloud 数据库或自动化回执。旧客户端状态缺少诊断字段时界面 MUST null-safe 降级。

#### Scenario: 已登记命令显示接收与交付边界

- **WHEN** 当前环境收到一条已登记、通过校验且存在本地处理器的主动命令
- **THEN** 开发者详情出现该命令，并将阶段更新为“已交给执行器”
- **AND** 界面明确该阶段不表示执行成功或平台确认

#### Scenario: Reels 主入口显示导航意图

- **WHEN** Edge 收到 `facebook.reels.scroll{reason:'facebook_reels_primary'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的主浏览入口摘要
- **AND** 阶段仍只显示 Edge 已收到或已交付的事实，不宣称已经进入 Reels

#### Scenario: Feed 结束回退显示导航意图

- **WHEN** Edge 收到 `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的 Feed 结束回退摘要
- **AND** 不把该命令显示为普通页面滚动

#### Scenario: 普通页面滚动保留原文案

- **WHEN** 滚动命令（`{platform}.{feed|search}.scroll` / `facebook.reels.scroll`）不携带任一 Reels 入口 reason
- **THEN** 开发者详情继续显示“页面滚动 / 滚动当前页面”

#### Scenario: 非法或未协商命令诚实显示拒绝

- **WHEN** Edge 收到未登记、能力未协商、payload 非法或没有本地处理器的主动命令
- **THEN** 诊断阶段显示“已拒绝”及固定安全原因，不显示已执行或成功
- **AND** 诊断行为不得改变原有 fail-closed 路由结果

#### Scenario: 只有可直接观测的步骤才显示结果

- **WHEN** `plan.response` 的顺序步骤在 EdgeClient 内完成并得到逐步结果
- **THEN** 对应诊断可更新为“步骤已完成”或“步骤失败”
- **AND** 该结果不得表述为整项业务完成或平台结果已确认

#### Scenario: 异步处理器不猜测终态

- **WHEN** 命令已经交给一个返回 `void` 或自行异步执行的业务处理器
- **THEN** 诊断停留在“已交给执行器”，直到未来有显式结果事件
- **AND** 客户端不得依据交付动作自行补造成功或失败

#### Scenario: 敏感 payload 只产生白名单摘要

- **WHEN** 评论、回复、发布、搜索、验证码或导航命令携带文本、账号标识、任务键、图片、坐标或完整 URL
- **THEN** 命令诊断只展示固定动作说明、允许的枚举、有界数量或文本字符数
- **AND** renderer 状态和可见诊断行中不存在上述原始内容或完整 payload

#### Scenario: 多环境命令诊断不串号

- **WHEN** 环境 A 与环境 B 同时收到不同命令且用户在二者之间切换
- **THEN** 开发者详情只展示当前选中环境的命令诊断
- **AND** 每个环境分别执行最多 50 条且最长 30 分钟的保留规则

#### Scenario: 普通活动流不展示接收噪声

- **WHEN** Edge 收到、拒绝或交付一条引擎命令
- **THEN** 该接收诊断只出现在开发者详情
- **AND** “今天做了这些”不得因此新增一条动作成功、失败或处理中记录

