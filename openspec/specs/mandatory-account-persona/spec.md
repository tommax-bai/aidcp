# mandatory-account-persona Specification

## Purpose
TBD - created by archiving change persona-driven-content-pipeline. Update Purpose after archive.
## Requirements
### Requirement: 人设是账号运行的前提

账号 SHALL 在绑定人设后方可参与浏览与发布。人设经 `getSoul(accountId)` / `resolvePersona(accountId)` 提供，浏览闭环与发布管线均以其为输入。账号无绑定人设时，系统 SHALL 诚实拒绝并给出 `no_persona`，MUST NOT 继续以任何替代人设运行（红线：不静默假成功）。

#### Scenario: 已绑人设的账号可运行

- **WHEN** 账号已绑定人设，触发浏览会话或发布
- **THEN** 浏览/发布以该账号真实人设为输入正常运行

#### Scenario: 无人设账号浏览被拒

- **WHEN** 账号未绑定人设，尝试启动浏览会话
- **THEN** 系统以 `no_persona` 诚实拒绝启动，不以任何默认/替代人设开始浏览

#### Scenario: 无人设账号发布被拒

- **WHEN** 账号未绑定人设，触发发布
- **THEN** 系统以 `no_persona` 诚实拒绝发布，不生成任何内容，不以替代人设代偿

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

