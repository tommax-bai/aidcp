## ADDED Requirements

### Requirement: 排期动作支持关、审批、免审三档

内容排期的自动发帖、自动评论、自动联系评论 SHALL 分别支持三档模式：`off`（不自动触发）、`review`（自动触发但每条仍需飞书审批）、`auto_approve`（自动触发且由后台配置视为预授权，飞书只发通知）。账号级 `autoEnabled=false` 仍 SHALL 作为总闸使所有动作等价不触发。为兼容既有数据，系统 SHALL 能从旧 boolean 字段推导模式：旧开 = `review`，旧关 = `off`；新写入模式时 MUST 同步旧 boolean 可读状态。

#### Scenario: 旧数据按审批模式兼容
- **WHEN** 某账号旧数据 `post_enabled=true` 且没有新 `post_mode`
- **THEN** 系统 SHALL 将自动发帖展示和执行为 `review` 模式，继续走飞书审批

#### Scenario: 免审不等于总闸开启
- **WHEN** 某账号 `autoEnabled=false` 且某动作模式为 `auto_approve`
- **THEN** 内容调度器 MUST NOT 触发该动作

#### Scenario: 新模式同步旧布尔视图
- **WHEN** 运营把自动评论设置为 `auto_approve`
- **THEN** 服务端 SHALL 持久化 `comment_mode='auto_approve'`，并使旧 `comment_enabled` 视图为 true

## MODIFIED Requirements

### Requirement: 定时自动发帖只提议、绝不自动发送

内容排期触发的发帖 SHALL 复用现有发布管线的生成、待审草稿、授权信号与发布派发器。`review` 模式到点只**生成草稿并落待审**，真发 MUST 仍只在飞书人审 `approved===true` 后由发布派发器进行（AC-PUB）。`auto_approve` 模式 SHALL 表示运营已在后台对该账号自动发帖预授权：系统生成草稿后 MUST 写入同形 `approved===true` 授权信号（含当前内容版本），再由现有发布派发器执行；同时 MUST 发送飞书通知卡说明本次由后台免审配置自动授权。内容调度器 MUST NOT 新增任何绕过发布派发器、绕过版本闸、或绕过 `approved===true` 复核的发送路径。手动 `/publish` MUST 完全不受排期时段限制、随时可发，且不因排期免审配置而跳过其既有人审要求。

#### Scenario: review 模式到点只产草稿待审
- **WHEN** 某账号命中其发帖排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有发帖触发机器生成草稿并落待审、发出飞书审批卡，绝不直接发送

#### Scenario: review 模式人审通过才发
- **WHEN** 排期产生的草稿在飞书被审批通过
- **THEN** 由现有发布派发器在 `approved===true` 后发送；未通过 / 超时 / 拒绝一律不发

#### Scenario: auto_approve 模式后台预授权后经 dispatcher 发送
- **WHEN** 某账号命中其发帖排期且动作模式为 `auto_approve`
- **THEN** 系统 SHALL 落待审草稿、写入当前版本的 `approved===true` 授权信号、触发现有发布派发器，并发送飞书免审通知卡

#### Scenario: 手动不受时段与免审配置影响
- **WHEN** 运营在排期时段外手动 `/publish`
- **THEN** 照常触发，绝不因内容时段格为「休眠」而被拦，也不因该账号排期发帖为 `auto_approve` 而跳过手动发布审批

### Requirement: 内容排期数据契约与 fail-closed 默认（未配即不自动）

系统 SHALL 用与浏览掩码**物理分开**的两处结构承载内容排期：一处全局「内容可自动时段」168 格 '0'/'1' 周历掩码（周一起头×24h、服务器本地时），一处每账号排期（总开关、发帖模式、发帖日上限、评论模式、评论日上限、联系评论模式、联系评论日上限、可选每账号时段覆盖）。所有默认 MUST fail-closed：账号未配（无排期行）、总开关关、动作模式为 `off`、日上限为 0、或时段掩码缺失 / 非法——任一 SHALL 使该账号对应动作不自动触发。全局内容掩码缺失 / 非法 SHALL 视作全 0（不自动），MUST NOT 复用浏览掩码「缺失=全天活跃」的 fail-open 兜底。

#### Scenario: 未配账号不自动
- **WHEN** 某账号没有内容排期行（或总开关为关、或动作模式为 `off`、或日上限为 0）
- **THEN** 内容调度器对该账号对应动作完全不触发

#### Scenario: 非法掩码当作不活跃
- **WHEN** 全局或账号内容掩码缺失或非 168 位 '0'/'1'
- **THEN** 判定为「当前非活跃内容格」、不触发，绝不回落为全天允许

### Requirement: 定时自动评论复用命令式评论管线、只提议不越审

