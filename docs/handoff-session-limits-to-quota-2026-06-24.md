# 交接：把「会话上限」从人设搬到安全限额层（2026-06-24）

> 给**新 session** 的交接文档。任务 = 实装「会话上限收口到安全限额层」（原 D `safety-quota-config` 的 §7，已从 D 摘出、单立一个 change 做）。
> 读完本文 + memory `console-worklist-10items-partition` 即可上手；不必重新考古。

## 0. 一句话目标

把**单场会话上限**（① 单场时长 `max_duration_min`；② 单场互动预算 `freshBudget()` 写死值）从**人设（soul.session_limits）/ 写死常量**搬进**安全限额层**（与 D 的 `quota_config` 同源治理：后台可改 + 热加载 + never-brick），并**把 `session_limits` 从人设里清理掉**（它本就是限额/风控性质、非人设性质，且大半是死配置）。

## 1. 决策与理由（用户 2026-06-24 拍板）

- 「会话硬上限」回答的是「这账号一场能做多少、多猛才安全」= **限额/风控**，不是「这账号是谁」= 人设。放在人设里是职责错位。
- 用户选项 A：**归安全限额层，不留人设**；做 D 时本想一并搬，后改为**单开新 change**（就是你这个 session）。
- 配套：人设此后**只承载身份 / 兴趣 / 行为偏好**。

## 2. 现状坐实（带文件:符号，动手前务必复核行号——并发改动多，行号会漂）

`aidcp-cloud`（同级目录 `../aidcp-cloud`，分支 `master`）：

- **人设里的会话上限**：`src/soul/types.ts` `SessionLimits`（max_duration_min / max_likes / max_collects / max_searches / cooldown_between_actions_sec）；`src/soul/loader.ts` `parseSessionLimits` 校验；`src/soul/soul.yaml` 填了一份。
- **真正在用的只有 `max_duration_min`**，且已是**惰性热加载**（F + 评审修复后）：
  - `src/orchestrator/role-dispatcher.ts` `maxDurationMs()`（约 :251）= `(this.resolveSoul().session_limits?.max_duration_min ?? 10) * 60_000`；`progress()` 疲劳乘子用它。
  - `src/agents/session-monitor-role.ts` `effectiveMaxDurationMs()`（约 :116）= `this.maxDurationMsOverride ?? (this.soul.session_limits?.max_duration_min ?? 10)*60_000`；role-dispatcher 已**不再传死值**（约 :403 注释），让它经 `this.soul`（getSoul 取值口）惰性解析。
  - `resolveSoul()`（role-dispatcher :244）= getSoul 取值口优先（按账号 resolvePersona）→ 兼容快照。
- **`max_likes` / `max_searches` / `max_collects` / `cooldown` 是死配置**：全仓 `grep -rn "session_limits" src/` 只有 `max_duration_min` 被读；其余解析了但运行时无处读取。
- **真正卡「单场最多点几个赞/收藏/搜几次」的是写死常量**：`src/orchestrator/role-dispatcher.ts` `static freshBudget()`（约 :484）返回 `{ likes:10, collects:5, follows:3, searches:5, comments:2, comment_likes:3 }`；既不来自人设、也不来自风控档位。`this.budget`（:211）初始化用它，`startSession`/`restartSession` 会 reset。
- **另有一份按档位单场上限挂在 v1 旧路径**：`src/risk/session-budget.ts` `SESSION_LIMITS`（:18，`const`、**未导出**）= conservative 15min/30动作、normal 30/60、aggressive 60/120；`SessionBudget` 类在 `src/comm/handler.ts:291` `new SessionBudget(...)` 用——那是 **v1 兼容 plan/select 路径**，**非现役事件驱动闭环**。现役闭环用的是上面的 `freshBudget()` + `maxDurationMs()`。可作为「单场上限默认值」的参考来源，但别假设它在线上生效。

人设侧（F `account-persona-config`，**已部署、未归档**，6.4 正向校准 pending）：后台 `/persona` 页 + `PersonaStore` 让你编辑整份 soul（含 session_limits）；**改 session_limits 里除时长外的字段不生效**（死配置）——这就是要清理的「能改却无效」误导。

## 3. 已建好的地基：D `safety-quota-config`（直接复刻/扩展它）

D 已实装+部署+归档（archive `openspec/changes/archive/2026-06-24-safety-quota-config/`）。你要做的几乎是它的「会话窗口」版，强烈建议**照抄形态**：

