# edge-cloud-env-selection Specification

## Purpose
TBD - created by archiving change edge-cloud-env-selector. Update Purpose after archive.
## Requirements
### Requirement: Cloud environment is selectable in client settings
边缘客户端 SHALL 在设置界面提供「云端环境」选择项，可选 dev、ol、自定义地址三者之一，并将选择持久化到本机设置（`userData/settings.json`），跨重启保留。两个正式云端地址（dev、ol）SHALL 收敛在 edge 内一处映射，界面按该映射解析并显示友好名。

#### Scenario: Operator selects a cloud environment
- **WHEN** 运营人员在设置抽屉的「云端环境」里选择 dev、ol 或自定义地址并保存
- **THEN** 该选择被写入本机设置并跨重启保留；写盘失败时如实回报「未持久化」而非谎报保存成功

#### Scenario: Custom endpoint validation
- **WHEN** 运营人员选择「自定义」并填入地址
- **THEN** 客户端 SHALL 对明显非法输入（非 `ws://` / `wss://`）诚实回错、不静默接受

### Requirement: Selection resolves cloud endpoint with UI-first precedence
派生核心子进程时，客户端 SHALL 按「界面选择 > 启动环境变量 `AIDCP_CLOUD_URL` > 缺省 dev」解析权威云端地址。当界面已显式选择（非空）时，SHALL 在最终 spawn 环境上显式设置 `AIDCP_CLOUD_URL`，覆盖任何从外壳进程继承来的同名变量（adspower 与 self 两条派生路径都覆盖）。当界面未选择（留空）时，SHALL NOT 注入该变量，完全沿用继承环境变量 / 缺省的既有行为，对现有以环境变量启动的流程零回归。

#### Scenario: UI selection overrides inherited env var
- **WHEN** 外壳以 `AIDCP_CLOUD_URL=<dev>` 启动，但界面已选择 ol，随后（重）启动某环境
- **THEN** 该核心连接 ol（界面选择在合并之后显式覆盖继承值），而非继承来的 dev

#### Scenario: Empty selection is zero-regression
- **WHEN** 界面云端选择留空（默认态），外壳以 `AIDCP_CLOUD_URL=<某地址>` 启动
- **THEN** 客户端 SHALL NOT 注入云端变量，核心连接该继承地址，行为与本 change 前逐字一致

#### Scenario: No env, no selection falls back to default
- **WHEN** 既未设 `AIDCP_CLOUD_URL`、界面也未选择
- **THEN** 核心连接缺省 dev 地址

### Requirement: Switching cloud takes effect only on explicit restart

保存新的 Cloud 选择 SHALL 只持久化目标，不得自动打断在途页面任务。切换生效 SHALL 由显式“连接目标 Cloud”动作触发各浏览器无关 core 的控制传输重绑：停止从旧 Cloud 接受新任务，在途页面任务到安全边界后关闭旧连接并连接新地址。客户端 MUST NOT 通过普通环境重启、浏览器启动队列或 AdsPower provider 实现 Cloud 切换；切换前浏览器关闭则保持关闭，已打开则保持打开但空闲，槽位占用不得因重绑被隐式改变。

#### Scenario: 保存目标不打断当前连接

- **WHEN** 运营人员切换 Cloud 并保存，此时有环境连接旧 Cloud
- **THEN** 当前连接和浏览器状态不被立即改变，界面显示目标 Cloud 尚未应用并提供显式连接动作

#### Scenario: 显式连接重绑全部核心但不启动浏览器

- **WHEN** 运营人员确认“全部连接目标 Cloud”且所有在途页面任务已到安全边界
- **THEN** 客户端有序重绑每个 core 的控制连接；原本关闭的浏览器保持关闭，MUST NOT 因重绑申请槽位

#### Scenario: 单环境重绑失败不冒充全量成功

- **WHEN** 多环境重绑中一个环境连接目标 Cloud 失败
- **THEN** UI 分别显示各环境实际 Cloud 和失败原因，MUST NOT 宣称全部已切换，也不得通过打开浏览器重试

### Requirement: Current cloud is always visible and matches actual connection

客户端 SHALL 在界面常驻显示每环境 core 实际连接的 Cloud 及已保存目标，而非仅显示全局选择。只有实际 Cloud 已知且与目标不一致时，才 SHALL 显示“实际 X / 目标 Y / 待连接或失败”；首次启动尚未报告实际 Cloud 时 MUST NOT 显示为“待重绑”或暗示需要人工重绑。客户端 MUST NOT 把保存成功等同于连接成功。浏览器状态 SHALL 独立展示，不能用浏览器开关推断 Cloud。ol 环境 SHALL 醒目标注为线上生产。

#### Scenario: 首次启动尚未报告实际 Cloud

- **WHEN** core 刚启动、实际 Cloud 尚未报告，已保存目标为 dev
- **THEN** 顶部 Cloud 状态不显示红色“待重绑”，也不提供仅因实际值为空而产生的重绑提示

#### Scenario: 目标待连接时诚实显示

- **WHEN** 已把目标从 dev 保存为 ol，但 core 仍实际连接 dev
- **THEN** UI 显示“实际 dev / 目标 ol / 待连接”，不显示成已连接 ol

#### Scenario: 浏览器关闭不影响实际 Cloud 显示

- **WHEN** core 已连接 dev 且浏览器关闭
- **THEN** UI 仍显示 Cloud 已连接 dev，同时独立显示浏览器关闭

#### Scenario: ol marked as production

- **WHEN** 某 core 实际连接 ol 或目标选择 ol
- **THEN** 对应实际/目标标签均以醒目方式标注线上生产含义

### Requirement: Switching to ol requires confirmation
在界面将云端选择切换到 ol 时，客户端 SHALL 弹出二次确认（提示将连接线上生产云端）；未确认则不改变已保存选择。

#### Scenario: ol switch confirmation
- **WHEN** 运营人员在界面把云端选择改为 ol
- **THEN** 弹出确认提示；确认后方保存为 ol，取消则保持原选择不变

### Requirement: Resolved cloud environment controls Facebook automatic browse mode

客户端 SHALL 以每环境 core 实际连接的同一 Cloud 解析结果派生 Facebook 自动浏览模式，MUST NOT 让模式和控制连接目标因继承环境变量而分叉。新目标只在 core 控制传输成功重绑后成为实际模式；应用模式变化 MUST NOT 要求 core 进程或浏览器重启。已打开浏览器 SHALL 保持空闲，下一自动化会话按新模式执行；已关闭浏览器 SHALL 保持关闭。

#### Scenario: 重绑到 dev 后未来会话使用 dev 模式

- **WHEN** 环境 core 从 ol 成功重绑到 dev 且浏览器关闭
- **THEN** core 实际模式更新为 dev，浏览器保持关闭，未来 Facebook 自动化取得执行器后使用 dev 模式

#### Scenario: 保存未连接不静默改变在跑模式

- **WHEN** 实际连接仍为 dev、只把目标保存为 ol
- **THEN** 当前 core 和在途自动化继续使用 dev 模式，直到显式重绑成功；UI MUST NOT 显示模式已切换

