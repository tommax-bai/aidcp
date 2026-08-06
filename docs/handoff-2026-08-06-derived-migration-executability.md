# 交接 · change `restore-derived-migration-executability`（2026-08-06）

> **给接手 session 用：从头读到尾，按本文执行即可。** 进度 **9/36**，第 1–2 节已完整交付并验证，
> 剩下第 3–7 节是「归属机制」那一大块。
>
> 权威文档：`openspec/changes/restore-derived-migration-executability/{proposal,design,tasks}.md`。
> **design.md 的「Decisions」五条是已定的方案，别推倒重来**；真要改，先读本文 §5 那两条硬约束——
> 大部分「更简单的做法」都是被它俩排除掉的。

---

## 0. 起手（先做，别跳）

```bash
bash scripts/task-preflight          # 四个 canonical 必须都停默认分支，exit 1 即停手
openspec list | grep restore-derived # 应为 9/36
ls -d ../aidcp-cloud ../aidcp-api ../aidcp-automation ../aidcp-content ../aidcp-transport
```

**本文写就时各仓头**（`origin` 上，均已推送）：

| 仓 | sha | 本 change 的改动 |
| --- | --- | --- |
| `aidcp`（控制仓，`main`） | `a3e83de5` | 同步脚本覆盖 `scripts/`；trisection 文档 §0.0.4 |
| `aidcp-cloud` | `343c464` | `scripts/migrate.ts` 取本仓仓根 |
| `aidcp-transport` | `2c635e8` | 纳入 `src/schema/schema-inspect.ts` |
| `aidcp-api` | `e91880d` | CLI 修复 + 删 7 个断脚本 + pin |
| `aidcp-automation` | `2bcca28` | 同上 |
| `aidcp-content` | `cc8a0ab` | 同上 |

---

## 1. 这个 change 在解什么

**一句话：拆仓后没有任何在跑的服务能执行数据库迁移，因此新环境无法从零建库。**

它不是「为了将来能建新机器」。**要害是日常改数据库结构这条路断了**——正规流程是写一条迁移、
部署前跑一下、它记一笔账；三个服务谁都跑不了这个命令，绕过去只剩「回那个不许上线的老仓跑」
或「手工连库改」，而后者正是这套机制建起来要消灭的东西。

空库实跑是**体检**，不是目的：现有的库早就建好了，任何毛病都被「反正东西都在」盖住，
拿空库跑一遍等于让这套记录自证一次。2026-08-05 那次自证没通过，照出两个真缺陷。

---

## 2. 已交付（第 1–2 节，9 项）

### 做完的事

- **三仓迁移 CLI 可执行**：引用改为包说明符（`aidcp-kernel/**` + `aidcp-transport/**`）；
  `schema-inspect.ts` 纳入共享包；迁移目录与属主清单改取自**脚本自己的仓根**。
- **`scripts/` 纳入拆仓同步**（根因）：点名清单 `SCRIPT_MEMBERS`（只有 `migrate.ts`）+
  `SCRIPT_UNMANAGED`（`db-split/`、字体子集脚本，有意留着、永不 prune）；其余判「多出」并已删。
- 派生仓 `scripts/` **自此是派生物，MUST NOT 手工改**——改事实源 `aidcp-cloud/scripts/` 再跑同步。

### 立项时判错、实施中被推翻的（**这段是本节最值钱的部分**）

原判「两处过期的 kernel 引用」，全量扫描实测：

- **三仓 10 个脚本里 9 个的相对 import 指向本仓不存在的路径**（api / content 各 7 个文件断、
  automation 4 个）。真实故障面是**整套迁移机器 api / content 根本够不着**：`src/schema/`
  判归 automation 独占，另两家靠共享包取用，而那个包只搬了 12 个文件里的 10 个。
- **修完 import 才露出第二层，且更危险**：`migrationsDir()` / `tableOwnershipPath()` 的默认值按
  「模块文件往上两级」解析，装进共享包后指向包自己的目录。
  **import 断了是响亮失败；路径默认值错了是读到零条迁移，而契约门会把「零条」判成通过。**
  仓内那道空目录守卫正是为此而设，这次是它第一次真正拦住东西。

### 删掉的 7 个脚本为什么是「留着有害」而非「暂时没纳管」

