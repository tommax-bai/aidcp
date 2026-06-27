## ADDED Requirements

### Requirement: 浏览器启动层可插拔且默认 adspower

edge 的**浏览器启动与生命周期**层 SHALL 经一个可选的 provider 选择，由 `AIDCP_BROWSER_PROVIDER` 决定，取值 `self` 或 `adspower`，**缺省为 `adspower`**。`adspower` 提供商 SHALL 把浏览器启动与生命周期托管给 AdsPower 指纹浏览器，并要求显式指定目标 profile（`AIDCP_ADS_USER_ID`），缺失即诚实报错；`self` 提供商（经显式 `AIDCP_BROWSER_PROVIDER=self` 选用）SHALL 自起一个真实指纹 Chrome，其行为与本能力引入前**逐字等价**。provider 的职责边界 SHALL **仅限启动与生命周期**，MUST NOT 改动 CDP 接入及其下游（定位 / 拟人 / 读身份）。以 self 为前提的编排路径（同机多节点启动器、Electron 桌面外壳）SHALL 各自显式钉回 `self`，不因默认翻转而启动失败。

#### Scenario: 未设 provider 时默认走 AdsPower
- **WHEN** 启动 edge 且未设置 `AIDCP_BROWSER_PROVIDER`
- **THEN** 默认走 `adspower` 提供商：已配 `AIDCP_ADS_USER_ID` 则经 AdsPower 启动该 profile 并接管生命周期；未配则诚实报错停手，绝不静默回落 self

#### Scenario: 显式切到 self 提供商
- **WHEN** 设 `AIDCP_BROWSER_PROVIDER=self`
- **THEN** edge 自起真实指纹 Chrome，启动 / 复用 / 登录等待 / 回收行为与本能力引入前一致，不依赖任何外部浏览器服务

#### Scenario: self 专属编排路径不受默认翻转影响
- **WHEN** 经同机多节点启动器或 Electron 桌面外壳启动 edge，且未在外部显式覆盖 provider
- **THEN** 这些路径各自钉回 `self`、自起真实指纹 Chrome，不因默认翻为 adspower 而启动失败

### Requirement: CDP 接入层在 provider 之下保持不变

无论选用哪个 provider，其 `launch` SHALL 产出一个统一形状的浏览器实例句柄（含可连接的 CDP host 与端口、以及关闭 / 确认关闭能力）。CDP 附着及其下游的定位、拟人化操作、登录身份读取 MUST NOT 因 provider 不同而出现任何分支或改动——它们 SHALL 只依赖该统一句柄给出的 host 与端口。

#### Scenario: AdsPower 的调试端口喂给现成接入层
- **WHEN** `adspower` 提供商启动浏览器并返回其标准 DevTools 调试端口
- **THEN** edge 用与 `self` 模式完全相同的 CDP 附着路径连上该端口，定位 / 拟人 / 读身份逻辑零改动地工作

### Requirement: AdsPower 提供商经本地 API 托管浏览器生命周期

`adspower` 提供商 SHALL 经 AdsPower 本地 API 完成「启动→取调试端口→等就绪」与「关闭→确认已关」：启动时取回该 profile 的调试端口并轮询至 CDP 就绪后才交付句柄；关闭时调用停止接口并确认浏览器已真正关闭。对本地 API 的调用 SHALL 串行节流以不触发其每秒一次的限速。

#### Scenario: 启动后等就绪再交付
- **WHEN** `adspower` 提供商请求启动某 profile
- **THEN** 它取回该 profile 的调试端口，轮询确认 CDP 端点就绪后才把句柄交给上层附着；未就绪则在超时后诚实报错

#### Scenario: 关闭并确认已关
- **WHEN** 上层请求回收该 `adspower` 浏览器
- **THEN** 提供商调用停止接口并确认浏览器已关闭；若无法确认已关，则如实报告而非假装已回收

### Requirement: provider 失败诚实停手、绝不静默回落

