## 0. 开工前置

- [x] 0.1 复核缺陷仍然存在（登记可能比代码旧）：确认 `automation-main.ts` 的 health 载荷仍带
  `asOf: Date.now()`，且 `automationOutboxRetentionTopics` 仍只有两条主题
  <!-- 2026-08-05 实读代码确认两者都还在。 -->
- [x] 0.2 记下当前基线，供部署后对账
  <!-- 2026-08-05 20:00 dev 属主库实测：
       · event_outbox 共 141,245 行 / 45MB（堆 28MB + 索引 17MB）
       · 分主题：sync_read.changed dev 81,938 + ol 59,253（99.98%）；config_mirror.bump dev 17；
         risk.command dev 6 / ol 1
       · 分流：automation_config_mirror_health dev 81,140 + ol 59,057（该主题 99.3%）；
         edge_presence dev 775 / ol 196；publish_in_flight dev 16；captcha_availability dev 9
       · 近 24h 该主题 +17,203 行 = 每 target 每 10 秒一条
       · automation_sync_read_owner_generation：该流代数 dev 81,148 / ol 59,064
       · 中继游标 api-sync-read-changed-relay 在队头，零积压 -->
- [x] 0.3 确认 `sync-split-repos` dry-run 的既存差异清单，本 change MUST NOT 卷入
  `aidcp-transport/src/schema/schema-contract.ts` 那条非本次差异
  <!-- 开工时它是「内容不同 1」；全程只用 --repo 限定 kernel / automation / api / content，
       没碰 transport 的 src。收工前该条已自行消失（他人 land），本 change 与它无交集。 -->

## 1. aidcp-cloud — 事实源（§8.0 永不部署，但改动必须落在它身上）

- [x] 1.1 `src/kernel/sync-read-facts.ts`：`AutomationConfigMirrorHealthSnapshot` 删除 `asOf` 字段
  <!-- aidcp-cloud 11bacad -->
- [x] 1.2 同文件 `isSyncReadFactPayload` 中该流的 `hasExactKeys` 穷举键同步删除 `asOf` 及其取值校验
  <!-- aidcp-cloud 11bacad 穷举键保持 exact，未放宽。 -->
- [x] 1.3 未触碰 `syncReadPayloadDigest` 的覆盖范围（digest 继续盖全 payload）
  <!-- 刻意不做「摘要排除若干字段」：那会让 same_cursor_payload_drift 失效。 -->
- [x] 1.4 单体侧该 health 载荷的生产者同步去掉 `asOf`
  <!-- aidcp-cloud 11bacad：server.ts 的 `...health` 改为逐字段取（面板投影仍保留 asOf，
       两者不是同一个东西）。全仓 grep 确认无第三处生产者。 -->

## 2. 派生同步（MUST NOT 手工搬文件）

- [x] 2.1 dry-run 确认待同步文件即为 1.x 改动
- [x] 2.2 `--apply` 同步 kernel / automation 派生物（含 `--tests`）
  <!-- aidcp-kernel 5aab64b（src + 自己那份 sync-read-facts.test.ts）。 -->
- [x] 2.3 对齐三仓 kernel sha pin
  <!-- kernel 5aab64b → transport 4c04cbe → api/automation/content 三仓同时跟 pin。
       ⚠️ **transport 自己也 pin kernel**，不跟着走会在同一进程里解析出两份 kernel；
       api 那条「api 与 transport 必须解析到同一个 kernel pin」的门禁当场拦下了本次。
       另：api 的 node_modules 装的仍是旧 sha 时 typecheck 一路绿，
       npm install 之后才暴露出一处 fixture 真的坏了（对应 memory worktree-stale-kernel-install）。 -->

## 3. aidcp-automation — 载荷生产者与保留策略表

- [x] 3.1 `automation-main.ts` 的 `configMirrorHealth()` 去掉 `asOf`，保留那份如实回报与其注释
  <!-- aidcp-automation 8a0d366 -->
- [x] 3.2 建立 outbox 主题穷举登记表（五条，各带保留裁定或「不需剪裁 + 理由」）
  <!-- 落在 aidcp-cloud 8dff95e → 派生 aidcp-automation 8a0d366：
       src/transport/event-outbox-topic-roster.ts。 -->
- [x] 3.3 `automationOutboxRetentionTopics` 增加两条主题，**都不设 `unconsumedRetentionMs`**
  <!-- aidcp-automation 8a0d366。中继消费者名由组装根注入、不在记账模块 import：
       automation → composition 是边界门禁禁止的方向（census 当场判 forbidden，已实撞一次）。
       该参数刻意必填无缺省——名字对不上时剪裁器会永远等一个不存在的消费者追平，
       与「漏登记」几乎同形。 -->
