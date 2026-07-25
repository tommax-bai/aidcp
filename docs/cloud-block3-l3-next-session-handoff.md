# Block③ L3 · 下一 session 交接（可直接粘贴）

> 更新于 2026-07-25 晚。**给接手 session 用：从头读到尾，按本文执行即可。**
> 权威地图 = `docs/cloud-block3-l3-cutover-plan.md`（**剩余工作全量清单在它的 §2.2**）。
> 操作红线全景 = `docs/cloud-block3-db-split-handoff.md`。Redis 决策 = `docs/redis-decision-cross-db-locks-and-async-bus.md`。
> 本文是「立刻能开工」的执行版。

---

## 0. 起手三件事（先做，别跳）

```bash
# ① 四个 canonical 必须都停在默认分支（aidcp=main，edge/cloud/console=master）
bash scripts/task-preflight          # 只读、不自愈；exit 1 就先把漂移的仓还原/挪进 worktree

# ② 复核提交指针（fleet 活跃，正文里的 sha 可能已滞后）
git -C . rev-parse --short HEAD                                   # 控制仓，本文写就时 = 59ae620
git -C ../aidcp-cloud fetch origin -q && git -C ../aidcp-cloud rev-parse --short origin/master   # 本文写就时 = 3f86c6c

# ③ sub-repo 必须存在于本机
ls -d ../aidcp-cloud
```

---

## 1. 现状（30 秒读完）

**目标**：aidcp-cloud 从「一个共享库」拆成三个属主库（content / automation / api），终态 = **三个真正独立的服务**（各自进程、各自库、只走接口）。

**架构铁律（不可违反）**：**一个域绝不直连另一个域的数据库。** 跨域读一律走「拥有那张表的域」的接口——接口定义在 `src/kernel/`，**属主域用它自己的连接池实现**，消费方只依赖接口。同进程期 = 进程内直调属主实现；拆进程后同一接口换 HTTP 客户端，消费方零改动。
> ⚠️ **被撤过的取巧**：曾把别的域的连接池注入消费方、让它「在对的池上跑查询」。那物理上分了库，但消费方仍直连别人的库、仍知道别人的表结构 = 反模式，**已撤销**。不要重蹈。

**当前安全垫**：三个 `AIDCP_PG_{API,AUTOMATION,CONTENT}_URL` **全未设** ⇒ 三个池回落到同一个共享库 ⇒ **一切接口化 / 换池改动此刻逐字节等价**。dev 已部署 `3f86c6c`、healthcheck 绿。
⚠️ **dev 与 ol 连同一台物理 PG**（在 dev 机 `121.89.85.150:5432`），**那台就是生产库**。

**已完成**（都经接口、都部署 dev）：

| 批 | sha | 内容 |
|---|---|---|
| step0 | `f8651f0` | outbox helper 池改绑 automation |
| content 3 读 | `5cbb6b1` | content 零跨库直连（dev 真实数据等价 31==31） |
| 面板 7 读 | `cf32544` | 新 kernel 端口 `PanelAutomationReader` |
| client-user 真纯读 6 | `6796488` | 新端口 `ClientEnvAutomationReader`；**dev 真实数据 45==45 逐字段全等** |
| 属主池补接 | `92a2196` + 修 `7f5232a` + 纠正 `b46708b` | 互动域三 store 绑各自**表的**属主池 |
| cleanup-grant 收口 | `7c2f6e3` | 「假跨域」一对整体搬回属主域，自开事务 |
| alerts 写端 | `3f86c6c` | 并入 automation 池，消掉读/写分池 |

⇒ **api HUB raw 跨库读 26 → 12；须监督读 8 → 7。**

---

## 2. 下一步做什么

**去读 `docs/cloud-block3-l3-cutover-plan.md` §2.2「剩余工作全量清单」**——那里按 A/B/C/D/E/F 六档排好了，每条都标了阻塞源。这里只给最短版：

- **A 档（今天可做、无阻塞）**：面板事件 tee 的三个生产隐患（**启用非单体模式当天就咬人**）、`core` 模式生成传输超时未接线（**是拆内容域那一步的硬阻断**）、接 `LISTEN` 唤醒 + 游标加 topic 维、让真库集成测试能跑（**必须带守卫**）、加行锁的机械门禁、面板事件信封补原始时间戳。
- **B 档（被 change `risk-state-cross-process-integrity` 挡住，别并行动）**：风控三处补接属主池，含**最严重的那把自动化写者锁**。
- **C 档（须先裁决设计）**：迁移账本形态、传输层形态、切换策略。
- **D 档（须用户在场）**：余 7 处跨库行锁、**反方向的跨属主互斥**、9 处跨库事务 + 1 处跨库写、外键降级 / 建库 / 拷数据 / 翻 URL。
- **E 档（硬期限 2026-08-14）**：离场清理的盲删第一次有机会咬人。

