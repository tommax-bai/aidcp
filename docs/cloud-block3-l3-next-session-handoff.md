# Block③ L3 · 下一 session 交接（可直接粘贴）

> 更新于 **2026-07-25 深夜**（离线维护窗口，用户全权授权）。**给接手 session 用：从头读到尾，按本文执行即可。**
> 权威地图 = `docs/cloud-block3-l3-cutover-plan.md`。操作红线全景 = `docs/cloud-block3-db-split-handoff.md`。
> Redis 决策 = `docs/redis-decision-cross-db-locks-and-async-bus.md`（结论：**不引入**，且它的两个前置先手已落地，见下）。

---

## 0. 起手三件事（先做，别跳）

```bash
bash scripts/task-preflight                                       # 四个 canonical 必须都停默认分支
git -C . rev-parse --short HEAD                                   # 控制仓
git -C ../aidcp-cloud fetch origin -q && git -C ../aidcp-cloud rev-parse --short origin/master   # 本文写就时 = 7b316ce
ls -d ../aidcp-cloud
```

---

## 1. 现状：**代码侧的拆库前置工作已全部完成**

**目标**：aidcp-cloud 从「一个共享库」拆成三个属主库（content / automation / api），终态 = 三个真正独立的服务。

**架构铁律（不可违反）**：**一个域绝不直连另一个域的数据库。** 跨域读一律走「拥有那张表的域」的接口——接口定义在 `src/kernel/`，**属主域用它自己的连接池实现**，消费方只依赖接口。

### 两道机械门禁现在都读到零

```
AC-LOCK  crossOwnerSites: 0   crossOwnerKeys: 0   exemptions: 0   frozenTotal: 0   （原 10 处 / 7 键）
AC-OWN   crossLayerWrites: 0  dmlViolations: 0    ddlViolations: 0  exemptions: 0   （原 1 处）
```

**全仓跨属主行锁归零、跨属主写归零、跨库联合提交归零。** 这不是人工盘点的结论，是两条扫描器每次 `npm run test:acceptance` 都会重算的机械事实，且**豁免清单只减不增**——有人写回一处新的跨属主行锁/写，门禁当场红。

### 本批落地清单（13 个提交，全部 land + 部署 dev + healthcheck 绿）

| 提交 | 内容 | 关键点 |
|---|---|---|
| `72d61b9` | **A2** `core` 模式生成传输超时接线（15s→180s） | 拆内容域的硬阻断；顺带把未捕获的 reject 收敛成诚实失败终态 |
| `c88c76c` | **拆库运维工具**：逐属主拷数据 + 只读等价校验 + AC-SPLIT-01 防漂移门禁 | 源库全程只读；目标库硬白名单；前置不满足即拒绝执行 |
| `835ab13` | **B1+B2** 风控两 store 接 automation 池 + 写者锁换连接来源 | 写者锁**加了连接串支持再换来源**（照旧处方会在错的库上取到锁且成功） |
| `f02c9ee` | **E1** 离场清理盲删修正 | 6 个真缺陷，全部**收窄**方向；见 §3 |
| `cc17eb0` | **A1+A6** 面板事件 tee 三隐患 + 信封原始时间戳 | 模式感知闸 / 帧上限 / outbox 保留期剪裁 |
| `edb8cbd` | **A4+A5** 真库集成测试通道（三重守卫）+ 行锁机械门禁 | 顺带堵掉「ECS 上跑 `npm test` 会打生产库」的活坑 |
| `25c0d28` | **A3** `LISTEN`/`NOTIFY` 唤醒 + 消费游标加 topic 维 | Redis 决策的两个前置先手，至此**都已用掉** |
| `f3452eb` | **content→api 跨属主外键降级 + AC-SPLIT-02 门禁** | 每条降掉的外键都写清了「等价守卫在哪」 |
| `4a91bd4` | **D3a** 4 个配置镜像跨库事务 → 最终一致（本域 outbox + 中继） | 不一致窗口上界 ≈ 8s；同刀把「门禁天然失明」的那处做成了机械断言 |
| `f1e20d2` | **C1** 迁移账本改**每库一份** + schema gate 假绿修掉 | 启动日志现在给出三个独立结论 |
| `cdb1e4d` | **D4a** api 属主 `accounts` 去规范化进 automation 侧守卫投影 | 陈旧/缺行一律 fail-closed；空快照不许冒充新鲜 |
| `09f81d1` | **D2+D3c** 反方向跨属主互斥收口进 api 窄网关 + 审计写走 outbox | 网关调用**必须在 BEGIN 之前**（否则构成 PG 检测不到的跨库死锁环），有回归用例钉住 |
| `7b316ce` | **D1+D3b** 离场生命周期最终一致化 | 5 处跨库联合提交消失，`OffboardWritePort` 整个文件删除 |

