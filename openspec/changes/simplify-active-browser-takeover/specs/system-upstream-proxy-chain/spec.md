## MODIFIED Requirements

### Requirement: 双跳状态 SHALL 由同链路证据驱动

双跳开关开启且 Inactive profile 已配置环境代理时，Facebook 代理预检与 AdsPower 新浏览器代际 SHALL 使用同一个受管 loopback 端点。预检成功只证明该时刻完整链路能够访问 Facebook；客户端 SHALL 分别显示配置模式、链路准备状态和可达性结果，MUST NOT 把任一层结果冒充浏览器公网出口验证。AdsPower 已报告 Active 的 profile SHALL 直接接管，不准备、探测或验证双跳链路。

#### Scenario: 预检与新浏览器使用同一入口
- **WHEN** 双跳模式下为 Inactive 环境完成启动前预检并随后启动浏览器
- **THEN** 预检使用该端点，浏览器启动前把 profile 同步为同一端点并读回；浏览器不直接持有原环境代理凭据

#### Scenario: 预检成功只证明链路可达
- **WHEN** 完整代理链预检成功
- **THEN** 界面显示系统前置双跳和代理可用
- **AND** MUST NOT 显示或推断浏览器实际出口、本机直连出口或公网出口验证

#### Scenario: Active 浏览器绕过双跳准备
- **WHEN** AdsPower 报告目标 profile 已经 Active
- **THEN** 客户端直接接管，不解析系统代理、建立 GOST 中继、运行链路预检或验证浏览器公网出口
