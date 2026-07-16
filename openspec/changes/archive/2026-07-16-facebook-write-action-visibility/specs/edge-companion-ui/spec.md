## MODIFIED Requirements

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
- **WHEN** Facebook 执行 `profile.open` 的就地读（不离开当前页）
- **THEN** 该核心日志 MUST NOT 命中中文兜底表中描述「顺路去作者主页看看」的跳转规则
- **AND** 客户端 MUST NOT 呈现任何声称已跳转作者主页的在场感文案

### Requirement: 叙述式活动流取代原始日志作为主信息面
主界面 SHALL 以叙述式活动流为主信息面：每条为一句人话 + 相对时间戳、最新在上、带「刚刚更新 · N 秒前」新鲜度走字；原始日志 SHALL 收进「开发者详情」折叠区。活动流条目 MUST 源自真实核心事件，MUST NOT 编造或美化未发生的动作。

活动流 SHALL 覆盖**账号在该平台上真实做过的写动作**，MUST NOT 因某类动作由内部委托路径执行而使其对运营不可见。一个动作**做了但不显示**与**没做**在客户端上 MUST 可区分：凡执行器已对该动作作出终局判断（成功 / 待第三方批准 / 结构性失败），活动流 MUST 如实呈现该判断。

#### Scenario: 核心事件映射为人话条目
- **WHEN** 核心进程产生已映射的动作日志（如点赞成功 / 提取内容 / 评论发布成功）
- **THEN** 活动流顶部新增一条对应的人话句子并带时间戳，今日计数同步递增

#### Scenario: 无新事件时不造条目
- **WHEN** 核心进程一段时间无新日志
- **THEN** 活动流不新增条目，新鲜度戳如实增长（如「1 分钟前」），不出现任何伪造的「仍在活动」条目

#### Scenario: 未识别日志行不进活动流
- **WHEN** 核心进程输出映射表未覆盖的日志行
- **THEN** 该行仅出现在「开发者详情」原始日志中，活动流不展示半截技术行

## ADDED Requirements

### Requirement: Facebook 写动作必须在客户端如实分档呈现

客户端 SHALL 为 Facebook 的**评论、加群、搜索**产出结构化活动条目，且 MUST NOT 因这些动作由委托处理器（而非浏览会话主出口）执行而静默无声。叙述 MUST NOT 新增任何成功判定：客户端 SHALL 只叙述执行器**已经作出、且已回报云端**的判断，判据与回报云端的 `action.completed` 完全一致，客户端与云端 MUST NOT 就「某动作是否发生」给出互相矛盾的结论。

四档 SHALL 互斥且穷尽：

- **成功**——仅当执行器既有后置校验判成（评论经本人身份服务器确认、加群经成员信号或结构确认）。
- **待第三方批准**——一手 DOM 观察到待审徽章或参与审批弹层。MUST 自成一档、MUST NOT 表述为已发布 / 已加入、MUST NOT 贡献任何计数。
- **结构性失败**——结构上做不到（评论框没找到 / 没权限 / 没结果）。MUST 呈现人话原因，MUST NOT 直接吐机器码。
- **未开始**——资源被占、被独占任务抢占、会话关闭中、能力不支持、只观察不点。MUST NOT 产条目，MUST NOT 计为失败。

「未开始」的判定 SHALL 以**拒绝集**（列举不算数的原因）实现，MUST NOT 以白名单（列举算数的原因）实现——后者会使未来新增的失败原因静默消失。

计数 SHALL 只在评论真成功时贡献一次本地兜底 `comments` 增量；加群与搜索 MUST NOT 贡献任何计数（二者在云端权威计数投影中均不存在对应字段）。

活动条目的主语 SHALL 只取自一手数据（打进去的评论文本、现读到的群名、下发的搜索词），MUST NOT 展示 permalink 或原始 note ID；群名读取失败 MUST 回落通用文案，MUST NOT 用 URL 顶替。