**测试基线**：typecheck 0 / acceptance **115 pass 0 fail** / 全量 **3312 pass 0 fail 10 skip**（10 skip = 真库集成测试，常规 `npm test` 下按设计跳过）。

### dev 上已完成的库侧动作

1. **三个空属主库已建**（`aidcp_content` / `aidcp_automation` / `aidcp_api`，`scripts/db-split/0075`）。零影响：owner URL 全未设，无人连。
2. **整库备份**：`/opt/aidcp/pgbackup/aidcp-pre-l3-20260725.dump`（`pg_dump -Fc`，2.9 MB）。
3. **15 条跨属主外键已降**（`scripts/db-split/0076`，全部 `DROP CONSTRAINT IF EXISTS`，幂等可逆，附重建语句）。库内外键 40 → 25。
4. **迁移 0075–0078 已应用**，账本 77 行、校验和全一致。
5. **拷数据前置自检已全绿**：`0077 --check` 三个属主全部 ready。

**真实数据验证**（不是桩，是 dev 生产库）：
- 属主映射**零漂移**——库里 98 张表，属主表 98 条，一一对应；
- 账号守卫投影首刷 **37 个账号**，与 `accounts` 行数逐字吻合；
- 离场准入的**存量认领**按设计生效——4 条终态离场台账全部在 api 域补出了准入行并正确标为已物化。**这就是拆库当天回填路径的真实验证**。

---

## 1.5 翻转当天暴露的问题与修法

**这一节是本次最有价值的产出**：下面每一条都只在「真的把 URL 指过去」那一刻才现形，
前置自检（`0077 --check`）一条都看不见。将来任何环境再做同样的切换都会撞上它们。

**三个运维缺陷**：

1. **`pg_hba.conf` 按库名授权。** 老库有 `host aidcp aidcp <addr> scram-sha-256` 两条（dev 一条、ol 一条），
   三个新库名没有条目 ⇒ 落到通用 `host all all 127.0.0.1/32 ident` ⇒ **`Ident authentication failed`**，
   服务起来了但端口一个都不监听。修法 = 追加两条同形规则（库名列表用逗号）+ `pg_reload_conf()`。
   **isales 那条一字未动。** 规则已生效，dev 与 ol 两个地址都覆盖了。
2. **`DROP SCHEMA public CASCADE; CREATE SCHEMA public;` 丢掉了 schema 授权。** 新建的 `public` 归 `postgres`、
   ACL 为空，应用角色 USAGE/CREATE 全 false。**后果极具误导性**：没有 USAGE 权限时，明明存在的表报的是
   **`relation "xxx" does not exist`** —— 一路把人往「拷贝漏了表」上带，而实际是权限。
   修法 = `GRANT USAGE, CREATE ON SCHEMA public TO PUBLIC`（与源库 ACL 逐字一致，不是放宽）。
3. **`pg_dump --table` 不带触发器函数。** 恢复会一路跑完表、数据、索引，到 post-data 建触发器那一步才炸——
   **看上去像已经拷好了**。修法见 `025871f`：拷表前先把 public 下的函数带过去，并在校验器里断言触发器都到位。

另外两处是**校验器自己的 bug**，都已修：`--no-owner` 会让新库的表归 `postgres`（应用写不进去，且只在切换后才暴露，
`2b65f9b`）；以及两侧排序规则不一致让 `comm` 报出**根本不存在的**差异（`3c3cff2`）。

还修了一个**每库账本设计的真缺口**（`41f2c73`）：跨属主迁移会进入每个相关属主的范围，而对象核验却要求它声明的
**全部**对象都在 ⇒ 新建 content 库被要求存在 automation 的 facebook 表 ⇒ baseline 永远拒绝 ⇒ 新库永远没有账本 ⇒
契约门永远报「账本表不存在」。修法 = 核验收窄到本属主拥有的对象；索引/约束声明不带表名、跨属主时无法归因，
就**如实打印「本次未核验」并逐条列出**，而不是静默跳过。

---

## 2. **物理拆库已完成（dev + ol 两端）**

2026-07-25 深夜，两台都已翻到三个属主库，指向**同一组**库 —— 今天的「dev 与 ol 共享同一份数据」语义逐字保住。

**终局实测**（在 dev 机的 PG 上取，它就是这四个库的宿主）：

```
连接分布：
  aidcp_api          dev 1   ol 1
  aidcp_automation   dev 3   ol 2
  aidcp_content      dev 1   ol 1
  aidcp（旧共享库）  应用连接 0 条

90 秒写入增量：
  aidcp              4 提交 / 0 插入 / 0 更新   ← 只剩探测查询，零业务写入
  aidcp_automation 442 提交 / 0 插入 / 232 更新
  aidcp_content    124 提交
  aidcp_api         66 提交
```

