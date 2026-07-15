# comment-search-command Specification

## Purpose
TBD - created by archiving change comment-search-command. Update Purpose after archive.
## Requirements
### Requirement: 飞书 /comment 命令触发按需评论任务

系统 SHALL 新增飞书聊天命令 `/comment <昵称>`：仿 `/publish` 解析与路由，按昵称定位**唯一真实账号**（沿用既有昵称匹配，0 个/多义时 honest-fail 并列出可选昵称），并触发一次按需评论任务。命令 MUST 两段式回执——同步先回「已触发」或失败原因；评论经人审发出后再补结果。命令 MUST NOT 在未解析到明确账号时回落到 `default` 或任意账号。

#### Scenario: 命令定位到唯一账号并触发
- **WHEN** 运营在飞书发送 `/comment <昵称>` 且该昵称唯一匹配一个真实账号
- **THEN** 启动该账号的按需评论任务，并同步回「已触发」回执

#### Scenario: 昵称无匹配或多义 → 诚实失败
- **WHEN** 昵称匹配 0 个或多个账号
- **THEN** MUST 回失败回执并列出可选昵称，MUST NOT 盲选账号、MUST NOT 回落 `default`

#### Scenario: 账号边端离线 → 诚实失败
- **WHEN** 解析到的账号当前无在线边端连接
- **THEN** MUST 回「边端离线」失败回执，MUST NOT 假装任务已在跑

#### Scenario: 红线反例——未解析到账号仍盲跑（禁止）
- **WHEN** 有实现在昵称缺省/无匹配时回落默认账号或随机账号执行评论
- **THEN** MUST 视为违规、不予合入；账号 MUST 由命令显式解析、honest-fail 而非回落

### Requirement: 按需评论任务为受控、独占边端的一次性流程

按需评论任务 SHALL 为一条有方向的一次性流程（仿发布任务），MUST 在发起任何搜索/开笔记/评论命令前**独占该账号边端**——先结束其自动浏览会话（标记不可恢复），任务结束后于 `finally` 恢复浏览。任务 MUST 按账号串行（同账号已有发布接管或另一评论任务时排队、不并发抢边端）。任务 MUST NOT 把命令意图注入正在运行的自治浏览会话。

**该独占 MUST 覆盖「选中候选 → 打开详情 → 撰写 → 飞书人审 → 发布」整段**：一旦选中一篇候选，系统 MUST 在**同一个持续持有的边端租约**内打开该笔记并保持在其详情页，**贯穿人审等待窗口不释放边端**，直至发布或诚实终止。此整段独占对**命令触发（人工 `/comment`）与自动排期触发（`priority='automatic'`）两条路径同等生效**；租约时长 MUST 覆盖搜索+撰写+人审超时+发布的最坏耗时。审批期间边端 MUST 停留在目标详情页、MUST NOT 被自治浏览闭环夺走或导航离开。

#### Scenario: 接管边端后跑流程、结束后恢复浏览
- **WHEN** 评论任务启动
- **THEN** MUST 先结束该账号自动浏览会话独占边端，跑完（成功/失败）后 MUST 恢复浏览会话

#### Scenario: 选中候选后持锁贯穿人审、审批期停在详情页
- **WHEN** 某搜索词选中一篇合格候选并打开其详情页
- **THEN** MUST 在同一持有租约内保持该详情页贯穿撰写与飞书人审等待，MUST NOT 在人审窗口释放边端使自治浏览闭环夺走浏览器并导航离开

#### Scenario: 同账号已有占用 → 串行排队
- **WHEN** 同账号已有发布接管或另一评论任务在执行
- **THEN** 新评论任务 MUST 串行等待、MUST NOT 与之并发占用同一边端

#### Scenario: 红线反例——不接管边端就下发命令（禁止）
- **WHEN** 有实现不结束自治浏览会话即下发搜索/评论命令，使其与自治浏览命令在同一边端命令队列交错
- **THEN** MUST 视为违规、不予合入；命令路径 MUST 独占边端后再下发

#### Scenario: 红线反例——人审期间释放边端后靠复搜找回（禁止）
- **WHEN** 有实现在人审窗口释放边端、发布前靠重新搜索关键词找回目标笔记
- **THEN** MUST 视为违规、不予合入；发布前定位 MUST 靠持锁保留的当前详情页，MUST NOT 依赖脆弱的关键词复搜

### Requirement: 当前笔记触发的自动联系评论复用当前上下文

当自动联系评论由自治浏览中的当前笔记触发（例如热帖引流线索在 `note.detail.arrived` 后经 `quality.pass` 命中）时，系统 SHALL 复用该当前 `note.detail` 上下文直接进入撰写/人审/发布流程，MUST NOT 再按标题搜索定位，MUST NOT 在当前上下文不可用时评论搜索到的相似笔记。该路径 MAY best-effort 继续采集当前详情页现场评论；采集失败不等于搜索兜底。后台或外部指定的非当前目标 MAY 继续使用标题搜索定位，但仍必须精确匹配目标 `noteId`。

