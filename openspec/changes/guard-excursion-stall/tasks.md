# Tasks — guard-excursion-stall

> 落点全部在 `aidcp-cloud`，属主均为 `automation`（§8：改完须经 `scripts/sync-split-repos` 同步到
> `aidcp-automation` 才能部署 dev——dev 现跑派生三服务，`aidcp-cloud.service` 已 disabled）。
> 不碰 `aidcp-edge`（`notification_back_home` 的语义 bug 由另一条工作流修）。

## 1. aidcp-cloud — 停滞判据与常量

- [x] 1.1 `src/risk/resume-limits.ts` 新增 `EXCURSION_STALL_TIMEOUT_MS`（300_000）与
      `EXCURSION_STALL_MAX_RECOVERIES`（1），写清 lockstep 不变量：MUST ≥ `IDLE_NUDGE_MIN_MS`
      （后者已锚定单次模型调用天花板 180s），且 `× (预算+1)` MUST 远小于 `DEFAULT_IDLE_END_MS`。
      <!-- aidcp-cloud 290f41d 常量 + 两条 lockstep 不变量写在注释里，由 §5.6 tripwire 断言 -->
- [x] 1.2 `src/event-bus/types.ts`：`notification.triage_done` 载荷加可选 `givenUp?: NotificationCategory[]`
      （additive，不动 `RoleName` 穷举、不新增角色）。
      <!-- aidcp-cloud 290f41d additive 可选字段；未动 RoleName、未新增角色 -->

## 2. aidcp-cloud — 三态原因值

- [x] 2.1 `src/agents/notification-triage.ts`：分诊完成时把「到尝试上限被放弃的分类」带进
      `notification.triage_done`（今天只进日志），使「清零收尾」与「诚实放弃」不再压成一态。
      <!-- aidcp-cloud 290f41d givenUp 随事件带出；日志保留原有 detail 串 -->
- [x] 2.2 `src/agents/excursion-resumer.ts`：`triage_done` 入口按 `givenUp` 分流出
      `triage_incomplete:<类名>`，与 `triage_done` 可区分。
      <!-- aidcp-cloud 290f41d triage_done / triage_incomplete:<类名> 两态 -->

## 3. aidcp-cloud — 停滞兜底（有界自愈 + 诚实收尾）

- [x] 3.1 `src/agents/excursion-resumer.ts` 装停滞计时器：`excursion.requested` 起算；
      前进信号（`notification.opening` / `home.arrived` / `category_selected` / `items.arrived` /
      巡视命令 `action.completed{ok:true}`）重排；**MUST NOT** 把 `page.cards.arrived` 等非巡视上报算前进。
      <!-- aidcp-cloud 290f41d 5 类前进信号；page.cards.arrived 刻意不订阅（M1 变异可证） -->
- [x] 3.2 时限到达且巡视仍 active ⇒ 先发一次只读重新对齐（emit `notification.opening{reason:'open'}`
      → `open_notifications`），消耗 1 次自愈预算并响亮记录；**不发**任何 `browse_notification_*`。
      <!-- aidcp-cloud 290f41d 只 emit notification.opening{reason:open}；无 browse_notification_* -->
- [x] 3.3 预算耗尽后诚实收尾：走既有 `resume()`（解除暂停 + 回信息流），reason = `stalled_no_progress:<phase>`；
      不推进「已通知」水位（既有实现天然不推，加断言守住）。
      <!-- aidcp-cloud 290f41d reason=stalled_no_progress:<phase> -->
- [x] 3.4 计时器生命周期：`resume()` 与 `unsubscribe()` 必清、`.unref()`、回调内二道闸复查
      `excursionActive`；`setTimeoutFn` / `clearTimeoutFn` / `clock` 可注入（照 `SessionMonitorRole` 先例）。
      <!-- aidcp-cloud 290f41d resume/unsubscribe 双清 + unref + onStall 复查 excursionActive -->
- [x] 3.5 更新 `excursion-resumer.ts` 文件头注释（它今天自陈「无计时器」）。
      <!-- aidcp-cloud 290f41d 文件头「无计时器」已改写 -->

## 4. aidcp-cloud — 观测缺口

- [x] 4.1 `src/orchestrator/role-dispatcher.ts` 软暂停（`browseSuspended`）丢弃分支补节流日志
      （照配额休眠分支的「首条 + 每 N 条」形态），与其它三条丢弃分支对齐。
      <!-- aidcp-cloud 290f41d 首条 + 每 50 条节流，excursion.requested 归零；上线当天即在 dev 真日志出现 -->

## 5. aidcp-cloud — 测试

- [x] 5.1 承重用例（复刻事故 + 违规输入）：巡视开着 → 之后只喂 `page.cards.arrived` → 推进假时钟
      ⇒ 断言先出自愈 `open_notifications`；再推进 ⇒ 断言 `browseSuspended=false`、`excursionActive=false`、
      `feed.entered{back_to_feed}` 已发、reason 以 `stalled_no_progress` 开头。
      <!-- aidcp-cloud 290f41d 违规输入置于窗口中段（置于窗口起点时 M1 变异抓不住，已修正） -->
- [x] 5.2 反向闸：时限内持续喂前进信号 ⇒ 零自愈命令、不强制收尾（守「兜底不误伤」）。
      <!-- aidcp-cloud 290f41d 四类前进信号逐条覆盖 -->
