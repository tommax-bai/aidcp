## ADDED Requirements

### Requirement: AdsPower 新浏览器代际 SHALL 接受受管代理覆盖

当 Electron 外壳为系统前置代理模式准备了受管 loopback 端点时，`adspower` provider SHALL 只把该非敏感本地端点作为本次 `browser-profile/start` 的浏览器代理覆盖参数，不永久修改 AdsPower profile 保存的环境代理。未配置覆盖时 SHALL 保持既有启动参数逐字等价。

provider SHALL 在调用 AdsPower 启动接口前校验覆盖值只包含受支持协议、loopback host 和合法端口。AdsPower 已报告 profile active 时，provider 无法证明该浏览器代际应用了当前覆盖，因而 MUST 拒绝接管并要求关闭重启；MUST NOT 把 active 自报或本地端口存在当作双跳证据。

#### Scenario: 新浏览器带本地代理覆盖启动
- **WHEN** AdsPower profile 为 inactive 且外壳提供合法受管 loopback 代理
- **THEN** provider 在本次 `browser-profile/start` 的 `launch_args` 中加入对应 `--proxy-server`，其余指纹、视口和生命周期行为保持不变

#### Scenario: 无双跳覆盖时零回归
- **WHEN** 外壳未提供受管代理覆盖
- **THEN** provider 不增加 `--proxy-server` 参数，并继续使用 AdsPower profile 已保存的环境代理

#### Scenario: active 浏览器不能证明覆盖
- **WHEN** AdsPower 报告目标 profile 已 active 且本次要求受管代理覆盖
- **THEN** provider 拒绝接管并显示需要关闭后重启，MUST NOT 声称双跳已生效

#### Scenario: 非 loopback 覆盖被拒绝
- **WHEN** provider 收到指向非 loopback host、非法端口或不受支持协议的代理覆盖
- **THEN** provider 在调用 AdsPower API 前诚实失败，且不回落 self 或 profile 原代理
