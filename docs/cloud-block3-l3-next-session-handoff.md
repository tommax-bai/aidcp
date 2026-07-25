# Block③ L3 读侧解耦 · 下一 session 交接（可直接执行）

> 生成于 2026-07-25。**给接手 session 用**：从头读到尾，按本文执行即可。
> 权威地图 = `docs/cloud-block3-l3-cutover-plan.md`；操作红线全景 = `docs/cloud-block3-db-split-handoff.md`。本文是「立刻能开工」的执行版，与那两份不冲突、只做浓缩 + 下一步落地。

---

## 0. 现状（接手先核对）

- **目标**：aidcp-cloud 从「一个共享库」拆成「三个属主库（content / automation / api）」，最终形态 = **三个真正独立的服务（各自进程、各自库、只走接口）**。
- **架构铁律（用户 2026-07-25 定，不可违反）**：**一个域绝不直连另一个域的数据库**。跨域读一律走「**拥有那张表的域**」的接口：接口定义在 kernel（`src/kernel/`），**属主域用它自己的连接池实现**，消费方只依赖接口、从不碰别人的库或表结构。同进程期 = 进程内直调属主实现（跑在属主池上）；拆进程后同一接口换 HTTP 客户端，消费方零改动。
  - ⚠️ **被撤过的取巧**：曾把别的域的连接池注入消费方、让消费方「在对的池上跑查询」。那物理上分了库，但消费方仍直连别人的库、仍知道别人的表结构 = 反模式，**已撤销**。不要重蹈。
- **代码位置**：cloud sub-repo 在 `../aidcp-cloud`（默认分支 `master`）。控制仓（本仓）在 `.`（默认分支 `main`）。**接手前先 `ls -d ../aidcp-cloud` 确认存在**。
- **当前提交指针**（接手时先 `git -C ../aidcp-cloud fetch && git -C ../aidcp-cloud rev-parse --short origin/master` 复核，fleet 活跃可能已推进）：
  - cloud `master` = **`cf32544`**（面板批已 land）
  - 控制仓 `main` = **`36734a2`**（文档已更新）
- **部署现状**：dev 已部署 `cf32544`、healthcheck 绿。**dev 与 ol 连同一台物理 PG**（PG 在 dev 机 `121.89.85.150:5432`，这台 PG **就是生产库**）；当前 `AIDCP_PG_{API,AUTOMATION,CONTENT}_URL` **全未设** ⇒ 三个池都回落共享库 `aidcp` ⇒ **一切接口化改动此刻逐字节等价**（读的是同一份数据，只是换了取数通道）。
- **已完成的读侧解耦**（都经接口、都部署 dev）：
  1. **content 三处**（`5cbb6b1`）：curated `listForClient` 经 `TriggeredPublishRefsReader`、media `assertFacebookAccount` 经 `AccountPlatformReader`、draft `claimNext` 移除 vestigial 守卫。⇒ content 零跨库直读。
  2. **api 面板批 7 读**（`cf32544`）：`panel/panel-store.ts` 经新 kernel 端口 `PanelAutomationReader`、属主实现 `src/risk/panel-automation-read.ts`（跑 automation 池）。⇒ api HUB raw 跨库读 **26→19**。

---

## 1. 复用配方（读侧解耦，已跑通两次：content + panel）

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

## 2. 立刻要做的下一批：api `client-user-store.ts` 的读

**位置**：`src/client-auth/client-user-store.ts`（api 属主；微信环境 offboard/scope 生命周期）。计划 §2 记为「14 处 raw 读 automation 表」。

**⚠️ 关键真相（接手前必须知道，2026-07-25 实测）**：这个文件**不是干净的只读批**。实测：
- **23 处 `FOR UPDATE`/`FOR SHARE`**（跨库行锁，在事务内——**接口化解决不了锁语义**）
- **24 个 `BEGIN`/`COMMIT`**（含 5 处 offboard「一笔事务横跨 api+automation 两库」的联合提交）
- **88 处 `client.query`（事务内） vs 26 处 `this.pool.query`（顶层）** ⇒ 绝大多数读夹在事务里
- 读的 automation 表：`risk_state` / `interaction_auth_state` / `interaction_offboards` / `interaction_runtime_controls`（15 处引用）

