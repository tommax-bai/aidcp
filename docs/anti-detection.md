# AIDCP 反检测与登录态维持方案

> 适用范围：aidcp 在小红书（XHS）场景下，基于 **Chrome + CDP 原生（--remote-debugging-port，
> 非 Playwright）** 的自动化。早期实现无任何反检测措施；**现已部分落地**（见下方实现状态框）。
> 本文给出从"立即止血"到"规模化"的完整反检测与登录态维持
> 方案，目标是：**让 CDP 驱动的浏览器在指纹、网络、行为三个层面都不可被识别为机器**。
>
> 配套文档：[风控模型设计](risk-control.md)。两者关系：风控文档管"做什么、做多少、
> 什么时候做"（频率/作息/状态机），本文管"怎么做才不被识别"（指纹/网络/行为拟人化的
> 技术实现）。两者必须同时落地——只有干净指纹但行为机械，或行为拟人但指纹暴露，
> 都会被风控。
>
> **实现状态（2026-06）**：分层落地。**已实装**：行为拟人化 `aidcp-edge/src/humanize/`
> （对数正态停顿 / 贝塞尔鼠标 / 键盘节奏 / 滚动物理 / 会话疲劳曲线）、stealth 注入
> `aidcp-edge/src/cdp/stealth-injector.ts`、`--user-data-dir` profile 隔离（Cookie/登录态基础持久化）、
> 反自动化启动参数（`--disable-blink-features=AutomationControlled` 等）。**仍待实装**：住宅代理 + IP
> 粘性、指纹画像表与 UA 管理、WebRTC/DNS 防泄露、Cookie 加密存储跨重启、指纹浏览器集成。
> 下文路线图 Phase 1–2 主体已完成。

---

## 0. 威胁模型：小红书在用什么手段检测自动化

XHS 的检测分三层，本文逐层对抗：

| 层 | 检测手段（已知/业界推断） | 本文对应章节 |
| --- | --- | --- |
| **浏览器/运行时指纹** | `navigator.webdriver`、CDP 协议特征、Canvas/WebGL 指纹、UA 与平台一致性、屏幕/字体/时区、Headless 残留特征 | §1、§4 |
| **网络/设备** | IP 信誉（机房 IP 黑名单）、IP 与账号绑定、DNS/WebRTC 真实 IP 泄露、设备指纹（XHS Web 与 App 都有设备 ID） | §2 |
| **行为** | 鼠标轨迹、键盘节奏、滚动模式、停留分布、操作序列规整度、24h 不间断 | §5（+ 风控文档 §3） |
| **登录态** | Cookie/Session 异常、登录设备突变、登录态与历史行为不一致 | §3 |

> 公开经验（Bright Data / puppeteer-extra-stealth 文档、r/webscraping 等）一致指出：
> **没有任何单一手段能"绕过一切检测"**，反检测是"持续把检测成本抬高"的工程，而非
> 一次性开关。因此本文强调**分层 + 一致性 + 路线图**，而不是堆插件。

---

## 1. 浏览器指纹防护

### 1.1 CDP / WebDriver 特征对抗

CDP 原生方案的"原罪"：连上 `--remote-debugging-port` 后，页面侧能感知到若干自动化
特征。必须在每个新 document 注入前清除。

| 暴露点 | 表现 | 对抗 |
| --- | --- | --- |
| `navigator.webdriver` | 自动化时为 `true` | 用 `Page.addScriptToEvaluateOnNewDocument` 注入脚本，`Object.defineProperty(navigator,'webdriver',{get:()=>undefined})`；或启动参数 `--disable-blink-features=AutomationControlled` |
| `Runtime.enable` 指纹 | 启用 Runtime 域会触发可被检测的 `console` 行为（见 §4.2） | 避免无谓 `Runtime.enable`；必要时用 isolated world 执行，不在主世界留痕 |
| `window.cdc_*` / `$cdc_` | ChromeDriver 注入变量（Selenium 残留） | CDP 原生方案本身没有，但要确保不引入相关库 |
| 自动化扩展/标志 | `--enable-automation` 导致 UA 带 `HeadlessChrome`、出现"Chrome 正受到自动测试软件的控制"提示 | 启动参数去掉 `--enable-automation`，加 `--disable-infobars`/`excludeSwitches` 等价处理 |