- `migrations/0010_quota_config.sql` + `src/config/quota-config-store.ts` `QuotaConfigStore`：表 `(tier, action, daily, per_minute, per_hour)`，实现 `QuotaProvider`（`src/risk/types.ts`）`windowQuotasFor(level)`；**缺行逐窗口回落 `deriveWindowQuotas(level)`（零回归基线，不是裸 burst cap）**；写库成功才刷镜像；永不抛。
- `src/config/quota-config-facade.ts`：getCatalog / setQuota（整数 + `>=0` + `<=QUOTA_MAX`(`src/risk/quotas.ts`) 校验，非法**整块拒不落库**）。
- `src/risk/risk-controller.ts` `effectiveQuotas()`：`quotaProvider?.windowQuotasFor(level) ?? deriveWindowQuotas(level)`；`RiskControllerRegistry` 透传 provider；构造期 D 在 `src/server.ts` 与其余 config store 同 try/catch init。
- 面板：`GET/PUT /api/quotas`（`src/panel/panel-server.ts`，JWT）；console `/quotas` 页 `src/pages/QuotasPage.tsx`（三档×7动作×三窗口可编辑表 + 弹窗、非乐观写）。
- 测试形态：`test/quota-config-store.test.ts`（fake pool + 零回归断言）、`test/quota-config-facade.test.ts`、`test/quota-effective-quotas.test.ts`。**照这套写你的单测**。

## 4. 设计：推荐 schema + 待你拍的开口

会话上限有两类，维度不同，别硬塞一张表：

1. **单场时长上限**：按**档位**（per tier），不按动作。
2. **单场互动预算**：按**档位 × 动作**（per tier × action），取代 `freshBudget()`。

推荐方案（务实、与 D 同源、YAGNI）：
- 新建 `session_config(tier TEXT PRIMARY KEY, max_duration_min INTEGER, max_actions INTEGER, updated_at, updated_by)` 存**单场时长 + 单场总动作上限**（默认回落 `session-budget.ts` `SESSION_LIMITS`）。
- 单场互动预算：**给 `quota_config` 加一列 `per_session INTEGER`**（每 tier×action 一个单场上限），provider 多给一个窗口；或另立 `session_action_budget(tier, action, per_session)`。**倾向加列**（复用 D 的表 + facade + provider，改动最小）。
- 统一一个 `SessionLimitProvider`（或扩 `QuotaProvider`）：`sessionDurationMsFor(level)` / `sessionBudgetFor(level)`，注入 role-dispatcher + session-monitor。

**待你拍的开口**：
- 维度=**档位**（tier）还是**账号**？现状 `max_duration_min` 是经人设**按账号**解析的；搬到安全限额层后默认按**档位**（与 D 一致）。这是语义切换：搬完后单场时长**不再来自账号人设、而是来自账号当前风控档位**。确认这符合预期（用户决策是「归限额层」，限额层是按档位的，所以按档位合理）。如果想保留「按账号」，需在表上加可空 `account_id`（与 stream C 的 account 缝对齐，YAGNI 可后做）。
- 单场互动预算用 `quota_config.per_session` 加列，还是另立表。

## 5. 实装清单（= 原 D §7.1–7.6，现作为你这个 change 的 tasks）

1. **存储**：迁移 + store/provider（单场时长 by tier + 单场互动预算 by tier×action）；never-brick 回落到现值（`SESSION_LIMITS` + `freshBudget()` 的数字）。
2. **接管单场时长**：`role-dispatcher.ts` `maxDurationMs()` + `session-monitor-role.ts` `effectiveMaxDurationMs()` 改为读新 provider（保留惰性热加载形态；按当前账号→档位解析）。
3. **接管单场互动预算**：`role-dispatcher.ts` `freshBudget()` 改为按当前档位从 provider 读（保留 reset 语义）。
4. **console**：`/quotas` 页加「单场上限」编辑区（时长 + 单场互动预算），非乐观写。
5. **人设清理（配套，碰已部署的 F，务必小心）**：把 `session_limits` 从人设移除——
   - `src/soul/types.ts` 去掉 `session_limits`（或标 deprecated）、`src/soul/loader.ts` `parseSessionLimits` 相应处理、`src/soul/soul.yaml` 删该段；
   - `/persona` 页若展示/可编辑 session_limits 则隐藏；
   - **never-brick**：现役只读 `max_duration_min` 一处，已全部改读新 provider 后才能安全删；删前确认无残留 `this.soul.session_limits` 读取（`grep -rn "session_limits" src/`）。
6. **验证**：改单场上限即时生效（热加载）；空表/缺值回落现值不 brick；人设页不再出现「能改却无效」字段；`grep` 确认无 `session_limits` 残读。

## 6. 红线 / 不变量（务必守）