自动联系评论的共用 comment 风险配额 SHALL 只在最终执行结果确认为 `commented` 后消费；任务触发成功但最终 `note_not_found`、`read_failed`、`compose_skipped`、`post_failed` 或其他未产出状态 MUST NOT 消费 comment 配额。联系评论尝试审计/子上限 MAY 在触发成功时记录，用于避免反复推审。

#### Scenario: 当前笔记触发 → 不搜索，直接评论当前笔记
- **WHEN** 热帖线索由当前笔记 `noteId=N` 的 `note.detail` 与质量通过事件触发
- **THEN** 任务 MUST 使用该 `note.detail` 作为评论目标，MUST NOT 下发 `search.execute` 或按标题搜索
- **AND** 评论发布目标 MUST 仍为 `noteId=N`

#### Scenario: 当前详情错配或丢失 → 不搜索兜底
- **WHEN** 当前详情 `noteId` 与目标 `noteId` 不一致，或当前笔记上下文不可用
- **THEN** 任务 MUST 诚实失败/未产出，MUST NOT 改按标题搜索并评论相似结果

#### Scenario: 未产出不消费 comment 风险配额
- **WHEN** 自动联系评论已触发但最终没有 `commented`
- **THEN** MUST NOT 记录共用 comment 风险配额消耗，但 MAY 记录一次联系评论尝试审计

#### Scenario: 外部指定目标仍可搜索但必须精确命中
- **WHEN** 后台/飞书入口只提供目标 noteId/title 且没有当前详情上下文
- **THEN** MAY 使用标题搜索定位；搜索结果中没有精确目标 noteId 时 MUST 不评相似笔记

### Requirement: 搜索词生成角色——人设 + 精选集，稀疏退回种子词

系统 SHALL 新增一个独立角色，从账号**人设兴趣** + **精选集**（`curated_content` 高收藏笔记标题/主题，按账号）生成一小批**有序**搜索词（供甄选不中时**逐个换词重试**）。精选集稀疏/为空时 MUST 退回人设种子词（`seed_keywords`），MUST NOT 编造与账号领域无关或凭空臆造的词。LLM 降级/解析失败时 MUST 诚实少出或退回种子词，MUST NOT 阻塞任务。

#### Scenario: 精选集有素材 → 生成贴合领域的搜索词
- **WHEN** 该账号精选集存在高收藏笔记
- **THEN** 角色据人设领域 + 精选标题/主题产出若干贴合该账号领域的搜索词

#### Scenario: 精选集为空 → 退回种子词
- **WHEN** 该账号精选集为空或过稀疏
- **THEN** 角色 MUST 基于人设 `seed_keywords` 产词，MUST NOT 编造占位词

#### Scenario: 红线反例——臆造离题搜索词（禁止）
- **WHEN** 有实现在无可用素材时填充与账号领域无关的占位/臆造词
- **THEN** MUST 视为违规、不予合入；无素材时 MUST 退回种子词或诚实少出

### Requirement: 搜索结果按平台原生「最多收藏」排序 +「一天内」时间窗筛选获取

命令路径的搜索 SHALL 在边端**驱动小红书搜索页原生「最多收藏」排序 +「一天内」时间筛选**控件后再采结果卡片。协议增量（搜索指令的排序/时间参数、结果卡片的收藏数字段）MUST 按 v2 四处原子同步（两份 `protocol.ts` 逐字一致 + `command-bridge` 映射 + `docs/protocol.md` 计数与表 + 必要时 edge 主动命令路由白名单），两份 `protocol-contract.test.ts` 计数断言同步。筛选控件定位失败时 MUST 诚实回报筛选未生效/降级，MUST NOT 把「综合/无时间窗」结果冒充为「最近一天最多收藏」。当平台搜索结果卡片真实暴露收藏数时，边端 SHALL 回传该真实 `collectCount`；当卡片不暴露收藏数时，边端 MUST NOT 用点赞数、评论数或推测值伪造收藏数，云端 SHALL 以原生「最多收藏」排序后的结果顺序作为主要排序事实。

#### Scenario: 驱动原生排序与时间窗后采卡
- **WHEN** 命令路径在搜索结果页执行
- **THEN** MUST 先切到排序=最多收藏、时间=一天内，再采结果卡片

#### Scenario: 卡片暴露收藏数时回传真实收藏数
- **WHEN** 采集搜索结果卡片且平台卡片 DOM 真实暴露收藏数
- **THEN** 每卡 MUST 带回真实收藏数，供云端在相关候选里择最多收藏

#### Scenario: 卡片不暴露收藏数时不伪造
- **WHEN** 搜索结果卡片只暴露点赞数等其它计数而不暴露收藏数
- **THEN** 边端 MUST NOT 将其它计数填成 `collectCount`
- **AND** 云端 SHALL 以原生「最多收藏」排序后的卡片顺序作为主要排序事实

