## 1. aidcp-cloud — 复判通道（自动化段属主）

- [x] 1.1 在角色调度器里定义可恢复拒绝原因集合（未绑人设 / 人设副本陈旧 / 配置镜像陈旧）与结构性拒绝集合（平台无浏览能力），并把「全局调度开关关闭」显式排除在可恢复集合之外；集合以具名常量表达，附一行说明「凭什么判它可恢复」，MUST NOT 写成散在各分支的字面量比较
  <!-- aidcp-cloud 15af742 实作为**穷举 Record** `START_GATE_VERDICT_RECOVERABLE` 而非 Set：
       新增一种裁决结论时不分类就编译不过。Set 会让新原因默默落进「不可恢复」那一支、
       原样重演本 change 要消灭的缺陷。同批把裁决结论抽成具名类型 SessionStartVerdict 供穷举。 -->
- [x] 1.2 加入每连接私有的复判计时器字段与退避节奏（2s → 5s → 10s → 30s → 60s → 稳定 60s），复用调度器既有的可注入计时器（测试桩）而非裸 `setTimeout`
  <!-- aidcp-cloud 15af742 START_GATE_RECHECK_BACKOFF_MS + startGateRecheckTimer/Step/BlockedReason 三字段，
       走既有 setTimeoutFn/clearTimeoutFn 注入口并 unref，与休息 / 窗口唤醒计时器同款。 -->
- [x] 1.3 在带副作用的裁决方法返回 false 的三个可恢复分支里武装复判（武装点收口在裁决方法内部，**不**逐个调用入口武装）；已武装则不重复武装、不重置退避进度
  <!-- aidcp-cloud 15af742 canStartSession 顶部一行收口：`if (START_GATE_VERDICT_RECOVERABLE[verdict]) armStartGateRecheck(verdict)`。
       下面各分支的日志与回调一字未改（零回归）。 -->
- [x] 1.4 复判每一跳只调用无副作用的纯判据：结论仍为可恢复原因 → 静默排下一跳；结论变为可启动 → 走既有的「绑定人设后就地开跑」方法（起会话 + 补重驱）；结论变为结构性拒绝 → 解除武装并记一次终态回执
  <!-- aidcp-cloud 15af742 onStartGateRecheckElapsed。**偏离（更严）**：额外加了一道前置——
       浏览器缺席 / 不在可活跃时段时静默继续等、不调用重启会话方法，否则那两条的既有日志会变成每跳一行的脉冲。
       这两种状态各有自己的恢复路径（浏览器状态事件 / 窗口唤醒计时器），本通道只负责启动闸。 -->
- [x] 1.5 放行时记一条可自证回执，写明「此前被哪一个闸挡住、复判后放行」，与普通握手启动可区分
  <!-- aidcp-cloud 15af742 `账号 X 此前被启动闸挡住（needs_persona_setup）→ 复判放行并就地开跑（无需边缘重连）`；
       只在会话**真的激活**那一刻打，闸放行但会话没起来时不打（否则又是脉冲）。 -->
- [x] 1.6 会话真正激活时解除复判武装
  <!-- aidcp-cloud 15af742 startSession / restartSession 两处 `sessionActive = true` 之后各一行。 -->
- [x] 1.7 在会话结束流程中解除复判武装，位置排在「会话本来就不活跃即提前返回」那一行**之前**（与既有的休息计时器 / 窗口唤醒计时器同处）——连接拆除走的正是这条路径
  <!-- aidcp-cloud 15af742。已核实连接拆除链路：connection-runtime teardown → dispatcher.endSession('disconnect')，
       此时 sessionActive 恒 false，故解除动作必须早于那条短路。已做变异检验，见 2.3。 -->
- [x] 1.8 复判跳内 MUST NOT 打日志、MUST NOT 触发被拒回调；确认 1.3 的武装动作本身不改变首次被拒的既有日志与告警行为（零回归）
  <!-- aidcp-cloud 15af742。用例 2.2 断言 6 跳后 onSessionRejected 仍只有 1 条。 -->

## 2. aidcp-cloud — 回归用例（克制，只钉承重的那几条）

- [x] 2.1 用例：未绑人设被拒 → 人设变为已绑 → 复判到点后会话激活且发出重驱；断言首次被拒的告警只出现一次
  <!-- aidcp-cloud 15af742 test/integration/session-start-gate-recheck.test.ts -->
- [x] 2.2 用例：连续多跳仍未绑人设 → 无任何新增日志、无重复被拒回调、退避间隔按节奏拉长
  <!-- 断言实际排期序列 [2000,5000,10000,30000,60000,60000]，末位稳定不再增长。 -->
- [x] 2.3 用例（承重）：连接拆除（走会话结束流程且会话本不活跃）后推进计时器 → 复判不再触发、不起会话、不发任何命令
  <!-- **已做变异检验**：把 1.7 的解除动作挪到「本来就不活跃即返回」短路之后 → 6 条里恰好这 1 条红、
       其余 5 条全绿（归因干净，承重的确实是它，不是端到端那条）。还原后 6/6 通过。 -->
