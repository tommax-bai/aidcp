# account-persona-config Specification

## Purpose
TBD - created by archiving change account-persona-config. Update Purpose after archive.
## Requirements
### Requirement: 账号人设可按账号持久化编辑，缺省回落打包默认绝不 brick

系统 SHALL 支持**按账号**配置人设（soul：identity / interests / behavior_guidelines），落 PostgreSQL `persona_config` 表（`account_id` 主键，外键引用 `accounts(account_id)`）。**系统不存在默认 / 兜底人设**：任一账号**缺行 / 人设为空 / 解析失败**时，解析器 MUST 返回明确的「无人设」信号（null），MUST NOT 回落到任何打包默认人设，MUST NOT 抛错。「无人设」账号能否运行由各入口闸决定（见 `persona-gated-session-start` 与 `mandatory-account-persona`）——解析器只如实报告有无。人设存储初始化失败 MUST fail-closed：全部账号按未绑人设对待（被入口闸拒绝），MUST NOT 以任何默认人设「带病运行」。写入 MUST 先持久化成功、再刷新内存镜像（绝不出现「镜像已变、库未变」的不一致）。

写入 SHALL 在**持久化成功的同一个数据库事务内**推进人设镜像的版本，供跨进程消费方据以失效重载；持久化失败 MUST NOT 推进版本。解绑（空人设保存）与绑定同样 MUST 推进版本——否则「客户在应用里清空了人设」这件事在其它进程里永远不可见。

当人设由**跨进程本地只读副本**提供时，「副本中缺行」MUST NOT 直接等同于「无人设」：只有副本新鲜时才可作此判定；副本超过声明的陈旧上限时 MUST 表达为「未知」，由入口闸按不可用态处理。人设存储**初始化失败**仍按上述 fail-closed 规则以「未绑」对待（那是权威侧明确不可用、且发生在进程启动期，与运行期副本陈旧是两回事）。

#### Scenario: 账号无人设行返回明确无人设信号

- **WHEN** 某账号在 `persona_config` 无行（或行内容为空 / 解析失败），且权威存储可读
- **THEN** 解析器返回「无人设」（null）信号——不抛错、不返回任何默认 soul；该账号的浏览 / 发布 / 评论入口闸据此诚实拒绝

#### Scenario: 人设存储初始化失败 fail-closed

- **WHEN** 进程启动时人设存储初始化失败（如 PG 不可用）
- **THEN** 全部账号按「未绑人设」对待、被入口闸拒绝运行，系统 MUST NOT 以默认人设继续跑任务（宁可停摆，不静默假成功）

#### Scenario: 写库成功才刷新镜像

- **WHEN** 面板写入某账号人设且 PG 持久化失败
- **THEN** 内存镜像不变、版本不变、返回诚实失败；绝不出现镜像与库不一致，也绝不出现版本已进而库未变

#### Scenario: 绑定与解绑都推进版本

- **WHEN** 某账号的人设被绑定，或被以空人设保存而解绑，且持久化成功
- **THEN** 人设镜像版本加一，其它进程的只读副本在有界时间内读到该变更

### Requirement: 人设写入经 soul 加载器校验，非法人设诚实拒绝绝不静默接受

写入某账号人设时，系统 MUST 用 soul 加载器（`loadSoulFromValue`）做保存前校验，仅在校验通过后写库。校验失败 MUST 拒绝写入、返回诚实原因（`persona_invalid`），MUST NOT 把非法人设落库、MUST NOT 刷新内存镜像、MUST NOT 返回成功。**空人设保存 MUST 被解释为显式解绑**：系统 SHALL 清除该账号的人设绑定，使该账号后续解析为「无人设」（null）并被既有浏览 / 发布 / 评论入口闸诚实拒绝，MUST NOT 回落任何默认人设，MUST NOT 保留一个空白但看似已绑定的人设行。

#### Scenario: 非法 YAML 被诚实拒绝

- **WHEN** 面板提交无法解析 / 缺必要字段的人设内容
- **THEN** 返回 `persona_invalid` 与诚实提示，库与镜像均不变

#### Scenario: 空人设保存解绑账号

- **WHEN** 面板或 API 直连提交空 / 全空白人设
- **THEN** 系统清除该账号的人设绑定，返回写后真态 `source=none`，该账号后续任务被未绑人设入口闸拒绝，MUST NOT 回落默认人设

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

