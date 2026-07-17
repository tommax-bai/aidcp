> **实装前必读**：本 change **纯云端单边**——不改边缘、不改 console、不碰协议、不碰 DB。
> 若你发现自己在改 `protocol.ts` / `main.cjs` / `renderer.js` / 任何迁移，**停手**：不是改错了地方，就是范围蔓延了（见 design D1/Non-Goals）。

## 1. aidcp-cloud — 平台感知的上限投影（纯函数）

- [ ] 1.1 在 `src/platform/surface.ts` 新增纯函数（与既有 `isNoteActionSupported:40` / `isOrchestrationCapabilitySupported:62` 同处），入参 `(platform, quotas)`、出参过滤后的 quotas。**同步、纯、永不抛**：内部自兜 try/catch，任何 registry 查询失败即原样返回入参 quotas（design D4——fail-open 由函数自证，不依赖调用点记得包 try）。
- [ ] 1.2 函数**两张矩阵都查**：note-scoped 动作（如 `collect`）查 `noteActions`，编排动作（如 `follow`）查 `capabilities`。**只查一张是缺陷不是取舍**——`follow` 的不支持声明在 `capabilities:307` 而非 `noteActions`，只查后者会结构性看不见它（design D2）。
- [ ] 1.3 只摘**显式声明为 `supported: false`** 的动作。缺失声明 / 平台解析不到 / 查询抛异常 ⇒ **不摘**（照发）。**MUST NOT** 用「限额=0」表达不支持，**MUST NOT** 给 `quota_config` 加 platform 维度（design D6；`platform-browse-surface` 明禁「靠数值巧合推断支持性」）。
- [ ] 1.4 单测（纯函数层）：FB 入参含 `collect`/`follow` ⇒ 出参恰好少这两项、其余逐位不变；XHS ⇒ 出参与入参**逐位相同**；platform 传 `null`/`undefined`/未知串 ⇒ 出参与入参逐位相同；registry 查询 throw ⇒ 出参与入参逐位相同（fail-open）。

## 2. aidcp-cloud — 接入点（位置即正确性）

- [ ] 2.1 **先逐点分类 `pickDailyUsageCounts` 的 4 个调用点**，在 PR 描述或注释里写明分类结论：`server.ts:2157/:2158/:2159` = **quotas 侧（本 change 要动）**；`:2099-2103` = **totals 侧（绝不动）**；`completeSessionUsageCounts:422` 内部一个 = 按其实际语义分类。四者入参均为宽松 `Partial<Record<string, number>>`，**typecheck 一个都不会提醒你**（design 风险条 2）。
- [ ] 2.2 在 `server.ts:2154-2193` 段接入 1.1 的函数：**必须在 try 块内**、在 `effectiveQuotas()` **之后**、`pickDailyUsageCounts` **之前**。**MUST NOT** 挪到 totals 段（`:2064-2103`，不在 try 内）之前——那会 fail-closed（`ui-snapshot.ts:130-133` 对整个 promise `.catch(() => null)` ⇒ 整行 KPI 消失、退回本机实时）（design D3）。
- [ ] 2.3 过滤对 minute / hour / day **三份 quotas 都生效**（`:2157/:2158/:2159`），不是只治 day。
- [ ] 2.4 确认 `totals` 段**零 diff**。摘 totals 键是无效功——`main.cjs:1604` 的 `cleanRequiredCounts` 会把六键无条件物化回 0，改动会 land、会全绿、会部署，**屏幕上一格都不会变**（design D1）。

## 3. aidcp-cloud — 载荷级验收测试

- [ ] 3.1 **小红书载荷逐位不变**（回归判据，非善意期待）：XHS 账号的 `ui.snapshot` 用量载荷与本 change 前**逐字节相同**（quotas 六项齐全 + totals 不变）。
- [ ] 3.2 **FB 载荷恰好少两项**：quotas 无 `collect`、无 `follow`，其余上限逐位不变；**totals 六项齐全且不变**（含 `collect: 0` / `follow: 0`——本 change 不动计数）。
- [ ] 3.3 **fail-open 断言**：平台解析失败 / 查询抛异常时，payload 仍带**完整六项上限**（不是空 quotas、不是整行消失）。
- [ ] 3.4 确认 `AC-PROTO-*` **无变化**——本 change 不碰协议，若这组断言有任何变动，即说明改错了地方（design Migration 步骤 3）。

## 4. 验证与部署

- [ ] 4.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序照 CLAUDE.md §4）。**注意**：`npm run typecheck | tail` 的退出码是 tail 的、会假绿——直接跑、看退出码。
- [ ] 4.2 提交 + push cloud master（commit message 末尾带 `Co-Authored-By`）。
- [ ] 4.3 部署 dev（安全序列照 §5：`scripts/deploy-target dev --check` → ECS 先备份 → rsync `--exclude .env --exclude node_modules --exclude .git` → `systemctl restart aidcp-cloud.service` → healthcheck）。**无需出安装包**、无需运营侧动作、无 DB 迁移。**红线**：绝不碰同机 isales。
- [ ] 4.4 dev 上取一个 FB 账号与一个 XHS 账号的实际用量载荷比对，坐实 3.1 / 3.2 的断言在真环境成立（**不是只在单测里成立**）。

## 5. 回写与收口

- [ ] 5.1 本文件按 §6 用 HTML 注释标 `[x]` + 写 commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha **必须取自已推送的提交**（判据：`git merge-base --is-ancestor`，不是 `cat-file`——后者对悬空提交照样说 commit）。
- [ ] 5.2 真机项登记 `docs/real-machine-acceptance-backlog.md` **簇 90**，一条即可：FB 环境的收藏格与关注格不再显示 `/N` 与进度条，且「今日计划已完成」横幅在 FB 上**第一次成为可触发的**。
- [ ] 5.3 `openspec validate platform-honest-usage-caps --strict` 通过。
- [ ] 5.4 与 `account-level-slow-start` 对账：告知其 owner 本 change 已落，其 `min(曲线, 档位)` 压低须排在本 change 的平台过滤**之前**（本 change 的过滤永远是最后一步，design D3）。

## 6. 登记（不实装，仅记录）

- [ ] 6.1 确认 design Open Question 2：dev 库查一次是否有 FB 账号在风控流水里留有历史 `follow` 记录。**不阻塞**——`totals` 不动，摘上限不影响数字本身。结论写回 design。
- [ ] 6.2 确认 design Open Question 1：视频号载荷形状是否需在过滤函数里显式短路。**倾向不短路**；无论结论如何，本 change 的验收 **MUST NOT** 依赖视频号的载荷形状。
- [ ] 6.3 把 proposal 的两条遗留登记进 backlog，**本 change 不治**：(a) 平台错标不可纠错（本 change 的天花板，建议另立 change）；(b) `edge-companion-ui` spec:934 的 falsifiable 理由应改为引用四档模型（独立 nit）。
