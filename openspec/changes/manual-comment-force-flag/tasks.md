# Tasks — manual-comment-force-flag

> 纯 aidcp-cloud 端改动。全部落在单次提交 `aidcp-cloud 3177735`（rebase 到最新 master 后 ff 合入）。
> <!-- aidcp-cloud 3177735 land origin/master -->
> <!-- 2026-07-11 deployed dev -->

## 1. aidcp-cloud — 命令解析与接线（src/feishu/commands.ts）

- [x] 1.1 `ParsedCommand` 增 `force?: boolean` 字段（带文档注释：`--force` = 跳过相关性 + 每笔记去重，仅手动路径）。 <!-- aidcp-cloud 3177735 -->
- [x] 1.2 `parseCommand` 的 `/comment` 尾部开关 `while` 循环加 `/^--force$/i` 分支（命中置 `force=true` 并从末尾吃掉该 token，与 `--contact`/`--join` 同构、任意顺序可组合）；`return` 带上 `force`。 <!-- aidcp-cloud 3177735 -->
- [x] 1.3 `CommandActions.comment` 选项类型加 `force?: boolean`（含文档：只放开相关性/去重，绝不放开人审/安全校验/诚实闸）。 <!-- aidcp-cloud 3177735 -->
- [x] 1.4 `CommandRouter.runComment` 把 `cmd.force` 透传进 `actions.comment(..., { ..., force: cmd.force })`。 <!-- aidcp-cloud 3177735 -->
- [x] 1.5 `HELP_TEXT` 增一行 `--force` 说明（跳过相关性 + 去重、仍需人审、可与 `--contact`/`--join` 组合）。 <!-- aidcp-cloud 3177735 -->

## 2. aidcp-cloud — 命令动作实现（src/server.ts）

- [x] 2.1 `actions.comment` 选项类型加 `force?: boolean`；调用 `commentScheduler.triggerManual(acct, { ..., force: options?.force })`——`force` 与硬编码的 `manualOverride: true` **分开传**（独立字段、独立语义）。 <!-- aidcp-cloud 3177735 -->

## 3. aidcp-cloud — 小红书路径（src/comment-agent/comment-scheduler.ts）

- [x] 3.1 `triggerManual` 选项加 `force?: boolean`；XHS 分支调用 `runTask(...)` 时透传 `force`（`runTask` 新增 `force: boolean = false` 参数）。 <!-- aidcp-cloud 3177735 -->
- [x] 3.2 `runTask` 甄选前去重过滤：`force` 时只按 `!card.noteId` 跳过、不再按 `dedup.hasInteracted` 过滤（已评过仍入候选）。 <!-- aidcp-cloud 3177735 -->
- [x] 3.3 `runTask` 甄选兜底：`picked.pickIndex == null` 且 `force` 时，在该词全体 `fresh` 候选里按 `collectCount` 降序取第一作为 `selected`，继续开帖流程（而非 `return { next: true }`）。 <!-- aidcp-cloud 3177735 -->
- [x] 3.4 `runTask` 发布前去重复检：`force` 时跳过 `already_commented_before_commit` 复检（允许再评）；发布成功后仍照常 `recordInteraction`。 <!-- aidcp-cloud 3177735 -->

## 4. aidcp-cloud — Facebook 路径（src/comment-agent/comment-scheduler.ts）

- [x] 4.1 `triggerManual` FB 分支把 `force` 透传进 `runFacebookTargetedTask` 与 `runFacebookJoinThenComment`。 <!-- aidcp-cloud 3177735 -->
- [x] 4.2 `runFacebookTargetedTask` / `runFacebookTargetedTaskBody` / `runFacebookJoinThenComment` 选项各加 `force?: boolean`，一路透传到 body。 <!-- aidcp-cloud 3177735 -->
- [x] 4.3 `runFacebookTargetedTaskBody` 选帖循环：`force` 时取 `search.candidates[0]?.permalink`（不再跳过已评过的候选）。 <!-- aidcp-cloud 3177735 -->
- [x] 4.4 `runFacebookTargetedTaskBody` 相关性校验：`force` 时给 `validateFacebookComment` 传空 `targetKeywords`（相关性分支 no-op，url/contact/mention/spam/length 安全校验照常）。 <!-- aidcp-cloud 3177735 -->

## 5. aidcp-cloud — 回执与透明

- [x] 5.1 `triggerManual` 触发回执文案在 `force` 时追加「（--force：跳过相关性/去重）」标注（XHS 与 FB 两侧回执均标）。 <!-- aidcp-cloud 3177735 -->

## 6. aidcp-cloud — 测试（桩可测）

- [x] 6.1 `parseCommand`：`--force` 单独、与 `--contact`/`--join`/`--join=<url>` 任意顺序组合、以及不带 `--force` 时 `force` 为 undefined（零回归）——解析断言。 <!-- aidcp-cloud 3177735 test/feishu-commands.test.ts -->
- [x] 6.2 XHS：无强相关候选 + `force` → 兜底选 top-collect 并继续（不 `no_strong_candidate`）；不带 `force` → 仍 `no_strong_candidate`（默认路径不变）。 <!-- aidcp-cloud 3177735 test/comment-agent/comment-scheduler.test.ts -->
- [x] 6.3 XHS：已评过候选 + `force` → 不被去重过滤挡下、可被选中；不带 `force` → 仍被过滤。 <!-- aidcp-cloud 3177735 -->
- [x] 6.4 FB：`force` → `weak_relevance` 被跳过；但草稿含 url/contact/spam 时仍 `compose_skipped`（安全校验不被覆盖）。 <!-- aidcp-cloud 3177735 -->
- [x] 6.5 人审闸：`force` 下人审未授权/超时仍不发（红线断言）。 <!-- aidcp-cloud 3177735 XHS 人审 reject + FB approval 未接线均验证 -->
- [x] 6.6 自动路径（`triggerTargeted` / 自动排期）默认 `force=false`，相关性/去重照旧（零回归断言）。 <!-- aidcp-cloud 3177735 triggerTargeted 不传 force；FB 无 force 用例验 weak_relevance/all_deduped -->

## 7. 验证与集成

- [x] 7.1 `npm run test:acceptance`（47 绿）→ `npm test`（1824 绿）→ `npm run typecheck`（clean）全过（`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 绿）。 <!-- aidcp-cloud 3177735 -->
- [x] 7.2 `scripts/land-change aidcp-cloud manual-comment-force-flag`（rebase 最新 master 409ee4f + ff 合并 3177735）。 <!-- aidcp-cloud 3177735 -->
- [x] 7.3 部署 dev：`scripts/deploy-target dev --check` → 备份 `cloud.bak.20260711-175101.tar.gz`+`.env.bak` → rsync src → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连接 + PG 就绪）。 <!-- 2026-07-11 deployed dev -->
- [x] 7.4 tasks.md 勾选并回写 `<repo> <sha>` 标注；登记真机 backlog 新簇（docs/real-machine-acceptance-backlog.md）。 <!-- 簇见 backlog -->
- [x] 7.5 `openspec validate manual-comment-force-flag --strict` → archive。
