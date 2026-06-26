## Context

「运行监控」页（`aidcp-console/src/pages/MonitorPage.tsx:25-40`）的「按笔记互动」表：动作列是无色 `<Tag>`，笔记列是 `Typography.Text code` 直出裸 `noteId`。它走 `useInteractions`（`aidcp-console/src/api/queries.ts:121-131`）→ `GET /api/monitor/interactions` → 云端 `panel-store.listInteractions`（`aidcp-cloud/src/panel/panel-store.ts:339-369`），后者 `SELECT account_id,note_id,action,interacted_at FROM risk_interactions`。

坐实的关键现状（均经代码核对）：

- **写入闸**：`aidcp-cloud/src/server.ts:462` 订阅 `interaction.occurred`，只在 `evt.noteId && (action==='like'||action==='collect')` 时 `recordInteraction()` 落 `risk_interactions`。评论被这条白名单挡掉；关注既无 `noteId`（发生在作者主页）又不在白名单。
- **表约束**：`risk_interactions`（迁移 `0003_risk_interactions.sql:5-11`）主键 `(account_id,note_id,action)`、`note_id NOT NULL`、`CHECK action IN (like,collect,comment)`、无标题 / url 列。关注的「按作者」语义天然进不去。
- **上游已就绪**：`handler.ts:267-279` 在 `action.completed` 且 `ok && action∈{like,collect,follow,comment,comment_like} && reason!=='already_followed'` 时已 emit `interaction.occurred`，并在 `session.currentNoteId` 存在时带 `noteId`。
- **去重不靠这张表**：内容去重是进程内 `InteractionGuard`（下发前按账号拦）+ `ON CONFLICT DO NOTHING`，历史已看笔记落 `liked_notes`；`pg-risk-store.ts` 的 `hasInteraction()` 与 `src/risk/interaction-dedup.ts` 是**死代码**（生产无人调用）。`risk_interactions` 的唯一生产读者就是面板。→ **可以完全不动它**。
- **边缘已有能力**：`browse-session.ts` 已有 `evalUrl()`（CDP `Runtime.evaluate('location.href')`，`:449-454`）；进详情 modal 时地址栏即 `https://www.xiaohongshu.com/explore/<id>?xsec_token=<t>`（带 token）；进作者主页（`:1541` 导航、`:1619` 解析）地址栏即 `/user/profile/<id>`（无需 token）。`NoteDetailPayload` 已带 `title+author(昵称)+authorId`；`ProfileDetailPayload` 只有 `authorId`（无昵称、无 url）。
- **多租户**：`interaction.occurred` 已带 `accountId`（`session.accountId ?? 'default'`），限频按真实账号。
- **并发 / 迁移**：0017（未跟踪 `publish_log_images`）与 0018（已提交 `text_provider`，并发 model-config 会话）均已占用，故用 **0019**。本机有并发会话在改 edge / cloud（不含本变更要动的 `protocol.ts` / `browse-session.ts`）。

## Goals / Non-Goals

**Goals:**
- 面板互动流记录四类动作；笔记动作按笔记、关注按作者。
- 笔记动作显示标题并可跳转真实详情页；关注显示昵称并可跳转作者主页。
- 抓不到真实链接 / 标题 / 昵称即诚实置空，绝不造假链接（红线）。
- 动作按类型着色。
- 零回归：不动 `risk_interactions` 及其去重 / 归因行为；不新增消息类型 / 命令。

**Non-Goals:**
- 不回填历史 `risk_interactions` 到新表（新表从零开始，明示）。
- 不解决 `xsec_token` 时效失效（只诚实披露 + 重开刷新）。
- 不引入「同一笔记多次互动的时间线」视图（按 (账号,动作,目标) 去重为一行，保留首次时间）。
- 不做 `comment_like`（按评论锚点、非按笔记 / 作者语义，刻意排除）。
- 不实时校验链接可达性。

## Decisions

### D1. 事件表 + 元数据旁表（读时 join），而非把标题 / url 反范式塞进事件行
- **选型**：新增 `interaction_feed`（账号 / 动作 / 目标 id / 时间）+ `interaction_target_meta`（账号 / 目标 id / 标题 / url / 更新时间），面板 `LEFT JOIN`。元数据在「进详情 / 进主页」上报到达时**独立 upsert**，与互动事件解耦。
- **为何**（对抗评审 YAGNI + 失败模式两路都指向此）：
  - 若把 `title/url` 直接写进事件行，则必须在「动作回执」时刻凑齐标题 / url → 要么给会话加 5 个字段、要么承受「动作回执先于详情到达 → 标题永久为空」的时序竞态。
  - 旁表方案把标题 / url 的捕获时机从「互动时」前移到「看到时」，读时 join 取**当前**元数据 → 竞态消失（迟到的元数据下次读就显示），会话只需 +1 字段（`currentAuthorId`）。
  - 与既有 `notification_contact_meta`（事件表 + 旁表 + 读时 LEFT JOIN）模式一致。
- **拒绝的备选**：反范式单表（被上述竞态 + 5 字段否决）；复用 / 改造 `risk_interactions`（破坏其按笔记去重主键语义、`note_id NOT NULL` 容不下关注）。

### D2. `risk_interactions` 一行不动，面板改读新表
- **决策**：保留 `risk_interactions` 作去重台账（其唯一读者本就是面板，但去重实际靠内存 guard，留着零害），面板数据源切到 `interaction_feed`。
- **为何**：改它会牵动既有 AC 测试与「按笔记去重」语义；新表是纯展示账本，与去重 / 风控解耦 → 零回归。明确放弃「全量迁移 / 退役旧写入」（对抗评审 path A）以换取并发期最低风险；点赞 / 收藏对两表的双写是廉价冗余，可日后清理。

