# tasks

> **先读 design.md §1 再动手**：cutover（第 5 节）是唯一串行段，前置＝所有触碰 cloud `src/` 的在飞 change 先 land + 用户显式点火。第 1–4 节可并行、可先落，全部落地也不改变任何现行行为（闸是 armed 不 enforcing）。
>
> 实测基线（2026-08-06，cloud@322472a）：受管 src 567（api 120 / automation 258 / content 80 / kernel 113 / transport 64 逐文件点名）；cloud test 文件 495，其中仅活在 cloud 的用例 ~134（08-05 实测：可搬 7 已搬走，跨属主 97、整图/迁移 24+、单体组装 5）；迁移残留 15。**这些数字随 fleet 增长，cutover 当天 MUST 重测，MUST NOT 照抄。**
>
> 并行纪律：控制仓提交只 stage 自己的路径（绝不 `-A`）；push 撞 non-ff 一律 rebase 重来，绝不 force。本批**不部署**（零运行时行为变化）。

## 1. 控制仓 — 换向闸（armed，本批落）

- [ ] 1.1 新增 `scripts/fact-source.json`：`{"flipped": false, "frozenCloudRef": null, "flippedAt": null}`，附一行注释性字段说明它由本 change 的 cutover 置位。
- [ ] 1.2 `scripts/sync-split-repos` 读标记：`flipped=true` 时 ① `--apply` / `--prune` 直接报错退出（指引到本 change）；② 默认模式转为冻结校验——`git -C ../aidcp-cloud diff --name-only <frozenCloudRef>..origin/master -- src/ migrations/` 非空即 exit 1 并列出文件。`flipped=false` 时行为逐字不变（在飞 change 还在用它）。
- [ ] 1.3 `scripts/task-preflight` 读标记：`flipped=true` 时新增检查——cloud 本地 checkout 的 `src/` `migrations/` 相对 frozenCloudRef 有 diff（含未提交）即 exit 1，输出「事实源已翻转，改到派生仓」。
- [ ] 1.4 变异验证两道闸（scratch 里翻开标记 + 故意改一个 cloud src 文件 → 两道闸都必须真的红；翻回确认绿；把验证过程记在本条注释里）。法条：闸恒真＝闸不在。

## 2. 共享包版本化（并行流 A，本批落）

- [ ] 2.1 `aidcp-kernel` / `aidcp-transport` 各打 annotated tag `v0.1.0` 于当前 master head（kernel 2fcbfdd / transport 416db19，执行时以当时 head 为准），push tag。
- [ ] 2.2 三个派生仓 `package.json` 钉子改为 `git+ssh://…#v0.1.0` 单一写法（**automation 的 transport 钉子现为 `github:` 简写且落后一位 sha——这就是要消灭的漂移实例**），重装依赖刷新 lockfile，`npm run typecheck` 三仓全绿。装完按 memory 法条核实 node_modules 里的 kernel 确为新引用（装到旧 sha 不报错）。
- [ ] 2.3 `sync-split-repos` 的 pin 检查改造：① 同时识别 `git+ssh://` 与 `github:` 两种写法，不认识的写法报错而非报「未 pin」；② 接受 tag 引用，经本地兄弟 checkout `git rev-parse <tag>^{}` 解析成 sha 比对；③ 翻转前要求解析到最新 tag（强度等价现行），翻转后落后只报告不报错。
- [ ] 2.4 登记：本项不部署（钉子解析到相同内容，零行为变化），随各服务下次正常部署自然生效。

## 3. 边界扫描器合并（并行流 B，本批落）

- [ ] 3.1 盘点：cloud 与 automation 两份扫描器逐行 diff，列出漂移点及各自语义；同时查 api / content 有无第三、四份副本。
- [ ] 3.2 合并为单一实现，落点默认 `aidcp-transport`（三家都要调、零属主 SQL，符合准入），cloud 与 automation 改薄壳引用；若盘点后发现更优落点，写明理由再改。
- [ ] 3.3 合并后两仓边界门禁全绿，且做一轮变异验证：故意违反一条边界规则，两边的门禁都要红（防「合并成谁都不跑的死代码」）。

## 4. 整图测试搬家 pilot（并行流 C，本批只产报告，cloud 零提交）

- [ ] 4.1 在 scratch worktree 里选 ≥6 个代表用例证明「兄弟仓直引」跑法，四类形态各至少一个：普通跨属主 / 把别属主源文件当数据读 / 迁移对齐（读三仓 migrations）/ 整图扫描。确定机制（tsconfig paths vs 相对路径）并跑绿。
- [ ] 4.2 产出 `openspec/changes/invert-split-fact-source/pilot-report.md`：跑法结论、codemod 草稿（可直接给 cutover 分桶执行）、已知坑清单、预计工作量修正。

## 5. CUTOVER（串行；前置＝触碰 cloud src 的在飞 change 全部 land ＋ 用户点火）

- [ ] 5.1 前置确认：`openspec list` 里无触碰 cloud `src/` 的在飞 change；`sync-split-repos` census 零漂移；重测头部基线数字。
- [ ] 5.2 置位 `fact-source.json`（frozenCloudRef=当时 cloud master sha）+ CLAUDE.md §8 头部加翻转声明（整节重写在 6.1）。此提交即点火。
- [ ] 5.3 按 pilot codemod 分桶并行改写 cloud test 全量引用，整图套件全绿。
- [ ] 5.4 删除 cloud `src/` 与 `migrations/`；`boundaries/` 归属清单转冻结历史记录（README 注明）；仓 README 自述改「集成测试仓」；整图套件在删除后的状态下再跑一遍全绿。
- [ ] 5.5 `sync-split-repos` 退役收尾：census 模式只剩冻结校验与 pin 报告；`--apply` 路径删除或永久封死。
- [ ] 5.6 「只测单体组装」的 5 个用例随单体死掉：删除并在本条注释记档。

## 6. 文档与脚本改指（cutover 后）

- [ ] 6.1 CLAUDE.md §8 整节重写为翻转后的模式（派生仓各自为政、cloud=集成测试仓、共享包版本化、新服务接入路径）。
- [ ] 6.2 控制仓引用 aidcp-cloud 的脚本逐一核对改指（08-05 盘点为 9 个，执行时重扫）：`protocol-parity` / `boundary-census` / `land-change` / `operation-registry-parity` 等。
- [ ] 6.3 memory 条目更新：`cloud-demoted-not-retired` 等涉及事实源方向的条目改写；本 change 结论入档。

## 7. 回滚路解绑（可与 5 并行准备，OL 演练等用户窗口）

- [ ] 7.1 写单服务回滚流程（解包上一版备份 + 重启该服务）进 `docs/deployment-environments.md`，在 dev 演练一次并记录。
- [ ] 7.2 单体最后备份包（dev / OL 各一）确认存在、写明日落日期；到期删除写进 backlog。
