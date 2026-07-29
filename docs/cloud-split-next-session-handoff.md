# 云端拆仓 · 下一 session 交接（可直接执行）

> 生成于 2026-07-26 07:00。**给接手 session 用**：从头读到尾，按本文执行。
> 对象 = `aidcp-cloud` 拆成 `aidcp-api` / `aidcp-automation` / `aidcp-content` 三个业务仓
> + `aidcp-kernel`（零副作用契约）/ `aidcp-transport`（跨进程运行时原语）两个共享包。
>
> **本文里凡是写「已实测」的，都是对着代码或命令实跑出来的。但 fleet 活跃、数字会滞后——
> §0 的每条命令请自己重跑一遍，以你跑出来的为准，不要相信本文的快照数字。**

---

## 0. 接手第一件事：核对现状

```bash
git -C /Users/baitianxing/codes/aidcp branch --show-current    # 必须是 main，不是就先停手（CLAUDE.md §7）
ls -d ../aidcp-cloud ../aidcp-api ../aidcp-automation ../aidcp-content ../aidcp-kernel ../aidcp-transport
./scripts/sync-split-repos                                     # 只读对账：七个目标是否一致 + kernel pin 是否对齐
cd ../aidcp-cloud && npm run test:acceptance 2>&1 | grep "AC-BOUND metrics"
```

**期望看到**（2026-07-26 07:00 实测）：

```
AC-BOUND metrics {"sourceFiles":455,"crossBoundaryEdges":0,"involvingContent":0,
                  "exemptionEntries":0,"frozenTotal":0,"unplanned":0}
```

`crossBoundaryEdges` **不是 0** ⇒ 有人新增了跨服务耦合，先查清楚再往下走（棘轮只许下降）。

### 0.1 当前指针（fleet 活跃，务必自己复核）

**2026-07-29 22:15 实测**（源 = `aidcp-cloud@b66c022`，change `split-cloud-automation-production-runtime` 第一批已 land）：

| 仓 | HEAD | 分支 | 状态 |
| --- | --- | --- | --- |
| `aidcp`（控制仓） | `beb8e5c1` | `main` | — |
| `aidcp-cloud`（事实源） | `b66c022` | `master` | typecheck 0 · 全量绿 |
| `aidcp-kernel` | `21cc10a` | `master` | typecheck 0 · 测试 57/57 |
| `aidcp-transport` | `08c4e81` | `master` | typecheck 0 · 测试 36/36 |
| `aidcp-api` | `662918f` | `master` | typecheck 0 · 测试 470/470 |
| `aidcp-automation` | `2c45e1b` | `master` | typecheck 0 · 测试 1888/1888 |
| `aidcp-content` | `3770ea2` | `master` | typecheck 0 · 测试 436/436 |

六仓：工作区干净、已推远端、共享包 pin 对齐（kernel `21cc10a` / transport `08c4e81`）。
`./scripts/sync-split-repos` 除组装根外零差异（api 115/115、automation 234/234、content 79/79、
kernel 102/102、transport 48）。边界门禁：`sourceFiles 526 · crossBoundaryEdges 0 ·
exemptionEntries 0 · frozenTotal 0`。
**`aidcp-cloud@b66c022` 已部署 dev（单体形态），healthcheck 全过，同机 isales 未触碰。**

**同步链路上这次实测出的两条，照着做能省一晚上：**
- **测试要单独一趟 `--apply --tests`，而且它不删。** `--prune` 与 `--tests` 互斥（脚本硬拦）。
  正确顺序：先 `--apply --prune` 收 src、再 `--apply --tests` 收测试、最后**人工删**它报出的「多出」。
  少了这一趟，src 搬走而测试留在原仓，原仓当场编译红。
- **派生仓自己那份 `boundaries/*.json` 不在同步范围内，会长期静默漂。** automation 那份与事实源
  已差 88 行，且早就漏了两条裁定——平时跑的 census 读的是**已生成**的 `module-ownership.json`，
  正好把窟窿盖住，只有跑 `boundaries:refresh` 才炸。见 change 的 tasks.md 0.7c。

**下面 0.1 之外的历史快照（`f9ff71e` / `7d32913` 那一版）已过期，只作追溯。**

### 0.2 一句话进度

**跨服务耦合处置已全部完成（Phase 0–5，96 → 0）；同步与验证链路 2026-07-29 已全部打通
（依赖装得上、迁移进同步范围、测试归属两类证据共同派生），六仓源码 / 迁移 / pin 三项零漂移。**

**下一步仍是主交付物：三个仓各写自己的启动入口 `main()`。** content 与 api 已有真手写入口；
**automation 的入口仍是有意 fail-closed 的壳**——`src/automation-composition-root.ts`
的 `runAutomationEntry()` 读完配置即抛 `AutomationRootNotReadyError`，
12 条 readiness blocker 全标 `closingChange:'future'`、**无 change 承接**。
这不是 bug 是设计，但意味着批次 4 未完成；批次 5（dev 三服务真跑）随之未开工。

