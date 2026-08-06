# pilot-report — 整图测试搬家（任务 4，2026-08-06）

> 环境：scratch worktree `aidcp-cloud.wt/invert-split-fact-source`（cloud@322472a，`npm ci` 后实测），
> 兄弟仓 = 本机 canonical checkout（api / automation / content / kernel / transport 全部在位且已装依赖）。
> **cloud 零提交**：worktree 已删、分支已删；本报告是任务 4 的唯一落地物。
> 文中所有计数都是当场实测值，cutover 当天 MUST 重测。

## 1. 跑器事实（runner facts）

- **测试跑器 = `tsx --test`（Node 内置 test runner，经 tsx 加载 TS）**。单测 `npm test` = `tsx --test 'test/**/*.test.ts'`；验收 `npm run test:acceptance` = `tsx --test test/acceptance/*.test.ts`；PG 集成套件由 `AIDCP_PG_INTEGRATION=1` 门控。没有 jest / vitest，没有第二套 transform 配置。
- **ESM 全程**：`package.json` `"type": "module"`；测试内 import 一律带 `.js` 后缀（`from '../../src/comm/protocol.js'`），tsx 与 tsc（`moduleResolution: "Bundler"`）都做 `.js → .ts` 替换。
- **tsconfig**：`module: ES2022` / `moduleResolution: Bundler` / `strict`，单一 tsconfig 服务 build + typecheck + 测试；`include` 只有 `src/**` 与 `test/**`，但 tsc 会把 include 外的依赖文件照常拉进 program 全量检查。
- **兄弟仓对包依赖的解析**：派生仓源码里 `import 'aidcp-kernel/kernel/x.js'` 按 Node 语义从**该文件自己所在仓**的 `node_modules` 解析（kernel 包 exports 映射到 `dist/*.js` 编译产物）。因此**兄弟仓必须各自 `npm ci` 过**，这是 cloud 测试能跑的新增前置。

## 2. 机制定夺：tsconfig paths 胜出

**赢家：tsconfig `paths` 别名 + 双候选回退**（每属主一个别名，数组里两级相对路径先后尝试）：

```jsonc
// tsconfig.json compilerOptions 增量（cutover 时落地形态）
"baseUrl": ".",
"paths": {
  "@api/*":        ["../aidcp-api/src/*",        "../../aidcp-api/src/*"],
  "@automation/*": ["../aidcp-automation/src/*", "../../aidcp-automation/src/*"],
  "@content/*":    ["../aidcp-content/src/*",    "../../aidcp-content/src/*"],
  "@kernel/*":     ["../aidcp-kernel/src/*",     "../../aidcp-kernel/src/*"]
}
```

- tsx 与 tsc **都原生吃这份配置**（含数组回退与 `.js → .ts` 替换），实测零额外 loader / flag。
- **双候选回退实测有效**：worktree（`aidcp-cloud.wt/<change>/`，兄弟在 `../../`）里第一候选落空、第二候选命中，7 个用例照绿；canonical 布局命中第一候选（同一机制，无需改任何文件）。**这就是「路径深度陷阱」的解**：一份 tsconfig 同时活在两种布局，测试文件里不出现任何相对深度。
- 别名按**属主**命名而非按仓名，与归属表词汇一致，codemod 可直接用 `module-ownership.json` 查表生成。

**输家：裸相对路径**。实测把 canonical 深度的相对引用（`../../aidcp-kernel/src/...`）拿到 worktree 里跑：

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module
  '/Users/baitianxing/codes/aidcp-cloud.wt/aidcp-kernel/src/kernel/account-identity.js'
