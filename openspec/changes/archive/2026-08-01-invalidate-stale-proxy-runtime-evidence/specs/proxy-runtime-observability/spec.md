## MODIFIED Requirements

### Requirement: 指纹浏览器出口证据必须来自该浏览器网络上下文

Edge SHALL 在每一代 AdsPower Facebook 浏览器启动或冷待机唤醒后，通过当前受管 page 的 CDP Network 上下文向受控回显端点发起禁止缓存且不携带凭据的探测，并取得浏览器实际来源 IP；MUST NOT 由 Electron 或 Node 请求结果冒充浏览器出口。探测请求 MUST NOT 携带账号 id、环境 id、Cookie 或业务正文。浏览器出口证据 SHALL 只在产生它的浏览器/core 代际仍存活时视为当前证据；该代际结束后 MUST 立即失效，MUST NOT 继续投影为“已验证”、沿用旧出口或保留旧会话流量。

#### Scenario: 浏览器出口与本机出口不同则验证成立
- **WHEN** 当前 Facebook page 的 CDP 探测和 Edge Node 直连探测均成功，且两者返回不同的规范化公网 IP
- **THEN** Edge 将当前浏览器代际标为“已验证”，并保留浏览器出口、本机出口和检测时间作为当前内存证据

#### Scenario: 浏览器出口与本机出口相同则疑似直连
- **WHEN** 两条探测均成功且返回相同的规范化公网 IP
- **THEN** Edge 将状态标为“疑似直连”，MUST NOT 因 AdsPower 中存在代理配置而显示“已验证”

#### Scenario: 浏览器探测不支持或失败时诚实降级
- **WHEN** CDP 命令不受支持、端点不可达、超时或响应缺少可验证来源 IP
- **THEN** Edge 显示“无法确认”或“待验证”，MUST NOT 回退使用 Node 结果冒充浏览器证据，且首版不因此自动停止环境

#### Scenario: 新浏览器代际使旧证据失效
- **WHEN** 环境重新启动浏览器或从冷待机唤醒而形成新浏览器代际
- **THEN** Edge 立即清空本次会话接收流量、使旧出口证据失效并异步重新探测；同一代际内的普通 CDP 重连 MUST NOT 重置累计值

#### Scenario: 核心或浏览器代际结束使证据失效
- **WHEN** 产生运行证据的 Edge 核心退出，或其受管浏览器被确认关闭
- **THEN** 客户端立即把该代际运行证据标为失效，清除浏览器出口、本机出口、检测时间和会话流量，且未启动环境 MUST NOT 继续显示“代理已验证”

#### Scenario: 替换代际在 spawn 前失败
- **WHEN** 已无存活浏览器代际的环境开始新一轮启动，但在运行时、内核或代理预检阶段失败而未 spawn 新核心
- **THEN** 上一代运行证据保持失效，本次预检可按自身状态展示，MUST NOT 被旧的“代理已验证”遮蔽
