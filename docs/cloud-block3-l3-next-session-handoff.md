# Block③ L3 读侧解耦 · 下一 session 交接（可直接执行）

> 生成于 2026-07-25，**2026-07-25 晚更新**（client-user-store 真纯读批已做完 + 部署 dev）。
> **给接手 session 用**：从头读到尾，按本文执行即可。
> 权威地图 = `docs/cloud-block3-l3-cutover-plan.md`；操作红线全景 = `docs/cloud-block3-db-split-handoff.md`。本文是「立刻能开工」的执行版，与那两份不冲突、只做浓缩 + 下一步落地。

---

## 0. 现状（接手先核对）

- **目标**：aidcp-cloud 从「一个共享库」拆成「三个属主库（content / automation / api）」，最终形态 = **三个真正独立的服务（各自进程、各自库、只走接口）**。
- **架构铁律（用户 2026-07-25 定，不可违反）**：**一个域绝不直连另一个域的数据库**。跨域读一律走「**拥有那张表的域**」的接口：接口定义在 kernel（`src/kernel/`），**属主域用它自己的连接池实现**，消费方只依赖接口、从不碰别人的库或表结构。同进程期 = 进程内直调属主实现（跑在属主池上）；拆进程后同一接口换 HTTP 客户端，消费方零改动。
  - ⚠️ **被撤过的取巧**：曾把别的域的连接池注入消费方、让消费方「在对的池上跑查询」。那物理上分了库，但消费方仍直连别人的库、仍知道别人的表结构 = 反模式，**已撤销**。不要重蹈。
- **代码位置**：cloud sub-repo 在 `../aidcp-cloud`（默认分支 `master`）。控制仓（本仓）在 `.`（默认分支 `main`）。**接手前先 `ls -d ../aidcp-cloud` 确认存在**。
- **当前提交指针**（接手时先 `git -C ../aidcp-cloud fetch && git -C ../aidcp-cloud rev-parse --short origin/master` 复核，fleet 活跃可能已推进）：
  - cloud `master` = **`7c2f6e3`**（面板批 + client-user 真纯读批 + 属主池补接 + cleanup-grant 收口，均已 land + 部署 dev）
  - 控制仓 `main` = 见 `git log`（本文档所在提交）
- **部署现状**：dev 已部署 `7c2f6e3`、healthcheck 绿。**dev 与 ol 连同一台物理 PG**（PG 在 dev 机 `121.89.85.150:5432`，这台 PG **就是生产库**）；当前 `AIDCP_PG_{API,AUTOMATION,CONTENT}_URL` **全未设** ⇒ 三个池都回落共享库 `aidcp` ⇒ **一切接口化改动此刻逐字节等价**（读的是同一份数据，只是换了取数通道）。
- **已完成的读侧解耦**（都经接口、都部署 dev）：
  1. **content 三处**（`5cbb6b1`）：curated `listForClient` 经 `TriggeredPublishRefsReader`、media `assertFacebookAccount` 经 `AccountPlatformReader`、draft `claimNext` 移除 vestigial 守卫。⇒ content 零跨库直读。
  2. **api 面板批 7 读**（`cf32544`）：`panel/panel-store.ts` 经新 kernel 端口 `PanelAutomationReader`、属主实现 `src/risk/panel-automation-read.ts`（跑 automation 池）。
  3. **api `client-user-store.ts` 真纯读批 6 读**（`6796488`）：新 kernel 端口 `ClientEnvAutomationReader`、属主实现 `src/interactions/client-env-automation-read.ts`（跑 automation 池，与同目录 `offboard-write-adapter` 读写配对）。改 `getOffboard` / `hasPendingRevocationHold` / `reconcileRevocationHolds` 候选扫描 / `listAllEnvironments`。**dev 真实数据新旧双跑 deep-equal 45==45 逐字段全等。**
  4. **互动域属主 store 补接属主池**（`92a2196` + 修 `7f5232a`）+ **cleanup-grant 一对收回属主域**（`7c2f6e3`）。
  ⇒ **api HUB raw 跨库读 26 → 19 → 13 → 12**；须监督读 8 → 7。

---

## 1. 复用配方（读侧解耦，已跑通三次：content + panel + client-user 纯读批）

**每处跨域读，照这七步做**：

1. **定接口（kernel）**：在 `src/kernel/<name>-types.ts` 加纯类型接口 + 返回行类型。
   - kernel 门禁硬约束：**零 SQL / 零 fetch / 零 LLM 标识符 / 无模块级 `new Set`/`new Map` / 无实现类名 / 无 setTimeout**。只放接口 + 类型别名。时间戳一律 epoch ms（`Date` 不过 HTTP）。
