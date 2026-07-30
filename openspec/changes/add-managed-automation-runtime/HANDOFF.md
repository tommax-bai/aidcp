# `add-managed-automation-runtime` 下一 session 交接

> 快照时间：**2026-07-30 17:36 +0800**。
>
> 这份文档用于继续现有 change 和两个现有 worktree。接手后先重跑 §0 的只读核查，
> 不要把本文的 SHA、ahead/behind 或测试数字当成不会变化的事实。
>
> **当前边界不是“整个 change 已完成”**。Qoder 任务板所称“期 1 完成”表示第一批源码骨架和
> 测试已形成 11 个 Cloud 提交；OpenSpec 的真实进度是 **3/111**，没有集成、推送或部署。

---

## 0. 接手第一件事

从 canonical control repo 做准入检查；不要切 canonical checkout 的分支，不要新建同名 worktree：

```bash
cd /Users/baitianxing/codes/aidcp
./scripts/task-preflight

git status --short --branch
git -C ../aidcp.wt/add-managed-automation-runtime status --short --branch
git -C ../aidcp-cloud status --short --branch
git -C ../aidcp-cloud.wt/add-managed-automation-runtime status --short --branch

git -C ../aidcp-cloud.wt/add-managed-automation-runtime fetch origin
git -C ../aidcp-cloud.wt/add-managed-automation-runtime rev-list \
  --left-right --count HEAD...origin/master

openspec list | rg 'add-managed-automation-runtime|Changes:'
openspec validate add-managed-automation-runtime --strict
```

然后完整阅读：

```bash
cd /Users/baitianxing/codes/aidcp.wt/add-managed-automation-runtime
sed -n '1,240p' openspec/changes/add-managed-automation-runtime/proposal.md
sed -n '1,1180p' openspec/changes/add-managed-automation-runtime/design.md
sed -n '1,220p' openspec/changes/add-managed-automation-runtime/tasks.md
for spec in openspec/changes/add-managed-automation-runtime/specs/*/spec.md; do
  sed -n '1,260p' "$spec"
done
sed -n '1,360p' openspec/changes/add-managed-automation-runtime/HANDOFF.md
```

注意：

- canonical control repo 当前有用户文件
  `tmp/add-managed-automation-runtime-cloud.diff`，不要删除、清理或覆盖。
- zsh 中不要把循环变量命名成 `path`；`path` 是 zsh 的特殊数组，会破坏 `PATH`，使循环里的
  `git` 变成 `command not found`。
- 后续开发继续使用现有两个 worktree；不要在 canonical `main`/`master` 上直接开发。

---

## 1. 已定稿的架构关系

用户已经明确裁定：

```text
手工任务 / Agent 提案 ───────────────┐
                                    ├─> Task / immutable ExecutionPlan
现有编排在第四期降级为自动任务生产者 ──┘                  │
                                                         v
                                               唯一 Task Runtime
                                                         │
                                                         v
                                           Intent / Attempt / Edge
```

核心含义：

1. 任务模式是同一通道的“手动挡”；未来编排是“自动挡”。
2. 现有编排把“什么时候、给谁、做什么”和“具体怎么执行”焊在一起。
3. 终态由 `TriggerRegistry + ManagedCycle` 承接排期、周期和自动派生，产出有界
   `Task/ExecutionPlan`；执行层不再维护第二套编排执行器。
4. 第一期建设的任务通道不是旁路，而是未来唯一执行主干。
5. 这不表示现有编排已经迁走。当前代码仍是 legacy producer + executor 的组合；只有对应
   capability 的 OpenSpec delta、准入、迁移和纵切验证完成后，才可逐片切换 trigger owner。

---

## 2. 当前仓库快照

