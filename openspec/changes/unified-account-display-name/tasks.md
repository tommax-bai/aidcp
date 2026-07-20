## 1. Cloud 统一账号显示名真源

- [x] 1.1 新增唯一的账号显示名纯解析模块与测试，覆盖运营别名、平台昵称、运营标签、账号 ID 的优先级及来源。
  <!-- aidcp-cloud: added account-display-name resolver and focused tests; 35/35 focused store/resolver tests pass, typecheck passes. -->
- [x] 1.2 为 `accounts` 增加 additive `operator_alias` 自愈列；扩展 AccountStore 预热缓存、设置/清除接口和可匹配名称目录，保持平台昵称写入互不覆盖。
  <!-- aidcp-cloud: additive operator_alias DDL, cache, set/clear and candidate APIs implemented without changing platform nickname writes. -->
- [x] 1.3 增加账号存储测试，覆盖非空 trim、空值清除、缓存写后可见、平台昵称刷新和同名机器身份隔离。
  <!-- aidcp-cloud: focused tests cover trim, clear fallback, immediate cache visibility, nickname refresh isolation and ID exclusion. -->

## 2. 客户环境运营别名写入口

- [x] 2.1 在 ClientUserStore 增加“当前客户自有环境 → 无冲突绑定账号”的收窄解析，区分越权、未绑定和账号缺失。
  <!-- aidcp-cloud: dedicated ownership/current-binding resolver preserves environment_not_owned, binding_unknown, account_not_found and binding_conflict. -->
- [x] 2.2 增加 `PUT /environments/:envKey/operator-alias`，通过 AccountStore 设置/清除别名并返回统一显示名与来源。
  <!-- aidcp-cloud: authenticated env-scoped PUT accepts only alias, derives accountId server-side and returns confirmed display projection. -->
- [x] 2.3 补客户鉴权 API/存储测试，覆盖成功设置、空值清除、越权 403、未绑定 409、无效输入和写入失败诚实回执。
  <!-- aidcp-cloud: 73/73 focused client-auth and client-user-store tests pass; typecheck passes. -->

## 3. Cloud Panel 与飞书统一消费

- [x] 3.1 扩展 Panel 账号 DTO 和查询映射，返回 `operatorAlias`、`displayName`、`displayNameSource`，所有映射复用统一解析器。
  <!-- aidcp-cloud: PanelAccount and publish history both reuse resolveAccountDisplayName; panel contract version advanced to v6. -->
- [x] 3.2 把飞书审批、告警、指令回执、评论/发布终态和委托任务的账号可见名统一接到账号目录；缺可读名显示“未获取昵称”，机器载荷保持 ID。
  <!-- aidcp-cloud: human Feishu surfaces use preferred directory names or 未获取昵称; routing/callback/task accountId remains unchanged. -->
- [x] 3.3 把飞书昵称选号和委托任务账号解析改为接受运营别名、平台昵称与运营标签，重名 fail closed，回执统一显示首选名。
  <!-- aidcp-cloud: slash commands and delegated tasks match the shared candidate directory and preserve ambiguity rejection. -->
- [x] 3.4 补 Panel、飞书卡片/通知、命令解析和机器载荷不变测试。
  <!-- aidcp-cloud: 110/110 focused Panel/Feishu/delegated tests pass; earlier combined Panel server suite and typecheck also pass. -->

## 4. Edge 人工昵称设置、清除与 Cloud 确认

- [x] 4.1 扩展本地环境成员保留系统名影子；人工期间系统刷新只更新影子，空内容清除人工来源并回落系统昵称。
  <!-- aidcp-edge: roster/handle/renderer preserve systemName; clearing removes manual markers and restores the latest observed system name. -->
- [x] 4.2 将昵称 IPC 改为本地快照 + Cloud 窄写的一致流程；renderer 保持 await 前 pending，成功确认，任一步失败完整回滚并提示真实原因。
  <!-- aidcp-edge: optimistic UI precedes the first await; env-scoped customer-auth write confirms success; Cloud/local failures restore snapshots. -->
- [x] 4.3 为升级前已有 `nameSource: manual` 成员增加客户会话恢复后的有界同步和明确未同步状态，不伪造全局成功。
  <!-- aidcp-edge: login/maintenance retry at most 20 aliases per round with 5s requests; failures retain local names with an amber unsynced marker. -->
- [x] 4.4 补 Edge 纯逻辑、IPC、renderer、客户鉴权请求和 Electron 原生加载回归测试。
  <!-- aidcp-edge: 60/60 nickname renderer/IPC tests and 94/94 fleet/companion/native-Electron tests pass; typecheck passes. -->

## 5. Console 统一账号显示

- [x] 5.1 扩展 `PanelAccount` 类型并把账号表、人设、内容、用量、联系人及其它账号 join 统一改为消费服务端 `displayName/displayNameSource`。
  <!-- aidcp-console/cloud: PanelAccount and content-schedule catalog carry unified fields; account table marks operator aliases with a restrained blue treatment. -->
- [x] 5.2 删除前端重复的昵称优先级，仅保留旧 DTO 的账号 ID 兼容回落，并补统一展示/清除回落测试。
  <!-- aidcp-console: helper no longer reads nickname/label priority; 45/45 focused page/helper tests and typecheck pass. -->

## 6. 验证、集成与 dev 发布

- [x] 6.1 运行 Edge/Cloud/Console focused tests、适用 acceptance、全量测试、typecheck/build，并记录真实通过范围。
  <!-- Cloud: focused 96/96 after final notification-priority audit, final full 2637 pass + 8 skipped, acceptance 59/59, typecheck/build pass. Edge: focused nickname 60/60 and fleet/native-Electron 94/94, full 1937/1937, acceptance 25/25, typecheck pass. Console: focused 45/45, isolated full 201 pass + 1 skipped, typecheck/build pass; the earlier three-suite parallel run was discarded after an isolated green rerun. -->
- [x] 6.2 运行 `openspec validate unified-account-display-name --strict`，核对 Cloud 优先部署、Console 后部署、Edge 重启和未构建安装包边界。
  <!-- Strict validation passes. Runtime order is Cloud then Console; Edge behavior requires a restarted source runtime/new release, and this change deliberately does not build an installer. -->
- [ ] 6.3 各仓提交后 fetch/rebase 最新默认分支，复验并 fast-forward 推送 Edge/Cloud/Console/control 默认分支。
- [ ] 6.4 按部署规范从默认分支部署 Cloud 与 Console 到 dev，验证服务、监听、健康、PostgreSQL additive 列、Panel DTO 与飞书连接；不构建桌面安装包。
