## ADDED Requirements

### Requirement: 客户端 SHALL 提供显式系统前置代理模式

客户端 SHALL 为 AdsPower 环境提供一个默认关闭的机器级设置，用于在直接环境代理与“系统代理 → 环境代理”之间选择。设置关闭时 MUST 保持既有环境代理行为逐字等价；设置打开时 MUST 只在新的浏览器代际应用，并在界面明确展示链路方向。运行中修改该设置 SHALL 要求重启受影响浏览器，不得把旧代际显示成新模式已生效。

#### Scenario: 缺省保持直接环境代理
- **WHEN** 用户从未开启系统前置代理模式
- **THEN** AdsPower 浏览器和启动前预检继续直接使用 profile 保存的环境代理，且不启动本地链路中继

#### Scenario: 开启后展示双跳方向
- **WHEN** 用户开启系统前置代理模式并保存
- **THEN** 客户端展示“系统代理 → 环境代理 → 目标网站”，并要求运行中的受影响环境重启后生效

#### Scenario: 旧浏览器代际不冒充双跳
- **WHEN** AdsPower profile 已由其他入口打开或当前代际没有应用受管本地代理覆盖
- **THEN** 客户端拒绝把该浏览器作为双跳环境接管，并提示关闭后重新启动

### Requirement: macOS 系统代理解析 SHALL 有限且诚实

首版客户端 SHALL 在 macOS 主进程读取当前系统代理，并只接受可解析的固定 SOCKS5 或 HTTP CONNECT 端点。多个固定端点同时启用时 SHALL 使用确定性的 `SOCKS5 → HTTPS web proxy → HTTP web proxy` 优先级；macOS 的 HTTPS web proxy 字段 SHALL 按 HTTP CONNECT 端点解释，MUST NOT 因字段名为 HTTPS 就猜测代理端口自身支持 TLS。

PAC、自动发现、缺少固定端点、非法 host/port、需要但无法取得认证信息、与本地中继形成回环或与环境代理重复的配置 SHALL 返回稳定的不可用原因。系统 MUST NOT 在双跳模式下把这些情况静默降级为直连或单跳。

#### Scenario: 解析固定 SOCKS5 系统代理
- **WHEN** `scutil --proxy` 报告一个启用且合法的 SOCKS5 端点
- **THEN** 客户端把该端点选为第一跳，并且不把 host、port 之外的未取得字段猜成凭据

#### Scenario: HTTPS web proxy 按 CONNECT 解释
- **WHEN** 系统设置只启用了 `HTTPSProxy/HTTPSPort`
- **THEN** 客户端把它作为明文 HTTP CONNECT 上游，而不是向该端口发起未经证明的 TLS 握手

#### Scenario: PAC 首版诚实拒绝
- **WHEN** 系统代理依赖 PAC 或自动发现才能决定有效上游
- **THEN** 客户端显示当前系统代理类型尚不支持，并阻止双跳启动，不直接连接环境代理

#### Scenario: 双跳前置代理消失
- **WHEN** 开关已开启但没有可用固定系统代理
- **THEN** 本次预检与浏览器启动均停止，并显示系统前置代理不可用，不回退单跳或直连

### Requirement: 受管本地中继 SHALL 安全组成两跳链路

客户端 SHALL 为需要启动的 AdsPower profile 创建受管本地代理中继，其入站只监听随机 loopback 端口，第一跳为解析后的系统代理，第二跳为该 profile 原本保存的环境代理。中继 SHALL 支持现有环境代理的 HTTP、HTTPS 与 SOCKS5 类型，并保持既有类型语义。

环境代理账号密码 MUST 只存在于 AdsPower 精确读取响应、主进程内存和中继私有配置输入中；MUST NOT 出现在进程 argv、renderer IPC、settings、链路状态、日志或错误正文。中继二进制 SHALL 固定版本、校验来源并作为桌面资源交付；开发态可使用显式覆盖路径。

#### Scenario: 两跳中继就绪后才交付
- **WHEN** 系统代理和环境代理均合法且中继成功监听 loopback
- **THEN** 客户端只有在有界探测确认本地端口就绪后才把该端点交给预检与浏览器

#### Scenario: 中继启动失败不泄露凭据
- **WHEN** 二进制缺失、配置不受支持、端口绑定失败或进程提前退出
- **THEN** 客户端返回稳定的中继不可用原因，错误和日志不包含环境代理用户名、密码或完整配置

#### Scenario: 本地入口不可被远程访问
- **WHEN** 中继处于运行状态
- **THEN** 它只监听 `127.0.0.1`，不得绑定 `0.0.0.0`、局域网或公网地址

#### Scenario: 生命周期回收
- **WHEN** 应用退出、profile 配置失效或相关浏览器确认关闭且链路不再使用
- **THEN** 客户端终止对应中继；下次启动还 SHALL 清理自身遗留的孤儿中继，不影响其他应用进程

### Requirement: 双跳状态 SHALL 由同链路证据驱动

开启双跳时，Facebook 代理预检与 AdsPower 新浏览器代际 SHALL 使用同一个受管 loopback 端点。预检成功只能证明该时刻完整链路能够访问目标；浏览器实际出口仍 SHALL 由既有浏览器网络上下文证据决定。客户端 SHALL 分别显示配置模式、链路准备状态和浏览器出口证据，MUST NOT 把任一层结果冒充另一层。

#### Scenario: 预检与浏览器使用同一入口
- **WHEN** 双跳模式下为某环境完成启动前预检并随后启动浏览器
- **THEN** 两者均使用该环境同一受管 loopback 端点，环境代理凭据不再由浏览器直接持有

#### Scenario: 预检成功不冒充浏览器出口
- **WHEN** 完整代理链预检成功但浏览器尚未取得出口证据
- **THEN** 界面只显示链路可用，浏览器实际出口仍显示未取得

#### Scenario: 浏览器出口证据确认最终代理
- **WHEN** 新浏览器代际通过既有 CDP 出口探测取得公网 IP
- **THEN** 客户端按既有规则显示已验证、疑似直连或无法确认，并把配置模式标为系统前置双跳