2. **属主域实现**：在属主域的某个文件里写实现类，**持有属主的连接池**（`automationPool` / `apiPool` / `contentPool`，都在 `src/server.ts` segA 构造、都在 ctx 上）。SQL 从消费方**逐字迁来**（保持聚合/过滤/排序/分页语义）。
   - 若属主的现成 store 是**条件构造**（`try/catch` 里、可能 undefined），**别依赖那个 store 对象**——直接用属主池新建一个专用只读实现类（panel 批就是这么做的：`PgPanelAutomationRead` 持 `automationPool`，不依赖 `alertStore`/`interactionFeedStore` 那些可能 undefined 的对象）。
3. **消费方改依赖接口**：消费方构造函数加一个**必填**的接口入参；把原来的跨库 SQL 换成调接口；**关联子查询 / 跨库 JOIN 拆成「本地读 + 接口取集合 + 本地判定/合入」**，保持原语义（如 LEFT JOIN 缺失 = null）。降级策略（如 `42P01` 缺表返空）留在消费方层。
4. **组合根接线（`src/server.ts`）**：按运行模式注入。
   - `mode`（`serviceModeFromEnv()`，默认 `monolith`）：`monolith`/`core` = 本地实现（跑属主池，逐字节等价）；`api` = **fail-closed**（各方法 reject 具名错误，如 `panel_automation_read_unavailable_in_api_mode`），镜像同文件 `publishStatusLocal` 的 api 模式 reject 先例。HTTP 客户端属 Block②（进程拆分）后续，**本刀不建**。
   - 属主池若不在目标段（segD）作用域，从 ctx 取（`apiPool` 已在 ctx；`automationPool` 已在 ctx）。segD 解构在 `src/server.ts` 那句超长 `const { ... } = ctx;`。
5. **边界门登记新 kernel 文件**（**这步会被 acceptance 门拦，必须做**）：
   - `boundaries/ownership-rules.json` 的 `fileOverrides` 加一条 `{ "path": "src/kernel/<name>-types.ts", "layer": "kernel", "basis": "…满足 §4.7 kernel 准入…" }`。
   - `boundaries/kernel-non-members.json` 的 `.kernelRoster.members[]` 加该文件路径（AC-BOUND-03 权威花名册）。
   - 属主实现文件若落在**单层目录**（如 `src/risk/` 全 automation，`newFile: inherit`），无需手工登记，`boundaries:refresh` 自动继承；若落在**逐文件裁决目录**（如 `src/cache/`）则需 fileOverride。
   - 跑 `npm run boundaries:refresh`（重生成 `module-ownership.json`）。**refresh 会顺手把 `table-write-exemptions.json` 的 `recordedAt` 日期改成今天——若只有日期变、frozenTotal/entries 未变，`git checkout` 回退它（纯噪声）**。
6. **测试**：消费方的单测注入接口桩（不再靠 pool 喂 automation 数据）；若 SQL 迁到了新实现类，把「SQL 形态断言」（如时区下界）搬到新实现类的测试。
7. **验证四连**（在 worktree 里）：`npm run typecheck` → `npm run test:acceptance`（边界门在这里）→ `npm test`（全量）。全绿再 land。

---

## 2. 立刻要做的下一批

`client-user-store.ts` 的**真纯读批已做完**（上面第 3 条）。下面按优先级列出接手 session 该做什么。

### 2A. 属主 store 补接属主池 —— **主体已完成，剩一处**

- ✅ 已做（`92a2196` + 修 `7f5232a` + 属主纠正 `b46708b`，部署 dev）：三个构造点绑各自**表的**属主池——
  `InteractionStore`→`automationPool`；**两个 reply-config store→`apiPool`**。
  ⚠️ **踩过的坑之一**：`92a2196` 曾按「它们都在 `src/interactions/` 目录」把三个一并绑成 automationPool，
  但那两个 reply-config store 的表**全是 api 属主** ⇒ 等于把同一个 split-brain 反向埋一遍。
  **目录位置不是属主判据，`boundaries/table-ownership.json` 才是**——补接属主池前逐表查一遍。
  **踩过的坑，接手务必知道**：这三个 store 的 `close()` 是 `pool.end()`，而互动域构造被 `try/catch` 包着、
  **失败分支正好会调它们** ⇒ 绑共享池后一次局部失败会 end 掉全域共用的池、升级成进程级瘫痪。
  已加 `ownsPool` 守卫（只 end 自己建的池）+ 回归用例。**给任何 store 补接属主池前，先查它的 `close()` 有没有调用方。**