| 仓库/位置 | 分支与 HEAD | 快照状态 |
| --- | --- | --- |
| canonical control `/Users/baitianxing/codes/aidcp` | `main@747bc2e3` | 跟踪 `origin/main`；存在用户未跟踪 diff 文件，须保留 |
| control worktree `/Users/baitianxing/codes/aidcp.wt/add-managed-automation-runtime` | `codex/add-managed-automation-runtime@b5e71b2b` | 干净；比远端同名分支 ahead 2 |
| canonical Cloud `/Users/baitianxing/codes/aidcp-cloud` | `master@843bac61` | 跟踪 `origin/master`，未承载本 change 代码 |
| Cloud worktree `/Users/baitianxing/codes/aidcp-cloud.wt/add-managed-automation-runtime` | `codex/add-managed-automation-runtime@db11692f` | 干净；相对 `origin/master` ahead 11、behind 5 |

截至快照：

- Cloud 远端没有 `refs/heads/codex/add-managed-automation-runtime`；11 个 Cloud 提交仅在本地。
- control 的 `d5785d58`、`b5e71b2b` 也尚未推送。
- 没有 Edge、Console 实现提交。
- 没有 merge 到 `main/master`。
- 没有 DEV/OL 部署；更没有 Edge 安装包或客户端发布。
- `openspec validate add-managed-automation-runtime --strict` 当前通过。
- `openspec list` 当前显示 **3/111 tasks**。

---

## 3. Qoder 这一批实际交付

### 3.1 Control 提交

| SHA | 内容 |
| --- | --- |
| `d5785d58` | 在 `docs/protocol.md` 记录可选 `hello.session.mode` 字段 |
| `b5e71b2b` | 在 `tasks.md` 为 1.3、1.6、2.3 写入完成证据 |

OpenSpec 只勾了三项是正确的。Qoder 的 8 个任务是内部任务板拆分，不能机械映射为 111 个
OpenSpec 条目已经完成。

### 3.2 Cloud 提交

| SHA | 内容 |
| --- | --- |
| `9182968` | 冻结 contracts 与旧状态映射 |
| `28bbfae` | migrations 0099–0102、8 张核心表、typed stores |
| `0cde61b` | 线性 PlanCompiler、StepExecutor、TaskRunWorker 骨架 |
| `0ec53d5` | `session.mode` 登记及 task-mode 调度排除 |
| `9ca945a` | Create/Cancel/Query service、内部 HTTP 与组合根入口 |
| `c5dd822` | Create/Cancel/Query service/transport tests |
| `8b48f02` | `persona.research@1` 只读 TaskDefinition/Capability registry |
| `de2fa75` | `ResearchStepExecutor` 与 `EdgeDispatchPort` |
| `e40e00b` | registry 和 account binding 接到 CreateTask 组合根 |
| `c1f4523` | 只读研究纵切 E2E 测试和 boundaries 登记 |
| `db11692` | 默认关闭 API 时的启动日志由 warn 降为 info |

相对该 feature branch 与 `origin/master` 的 merge base，本批快照为：

```text
65 files changed, 9310 insertions(+), 8 deletions(-)
```

Qoder 对话中显示的“15 个文件、+1527”只对应最早的 contracts 提交，不是整批最终规模。

---

## 4. 当前能做什么，不能做什么

### 4.1 已有的源码能力

- typed contracts：Task、TaskRevision、ExecutionPlan、TaskRun、StepRun、Intent、Attempt、
  DecisionTrace、CapabilityDefinition、TaskDefinition 等。
- 四个 additive migration 文件和 8 张 Automation-owned 核心表。
- 带 target、CAS、租约与终态保护的 typed stores。
- 有界线性 plan compiler 和 worker 类。
- 默认关闭的 task-mode scheduling exclusion：
  `AIDCP_TASK_MODE_SCHEDULING_EXCLUSION === 'true'` 时才排除 `mode='task'` 会话；
  默认不改变现役调度。
- 默认关闭的内部 Create/Cancel/Query API：
  `AIDCP_MANAGED_AUTOMATION_API_ENABLED === 'true'` 时才初始化 stores 并注册三条 Bearer route。