#### Scenario: 协议两端不漂移
- **WHEN** 新增搜索排序/时间参数与卡片收藏数字段后运行 `npm run typecheck` 与 `npm run test:acceptance`
- **THEN** `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 计数断言 MUST 全过；任一处漏改 MUST 使构建失败

#### Scenario: 红线反例——筛选未生效却冒充已筛（禁止）
- **WHEN** 原生排序/时间控件定位失败，但实现照常把未筛选结果当作「最近一天最多收藏」继续
- **THEN** MUST 视为违规、不予合入；筛选未生效 MUST honest 报降级、不冒充

### Requirement: 候选去重后强相关择优；不中则换搜索词重试、用尽诚实结束

对每个搜索词的结果卡片，系统 MUST **先**滤掉本账号**已评论过**的笔记（复用每笔记已交互去重，`action='comment'`，按账号），**再**由甄选角色判定**人设强相关**——只有与账号领域**强相关**（不是沾边/泛泛相关）且未评过的笔记才算合格候选；在合格候选里挑**收藏最高的一篇**。去重 MUST 在甄选之前。当前搜索词无合格候选时，系统 MUST **换下一个搜索词重试**（重跑搜索→原生筛选→去重→甄选）；**首个命中即止**、不再尝试余下搜索词。

**「换下一个搜索词」MUST 仅在「当前搜索词搜不到合格候选」（搜索未到结果页/空结果、或去重后无候选、或甄选判定无强相关）时触发。一旦选中一篇候选，系统 MUST 提交到该篇：MUST NOT 为已选中的笔记重新搜索，也 MUST NOT 因该篇后续读正文/人审/发布失败而回退去搜索或评论另一篇。** 系统 MUST 设尝试上限并受搜索限频/预算约束（不无限换词）；所有搜索词试完或达尝试上限仍无合格候选时 MUST 诚实结束任务、本次不评，MUST NOT 强行评一篇弱相关或已评过的笔记。每次任务最多评一篇。

**操作员覆盖例外（`--force`，change manual-comment-force-flag）**：仅当飞书手动命令带 `--force` 时，本条的两处「软筛选」被显式放开——(a) 甄选前的**去重过滤**被跳过（已评过的笔记仍参与候选）；(b) 当某搜索词**无强相关候选**时，系统 MAY **不换词**而在该词的全体候选里选**收藏最高的一篇**作为目标继续（兜底），而非本次不评。`--force` 仅由手动命令入口置位，自动/排期路径绝不带、行为不变。`--force` 覆盖的**只有**相关性与去重两处软筛选：仍 MUST 保留飞书人审、边端诚实闸（含发布前就地核对 noteId）、账号隔离；发布成功后 MUST 照常记每笔记去重（供后续任务参考）。注：`--force` 只影响「哪些卡片可被选中」；一旦选中，本条 keep-open 的「提交到该篇、不复搜不换篇、后续失败即诚实结束」仍照常适用。

#### Scenario: 去重在择优之前
- **WHEN** 某搜索词的候选含本账号此前已评论过的笔记
- **THEN** 这些笔记 MUST 在交甄选角色之前被滤掉，不参与择优、不耗模型判定

#### Scenario: 强相关候选里挑收藏最高的一篇
- **WHEN** 去重后某搜索词仍有与账号领域强相关的候选
- **THEN** 甄选角色 MUST 在强相关候选里挑收藏最高的一篇作为评论目标，并停止尝试余下搜索词

#### Scenario: 当前搜索词无强相关候选 → 换下一个搜索词
- **WHEN** 当前搜索词的候选全被去重、或甄选判定无一强相关（仅弱相关/不相关）
- **THEN** 系统 MUST 换下一个搜索词重试，MUST NOT 在弱相关候选里凑一篇评论

#### Scenario: 已选中的笔记后续失败 → 结束、不换词不找下一篇
- **WHEN** 已选中一篇候选，但其读正文、人审或发布未成功（含人审超时/被拒、发布前就地核对不过）
- **THEN** 系统 MUST 诚实结束本次任务，MUST NOT 为该篇重搜、MUST NOT 改评另一篇或换下一个搜索词

#### Scenario: 搜索词用尽/达尝试上限 → 诚实结束
- **WHEN** 所有生成的搜索词都试过、或达到尝试上限，仍无强相关合格候选
- **THEN** MUST 诚实结束任务并回执本次未评，MUST NOT 强评弱相关/已评过的笔记

#### Scenario: 红线反例——弱相关凑数或无限换词（禁止）
- **WHEN** 有实现（**在无 `--force` 的默认/自动路径上**）跳过去重、或在无强相关候选时挑一篇弱相关/沾边的笔记评论、或不设上限无限换词搜索
- **THEN** MUST 视为违规、不予合入；默认路径 MUST 先去重、只评强相关候选、且换词重试 MUST 有上限并受限频/预算约束

#### Scenario: 操作员 `--force` 覆盖——无强相关时兜底选收藏最高的一篇
- **WHEN** 操作员运行 `/comment <账号> --force`，某搜索词去重后仍有候选但甄选判定无一强相关
- **THEN** 系统 MAY 在该词全体候选里选**收藏最高的一篇**继续开帖→撰写→人审→发布，而非换词/本次不评；此兜底**仅**在带 `--force` 的手动命令路径生效，仍 MUST 经飞书人审

#### Scenario: 操作员 `--force` 覆盖——放开去重、允许再评已评过的笔记
- **WHEN** 操作员运行 `/comment <账号> --force`，候选里包含本账号已评过的笔记
- **THEN** 甄选前的去重过滤与发布前的去重复检 MUST 被跳过（该笔记仍可被选中并再评一条）；发布成功后仍 MUST 记一笔去重

### Requirement: 评论生成复用既有撰写链并接入现场评论

命令路径的评论生成 SHALL 复用既有「撰写→去AI味」链，且撰写 MUST 以**笔记正文 + 现场评论 + 人设 + 精选参考**为输入产出一条贴合语境的评论（撰写角色由现状的「仅标题+正文+精选参考」**扩展为同时读现场评论**）。现场评论采集复用既有评论区采集。撰写失败/产空/超长 MUST 诚实跳过，MUST NOT 回退模板/占位文本照发。

#### Scenario: 撰写吃正文与现场评论
- **WHEN** 目标笔记已打开且现场评论已采集
- **THEN** 撰写 MUST 以正文 + 现场评论 + 人设 + 精选参考为输入，产一条贴合该笔记语境的评论

#### Scenario: 去AI味复用既有确定性步骤
- **WHEN** 撰写产出草稿
- **THEN** MUST 复用既有去 AI 味/反抄袭步骤，无新 LLM、不抛异常

#### Scenario: 红线反例——撰写失败伪造文本（禁止）
- **WHEN** 撰写 LLM 失败或产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST 诚实跳过，绝不发伪造评论

### Requirement: 命令评论跳过自动硬阈值、不计入风控配额，但保留人审

命令路径发起的评论 SHALL **跳过**自治评论支线的硬数值阈值（赞>1000 且 藏>300）与「是否值得」自动判定（用户已手动指定意图、相关性由甄选角色把关）。命令路径的评论为**人工授权**动作，与 `/publish` 越过风控同理：MUST NOT 计入风控按账号按天评论配额、MUST NOT 因此消耗自治评论预算或推动风控状态机（不经 `canDo('comment')` 门控阻断）。但 MUST **保留飞书人工审核闸**（未授权/超时一律不发）。命令路径 MUST 仍记**每笔记去重**（`risk_interactions`，避免重复评同一篇），且评论的去重记账 MUST 仅在执行端真回执 `ok:true` 时发生。

**`--force` 覆盖例外（change manual-comment-force-flag）**：带 `--force` 的手动命令 MAY 跳过**发起前**的去重过滤（允许对已评过的笔记再评一条）；但去重**记账**行为不变——发布成功（`ok:true`）后仍 MUST 记一笔「已评论」。`--force` 不改变本条其余语义（仍跳过硬阈值、仍不计入风控配额、仍保留人审）。

> 取舍说明（用户决策）：不计入风控配额意味着真实评论速率（自治 + 手动）可能超过配置的安全配额；因 `/comment` 是运营**刻意触发**的人工动作，该速率由运营负责，故不纳入 bot 的自治安全预算（与 `/publish` 一致）。`--force` 进一步允许再评已评过的目标，属同类人工授权取舍——由运营负责。

#### Scenario: 命令路径不受自动硬阈值阻挡
- **WHEN** 命令选中的笔记 `likeCount ≤ 1000` 或 `collectCount ≤ 300`
- **THEN** 命令路径 MUST 仍可对其评论（不被自治支线的硬数值阈值拦），相关性由甄选角色保证

#### Scenario: 仍走人工审核
- **WHEN** 命令路径产出评论草稿（含带 `--force` 的手动命令）
- **THEN** MUST 经飞书人审授权后才下发评论命令；未授权/超时 MUST 不发、诚实跳过

#### Scenario: 不计入风控配额（人工授权）
- **WHEN** 命令路径的评论真发出（执行端回执 `ok:true`）
- **THEN** MUST NOT 计入风控按账号按天评论配额、MUST NOT 推动风控状态机（与自治评论预算隔离）；但 MUST 记每笔记去重（`risk_interactions`）供下次任务避开，且 MUST NOT 影响展示账本之外的安全终态

#### Scenario: `--force` 允许再评但仍记账
- **WHEN** 操作员运行 `/comment <账号> --force` 对一篇已评过的笔记再评并真发成功（`ok:true`）
- **THEN** 发起前的去重过滤 MUST 被跳过（允许再评），但发布成功后仍 MUST 记一笔去重；`--force` MUST NOT 改变「不计入风控配额、保留人审」的其余语义

#### Scenario: 红线反例——命令路径绕人审自动直发（禁止）
- **WHEN** 有实现让命令路径（含 `--force`）无人审自动直发评论
- **THEN** MUST 视为违规、不予合入；命令路径 MUST 保留飞书人审（未授权绝不发）

#### Scenario: 红线反例——把手动评论计入自治风控配额（禁止本 change 决策的回退）
- **WHEN** 有实现把命令路径的评论计入风控按天评论配额 / 经 `canDo('comment')` 阻断
- **THEN** MUST 视为违背用户决策、不予合入；手动评论 MUST 与自治评论预算隔离（人工授权）

### Requirement: 两个新角色登记进角色目录、后台可配模型

两个新角色（搜索词生成、搜索笔记甄选）SHALL 登记进云端角色目录（判定类），使其在后台「角色管理」自动出现并可配模型/温度。角色 MUST NOT 因未登记目录而在运行时回落到全局默认模型（须按判定类解析）。角色 `roleName` 与目录键（去 `browse:` 前缀后）MUST 逐字一致。

#### Scenario: 登记后后台可配
- **WHEN** 两新角色登记进角色目录
- **THEN** 后台「角色管理」MUST 自动列出二者并可单独配模型/温度，无需改前端

#### Scenario: 红线反例——漏登记目录致回落默认模型（禁止）
- **WHEN** 有实现新增角色但未登记进角色目录，运行时按全局默认模型解析
- **THEN** MUST 视为违规、不予合入；角色 MUST 登记进目录、按判定类配置解析

### Requirement: 账号隔离、发布后记账去重、诚实贯穿

任务全程 SHALL 严格按命令解析到的账号读写——人设、精选集、去重、落评论、落精选 MUST NOT 跨账号（PII 红线）。评论发布成功（真回执 `ok:true`）后 MUST 记一笔「已评论」（写入每笔记去重，供下次任务避开）；被评论的笔记正文/现场评论 MAY 写入精选集（复用既有捕获路径）。任一步（搜索、筛选、开笔记、撰写、发布）失败 MUST honest-fail，MUST NOT 静默假成功。

#### Scenario: 全程按账号隔离
- **WHEN** 任务读人设/精选集/去重并落评论
- **THEN** MUST 全部限定为命令解析到的账号，MUST NOT 读写其他账号数据

#### Scenario: 发布成功后记账供去重
- **WHEN** 评论命令真回执 `ok:true`
- **THEN** MUST 记一笔该笔记「已评论」（按账号），使后续任务对其去重

#### Scenario: 红线反例——跨账号读或静默假成功（禁止）
- **WHEN** 有实现跨账号读精选/去重，或在某步失败时静默当作成功继续
- **THEN** MUST 视为违规、不予合入；MUST 账号隔离 + 全程 honest-fail

### Requirement: 搜索采卡前 MUST 确认已到达搜索结果页，未到诚实回失败且不得把 feed 当结果

命令评论的搜索在采集/上报结果卡片之前，边端 MUST 以**实时页面 URL** 确认当前已处于搜索结果页（小红书 `search_result` / `search_result_ai` 一类结果页 URL）。当导航未确认到达结果页时（回车未提交、提交兜底失败、仍停在首页 feed 或其它页），边端 MUST NOT 采集/上报当前页卡片、MUST NOT 把首页 feed 当作搜索结果上报，且 MUST 跳过对错误页的原生筛选重试；边端 MUST 发一条诚实的搜索失败回执 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`。到达确认 MUST 以采卡时刻的实时 URL 为准，MUST NOT 仅凭一个可能滞后的「已导航」布尔与 URL 取 AND（避免把「其实已到结果页但确认稍慢」误杀成不上报）。此判定 MUST 仅作用于命令/搜索采卡路径，MUST NOT 影响自治浏览对首页 feed 的合法卡片上报。

