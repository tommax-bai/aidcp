# feishu-command-ingestion Specification

## Purpose
TBD - created by archiving change feishu-message-fast-ack. Update Purpose after archive.
## Requirements
### Requirement: 命令事件受理即回执（fast-ack）

飞书命令消息事件的处理器 SHALL 在**受理该事件后立即返回**（触发 SDK 向飞书回帧），MUST NOT 等待命令执行完成再回执。命令执行与事件回执解耦，使长耗时命令不再因处理器长时间不回帧而被飞书判超时、重推。

#### Scenario: 长耗时命令不再被重推、只执行一次

- **WHEN** 收到一条会触发长耗时执行的命令消息（如 `/publish`，发帖生成流水线实测约 3 分钟）
- **THEN** 处理器受理后立即返回、SDK 及时回帧，飞书 MUST NOT 因超时重推同一条消息
- **AND** 该命令只被执行一次，MUST NOT 因重推而弹出误导性的「发帖未产出／已有一轮在运行中」卡

#### Scenario: 快命令行为不回退

- **WHEN** 收到一条秒级完成的命令消息（如 `/status`）
- **THEN** 处理器同样受理即返回，命令照常执行并回结果卡，行为与时序无可感知回退

### Requirement: 命令结果异步回卡、honest-status 不变、无启动中间卡

命令执行完成后，系统 SHALL 异步发送反映**真实终态**的结果卡，措辞与配色沿用既有 honest-status 判级（触发成功／未产出／失败分色，MUST NOT 把「触发成功」染成「已发布」）。系统 MUST NOT 在终态卡之前插入「任务启动中／已触发」等中间卡。后台执行抛出的意外错误 MUST 被捕获并记录，MUST NOT 中断或重复入口处理。

#### Scenario: 终态卡异步照发、内容不变

- **WHEN** 命令在后台执行完成（成功／未产出／失败）
- **THEN** 系统异步发送与改动前**一字不改**的终态结果卡（含发帖审批卡），只是发送时机从「阻塞后发」变为「执行完异步发」

#### Scenario: 不插入启动中间卡

- **WHEN** 命令被受理并转入后台执行
- **THEN** 在终态卡到达前，系统 MUST NOT 向用户发送任何「任务启动中／已触发」中间卡

#### Scenario: 后台执行异常不外溢

- **WHEN** 后台命令执行抛出意外错误
- **THEN** 错误被捕获并记录日志，入口处理不崩溃、不重复处理该事件

### Requirement: 重复执行由既有并发闸兜底、入口不自建去重

入口 MUST NOT 依赖 fast-ack 单独保证「恰好一次」。当重复的命令仍抵达执行层（如长连接**重连 replay** 触发的重推），已在运行的发帖生成 SHALL 由既有并发闸拦截、跳过第二次，MUST NOT 产出第二篇帖子。本次入口层 MUST NOT 新增 `message_id`/`event_id` 显式去重。

#### Scenario: 重连 replay 重推仍不重复发帖

- **WHEN** 一条重复的 `/publish` 在首轮发帖生成仍在运行时抵达编排器
- **THEN** 该次被并发闸判 skipped、不产出第二篇帖子，即使 fast-ack 已消除超时重推这一主因

### Requirement: 命令结果卡片账号展示必须昵称优先

Feishu 命令结果卡片包含相关账号时，可见账号行 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于结果卡文案，命令解析、调度、发布 / 评论归属、审计和日志 MUST 继续使用真实 `accountId`。

#### Scenario: 参照创作失败结果卡展示昵称

- **WHEN** 精选内容池对账号 `acc-1` 触发参照创作，且账号 `acc-1` 的昵称为 `工程师大白`
- **AND** 参照创作编排失败并发送异步 Feishu 结果卡
- **THEN** 结果卡的账号行 SHALL 展示 `工程师大白`
- **AND** 结果卡标题、红黄绿 honest-status 判级和失败原因 MUST 保持真实终态语义

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 任何命令或异步任务结果卡关联账号 `acc-2`，但该账号没有可用昵称
- **THEN** 结果卡的账号行 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或把缺失昵称显示成成功状态

### Requirement: 账号影响类命令只在管理群受理，外部群纯通知投递

**管理群**由独立显式配置的白名单（env `FEISHU_MANAGEMENT_CHAT_IDS`，逗号分隔）界定。当白名单**非空**时，系统 SHALL 只在白名单会话中受理**任何非帮助类命令**（`/publish`、`/comment`、`/pause`、`/resume`、`/status`、`/bind` 等）；从**外部群**（客户所在的对外共享群）或任何非白名单群下达的此类命令，系统 MUST NOT 执行，SHALL 以诚实回执说明该群无权下达命令。外部客户群按定义**纯做通知投递**：外部成员即便能 @ 机器人，也 MUST NOT 借此驱动任何账号动作。当白名单**为空**（未启用作用域）时，系统 SHALL 放行全部命令（零回归上线 ramp：先零变更部署，待就绪再显式设白名单收紧）。`/help` 在任何群 SHALL 放行。

#### Scenario: 外部群命令被诚实拒绝（作用域已启用）

