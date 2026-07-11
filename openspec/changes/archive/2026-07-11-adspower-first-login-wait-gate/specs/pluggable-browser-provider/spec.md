## MODIFIED Requirements

### Requirement: provider 失败诚实停手、绝不静默回落

当所选 provider 无法交付一个可用且已就绪的浏览器（外部服务不可达、返回错误、取不到调试端口、或该 profile **经核心内有界登录等待门后仍未登录 / 身份读不出**）时，edge MUST **诚实报错并停止启动**。`adspower` 模式失败时 MUST NOT 静默回落到 `self` 自起本机 Chrome，MUST NOT 上报启动成功——因为那会让本应使用独立指纹与独立 IP 的账号偷偷以本机真实指纹和本机出口 IP 起跑，正是防关联要避免的最坏情况。

说明：「该 profile 未登录致身份读不出」这一触发项对 `adspower` 启动期首次读取 **MAY 先经一道有界的核心内「等待登录」门**（见 `account-identity-resolution`「启动期首次登录 MUST 有界等待」），即诚实停手可被该等待门**前置推迟**到窗口耗尽之后；这不放松「绝不回落 `self`、绝不猜身份、绝不静默以默认身份起跑」的红线，只改变诚实停手的**时点**。

#### Scenario: AdsPower 不可达时诚实失败
- **WHEN** `AIDCP_BROWSER_PROVIDER=adspower` 但 AdsPower 本地 API 不可达或返回错误
- **THEN** edge 诚实报错并停止启动，不自起本机 Chrome、不上报成功

#### Scenario: profile 未登录时诚实失败而非默认起跑
- **WHEN** AdsPower 浏览器起来了但该 profile 未登录目标小红书账号、登录身份读不出
- **THEN** edge 沿用「绝不静默以默认身份起跑」红线停手，不回落 `self`、不猜身份；对启动期首次读取，该停手 MAY 被核心内有界「等待登录」门前置推迟到窗口耗尽后再发生（红线不变）
