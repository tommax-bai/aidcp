# tasks

> **先读 design.md §1 再动手**：cutover（第 5 节）是唯一串行段，前置＝所有触碰 cloud `src/` 的在飞 change 先 land + 用户显式点火。第 1–4 节可并行、可先落，全部落地也不改变任何现行行为（闸是 armed 不 enforcing）。
>
> 实测基线（2026-08-06，cloud@322472a）：受管 src 567（api 120 / automation 258 / content 80 / kernel 113 / transport 64 逐文件点名）；cloud test 文件 495，其中仅活在 cloud 的用例 ~134（08-05 实测：可搬 7 已搬走，跨属主 97、整图/迁移 24+、单体组装 5）；迁移残留 15。**这些数字随 fleet 增长，cutover 当天 MUST 重测，MUST NOT 照抄。**
>
> 并行纪律：控制仓提交只 stage 自己的路径（绝不 `-A`）；push 撞 non-ff 一律 rebase 重来，绝不 force。本批**不部署**（零运行时行为变化）。

## 1. 控制仓 — 换向闸（armed，本批落）

- [x] 1.1 新增 `scripts/fact-source.json`：`{"flipped": false, "frozenCloudRef": null, "flippedAt": null}`，附一行注释性字段说明它由本 change 的 cutover 置位。
<!-- aidcp 2e476740 -->
- [x] 1.2 `scripts/sync-split-repos` 读标记：`flipped=true` 时 ① `--apply` / `--prune` 直接报错退出（指引到本 change）；② 默认模式转为冻结校验——`git -C ../aidcp-cloud diff --name-only <frozenCloudRef>..origin/master -- src/ migrations/` 非空即 exit 1 并列出文件。`flipped=false` 时行为逐字不变（在飞 change 还在用它）。
<!-- aidcp 2e476740。标记从脚本自身目录读、不受 AIDCP_CODES_ROOT 影响（标记与读它的代码必须同版本）；
     frozenCloudRef 先 rev-parse 验存在，不存在时响亮失败而非静默通过。 -->
- [x] 1.3 `scripts/task-preflight` 读标记：`flipped=true` 时新增检查——cloud 本地 checkout 的 `src/` `migrations/` 相对 frozenCloudRef 有 diff（含未提交）即 exit 1，输出「事实源已翻转，改到派生仓」。
<!-- aidcp 2e476740。覆盖三种漂移：已提交（diff ref）、未提交（diff 工作区）、未跟踪（ls-files --others）。
     cloud 未 clone 时 SKIP（与本闸其余检查同待遇）。 -->
- [x] 1.4 变异验证两道闸（scratch 里翻开标记 + 故意改一个 cloud src 文件 → 两道闸都必须真的红；翻回确认绿；把验证过程记在本条注释里）。法条：闸恒真＝闸不在。
<!-- 2026-08-06 实测四个变异全部按预期响：① flipped + 落后 30 提交的 frozenCloudRef → census exit 1、
     列出 54 个受冻结文件；② flipped + --apply → 拒绝 exit 2；③ flipped + frozenCloudRef=当前头 →
     census exit 0「冻结校验通过」；④ 本地给 cloud src/server.ts 追加一行 → task-preflight exit 1
     并点名文件，revert 后 exit 0。翻回 flipped=false 后 census / preflight 行为与基线逐字一致。 -->

## 2. 共享包版本化（并行流 A，本批落）

