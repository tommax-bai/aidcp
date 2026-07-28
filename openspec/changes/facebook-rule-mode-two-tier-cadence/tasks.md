# Tasks

> 进度回写格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha 必须取自**已推送**的提交。

## 1. 前置闸（控制仓，开工前必须全过）

- [ ] 1.1 确认 `facebook-rule-mode-cadence` 已归档、`facebook-rule-mode` 能力已并入 `openspec/specs/`；未归档则先归档，否则本变更是第四层 delta、归档顺序会静默定死最终文本
- [ ] 1.2 确认 `facebook-rule-mode-without-persona` 未在同期改动规则模式判定与调度接线（热点文件单写者，MUST 串行）
- [ ] 1.3 与 `environment-level-rule-mode-and-approval` 对齐：两者都 MODIFIED `Facebook rule mode is an explicit account-scoped fixed definition`，确认后落地的一方合并两处改动而非覆盖
- [ ] 1.4 核对 `Rule browsing does not use persona relevance or interaction preference` 中 `fixed ten-view cadence` 的措辞——该 requirement 同时被 `facebook-rule-mode-without-persona` 整段 MODIFIED，由后落地的一方统一为节奏无关措辞（本变更不单独 MODIFIED 该条以避免必然冲突）
- [ ] 1.5 跑 `scripts/task-preflight` 与 `scripts/new-change`，在 `../aidcp-cloud.wt/facebook-rule-mode-two-tier-cadence` 建 worktree

## 2. aidcp-cloud — 数据库迁移（expand）

