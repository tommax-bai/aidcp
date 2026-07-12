# account-identity-resolution Specification

## Purpose
TBD - created by archiving change account-identity-from-login. Update Purpose after archive.
## Requirements
### Requirement: 节点生命周期以「身份是否确立」为登录前/后分界

系统 SHALL 以「**系统是否已知此刻是哪个账号**」作为节点登录前/登录后的分界，而非以「登录」这个动作。节点生命周期 SHALL 分为三态：**无身份态**（账号无关）、**已确立身份·就绪闸**、**运行态**（账号作用域）。**无身份态 MUST NOT 替任何账号做任何账号作用域的事**（不读不写人设/风控/配额/去重/归因）。某操作是否属"登录后（账号绑定）"的判据 SHALL 是「不知道自己是哪个账号时它还成立吗」——不成立即账号绑定，MUST NOT 为绕过就绪闸把账号绑定操作挪到无身份态执行。

#### Scenario: 无身份态不做任何账号作用域操作
- **WHEN** 节点处于无身份态（尚未确立账号身份）
- **THEN** 它只做账号无关的事（节点初始化、进站、登录、读身份），绝不替任何账号浏览/互动/扣配额/归因，绝不借未知或默认账号开跑

#### Scenario: 操作分类按本质而非便利
- **WHEN** 判定某操作属登录前还是登录后
- **THEN** 以「不知道账号时它是否仍正确」为唯一判据；一个以账号身份行动的操作 MUST NOT 因实现方便被归到无身份态以规避就绪闸

### Requirement: 账号身份来自登录态读出的稳定 id，读不出即诚实失败

节点 SHALL 在登录完成后从登录态**读出该账号的稳定标识（如平台 userid）**作为账号身份，MUST NOT 以昵称作为身份主键（昵称仅作显示名）。读不出稳定 id 时 MUST **诚实失败、停手**，MUST NOT 猜测、MUST NOT 回落 `default`（否则等于借默认账号/默认人设静默开跑，违反「绝不静默假成功」）。

当启动期浏览器当前停在 `creator.xiaohongshu.com` 的真实创作平台页面（非 `/login`）时，该页面的登录门禁只证明"登录在场"；节点 MAY 进一步只读同源登录态存储中的平台 userid 字段来确立稳定账号 id。该路径 MUST 只接受形态合规且候选一致的稳定 id，MUST NOT 用右上角昵称、展示名、手机号、cookie/session token、畸形值或冲突值作为账号身份。若当前页是 `creator.xiaohongshu.com/login`，或创作平台同源存储无法给出可信稳定 id，节点 MUST 诚实失败或继续既有可证明安全的身份读取兜底，MUST NOT 猜测。

#### Scenario: 登录后读出稳定 id 作为身份
- **WHEN** 操作者在某节点的浏览器里登录了一个真实账号
- **THEN** 节点从登录态读出该账号的稳定 id，并以它作为该节点的账号身份（而非启动器外部指派的标签）

#### Scenario: 启动期停在创作平台真实页
- **WHEN** 节点启动后附着的浏览器页是 `creator.xiaohongshu.com` 的非 `/login` 页面，且同源登录态存储包含一致的形态合规 userid
- **THEN** 节点 MAY 用该 userid 确立账号身份并继续握手，MUST NOT 因消费端「我」锚点缺失而直接停手

#### Scenario: 创作平台只显示昵称但无可信稳定 id
- **WHEN** 创作平台页面右上角显示昵称，但同源登录态存储没有形态合规且一致的稳定 userid
- **THEN** 节点 MUST NOT 用昵称当主键，MUST 继续既有安全兜底或诚实失败停手

#### Scenario: 读不出稳定 id → 诚实失败，不回落 default
- **WHEN** 登录已完成但节点无法读出稳定账号 id
- **THEN** 节点诚实失败、停手并告警，绝不猜一个 id、绝不以 `default` 或任何默认身份开跑

