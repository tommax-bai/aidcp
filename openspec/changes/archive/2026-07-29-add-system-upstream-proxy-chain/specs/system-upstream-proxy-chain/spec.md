## ADDED Requirements

### Requirement: 客户端 SHALL 提供显式系统前置代理模式

客户端 SHALL 为 AdsPower 环境提供一个默认关闭的机器级设置，用于为已配置环境代理的 profile 在直接环境代理与“系统代理 → 环境代理”之间选择。设置关闭时 MUST 保持既有环境代理行为逐字等价；设置打开时 MUST 只在新的浏览器代际应用，并在界面明确展示链路方向。未配置环境代理的 profile MUST 保持既有无代理行为，不得因没有第二跳而阻断启动。运行中修改该设置 SHALL 要求重启受影响浏览器，不得把旧代际显示成新模式已生效。

#### Scenario: 缺省保持直接环境代理
- **WHEN** 用户从未开启系统前置代理模式
- **THEN** AdsPower 浏览器和启动前预检继续直接使用 profile 保存的环境代理，且不启动本地链路中继

#### Scenario: 开启后展示双跳方向
- **WHEN** 用户开启系统前置代理模式并保存，且当前 profile 已配置环境代理
- **THEN** 客户端展示“系统代理 → 环境代理 → 目标网站”，并要求运行中的受影响环境重启后生效

#### Scenario: 未配置环境代理时双跳不适用
- **WHEN** 用户开启系统前置代理模式，但待启动 profile 明确配置为无代理
- **THEN** 客户端不保存代理权威、不解析系统代理、不创建本地中继、不更新 AdsPower profile，并按既有无代理路径继续启动

#### Scenario: 未启动环境立即采用当前开关
- **WHEN** 用户修改系统前置代理开关且目标环境的浏览器代际尚未启动
- **THEN** 客户端立即持久化当前选择、作废该环境旧的代理预检和中继证据，并只按新选择执行随后的离线预检

#### Scenario: 运行中环境冻结实际模式
- **WHEN** 用户修改系统前置代理开关但目标环境已有运行中的浏览器代际
- **THEN** 客户端持久化目标选择但保持该代际的实际代理模式与中继生命周期不变，并明确要求重启后应用

#### Scenario: 旧浏览器代际不冒充双跳
- **WHEN** AdsPower profile 已由其他入口打开或当前代际没有经过启动前 profile 同步及读回
- **THEN** 客户端拒绝把该浏览器作为双跳环境接管，并提示关闭后重新启动

### Requirement: 原环境代理 SHALL 加密保存并按启动代际同步

客户端 SHALL 把用户为环境配置的代理作为 AIDCP 权威，并按 AdsPower `user_id` 使用 Electron `safeStorage` 加密保存。创建环境时 SHALL 仍将用户输入代理直接传给 AdsPower；只有创建成功后的浏览器启动阶段才根据系统前置开关选择写入原环境代理或 GOST loopback。客户端内修改代理 SHALL 同步更新权威；明确无代理 SHALL 删除该环境权威并跳过后续限制。

每次实际启动新浏览器代际前，包括冷待机唤醒，客户端 SHALL 更新 AdsPower profile 并精确读回验证，之后才允许 `browser-profile/start`。关闭后恢复原代理只是尽力兜底；异常退出留下的配置 SHALL 由下一次启动前同步纠正。凭据 MUST NOT 出现在 renderer、通用 settings、argv、环境变量或日志。

#### Scenario: 创建环境保留用户代理
- **WHEN** 用户创建一个配置了代理的 AdsPower 环境
- **THEN** 创建请求使用用户输入的代理，创建成功后客户端加密保存同一规范化原环境代理，不在创建阶段替换为 GOST

#### Scenario: 启动时按开关同步
- **WHEN** 已配置代理的 inactive 环境将启动新浏览器代际
- **THEN** 开启系统前置模式时写入该环境受管 GOST loopback，关闭时写入加密原环境代理；读回不一致则不启动

#### Scenario: 关闭后尽力恢复
- **WHEN** 已配置代理环境的浏览器已确认关闭
- **THEN** 客户端尽力写回并验证原环境代理；失败不推翻关闭事实，下一次启动前仍重新同步

#### Scenario: 异常退出后下一次启动纠偏
- **WHEN** 上一进程异常退出导致 AdsPower profile 暂留 GOST loopback
- **THEN** 下一次启动不信任该暂留值，而是按加密权威和当前开关重新写入并读回

#### Scenario: 无代理环境完全跳过
- **WHEN** 创建、编辑或精确读取确认环境未配置代理
- **THEN** 客户端不保存代理权威、不更新或恢复 profile、不进入双跳检测或 active-profile 限制

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

客户端 SHALL 为需要启动的 AdsPower profile 创建受管本地代理中继，其入站只监听随机 loopback 端口，第一跳为解析后的系统代理，第二跳为 AIDCP 加密权威中的原环境代理。中继 SHALL 支持现有环境代理的 HTTP、HTTPS 与 SOCKS5 类型，并保持既有类型语义。

