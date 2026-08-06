# invert-split-fact-source

## Why

拆仓已完成「拆进程」（dev / OL 都跑三个派生服务，单体永不部署），但**开发模式还停在过渡态**：派生仓的 `src/` 是从 `aidcp-cloud` 机械重放的产物，改任何一个服务都要「改 cloud → 同步 → 派生仓接线」三步，且只在派生仓改的代码会被下一次 `--apply` **静默覆盖**。共享包（kernel / transport）钉 git sha 且要求「恒等于最新」，三仓钉子靠人肉同步——2026-08-06 实测已抓到一处真漂移：`aidcp-automation` 的 transport 钉子用 `github:` 简写形式钉在落后一位的 sha 上，而检查器只认 `git+ssh://` 形式、把它报成「未 pin」，漂移完全不可见。

用户裁定（2026-08-06）：服务应当各自独立演化、后续能平滑接入新服务。本 change 把「事实源」翻转过来：**派生仓转正为各自代码的唯一事实源，cloud 瘦身成纯整图验证仓（集成测试场），重放机制退役**。

不退役的部分依据 `docs/cloud-retirement-blockers-2026-08-05.md`：约 120 个跨属主 / 整图用例本质上需要多仓摆在一起才跑得动，它们不消失、只换引用方式（从「cloud 自己的源码副本」改为「直接引兄弟仓源码」）。

## What Changes

- **换向闸（先落、带 armed/enforcing 两态）**：控制仓新增翻转标记文件；`scripts/sync-split-repos` 与 `scripts/task-preflight` 读它。未翻转＝现行为不变；翻转后＝`--apply`/`--prune` 拒绝执行、cloud `src/`+`migrations/` 冻结在记录的 sha、任务准入拦下任何 cloud 源码改动。闸落地即做变异验证（翻开标记确认真的会拦）。
- **共享包版本化**：kernel / transport 打 semver tag 发版；三仓钉子从裸 sha 改为 tag 引用并归一为单一写法；检查器改为「必须是已发布 tag、两种历史写法都要认得」；翻转前仍要求等于最新，翻转后落后只报告不报错（各仓自主升级节奏）。
- **边界扫描器合并**：cloud 与 automation 两份约千行的边界扫描器已实测漂开，合并为单一实现供各仓引用，消灭「同一套规则两份实现各自演化」。
- **整图测试搬家（cutover 的主体）**：cloud 里约 130 个跨属主 / 整图用例的引用从本仓 `../../src/` 改指兄弟仓源码。先以 pilot 证明跑法并产出 codemod，cutover 时分桶并行执行。
- **Cutover（串行、显式点火）**：翻转标记 → 批量改引用 → 全绿 → 删除 cloud 的 `src/` 与 `migrations/` 副本 → 仓自述改为「集成测试仓」→ 重放脚本退役。**前置＝所有触碰 cloud src 的在飞 change 先 land**，由用户确认时点。
- **回滚路解绑**：OL 回滚从「重新拉起单体」改为「单服务回退到上一版备份」，演练一次；单体最后备份留档并定日落日期。
- **不做**：不拆数据库（共库是产品约束）；不新建仓（集成测试场＝cloud 仓瘦身而来）；迁移链按服务拆编号为阶段二、另行立项。

## Capabilities

### New Capabilities

- `derived-repo-fact-source`: 拆仓终态的事实源归属——派生仓各自为政、cloud 源码副本冻结与移除、共享包版本化引用、整图校验对兄弟仓的直接引用、重放通道的退役判据。

### Modified Capabilities

（无。本 change 不改任何运行时行为；它改的是开发与验证模式。既有 spec 对拆仓的引用在 cutover 后由第 6 节文档改指统一收口。）

## Impact

- **代码**：控制仓 `scripts/sync-split-repos`、`scripts/task-preflight`、新增翻转标记文件；`aidcp-kernel` / `aidcp-transport` 打 tag；三个派生仓 `package.json` + lockfile；cloud 与 automation 的边界扫描器；cutover 时 cloud 的 `test/` 全量引用改写与 `src/`+`migrations/` 删除。
- **生产行为**：零变化。三个派生服务的部署产物不因本 change 改变；本批**不触发部署**（钉子换写法解析到相同内容，随下次正常部署自然生效）。
- **开发模式**：翻转后「改一个服务只动一个仓」；新服务接入不再进任何重放清单。
- **风险面**：翻转窗口期两个事实源并存是最坏状态——靠 armed 闸把窗口压缩为单次 cutover；整图测试在 cutover 前引用冻结的 cloud 副本、语义不变（这是 pilot 不提前落地的原因，见 design.md）。