**2026-07-29 更新：那 12 条孤儿 blocker 已有承接者** —— change
`split-cloud-automation-production-runtime`（用户当日拍板）。当前进度见该 change 的 `tasks.md`。
第一批已 land + 部署 dev，做完的是「前置」而非入口本身：
归属改判（四个精选评估角色 + 基类 + 精选闸 content → automation）、模型出口进 transport、
LLM 错误族抬进 kernel、automation→content 的三个 kernel 端口面、四条运营指令的 kernel/transport 契约。
**这些都只定义、未接线**；automation 的 `main()` 仍未写，批次 5 仍未开工。
台账本身也仍未清零（cloud 55 条 / automation 14 条），**清零是入口能写的前提，不是入口写完的结果**。

---

## 1. ✅ 已结案：风控状态机在 dev 和 ol 上都写不进库

> **2026-07-26 已修，dev 已部署验证；ol 未部署。** 用户选定候选 ①（走已有窄读口，接受 TOCTOU）。
> 修于 `aidcp-cloud@8d903dd`。真机证据：dev 上 `risk_state` 07:55:48 写入成功（上次成功 07-23），
> 那条卡了 2352 次重试的面板命令回读到 `state=applied` —— **§7 里那条「`applied` 成功路径从未在
> 真机跑通过」的缺口一并补上了。**
>
> 同批还抓到并修掉**第二处同形缺陷**（互动运行控制行的播种守卫同样内联 `SELECT 1 FROM accounts`），
> 并加了门禁 **`AC-OWN-06`（无跨属主表读，无豁免通道）**——原有 `AC-OWN-02/03` 只看写，
> 两处缺陷都是读、都被全绿放过去。已注入违规验证门禁会红；当前 `crossLayerReads: 0`。
>
> 下面保留原始诊断供追溯。

**这不是拆仓 Phase 的产物，是物理拆库的遗留后果。原文：未修，等用户拍板。**

**症状**：`risk_state` 的任何持久化都报 `relation "accounts" does not exist`。
dev 上 `risk_state` 最近一次更新停在 **2026-07-23**；ol 日志 2026-07-25 19:53 有同一条错。

**根因**：`aidcp-cloud/src/risk/pg-risk-store.ts` 的 `saveState` 用**归属条件写**，
SQL 里 `WITH owner AS (SELECT 1 FROM accounts WHERE account_id=$1 AND execution_target=$8)`。
`accounts` 是 **api 属主表**，而 `PgRiskStore` 绑的是 **automation 池**。
拆库前三域同库、这条 join 成立；拆完 automation 库里没有 `accounts`，整条写必炸。
同一文件另有第二处 `SELECT execution_target FROM accounts`（按符号名找 `saveState` 与其下方的归属读）。

**影响面**：`applySignal` 先改内存态、再落库，所以**进程活着时行为是对的、一重启全丢**，
回落到 07-23 的陈旧表。受影响的是全部状态迁移来源：验证码协助信号、FB 限流信号、后台人工信号。
配额计数（`risk_counters`）走另一条路，不受影响。

**为什么是现在才发现**：旧的同步后台路由调的是同一个方法、一样炸，只是回一个没有原因的 500。
是 P5-1 把风控写改成异步四态之后，失败原因第一次可见可归因（回读到
`state:'failed', reason:'relation "accounts" does not exist'`）——这正是那个设计要的效果。

**为什么没当场修**：条件写是**一条语句里同时做谓词与写**，拆成两步会在**风控单写者**路径上开 TOCTOU 窗口。
两条候选：

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| ① 走已有端口 | 用 `src/kernel/account-ownership-port.ts` 的 `getExecutionTarget` 先读再写 | 引入 TOCTOU 窗口；但该端口文档**本就写明** automation 侧「绝不自己拼 accounts 的 SQL」，即本就该这么改 |
| ② 属主落本域表 | 给 `risk_state` 加属主 target 列，谓词回到 automation 自己域内 | 无 TOCTOU；要加列 + 回填 + 一条迁移 |

**`automation_account_projection`（迁移 0077）帮不上忙**——它有意不带 `execution_target`（见该迁移注释）。

**接手怎么做**：把上面两条摆给用户选，选定后再改。**MUST NOT 自己挑一条就动**——
改的是线上风控单写路径。完整版见 `docs/cloud-composition-root-trisection.md` §0.0.2。

---

## 2. 主交付物：三个仓各写 `main()`

### 2.1 距离已量化（2026-07-26 实测，Phase 5 之后重测）

| 仓 | 业务代码断裂引用 | 组装根副本断裂引用 |
| --- | ---: | ---: |
| api | **0** | 107 |
| automation | **0** | 107 |
| content | **0** | 138 |

