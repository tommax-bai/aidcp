## MODIFIED Requirements

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

## ADDED Requirements

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
