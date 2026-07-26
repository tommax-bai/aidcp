## Context

当前 Electron 主进程会精确读取 AdsPower profile 保存的代理，并在浏览器启动前用 `https-proxy-agent` / `socks-proxy-agent` 直接请求 Facebook。通过后才 spawn Edge 核心；核心中的 `AdsPowerProvider` 再调用 `browser-profile/start`，让 AdsPower 浏览器使用 profile 自身代理。macOS“系统代理”只是应用层配置，Node Agent 和 AdsPower 已显式代理连接都不会自动把它作为上游，所以客户即使开启 Veee Global Mode，两个直接连接仍可能被网络复位。

首版只解决已观察到的 macOS 固定本地系统代理场景。它必须同时改变预检和浏览器数据面，又不能持久改写 AdsPower profile、泄露第二跳凭据或在失败时退回真实本机出口。

## Goals / Non-Goals

**Goals:**

- 提供默认关闭、可理解、需要重启生效的全局双跳开关。
- 在 macOS 把固定 HTTP CONNECT/SOCKS5 系统代理与每个 profile 的 HTTP/HTTPS/SOCKS5 环境代理组成完整链路。
- 让 Facebook 预检和 AdsPower 新浏览器代际使用同一 loopback 中继。
- 保持环境代理凭据仅在主进程和中继私有配置内短暂存在。
- 以浏览器实际出口证据验证最终结果，诚实区分配置、链路和浏览器证据。
- 为开发态和打包态提供来源固定、可校验的 GOST v3 sidecar 解析路径。

**Non-Goals:**

- 首版不支持 PAC/WPAD、系统代理认证、Windows/Linux 或任意 Network Extension/TUN。
- 不改变 AdsPower profile 的持久代理配置，不提供崩溃后恢复这种持久改写所需的台账。
- 不支持运行中浏览器热切换代理，也不接管无法证明启动参数的既有 active profile。
- 不改变 Cloud、协议 v2、数据库、风险状态或出口回显端点。
- 不把源码完成等同于签名安装包或客户真机验收。

## Decisions

1. **设置是机器级显式能力，不是每环境隐藏规则。** 新设置使用布尔值 `systemProxyUpstreamEnabled`，缺省 `false`，放在 AdsPower 浏览器设置中。系统代理是机器级资源，而第二跳仍来自每个 profile；首版不引入环境级覆盖矩阵。开关选择立即持久化，使未启动环境随后的后台预检使用当前可见选择并立即作废旧证据；只有读取到该 profile 已配置环境代理时，开关才对它启用双跳。未配置环境代理不是“双跳缺失”的错误，而是双跳不适用，保持既有无代理启动参数。已经运行的浏览器代际冻结其实际模式，界面继续要求显式重启，避免把持久化目标设置冒充成运行中 Chrome 的热切换。

2. **AIDCP 读取系统配置，再显式生成代理链。** 新的 macOS resolver 通过有界 `scutil --proxy` 读取固定端点，按 SOCKS5、HTTPS web proxy、HTTP web proxy 的顺序选择。HTTPS web proxy 在 macOS/Chromium 语义中仍是 HTTP CONNECT，不能写成 GOST 的 TLS dialer。PAC/WPAD 需要按目标 URL 执行系统 PAC 解析，首版若猜固定值会违背“系统代理”语义，因此明确不支持。

3. **使用固定版本 GOST sidecar，而不是 Proxifier/自研透明代理。** GOST 原生支持多 hop 和 HTTP/SOCKS/TLS 组合，MIT 许可允许随应用交付。Proxifier 是商业 Network Extension，需要额外安装、许可和进程规则，不适合作为产品内依赖；自研 CONNECT/SOCKS 链会重新承担协议、认证、背压和错误处理风险。构建脚本下载固定 v3.2.6 release，校验官方 SHA-256 后解包到架构目录；打包从 `${platform}-${arch}` 资源目录取二进制。开发态允许 `AIDCP_GOST_BINARY`，其次使用已 stage 的构建产物；打包态忽略外部覆盖并只信任资源内二进制。macOS Developer ID 会向嵌套 Mach-O 写入签名数据，因此开发态/staging/`afterPack` 继续校验签名前完整 SHA-256，签名包运行态改为校验固定资源路径、App 与嵌套二进制的有效 Developer ID 签名、相同且固定的 Team ID、预期 Identifier、目标架构，并仅在上述信任成立后执行 `gost -V` 校验版本。Native Page Engine 使用同一签名产物规则，避免 GOST 修复后被同源签名前哈希校验阻断。

4. **每个正在准备的 profile 使用独立中继进程。** 中继只监听 `127.0.0.1` 随机可用端口，配置包含系统 hop 和该 profile 环境 hop。独立进程让凭据和故障域按环境隔离，首版受浏览器槽位限制，进程数量可控。主进程按 profile 单飞创建并缓存；profile 代理或系统模式改变时作废。应用退出时有界终止全部中继。为避免浏览器尚在使用时断链，普通 Edge 子进程退出不立即杀中继；只有配置作废、确认不再使用或应用退出才回收。