#### Scenario: 未导航到结果页 → 不报卡 + 诚实回失败
- **WHEN** 边端执行搜索后实时 URL 仍非搜索结果页（如停在 `/explore` 首页 feed）
- **THEN** MUST NOT 上报任何卡片、MUST NOT 把当前 feed 卡当搜索结果
- **AND** MUST 发 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`
- **AND** MUST 跳过对该错误页的原生筛选重试

#### Scenario: 已到达结果页 → 照常采卡
- **WHEN** 边端执行搜索后实时 URL 已是搜索结果页
- **THEN** MUST 照常应用原生排序/时间筛选并采集、上报结果卡片

#### Scenario: 搜索执行抛错 → 走失败分支，不 fall through
- **WHEN** 搜索执行过程抛出异常
- **THEN** MUST 视为未到达结果页、走诚实失败回执分支，MUST NOT fall through 去上报当前页卡片

#### Scenario: 红线反例——把 feed 当搜索结果上报（禁止）
- **WHEN** 有实现在导航未确认时照常 `reportVisibleCards` 把首页 feed 卡当搜索结果上报
- **THEN** MUST 视为违规、不予合入；这会让云端选中与搜索词无关的幻影候选（静默假成功红线）

### Requirement: 云端 MUST 消费搜索导航失败回执并真实归因失败原因

云端命令评论的搜索步在等待结果时 MUST 同时监听结果卡片到达与搜索失败回执（竞速 `page.cards.arrived` 与 `action.completed{action:'search'}`）；收到 `ok:false` 时 MUST 立即以空候选快速失败，MUST NOT 干等满单步超时（消除多搜索词各等一遍超时的空转）。云端对「搜索未导航到结果页」MUST 用**独立、真实**的结论呈现，MUST NOT 沿用「（超时/边端离线）」措辞、MUST NOT 折叠进「无匹配笔记 / 无强相关候选」（那会把导航失败误报成内容缺失）。此外，命令评论的 `read_failed` 回执 MUST 携带真实失败原因（对齐 `post_failed` 的 reason 呈现），MUST NOT 一律硬编码「（边端超时或离线）」——边端在线的诚实失败绝不误报成离线。

#### Scenario: 收到搜索失败回执 → 快速失败 + 真实归因
- **WHEN** 云端搜索步收到 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`
- **THEN** MUST 立即以空候选返回、不等满单步超时
- **AND** 回执/日志 MUST 呈现「搜索未导航到结果页」的真实结论，MUST NOT 说「超时/边端离线」，MUST NOT 说「无匹配笔记」