> 关键：注入必须用 **`Page.addScriptToEvaluateOnNewDocument`**（CDP 原生支持），保证
> 在页面任何脚本之前执行，避免被"先读后改"识破。aidcp 现有 `CdpClient`（`src/cdp/client.ts`）
> 已是原生 WebSocket RPC；已落地的 `StealthInjector`（`src/cdp/stealth-injector.ts`）在每个
> target attach 后由 `attachToPage`（`src/cdp/session.ts`）调用注入。

### 1.2 Canvas / WebGL 指纹一致性

XHS 会采集 Canvas/WebGL 指纹做设备识别。两种思路，**二选一并保持稳定**：

- **方案 A（推荐 MVP）：真实暴露 + 保持一致**。不加噪、不伪造，让指纹等于真实
  Chrome 的指纹。前提是**一机一号**（§2.2）——指纹真实且与 IP/账号绑定，反而最安全。
- **方案 B（多账号同机）：稳定加噪**。对 `toDataURL` / `getImageData` / WebGL
  `readPixels` 注入**每账号固定的微小扰动**（seed 由账号 ID 派生），保证**同一账号
  每次访问指纹一致**。最忌讳"每次随机"——指纹漂移本身就是机器信号。

> WebGL 还需保证 `UNMASKED_VENDOR_WEBGL` / `UNMASKED_RENDERER_WEBGL`（显卡厂商/型号）
> 与 UA 声称的平台自洽（见 §1.5）。

### 1.3 User-Agent 管理

- UA 必须**真实且与浏览器版本、OS 平台、显卡完全自洽**：UA 里写 Windows，则
  `navigator.platform`、时区、字体、WebGL renderer 都应是 Windows 的。
- 不要用过旧或罕见 UA；跟随真实 Chrome 大版本。
- 一个账号绑定一个 UA，**长期稳定**；不要每次启动换 UA（UA 频繁变更=可疑）。
- 同步处理 **Client Hints**（`sec-ch-ua`、`sec-ch-ua-platform` 等），新版检测越来越依赖
  CH 而非 UA 字符串；CH 与 UA 不一致是明显破绽。

### 1.4 屏幕分辨率 / 字体 / 时区一致性

| 维度 | 要求 |
| --- | --- |
| 分辨率 / `devicePixelRatio` | 用常见真实组合（如 1920×1080@1.0、2560×1440），且 `window.outerHeight/innerHeight`、`availWidth` 等自洽（headful 下浏览器有真实窗口，比 headless 更可信） |
| 字体列表 | 与 OS 平台匹配（Windows 有微软雅黑/宋体等）；不要出现 Linux 字体却声称 Windows |
| 时区 / 语言 | `Intl.DateTimeFormat().resolvedOptions().timeZone`、`navigator.language` 与 IP 地理位置一致（中国大陆 IP 应为 `Asia/Shanghai` + `zh-CN`）——**时区/IP 错配是住宅代理最常见的翻车点** |

### 1.5 一致性是第一原则

指纹防护的核心不是"伪造得多像"，而是**各维度互相自洽**。检测方往往不是看单个值
是否异常，而是看**组合是否矛盾**（UA=Mac 但字体=Windows、IP=上海但时区=UTC）。
建议建立一张**"设备画像表"**，把 UA/平台/分辨率/字体/时区/语言/WebGL 锁成一套，
按账号绑定、长期不变。

### 1.6 App 端 vs Web 端