两端的契约门都给出三个**各自独立**的结论（content 0069 / automation 0077 / api 0078，全部通过），
两端 `does not exist` / `permission denied` / 认证失败**均为 0**。

**ol 的部署走的是发布分支** `release/20260725-db-split`（= master `41f2c73`），部署前已做
`/opt/aidcp/cloud.bak.20260725-oldbsplit.tar.gz` 与 `.env.bak.20260725-oldbsplit`。

### 旧库已退役（2026-07-25 16:03，不可逆）

`DROP DATABASE aidcp` 已执行。实例上现在只有 `aidcp_content` / `aidcp_automation` / `aidcp_api`
（+ 同机 `isales`，**一字未动**）。

退役前做实的三件事：
1. **六次采样、跨一分钟，`aidcp` 上的连接数恒为 0** —— 没有任何消费者。
2. **两份备份**（都在 `/opt/aidcp/pgbackup/`，该目录在 `cloud/` 之外、不受部署 rsync 影响）：
   - `aidcp-pre-l3-20260725.dump` —— **拆库之前**的完整状态（跨属主外键都还在），要整体回到「一个库」就用它；
   - `aidcp-final-before-drop-20260725.dump` —— 旧库**最终**状态，已用 `pg_restore --list` 验证可读、**含全部 98 张表的数据**。
3. **退役后冷启动验证**：dev 重启一次，47 条子系统就绪、三个契约门全过、**0 错误** —— 证明没有任何东西依赖旧库。

### ⚠️ 回滚方式已经变了

**「注释掉三行 URL + 重启」这条路已经不通了** —— 属主 URL 未设时会回落到 `PGDATABASE=aidcp`，而那个库已经不存在，
进程会**响亮地起不来**（这是对的方向：不存在的退路不该假装还在）。

现在真要回到单库，必须：
```bash
# 1. 停两端服务
# 2. 从备份重建旧库（选哪一份取决于你要回到哪个时点）
sudo -u postgres createdb -O aidcp aidcp
sudo -u postgres pg_restore -d aidcp /opt/aidcp/pgbackup/aidcp-final-before-drop-20260725.dump
# 3. 把三个属主库在退役之后产生的增量搬回去（这一步没有现成脚本，且随时间越来越大）
# 4. 注释掉两端 .env 的三行 AIDCP_PG_*_URL，重启
```
⇒ **实际上这已经是单向门。** 从这里往前只有修，没有退。

### 两处已知的残留（都无害，登记备查）

- 两端 `.env` 里 `PGDATABASE=aidcp` 仍指向一个已不存在的库。**刻意不改**：改成某个属主库名会让「回落」静默连上
  一个错误但存在的库，那比响亮失败坏得多。
- `pg_hba.conf` 里 `host aidcp aidcp <addr> scram-sha-256` 两条规则现在指向不存在的库，**惰性无害**（没有该库可匹配）。
  新增的 `host aidcp_content,aidcp_automation,aidcp_api aidcp <addr> scram-sha-256` 两条才是生效的。

### 还没做的收尾

- **enforce 模式仍未开**（`AIDCP_SCHEMA_GATE` 默认 warn）。三个契约门现在都真的在各自库上判，
  开 enforce 才能把「账本对不上就拒绝启动」变成硬保证。建议观察几天后再翻。
- **`aidcp_automation` 的账本带着全量 77 行**（随表一起拷过去的，`schema_migrations` 登记为 automation 属主），
  而 content / api 是用 `migrate baseline --owner=` 按自己范围新建的（20 / 53 行）。三者都过契约门；
  automation 那份多出来的行属过渡残留，`migrate status` 会如实报出，**没有自动删**（删账本行不可逆）。

## 3. 本批里最该知道的六件事（血泪，接手前必看）

1. **离场清理的盲删是真的会咬人**（`f02c9ee`，硬期限 2026-08-14 是库里第一条 `purge_due_at`）。最严重的一个：账号级删除**没有归属校验**——那批表（运行控制 + 五张回复配置表）主键只有 `(platform, account_id)`、**没有环境维**，只能整账号删。而账号可以改派环境，且占位离场会把 `accountId` 直接设成 `envKey`。原实现还在第一步就删掉了绑定行，于是崩溃重入时连「这是不是我该删的」都算不出来。修法：绑定行移到最后一步与状态翻转同事务，账号级删除**只在绑定仍是本次离场的环境时**才执行，否则只删环境维并留审计。**方向是收窄——宁可少删。**

2. **写者锁的旧处方是错的，别照抄任何旧文档。** 「让连接配置跟随 `resolveOwnerPgConfig('automation')`」会引入 bug：它的连接配置结构没有连接串字段，而 owner resolver 在 URL 已设时返回的正是连接串 ⇒ 五字段全空 → 回落内置默认 ⇒ **在错的库上取锁而且会成功**。正确修法（`835ab13` 已落地）：**先给连接配置加连接串支持，且连接串在场时排他**，绝不叠 host/port 回落。

