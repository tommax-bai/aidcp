## MODIFIED Requirements

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
