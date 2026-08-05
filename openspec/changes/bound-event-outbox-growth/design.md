## Context

### 现状与实测（2026-08-05 从 dev ECS 直查 automation 属主库）

- `event_outbox` 共 **141,245 行 / 45MB**（堆 28MB + 索引 17MB）
- 按主题：`sync_read.changed` dev 81,938 + ol 59,253（**99.98%**）；`config_mirror.bump` dev 17；
  `risk.command` dev 6 / ol 1
- `sync_read.changed` 按流：`automation_config_mirror_health` dev 81,140 + ol 59,057（该主题的 99.3%）；
  `edge_presence` dev 775 / ol 196；`publish_in_flight` dev 16；`captcha_availability` dev 9
- 近 24h 该主题新增 **17,203 行 = 每 target 每 10 秒一条**
- `automation_sync_read_owner_generation` 里该流代数已到 dev 81,148 / ol 59,064
- 中继消费者 `api-sync-read-changed-relay` 游标**在队头**（零积压），`event_outbox_cursor` 聚合行两个 target 都有

### 根因链（每一环单独看都是对的）

1. `aidcp-automation/src/automation-composition-root.ts:470` — `AUTOMATION_SYNC_READ_REFRESH_MS = 10_000`，
   属主流每 10 秒观测一次
2. `aidcp-automation/src/transport/automation-sync-read-source.ts:99-103` — 对**整份载荷**取摘要
   （`aidcp-kernel/src/kernel/sync-read-snapshot.ts:545`，sha256 over canonical JSON）
3. `aidcp-automation/src/transport/automation-sync-read-generation-store.ts:33-53` — 摘要不同才 `generation + 1`
4. `aidcp-automation/src/transport/sync-read-changed-outbox.ts:38-51` — 代数前进才写 outbox 行
   （**这个去重设计本身是正确的**，另外三条流就是靠它活得很干净）
5. **断在第 5 环**：`aidcp-automation/src/automation-main.ts:373-379` 的载荷是
   `{sourceService:'automation', asOf: Date.now(), enabled:false, pollMs:0, entries:[]}` ——
   `asOf` 每次都变 ⇒ 摘要必变 ⇒ 代数必增 ⇒ 行必写
6. 载荷其余字段恒定：该进程**没有**配置镜像刷新器（属 api），如实报 `entries: []`。
   该处注释已说明为什么不能编一份假条目表 —— **这个诚实是对的，本 change MUST NOT 改它**
7. 下游只读 `entries`；`asOf` 读的是**信封**那份
   （`aidcp-api/src/config/api-sync-read-mirrors.ts:160-162` 取 `view.metadata?.sourceAsOf`）
   ⇒ **唯一在变的字段，恰好是没有任何消费方读的字段**

### 每条无用通知的真实代价

写行 + `pg_notify` + 中继拉取 + HTTP 投递到 api（`aidcp-api/src/server.ts:3035-3052`）+
api 反向 HTTP 回拉快照 + `mirrors.apply` + 检查点 UPSERT。
而 api 自己本来就有周期全量刷新兜底（`aidcp-api/src/server.ts:492-495` 注释明写
「周期刷新才是承重，丢唤醒不会漏 delta」）⇒ 这 1.7 万趟/天**没有一趟是必需的**。

### 剪裁登记的现状

`automationOutboxRetentionTopics`（`aidcp-automation/src/automation-risk-accounting.ts:137-155`）
只有 `panel.event` 与 `risk.command`。`sync_read.changed` 与 `config_mirror.bump` 都不在名单里。
后者九天才 17 行，所以一直没暴露 —— **它和前者是同一个缺口，只是产量不同**。

## Goals / Non-Goals

**Goals:**

1. 让 `sync_read.changed` 的写入速率回落到「事实真的变了才写」，即该流从 ~8,600/target/天 降到接近 0
2. 修根因**不引入**新的就绪度抖动（见 Decisions 第 2 条，这是必需项不是搭车项）
3. 两条漏登记主题进保留策略，存量按消费者游标下界回收
4. 让「新增 outbox 主题却没有保留策略」在机械闸上当场失败，关掉这一**类别**而不只是这一**例**

