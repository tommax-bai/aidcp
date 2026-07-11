# pluggable-browser-provider Specification

## Purpose
TBD - created by archiving change adspower-browser-provider. Update Purpose after archive.
## Requirements
### Requirement: 浏览器启动层可插拔且默认 adspower

edge 的**浏览器启动与生命周期**层 SHALL 经一个可选的 provider 选择，由 `AIDCP_BROWSER_PROVIDER` 决定，取值 `self` 或 `adspower`，**缺省为 `adspower`**。`adspower` 提供商 SHALL 把浏览器启动与生命周期托管给 AdsPower 指纹浏览器，并要求显式指定目标 profile（`AIDCP_ADS_USER_ID`），缺失即诚实报错；`self` 提供商（经显式 `AIDCP_BROWSER_PROVIDER=self` 选用）SHALL 自起一个真实指纹 Chrome，其行为与本能力引入前**逐字等价**。provider 的职责边界 SHALL **仅限启动与生命周期**，MUST NOT 改动 CDP 接入及其下游（定位 / 拟人 / 读身份）。以 self 为前提的命令行多节点启动器 SHALL 显式钉回 `self`，不因默认翻转而启动失败；Electron 桌面外壳则 SHALL 由**应用内浏览器选择**决定 provider（见下方桌面 provider 选择需求）。

#### Scenario: 未设 provider 时默认走 AdsPower
- **WHEN** 启动 edge 且未设置 `AIDCP_BROWSER_PROVIDER`
- **THEN** 默认走 `adspower` 提供商：已配 `AIDCP_ADS_USER_ID` 则经 AdsPower 启动该 profile 并接管生命周期；未配则诚实报错停手，绝不静默回落 self

#### Scenario: 显式切到 self 提供商
- **WHEN** 设 `AIDCP_BROWSER_PROVIDER=self`
- **THEN** edge 自起真实指纹 Chrome，启动 / 复用 / 登录等待 / 回收行为与本能力引入前一致，不依赖任何外部浏览器服务

#### Scenario: 命令行多节点启动器不受默认翻转影响
- **WHEN** 经同机命令行多节点启动器启动 edge，且未在外部显式覆盖 provider
- **THEN** 该路径显式钉回 `self`、自起真实指纹 Chrome，不因默认翻为 adspower 而启动失败

### Requirement: 桌面外壳内可选浏览器 provider 且默认 adspower

Electron 桌面外壳 SHALL 提供**应用内浏览器选择**，让运维在 `adspower`（默认，界面对外统称「指纹浏览器」、不暴露具体方案名）与 `self`（本机 Chrome）之间一键切换（SHALL 可实现为「本机 Chrome」开关：关 = 默认 `adspower`、开 = `self`），并把选择与指纹浏览器配置（分身 id 必填、API key / API base 可选）**持久化到本机**、在下次启动沿用。桌面外壳按当前选择把对应的 `AIDCP_BROWSER_PROVIDER` 及相关 env 注入其派生的核心进程；外部显式设置的同名 env SHALL 仍可覆盖（逃生阀）。`adspower` 模式 SHALL 委托核心经指纹浏览器托管浏览器与登录态（不自起本机 Chrome、不做本机端口 cookie 轮询）；`self` 模式沿用自起 Chrome + 登录门。缺分身 id、浏览器缺失、核心诚实非零退出、以及**设置持久化写盘失败**等情形 SHALL 如实暴露给运维，MUST NOT 谎报成功或以「运行中」外观空跑。桌面外壳**对运维可见的文案 MUST NOT 暴露底层指纹浏览器的具体方案名**（对外统称「指纹浏览器 / 本地指纹浏览器服务」；内部代码标识符、env、网络地址不受此约束）。

#### Scenario: 桌面默认 adspower、可切 self
- **WHEN** 首次启动桌面外壳（未改设置）
- **THEN** 默认选 `adspower`；运维可在面板经「本机 Chrome」开关一键切到 `self`（本机 Chrome）并「保存并启动」，选择被持久化、下次启动沿用

