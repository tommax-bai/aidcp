## 1. aidcp-cloud — 曲线取用与回包

- [x] 1.1 在客户鉴权服务的 Facebook 运行策略端口上新增**必填**的曲线取用方法（返回当前生效的总天数与逐日上限），使两个组装根漏接线时编译期即失败
  <!-- aidcp-cloud 6c165c6 端口方法 slowStartAuthoredCurve()。落点比原计划更强：方法直接加在运行策略存储上，
       而两个组装根注入的都是该存储实例本身 ⇒ 漏接线在结构上不可能发生，派生 api 仓组装根一行未改。 -->
- [x] 1.2 环境慢启动读取记录补出该环境平台（与既有 ownership 查询同一 SQL 形状，不新增一次查询）
  <!-- aidcp-cloud 6c165c6 getEnvironmentSlowStart 的 SQL 加 e.platform，记录三态都带出。 -->
- [x] 1.3 未绑定 / 绑定冲突分支的总天数改为由调用点传入权威值，删除内联的 7
  <!-- aidcp-cloud 6c165c6 environmentOnlySlowStartView 增 totalDays 形参。 -->
- [x] 1.4 慢启动读路由在 Facebook 环境回传曲线：逐日上限只含该平台能执行且按日计数的动作（浏览 / 点赞 / 评论 / 关注 / 发布 / 搜索 / 加组），并带 day 序号
  <!-- aidcp-cloud 6c165c6 读路由 + 写后回读共用 slowStartCurveFor()。动作项直接取后台配置形状
       （本就只按 FB 能配的动作建格）⇒ 不必再查一次平台能力表、也不会补零。 -->
- [x] 1.5 曲线缺席按「字段整个不出现」实现：非 Facebook、平台未确认、策略不可用三种情况都不下发，且不影响其余慢启动真态返回
  <!-- aidcp-cloud 6c165c6 projectClientSlowStartCurve 返回 null 即整字段不出现；数据源刻意用
       slowStartAuthoredCurve()（未就绪返回 null）而非 slowStartRuntimePolicy()（未就绪回落编译默认）。 -->
- [x] 1.6 单体组装根注入曲线取用（读运行时全局策略，与配额 clamp 同一来源）
  <!-- 无需改动：组装根注入的就是运行策略存储实例，新方法随实例带上。1.1 的落点变化把这条变成零工作量。 -->

## 2. aidcp-cloud — 测试

- [x] 2.1 单测：后台改过曲线后，回包逐格等于策略值；总天数跟随策略
  <!-- aidcp-cloud 6c165c6 test/client-auth-server.test.ts；桩曲线刻意取 10 天且每格不同，
       **绝不用出厂默认做桩** —— 用默认会让「读了配置」与「压根没读」两种实现都通过。 -->
- [x] 2.2 单测：未绑定账号的 Facebook 环境总天数取权威值而非 7，且仍不返回 binding / dayQuotas
  <!-- aidcp-cloud 6c165c6 -->
- [x] 2.3 单测：非 Facebook 环境与策略不可用时回包整个不含曲线字段，其余真态照常
  <!-- aidcp-cloud 6c165c6 同文件；另加 test/client-slow-start-curve.test.ts 三条纯函数用例
       （行数不自洽即整体缺席 / fb 别名同源判平台 / 回落天数按引用断言等于风控侧常量）。 -->
