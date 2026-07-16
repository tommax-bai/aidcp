## MODIFIED Requirements

### Requirement: Auto-attribution of client-created environments

当已登录客户在官方客户端内通过 Electron 主进程的程序化 `user/create` 流程**明确新建**环境时，系统 SHALL 在创建前签发绑定当前客户的短时一次性创建意图；主进程取得 AdsPower 返回的真实 envKey 后，Cloud SHALL 以该意图在同一事务内登记新环境并将其显式唯一归属到当前客户。Cloud 完成归属后，客户端 MUST 重新读取 `/my-environments`；只有该权威读已包含新 envKey，主进程才可把环境加入并落盘运行花名册。加入花名册 MUST NOT 自动启动环境。

该能力只适用于本次程序化新建结果。普通客户请求、renderer、手填分身 ID、“加入已有环境”列表或旧 `POST /environments` MUST NOT 通过提交任意 envKey 创建、替换或恢复 ownership；已登记或已归属环境 MUST NOT 借创建完成端点被认领或转移。未在有效登录态创建的环境 MUST NOT 被自动归属。

创建意图 SHALL 短时过期、一次性且绑定客户；proof MUST 高熵、只回显一次并只以哈希落库。完成写 SHALL 幂等：同一意图与同一 envKey 重试返回相同归属真态，同一意图用于不同 envKey MUST 被拒绝。任一归属失败或权威回读不含该 envKey 时，客户端 MUST 如实说明“本机已创建但未完成分配”，MUST NOT 乐观加入花名册。

#### Scenario: 登录态程序化新建环境自动归属并入册
- **WHEN** 客户 A 在有效登录态下通过客户端“新建环境”触发程序化建号，创建意图有效，AdsPower 返回一个尚未登记的 envKey，Cloud 完成事务写且 `/my-environments` 回读包含该 envKey
- **THEN** 该环境被登记并唯一归属 A，主进程把它加入并落盘运行花名册，环境栏立即出现离线行，且环境不被自动启动

#### Scenario: intent 准备失败时不制造本地孤儿
- **WHEN** 客户鉴权启用但客户端在调用 AdsPower `user/create` 前无法取得有效创建意图
- **THEN** 客户端诚实拒绝本次创建并说明云端归属准备失败，MUST NOT 调用本地 `user/create`

#### Scenario: 本地已创建但权威归属未确认时不入册
- **WHEN** AdsPower 已返回新 envKey，但创建完成请求失败、意图过期、Cloud 拒绝或 `/my-environments` 权威回读不含该 envKey
- **THEN** 客户端标明环境仅在本机创建、未完成分配并给出管理员兜底，MUST NOT 把它加入运行花名册或显示为可启动环境

#### Scenario: 已有环境和任意 envKey 仍不能自认领
- **WHEN** 客户通过旧 `POST /environments`、手填 ID、“加入已有环境”或创建完成端点尝试认领一个已登记或已归属环境
- **THEN** Cloud 拒绝请求且原 owner 不变，客户后续 `/my-environments` 不得因此出现该环境

#### Scenario: 创建完成重试幂等且意图不可换目标
- **WHEN** 同一客户用同一 intent + proof + envKey 重试创建完成，或把同一 intent 改用于另一个 envKey
- **THEN** 前者返回同一成功归属真态且不重复插入，后者返回冲突且不得产生第二个 owner

#### Scenario: 未配代理不阻止归属但不自动启动
- **WHEN** 客户未配置代理即成功新建并完成权威归属
- **THEN** 环境仍被加入花名册并如实提示未配代理，但保持离线，必须由用户显式启动