- **WHEN** 已配置管理群白名单，且某外部客户群里的成员向机器人发送 `/publish <昵称>` 或 `/pause <账号>`
- **THEN** 系统 MUST NOT 执行该命令
- **AND** SHALL 回一条诚实说明「本群无权下达账号命令」的回执，MUST NOT 静默无响应地假装受理

#### Scenario: 管理群命令照常受理

- **WHEN** 在白名单管理群里下达 `/comment <昵称>`
- **THEN** 系统 SHALL 照常解析、执行并回执（结果卡回本管理群）

#### Scenario: 未配置白名单时零回归放行

- **WHEN** `FEISHU_MANAGEMENT_CHAT_IDS` 未配置（白名单为空）
- **THEN** 命令在任何群 SHALL 与本变更前一致地照常受理（零回归），系统 SHALL 记录一条「作用域未启用」日志

### Requirement: /bind 不授予全局默认或管理语义

`/bind` MUST NOT 使任意群获得全局默认群或管理群权限。管理群 / 默认投递群的指定 SHALL 是一项**独立的显式配置**（面板路由或独立标志位），MUST NOT 可被任意用户在自己所在群自助 `/bind` 而获得。据此，任何人在任意群下 `/bind` 都 MUST NOT 借此把 ops / 告警 / 兜底流量或账号命令权引到自己群。

#### Scenario: 自助 /bind 无法提权为管理群

- **WHEN** 某用户在一个未被授权的群里发送 `/bind`
- **THEN** 该群 MUST NOT 因此获得管理群或全局默认群语义
- **AND** 账号影响类命令在该群仍被拒

### Requirement: 作用域闸在命令入口生效，显式 accountId / 短路路径不得绕过

作用域校验 SHALL 在**命令入口**（解析后、派发到任何执行动作前）对**所有**非帮助类命令统一生效，与账号如何指定无关——无论显式 accountId、按昵称、还是单账号 / 空昵称便捷短路。据此，带显式 accountId 的 `/status`、`/pause`、`/resume` 与单账号短路 MUST NOT 因账号已在参数中给出而绕过作用域；非授权群一律诚实拒。入口闸判定 MUST 与账号命令解析解耦（先判权限、后解析账号），杜绝"解析出账号再放行"的漏判。

#### Scenario: 非管理群带显式 accountId 仍被拦

- **WHEN** 从非管理群下达 `/pause acc-1`（显式 accountId）
- **THEN** 系统 SHALL 校验来源群无权管理 `acc-1` 并诚实拒绝
- **AND** MUST NOT 因 accountId 显式给出而绕过作用域执行

#### Scenario: 单账号短路路径也过作用域

- **WHEN** 从非管理群下达无参 `/status`（依赖单账号短路解析）
- **THEN** 该短路解析 MUST 同样受来源群作用域约束，非管理群一律诚实拒

### Requirement: Feishu 自然语言委托必须解析为昵称唯一绑定的确认卡

Feishu 管理群 SHALL 接受 Phase 1 可确定解析的自然语言委托，并要求可读账号昵称；系统 MUST 以昵称精确唯一解析真实账号，展示账号昵称、平台、动作、数量、尝试上限、时间、约束、人审和优先级的确认卡。昵称缺失、找不到或重名 MUST 澄清，MUST NOT 接收裸 accountId 作为面向用户的替代。

#### Scenario: 昵称唯一解析后展示确认卡
- **WHEN** 管理群输入“让小萝北今晚前完成 5 条有效评论，最多尝试 8 次”且昵称唯一
- **THEN** 系统返回结构化 `awaiting_confirmation` 卡片
- **AND** 点击确认前不得执行评论

#### Scenario: 昵称重名时不猜账号
- **WHEN** 两个账号昵称都为“小萝北”
- **THEN** 系统要求用户消除重名或提供可读区分
- **AND** MUST NOT 任意选择一个 accountId

### Requirement: 旧 slash command 语法保持兼容；写命令直接排队、自然语言仍先确认

现有 `/publish`、`/comment`、`/status`、`/pause`、`/resume` 等命令 SHALL 保持语法兼容；只读命令可原路执行。`/publish` 与 `/comment` 等写命令 MUST 仍创建目标数为 1 的单次 DelegatedTask；因为账号昵称与目标已在命令中**显式给定、无可推断歧义**，系统 SHALL 直接确认并入队（`awaiting_confirmation → queued`），MUST NOT 再向用户展示结构化确认卡。自然语言委托（`source=feishu`）因账号 / 数量 / 截止 / 尝试均为**推断**，MUST 仍先展示结构化确认卡、明确确认后才入队。

直接排队 MUST NOT 削弱下游人审：`/publish`、`/comment` 单次任务保留 `review` 审批模式，逐篇内容 / 评论人审在任何平台写动作前仍然触发。昵称重名或找不到 MUST fail-closed 拒绝，MUST NOT 直接排队到任意账号或静默改选。确认后的单次任务 MAY 保留既有人工额度语义，但该语义 MUST NOT 被批量 / 异步任务继承。

#### Scenario: 旧 slash 写命令直接排队、不出确认卡