- ✅ 也已做（`3f86c6c`）：`alerts` 写端并入 automation 池。**两处构造修法故意不同** —— 启动期 `raiseStandaloneAlert` 那处 `finally` 调 `close()`，故**仍自建专用小池**、只换配置来源；只有常规 `alertStore` 注入共享池（它的 close() 全仓无调用方）。
- ⛔ **剩这些**（完整表见 cutover-plan §1 callout c；**注意排查盲区**：`grep "new Pool(resolveEnvPgConfig())"` 只命中一种写法，另一种 `new Pool({host: ...DEFAULT_PG_CONFIG})` 绕过它，正确口径是枚举全部 `new Pool(` 与 `new Client(`）：~~`PgAlertStore`~~（`alerts`，automation 属主）仍走 HOST-param 自建池，且与已迁到 automation 池的
  读端（面板读 `alerts`）**已构成一对 split-brain**。它在 `server.ts` 有两处构造、性质不同：
  常规 `alertStore` 可直接注入属主池；启动期 `raiseStandaloneAlert` 那处 `finally` 里调 `store.close()`，
  **必须继续自建池**，只应把配置来源从 HOST-param 换成 `resolveOwnerPgConfig('automation')`。
  ⚠️ 它是 HOST-param 形态 ⇒ 接池后会开始认 `DATABASE_URL`；dev/ol 均未设（L2 已 SSH 核实），但动前建议再核一次。
- 🚫 **不要动** `PgRiskStore` / `PgRiskCounterOutboxStore` / **`AutomationWriterLock`**：同样漏接，但 `src/risk/`
  属活跃 change `risk-state-cross-process-integrity`（§7 热点单写者）独占范围。待其归档后另起一刀。
  其中 `AutomationWriterLock` 是**最严重**的一项：advisory lock 按库，翻转后锁留旧库 / 写落新库 ⇒
  两进程各自「抢到同一把锁」却互不排斥 = **静默双写 `risk_state`**。且它 **MUST NOT 注入池**
  （会话级锁，池回收连接即释放），只应让连接配置跟随 `resolveOwnerPgConfig('automation')`。
- 另有 `runSchemaContractGate` 的账本 Client（`schema_migrations` 属 automation）翻转后会**假绿**；
  但「账本是一份还是每库一份」本身是未裁决的设计题，动它前先定。

### 2B.（须用户在场）`client-user-store.ts` 余下 7 处 + 跨库事务批

逐处清单（行号 + 表 + 方法 + 锁）见 `docs/cloud-block3-l3-cutover-plan.md` **§2.1 表格**。核心认识：

- 这 8 处**不是「更难的同类」，是性质不同的一类**：跨库行锁与本项目已经淘汰过一次的库级 advisory lock 同形——**两侧连不同库时两边各自加锁都会成功、互斥消失、且不产生任何错误**（同一教训写在 `src/db/environment-row-lock.ts` 头注释）。所以「先 HTTP 化再说」对它们是错的方向。
- §2.1 已经写清三个**改之前必须先答的题**：`setScope` 两道闸分居两库叠加 reconcile 两次提交 ⇒ 有把「正在清理的环境改派给新客户」的窗口；`OffboardWritePort` **接调用方事务句柄**、实现方自己不持连接 ⇒ 翻转后离场写全打到 api 库（要么 42P01 直接 500、要么写进副本变静默假成功）；`getOffboard` 的 404 语义在离场写变成独立提交后需要一个「已受理未物化」的中间态。
- **不要在用户不在场时动这批。**

### 2C. automation → api 的 accounts 守卫读

见 cutover-plan §2 automation 段。多在写事务内，需去规范化（把 accounts 的 platform/group_label/execution_target 投影冷备进 automation 库）或移守卫。

## 3. 操作命令（照抄）

### 起 worktree（不在 canonical master 上开发）
```bash
# 先自检 canonical 都在默认分支
git -C /Users/baitianxing/codes/aidcp     branch --show-current   # 须 = main
git -C /Users/baitianxing/codes/aidcp-cloud branch --show-current  # 须 = master

cd /Users/baitianxing/codes/aidcp-cloud
git worktree add ../aidcp-cloud.wt/block3-l3-<下一批名> -b block3-l3-<下一批名> master
cd ../aidcp-cloud.wt/block3-l3-<下一批名>
npm ci    # 每个 worktree 各自装,绝不软链 node_modules
```