- **Web 端**：上述指纹手段适用；XHS Web 功能受限（部分操作需登录、风控更严）。
- **App 端**：检测更强（设备指纹、设备 ID、root/越狱检测、Frida/Hook 检测、证书
  绑定），CDP 方案不适用，需要群控/真机/模拟器改机方案，成本与维护量都高一个量级。
- **建议**：aidcp 当前 CDP 架构**聚焦 Web 端**；App 端自动化不在本方案范围，若必须，
  应单独评估真机群控，而非用 Web 思路硬套。

---

## 2. 网络层

### 2.1 代理 IP 方案：住宅 vs 数据中心

| 类型 | 信誉 | 成本 | 适用 |
| --- | --- | --- | --- |
| **数据中心代理** | 低（IP 段已被大量标记，XHS 易识别） | 低 | **不推荐**用于账号互动；仅可用于无登录的纯采集 |
| **住宅代理（Residential）** | 高（真实家庭宽带 IP） | 高（按流量计） | **推荐**，账号互动/发布必须用 |
| **静态住宅 / 独享住宅** | 最高（固定、独享、不漂移） | 最高 | 规模化时为高价值账号配置，做到 IP 长期稳定 |

> 原则：**互动账号必须走住宅代理**；机房 IP 跑 XHS 互动几乎等于自首。优先**国内住宅
> 代理**（XHS 主体在中国大陆），避免境外 IP 触发地域风控。

### 2.2 IP 与账号绑定策略

- **一账号一 IP（粘性）**：每个账号长期绑定同一出口 IP（或同一城市/运营商的稳定段），
  不要今天上海明天广州——**IP 跳变是登录态突变的头号诱因**。
- **一机一号一 IP**：MVP 阶段最稳的拓扑——单台浏览器实例、单账号、单住宅 IP，三者
  一一绑定（与风控文档"一机一号"呼应）。
- 规模化时用**会话级粘性代理**（sticky session），保证单账号单会话内 IP 不变，跨会话
  尽量复用同一 IP。

### 2.3 DNS 泄露防护

- 所有 DNS 解析必须走代理通道（远程 DNS），禁止本地系统 DNS——否则真实 ISP 暴露。
- Chrome 启动用 `--proxy-server=...` 并确认 `--dns-prefetch-disable` 行为；用 SOCKS5
  代理时强制 `--host-resolver-rules` 或代理侧远程解析。
- 验证：访问 DNS 泄露检测站点，确认解析出口=代理地区。

### 2.4 WebRTC 泄露防护

WebRTC 会通过 STUN 暴露**真实本地/公网 IP**，绕过代理，是最隐蔽的翻车点。