#### Scenario: 昵称仅作显示名、不作主键
- **WHEN** 系统需要标识/区分账号
- **THEN** 用稳定 id 作主键，昵称只用于展示；昵称变化 MUST NOT 改变账号主键

### Requirement: 区分「节点初始化（一次性）」与「身份确立（可反复）」

无身份态 SHALL 含两件生命周期不同的事：**节点初始化**（一次性的基础设施：拉浏览器、分配端口/用户数据目录、连云端传输）与**身份确立**（可反复发生的态：进站→登录→读身份）。身份失效后重新确立身份时 MUST NOT 重跑节点初始化（MUST NOT 重启浏览器、重分端口/目录）。

#### Scenario: 掉登录只重跑身份确立、不重跑节点初始化
- **WHEN** 节点已建立（浏览器已起、端口/目录已分）但随后登录态失效
- **THEN** 节点退回无身份态、仅重新走"登录→读身份"，浏览器不重启、端口/用户数据目录不重新分配

### Requirement: 身份可翻转，须持续校验，翻转即退回无身份态重新确立

账号身份 SHALL 是一个**持续校验的状态**，不是握手时定死一次。当**确凿**判定登录态失效 / session 过期 / 同一用户数据目录换登了不同账号时，节点 MUST 退回无身份态、停掉账号作用域操作，并重新走"登录→读身份→就绪闸"。失效判定 MUST 满足「身份持续校验 MUST 按页面上下文分域判定」所定的口径——**「无法确认」不算失效**，MUST NOT 因就地读不到消费端锚点（例如浏览器此刻停在创作子域发布页或其它无「我」锚点的页面）就判失效。同一节点换登不同账号时，云端 MUST 把旧账号的会话拆除、按新账号重过就绪闸，MUST NOT 让两账号的上下文串味（状态单写）。

#### Scenario: 确凿登出/过期 → 退回无身份态重新确立
- **WHEN** 一个运行态节点被**确凿**判定登录态失效或过期（消费端页面读不出本人身份，或创作子域被重定向到 `/login`）
- **THEN** 节点退回无身份态、停止一切账号作用域操作，重新确立身份后再过就绪闸

#### Scenario: 同节点换登不同账号 → 旧账号会话拆除、新账号重过就绪闸
- **WHEN** 同一节点（同用户数据目录）从登录账号 A 改为登录账号 B
- **THEN** 身份从 A 翻转为 B，云端拆除 A 的会话、按 B 重建运行时并重过人设就绪闸，A、B 上下文互不串味

### Requirement: 身份确立后方握手、握手携带真实 id；无身份态不握手不被当配置错误

节点 SHALL 在**身份确立之后**才发起（或完成）握手，握手 MUST 携带登录态读出的真实账号 id。处于无身份态（尚未登录/未读出身份）的节点 MUST NOT 被当作"缺账号身份的配置错误"——它只是还没确立身份，应继续等待登录，MUST NOT 被静默映射成 `default`。本要求 MUST NOT 改动边-云协议（握手消息的账号字段已存在）。

#### Scenario: 无身份态节点不被当配置错误
- **WHEN** 节点已上线但尚未登录（无身份态）
- **THEN** 它不发起账号绑定的握手、也不被判为"缺 accountId 的配置错误"，而是继续等待登录；登录并读出身份后才握手

#### Scenario: 身份确立后握手携带真实 id
- **WHEN** 节点登录完成并读出稳定账号 id
- **THEN** 它以该真实 id 作为握手携带的账号身份，云端据此建运行时并过就绪闸（复用已部署门禁逻辑）

### Requirement: 启动器只分配节点槽位，环境变量标签降级为可选覆盖

多节点启动器 SHALL 只分配**节点槽位**（调试端口 / 用户数据目录 / `edgeId`），MUST NOT 再为节点分配账号 id；用户数据目录 SHALL 按节点槽位命名（账号未在登录前已知，是"谁登进这个槽位"的产物）。环境变量 `AIDCP_ACCOUNT_ID` SHALL 保留为**可选显式覆盖**：设了则用它、未设则走登录推导。