- **never-brick**：缺表/缺行/非法值 → 回落现值（`SESSION_LIMITS` + `freshBudget()` 数字），永不抛、不崩闭环。
- **零回归**：空表时行为与现状逐位一致（单场时长默认 10min/或档位值、单场预算 = 现 freshBudget 数字）。照 D 的 `windowQuotasFor` 空表=deriveWindowQuotas 的做法写零回归单测。
- **绝不碰风控状态单写**：`setQuotaLevel` / `applySignal` / `risk_state` 不动；新配置只读、只写自己的表。
- **不碰协议**（会话上限不经边-云协议；别动 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`）。
- **删 `session_limits` 前先确认所有读点已迁走**——这是唯一有「删了会 brick」风险的一步。

## 7. 协调 & 坑（同机重度并发，重点看）

- **同机多个会话并行写同一批仓库**（截至 2026-06-24：llm-token-usage-stats、return-to-feed-on-follow-block、multi-account-node-support、publish-history-account-and-detail）。**共享同一个工作树 + git index**——别人的 `git commit` 会把你 `git add` 的文件一起卷走（已发生：归档被并发提交 e4ec0d8 带走）。
  - **纪律**：只 `git add` 自己的具体文件，**绝不 `git add -A`**（见 memory [[precise-git-add-concurrent-sessions]]）。
  - **共享文件**（如 `src/panel/types.ts`、console `src/types/api.ts`）若被别的会话同时改：用 git plumbing **只暂存自己的 hunk**——`git show HEAD:<file>` 取基线 → 复刻自己的编辑 → `blob=$(git hash-object -w /tmp/mine)` → `git update-index --cacheinfo 100644,$blob,<file>`（工作树不动、别人 WIP 不丢）。本 session 用此法成功隔离过 panel/types.ts。
  - 最稳：开工前确认是否只有你一个写会话，或用独立 git worktree。
- **迁移号**：现有最高 `0013_llm_token_usage.sql`；`0012` 当年留给 stream B（account-real-nickname，**未实装**）。**先 `ls ../aidcp-cloud/migrations/` 复核**，建议取 **0014**（避开 B 的 0012），或与并发会话错峰协调。
- **测试命令已修**：`npm test` 现在是 `tsx --test 'test/**/*.test.ts'`（带引号，跑全 640+）。顶层 `test/*.test.ts` 现在**会跑**——你新加的顶层测试别再被 glob 漏掉了。
- **ECS 部署 = 全量 master 快照**（见 memory [[ecs-deploy-scope-full-master]]）：rsync 会连带其余已合并 master 一起上。部署前 `rsync --dry-run` 摸范围；**部署后 grep ECS 文件内容 + 看启动日志**确认新码生效（见 [[deploy-verify-content-after-rsync]]），别只信回执。同机 isales 绝不能碰。

## 8. 命令 / 位置速查

- 仓：中控 `.`（本仓，分支 `main`）；cloud `../aidcp-cloud`（`master`）；console `../aidcp-console`（`master`）。**动前先 `ls -d ../aidcp-cloud ../aidcp-console`**。
- 起 change：`/opsx:propose "把会话上限（单场时长+单场互动预算）从人设搬到安全限额层，按档位可配+热加载+never-brick，并清理人设里的 session_limits 死字段"`。
- cloud 验证：`cd ../aidcp-cloud && npm run typecheck && npm run test:acceptance && npm test`（AC-RISK 红线必过）。
- console 验证：`cd ../aidcp-console && npm run build`。
- openspec：`openspec list` / `openspec validate <change> --strict`（telemetry 报错是分析噪声，加 `OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1` 2>/dev/null 看结论）。
- 部署私钥 `~/codes/isales-4.pem`（须 `chmod 600`）；ECS `ssh -i ~/codes/isales-4.pem root@121.89.85.150`，cloud `/opt/aidcp/cloud`（systemd `aidcp-cloud.service`，8787，PG 同机），console `/opt/aidcp/console`（nginx 8088）。GitHub SSH 本机间歇被掐（`198.18.0.24:22`），push 需重试。

## 9. 参考

- 决策 + 坐实：memory `console-worklist-10items-partition`（「会话上限归属决策」段）；`openspec/changes/account-persona-config/design.md`「留的缝」。
- 地基范例：`openspec/changes/archive/2026-06-24-safety-quota-config/`（proposal / design / tasks）。
- D 的 spec delta 落点：`openspec/specs/interaction-risk-gating/spec.md`（你的会话上限要求大概率也并到这里，或 role/pacing 相关 spec——propose 时定）。