当所选 provider 无法交付一个可用且已就绪的浏览器（外部服务不可达、返回错误、取不到调试端口、或该 profile 未登录致身份读不出）时，edge MUST **诚实报错并停止启动**。`adspower` 模式失败时 MUST NOT 静默回落到 `self` 自起本机 Chrome，MUST NOT 上报启动成功——因为那会让本应使用独立指纹与独立 IP 的账号偷偷以本机真实指纹和本机出口 IP 起跑，正是防关联要避免的最坏情况。

#### Scenario: AdsPower 不可达时诚实失败
- **WHEN** `AIDCP_BROWSER_PROVIDER=adspower` 但 AdsPower 本地 API 不可达或返回错误
- **THEN** edge 诚实报错并停止启动，不自起本机 Chrome、不上报成功

#### Scenario: profile 未登录时诚实失败而非默认起跑
- **WHEN** AdsPower 浏览器起来了但该 profile 未登录目标小红书账号、登录身份读不出
- **THEN** edge 沿用「绝不静默以默认身份起跑」红线停手，不回落 `self`、不猜身份

### Requirement: 反检测恰好一层生效

反检测注入 SHALL 由 `AIDCP_STEALTH` 控制，缺省值**随 provider**：`self` 默认开启 edge 自研 stealth 注入，`adspower` 默认关闭 edge 自研 stealth、改由 AdsPower 内核的 CDP 掩蔽（cdp_mask）独占指纹层。两套反检测 MUST **恰有一层生效**：MUST NOT 在 `adspower` 模式下同时叠加 edge 自研 stealth 与 AdsPower 掩蔽（双层互相覆盖会制造可被识破的不自洽），也 MUST NOT 两层皆关致自动化特征裸奔。

#### Scenario: AdsPower 模式由 cdp_mask 独占且不暴露自动化特征
- **WHEN** `adspower` 模式且未显式覆盖 `AIDCP_STEALTH`
- **THEN** edge 自研 stealth 不注入、AdsPower 掩蔽独占指纹层，页面侧 `navigator.webdriver` 不暴露、指纹各面自洽

#### Scenario: self 模式仍由 edge 自研 stealth 兜底
- **WHEN** `self` 模式且未显式覆盖 `AIDCP_STEALTH`
- **THEN** edge 自研 stealth 照常注入，行为与本能力引入前一致

### Requirement: AdsPower 模式固定桌面视口

`adspower` 提供商启动浏览器时 SHALL 经其启动参数固定一个桌面宽度视口，使页面落入小红书的宽屏布局，而非窄屏布局变体。

#### Scenario: 固定桌面视口避免窄屏布局
- **WHEN** `adspower` 提供商启动浏览器
- **THEN** 浏览器以固定桌面视口打开，小红书主框架渲染为宽屏布局，定位 / 滚动 / 本人锚点选择器按宽屏布局正常命中

### Requirement: 防关联绑定契约——一 profile 一指纹一 IP 一账号

使用 `adspower` 模式做同机多账号防关联时，每个 AdsPower profile SHALL 唯一绑定：一套独立设备指纹、一个独立出口 IP（住宅代理优先）、一个小红书账号，且长期稳定不变。指纹与 IP SHALL **绑定到账号、而非绑定到任务或进程**：同一小红书账号 MUST NOT 被配置多套指纹或多个出口 IP（那会触发平台「换设备登录」风控告警，与防关联目标相悖）。出口 IP 的独立性与指纹的独立性同等必要——同一出口 IP 跑多账号，指纹再独立也会在 IP 维度被关联。

#### Scenario: 每账号独立 profile / 指纹 / IP
- **WHEN** 同机并行运营 N 个小红书账号
- **THEN** 每个账号绑定各自独立的 AdsPower profile（独立指纹 + 独立出口 IP + 该账号登录态），账号之间在指纹与 IP 两个维度均不可被关联

#### Scenario: 禁止同账号多指纹
- **WHEN** 试图为同一小红书账号配置多套指纹或多个出口 IP（例如不同任务用不同指纹）
- **THEN** 这违反绑定契约，等同制造「同账号换设备登录」信号，不被允许；账号与其指纹 / IP 的绑定保持唯一稳定