#### Scenario: read_failed 回执带真实原因
- **WHEN** 命令评论以 `read_failed` 结束且结果带有 reason（如复检目标不可用）
- **THEN** 回执 MUST 呈现该真实 reason，MUST NOT 一律硬编码「（边端超时或离线）」

#### Scenario: 红线反例——把在线诚实失败误标为离线（禁止）
- **WHEN** 边端在线且诚实回报了搜索/开笔记失败，但云端把它对运营呈现为「边端超时或离线」
- **THEN** MUST 视为违规、不予合入（假归因红线）；MUST 区分「未导航到结果页 / 无结果 / 真离线」并如实呈现

### Requirement: 发布前就地重读当前详情页 noteId 核对，替代复搜新鲜度

发布评论前，系统 SHALL 保留「commit 不信旧 DOM」的新鲜度不变量，但 MUST 通过**就地重读当前所停详情页的 `noteId` 并与目标 `noteId` 核对**来满足它，MUST NOT 通过重新搜索关键词。该核对 MUST 在真正提交评论前于执行端完成：当前详情页 `noteId` 与目标一致才提交；不一致（页面被弹层顶掉/被导航离开/笔记已删或改）MUST 诚实终止、回可辨识失败原因，MUST NOT 提交评论。核对 MUST NOT 触发任何搜索或重新打开动作。