排期触发的评论 SHALL 复用现有命令式评论任务管线（persona 闸、边端在线检查、有界任务、异步结果卡），但边缘占用 MUST 拆为两个任务租约阶段：prepare 租约执行搜索/读取并在获得目标快照后释放；云端撰写与审批/预授权期间不持有边缘租约；仅当评论获得授权后申请 commit 租约、按稳定 `noteId` 重开复检并提交，随后释放。`review` 模式真发 MUST 仍只在人审 approved 后进行，未接线 / 超时 / 拒绝一律不发。`auto_approve` 模式 SHALL 表示运营已后台预授权该账号自动评论：系统 MUST 不发审批按钮卡、不等待人工点击，而是在撰写完成后发送飞书免审通知并进入既有 commit 流程。评论任务可能诚实产出 0 条（无强相关目标），系统 MUST NOT 为凑数硬评、MUST NOT 把「未找到目标」报成成功。手动 `/comment` MUST 完全不受排期时段限制，也不受排期免审配置影响。

#### Scenario: review 模式到点自动发起评论任务
- **WHEN** 某账号命中其评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有命令式评论入口发起一次任务；prepare 读取目标后释放边缘，人审通过才重新获得 commit 租约并真发

#### Scenario: auto_approve 模式评论只通知不等审批
- **WHEN** 某账号命中评论排期且动作模式为 `auto_approve`，评论已完成撰写并通过本地内容闸
- **THEN** 系统 SHALL 发送飞书免审通知卡并继续既有 commit 租约与提交验证，MUST NOT 发送带同意/不发按钮的审批卡

#### Scenario: 人审等待不独占边缘
- **WHEN** 排期评论已完成目标读取、正在等待飞书人审或处理后台预授权通知
- **THEN** edge 不持有该评论任务租约，可继续浏览或处理更高优先级任务；授权后必须重新抢占并复检目标

#### Scenario: 诚实空槽
- **WHEN** 评论任务搜索甄选后无强相关目标
- **THEN** 本次不评，结果卡如实报「未找到强相关目标」，绝不硬凑、绝不染绿

#### Scenario: 手动不受限
- **WHEN** 运营在排期时段外手动 `/comment`
- **THEN** 照常触发，不被内容时段格拦截，也不因排期评论为 `auto_approve` 而跳过手动评论审批

### Requirement: 定时自动联系评论经同一评论机器、带独占刹车

排期触发的联系评论 SHALL 复用命令式评论任务机器并带 `injectContact`（缺联系方式 fail-closed、注入在授权前 verbatim、结果卡自补全部沿用）；`review` 模式真发 MUST 仍只在人审 approved 后进行，`auto_approve` 模式 SHALL 使用后台预授权并发送飞书免审通知。该动作 SHALL 过四道闸：① 单飞与评论动作共用（同一评论机器按账号 isRunning，互斥天然成立）；② **每日自动尝试上限**——判定与记录基于持久 attempts 记录（触发回执 ok 即记一条，按账号、服务器本地日历日），被人审拒 / 无强相关目标的尝试同样占额度（保守方向），MUST NOT 依赖内存计数器；③ 自动路径 MUST 过 `canDo('comment')` 配额（手动 `/comment --contact` 仍跳配额）；④ 联系评论日上限硬上限 SHALL 为 10（越界整块拒；与发帖 / 评论的 50 刻意分开）。触发被拒（配额 / 缺联系方式 / 离线 / 在跑）SHALL 回黄色卡如实说明，MUST NOT 静默。手动 `/comment --contact` MUST 完全不受排期时段限制，也不受排期免审配置影响。

#### Scenario: review 模式到点自动发起联系评论任务
- **WHEN** 某账号命中其联系评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统以 injectContact 调用命令式评论入口发起一次任务；联系方式在人审卡前 verbatim 接入，人审通过才发

#### Scenario: auto_approve 模式联系评论只通知不等审批
- **WHEN** 某账号命中联系评论排期且动作模式为 `auto_approve`
- **THEN** 系统 SHALL 在撰写出含联系方式的拟发评论后发送飞书免审通知，并继续既有提交链路，MUST NOT 降级为无联系方式评论

#### Scenario: 尝试即占额度（保守方向）
- **WHEN** 联系评论任务开跑后因无强相关目标或人审拒绝而未发出
- **THEN** 该次尝试仍计入当日上限；当日尝试数达上限后不再触发

#### Scenario: 重启不超发
- **WHEN** 云端重启后内存态丢失
- **THEN** 当日尝试计数来自持久 attempts 记录，不清零、不越限

#### Scenario: 联系评论硬上限
- **WHEN** 提交联系评论日上限为 11
- **THEN** 整块拒绝（越 10 上限），绝不部分落库