- [x] 2.1 `aidcp-kernel` / `aidcp-transport` 各打 annotated tag `v0.1.0` 于当前 master head（kernel 2fcbfdd / transport 416db19，执行时以当时 head 为准），push tag。
<!-- kernel v0.1.0 → 2fcbfdd5a919 / transport v0.1.0 → 416db19b9fe5，均 annotated 且已 push。 -->
- [x] 2.2 三个派生仓 `package.json` 钉子改为 `git+ssh://…#v0.1.0` 单一写法（**automation 的 transport 钉子现为 `github:` 简写且落后一位 sha——这就是要消灭的漂移实例**），重装依赖刷新 lockfile，`npm run typecheck` 三仓全绿。装完按 memory 法条核实 node_modules 里的 kernel 确为新引用（装到旧 sha 不报错）。
<!-- api d32e7ea / automation 596c2c0 / content 5a8ea52。memory 警告的坑真踩到了：automation 首次
     npm install 把 transport 的 resolved 静默留在旧 761b9bd，npm update 后复核才落到 v0.1.0；
     三仓 lockfile resolved 均 = tag 目标 sha，node_modules 内容 byte-match tag 内容，typecheck 3/3。
     偏离（api 内合理扩围）：两个守卫测试原样断言「40 位 sha 钉子」字面形态、在 tag 钉子下假红，
     改为断言下一层不变量（canonical git+ssh#v<semver> 形态 + lockfile 解析 sha 相等 + 共享包全仓唯一实例）。 -->
- [x] 2.3 `sync-split-repos` 的 pin 检查改造：① 同时识别 `git+ssh://` 与 `github:` 两种写法，不认识的写法报错而非报「未 pin」；② 接受 tag 引用，经本地兄弟 checkout `git rev-parse <tag>^{}` 解析成 sha 比对；③ 翻转前要求解析到最新 tag（强度等价现行），翻转后落后只报告不报错。
<!-- aidcp 83eb9671。变异三连全响：file: 写法→点名仓+行报错；过期 sha→「pin 过期」；解析不了的
     tag→指引 fetch --tags。超计划完成一块：翻转态的宽松报告（pin=存在的 tag、落后只列名）已随本条
     实装在翻转早退路径里（report_flipped_pins），5.5 的这部分等于预做。census 复跑：三仓两包
     pin 全部「对齐（v0.1.0 → sha）」，automation 不再报「未 pin」。 -->
- [x] 2.4 登记：本项不部署（钉子解析到相同内容，零行为变化），随各服务下次正常部署自然生效。
<!-- 确认未部署。census 仍 exit 1 来自既有的「组装根不同 2」（只报不改的常态），与 pin 无关。 -->

## 3. 边界扫描器合并（并行流 B，本批落）

- [x] 3.1 盘点：cloud 与 automation 两份扫描器逐行 diff，列出漂移点及各自语义；同时查 api / content 有无第三、四份副本。
<!-- 全量盘点见 scanner-merge-report.md（aidcp 8f7ae77a）。api / content 零副本。真漂移只有一处语义：
     classifyEdge 对「组装根→组装根」内部边的判序两边相反（automation 允许＝正确且有测试，cloud 判禁
     ＝与自己文档矛盾）。两份 boundary-record.ts 是设计上不同的程序（refresh 生成器 vs 派生 census），
     不是副本对、不合并。 -->
- [x] 3.2 合并为单一实现，落点默认 `aidcp-transport`（三家都要调、零属主 SQL，符合准入），cloud 与 automation 改薄壳引用；若盘点后发现更优落点，写明理由再改。
<!-- 偏离（有理由，见报告）：transport 落点在翻转前结构性走不通——扫描器活在 test/（transport 点名只
     重放 cloud src/）、REPO_ROOT 按模块自身位置解析。改为：语义对齐到 byte-identity（以派生侧裁定为准，
     保护性规则零放松；cloud e5db151 / automation bf015f7）+ 两仓各装防再漂移 parity 闸（只改一边立刻红，
     兄弟 checkout 缺失时如实报「没能确认」不报「一致」）。结构性单一落点合并推迟到 cutover（见 5.7）。 -->