### D3. 关注昵称在**边缘**抓，不靠「当前笔记作者」匹配
- **决策**：`ProfileDetailPayload` 新增 `nickname?`，边缘从作者主页 DOM 抓真实昵称。
- **为何**（对抗评审失败模式）：靠「`currentNote.author` 且 authorId 相等」推断昵称，在「搜索页直接关注作者卡片」「关注的作者≠当前打开笔记的作者」「通知页进主页关注」等场景都会落空 → 标题为空只能显示裸 authorId。边缘抓主页昵称对所有入口都成立，且顺带消除多租户串名风险（昵称来自被关注者本人主页，不来自会话里别的笔记）。

### D4. 事件去重保留首次时间（`ON CONFLICT DO NOTHING`），元数据刷新最新（`DO UPDATE ... COALESCE`）
- **决策**：`interaction_feed` 冲突不更新（首次互动时间不可变，诚实审计、不把旧互动重排成「刚刚」）；`interaction_target_meta` 冲突 `COALESCE` 合并（笔记上报补 `title+url`、主页上报补 `nickname+url`，互不抹除；重开笔记刷新到最新 token）。

### D5. 目标 id 单列、不引 `target_kind`
- **决策**：`target_id` 笔记动作存 `noteId`、关注存 `authorId`；动作列即可区分笔记 / 作者，无需额外 kind 列。主键 `(account_id,action,target_id)`：动作不同，即便 id 字符串巧合也不撞键。前端按动作派生「这是笔记还是作者」。

### D6. 诚实置空红线（BLOCKER，须有验收）
- **决策**：边缘只在 URL 含 `xsec_token` 时才带笔记 `url`；`evalUrl()` 失败返回空串须归一成 `undefined`；绝不用裸 id 拼链接。云端落库时空值落 `NULL`（非空串）。前端 `url` 为空只渲染纯标题 / 回落裸 id，绝不渲染死链。沿用发布链 `postUrl` 既有约定。

### D7. 协议只加可选上报字段，四处同步只命中两处
- **决策**：仅给 edge→cloud 上报 `NoteDetailPayload`（+`url?`）与 `ProfileDetailPayload`（+`nickname?` +`url?`）加可选字段。无新消息类型、无新 cloud→edge 命令 → `command-bridge.ts` 与边缘 `onMessage` 主动命令白名单**无需改**；只须两份 `protocol.ts` 逐字一致 + `docs/protocol.md` 改既有上报行（计数不变）。
- **注意**：payload 字段漂移 `typecheck` 抓不到（穷举只覆盖 `MessageType`），须手工核对两端 + 两仓各跑 `typecheck`。与并发 change `account-real-nickname` 正交（它新增 `account.identity` 消息类型，不碰这两个 payload）。

## Risks / Trade-offs

- **`xsec_token` 时效** → 较旧笔记链接会 404。缓解：重开笔记时 `interaction_target_meta` COALESCE 刷新最新 token；UI 加「链接含时效令牌，较旧的可能已失效」提示；绝不造假链接（宁可过期真链，不给假链）。多数行不会被重开刷新 —— 接受并明示。
- **裸作者主页链接可达性未证** → `/user/profile/<id>` 是否无 token 必可开仅由代码推断。缓解：列为真机校验项；若不可靠则改为诚实置空（昵称仍显示、只是不可点）。
- **关注昵称缺失（边缘抓不到）** → 诚实置空，前端回落显示 authorId。可接受的诚实降级。
- **协议两端漂移**（typecheck 不抓 payload 字段）→ 手工核对 + 两仓 typecheck + 边缘验收用例兜底。
- **新表从零、无回填** → 上线初期表为空，须向运营明示「历史互动不迁移，新互动起算」。
- **并发抢迁移号 0019** → `CREATE TABLE IF NOT EXISTS` 幂等防撞；提交只暂存本变更文件。
- **AC 测试形变** → `panel-store.test.ts` 的 `{noteId,action,interactedAt}` 期望需改为新形状 `{targetId,action,title?,url?,occurredAt}`，并新增 AC-PANEL（笔记→标题+详情 url；关注→昵称+主页 url；诚实 NULL 不造假）。

## Migration Plan

1. **云端先行（可独立部署、对边缘向后兼容）**：迁移 0019 建两表 → 写入链（handler/server/store）→ 面板读侧。此时即便边缘未升级，评论 / 关注已能进流、标题来自既有 `note.detail` 上报；只是笔记 / 主页链接暂为空（诚实置空）。
2. **前端**：动作配色 + 目标列标题可点链接 + 时效提示。
3. **边缘**：详情 / 主页读 `location.href`、主页抓昵称 → 真实链接 + 昵称补齐。边缘旧版本发 `undefined` url，云端落 `NULL`，不崩。
4. **回归纪律**：协议改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `typecheck`，两仓 `protocol.ts` 逐字核对，AC-PROTO 必过。
5. **部署**：cloud 按 §5 安全序列（备份 → rsync → restart → healthcheck → 失败回滚）；console 重新构建静态；edge 本地跑连 ECS。ECS 部署即 co-ship 全量 master（先 dry-run 看带出范围）。
6. **回滚**：新表与新字段均为新增 / 可选，回滚云端到备份即可；新表可保留（无人读则无害）。

## Open Questions

- 裸 `/user/profile/<id>` 真机是否稳定可开（无 token）？→ 真机校验，不可靠则昵称不可点。
- 笔记 / 主页地址栏在「discovery 弹层」与「explore 整页」两种形态下 `location.href` 是否都带 token？→ 真机抽样校验（代码与测试桩显示带 token）。
- 是否需要给运营一个「仅显示某账号 / 某动作」的筛选？→ 本期沿用现有 `?accountId` 过滤，动作筛选暂不做（YAGNI）。
