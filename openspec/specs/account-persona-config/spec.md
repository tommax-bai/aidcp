# account-persona-config Specification

## Purpose
TBD - created by archiving change account-persona-config. Update Purpose after archive.
## Requirements
### Requirement: 账号人设可按账号持久化编辑，缺省回落打包默认绝不 brick

系统 SHALL 支持**按账号**配置人设（soul：identity / interests / behavior_guidelines），落 PostgreSQL `persona_config` 表（`account_id` 主键，外键引用 `accounts(account_id)`）。**系统不存在默认 / 兜底人设**：任一账号**缺行 / 人设为空 / 解析失败**时，解析器 MUST 返回明确的「无人设」信号（null），MUST NOT 回落到任何打包默认人设，MUST NOT 抛错。「无人设」账号能否运行由各入口闸决定（见 `persona-gated-session-start` 与 `mandatory-account-persona`）——解析器只如实报告有无。人设存储初始化失败 MUST fail-closed：全部账号按未绑人设对待（被入口闸拒绝），MUST NOT 以任何默认人设「带病运行」。写入 MUST 先持久化成功、再刷新内存镜像（绝不出现「镜像已变、库未变」的不一致）。

#### Scenario: 账号无人设行返回明确无人设信号

- **WHEN** 某账号在 `persona_config` 无行（或行内容为空 / 解析失败）
- **THEN** 解析器返回「无人设」（null）信号——不抛错、不返回任何默认 soul；该账号的浏览 / 发布 / 评论入口闸据此诚实拒绝

#### Scenario: 人设存储初始化失败 fail-closed

- **WHEN** 进程启动时人设存储初始化失败（如 PG 不可用）
- **THEN** 全部账号按「未绑人设」对待、被入口闸拒绝运行，系统 MUST NOT 以默认人设继续跑任务（宁可停摆，不静默假成功）

#### Scenario: 写库成功才刷新镜像

- **WHEN** 面板写入某账号人设且 PG 持久化失败
- **THEN** 内存镜像不变、返回诚实失败；绝不出现镜像与库不一致

### Requirement: 人设写入经 soul 加载器校验，非法人设诚实拒绝绝不静默接受

写入某账号人设时，系统 MUST 用 soul 加载器（`loadSoulFromValue`）做保存前校验，仅在校验通过后写库。校验失败 MUST 拒绝写入、返回诚实原因（`persona_invalid`），MUST NOT 把非法人设落库、MUST NOT 刷新内存镜像、MUST NOT 返回成功。**空人设 MUST 被拒绝**（`persona_required`）——系统无默认人设可回落，「清空」不再是合法语义；绕过前端直接调 API 同样被拒、不落库。

#### Scenario: 非法 YAML 被诚实拒绝

- **WHEN** 面板提交无法解析 / 缺必要字段的人设内容
- **THEN** 返回 `persona_invalid` 与诚实提示，库与镜像均不变

#### Scenario: 空人设被拒绝而非视作清除

- **WHEN** 面板或 API 直连提交空 / 全空白人设
- **THEN** 返回 `persona_required`（HTTP 400），MUST NOT 落库、MUST NOT 把该账号置为「回落默认」（系统已无默认人设）

### Requirement: 派发时按当前账号解析人设，编辑热加载无需重启

决策派发链路 SHALL 在**派发时按当前账号解析人设**（取值口 getter），替换此前启动时拍下的全局人设快照。浏览侧角色的 prompt 构建与发布侧角色 SHALL 经同一取值口取人设，使面板写入后两侧 prompt **无需重启即改用新人设**（热加载）。取值口对「无人设」返回明确信号（null）而非默认 soul；**正常路径下未绑账号在入口闸即被拒、不会走到派发**——严格取值口在闸后意外遇到「无人设」时 MUST 以 `no_persona` 诚实失败（防御纵深），MUST NOT 回落任何默认人设继续派发。

#### Scenario: 后台改人设后浏览角色即时生效

- **WHEN** 经面板把某账号人设改为新内容并保存成功
- **THEN** 该账号后续浏览角色的 prompt 使用新人设的 identity / interests，无需重启进程

#### Scenario: 发布角色同样吃到最新人设

- **WHEN** 某账号人设被更新后触发一次发布
- **THEN** 发布侧角色（如内容创作 / 标题创作）按该账号最新人设生成，无需重启

#### Scenario: 闸后意外无人设按 no_persona 诚实失败

- **WHEN** 某任务已过入口闸、执行中该账号人设被解绑（TOCTOU），严格取值口解析得「无人设」
- **THEN** 该任务以 `no_persona` 诚实失败并记日志，MUST NOT 回落默认人设继续、MUST NOT 静默成功

### Requirement: 后台账号人设页受 JWT 守护且写非乐观

账号人设接口（`GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId`）MUST 与其它 `/api/*` 一样受 JWT 守护。管理后台 SHALL 提供人设页（`/persona` 路由 + 导航）：列出账号、按账号编辑其人设并保存，回显当前生效值与来源——来源为**已绑定（override）/ 未绑定（none）**两态，**不存在「回落默认」态**；未绑定账号 MUST 以醒目标注提示（该账号会被拒绝运行）。前端 MUST 对空人设做必填拦截（留空不允许保存 + 诚实提示），与服务端 `persona_required` 校验双重把关。写操作 MUST 非乐观——返回服务端写后真态（含生效人设 + `updatedBy` + `updatedAt`），并用诚实文案（已保存 / 人设格式无效无法保存），MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求任一 `/api/persona*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态含审计字段

- **WHEN** 面板成功保存某账号人设
- **THEN** 响应含服务端写后生效人设与 `updatedBy` / `updatedAt`，前端以真态刷新（非乐观）

#### Scenario: 未绑定账号在列表醒目标注

- **WHEN** 人设页列出一个无人设行的账号
- **THEN** 该行来源显示「未绑定」红标（而非「回落默认」），提示其任务会被拒绝运行