- `persona.research@1` 的四步只读图：search → browse → assess → summarize。
- 对 Edge 投递结果的诚实映射：completed、empty、failed、timeout、undeliverable、aborted
  不会被互相伪装。

### 4.2 仍然没有形成的运行时闭环

**不要把 `research-slice-e2e.test.ts` 的绿色理解成生产运行时已经接通。**

当前 `server.ts` 只在 API 开关开启时构造 stores、registry、PlanCompiler 和 `TaskEntryService`，
并注册 Create/Cancel/Query。生产组合根没有构造或启动：

- `TaskRunWorker`
- `ResearchStepExecutor`
- `CommEdgeDispatchAdapter`

它们目前只由单测/纵切测试装配。因此即使打开内部 API，CreateTask 可以创建权威记录和 run，
但没有生产 worker 去认领和执行该 run。

另外：

- worker 自身有默认关闭开关 `AIDCP_MANAGED_AUTOMATION_WORKER_ENABLED`，但尚未接入生产启动路径。
- 只读研究 E2E 使用测试装配，不是 named DEV account、真实 Edge/Host 或平台侧验证。
- 没有 Outbox/Inbox、完整 Trigger Registry、ManagedCycle 或第四期 legacy orchestration producer
  收敛。
- 没有写动作 capability；这批只允许 `research.read`。
- 没有客户侧/Console/Classic Client 入口。

所以当前准确状态是：

```text
contracts + persistence + entry API + engine/test slice
!= integrated runtime
!= deployed runtime
!= released client
!= real-platform evidence
```

---

## 5. 验证证据与边界

Qoder 在 control commit `b5e71b2b` 中记录的证据：

```text
typecheck: 0
full tests: 3990 discovered / 3975 passed / 0 failed / 15 skipped
review: 3-way review, 0 blocker / 0 major
```

其中 4 个 PostgreSQL integration tests 因本机没有 PostgreSQL 而未运行，覆盖：

- CAS races
- claim exclusion
- lease takeover
- execution-target isolation

当前交接 session 额外重跑并确认：

```text
openspec validate add-managed-automation-runtime --strict
=> Change 'add-managed-automation-runtime' is valid
```

当前 session 没有重复启动 Cloud 全量测试，也没有运行 DEV 数据库集成或真实账号 probe。
分支 rebase 后，旧测试结果不能继续作为新 HEAD 的验证证据，必须重跑。

---

## 6. 最高优先级集成阻塞

### 6.1 迁移编号已经冲突

feature branch 基于旧 `master` 使用：

```text
0099_managed_automation_task_authority
0100_managed_automation_run_state
0101_managed_automation_execution_ledger
0102_managed_automation_decision_traces
```

但新的 `origin/master@843bac61` 已经增加：

```text
0099_operator_command_receipt
```

因此下一 session **不得直接合并后继续开发**。先 fetch 最新 `master`，计算当前最大迁移号，
再把本 change 的四个 migration 连续重编号。若 `master` 仍以 0099 结尾，目标应为
0100–0103；若 fleet 又有新迁移，则从新的最大号之后开始，不能照抄本文数字。

重编号必须同步更新所有事实引用，包括但不限于：

- migration filenames 和文件头
- `src/schema/schema-contract.ts`
- stores 的 `sinceVersion`
- `boundaries/table-ownership.json`
- `test/schema/sync-read-checkpoint-migration.test.ts`
- `test/managed-automation/stores-unit.test.ts`
- `test/managed-automation/stores-pg.integration.test.ts`
- 其他 `0099–0102` 注释、断言和文档

用下面的命令找全，不能只改文件名：

```bash
cd /Users/baitianxing/codes/aidcp-cloud.wt/add-managed-automation-runtime
rg -n '0099|0100|0101|0102|KNOWN_MAX_SCHEMA_VERSION|REQUIRED_SCHEMA_VERSION' \
  src test scripts migrations boundaries
```

### 6.2 rebase 存在真实文本冲突和热点重叠