`generate-migration-headers.ts` 会 `writeFile(migrationsDir()/…)` **写回迁移文件**，
而派生仓 `migrations/` 只有本属主子集（实测 api 70 / automation 58 / content 20，事实源 110）。
在派生仓跑一次，就会按不完整集合重算头声明并改写**已应用的**迁移 → 校验和不符 → 该库迁移命令全停。
其余同理（按子集产出清单、或多一条绕开账本的路）。这 7 个当时全部处于断裂状态且零 `package.json` 引用。

---

## 3. 剩下要做的（第 3–7 节，27 项）

按 `tasks.md` 的顺序做即可。四块：

1. **第 3 节 · 把「执行范围」与「账本范围」拆开**（机制核心，先做）
   - 账本范围恒为全部属主（**不变**，两条既有理由：否则外域迁移会被当 pending 重放、
     且乱序闸会在每个库里判失序整批拒绝）；执行范围由显式声明给出。
   - 拆开之后，12 条单属主残留迁移**自动就对了**。
2. **第 4 节 · 归属解析顺序 + 封闭名册**
   - 顺序唯一：① 文件内属主头 → ② 名册条目 → ③ 对象声明能定位到表 → ④ **失败并指名**。
   - 第 ④ 步取代今天的残留分支，是本 change 的核心红线：**MUST NOT 静默计入全部属主**。
3. **第 5 节 · 13 条历史迁移逐条裁定**（含那条跨属主的处置）
4. **第 6–7 节 · 静态可执行性闸 + 分发验证**

---

## 4. 实测数据（起点，**MUST 逐条实读复核，MUST NOT 照抄**）

13 条残留迁移的粗扫归属（正则扫的，只作起点）：

| 属主 | 条数 | 版本 |
| --- | --- | --- |
| api | 9 | `0021` `0027` `0030_content_schedule_group_comments` `0040` `0043` `0044` `0050` `0051` `0069` |
| automation | 3 | `0045` `0046` `0055` |
| **跨属主** | **1** | **`0030_panel_hardening_indexes`** |

- **`0030_panel_hardening_indexes` 是唯一真跨属主的**：在 `risk_counters` / `interaction_feed`
  （automation）与 `llm_token_usage`（content）上各建索引，**在任何单一属主库里都跑不通**。
  空库实跑就停在它上面（`relation "risk_counters" does not exist`，进度 content 1/20、
  automation 13/57、api 20/70）。**粗扫会看漏它**（去重后只报一个属主）——这就是「MUST 实读」的理由。
- **`0050` 形态不同**：它是一个在表属主找不到时**主动 RAISE EXCEPTION** 的 DO 块，
  失败更响亮但同样整批停。

**为什么这些迁移「不持有存活对象」这句话是假的**：归属只看 `-- aidcp:objects=` 头，
索引名反推不出表；而头声明的生成规则是「每个对象归**最后**创建它的那个文件」，
所以早期迁移常只剩一个空头 → 落进残留分支。`migration-owners.ts` 文件头自称这类迁移
「不持有任何存活对象，多记是安全方向」——**实测 13 条里 12 条仍在对真实的表执行 DDL/DML**。
**第 3.1 项要求同批改掉这段注释**，留着会继续骗下一个人。

**判据（可机械化，就是第 6 节那道闸）**：一条迁移只在「它触及的每张表都由同样在该库执行的迁移创建」
的库里安全。`0000_baseline` 那种自己建自己用的跨属主迁移因此无害；只建索引不建表的就致命。

---

## 5. 两条硬约束（**大部分「更简单的做法」都是被它俩排除的**）

### ① 已应用迁移的字节不可改

校验和是**整文件 sha256**，账本行与磁盘不一致即 `migration_checksum_mismatch` **整批拒绝**
（`status` 与 `up` 都过 `planMigrations`，两个命令一起停）。
那 13 条全部 ≤ `0069`、**在 dev / ol 的账本里都已入账**。

⇒ **往它们里加一行属主头，dev 与 ol 的迁移命令当场全停。** 这就是为什么历史必须走
**独立的封闭名册**（只减不增）、只有新迁移才用文件内头。范式与仓内既有的
`boundaries/adjudicated-files.json` 一致（人工判过的集合，生成物不得回喂顶替）。

