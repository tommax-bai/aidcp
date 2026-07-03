# account-persona-config Specification

## Purpose
TBD - created by archiving change account-persona-config. Update Purpose after archive.
## Requirements
### Requirement: 账号人设可按账号持久化编辑，缺省回落打包默认绝不 brick

系统 SHALL 支持**按账号**配置人设（soul：identity / interests / behavior_guidelines / session_limits），落 PostgreSQL `persona_config` 表（`account_id` 主键，外键引用 `accounts(account_id)`）。任一账号**缺行 / 人设为空 / 解析失败**时，该账号的人设 MUST 回落到随源码打包的 `soul.yaml`（启动已 fail-fast 验证可解析的默认人设），解析器 MUST NOT 抛错、MUST NOT 使该账号的浏览或发布链路 brick。写入 MUST 先持久化成功、再刷新内存镜像（绝不出现「镜像已变、库未变」的不一致）。

#### Scenario: 按账号写入人设并持久化
- **WHEN** 经面板写入某账号（如 `default`）的人设并保存成功
- **THEN** 该人设落 `persona_config`（外键到该 `accounts` 行）并刷新内存镜像，重启后仍在

#### Scenario: 账号无人设行回落打包默认不 brick
- **WHEN** 某账号在 `persona_config` 无行，或其人设字段为空
- **THEN** 该账号的人设解析回落到打包 `soul.yaml`，浏览与发布链路正常运行、不报错、不 brick

#### Scenario: 写库成功才刷新内存镜像
- **WHEN** 写人设时数据库瞬断、写库失败
- **THEN** 内存镜像保持原值不变，绝不出现镜像与库不一致

### Requirement: 人设写入经 soul 加载器校验，非法人设诚实拒绝绝不静默接受

写入某账号人设时，系统 MUST 用 soul 加载器（`loadSoulFromValue`）做保存前校验，仅在校验通过后写库。校验失败 MUST 拒绝写入、返回诚实原因（`persona_invalid`），MUST NOT 把非法人设落库、MUST NOT 刷新内存镜像、MUST NOT 返回成功。空人设 MUST 被视作「清除覆盖 → 回落打包默认」而非非法（不校验、不报错）。

#### Scenario: 非法人设校验不过被拒不落库
- **WHEN** 写入一段缺必填字段或类型错误、`loadSoulFromValue` 校验抛错的人设
- **THEN** 系统返回 `persona_invalid`，不写库、不刷镜像、绝不假成功

#### Scenario: 合法人设校验通过才落库
- **WHEN** 写入一段 `loadSoulFromValue` 可解析为强类型 Soul 的人设
- **THEN** 校验通过后落库并刷镜像，返回写后真态

#### Scenario: 空人设视作清除覆盖
- **WHEN** 提交空人设
- **THEN** 系统将该账号置为「回落打包默认」，不视作非法错误

### Requirement: 派发时按当前账号解析人设，编辑热加载无需重启

决策派发链路 SHALL 在**派发时按当前账号解析人设**（取值口 getter），替换此前启动时拍下的全局人设快照。浏览侧约 11 个角色的 prompt 构建与发布侧角色 SHALL 经同一取值口取人设，使面板写入后两侧 prompt **无需重启即改用新人设**（热加载）。该取值口 MUST 永不抛——任一账号解析失败按回落链回落打包默认。

#### Scenario: 后台改人设后浏览角色即时生效
- **WHEN** 经面板把某账号人设改为新内容并保存成功
- **THEN** 该账号后续浏览角色的 prompt 使用新人设的 identity / interests，无需重启进程

#### Scenario: 发布角色同样吃到最新人设
- **WHEN** 某账号人设被更新后触发一次发布
- **THEN** 发布侧角色（如内容创作 / 标题创作）按该账号最新人设生成，无需重启

#### Scenario: 取值口永不抛
- **WHEN** 某账号人设镜像存在但意外无法解析
- **THEN** 取值口记 warn 并回落打包默认人设，绝不抛错中断派发

### Requirement: 后台账号人设页受 JWT 守护且写非乐观

账号人设接口（`GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId`）MUST 与其它 `/api/*` 一样受 JWT 守护。管理后台 SHALL 提供人设页（`/persona` 路由 + 导航）：列出账号、按账号编辑其人设并保存，回显当前生效值与来源（覆盖 / 回落）。写操作 MUST 非乐观——返回服务端写后真态（含生效人设 + `updatedBy` + `updatedAt`），并用诚实文案（已保存 / 人设格式无效无法保存），MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒
- **WHEN** 未带有效 JWT 请求任一 `/api/persona*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态含审计字段
- **WHEN** `PUT /api/persona/:accountId` 成功
- **THEN** 返回服务端持久化后的真实生效人设与 `updatedBy` / `updatedAt`，前端据真态 round-trip 重渲染

#### Scenario: 人设格式无效页面诚实报错
- **WHEN** 在人设页提交一段校验不过的人设并保存
- **THEN** 页面显示诚实失败文案（人设格式无效无法保存），不渲染为已保存

