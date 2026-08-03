# cloud-automation-content-owner-ports Specification

## Purpose
TBD - created by archiving change split-cloud-automation-production-runtime. Update Purpose after archive.
## Requirements
### Requirement: automation SHALL 只经窄端口访问 content 属主存储

automation SHALL 只经版本化窄端口读写草稿精修、Facebook 发帖素材、概念池、精选库
四类 content 属主存储，MUST NOT 构造 content owner store、对 content 属主库开池，
或把 content 模块复制为本地实现。端口方法面 SHALL 与真实 automation 消费者一一对应；
**没有消费者的方法 MUST NOT 开放 route**。

content 侧 SHALL 在既有内部 HTTP 服务端上注册这些写口，每组独立注册——
**一组初始化失败 MUST NOT 连带关闭其它组**。

#### Scenario: automation 写 content 属主表

- **WHEN** automation 需要写入概念池或精选库
- **THEN** 它经 content 的窄端口发起写入
- **AND** 不打开 content 属主库连接，也不构造 content owner store

#### Scenario: 某组写口初始化失败

- **WHEN** 精选库存储初始化失败
- **THEN** 该组路由不注册且原因可观测
- **AND** 其余组照常注册并可用

### Requirement: 跨属主构造 SHALL 做传递性检查，optional 实参不得静默缺席

跨属主依赖的注入 SHALL 逐个构造点核对，**包括可选实参**。可选的跨属主实参缺席
MUST NOT 被静默接受：实现 SHALL 让缺席在构造期以具名原因暴露，
MUST NOT 让它退化成「这几个副作用不再发生」而调用方仍拿到成功。

#### Scenario: 发帖素材存储实参缺席

- **WHEN** 发布下发器在构造时未获得 Facebook 发帖素材写口
- **THEN** 构造以具名原因失败或显式记录该能力不可用
- **AND** 不出现「预留释放 / 标记已用 / 隔离三个写静默消失而调用方仍成功」

### Requirement: 模型调用出口与角色工厂 SHALL 先裁决归属再落地

通用模型调用出口与内容属主角色工厂是**行为**，不是数据，MUST NOT 用「包一个 HTTP 客户端」
的方式跨过去。二者的归属 SHALL 先经显式裁决并记录在 design 中，再落地实现。
无论裁决结果如何，MUST NOT 在两个仓里各留一份同名实现——
两份实现会各自编译通过、各自测试通过，只有真跑起来才暴露差异。

token 用量记账 SHALL 与模型出口分开处置：它写 content 属主表，走窄端口即可；
其成本 SHALL 由厂商账单反算，MUST NOT 在该层硬编码价目表。

#### Scenario: 未裁决即实现

- **WHEN** 模型出口或角色工厂在归属未裁决时被实现
- **THEN** 该实现不被接受
- **AND** 变更退回到裁决步骤

#### Scenario: 同名实现出现两份

- **WHEN** 两个仓各自持有一份模型出口实现
- **THEN** 派生对账判定为漂移并失败
- **AND** 不以「两侧都能编译且测试通过」作为可接受依据

### Requirement: content 窄端口的失败语义 SHALL 与领域结局分离

content 写口 SHALL 只回报真实结果（真实影响行数、真实具名失败原因）。
传输层失败 MUST NOT 被翻译成领域上的「没有这条」「已完成」或「无需处理」；
调用方 SHALL 能区分「对面明确回答了否」与「没问到对面」。

#### Scenario: 传输失败

- **WHEN** 对 content 的写口调用因网络或超时失败
- **THEN** 调用方得到可识别的传输失败
- **AND** 不把它当作领域上的否定结果或成功结果

#### Scenario: 写入影响零行

- **WHEN** 写口执行成功但影响零行
- **THEN** 返回真实的零
- **AND** 不染成 1，也不染成失败

