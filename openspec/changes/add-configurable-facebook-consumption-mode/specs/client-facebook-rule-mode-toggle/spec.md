## MODIFIED Requirements

### Requirement: 客户端规则模式读写保持 Cloud 环境作用域权威

已发布的客户规则模式接口 SHALL 作为统一 Facebook operation policy 的窄兼容面继续只接受当前客户 `envKey` 与唯一请求字段 `{ enabled: boolean }`。Cloud MUST 逐请求复核环境 ownership 与环境权威平台；客户端 MUST NOT 提交或选择 `accountId`、operation mode、节奏参数、policy revision、运行进度、HTTP 目标或授权模式。该路由 MUST NOT 依赖环境是否已绑定账号、Edge 是否在线或浏览器内核是否启动。

Cloud SHALL 在同一条件写中按当前权威 mode 映射布尔意图：

- `enabled=true`：当前 mode 为 `persona` 时创建使用服务器默认 `viewsPerLike=5`、`joinEveryNRounds=2` 的新 `rule` policy revision；当前已为 `rule` 时幂等返回且保留现有参数；当前为 `slow_start` 或 `consumption` 时具名拒绝且不写。
- `enabled=false`：仅当前 mode 为 `rule` 时创建新的 `persona` policy revision；当前为 `persona` 时幂等返回且不写；当前为 `slow_start` 或 `consumption` 时具名拒绝且不写。

兼容写 MUST 使用服务端现读 revision 做原子条件更新并追加可区分的客户兼容面审计身份；并发 revision 已变化时 MUST 返回冲突与最新客户投影，MUST NOT 覆盖较新的 Console 配置。成功回包 SHALL 返回同一 `envKey` 的写后最小权威投影；响应不泄露 `accountId`、内部 actor 或可用于绕过统一 policy API 的参数写入口。

#### Scenario: Persona 环境通过旧开关启用默认规则

- **WHEN** 已登录客户为自己一个 Facebook persona 环境提交 `{ enabled: true }`
- **THEN** Cloud 原子创建 `rule` mode 的新 revision，并物化服务器默认 5/2 参数
- **AND** 返回写后 `enabled=true` 的环境投影，Edge 不创建本地规则配置

#### Scenario: 已配置规则的重复开启不重置参数

- **WHEN** 当前环境已处于参数经过后台调整的 `rule` mode 且旧客户端再次提交 `{ enabled: true }`
- **THEN** Cloud 幂等返回当前规则投影
- **AND** 不把自定义参数重置为默认值、不创建空 revision

#### Scenario: 关闭只从规则映射到 persona

- **WHEN** 当前环境处于 `rule` mode 且客户提交 `{ enabled: false }`
- **THEN** Cloud 创建新的 `persona` policy revision并返回写后 `enabled=false`
- **AND** 旧规则 revision 的运行态按统一 mode transition 契约收敛

#### Scenario: 兼容开关不能覆盖慢启动或消费模式

- **WHEN** 当前环境处于 `slow_start` 或 `consumption` 且旧客户端提交任一布尔值
- **THEN** Cloud 返回具名 mode conflict 与当前最小投影
- **AND** 不修改 mode、参数、slow-start anchor 或 policy revision

#### Scenario: 未绑定 Facebook 环境仍可兼容写

- **WHEN** 客户拥有的 Facebook 环境尚未绑定账号或其本地内核已停止，且当前 mode 允许该布尔映射
- **THEN** Cloud 仍可完成环境级兼容写并标注当前没有执行对象
- **AND** 不要求或伪造 `accountId`

#### Scenario: 非法范围和账号选择器失败关闭

- **WHEN** 环境不归属当前客户、环境平台不是 Facebook、环境注册表不可读，或请求包含 `enabled` 以外的字段
- **THEN** Cloud 返回可区分的拒绝或不可用结果
- **AND** 不修改 operation policy、运行态或审计成功记录

### Requirement: 客户端开关不得改变规则模式仲裁

客户端兼容开关 SHALL 只表达“尝试在 `persona` 与默认参数 `rule` 之间映射”的布尔意图，不是通用 mode selector。Cloud 仍 MUST 独占 operation-policy 仲裁、revision、环境绑定解析、活跃时段、风险、配额、单飞与 mode-transition 判定。旧开关 MUST NOT 停止或覆盖 `slow_start`，MUST NOT 开启、关闭或改写 `consumption`，MUST NOT 修改规则节奏参数。

Edge MUST NOT 根据本地 checkbox 自行选择模式、累计规则或消费计数、推断服务器默认值，或触发点赞、加群和评论。服务器默认值及后续参数变化只存在于 Cloud policy snapshot；客户端无需发版即可继续把兼容布尔意图交给 Cloud 裁决。

#### Scenario: 慢启动不能被旧开关改写

- **WHEN** 当前权威 mode 为 `slow_start`
- **THEN** 任一旧规则开关写都被 Cloud 拒绝且慢启动保持不变
- **AND** 客户端不得把未选中的 checkbox 解释成已切换到 persona

#### Scenario: 消费模式不能被旧开关关闭

- **WHEN** 当前权威 mode 为 `consumption` 且旧客户端提交 `{ enabled: false }`
- **THEN** Cloud 不执行“false 等于 persona”的映射
- **AND** 返回当前 mode conflict 真态而不是成功关闭

#### Scenario: 客户端不内置节奏数字

- **WHEN** Cloud 调整规则参数的默认值、范围或某环境的当前值
- **THEN** 客户端兼容开关仍只提交布尔值
- **AND** Edge 与客户端 MUST NOT 根据本地写死数字自行触发或预测任何动作