**所以这批分两类，必须分开处理**：

- **(A) 真·纯只读**（顶层 `this.pool.query`、非 `FOR UPDATE`、不在 `BEGIN/COMMIT` 内、且不与 api 表同查询 JOIN）：**可按第 1 节配方干净解耦**。这是本批**能自主做**的部分。
  - 其中若有 **api+automation 同查询 JOIN**（计划点名 `1359/2210/2225/2254` 一带，行号 fleet 活跃会漂、动前 grep 复核），拆成「本地查 api + 接口取 automation 集 + 本地合入」，**属行为变更、必须有测试覆盖**。
- **(B) 加锁读 + 联合提交事务**（`FOR UPDATE`/`FOR SHARE` 跨库锁、5 处 offboard 跨库 co-commit）：**这是环境注销关键路径，计划标「须监督」**。跨库锁和跨库事务原子性**接口化解决不了**，要改成最终一致（outbox / 2-phase）并接受语义变化。**不要在用户不在场时盲改**——注销做错会误删/漏删客户环境。**登记进 backlog、留给"用户在场"那一档。**

**执行决策门**：
1. 先通读 `client-user-store.ts`，把 14 处 automation 读逐个归入 (A) 或 (B)（带 `file:line` + 是否在事务/是否 `FOR UPDATE`/是否 JOIN api 表）。
2. **只做 (A)**：按第 1 节配方，属主（automation）加读端口、client-user-store 依赖接口。
3. **(B) 全部登记**到 `docs/cloud-block3-l3-cutover-plan.md` 的「9 处跨库事务 + 1 处跨库写」批 + `docs/real-machine-acceptance-backlog.md`，写清 `file:line` 与「须用户在场做最终一致重设计」的原因。**绝不静默跳过、也绝不盲改。**
4. 若通读后发现 (A) 子集**很小或与 (B) 无法干净切分**（很可能），**如实报告并停在 panel 批那个干净节点**，把整个 client-user-store 批连同 automation→api 守卫读一起归到「须监督」档——这也是一个正当的收尾。

**这批之后**（同属「须监督 / 近事务」，非本次自主范围）：
- automation → api 的 `accounts` 守卫读（`pg-risk-store` / `interaction-store` / `facebook-group-store` / `delegated-task/store` 里 `execution_target` 内联、`EXISTS(accounts)`、`FOR SHARE` 行锁）——多在写事务内，需**去规范化**（把 accounts 的 platform/group_label/execution_target 投影冷备进 automation 库）或移守卫。
- 9 处跨库事务（4 config-mirror `writeWithMirrorBump` + 5 offboard co-commit）+ 1 处跨库写（`interaction-store` 双写 api 的 `interaction_audit_events`）→ 架构级最终一致，**须用户在场**。

---

## 3. 操作命令（照抄）

### 起 worktree（不在 canonical master 上开发）
```bash
# 先自检 canonical 都在默认分支
git -C /Users/baitianxing/codes/aidcp     branch --show-current   # 须 = main
git -C /Users/baitianxing/codes/aidcp-cloud branch --show-current  # 须 = master

cd /Users/baitianxing/codes/aidcp-cloud
git worktree add ../aidcp-cloud.wt/block3-l3-client-user-read-port -b block3-l3-client-user-read-port master
cd ../aidcp-cloud.wt/block3-l3-client-user-read-port
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
git rev-list --left-right --count origin/master...block3-l3-client-user-read-port   # 左=0 才可直接 ff；非 0 先 rebase worktree 分支再重验四连
git merge --ff-only block3-l3-client-user-read-port
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
git worktree remove ../aidcp-cloud.wt/block3-l3-client-user-read-port
git branch -d block3-l3-client-user-read-port
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
