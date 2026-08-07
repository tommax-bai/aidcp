# Design — schema-gate-expand-ahead-pass

## Context

- 契约门是三个派生进程（api / automation / content）`main()` 的第一句、建池之前、无 try/catch；enforce 下判不过即抛、进程退出、systemd 重启。判定逻辑分三档：behind / ahead / unreadable。
- ahead 档现状（`schema-contract.ts` 的 evaluate 函数）：账本最高版本 > 本构建 `KNOWN_MAX` → 一律按「回滚场景」拒绝；唯一豁免是 `AIDCP_ALLOW_SCHEMA_AHEAD=<具体版本id>`（刻意不收布尔，防永久后门）。
- 分类判据已存在：迁移文件头 `-- aidcp:kind=expand|contract` 计划期强制（`migration-plan.ts:234`）；应用时写入 `schema_migrations.kind`（0064 起 `NOT NULL CHECK (kind IN ('expand','contract'))`）；收缩迁移执行还需显式 `--allow-contract`（`migration-plan.ts:252`）。
- 两份运行时拷贝：`aidcp-transport/src/schema/`（api / content 经 tag pin 消费；transport 现版 0.1.3、最新 tag v0.1.4）与 `aidcp-automation/src/schema/`（自持）。`schema-gate.ts` 两份逐字一致；`schema-contract.ts` 仅 `REQUIRED` / `KNOWN_MAX` 常量及其注释不同（各仓收窄到自己迁移范围），判定函数一致。测试全部在 automation `test/schema/`；transport 无 schema 测试；集成仓无 parity 闸（CLAUDE §8.3 已知递延项，不在本 change 补）。
- 门读账本时按属主裁剪账本行，但**保留本构建不认识的版本**（那是 ahead 检测的信号源），kind 信息必须跟着这些行一起活到判定层。

## Goals / Non-Goals

**Goals:**

- ahead 档从「一律拒绝」改为「全 expand 放行 + 告警；含 contract 或 kind 不明拒绝」。
- kind 缺失 / 非法 / 列不存在，一律按最危险类别（contract）处理——分类失败绝不变成放行理由。
- 放行必须响亮：结论文本明说哪些版本按扩张放行，并进既有启动期告警缓存（`takePendingSchemaGateAlert` 通道），与人工放行告警同路。
- 两份拷贝判定逻辑层继续逐字一致。

**Non-Goals:**

- 不改 behind / unreadable 档、warn/enforce 模式语义、`AIDCP_ALLOW_SCHEMA_AHEAD` 的解析与语义。
- 不给收缩迁移新增任何放行通道；不改迁移执行侧的收缩闸。
- 不在本 change 建两仓 parity 自动闸（递延项归属集成仓 5.7 结构性收口）。
- 不承诺保护运行中的进程——删列型事故发生在运行期、不经过重启，本闸只管启动路径，该边界写进 spec 场景措辞。

## Decisions

1. **kind 从账本读，不从文件读。** 旧构建没有新迁移的文件，账本是它唯一能拿到分类的地方；且账本 kind 是应用时由执行器从文件头抄写的，与执行侧收缩闸同源，作者已被 `--allow-contract` 强制对分类表态。备选「按版本号段猜」「按对象清单再解析」都需要旧构建理解新格式，放弃。
2. **判定层输入加一张 version→kind 映射（可选字段），不改 `ledgerVersions` 形状。** `evaluateSchemaGate` 的输入加 `ledgerKinds?`；缺映射 = 全部 kind 未知 = 拒绝，与今天行为同构。这样既有测试语义不变，新用例只增不改。备选「把 ledgerVersions 换成行对象数组」会让两仓所有调用点与测试一起翻新，收益只有形状洁癖，放弃。
3. **SELECT 加列 + 42703 回退。** `readLedgerVersions` 改查 `version, kind`；捕获 undefined_column（42703）时回退只查 `version`、kind 全未知。回退分支实际只在账本还停在 0064 之前的库上走到——那种库必然同时判 behind，回退只是保证「加列读取」永不成为新的失败面。
4. **放行优先级：先分类、后人工。** 全 expand → 直接 pass（新字段 `aheadExpandOnly`，`waived` 保持 false，语义区分「机制放行」与「人工放行」）；非全 expand → 走既有 waiver 判定。人工放行覆盖面更宽（可放行 contract 超前），保留为兜底。两种放行都进告警缓存，detail 里可区分。
5. **fail-safe 的具体化：** kind 值不是 `'expand'` 字面量的一切情形（`'contract'`、NULL、缺行、类型异常）都归入 blocking 列表；结论文本把 blocking 版本与其 kind 原样列出，排查时不用再进库查。
6. **spec 落点：** 修改 `split-service-runtime-deployment`，新增一条 ahead 方向的 Requirement（ADDED），不动既有「顺序倒置」requirement。

## Risks / Trade-offs

- [作者把收缩迁移误标 expand → 旧构建放行后运行期报错] → 执行侧 `--allow-contract` 强制表态在先；存储全为探测式 fail-closed，错也响亮、可恢复；按仓内加闸准入原则（概率低 × 后果可恢复）不为此保留粗闸。
- [两份拷贝手工同步漂移] → 本 change 内以 diff 校验逐字一致后提交；结构性 parity 闸仍是集成仓递延项，不扩本 change 范围。
- [新构建先落 dev、OL 旧构建仍是粗闸] → 本 change 对 OL 的收益要等 OL 下次发版才生效；过渡期应急仍是逐次放行环境变量。这不新增风险，只是收益延迟。
- [告警缓存只有单槽（pendingWaiverAlert）] → 人工放行与扩张放行同时发生时合并成一条 detail，不丢事实；不为此扩数据结构。

## Migration Plan

纯代码改动、零新迁移、零 env 变化。部署顺序：transport 出 tag → api / content 抬 pin → automation 自身改动随常规构建 → 各服务照常部署（dev 默认；OL 待用户点火）。回滚 = 回退各仓提交 / pin，无库侧状态。

## Open Questions

（无）
