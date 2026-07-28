# Design

## 1. 现状坐标（带文件:行）

**规则模式配置**以账号为主键持久化：`aidcp-cloud/migrations/0092_facebook_rule_mode_config.sql:5`（`account_id TEXT PRIMARY KEY`），存储与内存副本在 `aidcp-cloud/src/config/facebook-rule-mode-store.ts`，运行期裁决在 `aidcp-cloud/src/orchestrator/facebook-rule-mode.ts:12-37`，后台写入口 `aidcp-cloud/src/panel/panel-server.ts:1284,1959`。

**规则进度 / 去重 / 批次**同样以账号为键：`aidcp-cloud/migrations/0093_facebook_rule_mode_runtime.sql`（`facebook_rule_progress`、`facebook_rule_view_fact`、`facebook_rule_batch` 均以 `account_id + execution_target + definition_id + definition_version` 组主键）。**本变更不动这三张表。**

**评论审批覆盖策略**以账号为主键并外键到账号：`aidcp-api/migrations/0056_scoped_approval_policy.sql:10`（`account_id TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE`），存储在 `aidcp-cloud/src/config/approval-policy-store.ts:15-76`，有效模式合成点在 `aidcp-cloud/src/server.ts:4049`，后台写入口 `aidcp-api/src/panel/panel-server.ts:1738`。

**已经完成同构迁移的先例**是慢启动：`openspec/changes/archive/2026-07-26-environment-level-slow-start/`。其成品形态直接可复用——环境读设置与绑定三态在 `aidcp-api/src/client-auth/client-user-store.ts:1015-1060`，环境级单写（归属校验与更新同一语句、账号字段完全不参与）在 `:1064-1095`，按账号反查环境设置的热路径在 `:1003-1011`。

**创建链路**今天写死开启慢启动：`aidcp-edge/src/electron/main.cjs:7346`（`const slowStartEnabled = platform === 'facebook'`），经 `:896-935` 随归属完成请求提交，服务端字段白名单在 `aidcp-api/src/client-auth/client-auth-server.ts:1928`。创建表单在 `aidcp-edge/src/electron/renderer/index.html:1060-1082`，提交组装在 `aidcp-edge/src/electron/renderer/renderer.js:7206-7262`。

**在途依赖**：`client-facebook-rule-mode-toggle` 已实装到 Cloud（`aidcp-cloud` 提交 `0622af9`，已在 master）与 Edge（提交 `8d377a6`，尚未集成到 master），它提供的是 env-scoped 的 API 寻址，但持久化仍落账号键——正是本变更要升级的那一层。

## 2. 键迁移形态（照抄慢启动那次）

三步，非破坏性：

1. **expand**：两张表加环境键列并建唯一约束；不删旧账号键列、不加 NOT NULL。
2. **回填**：按 `client_environments` 现有唯一绑定，把存量账号行的配置写到其所在环境。存在绑定冲突（同一账号出现在多个环境）或跨客户争用的账号行 MUST NOT 回填，记具名跳过原因等人工处理。
3. **切读**：运行时读写全部切到环境键；旧账号键列停止参与新读写与判定，暂留作可回滚数据。删列另起变更。

回滚形态是只切读端回退，不回滚数据。

## 3. 反向解析与失败方向

环境到账号结构上是一对一（环境记录只有一个账号字段）；账号到环境在库层没有唯一约束，运行期靠「同一账号出现在多个环境」与「跨客户争用」两个判据识别为绑定冲突。所以按账号反查环境**必然可能失败**，两项配置的失败方向都必须是收紧的：

| 配置 | 解析失败时 | 为什么这是收紧方向 |
| --- | --- | --- |
| 规则模式 | 不启用规则模式，暴露具名 blocker | 不跑比错跑安全；与现有「慢启动真态未知即 fail-closed」一致 |
| 全局免审 | 回落 `source_rules`（人审） | 与现有「策略不可读不扩权」逐字一致，不新增判例 |

热路径不新增查询：复用慢启动那次建立的环境↔账号映射，两项配置作为该映射的附加字段随同一次刷新供给。

## 4. 三种运行方式如何映射到两个已有事实

创建表单的三选一是**呈现层的互斥**，落库仍是两个独立事实，运行期仲裁一字不改（慢启动对规则模式保持绝对优先权）：

| 选择 | 环境慢启动 | 环境规则模式 |
| --- | --- | --- |
| 普通 | 不开启 | 关 |
| 冷启动 | 开启 | 关 |
| 规则 | 不开启 | 开 |

**这里有一处真实的行为变化**：今天 Facebook 创建无条件开启慢启动，选择普通或规则等于新号从第一天就吃满每日额度，没有 7 天爬坡保护。用户 2026-07-28 裁定三者互斥且**界面不为此追加风险提示**——运行方式是运营的显式选择，与 `scoped-approval-policy` 对全局免审「不加解释性告警或 Tooltip」的既有口径一致。创建回执仍 MUST 如实反映未配置慢启动，MUST NOT 沿用「已默认开启慢启动」的旧文案：不提示风险不等于可以谎报状态。

之所以不让「规则」同时开启慢启动：慢启动激活期间规则模式按既有仲裁根本不启动，两个都开等于建出一个要等毕业才动的账号。要保留爬坡就选冷启动、毕业后再切规则，这条路径经环境级开关随时可走。

## 5. 免审开放给客户端的授权边界

放宽写入口是扩权动作，按四条收口：

- **归属**：逐请求校验 env ownership，与慢启动 env-scoped 写同一权威范围；非所有者 fail-closed，且不泄露该环境的账号身份。
- **入参**：请求体只接受模式枚举，夹带账号选择器或任何其它键整块拒绝。
- **审计**：客户写入的操作人身份 MUST 与后台管理员可区分，不复用管理员署名。
- **不扩安全闸**：免审只免第二次人工按钮，MUST NOT 绕过风险、配额、去重、目标复核、平台确认与真实终态记录——这条是既有要求，本变更逐字保留。

## 6. 为什么进度不跟着迁

配置属于环境这个稳定对象；而「已看过哪些内容」「本轮凑到第几条」是账号自己的行为历史。若把进度也挂到环境，换账号后新账号会继承旧账号的浏览去重集合，导致新账号跳过它其实从未看过的内容——这既不真实，也让「十条已确认浏览」这个规则定义失去意义。所以进度、去重事实与批次终态继续按账号存续，换账号即从零重新收集。

慢启动那次做的是相反选择（起点也随环境走、换账号继承已走天数），因为慢启动约束的是环境与出口链路的成熟度，不是账号的行为历史。两者性质不同，此处不照抄。

## 7. 交付顺序

1. 数据层 expand + 回填（api 单写域内，两表与环境花名册同属主）。
2. 云端读路径切环境键 + 反查失败 fail-closed。
3. customer-auth 免审路由 + 归属完成契约扩展（客户端与服务端白名单必须同批上线，否则新客户端配旧服务端会整请求 400、直接建不出环境）。
4. Edge 创建表单三选一与免审勾选。
5. Console 改按环境配置。
6. 旧账号键列停读留回滚，删列另起变更。
