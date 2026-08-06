# derived-repo-fact-source

## ADDED Requirements

### Requirement: 翻转后派生仓是各自代码的唯一事实源，cloud 源码副本冻结

翻转标记置位后，`aidcp-api` / `aidcp-automation` / `aidcp-content` / `aidcp-kernel` / `aidcp-transport` SHALL 各自为本仓代码的唯一事实源。`aidcp-cloud` 的 `src/` 与 `migrations/` MUST 冻结在标记记录的 ref；任何对它们的后续改动 MUST 被任务准入闸与同步脚本拦下并指引到对应派生仓，MUST NOT 被静默接受。

#### Scenario: 翻转后有人按旧模式改 cloud 源码

- **WHEN** 翻转标记已置位，开发者在 `aidcp-cloud` 的 `src/` 下产生了相对冻结 ref 的改动，随后经 `scripts/new-change` / `scripts/spawn-change` 起新任务
- **THEN** 任务准入 MUST exit 1 并指名改动文件与「改到派生仓」的指引，MUST NOT 放行开工

#### Scenario: 翻转后运行重放同步

- **WHEN** 翻转标记已置位，任何人运行 `scripts/sync-split-repos --apply`（或 `--prune`）
- **THEN** 脚本 MUST 拒绝执行并说明事实源已翻转，MUST NOT 向任何派生仓写入一个字节；不带写入参数的运行 MUST 转为冻结校验（cloud 受冻结目录相对冻结 ref 有差异即失败并列出文件）

### Requirement: 共享包按已发布版本引用，钉子形态必须全部可识别

派生仓对 `aidcp-kernel` / `aidcp-transport` 的依赖 SHALL 钉在已发布的 annotated tag 上。检查器 MUST 识别历史上出现过的全部钉子写法（`git+ssh://` 与 `github:` 简写）；不认识的写法 MUST 报错，MUST NOT 报成「未 pin」。翻转前钉子 MUST 解析到最新 tag；翻转后钉子 MUST 是存在的 tag，落后于最新 MUST 在报告中列明（谁、落后几版），MUST NOT 作为错误拦下。

#### Scenario: 检查器遇到不认识的钉子写法

- **WHEN** 某仓 `package.json` 里共享包依赖用了检查器不认识的引用形式
- **THEN** 检查 MUST 失败并指名该仓与该行，MUST NOT 将其静默归类为「未使用该包」

#### Scenario: 翻转后某仓落后两个版本

- **WHEN** 翻转标记已置位，kernel 已发 `v0.3.0`，某派生仓仍钉 `v0.1.0`
- **THEN** 检查 MUST 通过且报告中 MUST 出现该仓落后的事实与版本差，MUST NOT 静默

### Requirement: 整图校验直接引用派生仓源码，不依赖 cloud 副本

跨属主 / 整图用例 SHALL 存放于集成测试仓（瘦身后的 `aidcp-cloud`）并直接引用兄弟仓的源码与迁移目录。cutover 完成后，这些用例 MUST 在 cloud 无 `src/`、无 `migrations/` 的状态下全量可跑；MUST NOT 存在任何仍指向 cloud 本仓源码副本的引用。

#### Scenario: cutover 后跑整图套件

- **WHEN** cloud 的 `src/` 与 `migrations/` 已删除，在集成测试仓运行整图套件
- **THEN** 全部保留用例 MUST 可解析、可执行，引用的是 `../aidcp-api` / `../aidcp-automation` / `../aidcp-content`（及共享包）的真实现状

#### Scenario: 迁移对齐类用例的数据来源

- **WHEN** 迁移编号 / 顺序 / DDL 对齐用例运行
- **THEN** 它 MUST 读取三个派生仓各自的 `migrations/` 目录拼出全图，MUST NOT 读取任何冻结或已删除的 cloud 副本

### Requirement: 回滚不依赖单体

翻转完成后，dev / OL 的回滚路径 SHALL 是逐服务回退到部署序列产生的上一版备份。回滚流程 MUST NOT 依赖重新启用 `aidcp-cloud` 单体；单体最终备份包 MUST 有明确日落日期，过期删除。

#### Scenario: OL 某服务上线后需要回退

- **WHEN** 某个派生服务在 OL 部署后需要回滚
- **THEN** 操作 MUST 是解包该服务自己的上一版备份并重启该服务，MUST NOT 触碰其他两个服务，MUST NOT 启用任何单体 unit