- [x] 3.3 合并后两仓边界门禁全绿，且做一轮变异验证：故意违反一条边界规则，两边的门禁都要红（防「合并成谁都不跑的死代码」）。
<!-- cloud test:acceptance 198/198、automation 298/298、双侧 typecheck 与 census 全绿。三个变异全响：
     M1 cloud 越界边→AC-BOUND-04 红并点名；M2 automation 同形→census 非零退出；M3 单侧改扫描器
     →两仓 parity 闸同时红。各自 revert 后复绿。 -->

## 4. 整图测试搬家 pilot（并行流 C，本批只产报告，cloud 零提交）

- [x] 4.1 在 scratch worktree 里选 ≥6 个代表用例证明「兄弟仓直引」跑法，四类形态各至少一个：普通跨属主 / 把别属主源文件当数据读 / 迁移对齐（读三仓 migrations）/ 整图扫描。确定机制（tsconfig paths vs 相对路径）并跑绿。
<!-- 7 个代表用例覆盖全部四类形态，合跑 139/139 绿 + tsc --noEmit exit 0。机制定夺：tsconfig paths
     双布局 fallback 数组（"@api/*": ["../aidcp-api/src/*","../../aidcp-api/src/*"]），canonical 与
     .wt worktree 零文件差异各自可解析；相对路径方案实证出局（一种写法编码不了两种布局深度）。
     运行时数据读取走新 helper（AIDCP_CODES_ROOT → ../ → ../../，找不到响亮失败）。
     cloud 零提交，worktree 与分支已拆净，canonical 干净停 master。 -->
- [x] 4.2 产出 `openspec/changes/invert-split-fact-source/pilot-report.md`：跑法结论、codemod 草稿（可直接给 cutover 分桶执行）、已知坑清单、预计工作量修正。
<!-- aidcp e11ac106。改写 cutover 计划的关键发现：① 先删后搬——cloud 里 ~239 个单属主用例在派生仓
     已有复制（411 个复制测试文件），该删不该搬，砍掉一半改写量（剩 232 文件 / 1021 说明符，全可
     codemod）；② 迁移并集干净精确（cloud 112 = 72+60+22 去重，复制件全 byte-identical；配方=按文件名
     去重 + 断言校验和一致）；③ 23 个动态数据读取文件 codemod 够不着、只能点名人工；13 个组装根
     数据读取用例须裁决「死或重锚」；AC-BOUND 整图边界闸不搬（并集 import 图随单体消失）；
     ④ tsconfig 撤 rootDir/outDir 须与 paths 同一提交，验证命令不得管到 tail（吃掉 tsc 退出码）。
     工作量修正：≈1 个车队并行工作日（6 个目录桶 + 1 个整图收口），硬前置=兄弟仓全部 npm ci 就绪。 -->

## 5. CUTOVER（串行；前置＝触碰 cloud src 的在飞 change 全部 land ＋ 用户点火）

- [x] 5.1 前置确认：`openspec list` 里无触碰 cloud `src/` 的在飞 change；`sync-split-repos` census 零漂移；重测头部基线数字。
<!-- 偏离（用户裁定 2026-08-06）：「在飞 change 清场」这条前置被用户显式豁免——「我们直接改，不等他们了」。
     替代处置＝给 6 个仍有 cloud 侧任务的在飞 change（drop-dead-cloud-edge-commands /
     cloud-schema-migration-executor / browser-slot-scheduling / restore-native-facebook-residual-parity /
     close-account-layer-operation-manual / publish-approval-signal-to-database）逐个在 tasks.md 顶部
     写入改道说明（cloud 侧任务改落属主派生仓）。census 零漂移已核（cloud@2d34e06，受管 src 566）；
     基线重测：test 508 文件 / 引用 src 478 / 单属主可裁剪 233 / 待改写 245（内含数据读 38）。 -->
