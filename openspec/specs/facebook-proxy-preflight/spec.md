# facebook-proxy-preflight Specification

## Purpose
TBD - created by archiving change facebook-proxy-selection-preflight. Update Purpose after archive.
## Requirements
### Requirement: 离线 Facebook 环境选择 SHALL 预热代理检测
客户端 SHALL 在用户选中浏览器未运行的 Facebook AdsPower 环境后，于 Electron 主进程后台使用 AIDCP 加密保存的原环境代理执行一次有界代理检测；既有环境尚无权威记录时 SHALL 先从 AdsPower 精确读取并加密引导，MUST NOT 把受管 loopback 当成原环境代理。系统前置代理模式开启时，客户端 SHALL 先准备“系统代理 → 环境代理”的受管中继，并经该中继执行检测。检测 MUST NOT 启动浏览器、占用浏览器槽位或阻塞环境选择；非 Facebook、无代理配置或浏览器已运行的环境 MUST NOT 触发该检测。

检测 SHALL 只发起不含 Cookie、账号、环境标识或业务正文的无身份 Facebook 连通请求。代理密码 MUST NOT 进入 renderer IPC、日志、设置文件或检测结果。

#### Scenario: 选择离线认证代理环境
- **WHEN** 用户选中一个浏览器未运行且保存了认证代理的 Facebook 环境
- **THEN** 主进程读取或引导该 profile 的加密原环境代理权威并后台检测一次，界面选择立即完成，浏览器保持关闭且不占槽位

#### Scenario: 双跳选择预热完整链路
- **WHEN** 用户开启系统前置代理模式并选中符合条件的离线 Facebook 环境
- **THEN** 主进程准备该环境的受管中继并通过其检测完整两跳链路，不直接探测环境代理

#### Scenario: 快速切换环境
- **WHEN** 用户在短时间内连续切换多个环境
- **THEN** 客户端只为最终稳定选中的合格环境发起检测，同一环境已有检测在途时 MUST NOT 重复发起

#### Scenario: 密码不越过主进程边界
- **WHEN** 主进程用 AdsPower 首次返回或本地解密的代理账号密码执行单跳检测或准备双跳中继
- **THEN** fleet 快照、renderer IPC、日志、本机 settings、子进程 argv 和环境变量均不包含代理密码

### Requirement: 启动与唤醒 SHALL 复用短时预检结果
客户端 SHALL 仅为需要新启动浏览器的环境按环境在内存中短时复用最近一次确定的预检结果。环境选择预热、批量启动或自动冷待机唤醒遇新鲜确定结果 SHALL 沿用既有复用行为；结果缺失、过期或正在检测时 SHALL 复用同一在途检测或补做一次，不得建立轮询。AdsPower 已报告 Active 的 profile SHALL 直接进入接管路径，不消费、刷新或等待代理预检结果。

当用户对单个 Inactive 环境明确点击“启动”时，客户端 SHALL 在进入普通启动或待机唤醒分支前作废该环境此前已经完成的确定成功或失败结果，并 SHALL 以本次点击触发的新检测结果裁决本次启动。若点击时该环境已有真实检测在途，客户端 SHALL 等待并复用该单飞结果，MUST NOT 取消旧请求后产生可被其他启动路径当作“无法确认”消费的 `superseded` 结果。同一次手动启动内部重复执行网络准备时 SHALL 复用该次首次取得或等待的结果，MUST NOT 因入口强制刷新而重复探测。

新鲜确定失败 SHALL 停止本次新浏览器启动或唤醒并如实显示代理原因。无法读取 AdsPower 环境代理配置或检测设施自身异常 SHALL 表示“无法确认”，MUST NOT 冒充代理失效，也 MUST NOT 成为绕开既有新浏览器启动行为的新单点阻断。profile 明确配置为无代理时 SHALL 视为双跳不适用，跳过中继与代理预检并保持既有无代理启动行为。用户显式开启系统前置代理模式且 Inactive profile 已配置环境代理后，系统代理缺失、不受支持或中继无法建立 SHALL 表示确定的双跳配置不可用，并阻止本次新浏览器启动，MUST NOT 沿用单跳行为。客户端内修改代理配置或双跳开关后 SHALL 立即作废旧结果和旧链路。

#### Scenario: 单环境手动启动绕过新鲜失败
- **GIVEN** 一个 Inactive Facebook 环境最近一次确定预检失败仍在缓存有效期内
- **WHEN** 用户对该环境明确点击“启动”
- **THEN** 客户端 SHALL 作废旧失败并实际发起一次新的代理检测
- **AND** 本次启动 SHALL 只按新检测结果继续或失败

#### Scenario: 单环境手动启动绕过新鲜成功
- **GIVEN** 一个 Inactive Facebook 环境最近一次确定预检成功仍在缓存有效期内
- **WHEN** 用户对该环境明确点击“启动”
- **THEN** 客户端 SHALL 重新检测，MUST NOT 以点击前的成功结果直接启动浏览器

#### Scenario: 点击时已有真实检测在途
- **GIVEN** 环境选择预热发起的代理检测在用户点击“启动”时仍未完成
- **WHEN** 手动启动进入代理准备
- **THEN** 客户端 SHALL 等待并复用该环境的同一在途检测
- **AND** MUST NOT 取消它、产生 `superseded` 未知结果或并发发起第二次检测