**这是本次工作最重要的一个数**：三个仓里，**每一个属主业务文件的相对引用都已能在本仓内解析完毕**。
全部剩余断裂（107/107/138）来自**组装根副本** `src/server.ts`——它按设计从不自动同步，
保留着单体的原始相对引用。**各仓写完自己的 `main()`，这些一次全消。**

复现命令（判据 = 「该文件的相对 import 指向一个本仓没有的属主文件」）：

```bash
cd ../aidcp-cloud && python3 - <<'PY'
import json, os, re
own = {e['path']: e['layer'] for e in json.load(open('boundaries/module-ownership.json'))}
def resolve(base, spec):
    raw = os.path.normpath(os.path.join(os.path.dirname(base), spec))
    for c in (raw[:-3]+'.ts' if raw.endswith('.js') else raw, raw+'.ts', raw+'/index.ts'):
        if c in own: return c
for layer, path in {'api':'../aidcp-api','automation':'../aidcp-automation','content':'../aidcp-content'}.items():
    biz = root = 0
    for rel in sorted(own):
        f = os.path.join(path, rel)
        if not os.path.isfile(f): continue
        is_root = own[rel] == 'composition'
        if own[rel] != layer and not is_root: continue
        for spec in re.findall(r"from\s+'(\.[^']+)'", open(f, encoding='utf-8').read()):
            t = resolve(rel, spec)
            if t and not os.path.isfile(os.path.join(path, t)):
                root += 1 if is_root else 0; biz += 0 if is_root else 1
    print(f'{layer:11s} 业务 {biz}  组装根 {root}')
PY
```

### 2.2 写 `main()` 的硬约束（这几条错了会静默）

1. **组装根**永不自动同步。`scripts/sync-split-repos` 对 `src/server.ts` **只报不改**，
   `--apply` 也不动它。那是各仓要**手写**的主交付物；自动覆盖等于把它悄悄删掉。
2. **段落划分是现成的**：单体 `src/server.ts` 已被批次 0 切成四段
   `segAApiFoundation` / `segBContent` / `segCAutomation` / `segDApiServing`。
   每个仓的 `main()` = 取自己那几段 + 把跨段依赖换成注入的端口。
3. **跨段前向引用 MUST 经响亮取用闸**（`crossSegment`），**MUST NOT 写成裸 `ctx.X?.doSomething()`**——
   单体里恒有、拆完读到 `undefined` 就被 `?.` 静默吞掉，调用方照拿「成功」。
   `AC-SPLIT-CROSSSEG` 会当场拦；确属「缺席无后果」的进白名单并写理由。
4. **一个域绝不对另一个域的库开池**。本进程只对本属主库开池，启动期两个方向都断言。
5. **跨进程后 `instanceof` 恒 false** ⇒ 跨边界的错误识别 MUST 用结构化守卫（按 `name` + 具名字段判）。
   已知一条待办：`structuredClone` 会丢 `reason`，真 RPC 缝落地时传输层要显式映射 `{name, reason, message}`。
6. **`test/server-startup-order.test.ts` 的装配守卫会在拆分那天蒸发**——它对着单体组装根断言。
   写 automation 仓的 `main()` 时 MUST 把它复制过去、指向该仓自己的组装根。

### 2.3 之后是批次 5

dev 三服务部署 + soak，再**按用户明确要求**上 ol（从发布分支走，见 CLAUDE.md §5/§6）。

---

## 3. 每批的固定收尾（顺序不可换）

```
npm run typecheck
npm run test:acceptance          # 安全红线：AC-BOUND-* / AC-OWN-* / AC-SPLIT-* 必须全过
npm test
npm run boundaries:refresh
git diff boundaries/             # 逐条对账，MUST NOT 整体重序列化（见下）
commit / push
部署 dev + 哈希校验 + 健康检查
./scripts/sync-split-repos --apply --prune --tests    # 同步七个目标
回写 docs/cloud-composition-root-trisection.md 与 docs/cloud-cross-service-coupling-resolution.md
真机项登记 docs/real-machine-acceptance-backlog.md 簇 60
```

---

## 4. 踩过的坑（照着躲，别再踩一遍）

这些全部固化在 **CLAUDE.md §8（OVERRIDE 级）**，对任何触碰 `aidcp-cloud/src` 或 `boundaries/` 的改动生效。
下面是这次工作里**新踩到或再次确认**的几条：

- **豁免管得住门禁，管不住模块解析。** 有三条边曾被判「不做、维持豁免」——那个裁决在**单体语境**下是对的，
  因为三域同进程时边挂着不影响任何东西。但拆完之后目标仓的 `src` 里根本没有那个文件，import 解析不了、
  仓编译不过。**判「某条边可否留着」时，「门禁允不允许」与「拆完还能不能解析」是两个问题。**
