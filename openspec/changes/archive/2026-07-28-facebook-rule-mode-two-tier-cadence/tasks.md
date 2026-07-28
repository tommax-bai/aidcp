# Tasks

> 进度回写格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha 必须取自**已推送**的提交。

## 1. 前置闸（控制仓，开工前必须全过）

- [x] 1.1 确认 `facebook-rule-mode-cadence` 已归档、`facebook-rule-mode` 能力已并入 `openspec/specs/`；未归档则先归档，否则本变更是第四层 delta、归档顺序会静默定死最终文本
- [x] 1.2 确认 `facebook-rule-mode-without-persona` 未在同期改动规则模式判定与调度接线（热点文件单写者，MUST 串行）
- [x] 1.3 与 `environment-level-rule-mode-and-approval` 对齐：两者都 MODIFIED `Facebook rule mode is an explicit account-scoped fixed definition`，确认后落地的一方合并两处改动而非覆盖
- [x] 1.4 核对 `Rule browsing does not use persona relevance or interaction preference` 中 `fixed ten-view cadence` 的措辞——该 requirement 同时被 `facebook-rule-mode-without-persona` 整段 MODIFIED，由后落地的一方统一为节奏无关措辞（本变更不单独 MODIFIED 该条以避免必然冲突）
- [x] 1.5 跑 `scripts/task-preflight` 与 `scripts/new-change`，在 `../aidcp-cloud.wt/facebook-rule-mode-two-tier-cadence` 建 worktree

## 2. aidcp-cloud — 数据库迁移（expand）

