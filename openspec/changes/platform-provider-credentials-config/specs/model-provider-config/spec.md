## MODIFIED Requirements

### Requirement: API 密钥加密落库，明文绝不外泄

系统 SHALL 把平台级凭据经认证加密（AES-256-GCM）后落 PostgreSQL `provider_credentials`（`PK(provider, field)`，存密文 + iv + authTag + 写时算好的掩码提示），主加密密钥 MUST 来自环境变量 `AIDCP_CRED_KEY`、MUST NOT 入库 / 入仓 / 写日志。写凭据接口 SHALL 接受 `(provider, field, value)`，且 `(provider, field)` MUST 命中平台凭据注册表派生的白名单；白名单 SHALL 至少覆盖模型 API key（如 `dashscope:dashscope_api_key`、`volcengine:volcengine_api_key`）与账单查询 AccessKey（如 `aliyun:access_key_id`、`aliyun:access_key_secret`、`volcengine:access_key_id`、`volcengine:access_key_secret`）。未命中 MUST 诚实拒绝（非静默忽略）。任何读路径 MUST NOT 返回明文密钥，只返回每项凭据的「是否已配置 + 掩码提示 + 来源 + 展示标签」。

#### Scenario: 按平台凭据白名单写入密钥即加密落库
- **WHEN** 经 `PUT /api/config/credential` 提交某平台凭据的非空密钥（`{provider, field, value}`）且主密钥已配置、`(provider, field)` 在白名单内
- **THEN** 系统将其 AES-256-GCM 加密后落 `provider_credentials`，返回 `{ configured: true, maskedHint }`，响应体 MUST NOT 含明文密钥

#### Scenario: 账单 AccessKey 可通过同一写入口加密保存
- **WHEN** 经 `PUT /api/config/credential` 提交 `aliyun/access_key_id`、`aliyun/access_key_secret`、`volcengine/access_key_id` 或 `volcengine/access_key_secret`
- **THEN** 系统按平台凭据白名单接受并加密保存，后续账单查询运行时可按该平台凭据读取

#### Scenario: 未知厂商/字段被诚实拒绝
- **WHEN** 提交的 `(provider, field)` 不在平台凭据注册表派生的白名单内
- **THEN** 系统返回 400 与可辨认原因，不落任何密钥，绝不静默接受

#### Scenario: 读取永不回显明文
- **WHEN** 请求 `GET /api/config/model`
- **THEN** 返回的每项凭据字段只含 `configured` / `maskedHint` / `source` / 展示元数据，绝不含明文密钥

### Requirement: 后台模型配置页

管理后台 SHALL 将设置入口定位为平台配置页，而非单一模型配置页。该页 SHALL 至少包含「模型与厂商」和「平台凭据」两类区块：「模型与厂商」渲染全局文本厂商下拉（由注册表枚举）、当前文本/图片模型名（可改并保存）、各厂商 baseUrl（只读、由注册表/env 决定）；「平台凭据」渲染模型 API key 与云平台账单 AccessKey 等凭据状态和 password 输入。密钥 UI MUST NOT 回显明文，改密钥 MUST 整段重输；空值视作保持原值不变。保存文本模型时 SHALL 携带所选厂商，由服务端按该厂商探活后才写。写操作 MUST 非乐观并使用诚实文案（已保存 / 已加密保存待重启 / 主密钥未配置无法保存 / 该厂商密钥未配置）。账单凭据文案 MUST 使用平台名（如阿里云账单凭据、火山账单凭据），MUST NOT 把阿里云账单 AccessKey 误称为 DashScope 模型 API key。

#### Scenario: 平台配置页展示模型与厂商区块
- **WHEN** 打开设置入口
- **THEN** 页面标题与主要说明表达为平台配置，并在「模型与厂商」区块展示文本/图片厂商与模型配置

#### Scenario: 按平台凭据分别展示与编辑密钥
- **WHEN** 打开平台配置页
- **THEN** 每项平台凭据各有凭据状态（已配置 + 掩码 + 来源 + 标签）与独立 password 输入框，输入框为空、绝不回显明文

#### Scenario: 账单凭据使用平台名称展示
- **WHEN** 平台配置页展示账单查询凭据
- **THEN** 阿里云账单凭据显示为阿里云平台 AccessKey，火山账单凭据显示为火山引擎平台 AccessKey，避免与 DashScope/Ark 模型 API key 混淆

#### Scenario: 选厂商配模型
- **WHEN** 在平台配置页把全局文本厂商切到火山方舟并填模型名保存
- **THEN** 服务端用火山方舟探活通过后才落库，前端据写后真态渲染（非乐观）

#### Scenario: 主密钥未配置时禁用密钥编辑并说明
- **WHEN** `canEditCredential` 为 false
- **THEN** 各平台凭据输入均禁用并显示诚实说明（服务端未配置主加密密钥），模型名与厂商仍可改