- 注入脚本禁用/改写 `RTCPeerConnection`，或启动参数 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`；
- 更彻底：策略设为 `default_public_interface_only`，确保只暴露代理公网 IP；
- 验证：WebRTC 泄露检测页应只显示代理 IP，无本地 IP。

---

## 3. Cookie 与登录态管理

> 当前已通过固定 `--user-data-dir`（默认 `~/.aidcp-chrome-profile`，见 `src/cdp/chrome-launcher.ts`）
> 实现基础 Cookie/登录态持久化，重启后 profile 自然恢复。仍待实装：一账号一独立 profile
> 的多账号隔离、Cookie 加密存储与云端备份/续期机制。

### 3.1 Cookie 持久化方案

- **整体持久化用户数据目录**：Chrome 启动指定固定 `--user-data-dir=<account_profile>`，
  让 Cookie、LocalStorage、IndexedDB、缓存随 profile 自然持久——**这是最贴近真人的
  方式**（真人浏览器不会每次清空）。
- 或用 CDP `Network.getAllCookies` / `Storage` 域**显式导出/导入** Cookie 与 storage，
  存到云端（加密），供 session 恢复。
- **一账号一 profile**，目录隔离（见 §3.3）。

### 3.2 登录态过期检测与自动续期

- **检测**：复用现有 LocatingEngine 的**守卫层**（`src/locating/guard.ts` 已处理"登录
  过期"干扰）——检测到登录墙/登录弹窗即判登录态失效。
- **续期**：优先依赖 XHS 自身的长效凭证刷新（保持 profile + 定期有真人化活跃，登录态
  通常可长期维持）；失效后触发**重新登录流程**（扫码/短信），且重新登录应在**同一
  IP、同一指纹**下进行，避免"换设备登录"告警。
- 续期失败 → 上报风控状态机 `frozen`，告警人工（见 [风控文档 §7](risk-control.md)）。

### 3.3 多账号 Cookie 隔离

- 每账号独立 `--user-data-dir`，物理隔离 Cookie/storage，**绝不共用 profile**。
- 每账号独立指纹画像（§1.5）+ 独立代理 IP（§2.2），形成 **profile ⨯ 指纹 ⨯ IP** 三元
  绑定，长期固定。
- 进程隔离：每账号一个独立 Chrome 实例 + 独立 `--remote-debugging-port`，CDP 连接互不
  串扰。

### 3.4 Session 恢复策略

重启/崩溃后的恢复顺序：

```
1. 用账号绑定的 user-data-dir 启动 Chrome（指纹画像 + 代理一并恢复）
2. 打开 XHS，守卫层检测登录态
3a. 登录态有效 → 直接进入风控调度（保守档热身，见风控文档）
3b. 登录态失效 → 同 IP/同指纹下重新登录 → 成功后进保守档
4. 恢复"已互动集合""频率计数器"等持久化状态（与风控文档 §4.1 共享）
```

---

## 4. CDP 特征隐藏

### 4.1 隐藏 --remote-debugging-port 暴露的特征

- **端口不对外**：`--remote-debugging-port` 只绑 `127.0.0.1`，绝不监听 `0.0.0.0`；页面
  脚本无法直接探测本地调试端口，但要防止本机其他页面/扩展探测。
- **关闭调试发现接口**：`/json`、`/json/version` 等 HTTP 端点不暴露给非受控来源。
- 去掉 `--enable-automation`，避免 UA/标志暴露调试态（见 §1.1）。

### 4.2 Runtime.enable 等 CDP 事件指纹

- 启用 `Runtime` 域后，某些检测脚本能通过 **`Runtime.consoleAPICalled` / 异常对象的
  副作用**感知调试器存在。
- 对抗：**按需启用、用完即关**；执行注入脚本优先用 **isolated world**
  （`Page.createIsolatedWorld` + `Runtime.evaluate` 指定 contextId），避免污染主世界、
  减少可观测副作用。
- aidcp 现状是 `Runtime.evaluate(outerHTML)` 取 DOM（`CdpDomProvider`）——这类只读、
  低频调用风险较低，但仍建议走 isolated world，且不要常驻 `Runtime.enable`。

### 4.3 console.debug 检测绕过

经典检测：页面调用 `console.debug` 等，若 DevTools/调试器附着会触发可观测行为（如
`toString` 被调用、计时差异）。对抗：

- 不在被监控页面残留自定义 console 钩子；
- 注入脚本里**还原 `console.*` 与 `Function.prototype.toString`** 的"原生外观"
  （`toString` 返回 `function xxx() { [native code] }`），防止"注入函数被 toString
  识破"——这是 stealth 类方案的标准动作。

### 4.4 Headless 特征抹除（即便用 headful）

**强烈建议用 headful**（带真实窗口）跑互动账号，headless 残留特征太多。即便 headful
仍需检查：

| 特征 | headless 异常 | 处理 |
| --- | --- | --- |
| `navigator.plugins` / `mimeTypes` | headless 常为空 | headful 真实非空；若需补，注入真实结构 |
| `navigator.languages` | 可能为空/异常 | 设为 `['zh-CN','zh']` 与 IP 一致 |
| `window.chrome` 对象 | headless 可能缺失 `chrome.runtime` 等 | headful 真实存在；勿误删 |
| 权限查询 `Notification.permission` | headless 与真实不一致（`denied` vs `default` 矛盾） | 注入对齐 |
| WebGL/Canvas | headless 渲染路径不同 | headful + 真实 GPU 最可信（§1.2） |
| 窗口尺寸/焦点/可见性 | headless 无真实窗口 | headful 天然有；保证 `document.hidden=false` 时才操作 |

> 一句话：**headful + 一机一号 + 真实指纹** 本身就抹掉了绝大多数 headless 破绽，
> 比"headless + 一堆补丁"更稳。

---

## 5. 行为指纹

> 行为是最难伪造、也最被 XHS 重视的维度。本节给技术实现；**行为节奏/疲劳曲线/分布
> 参数**的策略层在 [风控文档 §3](risk-control.md)，本节聚焦"怎么用 CDP 把它做出来"。

### 5.1 鼠标移动模式（贝塞尔曲线参数）

绝不 `Input.dispatchMouseEvent(type=mousePressed)` 直接落点。完整动作 = 移动 + 悬停 +
按下 + 抬起：

```
轨迹: 三阶贝塞尔 B(t)=(1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 P3
  P0 = 当前光标, P3 = 目标 + 落点抖动(±3px 高斯)
  P1,P2 = 连线中点向法线方向偏移 (offset ~ U(0.1,0.3)×距离, 左右随机)
采样点数 N = clamp(round(距离/8), 15, 60)
逐点时间间隔: ease-in-out（先慢→快→逼近时减速, 符合 Fitts 定律）
overshoot: ~15% 概率越过目标 5–15px 后回拉
逐帧: Input.dispatchMouseEvent(type='mouseMoved', x, y)  → 末尾 mousePressed/mouseReleased
点击前: 在目标附近微停顿 (lognormal, 见风控文档 §3.1)
```

### 5.2 键盘输入节奏（按键间隔分布）

文本输入（评论/搜索/发布）绝不一次性 `Input.insertText` 整段灌入：

- 逐字符 `Input.dispatchKeyEvent`（keyDown/keyUp），**按键间隔服从对数正态**
  （中位 ~120ms，σ 适中），常用字快、生僻字/标点慢；
- 偶发**输入错误 + 退格修正**（概率 ~3–5%），模拟真人手误；
- 词间/句间有较长停顿（思考）；中文输入应模拟**拼音输入法**的节奏（输入拼音 →
  选词），而非逐汉字等距出现。

### 5.3 滚动模式（惯性 / 触控板 vs 鼠标滚轮）

- 用 `Input.dispatchMouseEvent(type='mouseWheel', deltaY=...)` 序列模拟，而非一次性
  `Runtime.evaluate(scrollTo)`（瞬移滚动=机器）。
- **鼠标滚轮**：离散"咔哒"步进（deltaY ≈ 100 的整数倍），步与步之间有间隔；
- **触控板**：连续小 delta + 惯性衰减尾（松手后还滑一段，delta 指数衰减）；
- 单账号固定一种风格（与设备画像一致：声称用笔记本则触控板，台式则滚轮），不要混用；
- ease-in-out 加速度 + 偶发回滚（见 [风控文档 §3.3](risk-control.md)）。

### 5.4 页面停留时间分布

- 停留时间服从对数正态 + 与内容长度相关（[风控文档 §3.1/§3.2](risk-control.md)）；
- 利用 `Page.lifecycleEvent` / 可见性，确保**页面可见且"聚焦"时**才计停留与操作，
  模拟真人"看着屏幕"。

### 5.5 操作序列的自然性

- **不总是同一顺序**：进笔记后不要永远"滚到底→点赞→返回"。随机化子动作顺序与
  取舍（有时只看不赞、有时看图不看文、有时看评论区、有时中途返回）。
- **插入无目的动作**：偶发"误触返回又进来""划走又划回""点开作者主页瞄一眼"等
  无产出动作，真人浏览充满这类噪声。
- **互动非必然**：浏览 N 篇才互动 1 篇（受点赞率约束），而非每篇都处理。

---

## 6. 技术选型建议

### 6.1 三条路线对比

| 方案 | 反检测效果 | 成本 | 维护性 | 多账号隔离 | 与 aidcp 现架构契合 |
| --- | --- | --- | --- | --- | --- |
| **A. 自研 CDP + stealth 注入**（现架构 + 本文 §1/§4 注入） | 中（够用，需持续维护补丁） | 低 | 中（需跟进检测升级） | 靠 profile+端口隔离，自己管 | **最高**（直接复用 `CdpClient`） |
| **B. 指纹浏览器**（AdsPower / MultiLogin / 候鸟 等） | 高（专业团队维护指纹） | 中–高（按账号/月订阅） | 高（厂商负责指纹升级） | **原生强**（每 profile 独立指纹+代理） | 中（多数支持 CDP/本地 API 接入，aidcp 连其调试端口即可） |
| **C. 改 Chromium 源码（patchwork）** | 最高（从源头抹特征） | 极高（编译/维护重） | 低（每次 Chrome 升级重打补丁） | 自己管 | 低（重活，不建议） |

### 6.2 关键判断

- **方案 C 不推荐**：维护成本与 Chrome 迭代速度不匹配，除非有专职团队。
- **MVP 阶段选 A**：现架构已是 CDP 原生，加 §1/§4 的注入脚本 + headful + 一机一号 +
  住宅代理，即可解决绝大多数明显检测点，**改动最小、契合度最高**。
- **规模化阶段选 B**：账号数上去后，指纹浏览器把"每账号独立指纹+代理+隔离"做成
  产品能力，省去自维护指纹的巨大成本。aidcp 只需把 CDP 连接指向指纹浏览器开放的
  本地调试端口，**定位/执行逻辑零改动**——这正是 aidcp"接口不变、实现可换"设计的
  红利。

### 6.3 推荐的最小可行方案（MVP）

```
Chrome (headful)
 ├─ 固定 --user-data-dir（账号 profile，持久化 Cookie）
 ├─ --remote-debugging-port 仅绑 127.0.0.1
 ├─ 去掉 --enable-automation，加 --disable-blink-features=AutomationControlled
 ├─ --proxy-server=国内住宅代理（粘性，一号一 IP）
 └─ Page.addScriptToEvaluateOnNewDocument 注入 stealth：
       webdriver=undefined / 还原 toString / WebRTC 关闭 / 一致性补丁
+ 行为层：HumanizedInput（贝塞尔鼠标 + 对数正态键入 + 惯性滚动）替换 random(4,8)
+ 一机一号一 IP，真实指纹不伪造
```

> 现状：上方 stealth 注入（`webdriver=undefined` / 还原 `toString` / 一致性补丁）与行为层
> （贝塞尔鼠标 + 对数正态键入 + 惯性滚动替换 `random(4,8)`）均已落地；唯 **WebRTC 关闭**
> 与 **住宅代理** 仍待实装。

---

## 7. 实施路线图

### Phase 1（立即，1–3 天）：最小防护，堵住明显检测点

- [x] 启动参数整改：去 `--enable-automation`、加 `--disable-blink-features=AutomationControlled`/`--disable-infobars`、调试端口默认绑 `127.0.0.1`、headful（`buildChromeArgs`，`src/cdp/chrome-launcher.ts`）。
- [x] `StealthInjector`（基于 `Page.addScriptToEvaluateOnNewDocument`）：`navigator.webdriver=undefined`、还原 `Function.prototype.toString`、`languages/plugins` 补齐已实装（`src/cdp/stealth-injector.ts`）；**WebRTC 关闭仍待实装**。
- [ ] 固定 `--user-data-dir`，实现 Cookie/登录态持久化（§3.1）。
- [ ] 配一个国内住宅代理，做到一账号一稳定 IP（§2.1/§2.2）。
- [ ] WebRTC / DNS 泄露自检通过。

> 产出：单账号在 sannysoft 类检测站点不报明显自动化特征；登录态可跨重启保持。

### Phase 2（1–2 周）：行为指纹拟人化

- [x] 边缘端拟人化模块 `src/humanize/`：贝塞尔鼠标轨迹（§5.1）、对数正态键盘节奏（§5.2）、惯性滚动（§5.3）、对数正态停顿与会话疲劳曲线。
- [x] 已用上述模块替换 `random(4,8)` 与瞬时 click/scroll（`src/browse/cdp-util.ts`、`feed-scroller.ts`），并接入停顿/疲劳曲线。
- [ ] 操作序列随机化 + 无目的动作注入（§5.5）。
- [ ] 指纹一致性画像表（§1.5）：UA/平台/分辨率/字体/时区/语言/WebGL 锁定并按账号绑定。
- [ ] Canvas/WebGL 策略确定（一机一号走真实暴露 §1.2 方案 A）。

> 产出：行为分布服从真人统计特征；指纹各维度自洽，无矛盾。

### Phase 3（规模化前）：多账号隔离 + 代理池 + 指纹浏览器

- [ ] 评估并接入指纹浏览器（方案 B），把 profile/指纹/代理隔离交给产品能力；aidcp 经其本地调试端口接入，复用现有 CDP 层。
- [ ] 住宅代理池 + 会话级粘性（§2.2），profile ⨯ 指纹 ⨯ IP 三元绑定持久化。
- [ ] 多账号进程/端口隔离编排，Cookie 物理隔离（§3.3）。
- [ ] 接入 [风控文档 §7](risk-control.md) 风控状态机：检测到限流自动降级，登录态失效告警人工。
- [ ] 指纹/检测对抗的持续监控与升级机制（检测手段会演进，反检测需常态化维护）。

> 产出：N 账号稳定共存，单账号被封不波及其他；指纹/IP/行为三层均可规模化维持。

---

## 8. 与 aidcp 现有架构的集成落点

| 能力 | 落点 | 说明 |
| --- | --- | --- |
| stealth 注入 / CDP 特征隐藏 | 边缘端，新增 `StealthInjector`，在 target attach 后经 `CdpClient` 调用 | 复用现有原生 WebSocket RPC（`src/cdp/client.ts`） |
| 拟人化输入（鼠标/键盘/滚动） | 边缘端 `src/humanize/`（贝塞尔鼠标/键盘节奏/惯性滚动），由浏览层 `src/browse/cdp-util.ts`（`dispatchClick`/`dispatchKeystrokes`）与 `feed-scroller.ts` 经 `Input.dispatchMouseEvent`/`Input.dispatchKeyEvent` 调用 | 已替换原 `random(4,8)` 与瞬时 click/scroll。注：`CdpActionExecutor`（`src/cdp/action-executor.ts`）仍走页面内 `el.click()`，未接入拟人化 |
| 登录态检测 | 复用守卫层 `src/locating/guard.ts` | 已处理"登录过期"干扰，接到续期/状态机即可 |
| 指纹画像 / 代理 / profile 绑定 | 云端配置下发 + 边缘按账号启动对应 Chrome | profile⨯指纹⨯IP 三元绑定存云端 PG |
| 检测信号 → 降级 | 复用后置校验/重试升级，上报 [风控状态机](risk-control.md) | 与风控文档共用一套信号通道 |

> 与"边轻云重 / 接口不变实现可换"一致：**指纹画像与代理配置在云端，注入与拟人化执行
> 在边缘**；未来切换到指纹浏览器时，仅 CDP 连接目标变化，定位/执行逻辑无需改动。
