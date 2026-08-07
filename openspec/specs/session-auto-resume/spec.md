# session-auto-resume Specification

## Purpose
TBD - created by archiving change session-auto-resume-with-excursions. Update Purpose after archive.
## Requirements
### Requirement: 单场正常结束后自动歇 N% 再续场

单场浏览会话**正常结束**后，云端 SHALL 自行接续而非停摆：等待一段休息后自动重开一场新会话（计时归零、互动预算刷新）。休息时长 SHALL = `全局单场时长 × rest_ratio`（`rest_ratio` 默认 10%；**取消账号维度——`rest_ratio` 与单场时长均为全局配置，所有账号一致**），并 SHALL 叠加 lognormal 抖动使每次休息不等长（拟人）。续场 MUST 经现有会话启动闸（调度全局开关 + 人设绑定）后才真正重开；启动闸不过则诚实不续，MUST NOT 以默认人设静默开跑。

#### Scenario: 时长到上限正常结束后续场
- **WHEN** 单场因时长到上限正常结束（`session.should_end` 携超时 reason）
- **THEN** 云端等待 `rest = 全局单场时长 × rest_ratio`（叠抖动）后经启动闸自动重开一场新会话，新会话计时从重开时刻起算、互动预算重置

#### Scenario: 休息时长全局配置热加载
- **WHEN** 运营把**全局** `rest_ratio` 由 10% 改为 20%
- **THEN** **所有账号**的**下一次**休息即按 20% 计（无需重启），不再有按账号差异

### Requirement: 续场资格按结束原因区分

只有「正常结束」才自动续场；运营显式停 / 验证码-风控暂停 / 边缘掉线 MUST NOT 触发自动续场。云端 SHALL 在结束会话时携带可续场资格标记，由结束的来源决定，MUST NOT 仅凭 reason 文本猜测。

#### Scenario: 正常结束（时长/动作数/预算）可续场
- **WHEN** 会话因时长到上限、或动作数到顶、或互动配额耗尽而结束
- **THEN** 该结束标记为可续场，进入休息+续场流程

#### Scenario: 运营停 / 风控暂停 / 掉线不续场
- **WHEN** 会话因运营在面板 `dispatch stop`、或账号被验证码/风控暂停、或边缘掉线而结束
- **THEN** 该结束标记为不可续场，云端 MUST NOT 安排休息计时器、MUST NOT 自动重开会话

### Requirement: 自动续场须过活跃时段窗口、每日上限与风控闸

续场前云端 SHALL 依次校验三道护栏，任一不过则**本轮不续**（诚实停，不报错）：① **活跃时段窗口**——仅在**全局配置**的时段窗口内才续，过点则本轮不续、待下一个窗口；② **每日上限**——每账号每日自动续场场数与累计时长 MUST 有上限，**该上限为全局配置（所有账号同一阈值）**，计数仍**按账号按日**统计，到顶即停续，计数按日界/窗口界重置；③ **撞风控不续**——账号风控状态为 restricted/frozen 时 MUST NOT 续场。三道护栏的阈值 SHALL **为全局可配（取消账号维度）**。

#### Scenario: 过了活跃时段窗口不续
- **WHEN** 单场正常结束时已超出**全局**活跃时段窗口（如窗口 08:00–24:00、当前 00:30）
- **THEN** 云端 MUST NOT 自动续场；待下一个活跃窗口开启时方可再起

#### Scenario: 当日续场已达上限不续
- **WHEN** 某账号当日自动续场已达**全局配置**的场数上限（或累计时长上限）
- **THEN** 云端 MUST NOT 再为该账号自动续场，直至日界/窗口界重置计数（计数按账号统计、阈值全局共用）

#### Scenario: 风控受限不续
- **WHEN** 单场正常结束时账号风控状态为 restricted 或 frozen
- **THEN** 云端 MUST NOT 自动续场

### Requirement: 休息计时器每连接私有、有界取消、绝不广播

休息计时器 MUST 每连接私有，且只重开**该连接自己**的会话，MUST NOT 调用任何全局批量启动而向其它连接误发命令。计时器 MUST 在以下任一情形立即取消、不再触发续场：运营 `dispatch stop`、账号被风控/验证码暂停、边缘掉线/连接拆除、休息期间该边缘先行重连（已自行重开会话）。计时器句柄 MUST 不挂住进程（`unref`）。

#### Scenario: 休息期边缘先重连则取消待发续场
- **WHEN** 休息计时器尚未触发时，该边缘自行重连并已重置重开了会话
- **THEN** 待发的休息计时器 MUST 被取消，云端 MUST NOT 再次重开会话（避免重复接线）

#### Scenario: 休息期运营停或掉线则取消续场
- **WHEN** 休息计时器待发期间，运营 `dispatch stop` 或该连接掉线拆除
- **THEN** 待发的休息计时器 MUST 被取消，MUST NOT 续场