### ② 归属判定 MUST NOT 由 SQL 文本反推表名

现有判据明写这条（会造出第二套口径）。第 6 节那道闸确实要扫 SQL 文本拿「引用了哪些表」，
**它 MUST NOT 参与归属判定，只有否决权，永远不得为任何迁移分配属主**——这句话要写进扫描器文件头。

---

## 6. 三个必须先查证、不许凭猜的点

1. **`migrate verify` 接不接受「同一对象被两个版本声明」？**（`0030` 与接替它的两条新迁移）
   实读对账代码确认。不接受时的退路是新迁移改用新索引名，并在名册 `basis` 里写明为什么换名。
   （tasks 5.4，**排在 5.3 之前做**）
2. **头声明生成器会不会回头改被接替的那条？** 它按「每个对象归最后创建它的那个文件」重算；
   接替迁移一落地它就想去改 `0030` 的头 → 撞约束①。**必须加「已应用 / 冻结集合内的不重写」守卫**，
   并实测「重跑生成器后 `git status --porcelain migrations/` 为空」。（tasks 5.5）
3. **名册的「冻结集合」怎么表达？** 倾向显式 version 清单（可审、可重放），
   不要用文件 mtime / git 首次出现时间。（design Open Questions）

---

## 7. 已知的坑

- **`owners: []`（记账不执行）MUST 同时带 `supersededBy`**，且被点名的迁移合起来 MUST 覆盖它
  创建过的全部对象。**这条不加，`0030` 的三个索引会在全新库上被悄悄丢掉**——这是本 change
  最容易犯的错。
- **MUST NOT 因执行范围收窄就从派生仓删除迁移文件。** 账本范围不变，删了账本行会变成
  `ledgerOnly` 噪声。分发按账本范围，执行范围只控制跑不跑。**这条容易做反。**
- **边界 seed 窗口已于 2026-08-06 关闭**（随 `cloud-service-boundary-gates` 归档）：
  `--reseed` 一律被拒；新增豁免只走 `--raise` 三字段通道。新增 `src/schema/**` 文件会要求
  逐个裁定归属（该目录的 `newFile` 是 `adjudicate`）——**能不新增豁免就不新增**。
- **`aidcp-cloud` 永不部署**（§8.0）。它是事实源 + 整图验证仓。本 change 全部改动对 dev / ol
  是**零 DDL、零校验和变更**，但**部署前仍 MUST 先跑一次迁移状态查询**自证零 pending 异常。
- **`npm install`，不要 `npm ci`**（派生仓 `npm ci` 会清空 `node_modules`）。
  共享包 `dist/` 是 gitignored、靠 `prepare` 在安装时构建，所以改了共享包必须
  推包 → 抬 pin → 三仓 `npm install`。
- 派生仓工作树可能有**并发 session 的脏文件**（本次在 `aidcp-api` 遇到过一个无关测试文件）。
  **提交一律按路径 stage，绝不 `git add -A`。**

---

## 8. 常用命令

```bash
# 对账（只读）/ 同步 / 同步并删清单外的
scripts/sync-split-repos
scripts/sync-split-repos --apply
scripts/sync-split-repos --apply --prune
scripts/sync-split-repos --repo aidcp-api        # 限定单仓

# 三仓自证 CLI（本机无库时预期停在 ECONNREFUSED，与「找不到模块」截然可分）
cd ../aidcp-api && npx tsx scripts/migrate.ts status

# 事实源仓三件套
cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck
cd ../aidcp-cloud && npm run boundaries:refresh   # 新增 src/schema/** 会要求逐个裁定归属
```

---

## 9. 这个 change 解除谁的阻塞

- `cloud-schema-migration-executor` 的 **5.9「全新空库拉起」**——本 change 落地后它**第一次具备
  执行条件**。**本 change MUST NOT 自称已验证空库拉起**，它只负责让那件事可执行。
- 该 change 的 **6.5（契约门默认转 `enforce`）** 与 **5.11（删过渡旋钮）** 依赖本 change 先落地：
  门一拦、新环境又建不出库 = 把自己锁在门外。
- 真机验收挂 `docs/real-machine-acceptance-backlog.md` **簇 111**（不是 110，那簇是风控写者锁）。
