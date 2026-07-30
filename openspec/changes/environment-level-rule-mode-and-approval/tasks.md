# Tasks

> 前置依赖：`facebook-rule-mode-cadence` 与 `client-facebook-rule-mode-toggle` 的能力规格尚未并入 `openspec/specs/`。本变更的 `facebook-rule-mode` 与 `client-facebook-rule-mode-toggle` delta MUST NOT 先于那两条变更归档而生效；实装可并行，归档顺序必须在后。

## 0. 前置确认

- [x] 0.1 确认 `client-facebook-rule-mode-toggle` 的 Edge 侧提交已集成到 `aidcp-edge` 默认分支（Cloud 侧 `0622af9` 已在 master，Edge 侧 `8d377a6` 当时尚未集成），避免本变更在一个缺少客户端环境作用域开关的基线上改造。
- [x] 0.2 盘点存量数据：统计两张策略表中账号行的数量，以及其中绑定未知 / 绑定冲突 / 跨客户争用因而无法回填的账号，形成人工处理清单。

## 1. aidcp-api — 数据层与归属完成契约

- [x] 1.1 为 `facebook_rule_mode_config` 与 `account_comment_approval_policy` 增加环境键列与唯一约束（expand，非破坏性；不删旧账号键列、不加 NOT NULL）。
- [x] 1.2 按 `client_environments` 现有唯一绑定回填存量配置到所属环境；绑定冲突、跨客户争用或环境缺失的行 MUST NOT 回填，写入具名跳过原因。
- [x] 1.3 两张表的存储与内存副本改以环境键读写，并提供按账号反查环境的读路径；反查得不到唯一环境时按各自安全方向 fail-closed（规则模式=未启用；审批策略=`source_rules`）。
- [x] 1.4 归属完成接口在严格白名单内新增运行方式与审批模式可选字段；非 Facebook 平台、非法枚举、非布尔值以及「慢启动与规则模式同时为真」MUST 在注册环境前整请求拒绝。
- [x] 1.5 新增 env-scoped 评论审批覆盖读写路由：只接受模式枚举、逐请求校验 env ownership、客户来源审计署名与管理员可区分、未绑定环境可保存可读取。
- [x] 1.6 旧账号键列停止参与运行时读写与判定，保留数据供回滚；删列不在本变更范围。
- [x] 1.7 针对上述各项补聚焦测试：回填正确性与跳过判据、反查歧义 fail-closed 双方向、白名单严格性、互斥意图拒绝、非所有者 fail-closed、未绑定环境读写、幂等重试不复原。

## 2. aidcp-cloud — 运行期读路径与仲裁

- [x] 2.1 规则模式裁决改读当前绑定账号所在环境的配置；反查失败暴露具名 blocker，MUST NOT 回落任何账号键存量值。
- [x] 2.2 有效审批模式合成点改为按账号反查环境后读策略；反查失败回落 `source_rules` 并记具名退化原因。
- [x] 2.3 两项配置接入既有环境↔账号映射的同一次刷新，热路径不新增按请求查询。
- [x] 2.4 确认规则进度、浏览去重事实与批次终态三张表保持账号键不变；补测「换绑后新账号从零收集、不继承去重集合、旧账号在途批次按自身账号键如实收敛」。
- [x] 2.5 确认慢启动对规则模式的绝对优先权、规则定义版本、风控与配额安全闸逐条未变，补回归测试。
- [x] 2.6 面板 API 的规则模式与审批策略写入口改按环境定位并回读真态。
  <!-- aidcp-cloud 6a77b05: added strict envKey PUTs and environment-list truth projections, removed account-targeted PUTs, returned each setter's committed row without a second fallible read, and projected execution binding with the runtime resolver. Validation: 53 focused Panel/policy tests, full 3916 pass + 11 skipped, typecheck. -->

## 3. aidcp-edge — 创建表单与提交契约

- [x] 3.1 Facebook 创建表单新增运行方式三选一（普通 / 冷启动 / 规则），取代写死的慢启动意图；单个与批量共用，批量对全批一致生效。
- [x] 3.2 新增可选全局免审勾选，默认关闭，与运行方式相互独立；仅 Facebook 展示，主进程对非 Facebook 的免审意图诚实拒绝。
- [x] 3.3 主进程按所选运行方式翻译成提交字段，并拒绝同时携带慢启动与规则模式开启意图的请求。
- [x] 3.4 改写创建区文案：删除「Facebook 单个、批量新建环境均默认开启慢启动」的旧表述；未选冷启动时不追加风险告警或 Tooltip，但回执必须如实反映未配置慢启动；免审文案不得暗示放宽风险、配额、去重或平台确认。
- [x] 3.5 创建回执如实区分本地创建、客户归属与各项配置确认状态，云端未确认前不宣称任何一项已生效。
- [x] 3.6 补 Electron 契约与 renderer 测试：三选一互斥、平台门禁双层、批量一致生效、免审默认关闭、非乐观回执呈现。