#### Scenario: 发前就地核对一致 → 提交
- **WHEN** 撰写已人审通过、准备发布，且当前详情页 `noteId` 等于目标 `noteId`
- **THEN** MUST 直接在该页提交评论，MUST NOT 重新搜索或重新打开

#### Scenario: 发前就地核对不一致 → 诚实终止不发
- **WHEN** 发布前读到当前详情页 `noteId` 与目标不一致，或读不到当前笔记标识
- **THEN** MUST NOT 提交评论，MUST 诚实回失败（页面被动过/目标已不在），MUST NOT 改在当前错误页面上发评论

#### Scenario: 红线反例——不核对当前页 noteId 盲发（禁止）
- **WHEN** 有实现在发布前不校验当前详情页 `noteId` 即提交评论
- **THEN** MUST 视为违规、不予合入；提交前 MUST 就地核对 `noteId` 一致

### Requirement: 发现搜索确认到达结果页须严格且关键词一致

命令/自动路径的发现搜索 MUST 以**严格的搜索结果页判据**确认已到达结果页，且该判据 MUST 与边端上报卡片时的权威判据（`SEARCH_LIST_RE`，按 URL 路径段而非任意子串）一致。边端确认导航时 MUST 额外要求 **URL 相对本次搜索起点发生变化**，并 MUST **核对结果页 URL 的关键词参数等于本次要搜的词**；任一不满足 MUST 判为未到达结果页、诚实回失败，MUST NOT 把停留在上一次搜索（不同关键词）的旧结果页当作本次搜索成功、MUST NOT 采其卡片。当依赖点击提交按钮兜底导航时，若提交控件定位失败 MUST 诚实记录，MUST NOT 因宽松判据在未真正提交查询时误判为已导航。

#### Scenario: 残留旧搜索页不算本次导航成功
- **WHEN** 搜索起点 URL 已含 `search` 子串（如上一步详情页带搜索来源参数、或停在旧关键词结果页），本次输入词后未真正提交/导航
- **THEN** MUST NOT 因 URL 含子串就判已到结果页，MUST 触发提交按钮兜底；仍未导航则诚实回未到结果页

