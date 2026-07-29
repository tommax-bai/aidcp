## MODIFIED Requirements

### Requirement: 环境展示名保真于 AdsPower 实时名并随列表刷新同步

写入运行花名册（并经主进程 `syncEnvHandles → fleetSnapshot / status.envName` 投影到左侧环境列表 / fleet rail）的**环境展示名**，在没有人工昵称时 SHALL 忠于该环境在 AdsPower `user/list` 返回的名字（`name`，缺则回落 `username`），使**左侧列表**与**环境管理**对同一环境呈现一致的名字，MUST NOT 让二者因来源不同而长期漂移。存在明确人工来源标记的成员 SHALL 保持人工昵称；环境管理对已按稳定 `profileId/envKey` 匹配到 fleet 或花名册的环境 SHALL 复用客户端统一显示名解析器并将人工昵称作为主昵称，MUST NOT 继续把不同的 AdsPower 实时名作为该行主昵称。尚未加入且无法匹配 fleet 或花名册的环境 SHALL 回落展示 AdsPower `name`、`username` 或稳定 profile ID。

- **创建路径 MUST NOT 以空名入册**：桌面外壳经程序化创建环境后自动选中该环境时，SHALL 把创建流实际写入 AdsPower 的环境名（`name`，缺省为模板名）经创建返回体带回渲染层并写入花名册，MUST NOT 因返回体漏带名字而以空字符串入册。此保真 SHALL 即时生效、不依赖后续任何列表刷新。
- **拉列表时以实时名回填非人工成员**：桌面外壳**成功且完整**地拉取 AdsPower 环境列表时（`user/list` 返回 `ok` 且未截断、且列表非空），SHALL 用实时名回填 / 更新花名册中对应成员的名字：仅覆盖**本次列表在场**、实时名**非空**、与花名册现存名**不同**且未标记人工来源的成员；人工成员 MUST 跳过。有回填即落盘一次以令左侧列表随即刷新。
- **缺数据不自残**：拉取失败 / 截断 / 空列表时 SHALL NOT 回填任何名字（沿用剔孤儿同款守卫 `r.ok && !r.truncated && live.size>0`），MUST NOT 因一次不完整的拉取把在用环境的名字误清或误改；宁可暂留旧名、绝不据缺数据改写。

#### Scenario: 创建环境后左侧列表与环境管理显示同一真名
- **WHEN** 运维经「创建环境」建出一个环境且该成员尚未人工命名，随后创建动作触发的列表刷新拉回该环境
- **THEN** 左侧环境列表与环境管理对该环境均显示其 AdsPower 环境名（默认为模板名），MUST NOT 显示「环境 …末4位」这类占位名

#### Scenario: AdsPower 端改名后刷新同步非人工成员
- **WHEN** 某未人工命名、已加入花名册的环境此后在 AdsPower 端被改名，运维再次成功且完整地刷新环境列表
- **THEN** 桌面外壳用实时名回填该成员的花名册名并落盘，左侧列表与环境管理随即显示新名

#### Scenario: 人工昵称成为环境管理主昵称
- **WHEN** 已人工命名的环境在 AdsPower 返回另一个实时名，且客户端能按稳定 profile ID 匹配该环境
- **THEN** 花名册、左栏与环境管理行均显示人工昵称，AdsPower 实时名 MUST NOT 覆盖花名册或继续作为管理行主昵称

#### Scenario: 未加入环境保留 AdsPower 名称
- **WHEN** AdsPower 返回一个尚未加入且无法匹配 fleet 或花名册的环境
- **THEN** 环境管理按 `name → username → profileId` 回落展示该物理环境，且加入动作仍以稳定 profile ID 为目标

#### Scenario: 拉取不完整时绝不误改环境名
- **WHEN** 环境列表拉取失败、被截断、或返回空列表
- **THEN** 桌面外壳不回填任何花名册成员名，在用环境的名字保持不变，MUST NOT 因缺数据把其名字清空或改错