环境代理账号密码 MUST 只存在于 AdsPower 首次精确读取响应、`safeStorage` 加密记录、受控内存、私有 pipe 和中继私有配置输入中；MUST NOT 出现在进程 argv/环境变量、renderer IPC、settings、链路状态、日志或错误正文。中继二进制 SHALL 固定版本、校验来源并作为桌面资源交付；开发态可使用显式覆盖路径。签名前 staging 和开发态 SHALL 校验固定上游归档及二进制 SHA-256；Electron `afterSign` 和最终发行产物门禁 SHALL 校验资源内 App、GOST 和 Native Page Engine 的 Developer ID、Team ID、Identifier、目标架构以及 GOST 固定版本。macOS 签名包运行态 SHALL 忽略外部覆盖，只验证固定资源目录内的兼容清单、可执行文件和目标架构，MUST NOT 因外层 App 的 Team ID 缺失、签名输出差异或签名前完整文件哈希拒绝启动；运行可用性 SHALL 由 GOST 实际进程启动和 loopback 就绪结果决定。

#### Scenario: 两跳中继就绪后才交付
- **WHEN** 系统代理和环境代理均合法且中继成功监听 loopback
- **THEN** 客户端只有在有界探测确认本地端口就绪后才把该端点交给预检与浏览器

#### Scenario: 中继启动失败不泄露凭据
- **WHEN** 二进制缺失、配置不受支持、端口绑定失败或进程提前退出
- **THEN** 客户端返回稳定的中继不可用原因，错误和日志不包含环境代理用户名、密码或完整配置

#### Scenario: 本地入口不可被远程访问
- **WHEN** 中继处于运行状态
- **THEN** 它只监听 `127.0.0.1`，不得绑定 `0.0.0.0`、局域网或公网地址

#### Scenario: 发行门禁验证嵌套中继身份
- **WHEN** macOS Developer ID 签名改变了资源内 GOST Mach-O 的完整文件哈希
- **THEN** `afterSign` 和最终发行验证器检查应用与 GOST 的有效签名、Team ID、Identifier、资源路径和 arm64/x64 架构并确认固定 GOST 版本；不得按签名前二进制哈希拒绝有效签名产物

#### Scenario: 安装态外层 App 被 ad-hoc 重签
- **WHEN** 客户机器对外层 `AIDCP.app` 做 ad-hoc 重签，使其 Team ID 显示为 `not set`，而固定资源内 GOST 清单、可执行性和架构仍兼容
- **THEN** 客户端不调用运行时 `codesign` 或启动前版本探针阻断中继，而是尝试启动 GOST，并按进程退出或 loopback 就绪结果如实判定可用性

#### Scenario: 安装态嵌套资源不可运行
- **WHEN** 固定包内 GOST 缺失、不可执行、清单不兼容、架构错误、启动即退出或未在有界时间内监听
- **THEN** 客户端如实返回中继不可用，MUST NOT 因放宽签名自检而把未启动的代理链报告为可用

#### Scenario: 打包态外部覆盖不绕过资源信任
- **WHEN** 已打包客户端进程环境包含 `AIDCP_GOST_BINARY`
- **THEN** 客户端忽略该覆盖并只解析、验证和执行应用资源目录内的 GOST

#### Scenario: 签名后产物门禁阻止无效嵌套代码
- **WHEN** Electron 完成 macOS 应用签名
- **THEN** 构建必须在生成分发包前验证最终 App、GOST 和 Native Page Engine 的签名身份、架构以及 GOST 版本，任一失败即停止出包

#### Scenario: 生命周期回收
- **WHEN** 应用退出、profile 配置失效或相关浏览器确认关闭且链路不再使用
- **THEN** 客户端终止对应中继；下次启动还 SHALL 清理自身遗留的孤儿中继，不影响其他应用进程

### Requirement: 双跳状态 SHALL 由同链路证据驱动

双跳开关开启且 profile 已配置环境代理时，Facebook 代理预检与 AdsPower 新浏览器代际 SHALL 使用同一个受管 loopback 端点。预检成功只能证明该时刻完整链路能够访问目标；浏览器实际出口仍 SHALL 由既有浏览器网络上下文证据决定。客户端 SHALL 分别显示配置模式、链路准备状态和浏览器出口证据，MUST NOT 把任一层结果冒充另一层。

#### Scenario: 预检与浏览器使用同一入口
- **WHEN** 双跳模式下为某环境完成启动前预检并随后启动浏览器
- **THEN** 预检使用该端点，浏览器启动前把 profile 同步为同一端点并读回；浏览器不直接持有原环境代理凭据

#### Scenario: 预检成功不冒充浏览器出口
- **WHEN** 完整代理链预检成功但浏览器尚未取得出口证据
- **THEN** 界面只显示链路可用，浏览器实际出口仍显示未取得

#### Scenario: 浏览器出口证据确认最终代理
- **WHEN** 新浏览器代际通过既有 CDP 出口探测取得公网 IP
- **THEN** 客户端按既有规则显示已验证、疑似直连或无法确认，并把配置模式标为系统前置双跳
