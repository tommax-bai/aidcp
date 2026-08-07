# schema-gate-expand-ahead-pass

## Why

启动期 schema 契约门的「库比代码新」分支只比版本号高低，不看超前迁移的性质。而 dev / OL 长期共库、异步部署，「账本超前于旧构建」是常态运维而非回滚事故——dev 每应用一条纯扩张迁移（新表 / 新列 / 新索引），就给 OL 旧构建埋一颗「下次重启拒启」的雷（2026-08-06 实测付过代价：共库迁移 + OL 旧构建重启 → 无声重启循环）。现行规避是新迁移攒着不执行、等 OL 出新版（0115 / 0116 的「惰性态」），等于 dev 的库演进被 OL 发版节奏串行化。

系统里分类信息已经存在且可信：每条迁移文件头强制声明 `-- aidcp:kind=expand|contract`（缺失或非法在计划期即拒绝），执行成功时 kind 随版本号写进账本 `schema_migrations.kind`（自 0064 起 NOT NULL + CHECK）。旧构建虽然没有新迁移的文件，但能从账本读到每条超前迁移自报的类别——精细放行所需的全部判据已经躺在库里，闸门只是没读。

## What Changes

- 契约门 ahead 分支改为**按账本 kind 分类判定**：
  - 超前版本**全部为 `expand`** → 放行启动（`pass=true`），结论文本明说「扩张类超前放行」，并走既有的启动期告警缓存通道（与超前放行告警同机制），让人知道该构建落后于库；
  - 超前版本**含任何 `contract`、或 kind 读不到 / 非法** → 照旧拒绝启动（fail-safe：缺失按 contract 算）；
  - 既有 `AIDCP_ALLOW_SCHEMA_AHEAD=<版本id>` 逐次放行通道**原样保留**，作为含 contract 超前时的人工兜底（语义不变、优先级不变：分类放行先判，判不过再看人工放行）。
- 账本读取从只取 `version` 改为取 `version, kind`；账本表尚无 kind 列时（42703）回退为只取 version、全部按 kind 未知处理——行为与今天逐字一致，绝不因新列读取失败而误放行。
- behind / unreadable 分支、warn / enforce 模式语义、结论文本逐字一致性约定，全部不变。
- 落点为闸门的**两份运行时拷贝**：`aidcp-transport/src/schema/`（api / content 进程经包消费）与 `aidcp-automation/src/schema/`（自持），判定逻辑层保持逐字一致；transport 出新 annotated tag，api / content 抬 pin。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `split-service-runtime-deployment`: 契约门新增 ahead 方向的分类判定要求——扩张类超前 SHALL 放行并告警，收缩类或类别不明的超前 SHALL 拒绝启动；既有「顺序倒置（behind）拒启」要求不变。

## Impact

- 代码：`aidcp-transport/src/schema/schema-contract.ts`、`schema-gate.ts`；`aidcp-automation/src/schema/` 同名两文件；automation `test/schema/` 既有测试补用例。api / content 无源码改动，仅抬 `aidcp-transport` pin（v0.1.4 → 新 tag）。
- 行为：只影响「账本超前」这一档在 enforce 模式下的启动结果；warn 模式下只有结论文本变化。dev / OL 现网生效需各自部署新构建；在旧构建追上之前，应急手段仍是既有的按版本逐次放行环境变量。
- 明确不做：不改迁移执行侧的收缩闸（`--allow-contract`）；不改 behind 分支；不给收缩迁移任何新的放行通道——收缩迁移在共库上的安全仍靠两段式流程（先让两侧代码不再碰目标对象，再收缩），闸门只是重启路径上的最后一道网。
