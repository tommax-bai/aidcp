## ADDED Requirements

### Requirement: 群目标账号分组范围经事务单写并回读真态

群目标范围写 SHALL 只经 Facebook group target store 的一等方法完成，MUST NOT 从 panel handler 发 raw SQL。请求 SHALL 包含一个或多个 canonicalizable group URL 以及作为完整替换值的账号分组标签集合；服务端 MUST 在同一事务内验证所有目标存在、所有标签为当前 Facebook 账号实际使用的规范化分组，并原子替换全部选中目标的映射。任一失败 SHALL 整块拒绝、不部分修改；成功 SHALL 返回数据库回读真态及审计更新人/时间。

#### Scenario: 任一目标不存在则整块拒绝
- **WHEN** 批量范围写中两个 URL 存在、一个 URL 不存在
- **THEN** 接口具名拒绝，三个目标相关的映射均不改变

#### Scenario: 写后返回完整映射
- **WHEN** 合法批量范围写成功
- **THEN** 响应来自同一事务写后回读，并精确返回每个目标当前完整账号分组集合

### Requirement: Facebook 自动加群配置经专属单写且只允许 Facebook 账号

每账号自动加群配置 SHALL 经 JWT 保护的专属一等写方法保存，写前校验账号存在且规范化平台为 Facebook；`enabled` 必须为 boolean，`dailyCap` 必须为服务端界限内非负整数，`weekMask` 必须为 null 或合法 168 位 `0/1` 掩码，非法值整块拒绝。无配置默认关闭；写后 SHALL 回读真实配置并聚合返回，MUST NOT 乐观假成功。该写不得修改 RiskController 额度、全局 kill switch、通用内容周历或其它动作字段。

#### Scenario: 非 Facebook 账号拒绝
- **WHEN** 对小红书或视频号账号提交自动加群配置
- **THEN** 接口返回可区分 `unsupported_automation_action`，不创建配置行

#### Scenario: 非法周历整块拒绝
- **WHEN** 提交的加群动作周历不是 168 位 `0/1` 掩码
- **THEN** enabled、dailyCap 和 weekMask 全部不落库，接口返回可区分 invalid value

#### Scenario: 合法配置写后回真态
- **WHEN** 为 Facebook 账号设置 enabled=true、dailyCap=1 和合法动作周历
- **THEN** 专属存储写入并回读相同真态，RiskController 与公共内容周历保持不变