#### Scenario: 启动器分配槽位、身份由登录产生
- **WHEN** 操作者用多节点启动器起 N 个节点
- **THEN** 启动器只分配每节点的端口/用户数据目录/edgeId（目录名按节点槽位），各节点的账号身份由"操作者登进哪个账号"决定，启动器不指派 accountId

#### Scenario: 显式覆盖作为逃生阀
- **WHEN** 操作者为某节点显式设置了 `AIDCP_ACCOUNT_ID`
- **THEN** 该节点以该显式值为账号身份（覆盖登录推导）；建议在显式值与登录态读出的真实 id 不一致时诚实告警

### Requirement: 身份持续校验 MUST 按页面上下文分域判定，无法确认既不误杀也不假愈

运行期身份校验 SHALL 先取当前浏览器页面的上下文（至少读 `location.href` 的子域与路径），再按域选取判据，MUST NOT 不看页面就一律用消费端「我」锚点判定：

- **消费端页面（`www.xiaohongshu.com` 等）且能取到本人「我」锚点** → 读稳定 id：等于基线判健康、不等判换号（`changed`）、取不到判失效（`lost`）。
- **创作子域 `creator.xiaohongshu.com`** → 用其**登录门禁**作判据：停在真实创作页（非 `/login`）判**健康**、MUST NOT 判 `lost`；被重定向到 `creator.xiaohongshu.com/login` 判 `lost`（真登出）。此路只确认"登录在场"、不解析账号 id，账号换号检测仍归消费端路径。
- **其它取不到本人锚点、又非上述已知可判域的页面**（如 AI 搜索结果页 `/search_result_ai` 叠弹层/看图态） → 判**「无法确认」（inconclusive）**：该轮 MUST NOT 计入失效防抖计数、MUST NOT 判 `lost`，也 MUST NOT 判健康或重置基线，SHALL 跳过本轮并留下**可观测日志**（MUST NOT 静默 no-op）。

本要求是**双向红线**：inconclusive MUST NOT 误杀（假登出），也 MUST NOT 假愈（把无法确认当健康）。分域闸 MUST NOT 掩盖真登出——发生在可判域上的真登出仍须被判 `lost`。

#### Scenario: 发布把标签页带到创作发布页 → 判健康、不误杀
- **WHEN** 一次发布把共用标签页整页跳到 `creator.xiaohongshu.com/publish/publish` 且未被重定向到 `/login`，身份校验此刻触发
- **THEN** 节点据创作子域登录门禁判**健康**，MUST NOT 判 `lost`、MUST NOT 退回无身份态

#### Scenario: 创作子域被弹到登录页 → 判真登出
- **WHEN** 浏览器停在 `creator.xiaohongshu.com` 且被重定向到 `creator.xiaohongshu.com/login`
- **THEN** 判 `lost`（确凿登出），进入退回无身份态流程

#### Scenario: 停在无锚点消费页/弹层态 → 无法确认，跳过本轮不计失效
- **WHEN** 浏览器停在 `/search_result_ai` 等无本人锚点的页面或看图/弹层态，就地读不出稳定 id
- **THEN** 判「无法确认」，本轮 MUST NOT 进失效防抖计数、MUST NOT 判 `lost`，留可观测日志，下一轮再校验

#### Scenario: 真登出发生在消费端 feed → 仍被判失效
- **WHEN** 账号在消费端首页被平台登出，本人「我」锚点消失且非「无法确认」域
- **THEN** 分域闸仍判 `lost`，MUST NOT 因引入分域判据而漏判真登出

### Requirement: 重新确立身份 MUST 先回到可读身份的页面再判定

退回无身份态后的重新确立身份，SHALL 在重读身份**之前**先把浏览器带回一个能读出身份的页面（关闭弹层 / 导航回消费端首页；若停在创作子域可改用其登录门禁判据），MUST NOT 直接在触发失效时所处的、可能无本人锚点的页面上判身份而无谓停摆。只有在**已回到可读页面仍读不出任何登录信号**时，才诚实停手——保留既有红线：MUST NOT 猜 id、MUST NOT 回落 `default`。