**Non-Goals:**

- 不改 `entries: []` 那份诚实回报（它是对的）
- 不改 `pruneEventOutbox` 的游标下界算法（现有实现够用，聚合游标行已就位）
- 不为 `sync_read.changed` 开强删兜底口子
- 不重构同步读的通知/快照分层，不动 `panel.event` / `risk.command` / `interaction.audit_event` 的既有策略
- 不处理「若 automation 将来真的跑起镜像刷新器、`entries` 内的 `lastComparedAt`/`staleForMs`
  会再次逐次变化」这一将来形态（见 Risks，本次显式登记不修）

## Decisions

### 决策 1：把 `asOf` 移出载荷，而不是把它移出摘要

**选中**：删除 `AutomationConfigMirrorHealthSnapshot.asOf`，同步删 `isSyncReadFactPayload` 里
该流 `hasExactKeys` 的对应键（`sync-read-facts.ts:62-80` 与 `:298-309`），并改两处生产者。

**否决：让摘要跳过若干「易变字段」。** 这条路看着更省事，但会**当场废掉一道红线闸**：
`same_cursor_payload_drift`（`sync-read-snapshot.ts` 的 apply 分支）靠「同游标必须同摘要」
判断载荷漂移。摘要一旦不盖全载荷，两份不同载荷就能合法共用一个游标而不被发现。
本仓已因「同游标不同载荷」栽过一次（拒收永久 + 启动期 fail-closed → 整机起不来），
dev 日志里 2026-08-05 16:49 还能看到 `client_environment_automation` 的同类拒收。
**摘要必须盖全载荷；不该进摘要的东西，本来就不该进载荷。**

**为什么删得掉**：投递时刻在信封上另有一份（`makeSyncReadFactEnvelope` 的 `asOf: observedAt`），
消费方读的就是信封那份，载荷里这份零消费方。删它是把一个**非事实**移出事实载荷，
不是丢失信息。

### 决策 2：新鲜度续期必须与变更通知通道解耦（必需项）

**现状是一个巧合**：`API_SYNC_READ_FULL_REFRESH_MS = 30_000`（`aidcp-api/src/server.ts:325`，
3303 行以默认值启动），而信封的 `freshUntil = observedAt + DEFAULT_FRESH_MS(30_000)`
（`automation-sync-read-source.ts:19,109-111`）—— **刷新周期恰好等于新鲜期，卡在边界上**。
凡是没有变更通知托底的流都会周期性 stale，dev 日志实测每分钟一条：

```
[aidcp-api] 全局周活跃掩码镜像非 fresh（state=stale），本次按「未配置」处理
```

`automation_config_mirror_health` 今天不抖，**正是因为决策 1 要修的那个 bug 每 10 秒触发一次
`refreshStream`、顺带续了一次期**。只修决策 1 ⇒ 这条流掉成和上面那条一样每 30 秒抖一次，
而它是 api 就绪度的五个判据之一（`api-sync-read-mirrors.ts:179-186`）。

**选中**：接口进程周期刷新压到新鲜期的三分之一（10s），与属主侧已选比例一致；
`API_SYNC_READ_FULL_REFRESH_MS = 30_000` 保留为**上限校验值**，另立实际默认值常量。

**否决：把 `freshUntil` 的窗口拉长。** 那是把新鲜度定义改松来迁就轮询周期，
等于降低所有消费方的陈旧判据精度，代价面比调周期大得多。

**否决：保留一条周期性的「保活通知」。** 那是把 bug 的副作用固化成设计，
且会让「通知＝有变化」这个语义永久失真 —— 通知通道从此再也不能用来判断事实是否变化。

**续期路径本来就有**：kernel 的 `freshness_renewed` 分支（同游标 + `owner_fetch` + 更晚 `asOf`）
已实现且有 spec 场景背书，只要刷新周期真的落在新鲜期以内就成立。

### 决策 3：两条主题按消费者游标下界剪，都不设强删