- **`boundaries/*.json` MUST 手工 Edit 追加，绝不脚本整体重序列化。** 它们一行一条、分组顺序有意义；
  重序列化会把「语义改 3 处」变成「diff 一千行」，今后每次 review 都看不见真正的改动。
- **kernel 准入检查只剥注释、不剥字符串字面量。** 这次真中了一次：kernel 里一句错误文案带了 `LlmClient`
  这个词，门禁当场判「LLM 或供应商 HTTP 调用」。改文案即可，但**原因一点都不显然**——
  `src/kernel/role-runtime.ts` 里已就地写明，别「顺手」改回去。
- **新增 kernel 成员必须同时改两处**：`ownership-rules.json` 的 `fileOverrides` + `kernel-non-members.json`
  的 `kernelRoster.members`（`AC-BOUND-03` 对两者 deepEqual）。漏一处 `boundaries:refresh` 直接抛错。
- **新增表必须同时改两处**：`boundaries/table-ownership.json` + 重跑
  `npx tsx scripts/db-split/generate-owner-table-lists.ts`（否则 `AC-SPLIT-01` 红）。
- **`sync-split-repos --prune` 的幂等 bug 已修**（`f9ff71e`）：文件已删时 `os.remove` 抛
  `FileNotFoundError` 会中断整轮、后面几个仓一个都同步不到，**且看着像同步跑完了**。
- **迁移文件不在同步脚本范围内**（见 §5）。

---

## 5. 已知机制缺口：迁移文件靠手工搬

`scripts/sync-split-repos` 明确「只管 `src/` + package.json 的 kernel pin」。
所以每加一条迁移，都要**按表属主手工放进对应 sub-repo**（本次 `0079` 手工放进了 `aidcp-automation/migrations/`）。

已实测这条规则**可机械化**：以 `boundaries/table-ownership.json` + 迁移头部 `-- aidcp:objects=` 声明推导
「该迁移进哪几个仓」，68 个带头声明的迁移里 **63 个严格符合**；另 5 个是共享基础设施
（账本表 `schema_migrations`、跨属主索引批）——它们进全部三个仓，是对的。
**补这个机制时要显式建模「共享基础设施」这一类，别把它当异常。**

在补上之前：**加迁移 = 记得手工放一份**，否则拆仓后那个仓的库永远缺这张表、且没有任何提示。

---

## 6. 相关文档与 openspec 指针

| 文档 | 作用 |
| --- | --- |
| `docs/cloud-composition-root-trisection.md` | **进度卡 + 下一步 + §0.0.2 那个待修缺陷**。接手先读 §0.0 |
| `docs/cloud-cross-service-coupling-resolution.md` | 96 条耦合的逐条处置 + 每个 Phase 的落地记录（§8 = Phase 5） |
| `docs/cloud-service-decomposition-proposal.md` | **归属的唯一事实源**（§4.7 / §4.6.x）。认为某行判错 ⇒ 先改它再回写规则表 |
| `docs/real-machine-acceptance-backlog.md` | 簇 60 = 本批全部真机验收项（含 Phase 5 增补四条） |
| `CLAUDE.md` §8 | 拆仓期不变量，OVERRIDE 级 |

**openspec**：耦合处置这一路是**文档驱动**的，没有对应 change 需要回写 tasks。
但有三个相关 change 仍有未完成 task，接手时顺手确认它们是否已被本批工作覆盖：

```bash
openspec list | grep -E "cloud-service-boundary-gates|cloud-schema-migration-executor|fix-cloud-multi-service-deploy-script"
```

（2026-07-26 实测分别剩 8 / 6 / 1 条未勾。`cloud-schema-migration-executor` 的迁移执行器
本次实跑过一次 `status` / `up` / `verify`，工作正常且按属主分组正确。）

---

## 7. 诚实：本文没做到的事

- ~~**`applied` 那条成功路径没在真机上跑通过**~~ —— **2026-07-26 已补验**：§1 的缺陷修好后，
  那条积压命令在 dev 上自己跑完了，回读 `state=applied`（`risk_command_outcome` 里可查）。
- **三个仓一个都没真跑起来过**。全部验证停在编译期 + 单测 + 单体 dev 部署。
  「拆出去能不能起」只有写完 `main()` 才知道。
- **§2.1 的断裂数是静态扫描**，判据是相对 import 说明符能否解析到本仓文件。
  它**不覆盖动态 `import()`**——这次已经吃过一次亏（文字卡渲染的两个依赖是懒加载的，
  静态扫描看不见，差点被当多余依赖删掉，而那条链路**工厂返回 null 即降级**，装漏了不崩不报）。
  写 `main()` 时凡是「依赖/引用类审计」，MUST 把动态 `import()` 一起算进去。