### 验证四连（worktree 内）
```bash
npm run typecheck
npm run test:acceptance          # 含边界门 AC-BOUND-*/AC-OWN-*；改 kernel 文件后必跑
npm test                         # 全量（约 60s，3195+ 用例）
npm run boundaries:refresh       # 加了新 kernel 文件后跑；再 git diff 检查 table-write-exemptions 只是日期就回退
```

### land + 部署 dev（从 canonical，不从 worktree 部署）
```bash
# 1) 在 worktree 提交后，回 canonical master ff-merge
cd /Users/baitianxing/codes/aidcp-cloud
git fetch origin
git rev-list --left-right --count origin/master...block3-l3-<下一批名>   # 左=0 才可直接 ff；非 0 先 rebase worktree 分支再重验四连
git merge --ff-only block3-l3-<下一批名>
git push origin master

# 2) 部署 dev（安全序列：clean 快照 → ECS 备份 → rsync → 重启 → healthcheck）
bash /Users/baitianxing/codes/aidcp/scripts/deploy-target dev --check   # key=~/codes/dev-0722.pem host=121.89.85.150 dir=/opt/aidcp/cloud
#   a. git archive HEAD → 干净 staging 目录（保证只含已提交内容）
#   b. ssh 到 ECS：cd /opt/aidcp && tar --exclude cloud/node_modules --exclude cloud/.git -czf cloud.bak.<ts>.tar.gz cloud && cp cloud/.env cloud/.env.bak.<ts>
#      （注意 ECS 是 GNU tar，--exclude 必须放在目录参数之前）
#   c. rsync -az --exclude '.env' --exclude 'node_modules' --exclude '.git' <staging>/ root@121.89.85.150:/opt/aidcp/cloud/   （不带 --delete）
#   d. ssh：systemctl restart aidcp-cloud.service
#   e. healthcheck：systemctl is-active + ss -ltnp 8787 + journalctl 近 70s 无 error + 各 store 就绪 + 飞书 onReady + sudo -u postgres psql -tAc 'select 1' aidcp
#      失败即回滚（解压 cloud.bak.<ts>.tar.gz + 重启）
```
> 依赖无新增时（本 change 不加 npm 包）**不用在 ECS 跑 npm install**，node_modules 原样。部署 = 源码 rsync，运行 `npx tsx src/server.ts`（无 build 步）。

### 收尾
```bash
cd /Users/baitianxing/codes/aidcp-cloud
git worktree remove ../aidcp-cloud.wt/block3-l3-<下一批名>
git branch -d block3-l3-<下一批名>
# 更新 docs/cloud-block3-l3-cutover-plan.md + docs/cloud-block3-db-split-handoff.md §0 + memory cloud-decoupling-execution-progress
# 控制仓 commit+push（main）
```

---

## 4. 红线（不可违反）

1. **域间只走接口**，绝不把别的域的池注入消费方（被撤过的取巧）。
2. **绝不碰同机 `isales`**（ECS 上另有独立 systemd 服务 / 目录 / 端口）。
3. **文档/提交/tasks.md 不写任何密码 / token / 私钥内容**，只记路径、服务位置、命令、读取方式。
4. **不静默假成功**：跨库读拿不到就 fail-closed 或如实降级，绝不返回伪造的空/成功。
5. **跨库事务 / 跨库写 / 加锁读**（第 2 节 (B) 类）**须用户在场**做最终一致重设计——不在用户不在时盲改环境注销关键路径。
6. **部署只从 canonical master 的 clean 快照走**（`git archive HEAD`），绝不从脏工作区或 worktree 直接 rsync。dev 默认可自动部署；**ol 只有用户明确要求 + 从 release 分支**。
7. **canonical 目录永远停默认分支**（aidcp=main，cloud=master），要分支隔离就开 worktree；worktree 的 node_modules **各自 `npm ci`、绝不软链**。

---

## 5. 一段话给用户的收尾口径（做完后）

用非技术语言讲：这次把「后台某某功能」以前直接读别的系统的数据库、改成了敲接口向那个系统要数据；线上没有任何变化（还是同一个库、同一份数据，只是取数方式变干净了）；哪些做完了、哪些因为涉及注销关键路径留给你在场时一起做。技术细节照给，但收尾那段要让非工程视角也看得懂。