- [x] 5.2 置位 `fact-source.json`（frozenCloudRef=当时 cloud master sha）+ CLAUDE.md §8 头部加翻转声明（整节重写在 6.1）。此提交即点火。
<!-- aidcp fe4914f1，frozenCloudRef=2d34e06、flippedAt=2026-08-06。点火后三道闸实弹核验：census=
     「冻结校验通过」+ 翻转态 pin 报告正常（transport 已被车队按新规矩发到 v0.1.1 并被正确识别）、
     --apply 拒绝 exit 2、task-preflight exit 0。cloud 侧基建随后落地（cloud 412b1d6：tsconfig 属主别名
     双布局回退 + 撤 rootDir/outDir/declaration + 退役 build script + test/helpers/sibling-repos.ts +
     scripts/codemod-repoint.mjs），未触碰冻结目录。 -->
- [ ] 5.3 按 pilot codemod 分桶并行改写 cloud test 全量引用，整图套件全绿。（pilot 定稿的执行序：**先删后搬**——先删 ~239 个派生仓已复制的单属主用例并对账，再 codemod 改写 232 文件 / 1021 说明符；23 个动态数据读取文件人工处理、13 个组装根数据读取用例逐条裁决；tsconfig paths + 撤 rootDir 同一提交；数字以当天重测为准。）
- [ ] 5.4 删除 cloud `src/` 与 `migrations/`；`boundaries/` 归属清单转冻结历史记录（README 注明）；仓 README 自述改「集成测试仓」；整图套件在删除后的状态下再跑一遍全绿。
- [ ] 5.5 `sync-split-repos` 退役收尾：census 模式只剩冻结校验与 pin 报告；`--apply` 路径删除或永久封死。（pin 报告那半已随 2.3 预做——翻转早退路径里已有宽松版 pin 报告；本条剩「删/封 --apply 代码路径」与收掉重放专用逻辑。）
- [ ] 5.6 「只测单体组装」的 5 个用例随单体死掉：删除并在本条注释记档。
- [ ] 5.7 边界扫描器结构性收口（3.2 递延项，细节见 scanner-merge-report.md）：cloud src 删除后 automation 侧副本成为唯一实现，撤下两仓 parity 闸；若 api / content 届时需要该闸，先把 REPO_ROOT 改成可注入再进 transport。同时裁决报告记录的 record 层不对称（派生侧 census 只拦 forbidden、不带棘轮）与三条既存 `--tests` 多出条目。

## 6. 文档与脚本改指（cutover 后）

- [ ] 6.1 CLAUDE.md §8 整节重写为翻转后的模式（派生仓各自为政、cloud=集成测试仓、共享包版本化、新服务接入路径）。
- [ ] 6.2 控制仓引用 aidcp-cloud 的脚本逐一核对改指（08-05 盘点为 9 个，执行时重扫）：`protocol-parity` / `boundary-census` / `land-change` / `operation-registry-parity` 等。
- [ ] 6.3 memory 条目更新：`cloud-demoted-not-retired` 等涉及事实源方向的条目改写；本 change 结论入档。

## 7. 回滚路解绑（可与 5 并行准备，OL 演练等用户窗口）

- [ ] 7.1 写单服务回滚流程（解包上一版备份 + 重启该服务）进 `docs/deployment-environments.md`，在 dev 演练一次并记录。
<!-- 文档半已落（本仓，与本批 tasks 同提交）：新增「Rollback（逐服务）」节（备份定位 / 单写者
     stop-then-start / .env 放回 / 契约门通过行 / 账本超前放行），并顺手把 08-04 的 dev/ol 形态表
     修正到 08-05 之后的现实（两环境都是派生三服务、单体 disabled+inactive 于 dev 实测）。
     dev 演练待 cutover 窗口一并做——fleet 活跃时段重启 dev 服务会打断在跑的边缘会话。 -->
- [ ] 7.2 单体最后备份包（dev / OL 各一）确认存在、写明日落日期；到期删除写进 backlog。
<!-- dev 侧已核：/opt/aidcp/ 下单体 tar 备份 165 个、aidcp-cloud.service disabled+inactive（2026-08-06
     实测）。OL 侧确认与日落日期定夺留待 cutover。 -->
