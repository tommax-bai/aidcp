## Context

飞书手动 `/comment <昵称>` 的执行链在 aidcp-cloud：解析（`src/feishu/commands.ts`）→ 命令动作实现（`src/server.ts` 的 `actions.comment`）→ 调度器手动扳机（`src/comment-agent/comment-scheduler.ts` 的 `triggerManual`）→ 小红书走 `runTask`、Facebook 走 `runFacebookTargetedTask(Body)` / `runFacebookJoinThenComment`。

当前有两类闸：
- **软筛选**（本 change 要给操作员覆盖）：小红书「强相关甄选」（`src/agents/comment-target-picker.ts`，无强相关候选 → `pickIndex=null` → `runTask` 换词；用尽 → `no_strong_candidate` 黄卡）；Facebook「零重叠相关性」（`src/comment-agent/facebook-comment-validators.ts` 的 `weak_relevance`）；两侧的「每笔记/每帖去重」（`dedup.hasInteracted`）。
- **硬闸**（本 change 绝不动）：飞书人审（`compose-approve` / `approveFacebookComment`）、Facebook 内容安全校验（同 validator 里的 url/contact/mention/spam/length）、边端诚实闸（关键词一致 / 页型 / 发布前就地核对 noteId / FB 成员态）、账号隔离。

现有 `manualOverride`（`server.ts` 手动出口硬编码 `true`）只绕**风控/配额**前置闸，**不**触及相关性、去重或人审。故 `--force` 是一条**全新**旁路，须独立接线，绝不复用 `manualOverride`。

约束：`comment-scheduler.ts` 是单写者热点文件（今天刚被 `comment-keep-open-through-approval` 重写、已 land），须与 `facebook-scheduled-comment` 串行、land 前 rebase 最新 master。纯 cloud 端，无协议变更。

## Goals / Non-Goals

**Goals:**
- 给 `/comment` 加一个尾部开关 `--force`，复用既有 `--contact` / `--join` 尾部开关解析（任意顺序可组合）。
- `--force` 同时放开**相关性**与**每笔记/每帖去重**两处软筛选（两侧平台），一个开关触发两项。
- 小红书：无强相关候选时兜底选「收藏最高的一篇」（不换词/不放弃）；Facebook：跳过 `weak_relevance`（传空关键词，安全校验分支不受影响）。
- 仅手动命令路径生效；自动/排期/面板/热帖路径零回归。
- 桩可测：解析、兜底选择、FB 传空关键词仍拦 url/contact/spam、人审在 `--force` 下仍拦。

**Non-Goals:**
- 不放开人审、内容安全校验、边端诚实闸、账号隔离（红线）。
- 不改两份 `protocol.ts` / `command-bridge` 动作映射 / 边端代码（无新协议消息）。
- 不为 `--force` 拆成两个开关（相关性 vs 去重）——用户定案为单一开关同时放开两项。
- 不改变去重**记账**（真发成功后照记）；`--force` 只放开发起前的去重**过滤**。

## Decisions

### D1. 单一 `--force` 开关，落 `manual-command-override` 能力
`--force` 是操作员对软筛选的覆盖，与既有「绕配额」覆盖同源。放在 `manual-command-override` spec（ADDED 一条 requirement），并修订两条内容侧 spec（`comment-search-command`、`facebook-scheduled-comment`）的相关性/去重条款开例外。**替代方案**：拆成 `--force-relevance` / `--force-dedup` 两开关——被否，用户明确要单一开关、对操作员更简单。

### D2. `force` 与 `manualOverride` 分离传递
`server.ts` 里 `manualOverride` 仍硬编码 `true`（绕配额），新增 `force` 由命令解析透传（缺省 `undefined`/`false`）。二者独立字段、独立语义，绝不合并。**理由**：`manualOverride` 语义（绕配额、绝不绕人审/相关性）与 `force`（绕相关性/去重、绝不绕人审）边界不同，合并会污染既有红线。