#### Scenario: 自愈时停在创作页/弹层态 → 先归位再判
- **WHEN** 触发重新确立身份时浏览器停在创作发布页或看图/弹层态
- **THEN** 先关弹层 / 回消费端首页（或对创作子域用登录门禁判据）再重读身份，健康账号据此真恢复、重连云端，而非停摆待人工

#### Scenario: 归位后仍无任何登录信号 → 才诚实停手
- **WHEN** 已回到消费端首页仍读不出本人稳定 id、且无任何登录在场信号
- **THEN** 诚实停手、停在无身份态、不重连云端、MUST NOT 回落 `default`

### Requirement: 退回无身份态断连前 MUST 先诚实回执在途发布

退回无身份态断开云端链路前，节点 SHALL 先排空在途发布指令登记，为每条尚未回执的发布指令回一条诚实的失败结果（`[recycled]` 语义），再断连，MUST NOT 先断连致在途发布结果永远发不出、云端无限期挂起等待。此为「绝不静默假成功 / 诚实回报」在**身份翻转断连**路径上的落实，与 `edge-node-supervised-recycle`「回收撞在途发布→诚实判失败不重复发」同源。

#### Scenario: 身份翻转断连撞上在途发布 → 断链前诚实回执
- **WHEN** 退回无身份态即将断开云端链路，且此刻有发布指令在途未回执
- **THEN** 先为每条在途发布回一条 `[recycled]` 失败结果送达云端，再断连，云端据此收口该发布、不被无限期挂起

#### Scenario: 无在途发布 → 直接断连
- **WHEN** 退回无身份态断连时没有在途发布
- **THEN** 直接断连，无额外回执副作用

### Requirement: Facebook identity reader returns stable platform id or fails honestly

The Facebook platform driver SHALL implement identity reading that returns a stable Facebook account identifier suitable for `accounts.account_id` registration/routing, plus an optional display name. Identity candidates MUST come from logged-in page/session signals that are stable enough for routing; raw session tokens, cookies, or display names alone MUST NOT be used as the account primary key. If no stable id can be read or candidates conflict, edge MUST fail honestly and MUST NOT fall back to `default`.

#### Scenario: Stable Facebook id read succeeds
- **WHEN** a logged-in Facebook AdsPower profile exposes a consistent stable account id through approved identity signals
- **THEN** edge uses that stable id in hello/account routing and may expose display name separately

#### Scenario: Display name alone is insufficient
- **WHEN** Facebook UI shows a name but no stable id candidate can be verified
- **THEN** edge does not use the name as account id, fails identity resolution honestly, and does not start account-scoped actions

#### Scenario: Conflicting identity candidates fail
- **WHEN** two identity candidates disagree for the same profile/session
- **THEN** edge treats identity as inconclusive, reports failure, and does not guess or fall back to `default`

### Requirement: Facebook login probe distinguishes logged-out from empty content

The Facebook identity/login probe SHALL distinguish logged-out/login-wall/checkpoint states from a legitimate page with no candidate posts. Logged-out or blocked states MUST produce login/blocking outcomes, not `no_strong_candidate`, empty feed, or other harmless browse outcomes.

#### Scenario: Logged-out page is not empty feed
- **WHEN** a Facebook target renders login UI or redirects to login while probing
- **THEN** the probe returns a login-required/blocking result and prevents account work, rather than reporting no candidate posts

### Requirement: 启动期首次登录 MUST 有界等待，无壳侧登录门的 provider 在核心内补一道有界等待门

系统在**启动期身份确立**时，若命中一个**可判定的门控条件**——provider 为无壳侧登录门的提供商（当前即 `adspower`）**且**这是启动期首次身份读取**且** `decideIdentity` 返回 `halt`——MUST 进入一个**有界的「等待登录」循环**、而非即刻停手：SHALL 保持已附着的浏览器与 CDP 连接**不断开**（使操作者看得见浏览器、扫得了码），并周期性**就地重读**身份，直到读出形态合规的稳定 id（据此正常握手）或达到一个宽松的**人类登录超时上限**才收口。

