## ADDED Requirements

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
保存新的云端选择 SHALL 只持久化、不打断在跑核心。因云端地址仅在核心启动时读取，切换 SHALL 通过显式重启在跑环境生效，客户端 SHALL 明确告知需重启，并提供一键「全部重启并连接新云端」入口（全环境重启，避免部分环境连旧云、部分连新云的裂脑）。客户端 MUST NOT 谎称切换已即时生效。

#### Scenario: Save persists without interrupting running cores
- **WHEN** 运营人员切换云端并保存，此时有环境正在运行
- **THEN** 在跑核心不被打断，界面提示「需重启运行中的环境才生效」

#### Scenario: Explicit restart applies the switch to all
- **WHEN** 运营人员点「全部重启并连接新云端」
- **THEN** 全部在跑环境有序停止并以新云端地址重启，不残留部分连旧云的环境

### Requirement: Current cloud is always visible and matches actual connection
客户端 SHALL 在界面常驻显示当前云端（dev / ol(线上) / 自定义），且显示值 SHALL 反映核心**实际连接**的云端、而非仅仅已保存的选择。当已保存新选择但相关环境尚未重启时，SHALL 显示为「目标 X · 待重启生效」，MUST NOT 显示成已切换生效。ol 环境 SHALL 以醒目方式标注为线上生产。

#### Scenario: Pending switch shown honestly
- **WHEN** 运营人员把云端从 dev 切到 ol 并保存，但尚未重启在跑环境
- **THEN** 界面显示在跑环境仍连 dev、目标为 ol「待重启生效」，不显示成已连 ol

#### Scenario: ol marked as production
- **WHEN** 当前云端为 ol
- **THEN** 界面以醒目方式标注其为线上生产环境

### Requirement: Switching to ol requires confirmation
在界面将云端选择切换到 ol 时，客户端 SHALL 弹出二次确认（提示将连接线上生产云端）；未确认则不改变已保存选择。

#### Scenario: ol switch confirmation
- **WHEN** 运营人员在界面把云端选择改为 ol
- **THEN** 弹出确认提示；确认后方保存为 ol，取消则保持原选择不变
