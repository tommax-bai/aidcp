## Context

现有 Facebook 代理运行证据由核心在 AdsPower 浏览器建立后通过 CDP 采集，属于浏览器代际观测，不阻止身份读取或自动化。Electron 主进程已经通过 AdsPower Local API 管理 profile；`user/list` 的原始 `user_proxy_config` 在本机可包含认证信息，但 `normalizeProfile` 有意在 IPC 前移除密码。

本变更只提前发现“配置类型不对、认证失败、代理不可达”等确定失败，不替代现有浏览器实际出口证据，也不改变浏览器槽位或冷待机重试策略。

## Goals / Non-Goals

**Goals:**
- 选择离线 Facebook 环境后，在用户点击启动前完成一次后台代理检测。
- 手动启动和冷待机唤醒复用短时结果，缺失或过期时只补做一次。
- 全程不把代理密码送入 renderer、日志或持久化状态。
- 只把确定的代理检测失败作为本次浏览器启动/唤醒失败；检测设施未知保持诚实且不造成新单点阻断。

**Non-Goals:**
- 不把预检结果称为浏览器实际出口已验证。
- 不要求每代浏览器在访问 Facebook 前同步等待额外出口探测。
- 不新增代理专用重试时间表、浏览器重启循环或持久化检测台账。
- 不修改 Cloud、边云协议、任务授权或客户 HTTP 数据面。

## Decisions

### 主进程按 profile 读取完整配置

为 `ads-local-api.cjs` 增加只供主进程调用的精确 profile 代理读取方法。方法使用既有 Local API base、鉴权与 1 req/s 串行节流，返回单个 `user_proxy_config` 给 Electron 主进程；现有 `listProfiles` IPC 继续只返回非密摘要。

不新增密码存储。配置只在一次调用栈和一次网络探测中存在，结果只保留状态与时间。

### 以无身份 Facebook 请求做一次真实代理连通测试

检测使用 AdsPower 配置的 HTTP、HTTPS 或 SOCKS5 代理请求 `https://www.facebook.com/`，不携带 Cookie、环境 id、账号 id 或业务正文。使用成熟的 HTTP(S)/SOCKS Agent 库，避免在产品代码内实现代理握手；请求使用 `HEAD`、禁止复用并设置有界超时。

任何 HTTP 响应都证明代理链路和 Facebook TLS 已建立；代理认证、TLS、连接拒绝或超时属于确定失败。无法读取 AdsPower 配置或检测器内部不可用属于未知，不冒充代理失效。

### 每环境内存单飞和短时复用

每个 `EnvHandle` 只持有公开预检快照、当前 Promise 和最近结果，成功或确定失败结果有效 2 分钟。结果不落 settings；代理配置经客户端保存修改后立即作废。环境快速切换使用一个短延迟选择定时器，只有最终选中的离线 Facebook 环境发起检测，避免冲击 AdsPower 1 req/s 限流。

### 复用现有启动与唤醒失败路径

完整冷启动在现有 AdsPower runtime/kernel 准备完成后消费预检：新鲜成功直接继续，新鲜失败停止本次启动，缺失或过期等待一次检测，未知则沿用既有启动行为。

冷待机唤醒在申请浏览器槽位前执行同样判断。确定失败交给现有 `onColdStandbyWakeFailed`，由既有待机状态与退避机制处理；本变更不增加任何重试定时器。

### 预检状态不污染浏览器出口证据

fleet 状态新增独立、无敏感字段的 `proxyPreflight` 投影。renderer 仅在浏览器运行证据缺失或过期时用它显示“检测中 / 代理可用 / 代理不可用 / 无法确认”；一旦浏览器运行证据存在，仍以原有 `proxyRuntime` 为权威。

## Risks / Trade-offs

- [风险] 代理在 2 分钟有效期内失效 → 仍由现有浏览器启动错误和非阻塞出口观察诚实暴露；不为缩短这个窗口增加持续轮询。
- [风险] AdsPower Local API 暂不可用 → 标记无法确认并沿用既有启动，不把检测设施故障误判为代理故障。
- [风险] 预检请求增加少量外部流量 → 仅选中离线 Facebook 环境或启动结果缺失/过期时执行一次 `HEAD`，无循环检测。
- [风险] 新 Agent 依赖进入桌面包 → 锁定直接生产依赖，运行聚焦测试、typecheck 与桌面构建输入校验；本次不制作安装包。