快照时两边共同改动 9 个文件：

```text
boundaries/import-exemptions.json
boundaries/module-ownership.json
boundaries/ownership-rules.json
boundaries/table-ownership.json
boundaries/table-write-exemptions.json
scripts/db-split/owner-tables.automation.txt
src/schema/schema-contract.ts
src/server.ts
test/schema/sync-read-checkpoint-migration.test.ts
```

只读 `git merge-tree` 已确认至少 4 个会产生文本冲突：

```text
boundaries/table-ownership.json
scripts/db-split/owner-tables.automation.txt
src/schema/schema-contract.ts
test/schema/sync-read-checkpoint-migration.test.ts
```

解决原则：

- 两个 change 的表都必须保留；不能用 ours/theirs 整体覆盖。
- `KNOWN_MAX_SCHEMA_VERSION` 指向 rebase 后数字最大的真实 migration。
- `REQUIRED_SCHEMA_VERSION` 是否抬高必须按“现役启动是否硬依赖该表”的既有门槛判断；
  不要因为新增表就机械抬高。
- `owner-tables.automation.txt` 应从合并后的 `table-ownership.json` 重新生成并核对，
  不要手填一个看似合理的 count。
- `src/server.ts` 虽可能文本自动合并，仍是语义热点，必须人工复核两边组合根接线都在。
- boundaries JSON 不得整文件重排或重序列化；保持可审查的最小 diff。

---

## 7. 下一 session 建议任务顺序

### 任务 A：准入、刷新与 rebase

1. 跑 §0。
2. fetch Cloud `origin/master`，记录新的 merge base/ahead/behind。
3. 在现有 Cloud feature branch 上 rebase 最新 `origin/master`。
4. 按 §6 重编号 migration、解四个文本冲突、人工审 9 个热点文件。
5. 不要修改 canonical `master`，不要 force-push。

### 任务 B：rebase 后统一验证

先跑 focused，再扩到 acceptance/full：

```bash
cd /Users/baitianxing/codes/aidcp-cloud.wt/add-managed-automation-runtime

npm run typecheck
npx tsx --test \
  test/comm/ws-server-task-mode.test.ts \
  test/handler-session-mode.test.ts \
  test/orchestrator/connection-runtime-task-mode.test.ts \
  test/managed-automation/engine-plan-compiler.test.ts \
  test/managed-automation/engine-worker.test.ts \
  test/managed-automation/entry-service.test.ts \
  test/managed-automation/research-slice-e2e.test.ts \
  test/managed-automation/stores-unit.test.ts \
  test/transport/managed-automation-http.test.ts
npm run test:acceptance
npm test
```

有可确认的非生产 PostgreSQL 时，再串行运行：

```bash
AIDCP_PG_INTEGRATION=1 npx tsx --test --test-concurrency=1 \
  test/managed-automation/stores-pg.integration.test.ts
```

不要把“PG tests skipped”写成通过；记录 skipped 原因和未覆盖边界。

### 任务 C：裁定并补齐运行时闭环

在继续宣称“只读研究纵切完成”之前，明确选择并记录：

1. 本批只交付 source/test slice，生产 worker 接线留到后续 OpenSpec task；或
2. 在本批补齐 `TaskRunWorker + ResearchStepExecutor + CommEdgeDispatchAdapter` 的生产组合根、
   生命周期、开关、退出、恢复和观测。

若选择 2，必须先对照 tasks 3.6、6.5、6.6，不能只 `new TaskRunWorker()` 就算完成；至少覆盖：

- invalid/missing `AIDCP_DEPLOY_ENV` 时 worker 禁用
- API/worker 两个开关的组合语义
- task-mode exact env/account binding
- Edge offline/reconnect、超时、中断和所有权易主
- restart recovery、重复认领与 late result discard
- shutdown 时停止 claim 并有界退出
- 不产生平台写动作

### 任务 D：诚实回写 OpenSpec