#### Scenario: adspower 缺分身 id 时诚实提示待配置
- **WHEN** 桌面选 `adspower` 但未填分身 id
- **THEN** 面板显示「待配置」并提示先填分身 id，不派生核心、不静默假装在跑

#### Scenario: 设置写盘失败如实告知
- **WHEN** 保存浏览器设置时写本机持久化文件失败（目录只读 / 磁盘满等）
- **THEN** 面板如实告知「本次已生效但写入本地失败、重启后可能丢失」，MUST NOT 谎报「已保存」

#### Scenario: 对外不暴露底层方案名
- **WHEN** 运维查看浏览器设置、状态提示或错误文案
- **THEN** 可见文案统称「指纹浏览器 / 本地指纹浏览器服务」，MUST NOT 出现底层方案名或其官网/下载入口（原「提供 AdsPower 下载入口」scenario 随之移除）

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

当所选 provider 无法交付一个可用且已就绪的浏览器（外部服务不可达、返回错误、取不到调试端口、或该 profile **经核心内有界登录等待门后仍未登录 / 身份读不出**）时，edge MUST **诚实报错并停止启动**。`adspower` 模式失败时 MUST NOT 静默回落到 `self` 自起本机 Chrome，MUST NOT 上报启动成功——因为那会让本应使用独立指纹与独立 IP 的账号偷偷以本机真实指纹和本机出口 IP 起跑，正是防关联要避免的最坏情况。

说明：「该 profile 未登录致身份读不出」这一触发项对 `adspower` 启动期首次读取 **MAY 先经一道有界的核心内「等待登录」门**（见 `account-identity-resolution`「启动期首次登录 MUST 有界等待」），即诚实停手可被该等待门**前置推迟**到窗口耗尽之后；这不放松「绝不回落 `self`、绝不猜身份、绝不静默以默认身份起跑」的红线，只改变诚实停手的**时点**。

#### Scenario: AdsPower 不可达时诚实失败
- **WHEN** `AIDCP_BROWSER_PROVIDER=adspower` 但 AdsPower 本地 API 不可达或返回错误
- **THEN** edge 诚实报错并停止启动，不自起本机 Chrome、不上报成功

#### Scenario: profile 未登录时诚实失败而非默认起跑
- **WHEN** AdsPower 浏览器起来了但该 profile 未登录目标小红书账号、登录身份读不出
- **THEN** edge 沿用「绝不静默以默认身份起跑」红线停手，不回落 `self`、不猜身份；对启动期首次读取，该停手 MAY 被核心内有界「等待登录」门前置推迟到窗口耗尽后再发生（红线不变）

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

### Requirement: browser provider startup and tab selection are platform-aware

The browser provider and edge startup flow SHALL accept a platform target descriptor that supplies start URL, allowed URL/domain predicates, and tab selection rules. For `facebook`, the startup flow MUST select or open Facebook URLs rather than requiring xhs-specific `urlIncludes` matches. Provider responsibilities remain limited to lifecycle/CDP endpoint delivery; downstream platform driver logic handles page-specific behavior.

#### Scenario: Facebook startup does not require xhs tab
- **WHEN** `AIDCP_PLATFORM=facebook` and the AdsPower profile has no `xiaohongshu.com` tab
- **THEN** edge still starts by selecting/opening an allowed Facebook tab and does not fail because an xhs URL is absent

#### Scenario: Provider boundary remains unchanged
- **WHEN** a Facebook profile is launched through AdsPower
- **THEN** AdsPower still only supplies browser lifecycle/CDP endpoint information; locating, identity, overlay detection, and page operations remain outside provider code

### Requirement: Facebook AdsPower fingerprint sanity probe runs before automation

For Facebook profiles, the system SHALL provide a read-only fingerprint sanity probe that records safe, non-secret signals such as viewport, timezone/language consistency, provider mode, stealth setting, and whether obvious automation flags are exposed. The probe MUST NOT attempt to bypass or solve platform defenses; it only verifies that configured provider state is not obviously inconsistent.

#### Scenario: Sanity probe reports non-secret fingerprint summary
- **WHEN** the Facebook fingerprint sanity probe runs
- **THEN** it reports safe summary fields and flags obvious misconfiguration, without dumping cookies, tokens, proxy credentials, or fingerprint raw internals