门控条件 MUST 用上述三项**可判定信号**表达，MUST NOT 依赖一个「读不出属于『登录尚未建立』还是『已登录但读不出』」的首读分类器——身份读取只回自由文本原因、无此结构化判别子，`allowNavigate=false` 下「全新未登录消费页」与「已登录但锚点未渲染」返回相同失败，首读时不可区分。**有界等待 + 超时兜底本身即吸收「其实是确凿登出/终态」的情形**（只是把诚实停手推迟到窗口之后），故无需首读分类。

本要求 SHALL 为无壳侧登录门的提供商补一道**有界的核心内等待登录门**。`self` 提供商的壳侧登录门是**无限等待不放弃**、`adspower` 的核心内门是**有界**——这一差异是**刻意保留**的（壳侧门有独立的登录态轮询与看护语义，核心内门须有界以让诚实停手与看护处置可收敛），MUST NOT 被理解为要把 adspower 门也做成无限等待。

超时上限 MUST 可经环境变量调整、缩短或关闭（供看护 / headless / 无人值守场景改用短超时或退回「不等待、即刻停手」的旧行为；注意「关闭等待」仍 MUST 经诚实真退出端点收口、MUST NOT 退回留存活僵尸的旧 bare-return）。等待与最终握手 MUST NOT 放松任何既有红线——只在读出真实稳定 id 时握手，MUST NOT 猜、MUST NOT 回落 `default`；等待期就地重读 MUST NOT 触发跳转兜底而在二维码 / 登录页上做无谓合成点击。`AIDCP_ACCOUNT_ID` 显式覆盖路径**不受此门影响**（逃生阀，按既有语义直接以覆盖值确立、不进入等待）。

#### Scenario: 新建环境首次扫码 → 有界等待而非即刻停手
- **WHEN** provider 为 `adspower`、一个全新（未登录）的分身启动后附着浏览器、核心启动期首次读身份 `decideIdentity` 返回 `halt`
- **THEN** 核心进入有界「等待登录」循环、保持浏览器与 CDP 附着，操作者扫码登录并读出稳定 id 后**无缝继续握手**，MUST NOT 在操作者尚未完成登录时即刻停手

#### Scenario: 门控用可判定信号、不用首读登录态分类器
- **WHEN** 判断是否进入等待门
- **THEN** 只用「provider=adspower + 启动期首读 + halt」三项可判定信号决定，MUST NOT 试图在首读时区分「登录尚未建立」与「已登录但读不出」（该区分无结构化判据）；确凿登出的情形由等待超时兜底诚实收口

#### Scenario: 等待期保持浏览器可见可交互
- **WHEN** 核心处于启动期「等待登录」循环
- **THEN** 浏览器与 CDP 连接保持可用，「显示浏览器」等运维操作可正常发出，MUST NOT 关闭 CDP 致其失灵

#### Scenario: 等待超时仍未登录 → 诚实干净停止、不自动重起
- **WHEN** 到达人类登录超时上限时操作者始终未完成登录
- **THEN** 核心诚实停手、以**干净停止**语义收口（退出码 MUST NOT 触发看护层自动重起——避免『每轮空等超过健康存活阈值→连续失败计数被清零→有界重起永不放弃』的无限重起环），由操作者经「启动」再触发；MUST NOT 猜 id、MUST NOT 回落 `default`

#### Scenario: 覆盖值设置时跳过登录门
- **WHEN** 为某节点显式设置了 `AIDCP_ACCOUNT_ID` 覆盖
- **THEN** 直接以覆盖值确立身份、**不进入**等待门（逃生阀语义与既有一致）

### Requirement: 启动期「等待登录」MUST 可即时中断（收窄到 IPC 生命周期命令路径）

