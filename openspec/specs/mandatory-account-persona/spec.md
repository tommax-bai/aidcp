# mandatory-account-persona Specification

## Purpose
TBD - created by archiving change persona-driven-content-pipeline. Update Purpose after archive.
## Requirements
### Requirement: 人设是账号运行的前提

账号 SHALL 在绑定人设后方可参与浏览与发布。人设经 `getSoul(accountId)` / `resolvePersona(accountId)` 提供，浏览闭环与发布管线均以其为输入。账号无绑定人设时，系统 SHALL 诚实拒绝并给出 `no_persona`，MUST NOT 继续以任何替代人设运行（红线：不静默假成功）。

唯一例外是 Facebook 规则模式：环境已启用规则模式且平台为 Facebook 时，该模式自身的浏览、点赞、加群与模板评论四个动作 SHALL 无需账号绑定人设即可运行，且 MUST NOT 读取人设做任何判断。该例外 MUST 逐条收窄：仅对规则批次成立；同一账号经普通浏览、发布、飞书手工评论、排期评论或 mandatory 评论触发时，人设闸逐字不变、仍以 `no_persona` 诚实拒绝；规则批次的评论段有效正文方案 MUST 为模板，显式生成方案时该评论段 MUST 以具名原因如实不可执行，MUST NOT 调用生成器。例外的含义是「这条路不需要人设」，MUST NOT 被实现为「缺人设时回落一份替代人设」。

#### Scenario: 已绑人设的账号可运行

- **WHEN** 账号已绑定人设，触发浏览会话或发布
- **THEN** 浏览/发布以该账号真实人设为输入正常运行

#### Scenario: 无人设账号浏览被拒

- **WHEN** 账号未绑定人设，尝试启动普通浏览会话
- **THEN** 系统以 `no_persona` 诚实拒绝启动，不以任何默认/替代人设开始浏览

#### Scenario: 无人设账号发布被拒

- **WHEN** 账号未绑定人设，触发发布
- **THEN** 系统以 `no_persona` 诚实拒绝发布，不生成任何内容，不以替代人设代偿

#### Scenario: 未绑人设的 Facebook 规则模式可运行

- **WHEN** 某 Facebook 环境已启用规则模式，其绑定账号未绑定人设
- **THEN** 规则模式的浏览、点赞、加群与模板评论正常运行，全程不读取人设，也不回落任何替代人设

#### Scenario: 例外不外溢到其它来源

- **WHEN** 一个未绑人设、已启用规则模式的 Facebook 账号被普通浏览、发布、飞书手工评论、排期评论或 mandatory 评论触发
- **THEN** 该次触发仍以 `no_persona` 诚实拒绝，MUST NOT 因规则模式例外而放行

#### Scenario: 生成式正文方案不被例外覆盖

- **WHEN** 未绑人设账号的规则批次进入评论段，而该账号显式选择了生成式正文方案
- **THEN** 该评论段以具名原因如实标为不可执行，批次只保留浏览与点赞结果，MUST NOT 调用生成器，MUST NOT 改用模板顶替该显式选择

### Requirement: 系统不提供默认或兜底人设

系统 MUST NOT 存在全局默认/兜底人设。人设解析器在账号无人设（或人设解析失败）时 MUST NOT 静默返回某个默认人设，SHALL 明确暴露「无人设」信号交由调用方诚实拒绝。已删除的 `default` 账号相关特判 SHALL 一并清理。

#### Scenario: 无人设时解析器不代偿

- **WHEN** 对一个未绑定人设的账号解析人设
- **THEN** 解析器返回「无人设」信号（而非某个默认人设），下游据此诚实拒绝，不产生任何以默认人设为前提的行为

#### Scenario: 不再特判已删除的 default 账号

- **WHEN** 判定某账号是否需要补人设
- **THEN** 判定仅依据该账号是否已绑人设，不再对已删除的 `default` 账号做任何特殊豁免

### Requirement: 绑定入口强制人设必填

账号绑定/编辑入口 SHALL 强制人设必填——console 端未填人设不允许保存，cloud 端写入校验同样拒绝无人设的绑定。校验 SHALL 双端一致，任一端 MUST NOT 放行无人设账号落库。

#### Scenario: 未填人设不允许绑定

- **WHEN** 在账号绑定/编辑处未填写人设即尝试保存
- **THEN** console 阻止保存并提示人设必填；即便绕过前端，cloud 写入校验也拒绝该无人设绑定，不落库