### Requirement: 浏览器提供商区分临时停用与最终回收

持有统一浏览器实例句柄的 edge 核心 SHALL 区分“临时停用自动运营”与“最终回收浏览器”。临时停用 MUST 关闭自动运营相关的云端、监测和 CDP 会话但 MUST NOT 调用拥有浏览器的关闭能力；最终回收 MUST 沿用提供商的关闭并确认已关能力。该区分 MUST 保持在统一 provider 句柄之上，Electron 外壳 MUST NOT 绕过核心直接成为第二个浏览器生命周期写入者。

#### Scenario: 临时暂停不调用浏览器关闭能力
- **WHEN** edge 核心收到客户端的临时暂停意图
- **THEN** 核心停用自动运营资源并保留其浏览器实例句柄
- **AND** 不调用该句柄的 `kill` 或 `killAndConfirmDead` 能力

#### Scenario: 显式关闭调用提供商关闭并确认
- **WHEN** 已暂停核心收到显式关闭意图
- **THEN** 核心调用原浏览器实例句柄的关闭并确认已关能力
- **AND** 无法确认时如实记录警告，MUST NOT 静默宣称浏览器已回收

#### Scenario: 终态回收和进程关机仍是最终关闭
- **WHEN** edge 发生不可恢复终态、收到正常终止信号或所属应用退出
- **THEN** 对自启并独占的浏览器仍执行最终回收
- **AND** 临时暂停语义 MUST NOT 弱化既有零孤儿与端口释放保证

#### Scenario: 复用外部浏览器仍不被回收
- **WHEN** edge 使用明确的外部浏览器复用模式并发生显式关闭或终态退出
- **THEN** 核心只诚实下线并退出，不终止不属于本进程的外部浏览器

### Requirement: Driven browser denies permission prompts by default
The edge browser startup path SHALL prevent native permission prompts (notifications, geolocation, camera, microphone, and other capability prompts) from interrupting automated browsing in the driven fingerprint browser, for both the AdsPower and self providers. Suppression SHALL deny rather than grant, and MUST NOT remove or replace any web permission API in a way that diverges from a normal browser where the user has blocked the permission.

#### Scenario: Fresh launch suppresses prompts before any page loads
- **WHEN** a driven browser is launched by either provider
- **THEN** the launch arguments include a switch that auto-denies permission prompts, so no permission dialog is shown for the first or any subsequent page

#### Scenario: A site requests notification permission
- **WHEN** the driven page requests notification permission
- **THEN** the request is denied without a visible prompt
- **AND** the browser does not surface an "allow notifications" dialog to the operator

#### Scenario: Reported permission state stays internally consistent under anti-detection
- **WHEN** anti-detection injection is active (self provider) and notifications are denied
- **THEN** `navigator.permissions.query({name:'notifications'})` reports `denied`, matching `Notification.permission`
- **AND** it does not report `prompt` while `Notification.permission` is `denied`, which would be a detectable inconsistency

### Requirement: Permission-prompt suppression survives reuse and reconnect
Because a launch switch cannot reach an already-running browser, the edge attach path SHALL apply an authoritative CDP permission override that denies the same set of permissions after CDP attach, and SHALL re-apply it after every reconnect. The override SHALL be best-effort: a failing permission override MUST NOT abort attach or crash the session.

#### Scenario: Reused browser instance is still silenced
- **WHEN** edge attaches to a browser that was already running before this launch (AdsPower hands back a live profile, or self reuses an open CDP port) and therefore never received the launch switch
- **THEN** edge applies the CDP permission denial after attach so prompts are still suppressed

#### Scenario: Reconnect re-applies the denial
- **WHEN** edge transparently reconnects to the driven page after a dropped CDP connection
- **THEN** it re-applies the permission denial together with domain re-enable and anti-detection re-injection

#### Scenario: Permission override failure is non-fatal
- **WHEN** a CDP permission override call rejects (e.g. an unsupported permission name on a given browser build)
- **THEN** edge continues attach and operation normally rather than aborting or reporting a false failure

