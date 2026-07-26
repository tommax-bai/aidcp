## Why

部分客户网络只能先经过 macOS 系统代理/VPN 出口，才能连接 AdsPower 环境配置的住宅代理；现有 Edge 代理预检和 AdsPower 浏览器都会直接连接环境代理，导致系统代理模式下连接被复位，而 TUN 模式才能工作。客户端需要一个显式、可验证且不静默直连的双跳模式，让同一环境按“系统代理 → 环境代理”访问目标网站。

## What Changes

- 在 AdsPower 浏览器设置中增加一个默认关闭的全局开关“系统代理作为前置跳板”，并明确展示关闭时“环境代理 → 目标网站”、打开时“系统代理 → 环境代理 → 目标网站”。
- 首版在 macOS 读取固定 HTTP CONNECT 或 SOCKS5 系统代理；PAC、无代理、系统代理返回直连或无法解析时如实拒绝双跳启动，不回退直连。
- Edge 管理仅监听 loopback 的本地代理中继，把系统代理和目标 AdsPower profile 的环境代理组成两跳链路；环境代理凭据不得进入命令行、设置、renderer 状态或日志。
- Facebook 启动前代理预检与 AdsPower 浏览器使用同一条本地代理链，避免“预检直连失败、浏览器另走链路”的分裂状态。
- AdsPower 启动只在本次浏览器进程注入本地代理覆盖，不永久改写 profile 已保存的环境代理；若 AdsPower 无法证明接受该覆盖，首版必须停止在明确失败，不得转为不具备崩溃恢复的临时 profile 改写。
- 运行中环境切换此开关需要重启浏览器代际；已经由其他入口打开且未应用双跳参数的浏览器不得冒充双跳已生效。
- 增加中继生命周期、端口隔离、失败分类、浏览器出口证据和打包资源边界的回归验证。

## Capabilities

### New Capabilities

- `system-upstream-proxy-chain`: 定义客户端双跳开关、macOS 系统代理解析、受管 loopback 中继、生命周期、安全边界和诚实失败语义。

### Modified Capabilities

- `facebook-proxy-preflight`: 开启双跳时，启动前预检必须通过与浏览器相同的受管中继；明确缺失或不支持的系统前置代理成为可解释的启动阻断。
- `pluggable-browser-provider`: AdsPower provider 启动新浏览器代际时可接收受管本地代理覆盖，并拒绝把未应用覆盖的既有浏览器当作双跳环境接管。

## Impact

- 所属实现仓：`aidcp-edge`。
- 主要影响 Electron 主进程设置/状态、renderer 浏览器设置、代理预检、AdsPower provider 启动参数和本地 sidecar 生命周期。
- 增加一个固定版本、校验来源并随桌面资源交付的代理中继二进制，以及开发态显式路径解析；不把代理凭据写入 argv 或持久化设置。
- 不改变 Cloud、Console、协议 v2、数据库、账号风险状态或 AdsPower profile 的持久代理配置。
- 源码完成不等于安装包已交付；签名、公证、安装包和客户真机验证保持独立验收边界。
