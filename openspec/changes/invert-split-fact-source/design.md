# design — invert-split-fact-source

## 0. 一句话

把「cloud 复制代码给三个服务」倒过来：三个服务各自当家，cloud 退休成考场。真正要杀的只是「重放」这一半身份；整图验证这一半不但保留，还是唯一合法身份。

## 1. 为什么 cutover 必须是一次性的、且在它之前批量改动不能落地

**两个事实源并存是本仓最怕的状态**：一段代码在两处都能改、谁覆盖谁取决于谁后跑一次同步。所以翻转必须原子——翻转前重放模式完整有效，翻转后立即失效，没有「一半仓转正了」的中间态。

**整图测试的批量改引用（③）不能先于翻转落地**，原因是测试语义：现行模式下，session 改 cloud 源码后跑 cloud 测试来验证改动。若测试已改为引用兄弟仓源码，它测到的是「上次同步过去的旧代码」，session 刚写的改动不在被测范围内——对约 10 个在飞 change 是静默的验证失效。因此 cutover 前只做 pilot（scratch worktree，证明跑法、产出 codemod，不落地）。

## 2. 换向闸的形态：armed / enforcing 两态

- 标记文件 `scripts/fact-source.json`：`{"flipped": false, "frozenCloudRef": null}`。cutover 时改为 `{"flipped": true, "frozenCloudRef": "<当时 cloud master sha>"}`，一行提交即点火。
- `sync-split-repos`：读标记。未翻转＝行为完全不变；已翻转＝`--apply` / `--prune` 直接报错退出（指引到本 change），默认 census 模式改为**冻结校验**：`git diff frozenCloudRef..origin/master -- src/ migrations/` 非空即 exit 1 并列出文件。
- `task-preflight`：已翻转时新增一道检查——cloud 本地 checkout 的 `src/` `migrations/` 相对 frozenCloudRef 有改动即 exit 1，指引「改到派生仓去」。它挂在 fleet 全部新任务的入口上，是防「有人还按旧模式开工」的主闸。
- **闸落地即变异验证**（法条：闸恒真=闸不在）：在 scratch 里翻开标记、故意改一个 cloud src 文件，两道闸必须真的红；再翻回去确认绿。
- 已知覆盖缺口（与 task-preflight 自身的缺口相同，不在本 change 修）：手动 `git worktree add`、`/impl` 复用已有 worktree 的路径绕过准入闸。兜底靠 CLAUDE.md §8 重写 + sync 脚本自身的拒绝。

## 3. 共享包版本化的规则

- kernel / transport 各打 annotated tag（起点 `v0.1.0` 于当前 head），此后每次改动出新 tag。
- 三仓钉子统一为 `git+ssh://git@github.com/tommax-bai/<pkg>.git#v<x.y.z>` 单一写法。**检查器必须同时认得 `git+ssh://` 与 `github:` 简写两种历史形态**——本次漂移（automation 钉 transport 落后一位）之所以不可见，正是检查器把不认识的写法报成「未 pin」。不认识的写法今后必须是错误，不是沉默。
- 翻转前：钉子必须解析到最新 tag（等价于现行「恒等于 head」的强度，靠本地兄弟 checkout `git rev-parse <tag>^{}` 解析，不走网络）。
- 翻转后：钉子必须是存在的 tag；落后于最新只**报告**（谁落后几版），不报错。升级是各仓自己的决定。

## 4. 整图测试搬家的跑法（pilot 要证明的）

- 目标形态：cloud 的 test 直接 import 兄弟仓源码（同级目录布局是既有前提，`sync-split-repos` 已用同样方式跨仓跑 TypeScript）。候选机制：tsconfig paths（`@api/*` → `../aidcp-api/src/*`）或相对路径直引，由 pilot 定夺并写进 recipe。
- 代表用例必须覆盖四类已知形态：① 普通跨属主用例；② 「把别的属主的源文件当数据读」的用例（约 10 个，import 图看不见，搬家时 `ENOENT` 现形）；③ 迁移对齐类（要读全部三仓的 `migrations/` 目录）；④ 整图扫描类（协议穷举 / 边界扫描）。「只测单体组装」的 5 个用例在 cutover 时随单体死掉，记档不搬。
- pilot 产出：`pilot-report.md`（跑法结论 + 已知坑）+ codemod 草稿（供 cutover 分桶并行执行）。**pilot 不在 cloud 落任何提交。**

## 5. cutover 之后 cloud 仓里留下什么

- `test/`（整图用例，已改指兄弟仓）+ 跑它们所需的构建链（package.json / tsconfig / fixtures）。
- `boundaries/` 的归属清单转为**冻结的历史记录**（重放输入这个身份随重放一起退役；属主归属的事实源仍是控制仓 §4.7，边界执法在各仓自己的扫描器）。细节由 cutover session 按当时状态定夺，原则：不留任何「看起来还活着」的机制。
- `src/` 与 `migrations/` 删除。README 自述改为「集成测试仓」。

## 6. 回滚路

- 现状：OL 唯一回滚路＝重新 enable 单体（§8.0 定为用户显式动作)。翻转后单体连代码都没了，这条路必须先换掉。
- 新形态：每个派生服务部署序列本就先备份（`/opt/aidcp/<svc>.bak.<ts>.tar.gz`），回滚＝解包上一版 + 重启该服务，逐服务独立。文档化 + 在 dev 演练一次。
- 单体最后一份备份包（两环境各一）留档、写明日落日期；过期即删，从此回滚词典里没有「单体」。

## 7. 不做与阶段二

- **不拆数据库**：共库是产品约束（DEV/OL 靠 `execution_target` 隔离），且「一个域绝不直连另一个域的库」的闸已在。
- **不新建仓**：集成测试场＝cloud 仓瘦身，构建链 / fixtures / git 历史都是现成的。
- **迁移链拆编号**（各仓独立编号 + 共享表边界交叉校验）：阶段二另行立项。硬约束先记下：已应用迁移字节不可改，只能「从今往后分叉」，不能回头重编历史。
