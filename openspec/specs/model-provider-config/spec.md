# model-provider-config Specification

## Purpose
TBD - created by archiving change console-model-provider-config. Update Purpose after archive.
## Requirements
### Requirement: API 密钥加密落库，明文绝不外泄

系统 SHALL 把模型厂商的 API 密钥经认证加密（AES-256-GCM）后落 PostgreSQL（存密文 + iv + authTag + 写时算好的掩码提示），主加密密钥 MUST 来自环境变量 `AIDCP_CRED_KEY`、MUST NOT 入库、入仓或写进日志。任何读路径 MUST NOT 返回明文密钥，只返回「是否已配置 + 掩码提示」。

#### Scenario: 写入密钥即加密落库
- **WHEN** 经 `PUT /api/config/credential` 提交一个非空密钥且主密钥已配置
- **THEN** 系统将其 AES-256-GCM 加密后落库，并返回 `{ configured: true, maskedHint }`，响应体 MUST NOT 含明文密钥

#### Scenario: 读取永不回显明文
- **WHEN** 请求 `GET /api/config/model`
- **THEN** 返回的凭据字段只含 `configured` 与掩码 `maskedHint`，绝不含明文密钥

### Requirement: 主密钥缺失时诚实拒绝，绝不静默假成功

当环境变量 `AIDCP_CRED_KEY` 未配置（无法加密）时，凭据写入 MUST 被拒绝并返回诚实原因（`cred_key_missing`），系统 MUST NOT 明文落库、MUST NOT 返回成功。此时模型名配置仍 SHALL 可用（不因凭据不可写而连带禁用）。

#### Scenario: 无主密钥拒绝写凭据
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/credential`
- **THEN** 系统返回 503 与 `cred_key_missing`，不落任何密钥，绝不假成功

#### Scenario: 无主密钥时模型名仍可配
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/model` 改模型名
- **THEN** 模型名照常写入并即时生效，`GET /api/config/model` 的 `canEditCredential` 为 false 以诚实标示凭据不可改

### Requirement: 模型名可配且运行时热加载，密钥变更重启生效

文本模型名与图片模型名 SHALL 落 PostgreSQL 单行配置（缺省回退云端代码默认值），LLM 文本客户端与图片客户端 MUST 在调用时从共享内存配置解析当前模型名，使 `PUT /api/config/model` 后**无需重启即生效**。API 密钥变更 SHALL 在下次进程启动时被客户端捕获生效（重启生效），前端文案 MUST 诚实告知此差异。

#### Scenario: 改模型名即时生效
- **WHEN** 经 `PUT /api/config/model` 改文本模型名为另一可用模型
- **THEN** 后续文本模型调用使用新模型名，无需重启进程

#### Scenario: 改密钥需重启生效
- **WHEN** 经 `PUT /api/config/credential` 改了 API 密钥
- **THEN** 系统提示需重启 cloud 才生效，运行中的客户端在重启前继续用启动时捕获的密钥

### Requirement: 模型配置面板接口受 JWT 守护且写非乐观

模型与凭据配置接口（`GET /api/config/model`、`PUT /api/config/model`、`PUT /api/config/credential`）MUST 与其它 `/api/*` 一样受 JWT 守护。写接口 MUST 非乐观——返回服务端写后真态供前端渲染，MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒
- **WHEN** 未带有效 JWT 请求任一 `/api/config/*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态
- **WHEN** `PUT /api/config/model` 成功
- **THEN** 返回服务端持久化后的真实模型配置，前端据真态渲染而非乐观更新

### Requirement: 后台模型配置页

管理后台 SHALL 提供模型配置页（落「设置」入口）：渲染当前文本/图片模型名（可改并保存）、provider 与 baseUrl（只读）、API 密钥（password 输入，掩码占位显示当前是否已配置）。密钥 UI MUST NOT 回显明文，改密钥 MUST 整段重输；空值视作保持原值不变。写操作 MUST 非乐观并使用诚实文案（已保存 / 已加密保存待重启 / 主密钥未配置无法保存）。

#### Scenario: 密钥不回显明文
- **WHEN** 打开模型配置页且密钥已配置
- **THEN** 页面以掩码占位标示「已配置」，输入框为空且为 password 类型，绝不回显明文

#### Scenario: 主密钥未配置时禁用密钥编辑并说明
- **WHEN** `canEditCredential` 为 false
- **THEN** 密钥输入禁用并显示诚实说明（服务端未配置主加密密钥），模型名仍可改

