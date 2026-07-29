## ADDED Requirements

### Requirement: 内部 Panel 环境管理不提供删除写面

内部 Panel SHALL 保留环境资产与历史 lifecycle 的读取能力，但 MUST NOT 注册或代理环境删除写端点，MUST NOT 调用 AdsPower，MUST NOT 创建删除申请或改变环境 lifecycle。对曾存在的 `POST /api/environments/:envKey/deletion` 的任何请求 SHALL 返回非成功结果且保持零删除副作用。

#### Scenario: 旧删除路径不再可用
- **WHEN** 内部管理员或旧 Console 请求 `POST /api/environments/:envKey/deletion`
- **THEN** 请求返回非成功结果，Cloud 不请求 AdsPower、不新增删除审计且不改变目标环境状态

#### Scenario: 环境资产读取保持可用
- **WHEN** 内部管理员读取环境列表、单环境影响信息或账号环境摘要
- **THEN** Panel 继续返回真实只读数据，包括已有历史 lifecycle，但不返回可执行删除动作

#### Scenario: 历史删除状态只读保留
- **WHEN** 数据库存在 deleting、delete_failed 或 deleted 历史行
- **THEN** Panel MAY 在只读查询中按真实状态展示，但 MUST NOT 自动重试、复活或推进这些行

### Requirement: Panel 平台凭据接口不提供 AdsPower API Key

`GET /api/config/model` SHALL 从平台凭据目录中省略 AdsPower API Key；`PUT /api/config/credential` 收到 `provider=adspower, field=api_key` SHALL 按未知或不允许的凭据拒绝，MUST NOT 新增、覆盖或读取 AdsPower 密文。其它已注册平台凭据行为保持不变。

#### Scenario: 设置读取不展示 AdsPower 凭据
- **WHEN** 管理员读取平台配置
- **THEN** 返回的凭据目录不包含 AdsPower API Key、掩码、来源或删除生效提示

#### Scenario: 旧客户端保存 AdsPower Key 被拒绝
- **WHEN** 旧 Console 向凭据端点提交 `provider=adspower, field=api_key`
- **THEN** Cloud 返回非成功结果且不写入或覆盖凭据数据

#### Scenario: 其它平台凭据不受影响
- **WHEN** 管理员读取或保存仍在允许列表中的模型或账单凭据
- **THEN** 其加密、掩码、来源与生效时机保持既有契约

## REMOVED Requirements

### Requirement: 内部 Panel 环境删除返回 Cloud 直调后的写后真态

**Reason**: 管理后台环境删除能力整体取消，不再存在 Cloud 直调后的写后结果。

**Migration**: 删除路由不再注册；环境资产接口仅提供读取。

### Requirement: Panel 平台凭据接口展示并保存 AdsPower API Key 状态

**Reason**: Cloud 不再需要 AdsPower 删除凭据，也不再允许配置该密钥。

**Migration**: 配置目录省略 AdsPower 项，旧写请求被拒；可能存在的历史密文行保持惰性且不读取。