### D3. 小红书兜底 = 「跑甄选，null 时选 top-collect」，而非「跳过甄选」
`--force` 下仍调用甄选角色：有强相关候选就用其最优（收藏最高的强相关篇，行为不变）；**仅当** `pickIndex==null` 时，在该词全体去重后候选里按 `collectCount` 降序取第一。**理由**：相关性存在时仍优先精准目标，`--force` 只在「没有强相关」这一步兜底，最小化行为意外；也与甄选角色内部「强相关里挑收藏最高」的确定性 tie-break 一致。**替代**：force 时完全不跑甄选、直接 top-collect——被否，会在有强相关目标时也盲选，反而更差。

### D4. 去重放开 = 跳过发起前过滤 + 发布前复检；记账不变
小红书在 `runTask` 的甄选前去重过滤（候选构建处）与发布前去重复检两处按 `force` 跳过；Facebook 在容器内选帖循环按 `force` 取第一个候选（不再跳过已评过的）。**发布成功后仍照记去重**（`recordInteraction`），保证账本诚实、供后续任务参考。**理由**：用户要「能再评」，但账本必须诚实。

### D5. Facebook 相关性放开 = 传空 `targetKeywords`
`--force` 下把 `validateFacebookComment` 的 `targetKeywords` 传空数组。校验器 `keywords.length>0` 守卫使整段相关性分支变 no-op，而 url/contact/mention/spam/length/low-signal 等安全校验在其之前、照常执行。**理由**：复用校验器既有守卫，零新增分支、最小改面、桩可测。**替代**：给校验器加 `skipRelevance` ctx 字段——被否，传空关键词已达同效、更少 API 面。

### D6. 回执文案标注 `--force`
`triggerManual` 的触发回执文案在 `--force` 时追加「（--force：跳过相关性/去重）」提示，便于操作员知情。**理由**：透明；`--force` 是刻意越过质量闸的动作，回执须让操作员看到本次用了它。

## Risks / Trade-offs

- [过度评论 / 低质量评论] → `--force` 可能让账号评到弱相关或重复目标，带来质量/风控风险。**Mitigation**：仅手动路径、须操作员显式带开关；人审闸仍在（人是刹车）；回执标注；不改自动路径。
- [热点文件冲突] `comment-scheduler.ts` 单写者、并发 change 多。**Mitigation**：worktree 开发、land 前 rebase 最新 master、与 `facebook-scheduled-comment` 串行；改动集中在 `force` 分支、不重构既有逻辑。
- [误把 `force` 泄漏到自动路径] → 会破坏自动路径的相关性/去重红线。**Mitigation**：`force` 只在飞书手动出口（`server.ts` `actions.comment`）从命令解析透传；`triggerTargeted`（面板/自动）与 `ContentScheduler` 入口不带该字段；加断言/测试覆盖自动路径默认 `force=false`。
- [边端仍诚实闸拦下] `--force` 够不着边端诚实闸（发布前 noteId 就地核对等），极端页面态下仍可能诚实失败。**这是预期**：`--force` 只放开软筛选，不放开完整性闸；诚实失败照回黄/红卡。

## Migration Plan

1. worktree `../aidcp-cloud.wt/manual-comment-force-flag`（off origin/master）开发。
2. 实装 7 跳接线 + FB/XHS 分支；补桩测。
3. `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 须绿）。
4. `scripts/land-change aidcp-cloud manual-comment-force-flag`（rebase + ff 合并 master）。
5. 部署 dev（`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。
6. tasks.md 回写 sha；登记真机 backlog 簇；`openspec validate --strict` → archive。

**Rollback**：`force` 缺省 `false`、旧命令（不带 `--force`）行为逐字不变，风险自然隔离；ECS 侧保留 `cloud.bak.<ts>` 可整包回滚。

## Open Questions

- 是否需要在结果卡片（异步补达的最终评/未评卡）也标注本次为 `--force`？当前决定只在**触发回执**标注（最小面）；若运营反馈需要，可后续增强结果卡片，不阻塞本 change。