- **WHEN** 用户发送 `/publish <昵称>` 或 `/comment <昵称>`，且昵称唯一可解析
- **THEN** 路由器创建目标数为 1 的单次 DelegatedTask 并直接确认入队（状态 `queued`），MUST NOT 展示结构化确认卡
- **AND** 回执为该任务的进度卡（已直接排队），该兼容语法 MUST NOT 被解释为 N 条批量任务
- **AND** 逐篇内容 / 评论人审在平台写动作前仍然触发（`review` 审批模式不变）

#### Scenario: 昵称歧义仍 fail-closed

- **WHEN** `/publish <昵称>` 或 `/comment <昵称>` 的昵称重名或找不到
- **THEN** 系统诚实拒绝并要求澄清，MUST NOT 直接排队到任意账号

#### Scenario: 自然语言委托仍先确认

- **WHEN** 用户发送自然语言业务目标（如「让 <昵称> 发布一篇稿件」「今晚前完成 3 条评论」）
- **THEN** 系统 MUST 仍先展示结构化确认卡，明确确认后才入队

### Requirement: 分号批命令必须逐段独立受理与回报

Feishu 命令入口 SHALL 接受有界数量的、由 ASCII 分号 `;` 或全角分号 `；` 分隔的已支持 slash 命令。分隔符只有在其后出现已识别的 slash 命令 token 时才构成命令边界；系统 MUST NOT 把 URL、昵称或普通参数中的分号盲目切开。

每个子命令 SHALL 独立完成作用域校验、解析、账号绑定、幂等与入队，且 SHALL 并发进入准备阶段而非按文本顺序串行等待。一个子命令无效 MUST NOT 阻止其它有效子命令入队；每个子命令的拒绝或后续业务结果 SHALL 独立、诚实回报。入口 fast-ack、不发送“已完成”式中间卡、发布/评论真实终态口径均保持不变。

#### Scenario: 发布与评论从同一消息独立入队

- **WHEN** 管理群发送 `/publish Tianxing Bai; /comment Tianxing Bai --join --contact --force`
- **THEN** 系统 SHALL 创建一个发帖任务和一个加群评论任务，而不是把分号后文本并入发帖昵称
- **AND** 两个任务 SHALL 独立进入准备阶段
- **AND** 评论任务 SHALL 同时携带 `joinGroup=true`、`injectContact=true` 与 `force=true`

#### Scenario: 一个子命令无效不吞掉有效兄弟

- **WHEN** 一个批消息中一个子命令合法、另一个子命令因昵称不存在而被拒
- **THEN** 合法子命令 SHALL 正常入队
- **AND** 无效子命令 SHALL 独立回报真实拒绝原因
- **AND** 系统 MUST NOT 把整批伪装成全部成功或全部失败

#### Scenario: 批命令仍然 fast-ack 且不发启动成功卡

- **WHEN** 一条批消息包含两个长耗时写命令
- **THEN** Feishu 事件处理器 SHALL 在受理后立即回帧，MUST NOT 等两个命令执行完成
- **AND** 精确写命令入队阶段 MUST NOT 发送暗示已经发布或评论完成的中间卡
- **AND** 后续审批卡、评论结果卡与发布结果 SHALL 仍按各自真实业务状态独立送达

#### Scenario: 重放按子命令稳定去重但同批重复命令保持独立

- **WHEN** Feishu 重放同一个 message id 的批消息
- **THEN** 每个原子子命令 SHALL 以稳定的 message-id 加子命令序号进行幂等，不产生重放副本
- **AND** 同一原始批消息中由不同序号表达的两条相同命令 SHALL 仍被视为两个显式子命令

#### Scenario: 参数内分号不被误切

- **WHEN** 昵称或 `--join=<url>` 参数中包含分号，但分号后不是已支持的 slash 命令 token
- **THEN** 该分号 SHALL 保留在当前命令参数中
- **AND** 系统 MUST NOT 因简单字符串切分创建伪命令

### Requirement: 飞书账号名称解析复用统一账号显示名目录

飞书 `/publish`、`/comment`、委托任务及其它按人类名称选账号的入口 SHALL 从 Cloud 账号显示名目录取得候选。输入 MAY 精确匹配运营别名、平台昵称或非空运营标签；候选清单与成功回执 SHALL 使用统一解析后的首选显示名。账号 ID MUST NOT 作为昵称输入的隐式匹配项；多账号命中时 MUST fail closed。

#### Scenario: 使用运营别名选择账号
- **WHEN** 操作者在飞书命令中输入某账号唯一的运营别名
- **THEN** 系统解析到该账号 ID，机器任务按 ID 创建，回执显示统一运营别名

#### Scenario: 旧平台昵称仍可选择
- **WHEN** 账号已有运营别名但操作者输入该账号唯一的平台真实昵称
- **THEN** 系统仍可解析到相同账号 ID，回执显示当前统一首选名

#### Scenario: 名称重名拒绝猜测
- **WHEN** 输入名称匹配多个账号的运营别名、平台昵称或运营标签
- **THEN** 系统拒绝执行并返回去重提示，MUST NOT 按列表顺序猜账号