#### Scenario: 结果页关键词须等于本次搜索词
- **WHEN** 到达一个搜索结果页，但其 URL 关键词参数不等于本次要搜的词
- **THEN** MUST 判为未到达本次搜索的结果页、诚实回失败，MUST NOT 采该页卡片当本次候选

#### Scenario: 红线反例——旧关键词结果页冒充本次结果（禁止）
- **WHEN** 有实现在提交失败、浏览器仍停在旧关键词结果页时，把该页当本次搜索成功并采卡
- **THEN** MUST 视为违规、不予合入；确认导航 MUST 校验结果页关键词与本次搜索词一致

### Requirement: 评论结果回执区分自动排期与人工命令来源

评论任务的终态结果卡 SHALL 标明触发来源——**自动排期评论**（`priority='automatic'`）与**人工 `/comment` 命令**（`priority='human'`）在回执上可辨识区分，MUST NOT 把自动排期评论一律标为「/comment 命令」使运维无法区分来源。

#### Scenario: 自动排期评论回执标注来源
- **WHEN** 一次自动排期触发的评论任务产出终态回执
- **THEN** 回执 MUST 标明为「排期评论（自动）」类来源，与人工命令回执可区分

#### Scenario: 人工命令评论回执标注来源
- **WHEN** 一次人工 `/comment` 触发的评论任务产出终态回执
- **THEN** 回执 MUST 标明为人工命令来源

### Requirement: /comment --join accepts a specific group URL

The Feishu command `/comment <昵称> --join=<群链接>` SHALL join the specified Facebook group URL for the resolved account, then comment in that group. The URL form MUST be parsed as a trailing switch (any order with `--contact`), leaving the rest as the nickname; a mid-nickname `--join=` token stays part of the nickname (trailing-only). Bare `--join` (no URL) keeps its existing next-from-library behavior. The targeted group MUST be scoped to this account only: the implementation MUST NOT register the URL as a shared, broadly auto-joinable target for other accounts.

#### Scenario: Join a specific URL then comment
- **WHEN** an operator sends `/comment <昵称> --join=<url>` for a Facebook account that is not yet a member of that group
- **THEN** the system MUST join that specific group, and on confirmed membership MUST comment inside it (with contact info only if `--contact` was also given, still via human review)

#### Scenario: Already a member → skip join, comment directly
- **WHEN** the account is already a confirmed member of the specified group URL
- **THEN** the system MUST skip the join edge round-trip and comment directly in that group

#### Scenario: Invalid group URL → honest failure
- **WHEN** the `--join=<url>` value is not a valid Facebook group URL
- **THEN** the system MUST return an honest failure receipt (`invalid_group_url`) and MUST NOT join or comment

#### Scenario: Group owned by another account → honest failure
- **WHEN** the specified group URL is already held by a different account's membership row
- **THEN** the system MUST return an honest failure receipt (`owned_by_other_account`), MUST NOT comment, and MUST NOT impersonate membership

#### Scenario: Non-Facebook account → rejected
- **WHEN** `--join=<url>` is used on a non-Facebook account
- **THEN** the system MUST reject with the existing "仅支持 Facebook" honest receipt

#### Scenario: Red-line reversal — URL form silently falls back to a random library group (forbidden)
- **WHEN** `--join=<url>` is given but the specific-join path is unwired or the URL is invalid, and an implementation instead joins the next group from the shared library
- **THEN** it MUST be treated as a violation and not merged; the URL form MUST fail honestly, never join a different group

#### Scenario: Red-line reversal — URL form creates a shared auto-join target (forbidden)
- **WHEN** an implementation registers the `--join=<url>` group as an `enabled` shared target so the auto-join sweep hands it to other accounts
- **THEN** it MUST be treated as a violation and not merged; the target row backing the per-account membership MUST be `enabled=false`

### Requirement: 搜索提交 MUST 用真实用户手势，未确认跳转 MUST 有界重试

边端在搜索结果页采卡**之前**的「提交搜索」这一步，MUST 使用**真实用户手势**驱动小红书搜索框（尤其已灰度 AI 搜索、搜索框为 `textarea[name="aiSearchTextarea"]`、结果落 `/search_result_ai` 的账号——其「回车导航」不响应纯程序化聚焦）：