5. **敏感配置从 stdin 进入 GOST。** GOST 以 `-C -` 从 stdin 读取 YAML/JSON，argv 只包含固定参数。主进程不打印配置和 stderr 原文，只投影稳定错误枚举；renderer 只获得 `direct` / `system_then_environment`、准备状态和安全提示。二进制路径和 loopback 端口可以记录，用户名、密码和完整节点 URL 不可以。

6. **预检先确认第二跳存在，再建立链并把本地端点作为唯一代理。** 现有精确 profile reader 继续作为第二跳真源。双跳关闭时控制器保持原行为；打开且 profile 已配置环境代理时，reader 交给 chain manager，成功后返回无认证的本地 HTTP 代理配置，后续现有预检逻辑不再知道第二跳凭据。profile 明确返回无代理时跳过中继与代理预检，并按既有无代理路径启动；只有适用双跳的 profile 遇到系统代理/sidecar 显式配置失败时才映射为 `unavailable` 并阻止启动。双跳关闭时既有“检测设施 unknown 不阻断”语义保持不变。

7. **主进程把本地端点注入 Edge 子进程，provider 只负责本次启动覆盖。** `spawnEdgeChild` 在成功预检后从 chain manager 取得当前 profile endpoint，注入非敏感 `AIDCP_ADS_PROXY_OVERRIDE`。`selectBrowserProvider` 校验它必须是 `http://127.0.0.1:<port>`，并把 `--proxy-server=<url>` 加入 `browser-profile/start.launch_args`。AdsPower 官方 start API没有临时 proxy object，只提供 `launch_args`；因此不永久调用 profile update。

8. **active profile 在双跳模式下 fail closed。** 当前 provider 会接管 AdsPower 已 active 的 profile，但这种浏览器可能由手工入口或旧设置启动，无法证明应用了当前 loopback 参数。首版在存在 override 时拒绝 active 接管，要求关闭重启。若后续能取得可信启动命令行并精确匹配，可另案放宽。

9. **验收分三层。** 单元/契约测试证明解析、配置生成、凭据脱敏、生命周期与启动载荷；开发态集成测试用本地固定系统代理和无账号目标证明 GOST 两跳；AdsPower 真机测试必须从新 inactive profile 启动，并由既有 CDP 出口探测证明最终业务代理出口。打包资源、签名公证和客户安装包另行验收，源码测试不能替代。Electron `afterSign` 必须对每个最终 `.app` 执行嵌套签名身份、架构与版本检查；发行脚本在公证/装订后重复最终信任门禁，防止只通过签名前 `afterPack` 的不可运行产物进入 DMG。

## Risks / Trade-offs

- [AdsPower 内核或代理扩展覆盖 `--proxy-server`] → 以新 inactive profile 做浏览器级出口验证；未证明前不标完成，不回退持久改 profile。
- [抢占随机 loopback 端口] → 分配后立即 spawn，并以有界 TCP 就绪探测确认；失败返回稳定错误，不换成 `0.0.0.0`。
- [Veee 改变本地端口或断开] → 每次新建链重新解析；已建连接失败时不直连，界面显示链路不可用。首版不增加未经观察的后台重试器。
- [GOST 二进制供应链或打包签名] → 固定 release、架构和签名前 SHA-256；构建缺失即失败；正式包把嵌套二进制纳入 codesign、notarization 和签名后身份/版本检查，不把签名前完整文件哈希错误地用于已签名 Mach-O。
- [多个 sidecar 增加资源占用] → 首版按 profile/浏览器槽位有界，换取简单隔离；有真实资源证据后再考虑合并为单进程多 service。
- [本地其他进程访问无认证 relay] → 仅 loopback、随机端口、只在需要时存活；不把端口暴露到 renderer 或 Cloud。若后续威胁模型要求同用户进程隔离，需要原生 socket 身份或本地认证另案。

## Migration Plan

1. 合入设置与解析/中继代码，但开关默认关闭，现有环境零迁移。
2. 在开发态显式 stage GOST，并用测试 profile 验证 `--proxy-server`、完整预检和浏览器出口。
3. 验证通过后才把 GOST 资源 staging 接入桌面构建；源代码和打包产物分别记录验证。
4. 回滚时关闭开关即可恢复直接环境代理；移除代码时无需恢复 AdsPower profile 或迁移数据，因为首版不写其持久代理。

## Open Questions

- AdsPower 当前随包内核及其代理扩展是否始终尊重 API `launch_args` 传入的 `--proxy-server`？这是首版真机验收门，若失败则本 change 暂停，持久 profile 改写必须另行设计事务与崩溃恢复后才能采用。
