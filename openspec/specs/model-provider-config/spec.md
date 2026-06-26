# model-provider-config Specification

## Purpose
TBD - created by archiving change console-model-provider-config. Update Purpose after archive.
## Requirements
### Requirement: API 密钥加密落库，明文绝不外泄

系统 SHALL 把**各文本厂商**的 API 密钥经认证加密（AES-256-GCM）后落 PostgreSQL `provider_credentials`（`PK(provider, field)`，存密文 + iv + authTag + 写时算好的掩码提示），主加密密钥 MUST 来自环境变量 `AIDCP_CRED_KEY`、MUST NOT 入库 / 入仓 / 写日志。写凭据接口 SHALL 接受 `(provider, field, value)`，且 `(provider, field)` MUST 命中由 provider 注册表派生的白名单（如 `dashscope:dashscope_api_key`、`volcengine:volcengine_api_key`），未命中 MUST 诚实拒绝（非静默忽略）。任何读路径 MUST NOT 返回明文密钥，只返回每厂商的「是否已配置 + 掩码提示 + 来源」。

#### Scenario: 按厂商写入密钥即加密落库
- **WHEN** 经 `PUT /api/config/credential` 提交某厂商一个非空密钥（`{provider, field, value}`）且主密钥已配置、`(provider, field)` 在白名单内
- **THEN** 系统将其 AES-256-GCM 加密后落 `provider_credentials`，返回 `{ configured: true, maskedHint }`，响应体 MUST NOT 含明文密钥

#### Scenario: 未知厂商/字段被诚实拒绝
- **WHEN** 提交的 `(provider, field)` 不在注册表派生的白名单内
- **THEN** 系统返回 400 与可辨认原因，不落任何密钥，绝不静默接受

#### Scenario: 读取永不回显明文
- **WHEN** 请求 `GET /api/config/model`
- **THEN** 返回的每厂商凭据字段只含 `configured` / `maskedHint` / `source`，绝不含明文密钥

### Requirement: 主密钥缺失时诚实拒绝，绝不静默假成功

当环境变量 `AIDCP_CRED_KEY` 未配置（无法加密）时，凭据写入 MUST 被拒绝并返回诚实原因（`cred_key_missing`），系统 MUST NOT 明文落库、MUST NOT 返回成功。此时模型名配置仍 SHALL 可用（不因凭据不可写而连带禁用）。

#### Scenario: 无主密钥拒绝写凭据
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/credential`
- **THEN** 系统返回 503 与 `cred_key_missing`，不落任何密钥，绝不假成功

#### Scenario: 无主密钥时模型名仍可配
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/model` 改模型名
- **THEN** 模型名照常写入并即时生效，`GET /api/config/model` 的 `canEditCredential` 为 false 以诚实标示凭据不可改

### Requirement: 模型名可配且运行时热加载，密钥变更重启生效

文本模型名、**全局文本厂商**（`text_provider`）与图片模型名 SHALL 落 PostgreSQL 单行配置（缺省回退云端代码默认值），文本 LLM 客户端 MUST 在调用时从共享内存配置解析当前模型名与 provider，使 `PUT /api/config/model` 后**无需重启即生效**（热加载）。各厂商 API 密钥变更 SHALL 在下次进程启动时被捕获生效（重启生效），前端文案 MUST 诚实告知此差异。图片模型名 SHALL 钉死走 DashScope（万相），MUST NOT 经文本 provider 解析路由。

#### Scenario: 改模型名/厂商即时生效
- **WHEN** 经 `PUT /api/config/model` 改全局文本厂商为 `volcengine` 并填一个该厂商可用模型名
- **THEN** 后续未被角色/分类覆盖的文本调用发往火山方舟端点、用新模型名，无需重启进程

#### Scenario: 改密钥需重启生效
- **WHEN** 经 `PUT /api/config/credential` 改了某厂商 API 密钥
- **THEN** 系统提示需重启 cloud 才生效，运行中的客户端在重启前继续用启动时捕获的映射

#### Scenario: 切文本厂商不影响图片
- **WHEN** 全局文本厂商切到 `volcengine`
- **THEN** 图片生成仍走 DashScope（万相）、其 key 启动期照常加载，图片路径零回归

### Requirement: 模型配置面板接口受 JWT 守护且写非乐观