- [x] 2.4 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`
  <!-- 2026-08-05 acceptance 204/0、全量 4211/0、typecheck 0。期间 boundaries:refresh 把新文件登记为 api 属主
       （AC-BOUND-01 起初红，属预期的「新文件待登记」）。 -->

## 3. aidcp-api — 派生仓同步与手写组装根

- [x] 3.1 从控制仓跑派生同步（先 dry-run 对账再 apply），确认客户鉴权服务的改动已进派生仓
  <!-- 2026-08-05 scripts/sync-split-repos --repo aidcp-api（dry-run → --apply），源 aidcp-cloud@6c165c6，写入 4 文件。 -->
- [x] 3.2 派生仓手写组装根注入曲线取用（该文件不参与自动同步，必须手改）
  <!-- 无需改动，理由同 1.6；对账明确报告组装根「只报不改」且两处 server.ts/index.ts 差异与本 change 无关。 -->
- [x] 3.3 派生仓 `npm run typecheck` 通过
  <!-- aidcp-api c80beb4 本机 typecheck 0；ECS 上部署后又跑一次，同样 0。 -->

## 4. aidcp-edge — 客户端曲线表按数据渲染

- [x] 4.1 页面结构：删除写死的表体数字与「与云端常量逐格同步」的注释承诺，表头补上「搜索」列
  <!-- aidcp-edge d128a10 index.html 只留空 thead/tbody 容器；列由回包决定，故表头也动态。 -->
- [x] 4.2 渲染层：按回包曲线渲染表体，行数取回包行数；数字一格不本地推算
  <!-- aidcp-edge d128a10 ui-logic.slowStartCurveView（纯函数）+ renderer.renderSlowStartCurve。 -->
- [x] 4.3 缺席降级：回包无曲线时就地说明读不到，不显示任何数字，不回落上一次 / 内置 / 另一环境的曲线
  <!-- aidcp-edge d128a10 曲线随读 / 写后回执整体采用（回执不带即置 null）；占位、读失败、整行隐藏三处都清空表。 -->
- [x] 4.4 说明文案按权威总天数表述，删除写死的「7 天」
  <!-- aidcp-edge d128a10 ui-logic.slowStartCopyText；读不到曲线时不提天数而非编一个。 -->
- [x] 4.5 环境切换时曲线随环境隔离，晚到响应不得落到当前环境
  <!-- aidcp-edge d128a10 曲线存在既有的按 envKey 隔离缓存里，渲染入口按当前 context.envKey 现取，
       沿用该行既有的晚到丢弃逻辑，未新增第二套隔离。 -->

## 5. aidcp-edge — 测试

- [x] 5.1 单测：给定回包曲线 → 渲染行数与数字逐格一致；给定 10 天曲线 → 10 行
  <!-- aidcp-edge d128a10 ui-logic.test.ts（纯逻辑）+ renderer-smoke.test.ts（真渲染到 DOM）。 -->
- [x] 5.2 单测：回包无曲线 → 不出现任何数字且给出读不到的说明
  <!-- aidcp-edge d128a10 同上；另把两条既有结构断言改为守「页面结构里一个曲线数字都不留」。 -->
- [x] 5.3 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`
  <!-- 2026-08-05 acceptance 39/0、typecheck 0、全量 3143/1 —— 唯一红的是
       test/electron/interaction-workspace.test.ts「Cloud 离线局部刷新」，单跑 48/0 全绿 ⇒ 全量并发下的 flaky，
       与本 change 无关（该文件一行未碰，断言的是视频号收件箱文案）。 -->

## 6. 集成与部署

- [x] 6.1 两仓分别 rebase 到最新默认分支、合并、推送
  <!-- aidcp-cloud 6c165c6（scripts/land-change --yes）、aidcp-edge d128a10、aidcp-api c80beb4。 -->
- [x] 6.2 部署 dev（客户 API 由 api 进程承载，重启的必须是承载客户口的服务）
  <!-- 2026-08-05 12:03–12:08 dev 现役为派生三服务：备份 /opt/aidcp/api.bak.20260805-120644.tar.gz + .env.bak
       → rsync（排除 .git/node_modules/.env）→ ECS 上 tsc 0 → systemctl restart aidcp-api.service。
       **单体 aidcp-cloud.service 未动**（它已 stop+disable，起来会抢锁与 8787）。 -->
- [x] 6.3 dev 健康检查：服务在跑、客户口可达、数据库可读
  <!-- active、NRestarts=0、8090/8091 在听、飞书长连接已建立、日志无新错；automation/content 未受影响。
       慢启动读路由无 token 打回 401（不是 404）⇒ 路由在。 -->
- [x] 6.4 真机验收项登记进 backlog（客户端需出包才到运营机，本仓默认不打包）
  <!-- docs/real-machine-acceptance-backlog.md 簇 135（6 项）。**客户端侧未出包** ⇒ 运营机上仍是旧的写死表，
       本 change 的用户可见效果要等一次显式打包才到位（本仓默认不打包，属用户显式触发的动作）。 -->

## 7. 收口

- [x] 7.1 tasks.md 按 sub-repo 回写 commit sha 与偏离说明
- [x] 7.2 `openspec validate sync-slow-start-curve-to-client --strict` 通过
- [x] 7.3 归档 change，清理 worktree 与分支
  <!-- worktree/分支已由 scripts/land-change --yes 清理（cloud / edge 各一）。 -->
