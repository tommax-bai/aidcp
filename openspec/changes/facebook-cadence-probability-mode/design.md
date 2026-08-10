# Design: facebook-cadence-probability-mode

## Context

「Facebook 全局运行数值」= PG 单例表 `facebook_operation_global_policy`(api 属主,迁移 0103 建、0114 收成 singleton),面板 `PUT /api/facebook/operation-global-policy` 原子写(revision 乐观锁 + 审计 + 级联传播继承环境 + 同事务 bump 三个镜像版本,`facebook-operation-policy-store.ts:1209-1425`),经 sync-read 流 `facebook_operation_policy` 下发 automation(逐环境基线 11 键,`api-sync-read-source.ts:1100-1119` 逐字段构造禁 spread;游标 = `config_mirror_version` 经 cantor 折叠)。

11 个「N 次 A → 1 次 B」数值的触发点(automation):

| 触发点 | 位置 | 形态 |
|---|---|---|
| Reel 节奏 ×6 | `role-dispatcher.ts:4160/4163` `ordinal % N === 0` | 会话内存计数,单点决策 |
| 规则 viewsPerLike | `facebook-rule-mode-runtime-store.ts:371` `nextCount < N` | PG 事务,单点决策 |
| 规则 joinEveryNRounds | kernel `facebookRuleRoundIncludesJoin(sequence, N)`,被 `batchFromDb`(:155)与状态读(:264)**反复调用** | 纯函数派生,**非单点** |
| 消费 viewsPerLike | `facebook-consumption-mode-runtime-store.ts:647` | PG 事务,单点决策 |
| 消费 likes→join / joins→comment | `facebook-consumption-mode.ts:71-101` reducer | 事务内 reducer,单点决策 |

## Goals / Non-Goals

**Goals:**

- 一个全局开关 `cadenceMode: 'fixed' | 'probabilistic'`,统管全部 11 个数值的解释方式;fixed 逐字零回归。
- 概率判定单点化:反复读取的判定(轮含加群)在创建时掷骰并落库。
- 版本偏斜安全:任意部署顺序不拒收、不错乱,最坏回落 fixed。

**Non-Goals:**

- 不做环境级模式覆盖(模式只在全局单例;环境覆盖的仍只是数值)。
- 不动 feed 视频 0.25 伯努利赞(已是概率,硬编码,独立机制)。
- 不做「概率模式防长旱保底」(纯 Bernoulli,无 pity 机制——加保底就又造出可预测节拍,违背本意)。
- 不改慢启动每日上限(那是配额不是节奏)。

## Decisions

1. **字段落全局单例表,随既有写路径**。`cadence_mode TEXT NOT NULL DEFAULT 'fixed' CHECK IN ('fixed','probabilistic')`。模式变更视同 rule/consumption 数值变更触发级联传播(继承环境 policy_revision 逐行 +1)——运行时快照按既有 mismatch 机制重置,杜绝「旧模式计数 + 新模式判定」混跑。schemaVersion 抬 `facebook_operation_global_policy@4`。
2. **模式进各运行时策略快照**。规则 / 消费 store 的 `policy.snapshot` 增加 `cadenceMode`,`sameSnapshot` 比较含它——快照即行为指纹,模式翻转 = 快照失配 = 进度重置,与数值变更同一语义。
3. **轮含加群:创建时掷骰落库**。规则批次表加列 `includes_join BOOLEAN`(automation 迁移;NULL = 旧行,读取时回落 `sequence % N` 派生)。fixed 模式创建时也落派生值(单一事实源);probabilistic 落掷骰结果。kernel 的 `facebookRuleRoundIncludesJoin` 保留为 fixed 派生用。
4. **kernel 校验器接受两种键集**。`isFacebookOperationBaseline` 改为「11 键必备 + `cadenceMode` 可选(有则必须合法值)」;消费方缺字段回落 `'fixed'`(= 现状,是安全缺省而非静默错标)。api 发新字段前镜像 version 必 bump(迁移内 DML,样板 0108)→ 消费方全量重放,不触 `same_cursor_payload_drift`。
5. **随机源全部注入口**。role-dispatcher 复用已有 `random` 注入(上一 change 加的);规则 / 消费 store 构造项加 `random?: () => number`。概率判定 `random() < 1 / N`。
6. **kernel v0.1.5**。类型 `FacebookCadenceMode` + `FACEBOOK_CADENCE_MODES` + 投影字段 + 校验器,纯类型/纯函数,符合 kernel 准入。api pin 从 v0.1.1 直抬 v0.1.5(跨 4 版,typecheck + 全量测试把关兼容性);automation 从 v0.1.4 抬 v0.1.5。
7. **schema 门一并抬**(0108 先例):automation 读新字段硬依赖 api 迁移 0118 已应用,`REQUIRED_SCHEMA_VERSION` / `KNOWN_MAX_SCHEMA_VERSION` 抬到本批迁移。

## Risks / Trade-offs

- [概率长旱/爆发] N=10 时 30 次不中概率约 4%,也可能相邻两次命中 → 本性使然,用户要的就是不可预测;配额 / 冷却闸兜住爆发侧。
- [api pin 跨 4 版] v0.1.2–v0.1.4 的 kernel 变更(词汇批改名等)随 pin 进入 api → typecheck + api 全量测试把关;部署时随包送新 kernel(ECS 拉不动私有 git 依赖)。
- [部署窗口偏斜] automation 先带新校验器 / api 先发新字段,两个方向都被「可选键 + 缺省回落 fixed」覆盖;镜像 bump 迁移保证游标前进。
- [console 提交体手写展开漏字段] 编辑器提交处逐字段手写(`FacebookOperationGlobalPolicyEditor.tsx:461-475`),新字段必须显式加——已列入任务防漏。

## Migration Plan

- api 迁移 0118:加列 + `config_mirror_version` bump(单迁移两段,DDL 幂等 IF NOT EXISTS + DML)。
- automation 迁移 0119:规则批次表加 `includes_join BOOLEAN`(NULL 容忍旧行)。
- 部署 dev:automation 先(新 kernel + 校验器 + 消费分支,缺字段回落 fixed)→ api(迁移 + 发新字段)→ console。回滚 = 逐服务备份还原;列是 additive、default 'fixed',回滚服务不需回滚库。
