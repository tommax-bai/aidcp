## MODIFIED Requirements

### Requirement: 定时自动评论复用命令式评论管线、只提议不越审

排期触发的评论 SHALL 复用现有命令式评论任务管线（persona 闸、边端在线检查、有界任务、异步结果卡），但边缘占用 MUST 拆为两个任务租约阶段：prepare 租约执行搜索/读取并在获得目标快照后释放；云端撰写与审批/预授权期间不持有边缘租约；仅当评论获得授权后申请 commit 租约、按稳定 `noteId` 重开复检并提交，随后释放。账号未开启全局评论免审时，`review` 模式真发 MUST 仍只在人审 approved 后进行，未接线 / 超时 / 拒绝一律不发；`auto_approve` 模式 SHALL 表示运营已后台预授权该账号自动评论。账号显式 `auto_approve_all` 时 MUST 覆盖排期来源模式为免审。有效免审模式 MUST 不发审批按钮卡、不等待人工点击，而是在撰写完成后发送飞书免审通知并进入既有 commit 流程。评论任务可能诚实产出 0 条（无强相关目标），系统 MUST NOT 为凑数硬评、MUST NOT 把「未找到目标」报成成功。手动 `/comment` MUST 完全不受排期时段限制，也不受**排期自身**免审配置影响，但 SHALL 服从账号全局免审覆盖。

#### Scenario: review 模式到点自动发起评论任务
- **WHEN** `source_rules` 账号命中其评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有命令式评论入口发起一次任务；prepare 读取目标后释放边缘，人审通过才重新获得 commit 租约并真发

#### Scenario: auto_approve 模式评论只通知不等审批
- **WHEN** 某账号命中评论排期且有效模式为 `auto_approve`，评论已完成撰写并通过本地内容闸
- **THEN** 系统 SHALL 发送飞书免审通知卡并继续既有 commit 租约与提交验证，MUST NOT 发送带同意/不发按钮的审批卡

#### Scenario: 账号全局免审覆盖排期 review
- **WHEN** 账号显式 `auto_approve_all`，排期来源模式仍为 `review`
- **THEN** 本次有效模式为 `auto_approve`，通知成功后继续提交且不等待按钮审批

#### Scenario: 人审等待不独占边缘
- **WHEN** 排期评论已完成目标读取、正在等待人审或处理后台预授权通知
- **THEN** edge 不持有该评论任务租约，可继续浏览或处理更高优先级任务；授权后必须重新抢占并复检目标

#### Scenario: 诚实空槽
- **WHEN** 评论任务搜索甄选后无强相关目标
- **THEN** 本次不评，结果卡如实报「未找到强相关目标」，绝不硬凑、绝不染绿

#### Scenario: 手动只服从账号全局覆盖而非排期模式
- **WHEN** 运营在排期时段外对 `source_rules` 账号手动 `/comment`，而排期评论为 `auto_approve`
- **THEN** 照常触发且仍需人审；若账号本身为 `auto_approve_all`，则通知后免审

### Requirement: 定时自动联系评论经同一评论机器、带独占刹车

排期触发的联系评论 SHALL 复用命令式评论任务机器并带 `injectContact`（缺联系方式 fail-closed、注入在授权前 verbatim、结果卡自补全部沿用）；账号未开启全局评论免审时，`review` 模式真发 MUST 仍只在人审 approved 后进行，`auto_approve` 模式 SHALL 使用后台预授权并发送飞书免审通知。账号显式 `auto_approve_all` 时 MUST 覆盖联系评论来源模式为免审。该动作 SHALL 过四道闸：① 单飞与评论动作共用（同一评论机器按账号 isRunning，互斥天然成立）；② **每日自动尝试上限**——判定与记录基于持久 attempts 记录（触发回执 ok 即记一条，按账号、服务器本地日历日），被人审拒 / 无强相关目标的尝试同样占额度（保守方向），MUST NOT 依赖内存计数器；③ 自动路径 MUST 过 `canDo('comment')` 配额（手动 `/comment --contact` 仍跳配额）；④ 联系评论日上限硬上限 SHALL 为 10（越界整块拒；与发帖 / 评论的 50 刻意分开）。触发被拒（配额 / 缺联系方式 / 离线 / 在跑）SHALL 回黄色卡如实说明，MUST NOT 静默。手动 `/comment --contact` MUST 完全不受排期时段限制，也不受**排期自身**免审配置影响，但 SHALL 服从账号全局免审覆盖。

#### Scenario: review 模式到点自动发起联系评论任务
- **WHEN** `source_rules` 账号命中其联系评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统以 injectContact 调用命令式评论入口发起一次任务；联系方式在人审卡前 verbatim 接入，人审通过才发

#### Scenario: auto_approve 模式联系评论只通知不等审批
- **WHEN** 某账号命中联系评论排期且有效模式为 `auto_approve`
- **THEN** 系统 SHALL 在撰写出含联系方式的拟发评论后发送飞书免审通知，并继续既有提交链路，MUST NOT 降级为无联系方式评论

#### Scenario: 全局免审不绕自动联系评论刹车
- **WHEN** `auto_approve_all` 账号命中联系评论排期但已达尝试上限或 `canDo('comment')` 拒绝
- **THEN** 本槽仍被拒并如实回卡，MUST NOT 因免审绕过额度或配额

#### Scenario: 尝试即占额度（保守方向）
- **WHEN** 联系评论任务开跑后因无强相关目标或人审拒绝而未发出
- **THEN** 该次尝试仍计入当日上限；当日尝试数达上限后不再触发

#### Scenario: 重启不超发
- **WHEN** 云端重启后内存态丢失
- **THEN** 当日尝试计数来自持久 attempts 记录，不清零、不越限

#### Scenario: 联系评论硬上限
- **WHEN** 提交联系评论日上限为 11
- **THEN** 整块拒绝（越 10 上限），绝不部分落库
