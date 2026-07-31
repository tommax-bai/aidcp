## MODIFIED Requirements

### Requirement: Facebook 运行页顶栏区分代理配置与运行证据

桌面主界面 SHALL 仅在当前选中环境为 Facebook 时，于顶栏账号身份区呈现紧凑代理状态入口；紧凑态 SHALL 显示代理配置、Facebook 可达性预检结论和“本次会话接收流量”。详情 SHALL 展示非密代理配置摘要、预检时间、接收流量及其统计口径，MUST NOT 展示或推断浏览器实际出口、本机直连出口或公网出口相等结论。代理密码 MUST NOT 进入运行页渲染数据，主环境列表 MUST NOT 铺开完整代理地址。

#### Scenario: 预检成功显示代理可用和流量
- **WHEN** 当前选中 Facebook 环境的代理预检成功
- **THEN** 顶栏显示“代理可用”和格式化后的本次会话接收流量，详情展示非密配置摘要与检测时间
- **AND** MUST NOT 使用“代理已验证”或显示浏览器、本机公网出口

#### Scenario: Active 浏览器无预检也不伪造成功
- **WHEN** 当前浏览器由 Active 直接接管且本次未运行代理预检
- **THEN** 顶栏显示已有配置摘要、真实浏览器状态和流量
- **AND** MUST NOT 因接管成功而伪造代理可达或公网出口验证

#### Scenario: 配置存在但预检未知不显示成功
- **WHEN** AdsPower 环境存在代理配置但 Facebook 可达性预检尚未完成或失败
- **THEN** 顶栏显示“待检测”“无法确认”或“代理不可用”的对应诚实状态，MUST NOT 使用绿色已验证状态

#### Scenario: 非 Facebook 环境不出现代理入口
- **WHEN** 当前选中环境平台不是 Facebook
- **THEN** 顶栏隐藏该代理入口，不改变既有平台身份与健康状态布局

#### Scenario: 详情只使用安全聚合数据
- **WHEN** 运维打开代理详情
- **THEN** 界面只展示配置类型/地址等非密摘要、预检时间与聚合接收字节，并说明该流量不是代理商计费口径
- **AND** MUST NOT 展示公网出口、URL、Cookie、请求正文或代理密码