- [x] 2.4 用例：平台无浏览能力被拒 → 不武装复判，推进计时器无任何动作
- [x] 2.5 用例：全局调度开关关闭 → 不武装复判（守住决策四的取舍，防止日后被顺手纳入）
- [x] 2.6 用例：复判与续场休息计时器同窗口先后触发 → 至多起一场会话，无重复订阅 / 重复重驱
  <!-- **偏离**：实作成更贴近真实风险的形态——「复判到点时会话已被别的路径（边缘自行重连）起来」→
       直接解除武装、不重复起会话、不重复重驱。续场休息计时器需注入 resumeConfigProvider 才会武装，
       而真正要防的是「两条恢复路径撞车」这件事本身，与是哪一条撞无关。 -->

## 3. 派生仓同步与门禁

- [x] 3.1 控制仓跑 `scripts/sync-split-repos`（先不带参数 dry-run 对账，再 `--apply --repo aidcp-automation`）；MUST NOT 手工搬文件
  <!-- dry-run 报「内容不同 1」，恰好只有 src/orchestrator/role-dispatcher.ts。--apply 写入 1 个文件。
       另有一条既存的 `多出 src/automation-nurture-provider.ts`（清单外派生私有文件），**未 prune**、与本 change 无关。
       test/ 不派生（既有约定），故用例只在 aidcp-cloud。 -->
- [x] 3.2 `aidcp-cloud` 与 `aidcp-automation` 各跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`，安全红线全过
  <!-- aidcp-cloud: acceptance 204/204、全量 4221（pass 4210 / fail 0 / skip 11）、typecheck exit=0。
       aidcp-automation: typecheck exit=0（本机）+ **ECS 上再跑一次 exit=0**。
       aidcp-automation 工作区当时另有他人未提交的 WIP（automation-publish-dispatch.ts），
       故只显式 stage 了 role-dispatcher.ts，且部署用的是从已推送提交做的干净快照、不是脏工作区。 -->
- [x] 3.3 确认本 change 未触碰热点文件（两份 protocol.ts、动作映射、角色注册、风控状态机）与 `boundaries/` 生成物
  <!-- 改动面 = role-dispatcher.ts 一个文件 + 一个新用例文件。协议 / 数据库 / 边缘 / 接口进程零改动。 -->

## 4. 上线与验收

- [x] 4.1 提交并推送 `aidcp-cloud` / `aidcp-automation` 默认分支
  <!-- aidcp-cloud master 15af742（经 scripts/land-change --yes，rebase + 全量 + typecheck 后 ff 推送）
       aidcp-automation master d2d5896 -->
- [x] 4.2 部署 dev（先探 ECS 现状 → 备份 → rsync → 重启 → healthcheck），按 §5 安全序列
  <!-- 2026-08-05 11:15–11:20 deployed。部署前探得：单体 aidcp-cloud.service 仍 disabled+inactive（守住既有雷）；
       有人在 10:48 手动重启过 automation 但无备份、非部署，线上代码确认仍是旧版（标记串计数 0）。
       序列：automation.bak.20260805-111544.tar.gz + .env.bak → 从 d2d5896 的 git archive 干净快照 rsync
       （排除 .env / node_modules / .git，未用 --delete）→ ECS 上 typecheck exit=0 → restart →
       healthcheck 全过：active、NRestarts=0、六端口齐（8787/8090/8091/8092/8093/8094）、
       schema 契约门 enforce 通过、同步读就绪度 ready、单体仍 inactive。
       重启后 4 个边缘全部重连、会话均已重启（含此前被判死的 61579018622326）。
       **一条如实记录**：停止阶段 SIGTERM 超时被 SIGKILL（10:48 那次人工重启同样如此）——
       是既有的优雅关停问题，非本 change 引入，未处理。 -->
- [x] 4.3 **【按用户裁定清账 2026-08-05：真机验收 / 出包类不再登记、不再统计，直接归档。此勾表示「按裁定清账」，MUST NOT 读成「已验证」】** 真机验收：新建或重连一个未绑人设的 Facebook 环境，确认「被拒 → 人设补齐 → 秒级自动开跑」，且日志里能看到那条可自证的放行回执；结论回写本文件，未覆盖项登记 `docs/real-machine-acceptance-backlog.md`
  <!-- **未验，如实记**：部署后连上的 4 个账号人设都已绑好，没有一个走到 needs_persona_setup，
       因此复判路径在真机上一次也没被触发过。已登记为 backlog 簇 134（134.1~134.4），
       触发条件是日常批量建号里下一个全新 Facebook 环境首次上线，不需要专门造场景。
       MUST NOT 把「桩测 6 条全绿 + 已部署」读成「真机验证过」。 -->