3. **api 网关调用必须在 `BEGIN` 之前。** 把它放进 automation 事务里会构成「api 连接等 automation 行 / automation 连接等 api 行」的环，而 **PostgreSQL 的死锁检测器看不见**（两条连接在它的锁图里无关），两边都会挂到超时。有专门的回归用例断言顺序是 `GATE, CONNECT, BEGIN`。

4. **`event_outbox` 属 automation 单写——api 域不能拿它当自己的 outbox。** 离场那一刀因此没有复用它，而是让**准入行本身就是 outbox 行**（那行本来就必须存在且逐字携带全部载荷，再造一张表等于凭空造出「两行必须一致」的新问题）。事务型入队 + at-least-once + 幂等键的语义逐字对齐。

5. **门禁会因为「你把问题修好了」而变红。** 行锁豁免清单与跨属主外键例外清单都是**只减不增 + 僵尸条目也失败**：修掉一处就必须同步删登记并调低 `frozenTotal`。本批集成时踩了三次，每次都是门禁先红、我再收口——这正是它该有的样子。

6. **迁移号会撞车。** 三条并行分支同时取了 `0075`。集成时按落地顺序重编号（`0075` topic-cursor / `0076` config-mirror-inbox / `0077` accounts-projection / `0078` cleanup-admission），并把 `KNOWN_MAX_SCHEMA_VERSION` 与文件头注释一起改。并行开分支时**先约定号段**能省这一步。

---

## 4. 已登记、但本批**没做**的事

- **`interaction-store.ts:1403`** 写运行控制时内嵌的 `EXISTS(accounts)` 守卫：属账号投影那一刀的范围，但两刀并行、文件互斥，**未接上投影**。翻转前应改读本域投影表。
- **`interaction-store.ts:397`** 用 `to_regclass` 探测 api 属主的 `interaction_reply_configs`。这是目录探测、不是数据读，**没有任何门禁看得见它**；翻转当天它会**静默报「表不存在」**，把互动域降级成 `legacy_read_only` —— 降级原因是错的，而且不响亮。**这是本批发现的最隐蔽的一处残留。**
- **`assertAccountScope` 的 hold 检查范围变宽**：准入行不再随物化删除，所以已物化但未清除的环境现在也会被拒绝互动写（原来那个窗口不拒）。方向是更 fail-closed、错误码不变，**有意保留**。若要精确复原旧义，给网关那条查询加 `AND materialized_at IS NULL`。
- **`interaction_offboards` / `client_env_revocation_holds` 仍无 `execution_target` 列**，dev 与 ol 两台各跑一份定时器扫同一批行。今天靠 `FOR UPDATE SKIP LOCKED` + 幂等兜住；补列要连带想清回填（猜错 target 的行会从此两台都不认领 = 永不清理），故位置是「撤行锁之后」而非「立刻」。
- **`scripts/` 不进 typecheck**（tsconfig `include` 只有 `src/**` + `test/**`）。迁移执行器的类型错误 `npm run typecheck` 抓不到。
- **`run-migration.ts` 从不写账本**（既存缺口）。用它跑迁移会让账本与库分叉。
- **enforce 模式仍未开**（`AIDCP_SCHEMA_GATE` 默认 warn）。翻转稳定后再开。

---

## 5. 红线（不变）

1. **域间只走接口**，绝不把别的域的池注入消费方。
2. **绝不碰同机 `isales`**（独立 systemd / 目录 / 端口；它还占着 dev 的 6379 与 `redis.service` unit 名）。
3. **文档 / 提交 / tasks.md 不写任何密码 / token / 私钥**。
4. **不静默假成功**；特别注意**失败方向**——若某方法的 `false` 是「放行」，它 MUST NOT 把读失败吞成 `false`。
5. **部署只从 canonical master 的 clean 快照走**（`git archive HEAD`）。dev 默认可自动部署；**ol 只有用户明确要求 + 从 release 分支**。
6. **canonical 目录永远停默认分支**；worktree 的 node_modules **各自装、绝不软链**。
7. **不引入 Redis**（决策已定；它的两个前置先手 `25c0d28` 已落地，重开话题的可判定触发条件见决策文档 §5）。

---

## 6. 收尾时给用户的口径

用非技术语言讲：以前系统里三块业务是混在一个数据库里的，很多地方一块业务直接伸手去读、去改另一块业务的数据；这一批把这些手全部收了回去，改成「你要什么，向管这块的人要」。现在机器能自动证明「没有任何一处再越界」，而且以后谁写回一处越界，测试当场就红。数据库本身还没有拆开——真正拆开只剩最后一步（把数据分别拷进三个新库、把地址换过去），随时可以一键退回原样。