- [x] 2.1 新建迁移，`kind=expand`：放宽 `facebook_rule_mode_config` / `facebook_rule_progress` / `facebook_rule_view_fact` / `facebook_rule_batch` 四表对定义号与定义版本的 CHECK，从「等于旧值」改为「属于新旧集合」
<!-- aidcp-cloud aae5c0f+f3ff346 0094(api)+0095(automation) 两条 expand 迁移 -->
- [x] 2.2 同一迁移放宽 `facebook_rule_batch` 三个动作状态列的 CHECK，容纳新增的「本轮不适用」取值
<!-- aidcp-cloud aae5c0f+f3ff346 batch 三个状态列 CHECK 加 not_scheduled -->
- [x] 2.3 删除既有 CHECK MUST 先查系统目录拿真名再动态删除；**MUST NOT** 用猜名 + `DROP CONSTRAINT IF EXISTS`（名字不符会静默 no-op，新旧 CHECK 取合取，迁移报成功而运行期写入仍被拒）
<!-- aidcp-cloud aae5c0f+f3ff346 按 pg_constraint 动态查名；合同测试断言不得出现 DROP CONSTRAINT IF EXISTS -->
- [x] 2.4 确认未编辑任何已入账本的既有迁移（改磁盘内容即校验和不匹配、整批拒绝）
<!-- aidcp-cloud aae5c0f+f3ff346 0092/0093 未改；DEV 账本实测 api 59/59、automation 51/51 校验和一致 -->
- [x] 2.5 抬升 `REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 两个常量，并同步其字面量断言测试（已知会打红，不是意外）
<!-- aidcp-cloud aae5c0f+f3ff346 REQUIRED/KNOWN_MAX 抬到 0095；sync-read-checkpoint 的字面量断言同步 -->
- [x] 2.6 新增迁移形态断言：验证放宽后的 CHECK 同时接受新旧定义号与新动作状态取值
<!-- aidcp-cloud aae5c0f+f3ff346 test/schema/facebook-rule-mode-migration.test.ts 新增两级节奏合同断言 -->

## 3. aidcp-cloud — 规则定义与两级节奏

- [x] 3.1 规则定义常量改为新定义号 `facebook_browse_5_like_1_join_contact_every_2` + 版本 2，一级阈值改 5，新增二级周期常量 2；kernel 成员变化须同改 `boundaries/ownership-rules.json` 的 fileOverrides 与 `kernel-non-members.json` 的 kernelRoster（两者 deepEqual 有门禁）
<!-- aidcp-cloud aae5c0f+f3ff346 -->
- [x] 3.2 动作状态枚举新增「本轮按节奏不适用」取值；MUST NOT 复用 `not_started` / `structural_skip`
- [x] 3.3 轮次上下文补齐轮次序号字段，建轮次时从返回值带入（二级判据的输入）
- [x] 3.4 在加群联系评论入口的幂等守卫之后加入二级节奏判据；五个点赞终态调用点不改
- [x] 3.5 本轮不加群时走正常终结路径：两格写「不适用」、标记终态、清空活跃轮次指针、按「未启动加群」分支续跑浏览
- [x] 3.6 本轮不加群时 MUST NOT 写阻断原因（该列三阶段共用、后写覆盖先写，会抹掉点赞阶段的抑制原因）
- [x] 3.7 二级判据按轮次序号而非成功点赞数；点赞任一终态都推进周期

## 4. aidcp-cloud — 投影与配置回读

- [x] 4.1 运行时投影新增二级节奏字段：当前轮次在两轮周期中的位置、本轮是否包含加群；浏览阈值投影字段的字面量类型同步放开
<!-- aidcp-cloud aae5c0f+f3ff346 -->
- [x] 4.2 配置回读改为读库中真实定义号与版本，MUST NOT 继续直接返回代码常量；库值与常量不匹配时暴露具名投影问题
- [x] 4.3 运行时存储的必需列清单核对（本变更不新增列，确认无遗漏即可）
- [x] 4.4 面板 API 与客户端契约同步新字段；客户端契约测试对规则模式对象做整对象比对，需同步

## 5. aidcp-cloud — 测试

- [x] 5.1 阈值与定义号断言改到新值；两处「凑满十条」的成批循环改为五条
<!-- aidcp-cloud aae5c0f+f3ff346 -->
- [x] 5.2 新增：第 1 轮只点赞不加群、第 2 轮点赞后加群，周期正确循环
- [x] 5.3 新增（活锁回归，最关键）：连续多个只点赞轮次后，活跃轮次指针每次都被清空、浏览计数持续推进，不依赖会话边界对账或重启恢复
- [x] 5.4 改写既有「点赞被日配额抑制仍独立尝试一次加群」的集成用例：抑制仍推进周期，但只在第 2 轮触发加群
- [x] 5.5 新增：只点赞轮次的点赞阻断原因在终结后仍可读，未被覆盖
- [x] 5.6 新增：会话边界对账与进程重启恢复对只点赞轮次同样生效
- [x] 5.7 补 AC 级红线用例（规则模式当前在验收层零覆盖）：定义号漂移、动作状态不得回落为假失败、部署目标隔离
<!-- aidcp-cloud 11e53ef test/acceptance/facebook-rule-cadence.test.ts：AC-FBRULE-01..06。
     01 定义号自身编码节奏并与常量对账；02 二级节奏按轮次序号非成功点赞数；03 加群频率未升高（5×2=10）；
     04 真跑调度器：只点赞轮次终结为 not_scheduled、不调加群、不覆盖 blocker（假失败 + 活锁 + 原因抹除三合一）；
     05 运行时三表按 execution_target 分区、配置表无该列是具名已知事实；06 迁移只放宽不收缩且旧定义仍可写。
     test:acceptance 162/162 -->
- [x] 5.8 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿
<!-- aidcp-cloud aae5c0f+f3ff346+11e53ef test:acceptance 162/162（含新增 AC-FBRULE-*）；npm test 3747 pass 0 fail；typecheck 干净 -->

## 6. aidcp-console — 展示

- [x] 6.1 定义号与阈值的字面量类型同步（不同步则 typecheck 失败）
<!-- aidcp-console 0fae387 -->
- [x] 6.2 动作状态中文映射与配色新增「本轮不适用」；该映射是穷举，漏改会整页白屏
- [x] 6.3 进度展示改为两级：浏览进度 `0..4/5` + 本轮在两轮周期中的位置 + 本轮是否含加群
- [x] 6.4 列标题与固定规则说明文案改为新节奏描述
- [x] 6.5 只点赞轮次 MUST 渲染为「本轮不适用」中性态，MUST NOT 显示为待处理/进行中/失败
- [x] 6.6 前端测试 fixture 与文案断言同步；`npm test` + `npm run typecheck` 全绿

## 7. aidcp-edge

- [x] 7.1 确认零代码改动（客户端只透传开关，渲染层对定义号只做类型校验、无字面量断言；边-云协议无阈值/进度字段）；若确有改动，说明原因
<!-- aidcp-edge 无改动：渲染层对 definitionId 只做 typeof string 校验、对 definitionVersion 只做 Number.isInteger，无字面量断言；协议无阈值/进度字段 -->

## 8. 集成、部署与验收

- [x] 8.1 各仓 rebase 到最新默认分支、解冲突、跑全量测试后 ff 合并
<!-- aidcp-cloud aae5c0f + f3ff346；aidcp-console 0fae387。cloud 第二次 push 撞 non-ff（并发 session 先推 5b61f81），按纪律 rebase 重来、未 force -->
- [x] 8.2 迁移在 DEV 执行前先探 ECS 真实现状（账本状态、既有 CHECK 真名）
<!-- 2026-07-28 实测 DEV：服务 active；账本 content 20/20、automation 51/51（最高 0093）、api 59/59（最高 0092），零待应用、校验和一致。既有 CHECK 真名与 PG 自动命名一致（<表>_<列>_check），但迁移仍按 pg_constraint 动态查名，不依赖该巧合 -->
- [x] 8.3 按部署安全序列部署 DEV：命名 target → 备份 → rsync → 重启 → healthcheck → 失败即回滚
<!-- 2026-07-28 deployed。target=dev（deploy-target --check 通过）。备份 cloud.bak.20260728-152023.tar.gz +
     cloud.env.bak.20260728-152023；console.bak.20260728-152401.tar.gz（备份轮转保留最近 10 份）。
     多 session 并行 ⇒ 未从共享工作区 rsync，改用 `git archive origin/master` 干净快照（cloud f3ff346 / console 0fae387）。
     rsync 排除 .env / node_modules / .git，.env 完好。
     迁移：api 0094 (expand, 5ms)、automation 0095 (expand, 9ms)，content 无待应用。
     重启后 active、NRestarts=0，监听 8787 / 8090 / 8088 齐全，/api/health {"ok":true}，
     三个属主的 schema 契约门（enforce）全部通过新版本，飞书长连接 onReady 已建立，
     "stored definition mismatch" 告警 0 条。同机 isales 四服务未受影响。无需回滚。
     console 产物核验：新文案「本轮不适用 / 含加群 / 只点赞 / 规则定义不一致」均在包内，旧文案「确认浏览 10 条」已消失，
     index + js + css 三个公网路径均 200 -->
- [ ] 8.4 DEV 验证：规则模式账号能按 5 条建轮次；第 1 轮只点赞并正常终结、浏览继续；第 2 轮触发加群联系评论
<!-- 未完成：需真实账号在活跃时段联机浏览才能产生新定义下的轮次。部署当刻新定义进度行为 0（预期，等账号下次浏览）。
     已收拢进 docs/real-machine-acceptance-backlog.md -->
- [x] 8.5 显式登记：换定义号导致存量进度不可见（部署前实测两侧行数并记入本文件）
<!-- 2026-07-28 部署前实测 DEV（**推翻母变更记录的「均为 0」**，那是它上一日部署当刻的快照、已过期）：
     facebook_rule_mode_config 22 行 / 21 行 enabled，全部在旧定义；facebook_rule_progress 11 行；
     facebook_rule_view_fact 418 行；facebook_rule_batch 38 行。
     处置：配置行由 0094 回填到新定义（只动身份，不动 enabled / updated_by）；进度、去重事实、批次
     三张运行时表**不回填**，旧行留作历史、新定义查不到，账号从 0/5 重新收集（每账号至多丢 4 条已累计浏览）。
     旧定义下残留的非终态批次由存储层重启恢复统一终结（按部署目标扫描、不按定义号）。
     教训：母变更部署记录里的数据量是当刻快照，MUST NOT 当实装期现状引用 -->
- [x] 8.6 裁定并记录 DEV/OL 部署策略（配置表无部署目标列 + 共库 + 单侧部署会两套节奏并存且无机械暴露）
<!-- 裁定：本次只部署 DEV，OL 不部署。实测依据：规则模式运行时行**全部**是 execution_target=dev
     （progress 11 行、batch 38 行且非终态 0 行，ol 侧 0 行）——规则模式从未在 OL 跑过，所以「两套节奏并存」
     在 OL 侧没有实际载体。
     仍需知道的暴露面：配置表 facebook_rule_mode_config **没有 execution_target 且 dev 与 ol 共库**，
     所以 0094 的回填把两侧共享的那 22 行一起改成了新定义。OL 上跑的是旧代码，其配置回读本来就直接返回
     代码常量、不读库值，因此 OL 的行为不变（仍按旧定义查它自己的 target 行）。
     结论：OL 下次部署时会自动切到新节奏，不需要额外数据动作；在那之前 OL 不受影响。
     若将来要让两侧节奏不同，必须先给该表加 execution_target，否则无解 -->
- [x] 8.7 真机验收项（真实账号跑满一个完整两轮周期）收拢进 `docs/real-machine-acceptance-backlog.md`
<!-- 簇 114（8 条）：一级 5 条触发、第 1 轮只点赞且真收尾（活锁正面验收）、第 2 轮才加群、
     点赞被压制不连带停掉加群、点赞原因不被终结抹掉、存量账号无缝续跑、点赞密度翻倍未触顶、OL 侧不受影响 -->

## 9. 控制仓回写与归档

- [x] 9.1 各 task 标 `[x]` 并写 `<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`
- [x] 9.2 `openspec validate facebook-rule-mode-two-tier-cadence --strict`
- [ ] 9.3 归档，删除 worktree 与分支