- [ ] 2.1 新建迁移，`kind=expand`：放宽 `facebook_rule_mode_config` / `facebook_rule_progress` / `facebook_rule_view_fact` / `facebook_rule_batch` 四表对定义号与定义版本的 CHECK，从「等于旧值」改为「属于新旧集合」
- [ ] 2.2 同一迁移放宽 `facebook_rule_batch` 三个动作状态列的 CHECK，容纳新增的「本轮不适用」取值
- [ ] 2.3 删除既有 CHECK MUST 先查系统目录拿真名再动态删除；**MUST NOT** 用猜名 + `DROP CONSTRAINT IF EXISTS`（名字不符会静默 no-op，新旧 CHECK 取合取，迁移报成功而运行期写入仍被拒）
- [ ] 2.4 确认未编辑任何已入账本的既有迁移（改磁盘内容即校验和不匹配、整批拒绝）
- [ ] 2.5 抬升 `REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 两个常量，并同步其字面量断言测试（已知会打红，不是意外）
- [ ] 2.6 新增迁移形态断言：验证放宽后的 CHECK 同时接受新旧定义号与新动作状态取值

## 3. aidcp-cloud — 规则定义与两级节奏

- [ ] 3.1 规则定义常量改为新定义号 `facebook_browse_5_like_1_join_contact_every_2` + 版本 2，一级阈值改 5，新增二级周期常量 2；kernel 成员变化须同改 `boundaries/ownership-rules.json` 的 fileOverrides 与 `kernel-non-members.json` 的 kernelRoster（两者 deepEqual 有门禁）
- [ ] 3.2 动作状态枚举新增「本轮按节奏不适用」取值；MUST NOT 复用 `not_started` / `structural_skip`
- [ ] 3.3 轮次上下文补齐轮次序号字段，建轮次时从返回值带入（二级判据的输入）
- [ ] 3.4 在加群联系评论入口的幂等守卫之后加入二级节奏判据；五个点赞终态调用点不改
- [ ] 3.5 本轮不加群时走正常终结路径：两格写「不适用」、标记终态、清空活跃轮次指针、按「未启动加群」分支续跑浏览
- [ ] 3.6 本轮不加群时 MUST NOT 写阻断原因（该列三阶段共用、后写覆盖先写，会抹掉点赞阶段的抑制原因）
- [ ] 3.7 二级判据按轮次序号而非成功点赞数；点赞任一终态都推进周期

## 4. aidcp-cloud — 投影与配置回读

- [ ] 4.1 运行时投影新增二级节奏字段：当前轮次在两轮周期中的位置、本轮是否包含加群；浏览阈值投影字段的字面量类型同步放开
- [ ] 4.2 配置回读改为读库中真实定义号与版本，MUST NOT 继续直接返回代码常量；库值与常量不匹配时暴露具名投影问题
- [ ] 4.3 运行时存储的必需列清单核对（本变更不新增列，确认无遗漏即可）
- [ ] 4.4 面板 API 与客户端契约同步新字段；客户端契约测试对规则模式对象做整对象比对，需同步

## 5. aidcp-cloud — 测试

- [ ] 5.1 阈值与定义号断言改到新值；两处「凑满十条」的成批循环改为五条
- [ ] 5.2 新增：第 1 轮只点赞不加群、第 2 轮点赞后加群，周期正确循环
- [ ] 5.3 新增（活锁回归，最关键）：连续多个只点赞轮次后，活跃轮次指针每次都被清空、浏览计数持续推进，不依赖会话边界对账或重启恢复
- [ ] 5.4 改写既有「点赞被日配额抑制仍独立尝试一次加群」的集成用例：抑制仍推进周期，但只在第 2 轮触发加群
- [ ] 5.5 新增：只点赞轮次的点赞阻断原因在终结后仍可读，未被覆盖
- [ ] 5.6 新增：会话边界对账与进程重启恢复对只点赞轮次同样生效
- [ ] 5.7 补 AC 级红线用例（规则模式当前在验收层零覆盖）：定义号漂移、动作状态不得回落为假失败、部署目标隔离
- [ ] 5.8 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿

## 6. aidcp-console — 展示

- [ ] 6.1 定义号与阈值的字面量类型同步（不同步则 typecheck 失败）
- [ ] 6.2 动作状态中文映射与配色新增「本轮不适用」；该映射是穷举，漏改会整页白屏
- [ ] 6.3 进度展示改为两级：浏览进度 `0..4/5` + 本轮在两轮周期中的位置 + 本轮是否含加群
- [ ] 6.4 列标题与固定规则说明文案改为新节奏描述
- [ ] 6.5 只点赞轮次 MUST 渲染为「本轮不适用」中性态，MUST NOT 显示为待处理/进行中/失败
- [ ] 6.6 前端测试 fixture 与文案断言同步；`npm test` + `npm run typecheck` 全绿

## 7. aidcp-edge

- [ ] 7.1 确认零代码改动（客户端只透传开关，渲染层对定义号只做类型校验、无字面量断言；边-云协议无阈值/进度字段）；若确有改动，说明原因

## 8. 集成、部署与验收

- [ ] 8.1 各仓 rebase 到最新默认分支、解冲突、跑全量测试后 ff 合并
- [ ] 8.2 迁移在 DEV 执行前先探 ECS 真实现状（账本状态、既有 CHECK 真名）
- [ ] 8.3 按部署安全序列部署 DEV：命名 target → 备份 → rsync → 重启 → healthcheck → 失败即回滚
- [ ] 8.4 DEV 验证：规则模式账号能按 5 条建轮次；第 1 轮只点赞并正常终结、浏览继续；第 2 轮触发加群联系评论
- [ ] 8.5 显式登记：换定义号导致存量进度不可见（部署前实测两侧行数并记入本文件）
- [ ] 8.6 裁定并记录 DEV/OL 部署策略（配置表无部署目标列 + 共库 + 单侧部署会两套节奏并存且无机械暴露）
- [ ] 8.7 真机验收项（真实账号跑满一个完整两轮周期）收拢进 `docs/real-machine-acceptance-backlog.md`

## 9. 控制仓回写与归档

- [ ] 9.1 各 task 标 `[x]` 并写 `<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`
- [ ] 9.2 `openspec validate facebook-rule-mode-two-tier-cadence --strict`
- [ ] 9.3 归档，删除 worktree 与分支