启动期「等待登录」循环落在**生命周期信号尚未完全接线的启动早窗**。此窗内唯一会被搁置的中断路径是**经 IPC 下发、堆进待派发生命周期命令队列**的暂停 / 关闭意图（正常要到握手后生命周期派发就绪才处理）；操作系统信号（SIGINT/SIGTERM）在此窗内走进程默认处置（立即终止），本就即时、**不被搁置**，故本要求 MUST NOT 要求临时接管 SIGINT/SIGTERM（那是对非问题的多余接线）。

核心 SHALL 在等待循环中**主动排空 / 拦截该 IPC 生命周期命令队列**：等待期收到暂停或关闭意图 MUST **即时中断循环并收口**。因启动早窗尚无运行中的账号作用域会话可暂停、且 `adspower` 浏览器由外部托管（进程退出不关它），此窗内的暂停 / 关闭意图 SHALL 一律解读为「本节点下线待重触发」→ 以**干净停止**语义退出（不触发自动重起），操作者经「启动 / 恢复」再来。等待循环结束后（无论因登录成功、超时、还是中断），核心 SHALL 交回正常生命周期接线，等待期排队的命令 MUST **恰好派发一次**（不双派发、不悬挂）。

#### Scenario: 等待期收到关闭 / 暂停 → 即时收口、干净停止
- **WHEN** 核心处于启动期「等待登录」循环，操作者经 IPC 请求暂停或关闭该环境
- **THEN** 核心即时中断等待、以干净停止语义收口退出（不触发自动重起），MUST NOT 等满登录超时才响应、MUST NOT 因退出码为可重起语义而被看护重起后再次进入等待

#### Scenario: 中断优先于超时
- **WHEN** 等待循环同时面临「仍未登录」与「到达关闭 / 暂停意图」
- **THEN** 以中断为先立即收口，MUST NOT 因仍在等待登录而漏掉、延迟该次关闭 / 暂停

#### Scenario: 登录成功续握手后交回正常接线、命令恰好派发一次
- **WHEN** 等待期读出稳定 id、核心继续正常握手，且等待期曾有 IPC 生命周期命令排队
- **THEN** 核心交回正常生命周期派发，排队命令**恰好派发一次**，MUST NOT 因等待期的临时拦截与握手后的正式派发造成双派发或悬挂

### Requirement: 启动期已验证昵称变化 MUST 刷新系统显示名

系统在 XHS 或 Facebook 账号每次启动任务并完成稳定账号 id 校验后，SHALL 尝试读取该平台当前登录账号的已验证昵称。若读取到的昵称非空、来源与已确立稳定账号 id 绑定，且与系统当前存储昵称不同，云端 MUST 将系统昵称更新为该已验证昵称。若读取不到昵称、昵称为空、昵称未与当前稳定账号 id 绑定、或身份候选冲突，系统 MUST NOT 更新昵称。昵称刷新 MUST 仅影响展示、人工选择和通知文案，MUST NOT 改变账号主键、路由、风控、配额或任务归因。

#### Scenario: XHS 启动检测到昵称变化后更新

- **WHEN** XHS 账号启动任务时已确立稳定账号 id，平台本人主页 / 登录态读取到非空昵称，且该昵称与系统已存昵称不同
- **THEN** 云端更新该账号系统昵称为平台当前昵称，账号 id 与任务归因保持不变

#### Scenario: Facebook 启动检测到昵称变化后更新

- **WHEN** Facebook 账号启动任务时已确立稳定数字 id，边端就地读取到与该 id 绑定的非空昵称，且该昵称与系统已存昵称不同
- **THEN** 云端更新该账号系统昵称为平台当前昵称，账号 id 与任务归因保持不变

#### Scenario: 未验证或空昵称不更新

- **WHEN** 启动期读不到昵称、昵称为空、昵称来源未与当前稳定账号 id 绑定、或身份候选冲突
- **THEN** 系统保留原系统昵称，MUST NOT 猜测或用页面标题 / 通用外壳文本覆盖

#### Scenario: 昵称不参与身份

- **WHEN** 平台昵称发生变化
- **THEN** 系统只更新显示昵称，MUST NOT 因昵称变化创建新账号或改写账号主键

