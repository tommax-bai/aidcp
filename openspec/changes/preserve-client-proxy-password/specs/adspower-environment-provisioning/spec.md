## MODIFIED Requirements

### Requirement: 凭据只内存持有、绝不明文落盘、日志脱敏

AdsPower API key 与代理账号密码 SHALL 仅在创建 / 改代理批处理以及当前代理编辑界面的读取、回填、提交期间**内存持有**，MUST NOT 明文写入 `settings.json` 或任何台账/文档；台账 SHALL 只存非密的代理摘要。`user/create` 与 `user/update` 的 POST 请求体 SHALL NOT 被整体 stringify 进日志/错误，日志与错误透传层 SHALL 显式脱敏 `proxy_user`/`proxy_password` 与 `Authorization`。当 AdsPower `user/list` 返回已存 `proxy_password` 时，渲染层 SHALL 仅在该环境的代理编辑输入框中直接回显该密码，使未修改的密码可随本次保存原样提交；该值 MUST NOT 出现在环境列表摘要、设置、诊断或日志。确需在编辑会话之外持久化敏感值时 SHALL 用 OS keychain（如 `safeStorage`），MUST NOT 写明文设置。

#### Scenario: 代理账密不落盘不进日志
- **WHEN** 创建或改代理时携带了代理账号密码，且某条 `user/create` / `user/update` 返回错误
- **THEN** 账密只在允许的本地内存链路中持有、不写入 settings/台账，错误信息中 `proxy_password`/`Authorization` 被脱敏，MUST NOT 出现在日志或环境列表摘要

#### Scenario: 已存密码仅在对应代理编辑框回显
- **WHEN** AdsPower `user/list` 为客户可见环境返回 `user_proxy_config.proxy_password`
- **THEN** 客户端在该环境的代理编辑输入框中直接显示密码，但 MUST NOT 把它写入设置、花名册、代理摘要、诊断或日志

### Requirement: 代理可在客户端配置：创建可选填、已有环境可增改、无代理如实标注

桌面外壳 SHALL 允许在客户端内完成代理配置：**创建时**表单提供可选代理区块（类型 `http`/`https`/`socks5` + host/port + 可选账密，默认「无代理」）；**已有环境**提供逐环境的「代理」编辑入口，读回现配置字段预填。当 AdsPower 返回现有密码时，密码 SHALL 在编辑框中直接回显并作为当前表单值保留，保存经写客户端的 `user/update` 封装下发；用户 MAY 修改或清空该值。代理输入 SHALL 经统一归一层校验（类型枚举、host 非空、port 为 1-65535 整数、有密码必须有用户名），任一不合法 SHALL **诚实拒绝提交**（创建时拒建、编辑时拒存并说明原因），MUST NOT 静默降级成 `no_proxy` 或砍掉非法字段后照发。选「无代理」保存 SHALL 显式下发 `{ proxy_soft: 'no_proxy' }`（支持清除既有代理）。桌面外壳 SHALL NOT 因未配代理而阻止创建：未配代理时 SHALL 给出提醒，但仍允许创建；环境列表 SHALL 如实呈现「无代理」状态，该标注 MUST NOT 拦截任何操作。编辑已配代理的环境时 SHALL 提示改代理对已养成账号画像的影响（出口 IP / 时区 / 地理随代理跳变）。桌面外壳 MUST NOT 自动采购/管理代理池、MUST NOT 引用/管理 AdsPower 侧已保存代理账本（`proxyid`/`global_config` 不做）。改代理的生效时机以 AdsPower 实际行为为准，UI SHALL 按「下次启动该环境生效」的保守口径提示，MUST NOT 承诺即时生效。

#### Scenario: 未配代理仍可创建但给提醒并标注
- **WHEN** 运维未填代理即点「创建环境」
- **THEN** 桌面外壳给出「未配置代理」提醒但仍允许创建，成功后该环境在列表如实标「无代理」，不阻止任何后续操作

#### Scenario: 创建时填合法代理随建号下发
- **WHEN** 运维在创建表单选择 socks5 并填合法 host/port（及可选账密）后点「创建环境」
- **THEN** `user/create` 的 `user_proxy_config` 携带 `{ proxy_soft:'other', proxy_type:'socks5', … }`，建成后列表如实显示该代理摘要

#### Scenario: 非法代理输入诚实拒绝
- **WHEN** 代理输入含非法 port（如 `70000`）或选了类型但 host 为空
- **THEN** 归一层在提交前诚实拒绝并说明原因，MUST NOT 发出请求、MUST NOT 静默按 `no_proxy` 处理

#### Scenario: 已有环境修改其他代理字段时保留现有密码
- **WHEN** AdsPower 已返回某环境的现有代理密码，运维打开代理编辑浮层、只修改 host、port、类型或用户名后保存
- **THEN** 写客户端以 `{ user_id, user_proxy_config }` 两键 body 调 `user/update`，其中 `user_proxy_config.proxy_password` 仍为回显的现有值

#### Scenario: 已有环境可修改或清空代理密码
- **WHEN** 运维在已有环境的代理编辑浮层修改或清空已回显密码后保存
- **THEN** `user/update` 按当前表单值提交完整代理配置，成功后提示「下次启动该环境生效」并刷新列表摘要；失败按 AdsPower 返回诚实展示

#### Scenario: AdsPower 未返回密码时不伪造旧值
- **WHEN** AdsPower `user/list` 未返回某环境的 `proxy_password`
- **THEN** 客户端密码框如实为空，MUST NOT 声称已保留或恢复未知密码

#### Scenario: 显式清除代理
- **WHEN** 运维在编辑浮层选「无代理」并保存
- **THEN** 下发 `{ proxy_soft:'no_proxy' }`，列表摘要回到「无代理配置」