- **聚焦 MUST 派发真实指针点击**（对可见搜索框坐标发 `Input.dispatchMouseEvent` 按下+抬起），MUST NOT 仅用程序化 `el.focus()` 聚焦即提交。取不到可见搜索框坐标时 MAY 回退程序化聚焦（诚实降级），MUST NOT 因此静默假成功。
- **回车 MUST 携带字符文本**（`text:'\r'`，产生真实 `keypress` 形态），MUST NOT 只发不带 text 的裸 `keydown`（裸回车在 AI 搜索框上不触发导航）。
- 输入完成到回车之间 MUST 留一个**停顿地板**，让搜索框内部状态就绪，MUST NOT 输入后立即回车导致提交被忽略。
- 首次回车在有界窗口内**未确认跳转到结果页**时，MUST **有界重试回车**（受尝试上限约束），MUST NOT 把「点击一个可能不可见（0×0）的提交按钮」当作唯一或必需兜底；提交按钮点击**仅在其确可见时** MAY 作为附加尝试。
- 所有提交尝试用尽仍未确认到达结果页时，MUST 走既有诚实失败契约（以采卡时刻实时 URL 判定，回 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`，MUST NOT 采/报当前页 feed）。本要求是既有「搜索采卡前 MUST 确认已到达搜索结果页」契约的**提交侧补全**：既有契约保证「到不了不撒谎」，本要求保证「用对手势真的到得了」。

此要求 MUST 同时覆盖 `/search_result` 与 `/search_result_ai` 两种结果页；两者的 URL 判据、关键词（含双重编码）归一、卡片提取沿用现状、不因页型分叉。

#### Scenario: AI 搜索框——真实点击聚焦 + 带文本回车 → 跳转成功
- **WHEN** 边端在 AI 搜索账号上提交搜索
- **THEN** MUST 先对可见搜索框派发真实指针点击聚焦，逐字输入关键词
- **AND** MUST 在输入后留停顿地板再派发**携带 `text:'\r'`** 的回车
- **AND** 以采卡时刻实时 URL 确认到达 `/search_result` 或 `/search_result_ai` 后照常采卡上报

#### Scenario: 首次回车未跳转 → 有界重试回车
- **WHEN** 边端派发回车后在有界窗口内实时 URL 仍非结果页
- **THEN** MUST 再次派发回车（受尝试上限约束），MUST NOT 仅点一个不可见的提交按钮就放弃
- **AND** 若在重试内确认跳转，则照常采卡；全部尝试用尽仍未跳转，MUST 回 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}` 且不采/报当前页

#### Scenario: 纯程序化聚焦 / 裸回车 / 仅点不可见按钮 → 视为违规
- **WHEN** 有实现仅用程序化 `el.focus()` 聚焦、或发不带字符文本的裸回车、或仅依赖点击一个不可见提交按钮来提交搜索
- **THEN** MUST 视为不满足本要求（AI 搜索框上这些方式不可靠、会造成大面积 `not_on_search_page` 假阴性）

### Requirement: 云端开笔记步 MUST 竞速消费开笔记失败信号、不干等满超时、失败如实归因

云端按需评论的「开笔记 / 读正文」步在等待目标笔记详情时，MUST **同时**监听「成功」与「失败」两类信号并竞速取先到者，MUST NOT 只监听 `note.detail.arrived` 而对失败信号充耳不闻、干等满单步超时：

- **成功**：`note.detail.arrived` 且 noteId 与目标一致 → 照常读正文 / 采现场评论。
- **失败（边缘诚实回执）**：`action.completed{action:'open_note', ok:false}`（弹层不弹 / 抽取失败 / 墙钟预算耗尽 / 无 noteId 找不到卡等）→ MUST 立即以失败返回，携带边缘上报的真实 `reason`。
- **失败（目标卡已不在当前页）**：边缘重报的 `page.cards.arrived`（带 noteId 的目标卡被虚拟列表回收、有界滚回仍找不到时，边缘重报当前卡片）→ MUST 立即以失败返回（reason 表意为「目标不在当前页」）。

任一失败信号先到即快速失败，MUST NOT 继续干等满单步超时（消除每次开笔记失败白等约一个单步预算）。三类信号都未到（真超时 / 无送达）时才按超时失败，且措辞 MUST 中性（如「无回执（超时/结果未就绪）」），MUST NOT 把**边缘在线的诚实失败**冒充「（超时/边端离线）」（假归因红线，与搜索导航失败归因同口径）。

此要求为既有「云端 MUST 消费搜索导航失败回执并真实归因失败原因」的开笔记侧对称件；两步都 MUST 竞速消费诚实失败、快速失败、如实归因。

#### Scenario: 边缘诚实回开笔记失败 → 立即失败带真实原因
- **WHEN** 云端开笔记步在等详情时收到 `action.completed{action:'open_note', ok:false, reason}`
- **THEN** MUST 立即以失败返回（不再等详情），日志/回执归因 MUST 呈现真实 `reason`，MUST NOT 说「（超时/边端离线）」

#### Scenario: 目标卡已被回收、边缘重报卡片 → 立即失败
- **WHEN** 云端开笔记步在等详情时收到边缘重报的 `page.cards.arrived`（而非目标 `note.detail`）
- **THEN** MUST 立即以失败返回（reason 表意「目标不在当前页」），MUST NOT 干等满单步超时

#### Scenario: 三路皆未到（真超时）→ 中性措辞
- **WHEN** 单步预算内既无匹配 `note.detail`、也无 `open_note` 失败回执、也无重报 `page.cards`
- **THEN** MUST 按超时失败，措辞中性（不断言「边端离线」）

