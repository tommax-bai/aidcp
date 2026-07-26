## Why

部分客户网络只能先经过 macOS 系统代理/VPN 出口，才能连接 AdsPower 环境配置的住宅代理；现有 Edge 代理预检和 AdsPower 浏览器都会直接连接环境代理，导致系统代理模式下连接被复位，而 TUN 模式才能工作。客户端需要一个显式、可验证且不静默直连的双跳模式，让同一环境按“系统代理 → 环境代理”访问目标网站。

## What Changes

- 在 AdsPower 浏览器设置中增加一个默认关闭的全局开关“系统代理作为前置跳板”；该开关只作用于已配置环境代理的 profile，未配置代理的 profile 保持既有无代理启动行为。界面明确展示关闭时“环境代理 → 目标网站”、实际适用时“系统代理 → 环境代理 → 目标网站”。
- 首版在 macOS 读取固定 HTTP CONNECT 或 SOCKS5 系统代理；PAC、无代理、系统代理返回直连或无法解析时如实拒绝双跳启动，不回退直连。
- Edge 管理仅监听 loopback 的本地代理中继，把系统代理和目标 AdsPower profile 的环境代理组成两跳链路；环境代理凭据不得进入命令行、设置、renderer 状态或日志。
- Facebook 启动前代理预检与 AdsPower 浏览器使用同一条本地代理链，避免“预检直连失败、浏览器另走链路”的分裂状态。
- AIDCP 把用户输入的环境代理作为本地加密权威保存；创建环境时仍把该原始代理写给 AdsPower，不以本地中继替换创建参数。
- 每次 AdsPower 实际启动新浏览器代际前，AIDCP 按当前开关把 profile 代理同步为原环境代理或受管 GOST loopback，并在读回一致后才启动。浏览器确认关闭后尽力恢复原环境代理；恢复只是兜底，下一次启动前同步才是一致性保证。
- AdsPower profile 是浏览器启动时唯一代理权威；不再同时注入 `--proxy-server`。已配置代理但不能完成同步或读回验证时明确拒绝启动；未配置代理的环境不保存代理权威、不更新 profile，也不进入双跳限制。
- 运行中环境切换此开关需要重启浏览器代际；已经由其他入口打开且未应用双跳参数的浏览器不得冒充双跳已生效。
- 增加中继生命周期、端口隔离、失败分类、浏览器出口证据和打包资源边界的回归验证。
- 修复 macOS Developer ID 签名会改变嵌套 Mach-O 完整文件哈希的问题：开发态继续校验原始 SHA-256，签名安装包改为校验固定资源路径、Developer ID/Team ID/Identifier、架构和版本，并在签名完成后阻止不可运行产物继续出包。

## Capabilities

### New Capabilities

- `system-upstream-proxy-chain`: 定义客户端双跳开关、macOS 系统代理解析、受管 loopback 中继、生命周期、安全边界和诚实失败语义。

### Modified Capabilities

- `facebook-proxy-preflight`: 预检从 AIDCP 加密保存的原环境代理建立链路；开启双跳时必须通过与浏览器 profile 同步到的同一受管中继。
- `pluggable-browser-provider`: AdsPower provider 在每次新浏览器代际启动前更新并读回 profile 代理，关闭后尽力恢复原环境代理，并拒绝接管无法证明当前代理代际的既有浏览器。

## Impact

- 所属实现仓：`aidcp-edge`。
- 主要影响 Electron 主进程设置/状态、renderer 浏览器设置、代理权威加密存储、代理预检、AdsPower provider 启动/关闭生命周期和本地 sidecar 生命周期。
- 增加一个固定版本、校验来源并随桌面资源交付的代理中继二进制，以及开发态显式路径解析；代理凭据只进入 Electron `safeStorage` 加密记录、主进程/子进程私有管道和 GOST stdin，不进入 argv、环境变量、通用设置、renderer 状态或日志。
- AdsPower profile 的代理配置会在浏览器代际边界受控更新，并在确认关闭后尽力恢复；不改变 Cloud、Console、协议 v2、数据库或账号风险状态。
- 源码完成不等于安装包已交付；签名、公证、安装包和客户真机验证保持独立验收边界。