`sync_read.changed` 消费者 `api-sync-read-changed-relay`，`config_mirror.bump` 消费者
`config-mirror-bump`，两者的聚合游标行都已就位且在队头 ⇒ 现有
`pruneEventOutbox` 的 `min(last_id)` 下界逻辑**不需要改**，只是名单里缺登记。

**两条都 MUST NOT 设 `unconsumedRetentionMs`**：
- `config_mirror.bump` 是**承重失效信号**，删掉未投递的 = 一处配置永远不 reload；
- `sync_read.changed` 虽然按设计只是加速器（周期快照才承重），但它没有非开不可的理由，
  开一个强删口子等于给将来留一条「消费者没上线也照删」的路。

### 决策 4：穷举登记表 + 机械闸

照本仓已有范式（两份 `protocol.ts` 用 `Record<MessageType,true>` 穷举，漂移即 typecheck 失败）：
给 outbox 主题建穷举登记表，保留策略表必须**逐条覆盖**该登记表。
「确实不需要剪」必须显式写明理由（例如某主题恒为空、或由别处剪），
**MUST NOT 靠在名单里缺席来表达**。

**为什么这道闸是本 change 的主交付物之一**：`config_mirror.bump` 与 `sync_read.changed`
是同一个缺口漏了两次，两次都零告警、零测试覆盖，**本次是靠人工查库才发现的**。
没有这道闸，下一条新主题会以同样的方式静默复发。

## Risks / Trade-offs

**[kernel 契约变更波及三仓]** → 走 `scripts/sync-split-repos --apply` 同步派生物并对齐三仓
kernel sha pin（对账由该脚本负责）；MUST NOT 手工搬文件。
注意当前 dry-run 已有一条**非本 change 造成**的既存差异
（`aidcp-transport/src/schema/schema-contract.ts`），MUST NOT 卷进本次提交。

**[存量检查点里的旧摘要]** → 载荷少一个键 ⇒ 摘要变一次 ⇒ 代数 +1 一次 ⇒ 各消费方按更高游标
正常 apply。这是一次性的、走的是既有 `applied` 路径，不触发 `same_cursor_payload_drift`
（游标前进了）。**不需要清库、不需要迁移。**

**[api 刷新周期 30s → 10s 的负载]** → 快照拉取变 3 倍，但同时**移除**了每 target 每 10 秒一次的
通知驱动 `refreshStream`（那一趟同样是一次快照拉取 + 一次检查点写）。净变化接近零，
且去掉了 outbox 写入与中继投递两段。

**[决策 2 会改变一个正在观察的行为]** → `deploy-derived-services-to-dev` 8.1 第 ④ 条登记的
`publish_in_flight` / `captcha_availability` 周期性 stale 会一并消失。这是修好，不是掩盖；
验收时**MUST 分别确认**「该告警消失」与「不是因为把判据改松了」。

**[将来形态：`entries` 内的时钟字段]** → 若 automation 日后真的跑起镜像刷新器，
`lastComparedAt` / `staleForMs` 会逐次变化、重新引发同类churn。**本次显式不修**（YAGNI：
今天 `entries` 恒为空），但**MUST 在 tasks 里登记这条残留**，别让它下次被当成新发现。

**[剪裁首轮删除量]** → 存量 14 万行，`DEFAULT_OUTBOX_PRUNE_BATCH = 2000`、剪裁周期 10 分钟
⇒ 单 target 约需 40 轮 / 近 7 小时排空，**有界、不锁表**。属预期而非故障，验收时按速率判断而非按「一轮清空」判断。

## Migration Plan

1. cloud（事实源）改 → `scripts/sync-split-repos --apply` 同步 kernel/automation 派生物 → 对齐 sha pin
2. automation / api 各自组装根改
3. 三仓 `npm run test:acceptance` → `npm test` → `npm run typecheck`
4. 提交推送后按 §5 安全序列部署 dev（三个派生服务；`aidcp-cloud` 按 §8.0 **永不部署**）
5. 部署后按 tasks 的验收口径直接查库与查日志

**回滚**：三仓各自回退提交并重新部署；无 schema 迁移、无数据不可逆动作。
剪裁已删掉的行不可恢复，但被删的都是**游标下界以内、已确认投递**的行。