- [x] 5.3 自愈恰好 1 次（不是 0、不是 2）。
      <!-- aidcp-cloud 290f41d 断言恰好 1 条自愈命令（M2/M3 变异各自转红） -->
- [x] 5.4 三态原因值可区分：诚实放弃 ⇒ `triage_incomplete` 前缀，与 `triage_done` 不相等。
      <!-- aidcp-cloud 290f41d 含 triage 角色真产出 givenUp 的接线断言 -->
- [x] 5.5 计时器不跨场：`unsubscribe()` 后推进时钟 ⇒ 零事件。
      <!-- aidcp-cloud 290f41d 另补「显式终止即停表」用例（M4 变异需靠它才抓得住） -->
- [x] 5.6 acceptance tripwire：常量关系断言（§1.1 的两条不变量）。
      <!-- aidcp-cloud 290f41d 落 test/pacing-snapshot.test.ts（既有 lockstep tripwire 的同一处） -->

## 6. 门禁与集成

- [x] 6.1 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（aidcp-cloud）。
      <!-- aidcp-cloud 290f41d acceptance 189/189；全量 4202 pass / 0 fail / 11 skip；typecheck 0 -->
- [x] 6.2 边界门禁无新增违规（`npm run boundaries:refresh` 对账 + `test/acceptance/module-boundary.test.ts`）。
      <!-- aidcp-cloud 290f41d module-boundary 12/12；boundaries:refresh 跨层边 0、生成物零漂移 -->
- [x] 6.3 `scripts/land-change aidcp-cloud guard-excursion-stall` 合回 master 并推送。
      <!-- aidcp-cloud 290f41d land-change --yes，ff 推送 origin/master -->
- [x] 6.4 `scripts/sync-split-repos --repo aidcp-automation` 对账 → `--apply`（src + tests），
      在 `aidcp-automation` 跑 typecheck + 测试并推送。
      <!-- aidcp-automation 7829333 sync-split-repos --repo aidcp-automation --tests --apply（5 src + 4 test，含 2 个既有派生漂移的 publish-agent 测试）；typecheck 0；全量 2250 pass / 1 fail = 既有基线红 boundary-record（stash 对比证明与本批无关） -->

## 7. 部署（dev）

- [x] 7.1 探 ECS 真实现状（跑的是 `aidcp-{api,automation,content}.service`，`aidcp-cloud.service` disabled）。
      <!-- 2026-08-05 dev 跑 aidcp-{api,automation,content}.service，aidcp-cloud.service disabled；automation 听 8787 + 127.0.0.1:8094，ExecStart=npx tsx src/server.ts（无 build 步） -->
- [x] 7.2 备份 `/opt/aidcp/automation` → rsync（`--exclude .env --exclude node_modules --exclude .git`）
      → `systemctl restart aidcp-automation.service` → healthcheck（active + 8787 监听 + 日志无启动错）。
      <!-- aidcp-automation 7829333 2026-08-05 deployed：备份 automation.bak.20260805-152438.tar.gz + .env.bak → git archive HEAD 干净快照 rsync → restart → schema 门 enforce/通过、同步读 ready、8787+8094 在听、边缘 ads-k1e0ero8 重连后浏览闭环正常跑（open_note/back/LLM 判定齐全）；api/content/isales 六个服务未受影响 -->
- [x] 7.3 失败即回滚。**不碰 ol**、不碰同机 isales。
      <!-- 未触发回滚。备份保留最近 10 个 -->

## 8. 部署途中的两项发现（非本 change 引入，登记给后续部署者）

- **dev ECS 装不了 git 私有依赖**：`npm install` 在 `/opt/aidcp/automation` 直接 `git@github.com: Permission denied
  (publickey)` —— 机器上没有这四个私有仓的 GitHub key。凡涉及 `aidcp-kernel` / `aidcp-transport` pin 变动的部署，
  MUST 改为把本机已装好的 `node_modules/<包>` 目录 rsync 上去，MUST NOT 指望机上 `npm ci` / `npm install`。
  （本次即如此处理，rsync 逐条 itemize 证明是纯新增、既有文件一个字节没被改写。）
- **本次 rsync 带上了另一条 change 的 transport pin**：部署前 `/opt/aidcp/automation/package.json` 停在
  `aidcp-transport#7e6cba4`，而 master 已是 `#b8c8dd7`（change `restore-panel-capability-wiring` 落的，尚未部署）。
  从 master 部署必然带上它。**放行判据不是「大概没事」而是实读**：`git diff 7e6cba4 b8c8dd7` 是纯增两个文件
  （`src/transport/{model-probe-http,panel-content-http}.ts`），`src/llm` 零改动 —— 而 automation 对 transport 的
  全部消费面只有 `automation-model-exit.ts` 的 `llm/providers.js` + `llm/qwen.js`，逐字未变。故装上是安全的，
  且**必须装**：留 package.json 声明一个没装上的 sha，正是 CLAUDE.md §8.1 那条「npm 装到旧 sha 不报错、编译照过、
  跑的却是过期契约」的静默漂移。同批新增的两个 `src/transport/*.ts` 在 automation 内**无人 import**，运行时惰性。