## 4. aidcp-console — 按环境配置

- [x] 4.1 规则模式开关由账号维度改为环境维度，保留写后回真态与非乐观呈现。
- [x] 4.2 全局免审选择由账号维度改为环境维度；未绑定环境可配置并如实标注当前没有执行对象。
- [x] 4.3 界面明确该配置作用于环境、由当前绑定账号执行，换绑后不展示旧账号为当前生效者。
- [x] 4.4 补对应前端测试。
  <!-- aidcp-console 8798fd9: moved both controls to Environments, removed account-targeted writes, kept account runtime progress read-only, surfaced stored definition mismatch with a safe disable path, and only claims an executor for a matching unique binding. Validation: 38 focused tests, full single-worker 304 pass + 1 skipped, typecheck, production build. -->

## 5. 验证与集成

<!-- aidcp-cloud 985d47e / aidcp-edge 959504d — land-change 跑完 acceptance+全量+typecheck 才 ff 推送 -->
<!-- 集成期间基线三次前移：two-tier cadence 占 0094/0095、后续变更占 0096，本变更迁移最终定为 0097；schema 契约常量、两个存储的 fail-closed 版本号、属主归属断言与迁移提示标签同步改号 -->
<!-- 2026-07-28 deployed dev — 0097 applied (expand, 20ms)；回填：规则模式 22→20（2 行 environment_missing）、审批策略 22→21（1 行 environment_missing）；20 行新配置全部带 v2 定义身份，证实 CHECK 必须新旧都接受 -->
<!-- 2026-07-30 DEV closeout — deployed aidcp-cloud 6a77b05 and aidcp-console 8798fd9 from clean defaults. Backups: cloud.bak.20260730-151307.tar.gz, cloud/.env.bak.20260730-151307, console.bak.20260730-151307.tar.gz. Migration status: content/automation/api pending=0; enforce schema gates passed; service active with NRestarts=0; writer lock held; 8787/8090/8088/8091 healthy; PostgreSQL and Feishu ready. Authenticated environment catalog: 99 rows, Facebook rule projections 72/72, comment approval projections 99/99, binding states 65 bound + 34 unbound. Cloud and Console checksum deltas=0. -->

- [x] 5.1 各仓跑聚焦测试 → 全量测试 → typecheck，输出有界记录。
  <!-- Cloud: focused Panel/policy 53/53, acceptance composition 25/25, full 3916 pass + 11 skipped, typecheck. Console: focused 38/38, full single-worker 304 pass + 1 skipped, typecheck and Vite production build. Two default-worker Console attempts timed out only in untouched suites; isolated reruns passed, so the deterministic single-worker full run is the recorded gate. -->
- [x] 5.2 各 worktree rebase 到最新默认分支、重跑必需验证、fast-forward 集成并推送，回写本清单的 commit-sha。
  <!-- All feature tips were direct descendants of the fetched defaults, so no rebase rewrite was needed. Fast-forwarded and pushed: aidcp-cloud master 6a77b05, aidcp-console master 8798fd9, aidcp main implementation record ab603763. This follow-up records the completed integration gate. -->
- [x] 5.3 `openspec validate environment-level-rule-mode-and-approval --strict` 通过。
  <!-- 2026-07-30 strict validation passed after Cloud/Console implementation and delivery-boundary updates. -->

## 6. 交付边界

- [x] 6.1 数据迁移在 DEV 先执行并核对回填结果与跳过清单，再谈其它环境。
- [x] 6.2 客户端与服务端的归属完成契约扩展必须同批上线；新客户端配旧服务端会因白名单整请求 400 而建不出环境，发版顺序需显式核对。
  <!-- Release-order check: Cloud 985d47e and Edge 959504d are both ancestors of their current origin/master. DEV received the Cloud contract/migration before any future installer release; no installer is produced by this change. Any later client release must target a server at or after that Cloud contract. -->
- [x] 6.3 OL 部署、Edge 打包签名与真实账号写入验收不在本变更范围，分别作为独立事实报告。
  <!-- Boundary retained: this completion deploys only DEV Cloud/Console after integration; no OL mutation, Edge package/signing, or real-account platform write is authorized. -->
- [x] 6.4 规则模式脱离人设入口闸不在本变更范围，另立变更承接。
  <!-- Tracked separately by active change facebook-rule-mode-without-persona; no persona-gate behavior is changed here. -->