```

一份文本只能编码一种深度，canonical 与 `.wt` 必然一真一假；且 471 个文件里各 test 子目录深度不一（`test/x.test.ts` 与 `test/comm/x.test.ts` 的前缀不同），codemod 复杂度也更高。判负。

**运行时数据读取（非 import）另配一个 helper**：`test/helpers/sibling-repos.ts`，导出 `siblingRepoRoot(name)` / `ownedSourcePath(owner, srcRelPath)` / `BUSINESS_REPOS`。解析顺序 = `AIDCP_CODES_ROOT` env（与控制仓 `sync-split-repos` 同一约定）→ `仓根/../<name>` → `仓根/../../<name>`，命中判据是目标里有 `package.json`，落空**响亮抛错**（静默读到空树 = 假成功红线）。与 tsconfig 双候选是同一套语义，一个管编译期、一个管运行时。

## 3. 用例结果（7 个，四类形态全覆盖，最终合跑 139/139 全绿 + 全仓 typecheck exit 0）

| # | 形态 | 用例 | 跨到的仓 | 结果 |
| - | --- | --- | --- | --- |
| 1 | (a) 普通跨属主 | `test/acceptance/persona-mandatory.test.ts` | api+automation+kernel | **5/5 绿**（首跑即绿） |
| 2 | (a) 普通跨属主（最大广度） | `test/client-auth-server.test.ts` | api+automation+content+kernel 四仓 17 处 import | **86/86 绿** |
| 3 | (a) 红线验收 | `test/acceptance/protocol-contract.test.ts` | automation（AC-PROTO 指到 automation 仓的 protocol.ts） | **25/25 绿** |
| 4 | (b) 把别属主源文件当数据读 | `test/comm/host-standby-decision.test.ts` | import 走 automation+content；3 处 `readFileSync(new URL('../../src/…'))` 改经 `ownedSourcePath('automation', …)` | **12/12 绿** |
| 5 | (b) 数据读 + 归属表 | `test/agents/content-role-names.test.ts` | 角色类分居 automation 与 content 两仓、目录在 api；`boundaries/module-ownership.json` 留在 cloud（冻结史料）原样读 | **3/3 绿** |
| 6 | (c) 迁移对齐 | `test/schema/migration-numbering.test.ts` | 枚举三仓 `migrations/` 并集（见 §4） | **4/4 绿** |
| 7 | (d) 整图扫描 | `test/schema/ddl-parity.test.ts` | 三仓 `src/` 全树 DDL 对象 ∪ 三仓 `migrations/` ∪，单向包含断言不变 | **4/4 绿** |

合跑输出（7 文件一次进程，同时证明相互间无模块实例冲突）：

```
ℹ tests 139
ℹ pass 139
ℹ fail 0
```

全仓 `npx tsc -p tsconfig.json --noEmit` → exit 0（567 src + 505 test + 被拉入的兄弟仓源文件全量类型检查通过；tsconfig 需先做 §5-P1 的修正）。

## 4. 迁移并集的对账口径（形态 c 的 recipe）

当场实测：**cloud `migrations/` 112 个 = 三仓并集，两个方向零差集**。重叠（同名复制）：api∩automation 23、api∩content 19、automation∩content 18、三仓皆有 18；72+60+22−23−19−18+18 = 112。**所有复制副本与 cloud 原件逐字节一致**（sha256 全比对零漂移）。

并集加载器（已在用例 6 落地验证）的规则：

1. 逐仓调既有 `loadMigrationFiles(dir)`（显式传目录——该函数注释本就要求消费方显式传入，默认值只服务单体）；
2. **按文件名去重；同名副本 MUST 断言 checksum 相等**，不一致即红——复制迁移的漂移 = 共库历史被静默分叉，绝不能「保留其中一份」了事；
3. 并集按 `compareVersions(versionOf(name))` 复合序重排——四组历史同号碰撞的冻结顺序在并集上原样成立（用例 6 的断言未改一字就绿了）。

## 5. 已知坑（每条都是本次实测撞到或坐实的）

- **P1（会挡住 typecheck，cutover 必须处理）`rootDir` 与兄弟仓源文件冲突**：现行 tsconfig 有 `rootDir: "."`，paths 拉进来的兄弟仓文件全部触发 **TS6059**（`--noEmit` 也报）。修法 = 删 `rootDir` / `outDir` / `declaration`——cutover 后 cloud 是纯测试仓，`npm run build` 一并退役。删掉后实测 exit 0。
- **P2（本次差点误判）管道尾巴吃掉退出码**：`tsc … 2>&1 | tail` 的退出码是 `tail` 的 0，第一轮据此误记 typecheck 通过、实则 TS6059 一屏。cutover 的分桶验证命令 MUST 直接跑裸命令看退出码（或 `set -o pipefail`）。
- **P3 kernel 双实例是常态，且被 kernel 自己的准入豁免**：cloud 测试经 `@kernel/*` 读 aidcp-kernel 的 **src**，而兄弟仓源码经各自 `node_modules` 读 kernel 的 **dist**——同一契约两份模块实例。无害的依据是结构性的：kernel 准入禁模块级活状态（无 Set/Map/定时器/池），跨副本 `instanceof` 本就被 §8.5 明令改结构化守卫。**但 transport 成员没有这层豁免**（准入允许副作用）：owner 仓副本与 aidcp-transport 包副本并存，若测试同时经两条路触达同一 transport 成员且依赖模块级状态，会静默各玩各的。分桶执行时遇到 transport 成员相关断言异常，先查这一条。
- **P4 动态数据读逃逸 codemod 正则**：`readFileSync(new URL(\`../../${file}\`))` 这类变量路径改不动也报不出来，只能靠 §6 的清单兜住（当场实测 23 个文件带运行时 src/migrations 读取模式）。这 23 个文件 MUST 逐个人工过，机器只负责点名。
- **P5 单体组装测试该死不该搬**：13 个文件把 `src/server.ts`（composition，无继承者）**当数据读**（AST / 文本断言组装根接线；无一个是模块级 import——import 会把服务器拉起来）。这批与 tasks.md 5.6 的「只测单体组装」名单同源，处置 = 随单体死或改锚到三个派生服务入口（`*-service-entry.ts`），**绝不能机械 codemod**——把「单体组装根有没有接线 X」改写成读某个派生仓文件，断言就从「整机有 X」漂成「某仓有 X」，是语义级改判，须逐条人审。
- **P6 兄弟仓必须先 `npm ci`**：跨仓 import 在运行时依赖各兄弟仓自己的 `node_modules`（kernel/transport 包从那里解析）。本机全部在位所以零障碍；CI / 新机器上这是硬前置。另注意 memory 条目：派生仓 npm 装机有已知坑（git+ssh 钉子需要 SSH 凭据；ECS 上 `npm ci` 会清空 node_modules）。
- **P7 编译旗标耦合**：兄弟仓源文件被拉进 cloud 的 program 后按 **cloud 的旗标**重新全量检查。今天全绿（毕竟刚从同一单体机械重放出去）；各仓旗标独立演化后（例如某仓开 `exactOptionalPropertyTypes`、cloud 没开）会出现「owner 仓绿、cloud 红」的错位。报告结论：cloud 的旗标从此只能取三仓的**交集下界**，收紧前先跑整图。
- **P8 `boundaries/module-ownership.json` 留在 cloud 且继续可读**：转冻结史料后路径不动，读它的测试（用例 5）零改动。但 **AC-BOUND 整图边界门禁（`test/acceptance/module-boundary.test.ts` 家族）不搬**：cutover 后跨仓 import 物理上不存在，「单体 import 图上的方向执法」失去被测对象；边界执法住在各仓自己的扫描器（本 change 第 3 节正在合并实现）。该家族随 5.4/5.6 处置，**搬 = 给死图续命，白费工**。

## 6. codemod（供 cutover 5.3 分桶执行）

### 6.1 全量名单怎么拉

```bash
# 事实源 = 归属表 + import 解析，不 grep 字符串。census 脚本（≈40 行,见 6.2 附）当场输出:
#   - 引用 src/** 的 test 文件全集及每文件属主集合(单/多属主分桶的依据)
#   - 运行时数据读取嫌疑名单(readFile/readdir/new URL/migrationsDir/repoRoot 模式)
```

当场实测规模（cloud@322472a，cutover 当天重测）：test 树 505 个 .ts；**471 个文件共 1548 处 `src/**` import 指名**；多属主 232 文件 / 1021 处；运行时数据读嫌疑 23 文件；组装根数据读 13 文件（含在 23 里，与多属主有交集）。

**先裁剪、后改写**（顺序建议，能砍掉约一半工作量）：派生仓已各自携带测试（api 84 / automation 256 / content 71 个 test 文件），cloud 里单属主的 ~239 个文件是重放副本，**cutover 时直接删除而非改写**（它们的事实源测试在 owner 仓里跑）。改写只做剩下的多属主 + 整图 + 数据读集合（≈232 文件 + 23 的并集）。这一步需要用户 / cutover session 确认口径；若裁定「cloud 全量保留」，codemod 同样吃得下（1548 处，纯机械）。

### 6.2 机械改写脚本（pilot 实跑版，7 用例即由它改出）

```js
#!/usr/bin/env node
// codemod-repoint.mjs <cloudRepoRoot> [--dry] <file.ts> [...]
// 把相对 src/** import 改写为属主别名；composition 与 UNMAPPED 只报不改；
// 顺带点名 new URL 数据读。属主查 boundaries/module-ownership.json（冻结后仍在原路径）。
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';

const args = process.argv.slice(2).filter((a) => a !== '--dry');
const dry = process.argv.includes('--dry');
const ROOT = args[0];
const ownership = JSON.parse(readFileSync(join(ROOT, 'boundaries/module-ownership.json'), 'utf8'));
const ownerOf = new Map(ownership.map((e) => [e.path, e.layer]));
const SPEC_RE = /((?:from\s+|import\s*\(\s*|require\s*\(\s*|import\s+)['"])(\.[^'"]+)(['"])/g;

for (const file of args.slice(1)) {
  const abs = resolve(file);
  const text = readFileSync(abs, 'utf8');
  const notes = [];
  const out = text.replace(SPEC_RE, (whole, pre, spec, post) => {
    const rel = relative(ROOT, resolve(dirname(abs), spec));
    if (!rel.startsWith('src/')) return whole;
    const owner = ownerOf.get(rel.replace(/\.js$/, '.ts'));
    if (!owner) { notes.push(`UNMAPPED ${rel}`); return whole; }
    if (owner === 'composition') { notes.push(`COMPOSITION ${rel} — 5.6 名单，人工处置`); return whole; }
    const under = rel.replace(/^src\//, '').replace(/\.ts$/, '.js');
    notes.push(`${spec} -> @${owner}/${under}`);
    return `${pre}@${owner}/${under}${post}`;
  });
  for (const m of text.matchAll(/new URL\(\s*[`'"](\.\.\/)+(src\/[^'"`]+)/g))
    notes.push(`DATA-READ ${m[2]} — 改经 test/helpers/sibling-repos.ts`);
  console.log(`== ${relative(ROOT, abs)}`); notes.forEach((n) => console.log('   ' + n));
  if (!dry && out !== text) writeFileSync(abs, out);
}
```

映射规则：`api|automation|content|kernel → @<owner>/<src 下路径>.js`（kernel 仓 src 与单体同构，`src/kernel/x.ts → @kernel/kernel/x.js`、`src/deployment-target.ts → @kernel/deployment-target.js`，已实测）；`composition` → 不改、进 5.6 名单；查不到 → 响亮报出。**前提已验证：567 个受管 src 文件在属主仓同路径全部存在（0 缺失）**。

### 6.3 一次性配套（cutover 开场先落，再开分桶）

1. tsconfig：加 `baseUrl` + 四条 paths（§2 形态），**同一提交删 `rootDir`/`outDir`/`declaration` 与 `build` script**（P1）；
2. 落 `test/helpers/sibling-repos.ts`（§2 末段；pilot 版全文可从本报告直接抄，语义 = AIDCP_CODES_ROOT → `../` → `../../`，落空抛错）；
3. 用例 6/7 的并集加载器（§4 规则）随其所在文件落地，其他迁移/DDL 类测试引用同一 helper，不许每处自摊一份并集逻辑。

### 6.4 分桶与每桶验证

- **桶按 test 子目录切**（`test/acceptance`、`test/agents`、`test/comm`、`test/config`、`test/schema`、其余根级平摊），桶间无共享文件、可并行 agent 各领一桶；`tsconfig`/helper 是唯一热点，按 6.3 先行落地后各桶零冲突。
- 每桶验证命令（P2：裸跑看退出码，勿接管道）：
  1. `npx tsx --test <该桶全部文件>` → 全绿；
  2. `npx tsc -p tsconfig.json --noEmit` → exit 0（全仓，兜跨桶类型回归）；
  3. `grep -rn "\.\./src/\|\.\./\.\./src/" <桶> --include='*.ts'` → 零命中（改写无遗漏；数据读 23 文件除外，逐个人工销号）。
- 收尾整图验证 = `npm test`（此时 `src/` 尚在）→ 删 `src/` + `migrations/` → **再跑一遍全绿**（5.4 的顺序，删除后那遍才是真验收——`src/` 还在时任何漏改都被本仓副本静默兜住，绿得没有意义）。

## 7. 工作量修正（5.3 原口径 ≈130 用例）

| 项 | 量（当场实测） | 定性 |
| --- | --- | --- |
| 机械改写 | 232 多属主文件 / 1021 处指名（若不裁剪则 471/1548） | codemod 秒级；桶验证占大头 |
| 单属主裁剪 | ~239 文件删除 + 与 owner 仓副本对账 | 新增工序（原口径没有这一步）；对账可脚本化（文件名 + 内容 diff） |
| 数据读人工 | 23 文件（P4） | 每个 5–20 分钟 |
| 组装根处置 | 13 文件（P5，与上有交集） | 逐条人审改锚或判死，最重的一类 |
| 一次性配套 | tsconfig + helper + 并集加载器（6.3） | 半小时内，已有 pilot 成品 |
| 门禁家族处置 | AC-BOUND 整图门禁不搬（P8）+ 5.6 名单 | 判死写档，不是搬家工 |

**修正结论**：「~130 用例」低估了指名规模（多属主口径就有 232 文件 / 1021 处），但机械部分完全 codemod 化后不构成瓶颈；真实成本集中在**三类人工**——单属主裁剪对账、23 个数据读、13 个组装根判死/改锚。按 6.4 分桶（6 桶并行 + 一人收尾整图），估 **1 个并行 fleet 工作日**（原先按 130 逐个手改的想象大约也是一天，但构成完全不同：那种估法会漏掉裁剪与组装根这两块最重的活）。前置硬条件：兄弟仓全部在位且 `npm ci` 过（P6）。

## 8. pilot 遗留物处置

- scratch worktree 与分支已删（`git worktree list` 已核实无残留），canonical cloud 未被触碰；
- 本报告是任务 4 唯一落地物；pilot 里改过的 7 个测试文件 + tsconfig + helper 的最终形态都以「随 worktree 一起销毁、内容收进本报告」处置——cutover 时按 §6 重放，不依赖任何未提交状态。
