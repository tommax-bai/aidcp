## ADDED Requirements

### Requirement: 平台配置页凭据编辑体验

管理后台 SHALL 将平台配置页的模型/厂商配置与平台凭据配置分区展示，并使用一致的运营文案区分模型 API Key、平台账单 AccessKey、加密保存状态、环境变量来源、未配置状态、以及重启 cloud 后生效的运行时影响。每项凭据输入 SHALL 使用稳定且唯一的前端状态键和 DOM 字段名；编辑任一凭据输入 MUST NOT 改变其他凭据输入框的可见值。凭据输入 MUST NOT 回显明文密钥，已配置凭据仍要求整段重输。

#### Scenario: 平台配置页分区呈现

- **WHEN** 打开设置入口
- **THEN** 页面将模型/厂商配置与平台凭据维护展示为清晰分区，并以平台配置语义说明保存、加密、来源和重启影响

#### Scenario: AccessKey ID 和 Secret 输入互不串联

- **WHEN** 操作员在阿里云或火山引擎平台 AccessKey ID 输入框输入内容
- **THEN** 同平台 AccessKey Secret 输入框的可见值保持不变，反向输入也保持独立

#### Scenario: 已配置凭据不回显明文

- **WHEN** 平台配置页渲染已配置的模型 API Key 或账单 AccessKey
- **THEN** 输入框为空且仅展示配置状态、来源和掩码提示，修改时必须整段重输后保存