- [x] 3.4 保留期取值定档并写明理由
  <!-- sync_read.changed 1h（纯加速器）/ config_mirror.bump 24h（承重信号、产量极低）。 -->
- [x] 3.5 机械闸：保留策略表逐条覆盖登记表；类型层 `Record<EventOutboxTopic, …>` 穷举
  <!-- 变异验证做了两次，各自精确变红：
       ① 把 asOf 加回穷举键 ⇒ 契约用例红；
       ② 把观测时刻折进摘要输入 ⇒ 行为用例红。
       另有一次**变异未变红**并被追查：改真 SQL 时新增用例没红，因为它走的是测试里的
       内存假池而非真 SQL —— 记在这里，别把那次绿读成「闸有效」。 -->
- [x] 3.6 补验收用例：登记表 / 策略表双向对账
  <!-- AC-OUTBOX-RETENTION-01/02/03，aidcp-automation 8a0d366。
       主题名在登记表里是手抄的（避免跨属主 import 图），配套引用断言逐条 === 真导出常量。 -->

## 4. aidcp-api — 新鲜度续期与变更通知解耦

- [x] 4.1 新增 `API_SYNC_READ_REFRESH_MS = 10_000`；`API_SYNC_READ_FULL_REFRESH_MS` 退回上限身份
  <!-- aidcp-api beeeb84 -->
- [x] 4.2 `startPeriodic` 默认间隔改用新常量
  <!-- aidcp-api beeeb84 -->
- [x] 4.3 验收用例断言周期 **严格小于** 新鲜期窗口
  <!-- AC-API-SR-MARGIN-01/02。变异验证：把周期改回 30_000，两条当场变红。 -->
- [x] 4.4 无通知时仅凭周期 fetch 仍持续 fresh
  <!-- 由 kernel 既有 `freshness_renewed` 路径 + 4.3 的余量断言共同保证。
       另加一道**跨仓漂移守卫**（4.3 钉不住的那半）：新鲜期窗口是 automation 仓的常量，
       改按收到的真实信封判，窗口 < 3 倍周期即具名 warn（每条流只说一次、照常应用快照）。 -->

## 5. 回归（§4 纪律：先 acceptance 再全量再 typecheck）

- [x] 5.1 aidcp-cloud：acceptance 189/189 → 全量 4225 pass / 0 fail / 11 skip → typecheck CLEAN
- [x] 5.2 aidcp-automation：acceptance 296/296 → 全量 2286 pass / 0 fail / 3 skip → typecheck CLEAN
- [x] 5.3 aidcp-api：acceptance 26/26 → 全量 570 pass / 0 fail → typecheck CLEAN
- [x] 5.4 aidcp-kernel 71 pass / aidcp-transport 36 pass / aidcp-content 469 pass，各自 typecheck CLEAN
- [x] 5.5 变异检查（见 3.5 / 4.3）
  <!-- ⚠️ 恢复变异 MUST NOT 用 `git checkout -- <file>`：本次那么做过一次，把同文件里
       真正的改动一起revert 了（当时已发现并重做）。用反向 patch 精确还原。 -->

## 6. 提交与部署（§5 / §6 / §7）

- [x] 6.1 各仓提交推送（cloud 走 worktree + land-change；其余在 canonical master 上按路径 stage）
  <!-- aidcp-cloud 11bacad / 8dff95e（两条 worktree 分支已 land 并清理）
       aidcp-kernel 5aab64b · aidcp-transport 4c04cbe
       aidcp-automation 8a0d366（+ 0ccdef2 pin）· aidcp-api beeeb84 · aidcp-content cfa6544
       另 aidcp-automation 322215f 是 `--tests` 顺带带下来的三份他人派生测试，
       单独一提交、刻意不混进本 change 的台账。 -->
- [x] 6.2 部署前先探 dev ECS 真实现状
  <!-- 三服务 active、六端口在、单体 inactive+disabled（那个抢锁的雷是关着的）、isales inactive。
       ⚠️ **实测发现且非本 change 造成**：api/automation/content 三个 unit 都是 `disabled`，
       重启机器不会自启。已在 8.3 登记。 -->
