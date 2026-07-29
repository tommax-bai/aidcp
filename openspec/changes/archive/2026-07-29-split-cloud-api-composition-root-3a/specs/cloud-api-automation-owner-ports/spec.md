## ADDED Requirements

### Requirement: api 只经显式端口访问 automation 属主能力

`aidcp-api` SHALL 通过版本化内部 HTTP 端口访问 automation 属主的面板投影、四类限频配置、Facebook 群运营事实、团队群路由和告警勾销，MUST NOT 打开 automation 数据库连接、直接读取其表或 import automation 业务实现。本 change 未提供的 Facebook scope 写 MUST 保持未就绪，不得以部分客户端冒充完整面板依赖。

#### Scenario: api 读取 automation 面板投影
- **WHEN** api 请求今日动作计数、批量风控态、告警或互动流
- **THEN** 请求经 automation 内部端口执行，api 不查询 `risk_counters` / `risk_state` / `alerts` / `interaction_feed`

#### Scenario: api 修改 automation 属主数据
- **WHEN** api 保存限频配置、启停既有 Facebook 群目标、团队群路由或勾销告警
- **THEN** 写只在 automation owner 内执行并回传真实结果，api 不持有相应 store 或写表权限

### Requirement: automation 面板投影保持完整异步方法面

内部端口 SHALL 完整提供 `PanelAutomationReader` 的 `todayActionTotals`、`todayActionTotalsByAccount`、`todayLikeViewTotal`、`riskStateProjection`、`listAlerts`、`listInteractions` 六个方法，并保持筛选参数与逐字段载荷语义。

#### Scenario: 批量风控态只返回存在的 owner 行
- **WHEN** api 传入一组账号 ID 请求 `riskStateProjection`
- **THEN** automation 只返回其中实际存在风控行的账号，api 继续把缺失账号映射为无状态而不是伪造默认状态

#### Scenario: 面板投影读取失败
- **WHEN** automation 查询失败或内部 HTTP 不可达
- **THEN** 客户端抛出可辨错误，MUST NOT 返回零计数、空告警或空互动冒充成功

### Requirement: 四类配置校验和真态回读留在 automation

quota、pacing、session、resume 四个 facade SHALL 继续由 automation 持有。读请求 SHALL 返回 owner 当前真生效视图；写请求 SHALL 由 owner 完成既有校验、整块写入、镜像版本推进并返回写后真态。api MUST NOT 复制校验或直接写配置表。

#### Scenario: 合法配置写入
- **WHEN** api 经内部端口提交合法配置补丁
- **THEN** automation 使用既有 facade 写入并回传写后真态，api 以该结果响应而不做乐观更新

#### Scenario: 非法配置整块拒绝
- **WHEN** 补丁违反既有数值、枚举、区间或必填字段校验
- **THEN** automation 返回既有 `{ok:false, reason}`，不写任何部分字段、不推进假状态

#### Scenario: owner 不可达时读取配置
- **WHEN** api 读取四类配置而 automation 不可达或读取失败
- **THEN** 请求失败并显式呈现不可用，MUST NOT 回代码默认、陈旧缓存或空视图

### Requirement: Facebook 群运营端口覆盖写面与目录所需 owner 事实

内部端口 SHALL 提供群目标列表、筛选面、启停、账号进度、分配列表、陈旧分配回收，并提供 scope 计数与最近排期结果的单条/批量读取。账号自动化目录 SHALL 在 api 侧用本地配置与这些 owner 事实组装，automation MUST NOT 为此反向读取 api。

#### Scenario: api 组装账号自动化目录
- **WHEN** api 为多个 Facebook 账号组装内容排期自动化目录
- **THEN** api 使用本地排期/账号配置、既有 risk-read 与 automation 的批量 scope/排期结果端口完成组装，不调用 automation mega-route 读取 api 事实

#### Scenario: 批量 Map 跨 HTTP 往返
- **WHEN** automation 的 store 返回按账号键控的 `Map`
- **THEN** route 将其编码为稳定 JSON 数组，客户端逐键重建且不丢失缺席项、null 与时间戳

#### Scenario: Facebook 群写失败
- **WHEN** 启停或回收操作在 owner 内失败
- **THEN** 错误原样传播，api MUST NOT 返回成功或使用本地猜测结果

#### Scenario: scope 写等待账号花名册配对
- **WHEN** api 独立组装根仍缺少 automation → api 的账号花名册刷新端口
- **THEN** `importTargets` / `replaceTargetScopes` 保持未注入/未就绪，MUST NOT 删除判否前刷新、使用陈旧标签放行或声称完整 Facebook 群运营面可用

### Requirement: 团队群路由按事实归属拆成两步

群路由端口 SHALL 以 `groupLabel` 为查询/写入键，提供 `getRoute`、`listRoutes`、`setRoute`。api SHALL 在本地解析账号的 `groupLabel`，再请求 automation；automation MUST NOT 反向读取 api 的账号表。

#### Scenario: 命中团队群路由
- **WHEN** api 已从本地账号事实得到非空 `groupLabel` 且 automation 返回对应 chat ID
- **THEN** 既有卡片解析链使用该 chat ID，并保持来源会话优先级不变

#### Scenario: 路由未配置
- **WHEN** `getRoute(groupLabel)` 合法返回 `null`
- **THEN** api 按既有默认群链回落并保留 config-gap 诊断，transport 不伪造 chat ID

#### Scenario: 路由 owner 读取失败
- **WHEN** automation 不可达或 `getRoute` 发生非缺行错误
- **THEN** transport 抛出错误而不把它改写成 `null`；是否回落及其诊断由 api 既有解析链决定

### Requirement: 告警勾销返回真实更新行数且不碰风控状态

告警勾销端口 SHALL 调用 automation 的 `AlertResolutionPort.resolveById`，返回真实更新行数，并 MUST NOT 调用 `applySignal`、`setQuotaLevel`、修改 `risk_state` 或恢复 Edge。

#### Scenario: 勾销未解决告警
- **WHEN** api 提交一个存在且未解决的 `alertId`
- **THEN** automation 只更新该告警的 `resolved_at` 并返回 `1`

#### Scenario: 告警不存在或已解决
- **WHEN** `alertId` 不存在或已经解决
- **THEN** automation 返回 `0`，api 不把它伪造成发生了一次更新

### Requirement: 服务端、客户端与共享包版本机械对账

每个 3a 端口 SHALL 同时具有 route、client 和直接 HTTP 契约测试，并作为 `aidcp-transport` 的逐文件成员发布。消费仓 SHALL 固定到精确 transport 版本；源码、package exports 和 pin 漂移 MUST 由同步检查失败暴露。

#### Scenario: route 和 client 方法面漂移
- **WHEN** 任一侧新增、删除、改名方法或改变 JSON 载荷而未同步另一侧
- **THEN** 类型检查、契约测试或 `sync-split-repos --check` 至少一道失败并指名差异

#### Scenario: 三进程尚未验收
- **WHEN** 服务端 route 与客户端测试均通过但 api 独立 `main()` 尚未启动
- **THEN** 交付记录只声明“服务端 route 可用、客户端契约可用”，MUST NOT 声称三进程互通或 api 已运行
