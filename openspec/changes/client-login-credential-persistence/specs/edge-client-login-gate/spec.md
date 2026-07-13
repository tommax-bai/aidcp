## ADDED Requirements

### Requirement: Login credential prefill is local and clearable

登录成功后，客户端 SHALL 在当前实例的 `userData` 范围内保存账户名与访问密钥的加密副本，并在后续登录门打开时回填两个输入框。访问密钥 MUST NOT 以明文写入本地存储、session 文件、日志、协议或云端；加密能力不可用时 MUST 不写明文回退且不阻断正常登录。

#### Scenario: 成功登录后下次回填

- **WHEN** 客户使用有效账户名和访问密钥登录成功，随后再次打开登录门
- **THEN** 登录页回填上次成功提交的账户名和访问密钥，客户可以直接继续登录

#### Scenario: 用户手动清空后不再回填

- **WHEN** 客户在登录页把账户名或访问密钥输入框清空
- **THEN** 客户端立即删除本地记忆，后续打开登录门不得回填旧凭据

#### Scenario: 退出登录清除凭据记忆

- **WHEN** 客户显式退出登录，或服务端判定客户会话失效并把客户端送回登录门
- **THEN** 客户端清除本地凭据记忆，重新打开的登录页保持为空