账号人设接口（`GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId`）MUST 与其它 `/api/*` 一样受 JWT 守护。管理后台 SHALL 提供人设页（`/persona` 路由 + 导航）：列出账号、按账号编辑其人设并保存，回显当前生效值与来源——来源为**已绑定（override）/ 未绑定（none）**两态，**不存在「回落默认」态**；未绑定账号 MUST 以醒目标注提示（该账号会被拒绝运行）。前端 MUST 允许操作员清空编辑器并保存为解绑，保存成功后以服务端返回真态显示「未绑定」；该后台显式清空操作 MUST 同时清除账号已有的首作新人状态，使账号恢复为下一次成功建立人设时可重新触发新人引导的初始化状态。人设解绑与首作状态复位 MUST 原子完成；任一步失败时数据库与内存镜像 MUST 保持清空前状态，接口 MUST 返回失败而非部分成功。前端 MAY 对非空内容做格式提示，但 MUST NOT 用必填校验阻止显式解绑。写操作 MUST 非乐观——返回服务端写后真态（含生效人设 / 来源 + `updatedBy` + `updatedAt`），并用诚实文案（已保存 / 已解绑 / 人设格式无效无法保存），MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求任一 `/api/persona*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态含审计字段

- **WHEN** 面板成功保存某账号人设
- **THEN** 响应含服务端写后生效人设与 `updatedBy` / `updatedAt`，前端以真态刷新（非乐观）

#### Scenario: 未绑定账号在列表醒目标注

- **WHEN** 人设页列出一个无人设行的账号
- **THEN** 该行来源显示「未绑定」红标（而非「回落默认」），提示其任务会被拒绝运行

#### Scenario: 清空编辑器保存为未绑定并复位初始化状态

- **WHEN** 操作员在人设页把某账号编辑器内容清空并保存
- **THEN** 后台原子清除该账号的人设绑定与首作新人状态，页面以服务端真态刷新为「未绑定」
- **AND** 系统 MUST NOT 在前端提示必填并阻止保存，也 MUST NOT 清理该账号的发布、精选、风控或主数据

#### Scenario: 首作状态复位失败不产生部分解绑

- **WHEN** 后台清空人设时首作新人状态无法删除
- **THEN** 清空操作整体失败，原人设持久态与内存镜像保持不变
- **AND** 后台 MUST NOT 显示已解绑或返回部分成功

### Requirement: 账号人设支持严格校验的结构化强制互动规则

账号 soul MAY 包含可选 `mandatory_interactions` 列表；每条规则 MUST 具有账号内唯一、格式稳定的 `id`，非空语义条件 `when`，只含 `like` / `comment` 的非空动作集合，以及在含 `comment` 时必填的 `comment_guidance` 与显式 `comment_approval`（`review` / `auto_approve`）。为适配既有评论事件链，含 `comment` 的规则 MUST 同时含 `like`。loader MUST 限制规则数量与文本长度，拒绝重复 id、未知动作、未知审批模式和非法字段组合；任一规则非法 MUST 使整份人设以 `persona_invalid` 被拒，库与内存镜像均不变。

该字段 SHALL 与 identity / interests 一样经账号 persona 取值口热加载；保存成功后后续选卡、详情匹配、点赞与评论角色 MUST 使用新规则，无需重启。未配置该字段的账号 MUST 保持既有普通互动行为，MUST NOT 被推导出隐式强制规则。

#### Scenario: 合法强制规则保存并热加载
- **WHEN** 操作员给已绑定账号保存一条唯一 id、`actions=[like,comment]`、评论指引和 `comment_approval=auto_approve` 的合法规则
- **THEN** persona API 返回写后真态，后续浏览角色立即读到该规则，无需重启 cloud

#### Scenario: 非法规则整份拒绝
- **WHEN** 规则 id 重复、动作未知、含 comment 但无 like / 无评论指引、或审批模式非法
- **THEN** persona API 返回 `persona_invalid`，数据库与内存镜像保持保存前真态，MUST NOT 部分接受

#### Scenario: 未配置规则零回归
- **WHEN** 某账号人设不含 `mandatory_interactions`
- **THEN** 其选卡、点赞、评论门槛、冷却与审批行为与变更前逐位一致，系统 MUST NOT 从自由文本猜出强制授权

### Requirement: 人设行为模板支持结构化三档点赞倾向

账号 soul 的 `behavior_guidelines` MAY 包含可选 `like_affinity`，且存在时 MUST 严格为 `normal`、`like_more`、`like_most` 之一。loader MUST 拒绝未知档位，serializer MUST 保留该字段往返；字段缺省 SHALL 等价 `normal`，历史人设无需迁移。`like_affinity` 与 `like_principle` SHALL 同时进入账号级热加载人设，但 MUST NOT 自动生成、修改或暗示 `mandatory_interactions`。

#### Scenario: 合法档位往返不丢失

- **WHEN** 一份合法 soul 含 `behavior_guidelines.like_affinity=like_more` 并经 loader → serializer → loader 往返
- **THEN** 最终人设仍为 `like_more`，其他 identity、interests 与行为原则保持不变

#### Scenario: 历史人设缺字段按正常档

- **WHEN** 一份历史 soul 有 `behavior_guidelines` 但没有 `like_affinity`
- **THEN** loader 继续接受，运行时按 `normal` 解释，MUST NOT 要求数据库迁移

#### Scenario: 未知档位整份拒绝

- **WHEN** 保存的人设含未知 `like_affinity`
- **THEN** soul 校验以 `persona_invalid` 拒绝，数据库与内存镜像不变

#### Scenario: 倾向不产生强制互动规则

- **WHEN** 任一档位经 onboarding 生成并持久化
- **THEN** 产物不因档位出现 `mandatory_interactions`，普通倾向 MUST NOT 被解释为确定性点赞授权

### Requirement: 客户端人设视图只呈现当前真实人设并复用权威单写

面向客户的环境级人设读取 SHALL 仅在账号存在有效 `persona_config` 时返回当前 soul YAML；同时 SHALL 由 Cloud 解析并返回有界的人设摘要，包括身份名、定位、背景、语气、发言语言、兴趣方向、搜索种子与结构化点赞倾向。未绑定账号 MUST 返回明确 `missing` 且 persona 为空，MUST NOT 把后台编辑器使用的打包起点模板或任何示例人设冒充为当前人设。

客户确认更新 SHALL 复用与 Console 相同的人设单写通道和 soul 校验，写库成功后才刷新内存镜像并触发账号热加载；响应 SHALL 为写后真态，MUST NOT 本地或服务端乐观判成功。客户视图 MUST NOT 暴露内部 `updatedBy` 或账号键。

#### Scenario: 已绑定账号返回可读摘要与完整定义

- **WHEN** 客户读取一个已有合法账号人设的授权环境
- **THEN** Cloud 返回当前 soul YAML、由同一份 soul 解析出的有界摘要和 `updatedAt`
- **AND** 客户端无需复制 soul 解析器即可展示当前人设

#### Scenario: 未绑定账号不展示模板假态

- **WHEN** 授权环境已绑定账号但该账号没有人设行
- **THEN** 客户视图明确返回 `missing` 且不返回打包默认/起点模板作为当前人设

#### Scenario: 客户更新后运行链即时使用新人设

- **WHEN** 客户在停止环境中确认保存一份合法新人设
- **THEN** 写入成功后后续浏览与发布在账号再次运行时直接读取新人设，无需重启 Cloud
- **AND** 保存回执只声明人设已更新，MUST NOT 声称浏览器或首作已经启动

### Requirement: Soul 写作语言可选解析、受控写入并热加载
Soul 类型、YAML loader 与 serializer SHALL 支持可选顶层 `writing_language`，存在时只允许 `zh-CN/en/vi`；缺省时旧人设仍可解析。Facebook 新生成/更新由入口强制存在，非 Facebook 继续缺省。保存成功后运行时 SHALL 从账号热加载 soul 读取，不建立第二份独立语言事实源。

#### Scenario: 旧 soul 无语言仍可加载
- **WHEN** 加载一份只有 identity/interests 的存量 soul
- **THEN** loader 正常返回人设且 `writing_language` 缺省，MUST NOT 因 schema 扩展把账号误判为无人设

#### Scenario: 合法语言 round-trip
- **WHEN** 含 `writing_language: vi` 的 soul 经 serializer 再由 loader 读取
- **THEN** 结果仍为 `vi`，其它 identity/interests/behavior 字段保持不变

#### Scenario: 非法持久化被拒
- **WHEN** 面板或 Edge persist 尝试保存 `writing_language: vietnam`
- **THEN** 现有人设单写通道返回 `persona_invalid` 且不落库、不刷新镜像

### Requirement: 账号全局评论免审覆盖人设规则局部审批模式

结构化 `mandatory_interactions[].comment_approval` SHALL 继续表达 `source_rules` 账号的局部站立授权；当账号显式配置全局评论 `auto_approve_all` 时，Cloud MUST 将该账号所有 mandatory 评论的有效模式解析为 `auto_approve`，即使命中规则写为 `review`。该覆盖 MUST NOT 改写 persona 原文或放宽 mandatory 匹配、详情确认与动作集合；免审通知仅作旁路记录，不参与授权。

#### Scenario: 全局免审覆盖 mandatory review
- **WHEN** `auto_approve_all` 账号命中一条详情确认且 `comment_approval=review` 的 mandatory 评论规则
- **THEN** 该评论直接获得授权，MUST NOT 等待按钮审批；旁路通知失败不阻止提交

#### Scenario: 来源规则账号保持 persona 局部模式
- **WHEN** 账号为 `source_rules`
- **THEN** mandatory 规则的 `review|auto_approve` 继续逐条决定该来源审批方式，MUST NOT 被改写

#### Scenario: 覆盖不改变规则匹配
- **WHEN** `auto_approve_all` 账号的帖子未命中任何 mandatory 规则
- **THEN** 免审只作用于实际由普通评论链产生的候选，MUST NOT 伪造 mandatory 命中或强制生成评论

