## ADDED Requirements

### Requirement: 平台配置页不管理 AdsPower API Key

平台配置页 SHALL 只展示 Cloud 当前仍支持的模型与账单平台凭据，MUST NOT 展示 AdsPower API Key、浏览器服务凭据分组、云端删除生效提示或 AdsPower 密钥输入框。页面 MUST NOT 从旧缓存或历史配置状态恢复该输入项。

#### Scenario: 设置页不显示 AdsPower 凭据
- **WHEN** 管理员打开平台配置页
- **THEN** 页面不存在 AdsPower API Key 标签、输入框、掩码、来源或“下一次删除生效”文案

#### Scenario: 其它凭据编辑保持正常
- **WHEN** 管理员编辑仍受支持的模型或账单凭据
- **THEN** 各输入框隔离、明文不回显和真实生效时机等既有行为不受影响

## REMOVED Requirements

### Requirement: 平台配置页管理 AdsPower API Key 且逐项说明生效时机

**Reason**: 管理后台云端删除环境能力取消，平台配置不再需要 AdsPower 凭据。

**Migration**: 删除 AdsPower 卡片、输入状态和即时生效文案；其它凭据继续按自身规则展示。