当前只勾 1.3、1.6、2.3。不要按 Qoder 任务板批量勾选：

- 2.1 要求的 durable tables 不止当前 8 张，不能因为四个 migration 已存在就勾完。
- 2.4 还包括 transaction/owner/pagination/retention/cross-owner interface 全约束。
- 3.1/3.3/3.6 与 6.1–6.6 目前都是部分实现。
- 研究 E2E 不是 6.7 的 named DEV account probe。

每个完成项按仓库规范写：

```text
repo + commit SHA + validation + deployment + deviations
```

然后：

```bash
cd /Users/baitianxing/codes/aidcp.wt/add-managed-automation-runtime
openspec validate add-managed-automation-runtime --strict
```

### 任务 E：集成、推送与 DEV

只有 rebase、focused、acceptance、full、typecheck、OpenSpec strict 全绿后才进入：

1. 推送两个 feature branch。
2. 按 worktree/integration 规范进入 serial integration。
3. runtime 行为要落 DEV 时，先读 `docs/deployment-environments.md` 并运行：

   ```bash
   cd /Users/baitianxing/codes/aidcp
   ./scripts/deploy-target dev --check
   ```

4. 新 migration 必须走 owner database 的正式 migration ledger；先备份、核对 pending 集合，
   再 migrate、重启指定 AIDCP service、检查 listener/health/log/schema。
5. **不要部署 OL**，除非用户明确给出 OL release scope。
6. 不要构建 Edge installer；本 change 当前也没有 Edge 客户端交付。

---

## 8. 可直接粘贴给下一 session 的启动指令

```text
继续 OpenSpec change add-managed-automation-runtime。先读
/Users/baitianxing/codes/aidcp/AGENTS.md 和
/Users/baitianxing/codes/aidcp.wt/add-managed-automation-runtime/openspec/changes/add-managed-automation-runtime/HANDOFF.md，
再读 proposal/design/tasks/spec deltas。先在 canonical control repo 跑 ./scripts/task-preflight。

继续使用现有两个 worktree：
- control: /Users/baitianxing/codes/aidcp.wt/add-managed-automation-runtime
- cloud: /Users/baitianxing/codes/aidcp-cloud.wt/add-managed-automation-runtime

不要切 canonical 分支，不要清理用户文件，不要新建同名 worktree。第一优先级不是新增功能，
而是 fetch/rebase 最新 origin/master，解决 master 的 0099_operator_command_receipt 与本 change
0099–0102 的迁移编号冲突。以 fetch 后真实最大迁移号为准连续重编号，并更新 schema constant、
store sinceVersion、ownership、tests 和所有引用。git merge-tree 已知至少四个文本冲突：
table-ownership.json、owner-tables.automation.txt、schema-contract.ts、
sync-read-checkpoint-migration.test.ts；server.ts 等 9 个热点文件必须人工语义复核。

rebase 后依次跑 managed-automation focused tests、acceptance、full tests、typecheck 和 OpenSpec strict。
本机没有 PG 时必须如实记录 4 个 PG tests 未运行。当前 TaskRunWorker、
ResearchStepExecutor、CommEdgeDispatchAdapter 尚未进入生产 server 组合根，研究纵切只是源码/测试闭环，
不是已部署/真实 Edge 闭环；在补齐运行时接线或明确延期前，不得宣称期 1 可运行。

只按 OpenSpec 完整条款勾 tasks；当前真实进度 3/111。完成后提交、推送 feature branches，
再按规范串行集成和部署 dev。未获明确授权不得部署 ol，不构建 Edge installer。
```

---

## 9. 一句话状态

**方向已经定稿，第一批地基代码已经在隔离 worktree 的本地 feature branch 成形并有测试证据；
但它落后 master、迁移号冲突、尚未推送/集成/部署，生产 worker 也未接线。下一 session 应先完成
rebase 与迁移重编号，再决定是否把只读研究从测试纵切补成真实运行时纵切。**
