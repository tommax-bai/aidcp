## Why

`event_outbox` 上有一个主题只进不出：dev 上该表 141,245 行 / 45MB，其中 `sync_read.changed` 占
99.98%，而该主题里 `automation_config_mirror_health` 一条流又占 99.3%，在 **dev/ol 共用的生产库**上
每 target 每 10 秒稳定写一行（近 24h 实测 17,203 行）。

根因不是「事实变得快」，是**「变没变」的判据里混进了一个时钟**：那条流的载荷带
`asOf: Date.now()`，而变更检测取的是整份载荷的摘要 ⇒ 摘要每次必变 ⇒ 代数必增 ⇒ 通知必发。
更讽刺的是这条流在派生进程里内容恒定为空（`entries: []`，因为镜像刷新器属 api），
**全库最大的数据生产者，报的是「这里什么都没有」**。

剪裁器本身是接了的，但它的主题名单只有 `panel.event` 与 `risk.command`；
`sync_read.changed` 与 `config_mirror.bump` 两条都不在名单里 ⇒ 无界增长且无任何告警。
本次是靠人工查库才发现的 —— 这个类别今天**没有任何机械手段能看见**。

## What Changes

- **把观测时间戳移出载荷**：`AutomationConfigMirrorHealthSnapshot` 删除 `asOf` 字段（含 kernel 类型、
  `isSyncReadFactPayload` 的穷举键校验与两处生产者）。投递时刻由信封的 `asOf` 承担，
  消费方本来读的就是信封那份，载荷里这份无任何消费方。
  **BREAKING**（kernel 契约）：三仓 kernel sha pin 同步推进。
- **MUST NOT 改成「摘要排除某字段」**：摘要必须盖全载荷，否则 `same_cursor_payload_drift`
  那道闸失效 —— 本仓已因「同游标不同载荷」栽过（拒收永久 + 启动期 fail-closed → 整机起不来）。
  正确形态是把非事实字段移出载荷，不是移出摘要。
- **新鲜度续期与变更通知解耦**：接口进程的周期快照刷新压到新鲜期的三分之一（30s → 10s），
  与属主侧已在用的比例对齐。今天两者恰好相等、卡在边界上，
  凡是没有变更通知托底的流都会周期性 stale（dev 日志每分钟一条实测在刷）。
  `automation_config_mirror_health` 今天不抖，**正是因为这个 bug 每 10 秒顺手续了一次期**；
  不一并修就等于用一处数据库膨胀换一处就绪度抖动。
- **补齐剪裁登记**：`sync_read.changed`（消费者 `api-sync-read-changed-relay`）与
  `config_mirror.bump`（消费者 `config-mirror-bump`）进保留策略表，按消费者游标下界剪，
  两条都 MUST NOT 设强删兜底。
- **加一道穷举闸**：outbox 主题建穷举登记表，保留策略必须逐条覆盖；
  「确实不需要剪」要显式写明理由，MUST NOT 靠遗漏表达。新增主题却没有保留策略 ⇒ 当场失败。

## Capabilities

### New Capabilities
- `event-outbox-retention`: `event_outbox` 的保留期契约 —— 每条主题必须有显式保留裁定、
  按消费者游标下界剪裁、承重主题禁止强删、遗漏由机械闸当场拦下。

### Modified Capabilities
- `cloud-api-automation-sync-read-mirrors`: ① 变更通知只由**事实**变化触发，观测时刻
  MUST NOT 进入参与变更检测的载荷；② 镜像新鲜度续期 MUST NOT 依赖变更通知通道，
  周期 owner fetch 必须严格落在新鲜期以内；③ config-mirror health 载荷不再携带 `asOf`。

## Impact

- **aidcp-cloud**（事实源，§8.0 永不部署）：`src/kernel/sync-read-facts.ts`、
  `src/transport/automation-sync-read-source.ts`
- **aidcp-kernel / aidcp-automation**：上述两文件的派生物，经 `scripts/sync-split-repos --apply` 同步，
  MUST NOT 手工搬文件；三仓 `package.json` 的 kernel sha pin 同步
- **aidcp-automation**（派生仓私有组装根，直接改）：`src/automation-main.ts`（载荷生产者）、
  `src/automation-risk-accounting.ts`（保留策略表）
- **aidcp-api**（组装根，直接改）：`src/server.ts`（周期刷新间隔）
- **数据库**：`event_outbox` 存量按游标下界回收；`automation_sync_read_owner_generation`
  的代数不再空转增长。无 schema 迁移。
- **顺带收口**：`deploy-derived-services-to-dev` 的 tasks.md 8.1 第 ④ 条（同步读就绪度仍在抖）