#### Scenario: 续场只作用于本连接
- **WHEN** 多账号多连接在线，其中一条连接的会话正常结束并到点续场
- **THEN** 续场命令 MUST 只重开该连接自己的会话，MUST NOT 向其它连接/账号发任何命令

### Requirement: 续场与护栏配置须落库、热加载、缺值绝不 brick

续场相关配置（`rest_ratio`、活跃时段窗口、每日上限）SHALL **作为全局单例落库（单行、无账号维度，参照模型配置单行 `id=1` 模式）**、管理后台可改、运行时每次现读（热加载、无需重启）。缺表 / 全局行缺失 / 非法值 MUST 逐位回落写死默认（**绝不 brick**）；空表行为与「不配护栏、仅按默认 `rest_ratio` 续场」逐位一致。配置的存储与编辑 MUST NOT 触碰风控状态单写路径。

#### Scenario: 全局配置缺失回落默认
- **WHEN** 全局续场配置表无行（全新部署/迁移刚跑完）
- **THEN** 续场按写死默认 `rest_ratio` 进行，护栏取默认（不阻塞续场），云端照常运行不崩

#### Scenario: 非法配置整块拒、不部分落库
- **WHEN** 管理后台提交的续场配置含非法字段（负数/超上限）
- **THEN** 服务端整块拒（4xx），MUST NOT 部分落库或假成功，内存生效值保持改前真态

### Requirement: 会话正常结束流程对单次结束只触发一次且不得自毁续场计时器

监测体判定的**单次会话结束** MUST 只走**一次**结束流程（单一结束入口）。结束流程 MUST NOT 在同一次结束里被调用两次；尤其当结束流程顶部「无条件取消续场休息计时器」与「会话活跃守卫早退」并存时，MUST NOT 出现「第一次结束武装续场计时器、第二次结束又把它取消并早退、致续场永不触发」的自毁。结束流程对**可续场**的正常结束 MUST 在结束流程内武装休息计时器，且该计时器 MUST NOT 被同一次结束的任何后续调用取消。

#### Scenario: 时长超限单次结束只走一次结束流程

- **WHEN** 单场因时长到上限正常结束（监测体触发一次结束）
- **THEN** 云端的会话结束流程对这一次结束恰好执行一次（MUST NOT 执行两次），其余结束方式（动作数到顶、互动预算耗尽、idle 看门狗）同此

#### Scenario: 正常结束后续场休息计时器仍存活、未被同次结束取消

- **WHEN** 一次可续场的正常结束完成
- **THEN** 为续场武装的休息计时器处于「已武装且未被取消」状态，休息到点后续场流程（休息→过启动闸→重开会话）正常触发，MUST NOT 因同次结束的重复调用被清掉

### Requirement: 续场重开会话后必须主动重新驱动边端浏览闭环

浏览闭环的实际推进由**边端结构化上报**驱动；会话结束后边端浏览循环停止、不再上报。因此云端**续场重开会话**后 MUST 主动下发一条引导浏览命令，重新驱动边端浏览循环重报卡片、使决策环得以继续；MUST NOT 仅在云端激活新会话而不向边端发任何命令（否则边端无输入、循环空转）。所有主动重驱 MUST 复用既有滚动通道（动作 `scroll` → 消息 `{platform}.feed.scroll`；Facebook 会话钉住 Reels 面时为 `facebook.reels.scroll`——本次要恢复的浏览面由命令名的面段承载，不再有 `targetSurface` 载荷字段），使用统一的 `reason:'resume_redrive'`。系统 MUST NOT 为此新增协议消息类型；两份 TypeScript 协议、命令映射、Native 严格解码与协议文档 MUST 保持一致。

#### Scenario: 续场后云端主动下发统一重驱命令

- **WHEN** 自动续场经启动闸重开了一场新会话（`feed.entered{trigger:'session_start'}`）
- **THEN** 云端按该场钉住的目标浏览面下发一次 `{platform}.feed.scroll{reason:'resume_redrive'}`（Facebook 会话钉住 Reels 面时为 `facebook.reels.scroll{reason:'resume_redrive'}`）
- **AND** 边端据此重新驱动浏览循环并重报 `page.cards`，决策环继续

#### Scenario: 续场引导不新增协议消息

- **WHEN** 实现续场后的边端重驱
- **THEN** 系统复用既有滚动通道（动作 `scroll` → `{platform}.feed.scroll` / `facebook.reels.scroll`）与边端主动命令白名单，MUST NOT 新增协议消息类型
- **AND** 重驱要恢复的浏览面由命令名的面段在 Cloud、Edge、Native 与协议文档中保持一致

#### Scenario: 非 Facebook 重驱保持兼容

- **WHEN** 非 Facebook 平台收到 `xiaohongshu.feed.scroll{reason:'resume_redrive'}`
- **THEN** Edge 按既有普通滚动语义执行，不因 `resume_redrive` reason 改变滚动行为

