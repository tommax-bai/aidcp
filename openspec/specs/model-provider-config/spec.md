# model-provider-config Specification

## Purpose
TBD - created by archiving change console-model-provider-config. Update Purpose after archive.
## Requirements
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

### Requirement: 主密钥缺失时诚实拒绝，绝不静默假成功

当环境变量 `AIDCP_CRED_KEY` 未配置（无法加密）时，凭据写入 MUST 被拒绝并返回诚实原因（`cred_key_missing`），系统 MUST NOT 明文落库、MUST NOT 返回成功。此时模型名配置仍 SHALL 可用（不因凭据不可写而连带禁用）。

#### Scenario: 无主密钥拒绝写凭据
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/credential`
- **THEN** 系统返回 503 与 `cred_key_missing`，不落任何密钥，绝不假成功

#### Scenario: 无主密钥时模型名仍可配
- **WHEN** `AIDCP_CRED_KEY` 未配置而请求 `PUT /api/config/model` 改模型名
- **THEN** 模型名照常写入并即时生效，`GET /api/config/model` 的 `canEditCredential` 为 false 以诚实标示凭据不可改

### Requirement: 模型名可配且运行时热加载，密钥变更重启生效

文本模型名、**全局文本厂商**（`text_provider`）、图片模型名与**全局图片厂商**（`image_provider`）SHALL 落 PostgreSQL 单行配置（缺省回退云端代码默认值），文本 LLM 客户端与图片客户端 MUST 在调用时从共享内存配置解析当前模型名与 provider，使 `PUT /api/config/model` 后**无需重启即生效**（热加载）。各厂商 API 密钥变更 SHALL 在下次进程启动时被捕获生效（重启生效），前端文案 MUST 诚实告知此差异。图片厂商 SHALL 可在注册表枚举的图片厂商间配置（至少 `dashscope` 万相与 `volcengine` 即梦-Seedream，经火山方舟 Ark），缺省 `dashscope`（零回归）；图片厂商解析链 SHALL **独立于**文本厂商解析链，切换一侧 MUST NOT 影响另一侧。

#### Scenario: 改模型名/厂商即时生效
- **WHEN** 经 `PUT /api/config/model` 改全局文本厂商为 `volcengine` 并填一个该厂商可用模型名
- **THEN** 后续未被角色/分类覆盖的文本调用发往火山方舟端点、用新模型名，无需重启进程

#### Scenario: 改密钥需重启生效
- **WHEN** 经 `PUT /api/config/credential` 改了某厂商 API 密钥
- **THEN** 系统提示需重启 cloud 才生效，运行中的客户端在重启前继续用启动时捕获的映射

#### Scenario: 切文本厂商不影响图片
- **WHEN** 全局文本厂商切到 `volcengine`
- **THEN** 图片生成仍按当前 `image_provider` 走（未改则仍 DashScope 万相）、其 key 启动期照常加载，图片路径零回归

#### Scenario: 切图片厂商不影响文本
- **WHEN** 全局图片厂商切到 `volcengine`（即梦-Seedream）并填一个 Seedream 模型名
- **THEN** 后续配图执行发往火山方舟图片端点、用新图片模型名、无需重启；文本调用不受影响、仍按各自解析链走

### Requirement: 模型配置面板接口受 JWT 守护且写非乐观

模型与凭据配置接口（`GET /api/config/model`、`PUT /api/config/model`、`PUT /api/config/credential`）MUST 与其它 `/api/*` 一样受 JWT 守护。写接口 MUST 非乐观——返回服务端写后真态供前端渲染，MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒
- **WHEN** 未带有效 JWT 请求任一 `/api/config/*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态
- **WHEN** `PUT /api/config/model` 成功
- **THEN** 返回服务端持久化后的真实模型配置，前端据真态渲染而非乐观更新

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

### Requirement: 图片厂商按胜出配置取地址与密钥，缺密钥诚实失败绝不跨厂商兜底

图片出口 SHALL 在**每次生成**按当前全局 `image_provider`（经归一：未知/脏串回落代码默认 `dashscope`、MUST NOT 抛错 brick）分发到对应图片客户端：`dashscope` → 万相（DashScope 异步文生图）、`volcengine` → 即梦-Seedream（火山方舟 Ark **OpenAI 兼容同步** `POST {arkBase}/images/generations`）。选中图片厂商的密钥 SHALL 复用启动期预载的该厂商 `{baseUrl, apiKey}`（与文本同厂商同源、密钥变更重启生效）。当选中图片厂商的密钥不可用或生图失败时，被选中的图片客户端 MUST 诚实返回 `{ url: null, error }`（绝不抛、绝不伪造/占位 URL），路由 MUST NOT 静默改用另一图片厂商顶替（归一仅用于未知 provider，绝不用于把已选定但失败的厂商偷换掉）。

#### Scenario: 按配置路由到即梦-Seedream
- **WHEN** `image_provider = 'volcengine'` 且火山密钥就绪、`image_model` 为一个 Seedream 模型名
- **THEN** 配图执行经 Ark 同步端点单次请求取回图片 URL，无异步轮询；成功 URL 进 `imageUrls`

#### Scenario: 选中图片厂商缺密钥则诚实失败、不跨厂商顶替
- **WHEN** `image_provider = 'volcengine'` 但运行时无火山密钥
- **THEN** Seedream 客户端返回 `{ url: null, error }`（含可辨认原因），该张记失败、MUST NOT 回落到万相顶替；若成功图数 M=0 则由下游执行端诚实判 `failed`

#### Scenario: 未知图片厂商归一不 brick
- **WHEN** `image_provider` 为空或注册表外的脏串
- **THEN** 路由把它归一为 `dashscope`（万相）、正常出图不报错

### Requirement: 全局 textModel 即「默认模型」，不新造冗余全局层

后台 SHALL 把既有的全局文本模型名（`model_config.text_model`，经 `PUT /api/config/model` 可改、热加载生效）在文案上**正名为「默认模型」**，使其在角色 / 分类配置语境中表意清晰——它是模型解析优先级链**末端的全局默认**（角色与分类「回落到默认」即回落到它）。本要求为**纯正名**：系统 MUST NOT 为此新增任何第二个全局模型层级、新表或新写接口，既有 `model_config` 单行存储、读写接口与热加载行为 MUST 保持不变（YAGNI，避免冗余层）。

#### Scenario: 默认模型即既有全局 textModel
- **WHEN** 在后台查看「默认模型」
- **THEN** 其值与 `GET /api/config/model` 返回的全局 `textModel` 一致，改它即改全局默认（无独立的第二全局层）

#### Scenario: 正名不改既有存储与行为
- **WHEN** 经正名后的「默认模型」入口修改全局文本模型名
- **THEN** 仍写 `model_config` 单行、仍 `PUT /api/config/model`、仍无需重启热加载生效，行为与正名前逐字一致

#### Scenario: 角色与分类回落指向默认模型
- **WHEN** 某角色无 per-role 覆盖、其分类也无默认模型
- **THEN** 其生效模型回落到「默认模型」（即全局 `textModel`），后台「生效来源」标注为继承默认

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

### Requirement: 平台配置页管理 AdsPower API Key 且逐项说明生效时机

平台凭据注册表 SHALL 增加 AdsPower API Key，设置页 SHALL 在独立的浏览器服务凭据分组展示其标签、配置状态、来源和掩码，并提供空态 password 输入用于整段覆盖保存。明文 MUST NOT 回显、复制到 DOM 默认值或日志。页面 SHALL 按每项 `restartRequired` 分别说明生效时机：AdsPower Key 保存后下一次删除立即生效；启动期预载的模型/账单凭据仍按其真实规则提示重启，不得用一条“所有凭据都需重启”的笼统文案。

#### Scenario: AdsPower Key 以掩码展示
- **WHEN** 打开设置页且服务端已有 AdsPower API Key
- **THEN** 页面在浏览器服务凭据分组显示已配置、来源和掩码，输入框为空且不含明文

#### Scenario: AdsPower Key 保存后即时用于下一次删除
- **WHEN** 管理员输入完整新 Key 并保存成功
- **THEN** 输入框清空，页面提示下一次删除立即生效且无需重启 Cloud

#### Scenario: 不误导其它凭据生效方式
- **WHEN** 同一页面同时展示 AdsPower Key 与仍需启动期载入的模型凭据
- **THEN** 每项按自身 `restartRequired` 展示提示，AdsPower 标为即时生效而模型凭据仍标为重启生效

#### Scenario: 凭据输入彼此隔离
- **WHEN** 管理员编辑 AdsPower Key 输入框
- **THEN** 其它模型或账单凭据输入框的可见值保持不变，保存请求只携带 `provider=adspower, field=api_key`