模型与凭据配置接口（`GET /api/config/model`、`PUT /api/config/model`、`PUT /api/config/credential`）MUST 与其它 `/api/*` 一样受 JWT 守护。写接口 MUST 非乐观——返回服务端写后真态供前端渲染，MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒
- **WHEN** 未带有效 JWT 请求任一 `/api/config/*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态
- **WHEN** `PUT /api/config/model` 成功
- **THEN** 返回服务端持久化后的真实模型配置，前端据真态渲染而非乐观更新

### Requirement: 后台模型配置页

管理后台 SHALL 提供模型配置页（落「设置」入口）：渲染**全局文本厂商下拉**（由注册表枚举）、当前文本/图片模型名（可改并保存）、各厂商 baseUrl（只读、由注册表/env 决定）、**各文本厂商的 API 密钥分别输入**（password、掩码占位标示各自是否已配置与来源）。密钥 UI MUST NOT 回显明文，改密钥 MUST 整段重输；空值视作保持原值不变。保存文本模型时 SHALL 携带所选厂商，由服务端按该厂商探活后才写。写操作 MUST 非乐观并使用诚实文案（已保存 / 已加密保存待重启 / 主密钥未配置无法保存 / 该厂商密钥未配置）。

#### Scenario: 按厂商分别展示与编辑密钥
- **WHEN** 打开模型配置页
- **THEN** 每个文本厂商各有一行凭据状态（已配置 + 掩码 + 来源）与独立 password 输入框，输入框为空、绝不回显明文

#### Scenario: 选厂商配模型
- **WHEN** 在设置页把全局文本厂商切到火山方舟并填模型名保存
- **THEN** 服务端用火山方舟探活通过后才落库，前端据写后真态渲染（非乐观）

#### Scenario: 主密钥未配置时禁用密钥编辑并说明
- **WHEN** `canEditCredential` 为 false
- **THEN** 各厂商密钥输入均禁用并显示诚实说明（服务端未配置主加密密钥），模型名与厂商仍可改

### Requirement: 文本模型支持多厂商，provider 跟模型逐层解析

系统 SHALL 支持配置**多个 OpenAI 兼容的文本厂商**（至少 `dashscope` 与 `volcengine` 火山方舟 Ark），由一份**字面注册表**枚举（每项含 `id` / 显示名 / 默认 baseUrl / 凭据字段名 / key 的 env 回退键）。文本模型的"生效厂商"SHALL 跟着"生效模型"**逐层解析**：全局默认、按角色覆盖、按分类默认每层各自携带 provider，解析器 MUST 取**与胜出模型同一层、同一行**的 provider，MUST NOT 把某层的 provider 配到另一层的 model。某层的 provider **缺失或未知**时 MUST 归一回落到代码默认厂商（`dashscope`）、解析器 MUST NOT 抛错（绝不 brick）。

#### Scenario: 火山方舟可作为文本厂商配置
- **WHEN** 注册表枚举了 `volcengine`（火山方舟 Ark，OpenAI 兼容端点）
- **THEN** 运营可把全局/角色/分类的文本模型连同 prov 选为 `volcengine`，且后续该层的文本调用发往火山方舟端点

#### Scenario: provider 跟胜出模型同层
- **WHEN** 某角色覆盖了模型与 provider，而全局是另一厂商
- **THEN** 该角色的调用使用**该角色覆盖行**的 provider + 模型，绝不用全局的 provider 配该角色的模型（或反之）

#### Scenario: 未知/缺失 provider 归一回落不 brick
- **WHEN** 某配置行的 model 非空但 provider 为空、或为注册表外的脏串
- **THEN** 解析器把该层 provider 归一为 `dashscope`，正常运行不报错

### Requirement: 每次调用按胜出 provider 取地址与密钥，缺失诚实失败绝不跨厂商兜底

文本 LLM 出口 SHALL 在**每次调用**按解析出的 provider，从启动期预载的 `provider → {baseUrl, apiKey}` 静态映射中取该厂商的 baseUrl 与密钥。当选中 provider 的密钥**不可用**（库内无、env 也无）时，出口 MUST 在**发起请求之前**诚实抛错（带可辨认的 provider 名），MUST NOT 退回另一厂商的密钥或 baseUrl、MUST NOT 发空 Bearer、MUST NOT 静默假成功。每厂商密钥 SHALL 在启动期一次性解密载入（与现有 DashScope 行为一致：模型名热加载、**密钥变更重启生效**）。

#### Scenario: 选中厂商缺密钥则发请求前诚实失败
- **WHEN** 某调用解析到 `provider=volcengine` 但运行时无火山密钥
- **THEN** 出口在发起 HTTP 前抛出含 `volcengine` 的诚实错误，绝不改用 DashScope 的密钥/地址，绝不发出请求

#### Scenario: 绝不跨厂商兜底
- **WHEN** 任一 provider 的调用因密钥缺失或鉴权失败
- **THEN** 系统 MUST NOT 以另一厂商的密钥/模型重试或顶替，避免把模型名发到错误厂商的"静默走错"

#### Scenario: 新增厂商密钥重启生效
- **WHEN** 经后台为火山方舟新存了密钥但未重启 cloud
- **THEN** 运行中进程仍以启动时载入的映射为准，UI SHALL 诚实告知需重启 cloud 方生效