#### Scenario: 同一次手动启动内部复用新结果
- **WHEN** 一次单环境手动启动在前置准备与真正 spawn 前重复确认网络
- **THEN** 第一次确认 SHALL 发起新检测或等待点击时已经在途的真实检测
- **AND** 后续确认 SHALL 复用该次结果，不得再次探测

#### Scenario: 启动消费选择时的成功结果
- **WHEN** 用户选中 Inactive 环境后完成代理检测，并在结果有效期内通过批量启动或非单环境显式重试路径启动
- **THEN** 启动流程直接复用结果，不重复请求代理检测，随后沿用既有新浏览器启动流程

#### Scenario: 自动唤醒缺少结果
- **WHEN** 冷待机 Facebook 环境因系统任务自动唤醒、AdsPower profile 为 Inactive 且没有新鲜结果
- **THEN** 客户端在申请浏览器槽位前检测一次，成功后继续既有唤醒流程

#### Scenario: 确定失败不启动新浏览器
- **WHEN** Inactive profile 的检测确认代理类型、认证或连通性失败
- **THEN** 本次启动或唤醒失败，浏览器不被新建，并复用既有启动或冷待机失败处理，不新增代理专用重试定时器

#### Scenario: Active profile bypasses preflight
- **WHEN** AdsPower 报告目标 profile 已经 Active
- **THEN** 客户端直接接管该浏览器，不读取、刷新、等待或以任何代理预检结果阻止接管

#### Scenario: 检测设施未知不误杀新启动
- **WHEN** 双跳未开启且 Inactive profile 的 AdsPower 配置读取或检测设施本身不可用，因而无法判断环境代理
- **THEN** 客户端显示无法确认并沿用既有新浏览器启动行为，MUST NOT 显示代理无效

#### Scenario: 显式双跳配置不可用时阻止新启动
- **WHEN** 双跳已开启、Inactive profile 已配置环境代理，但系统代理无法解析或受管中继无法建立
- **THEN** 客户端显示对应双跳原因并阻止新浏览器启动，MUST NOT 直接连接环境代理或目标网站

#### Scenario: 无环境代理时不进入双跳检测
- **WHEN** 双跳开关已开启，但 Inactive profile 明确未配置代理
- **THEN** 客户端跳过系统代理解析、中继和 Facebook 代理预检，并按既有无代理路径继续启动

### Requirement: 预检状态 SHALL 与浏览器出口证据分离
客户端 SHALL 以独立安全投影展示代理配置和 Facebook 可达性预检状态。预检成功 SHALL 显示“代理可用”及检测时间，但 MUST NOT 显示“代理已验证”、浏览器实际出口、本机直连出口或任何推断的运行时代理结论。Active 浏览器直接接管且未运行预检时，客户端 MUST NOT 伪造一个成功预检。

#### Scenario: 离线环境预检成功
- **WHEN** Inactive 环境的代理预检成功
- **THEN** 代理入口显示“代理可用”及检测时间，不显示浏览器或本机公网出口

#### Scenario: Active 浏览器直接接管
- **WHEN** 同一环境已经 Active 并被客户端直接接管
- **THEN** 界面显示真实浏览器运行状态和已有代理配置摘要
- **AND** MUST NOT 因浏览器已运行而显示“代理已验证”或构造公网出口证据

### Requirement: Proxy preflight SHALL bind one Cloud authority revision
For an Inactive environment AdsPower reports as proxy-configured, Edge SHALL fetch the exact Cloud proxy authority before preflight and freeze its revision and configuration for the resulting fresh-start attempt. The local system-upstream switch SHALL choose either the original Cloud proxy or a GOST loopback whose second hop is that same original proxy. Preflight SHALL test anonymous Facebook reachability through that effective route and SHALL NOT probe or retain public egress. Environments AdsPower reports Active SHALL bypass Cloud proxy-authority resolution, proxy preflight, and proxy mutation. Environments AdsPower or Cloud explicitly report as `no_proxy` SHALL skip those same proxy operations when a fresh start is required.

#### Scenario: Direct mode tests the Cloud original proxy
- **WHEN** the Inactive environment has a configured Cloud proxy and system-upstream mode is disabled
- **THEN** preflight SHALL test Facebook reachability through the frozen original proxy directly
- **AND** SHALL NOT call a public-egress detector or retain an expected egress IP

#### Scenario: Double-hop mode tests the generated loopback
- **WHEN** the Inactive environment has a configured Cloud proxy and system-upstream mode is enabled
- **THEN** Edge SHALL construct the GOST chain from the local system proxy to the frozen Cloud original proxy
- **AND** preflight SHALL test Facebook reachability through the generated loopback endpoint without public-egress probing

#### Scenario: Active environment bypasses authority and preflight
- **WHEN** AdsPower reports the environment Active
- **THEN** Edge SHALL attach without resolving Cloud authority, starting GOST, probing reachability or public egress, or mutating the profile

#### Scenario: No-proxy Inactive environment bypasses proxy gates
- **WHEN** AdsPower or Cloud authority is explicit `no_proxy` and the environment is Inactive
- **THEN** Edge SHALL not require a second hop, start GOST, or block startup on proxy preflight

#### Scenario: Cloud is unavailable for an Inactive configured environment
- **WHEN** Edge cannot resolve a required Cloud authority revision before a fresh start
- **THEN** preflight and managed fresh startup SHALL fail closed with an authority-unavailable result
- **AND** SHALL NOT reuse AdsPower's current proxy as the original

