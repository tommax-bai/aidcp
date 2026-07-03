## ADDED Requirements

### Requirement: 内容生成人设驱动且话题中立

发布内容生成（正文创作 system 与 user prompt，以及选题侦察 / 标题 / 话题 / 质量评分等各脚手架 prompt）SHALL 以账号绑定的人设为准，MUST NOT 硬编码任何特定领域框定（如「技术帖」「技术博主」「小林」等）。正文创作 SHALL 使用管线已传入的账号人设（`trigger.generateInput.soul`），与标题角色一致；脚手架措辞 SHALL 使用领域中立的「笔记」，领域由人设决定。few-shot 范文 MUST NOT 绑定单一领域（如全为技术示例）。

#### Scenario: 内容随人设领域变化

- **WHEN** 账号人设为某非技术领域（如美食），触发发布并生成正文
- **THEN** 生成的正文与标题体现该账号人设的领域与语气，不含「技术帖 / 技术博主」等被写死的技术框定

#### Scenario: 正文创作使用真实人设而非写死默认

- **WHEN** 正文创作角色构建 prompt
- **THEN** prompt 取自 `trigger.generateInput.soul` 的账号人设，而非硬编码的固定人设字符串

#### Scenario: 脚手架话题中立

- **WHEN** 选题侦察 / 标题 / 话题 / 质量评分等 prompt 被构建
- **THEN** 其措辞为领域中立的「笔记」，不出现写死的「技术帖」，领域交由人设体现

### Requirement: 无人设不得发布且不以默认人设代偿

发布管线在账号无绑定人设时 SHALL 以 `no_persona` 诚实拒绝，MUST NOT 回落到任何默认/兜底人设生成内容（红线：不静默假成功）。

#### Scenario: 无人设发布被拒且不生成内容

- **WHEN** 对未绑定人设的账号触发发布
- **THEN** 管线以 `no_persona` 拒绝，不生成正文/标题，不使用任何替代人设代偿
