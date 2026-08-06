# 边界扫描器合并报告（任务 3 · 2026-08-06）

落地提交：aidcp-cloud `e5db151` / aidcp-automation `bf015f7`（均已推 origin/master）。
基线：cloud `322472a` / automation `7791de9`。本批不部署、零运行时行为变化（只动 test/）。

## 1. 盘点（3.1）

| 副本 | 行数 | 接线 |
| --- | --- | --- |
| `aidcp-cloud/test/acceptance/helpers/boundary-scan.ts` | 1046→1047 | 被 5 个验收测试 import（`module-boundary`（AC-BOUND-01..06 + 两组保真自检）、`table-ownership`、`row-lock-ownership`、`cross-owner-schema-probe`、`sync-read-inventory`）+ `boundary-record.ts`（`npm run boundaries:refresh / boundaries:census`）|
| `aidcp-automation/test/acceptance/helpers/boundary-scan.ts` | 1047 | 被 `boundary-record.test.ts`、`cross-owner-foreign-keys.test.ts` import + 自己的 `boundary-record.ts`（同名 npm scripts）|
| aidcp-api / aidcp-content | — | **无副本**（按 `*boundar*` 全文件名扫 + 全文 grep，零命中）|

automation 副本的来历坐实了漂移机理：`13de4f2` 从 cloud@`8d903dd` 机械同步而来，`f21bd74` 就地改判向，
且文件带 `aidcp:test-owner=derived` 标记 = **派生私有、被测试同步对账排除** —— 从那一刻起没有任何机械
手段会报两份不一致。这正是本任务要关掉的洞。

**非副本对（不合并，留档）**：两仓的 `boundary-record.ts` 同名但**是两个程序**——cloud 442 行
（refresh 全量重算 + 棘轮 / raise / reseed 通道），automation 109 行（派生 census，只拦 forbidden）。
不存在「同一实现的漂移」，不纳入份际闸。

## 2. 漂移表与裁定（3.1）

| # | 漂移点 | cloud 侧 | automation 侧 | 裁定 |
| --- | --- | --- | --- | --- |
| 1 | `classifyEdge` 判序 | `to==='composition'` 先判 → composition→composition = **forbidden** | `from==='composition'` 先判 → **allowed**（注释明写「包含 composition 内部的组合根拆分」）| **派生侧为准**。automation 组合根实际拆成 6 个文件互引（`automation-main` / `automation-service-entry` / `automation-composition-root` / …），改判是有意为之且有测试钉住；两侧文档注释都写着「同层内部恒允许」，cloud 实现顺序与自家注释自相矛盾；cloud 现存 composition 仅 2 文件（`index.ts` / `server.ts`）且零互引边 → 采纳后 cloud 当前判决**零变化**。反向保护一条没松：业务层 / kernel → composition 恒 forbidden、kernel → 业务层恒 forbidden，两侧本就一致，且现在两仓各有一条真值表测试把它钉死（此前 cloud 对 classifyEdge 没有任何直接断言）。|
| 2 | 头注 `aidcp:test-owner=derived` 标记行 | 无 | 有 | **保留差异**（机制需要：标记 = 派生私有）。份际闸把归属标记行列为唯一合法差异。|
| 3 | 「composition MAY →」注释文案 | 旧 | 新 | 随 #1 采纳派生侧。 |

除上述外两份逐字一致（合并后 `diff` 唯一输出 = 标记行）。

## 3. 路径选择（3.2）：语义并齐 + 双向份际闸，结构性合并推迟到 cutover

tasks.md 3.2 的默认落点是 aidcp-transport。盘点后判定翻转前走包落点不干净，理由（按「不改的代价」排序）：

1. **扫描器活在 `test/`、不在 `src/`**：transport 逐文件点名只回放 cloud `src/` 文件。要走包就得先把
   1047 行搬进 src/ —— 新增归属裁决、让扫描器扫它自己，而 cutover 5.4 马上要删 cloud src/，这些都是
   即弃工程。
2. **`REPO_ROOT` 按模块自身位置上三层解析**（`boundary-scan.ts:16`）。装进包后会解析到 node_modules
   深处、指错仓。改成注入式仓根＝重写门禁自身的路径机制——正当目标是消灭漂移时，最不该做的就是
   顺手重构被守卫的东西。
