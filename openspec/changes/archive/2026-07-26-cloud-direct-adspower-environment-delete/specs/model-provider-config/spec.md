## ADDED Requirements

### Requirement: 平台配置页管理 AdsPower API Key 且逐项说明生效时机

平台凭据注册表 SHALL 增加 AdsPower API Key，设置页 SHALL 在独立的浏览器服务凭据分组展示其标签、配置状态、来源和掩码，并提供空态 password 输入用于整段覆盖保存。明文 MUST NOT 回显、复制到 DOM 默认值或日志。页面 SHALL 按每项 `restartRequired` 分别说明生效时机：AdsPower Key 保存后下一次删除立即生效；启动期预载的模型/账单凭据仍按其真实规则提示重启，不得用一条“所有凭据都需重启”的笼统文案。

#### Scenario: AdsPower Key 以掩码展示
- **WHEN** 打开设置页且服务端已有 AdsPower API Key
- **THEN** 页面在浏览器服务凭据分组显示已配置、来源和掩码，输入框为空且不含明文

#### Scenario: AdsPower Key 保存后即时用于下一次删除
- **WHEN** 管理员输入完整新 Key 并保存成功
- **THEN** 输入框清空，页面提示下一次删除立即生效且无需重启 Cloud

#### Scenario: 不误导其它凭据生效方式
- **WHEN** 同一页面同时展示 AdsPower Key 与仍需启动期载入的模型凭据
- **THEN** 每项按自身 `restartRequired` 展示提示，AdsPower 标为即时生效而模型凭据仍标为重启生效

#### Scenario: 凭据输入彼此隔离
- **WHEN** 管理员编辑 AdsPower Key 输入框
- **THEN** 其它模型或账单凭据输入框的可见值保持不变，保存请求只携带 `provider=adspower, field=api_key`