**建议顺序**：A2（`core` 生成超时，硬阻断）→ A4+A5（先接通验证装置再动语义）→ A1+A6（生产隐患）→ A3（吃掉 broker 卖点）。**B/D 不要抢跑。**

---

## 3. 复用配方（读侧解耦，已跑通四次）

**每处跨域读，照这七步做**：

1. **定接口（kernel）**：`src/kernel/<name>-types.ts`，纯类型接口 + 返回行类型。
   门禁硬约束：**零 SQL / 零 fetch / 零 LLM 标识符 / 无模块级 `new Set`·`new Map` / 无实现类名 / 无 setTimeout**。时间戳一律 epoch ms（`Date` 不过 HTTP）。
2. **属主域实现**：在属主域文件里写实现类，**持有属主的连接池**（`apiPool` / `automationPool` / `contentPool`，都在 `src/server.ts` segA 构造、都在 ctx 上）。SQL 从消费方**逐字迁来**。
   - 若属主现成 store 是**条件构造**（`try/catch` 里、可能 undefined），**别依赖那个对象**——直接用属主池新建专用只读实现类。
3. **消费方改依赖接口**：构造函数加接口入参；关联子查询 / 跨库 JOIN 拆成「本地读 + 接口取集合 + 本地判定合入」，保持原语义（LEFT JOIN 缺失 = null）。降级策略（缺表返空）留在消费方层。
4. **组合根接线**（`src/server.ts`）：按 `serviceModeFromEnv()` 注入。`monolith`/`core`/`automation`/`content` = 本地实现（逐字节等价）；`api` = **fail-closed**（各方法 reject 具名错误）。
5. **边界门登记新 kernel 文件**（**这步会被 acceptance 门拦，必须做**）：
   - `boundaries/ownership-rules.json` 的 `fileOverrides` 加一条；
   - `boundaries/kernel-non-members.json` 的 `.kernelRoster.members[]` 加该文件；
   - 属主实现文件若落在**逐文件裁决目录**（如 `src/interactions/`、`src/cache/`）**也要**加 fileOverride；落在单层目录（如 `src/risk/`）自动继承。
   - 跑 `npm run boundaries:refresh`。**它会顺手把 `table-write-exemptions.json` 的 `recordedAt` 改成今天——若只有日期变，`git checkout` 回退它（纯噪声）。**
   - ⚠️ **改这两个 JSON 用文本追加，别用 `json.dump` 重写**——会把整个文件重排、diff 炸到几百行。
6. **测试**：消费方单测注入接口桩；SQL 形态断言搬到新实现类的测试。
7. **验证四连**（worktree 内）：`npm run typecheck` → `npm run test:acceptance` → `npm test`。全绿再 land。

---

## 4. 五条踩过的坑（血泪，务必先看）

1. **目录位置不是属主判据，`boundaries/table-ownership.json` 才是。**
   `92a2196` 曾按「都在 `src/interactions/` 目录」把三个 store 一并绑 `automationPool`，但其中两个（回复配置）的表**全是 api 属主** ⇒ 等于把同一个 split-brain **反向**埋一遍。补接属主池前**逐表查一遍**。

2. **给 store 补接共享属主池前，先查它的 `close()` 有没有调用方。**
   `close()` 通常是 `this.pool.end()`。互动域构造被 `try/catch` 包着（schema/迁移未就位时整域降级），**失败分支正好会调这三个 `close()`** ⇒ 绑共享池后一次**局部**失败会 end 掉全域共用的池、升级成**进程级瘫痪**。修法 = `ownsPool = options.pool === undefined`，`close()` 只 end 自己建的池。**同类形态在别处仍存在**（多数注入属主池的 store 的 close() 亦会 end 共享池，只是当前无人调用）。

3. **排查自建池的 grep 有盲区。**
   `grep "new Pool(resolveEnvPgConfig())"` **只命中一种写法**；`new Pool({ host: options.host ?? DEFAULT_PG_CONFIG.host, ... })` 完全绕过它。正确口径 = **枚举全部 `new Pool(` 与 `new Client(`**，再逐个看组合根有没有注入。第一版漏接名单就是这么漏了四项的。

4. **`AutomationWriterLock` 的修法处方曾是错的，别照抄旧文档。**
   「让连接配置跟随 `resolveOwnerPgConfig('automation')`」会**引入 bug**：它的连接配置结构没有连接串字段，而 owner resolver 在 URL 已设时返回的正是连接串 ⇒ 五个字段全空 → 回落内置默认（本机 + 明文口令兜底）⇒ **在错的库上取锁而且会成功**。正确修法见 cutover-plan §1 callout c 的更正块。