3. **消费耦合正在飞**：automation 的 transport 钉子迁移 v0.1.0 是另一 session 的在飞任务（其
   package.json 工作区 WIP 实测在场、未提交）。此刻往 transport 塞新文件要切 v0.1.1 并追改消费方钉子，
   徒增碰撞、零门禁收益。
4. **cutover 本来就是指定唯一副本的自然时点**：5.4 之后 cloud src/ 删除、`boundaries/` 冻结，扫描器的
   唯一现役家自然落在派生侧。现在结构性合并等于对一个注定要动的落点做两次搬家。

**实际落地**：
- cloud `e5db151`：`classifyEdge` 并齐派生侧判序（漂移点 #1/#3）+ 新增 `test/acceptance/boundary-scan-parity.test.ts`。
- automation `bf015f7`：同名份际闸镜像（带 `aidcp:test-owner=derived` 标记）。

**份际闸机制**：两仓各持一份同名测试（互为镜像、把自身也纳入比对，改闸必须两边同批改）；按
`package.json.name` 定向对照（cloud↔automation；未来若 api / content 出现第三份，其副本自动对照事实源
cloud）；兄弟 checkout 逐级向上解析，主 checkout（`codes/<repo>`）与 worktree（`codes/<repo>.wt/<change>`）
布局都可达；比对以「归属标记行」为唯一豁免。找不到兄弟 checkout 时 `skip` 并明说「没能确认」——三态诚实，
不把「没比成」报成「比过且一致」；fleet 布局下两仓恒同级在场，且闸是双向的，单侧缺席由对面补位。

## 4. 验证（3.3 + 变异）

绿态（合并后）：
- 两份 `boundary-scan.ts` `diff` 唯一输出 = ` * aidcp:test-owner=derived`。
- cloud：AC-BOUND 全家 + 保真自检 16/16；扫描器其余 4 个 importer 测试 29/29；`test:acceptance` 全量
  **198/198**；`boundaries:census` 567/567、跨层违规 0；`typecheck` 过。
- automation：parity + boundary-record 6/6；`test:acceptance` 全量 **298/298**；census
  `source=282 … forbidden=0`；`typecheck` 过。
- 控制仓 census：src 侧无新增漂移（transport 64/64 · 多出 0）；`--tests` 对账新文件计入「派生私有 43」、
  未新增「多出」。

变异（每条都先见红、revert 后复绿）：
- **M1 cloud 门禁真跑**：给 `src/risk/risk-state-machine.ts` 加一条对 `src/server.ts` 的 import
  （automation→composition）→ `AC-BOUND-04` 红并点名
  `src/risk/risk-state-machine.ts -> src/server.ts (automation->composition)`；census 报「无豁免通道 1 条」。
  revert 后 12/12 绿。
- **M2 automation 门禁真跑**：给 `src/automation-business-config.ts` 加同型 import → census 子进程非零
  退出并点名边；验收测试「census executable exits zero」红。revert 后复绿。
- **M3 份际闸双向**：automation 侧 `boundary-scan.ts` 追加一行 → **两仓**的 parity 测试各自红、各自点名
  漂移文件与对侧仓名。revert 后两侧 2/2 绿。

M1/M2 同时证明合并后的实现就是两仓门禁实际执行的那一份（不是谁都不跑的死代码）；M3 证明再漂移
不再沉默。

## 5. 留给 cutover 的清单

1. **结构性合并本体**（cutover 5.4 时）：cloud src/ 删除、boundaries/ 冻结后，把 automation 副本立为唯一
   现役实现；cloud 侧副本与份际闸随仓降级一并处置（删除，或改为对照冻结 ref 的历史校验）。若届时决定
   api / content 也要跑边界门禁而走 aidcp-transport，**先做且只需做一件结构改造：`REPO_ROOT` 从模块位置
   推导改为注入式仓根**（`boundary-scan.ts:16`），再按点名清单入包。
2. **record 层不对称留档**：automation 的派生 census 只拦 forbidden，`exemptable`（现值 8）只报数、不对账
   豁免清单；cloud 侧有完整棘轮。派生侧要不要棘轮，随 cutover 一并裁，本批不扩权。
3. **与本任务无关的既有 `--tests` 多出 3 条**（`outbox-retention-coverage` / `served-route-inventory` /
   `sync-read-refresh-margin`，归属重判残留）：待人工确认删除，本批未动。
