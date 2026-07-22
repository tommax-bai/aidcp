## MODIFIED Requirements

### Requirement: 定时自动发帖只提议、绝不自动发送

内容排期触发的发帖 SHALL 复用现有发布管线的生成、待审草稿、人审授权与发布派发器。`review` 模式到点只**生成草稿并落待审**，真发 MUST 仍只在人审 `approved===true` 后由发布派发器进行（AC-PUB）。`auto_approve` 模式 SHALL 表示运营已在后台对该账号自动发帖预授权：系统生成草稿后 MUST 经与人工审批**同一个**授权写出口写入一条持久授权记录（`approved===true`、含当前内容版本、`decidedVia` 标为排期免审、`decidedBy` 为触发该免审的排期规则标识），再由现有发布派发器执行；同时 MUST 发送飞书通知卡说明本次由后台免审配置自动授权。

免审授权 MUST NOT 走任何绕过该写出口的旁路，MUST NOT 以本机文件承载。内容调度器 MUST NOT 新增任何绕过发布派发器、绕过版本闸、或绕过 `approved===true` 复核的发送路径。手动 `/publish` MUST 完全不受排期时段限制、随时可发，且不因排期免审配置而跳过其既有人审要求。

#### Scenario: review 模式到点只产草稿待审
- **WHEN** 某账号命中其发帖排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有发帖触发机器生成草稿并落待审、发出飞书审批卡，绝不直接发送

#### Scenario: review 模式人审通过才发
- **WHEN** 排期产生的草稿在飞书被审批通过
- **THEN** 由现有发布派发器在 `approved===true` 后发送；未通过 / 超时 / 拒绝一律不发

#### Scenario: auto_approve 模式后台预授权后经 dispatcher 发送
- **WHEN** 某账号命中其发帖排期且动作模式为 `auto_approve`
- **THEN** 系统 SHALL 落待审草稿、经同一授权写出口写入当前版本的 `approved===true` 持久授权记录（渠道标为排期免审、决策主体为该排期规则）、触发现有发布派发器，并发送飞书免审通知卡

#### Scenario: 免审授权同样进入待下发可见态
- **WHEN** 免审授权已写入但下发侧不可用
- **THEN** 该稿呈现为「已批准·待下发」并给出阻塞原因，MUST NOT 停留在与「待审批」不可区分的状态

#### Scenario: 手动不受时段与免审配置影响
- **WHEN** 运营在排期时段外手动 `/publish`
- **THEN** 照常触发，绝不因内容时段格为「休眠」而被拦，也不因该账号排期发帖为 `auto_approve` 而跳过手动发布审批