- [x] 6.3 按 §5 安全序列部署 dev 三个派生服务；`aidcp-cloud` 按 §8.0 未部署
  <!-- 2026-08-05 21:30–21:36。序列：三槽各自备份（*.bak.20260805-212958.tar.gz + .env.bak）
       → git archive HEAD 快照 rsync（不从工作区推、排除 .git/node_modules/.env）
       → 删 node_modules/aidcp-{kernel,transport} + npm install
       → ECS 上三槽各跑一次 typecheck，全 CLEAN
       → 按属主域先接口域后重启（content → automation → api）
       → 三服务 active、NRestarts=0、六端口全在、单体仍 inactive+disabled、isales 未碰。

       ⚠️ **content 的 npm install 失败过一次**：node_modules 里残留的 esbuild 二进制版本
       与 package 期望不符（0.28.0 vs 0.28.1）。`rm -rf node_modules` 全量重装后 CLEAN。
       依赖 pin 变动时半量安装会踩这个，照 memory textcard-cover-form-change 的口径走全量。

       ⚠️ **滚动重启期间中继短暂受阻属预期**：automation 先起、api 还是旧构建，
       新载荷过不了旧契约的穷举键校验 ⇒ 中继停在 id=142398 之前重放（**没有丢弃**），
       api 起来后自行恢复、游标回到队头。契约跨进程变更必然有这个窗口，
       中继「堵住而不跳过」正是要的行为。 -->
- [x] 6.4 落地 sha 回写本文件（见 6.1）；sha 均取自已推送的提交

## 7. 部署后验收（直接查库 / 查日志，MUST NOT 用「进程还活着」代替）

- [x] 7.1 `automation_config_mirror_health` 代数停止空转增长
  <!-- dev 代数停在 81,735、updated_at=21:36:04（重启那一刻）之后不再前进。
       对照组 ol 仍在涨（59,644 → 21:37:06 仍在动）——**OL 还跑着旧构建**，
       这同时证明这项测量是灵敏的，不是「查不出来」。 -->
- [x] 7.2 `sync_read.changed` 新增速率掉到接近 0
  <!-- dev 侧 max(created_at) 停在 21:36:04（部署时刻）。ol 侧继续按每 10 秒一条产出。 -->
- [x] 7.3 剪裁生效
  <!-- 重启后第一轮即：`剪裁 topic=sync_read.changed 删除 2000 行（上界 id=142396）`
       + `剪裁 topic=config_mirror.bump 删除 17 行（上界 id=118859）`。
       config_mirror.bump 已**清零**（该主题从表里消失）。
       sync_read.changed 存量 8 万行，按 2000 行/10 分钟推进 ⇒ 单 target 约 6.7 小时排空，
       属预期，MUST NOT 因「一轮没清空」判失败。 -->
- [x] 7.4 剪裁 MUST NOT 越过游标
  <!-- dev：剪后 min(id)=2005、max(id)=142398，而中继游标 last_id=142398（在队头）。
       删的全在游标下界以内。 -->
- [ ] 7.5 api 日志里「全局周活跃掩码镜像非 fresh」每分钟一次的告警消失，
  且 **MUST 分别确认**：是续期真的接上了，不是把陈旧判据改松了
  <!-- 部署后 3 分钟窗口内该告警零条，但**时间太短，不作数**：原频率约每分钟一条，
       三分钟的静默不足以与偶发区分。留作观察项，见 8.3。
       判据的后半（没改松）已由代码面确认：陈旧判据本身一行未动，
       改的只是周期刷新间隔（30s → 10s）。 -->
- [x] 7.6 三条真变化流的通知仍正常产生
  <!-- 反向断言由 AC-OUTBOX-RETENTION 之外的行为用例覆盖（事实真变了必须发）；
       真机侧 edge_presence 在部署后仍有新代数产生。 -->

## 8. 收口

- [x] 8.1 登记本次显式不修的残留
  <!-- ① 若 automation 日后真的跑起镜像刷新器，`entries` 内的 `lastComparedAt` / `staleForMs`
          会重新引发同类 churn。今天 entries 恒为空故按 YAGNI 不修，
          **下次遇到不得当成新发现**。
       ② **OL 仍跑旧构建**，该主题在 OL 侧继续按每 10 秒一条增长（部署 OL 需用户明确要求，
          且须从 release 分支走，见 §5）。
       ③ 单体 aidcp-cloud 的剪裁名单仍只有两条主题。它按 §8.0 永不部署、只作回滚路径，
          本次刻意未动（monolith 形态下这两条主题的消费者是否存在需另行判定，
          `consumers: []` 与 `consumers: [不存在的名字]` 后果相反）。 -->
- [ ] 8.2 回写 `deploy-derived-services-to-dev` 的 tasks.md：8.1 第 ④ 条已由本 change 收掉
- [ ] 8.3 观察项登记进 `docs/real-machine-acceptance-backlog.md`
  <!-- ① 7.5 的告警消失需一段够长的观察窗（原频率约每分钟一条）；
       ② dev 存量排空需约 6.7 小时，届时确认行数确实降到保留期以内；
       ③ **非本 change 造成**：dev 上 api/automation/content 三个 unit 都是 disabled，
          重启机器不会自启。 -->
- [ ] 8.4 `openspec validate bound-event-outbox-growth --strict` 通过后归档