#### Scenario: 评论真成功
- **WHEN** Facebook 评论经本人身份服务器确认落地（执行器回 `ok:true`）
- **THEN** 活动流新增一条含评论文本有界摘要的「评论了」条目
- **AND** 该条目贡献且只贡献一次本地 `comments` 兜底增量

#### Scenario: 评论卡在群参与审批
- **WHEN** 执行器观察到待审徽章或参与审批弹层，回 `ok:false, reason:'pending_group_approval'`
- **THEN** 活动流新增一条明确表述「评论待管理员批准、还没显示出来」的条目
- **AND** 该条目 MUST NOT 表述为已发布，MUST NOT 贡献任何计数

#### Scenario: 评论框没找到
- **WHEN** 执行器回 `ok:false, reason:'editor_not_found'`
- **THEN** 活动流新增一条含人话原因的「评论没发出去」条目，MUST NOT 直接展示 `editor_not_found` 机器码

#### Scenario: 被占用或被抢占不产条目
- **WHEN** 命令因 `busy` / `preempted_by_task` / `session_closing` / `browse_disabled` / `capability_unsupported` 回非成功
- **THEN** 活动流 MUST NOT 新增任何条目，且 MUST NOT 把该情形叙述为一次失败

#### Scenario: 未知失败原因默认可见
- **WHEN** 执行器回一个拒绝集之外、映射表未覆盖的新失败原因
- **THEN** 活动流 MUST 仍产出一条回落通用文案的失败条目，MUST NOT 静默吞掉

#### Scenario: 加群成功以云端同一证据闸为准
- **WHEN** 加群回 `ok:true` 且 `clicked===true`
- **THEN** 活动流新增一条含现读群名的「加入了小组」条目
- **AND** 该判据 MUST 与云端 `interaction.occurred` 的加群闸一致

#### Scenario: 加群待批准与需答问卷
- **WHEN** 加群回 `pending` 或 `questionnaire_required`
- **THEN** 活动流新增一条表述「等待管理员通过」或「需要回答入群问题、没有自动作答」的条目，MUST NOT 表述为已加入

#### Scenario: 已是成员或只观察不产条目
- **WHEN** 加群回 `already_member` 或 `observation_only`
- **THEN** 活动流 MUST NOT 新增条目——二者均未发生一次真实加群动作

#### Scenario: 搜索呈现容器与真实结果数
- **WHEN** Facebook 定向搜索在某群内成功返回候选
- **THEN** 活动流新增一条含现读群名、搜索词与真实候选数的条目
- **AND** 该条目 MUST NOT 贡献任何计数

#### Scenario: 搜索零结果与搜索失败可区分
- **WHEN** 搜索成功执行但零候选，或搜索因结构性原因失败
- **THEN** 前者 MUST 表述为「没有匹配的帖子」、后者 MUST 表述为搜索失败并给出人话原因，二者 MUST NOT 混为一谈

### Requirement: 同一条开帖在两条路径上的叙述必须一致

`note.open` 经浏览路径与经评论路径（按 permalink 开帖）SHALL 产出**同一套**「读」叙述与同一次本地浏览兜底增量，MUST NOT 因执行路径不同而一路可见、一路隐形。

当评论路径开帖成功读到内容、但评论框始终催不出来（回非成功以便云端换下一个候选）时，客户端 MUST NOT 产出「读失败」条目——帖子确实打开并读到了，该情形 SHALL 沉默，MUST NOT 把一次成功的阅读叙述成失败。

#### Scenario: 评论路径开帖产出与浏览路径一致的读条目
- **WHEN** 评论路径按 permalink 开帖并成功上报帖子详情
- **THEN** 活动流新增一条与浏览路径措辞一致的「读」条目
- **AND** 贡献且只贡献一次本地浏览兜底增量

#### Scenario: 开帖成功但评论框没找到不叙述为读失败
- **WHEN** 评论路径开帖成功、读到正文，但评论框未就绪，回 `editor_not_found`
- **THEN** 活动流 MUST NOT 新增「读失败」条目