5. **「等价」要有机械依据，不要靠眼看。**
   拆 JOIN 之所以敢说逐字等价，是因为**表上有唯一索引 / 主键保证那些 JOIN 是 1:1**（不放大行数、不改 LIMIT 选中集）。没有这种依据时，要么别拆，要么在 dev 上**新旧双跑做 deep-equal**（本批做过两次：31==31、45==45 逐字段全等）。

---

## 5. 操作命令（照抄）

### 起 worktree（**绝不在 canonical 上开发**）
```bash
bash scripts/task-preflight       # 必须先过
cd /Users/baitianxing/codes/aidcp-cloud
git worktree add ../aidcp-cloud.wt/<change-name> -b <change-name> master
cd ../aidcp-cloud.wt/<change-name>
npm ci                            # 每个 worktree 各自装；**node_modules 绝不软链**（会被 git add -A 提交进仓）
```

### 验证四连
```bash
npm run typecheck
npm run test:acceptance           # 边界门 AC-BOUND-* / AC-OWN-* / AC-LOCK-* 在这里
npm test                          # 全量（约 60s；本文写就时 3210 pass / 0 fail / 10 skip）
npm run boundaries:refresh        # 加了新 kernel 文件后跑；再 git diff 检查 table-write-exemptions 只是日期就回退
```

### land + 部署 dev（**只从 canonical 的 clean 快照，绝不从 worktree**）
```bash
cd /Users/baitianxing/codes/aidcp-cloud
git fetch origin
git rev-list --left-right --count origin/master...<change-name>   # 左=0 才可 ff；非 0 先 rebase 再重验四连
git merge --ff-only <change-name>
git push origin master

bash /Users/baitianxing/codes/aidcp/scripts/deploy-target dev --check
#  a. git archive HEAD | tar -x -C <staging>            ← 保证只含已提交内容
#  b. ssh：cd /opt/aidcp && tar --exclude cloud/node_modules --exclude cloud/.git \
#          -czf cloud.bak.<ts>.tar.gz cloud && cp cloud/.env cloud/.env.bak.<ts>
#          （ECS 是 GNU tar：--exclude 必须放在目录参数之前）
#  c. rsync -az --exclude '.env' --exclude 'node_modules' --exclude '.git' <staging>/ \
#          root@121.89.85.150:/opt/aidcp/cloud/            ← 不带 --delete
#  d. ssh：systemctl restart aidcp-cloud.service
#  e. healthcheck：is-active + 8787/8090 监听 + journalctl 近 80s 无 error
#                  + 各 store 就绪行 + sudo -u postgres psql -tAc 'select 1' aidcp
#     失败即回滚（解压 cloud.bak.<ts>.tar.gz + 重启）
```
> 本 change 不加 npm 包时**不用在 ECS 跑 npm install**。部署 = 源码 rsync，运行 `npx tsx src/server.ts`（**无 build 步**）。

### 收尾
```bash
cd /Users/baitianxing/codes/aidcp-cloud
git worktree remove ../aidcp-cloud.wt/<change-name> && git branch -d <change-name>
# 回写：cloud-block3-l3-cutover-plan.md（§2.2 清单 + §1 矩阵）、cloud-block3-db-split-handoff.md §0、本文
# 真机验收项 → docs/real-machine-acceptance-backlog.md（本批新增簇 112）
# 控制仓 commit + push（main）
```

---

## 6. 红线（不可违反）

1. **域间只走接口**，绝不把别的域的池注入消费方。
2. **绝不碰同机 `isales`**（独立 systemd / 目录 / 端口；**它还占着 dev 的 6379 与 `redis.service` unit 名**）。
3. **文档 / 提交 / tasks.md 不写任何密码 / token / 私钥内容**，只记路径、服务位置、命令、读取方式。
4. **不静默假成功**：跨库读拿不到就 fail-closed 或如实降级。特别注意**失败方向**——若某方法的 `false` 是「放行」的意思，那它 MUST NOT 把读失败吞成 `false`。
5. **跨库事务 / 跨库写 / 加锁读**（D 档）**须用户在场**做最终一致重设计。
6. **部署只从 canonical master 的 clean 快照走**（`git archive HEAD`）。dev 默认可自动部署；**ol 只有用户明确要求 + 从 release 分支**。
7. **canonical 目录永远停默认分支**；worktree 的 node_modules **各自 `npm ci`、绝不软链**。
8. **不引入 Redis**（决策已定，见 `docs/redis-decision-cross-db-locks-and-async-bus.md`；重开话题的可判定触发条件在它的 §5）。

---

## 7. 收尾时给用户的口径

用非技术语言讲：这次把「某某功能」以前直接读别的系统的数据库、改成了敲接口向那个系统要数据；线上没有任何变化（还是同一个库、同一份数据，只是取数方式变干净了）；哪些做完了、哪些因为涉及关键路径留给你在场时一起做。技术细节照给，但收尾那段要让非工程视角也看得懂。
