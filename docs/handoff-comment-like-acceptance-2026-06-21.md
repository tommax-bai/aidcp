# Handoff — 验收「详情页评论点赞」(comment-like-on-detail)

> 写给下一个 session 做**验收**。功能已实装 + 部署上线 ECS（2026-06-21，`AIDCP_COMMENT_LIKE=true`）。
> 离线测试 + 部署健康检查 + PG 迁移**已全绿**；剩下的是**真机 E2E**（只能在运营机真账号上跑一遍）。
> openspec change：`openspec/changes/comment-like-on-detail/`（proposal / design / specs×2 / tasks）。

---

## 0. 一句话现状

机器人看详情页时，会**偶尔给别人的一条好评论点赞**（独立风控动作、≈笔记赞的 15%），并把点过的好评论攒进 PostgreSQL 语料库、日后写评论时作参考（不照抄）。代码全程在 `AIDCP_COMMENT_LIKE` 开关后，线上已置 `true`。

涉及提交（已推送）：
- `aidcp-cloud@master 1b86a0b`（协议/风控/appraiser/分发/语料库/composer/de-ai）
- `aidcp-edge@master ffeac42`（协议镜像/executeLikeComment/候选抽取）
- `aidcp@main b95a29b`（docs + tasks）

---

## 1. 已经验证过的（不用再验）

- **两仓 typecheck 全绿**；**cloud 全量测试 308/308**；**两仓验收**含 `AC-PROTO`(56)、`AC-RISK`、新增 8 个 `AC-CLIKE`（`test/acceptance/comment-like.test.ts`）。
- **Phase-0 真机探针**（`aidcp-edge/scripts/comment-like-probe.ts`，2026-06-21）：单条评论赞按钮 = `#comment-<id> .interactions .like .like-wrapper`；已赞信号 = svg `use` `#like→#liked` + 赞数 +1（`like-active` 是常驻类、不是信号）；评论锚点滚动后 `getElementById` 存活率 **100%**（不虚拟化）。
- **部署健康检查**：服务 active + 8787 监听 + 飞书长连接 + `RoleDispatcher 已启动`；启动日志零异常。
- **PG 迁移**（线上已确认）：`risk_counters` 约束**放行** `comment_like`；`risk_interactions` 约束**仍排除** `comment_like`；`valuable_comments` 表已建；`select 1` 通。

---

## 2. 待验收（本次验收的目标）= 真机 E2E

> 离线测不到的两块，必须在运营机（已登录小红书、CDP 9222 的真账号）上跑真实浏览会话确认。

### AC-E2E-1 端到端：真的点成一条评论赞，且如实记账

**怎么触发**：让 edge 连上线 cloud（`ws://121.89.85.150:8787`）跑一次正常浏览会话。注意频率闸——评论赞数 ≈ 笔记赞数的 15%，**早场（笔记赞 < ~7）几乎不会点**，要刷到累计点了若干篇笔记赞后才可能触发（这是预期行为，不是 bug）。一场约 10 篇笔记赞 → 期望约 1 条评论赞。

**通过判据**（看 cloud 日志 + PG）：
- cloud 日志出现整条链路：`[comment_like_appraiser]` 选中 → `comment_like.intended` 下发 → edge 回执 → `[browse] ✓ 评论点赞成功`；
- PG `risk_counters` 多了一条 `action='comment_like'`（**真点赞被记进风控**——这是最关键红线）；
- PG `valuable_comments` 多了一行（**点过的好评论已归档**）。

### AC-E2E-2 红线：绝不静默假成功

- 边缘找不到锚点 → 回执 `no_target`，云端**不记账、不扣预算、不归档**；
- 点了没翻转 → `state_unchanged`，同样不记账；
- 这两条很难在正常流里刻意构造，可用**探针脚本**直接验执行器（见 §4）。

### AC-E2E-3 不死锁

- 即便评论赞那一步发生（或失败/弃权），详情页后续「给笔记点赞 / 进作者主页 / 返回 feed」照常推进——日志里 `reading.done` 之后的链路不受影响。

### AC-E2E-4 攒素材 + 不抄袭

- 多刷几篇后 `valuable_comments` 有若干行；
- 之后机器人发评论时（手动 `/publish` 或浏览闭环里发评论），若取用了语料参考，**终稿不得近似照搬**——撞车时日志会出现 `comment.skipped reason=overlaps_reference`（重写一次仍撞则弃发）。

---

## 3. 验收命令（可复制）

> SSH：`ssh -i ~/codes/isales-4.pem root@121.89.85.150`（私钥须 `chmod 600`）。**只碰 `/opt/aidcp/cloud` 与 `aidcp-cloud.service`，绝不碰 isales。**

**A. 实时看链路日志**（跑会话时开着）：
```bash
ssh -i ~/codes/isales-4.pem root@121.89.85.150 \
  'journalctl -u aidcp-cloud.service -f --no-pager' \
  | grep -E "comment_like|评论点赞|comment_like.intended|overlaps_reference|valuable"
```

**B. PG 核对**（密码从 .env 取、不打印）：
```bash
ssh -i ~/codes/isales-4.pem root@121.89.85.150 'export PGPASSWORD="$(grep -m1 "^PGPASSWORD=" /opt/aidcp/cloud/.env | cut -d= -f2-)";
  echo "--- 今日 comment_like 记账数（应 >0 说明真点赞被记） ---";
  psql -U aidcp -d aidcp -h 127.0.0.1 -tAc "SELECT count(*) FROM risk_counters WHERE action='"'"'comment_like'"'"' AND occurred_at > now() - interval '"'"'1 day'"'"';";
  echo "--- 语料库最近归档（应有行，含文本/作者/主题键） ---";
  psql -U aidcp -d aidcp -h 127.0.0.1 -tAc "SELECT left(comment_text,30), author, source_note_title, topics FROM valuable_comments ORDER BY liked_at DESC LIMIT 5;"'
```

**C. 迁移/表健康**（部署后已验过，复查用）：
```bash
ssh -i ~/codes/isales-4.pem root@121.89.85.150 'export PGPASSWORD="$(grep -m1 "^PGPASSWORD=" /opt/aidcp/cloud/.env | cut -d= -f2-)";
  psql -U aidcp -d aidcp -h 127.0.0.1 -tAc "SELECT pg_get_constraintdef(oid) LIKE '"'"'%comment_like%'"'"' FROM pg_constraint WHERE conname='"'"'risk_counters_action_check'"'"';";
  psql -U aidcp -d aidcp -h 127.0.0.1 -tAc "SELECT to_regclass('"'"'valuable_comments'"'"') IS NOT NULL;"'
```

---

## 4. 用探针确定性验「边缘执行器」（AC-E2E-2 的旁路）

正常流里很难刻意造 `no_target`。要确定性验执行器，用 `aidcp-edge/scripts/comment-like-probe.ts`（CDP 9222 上、已登录的真机 Chrome）：

```bash
# 只读探测（选择器/已赞信号/锚点存活率）——零交互、不点赞
cd ../aidcp-edge && node_modules/.bin/tsx scripts/comment-like-probe.ts

# 点赞标定（点一条→读变化→立刻取消，自还原、净状态为零）——验「点后校验」信号
AIDCP_LIKE_CALIBRATE=1 node_modules/.bin/tsx scripts/comment-like-probe.ts
```
> ⚠️ 标定会在真账号上**真点一次赞再取消**（对外动作、会通知到对方），自动审批可能拦，需人工放行或本人在终端跑。这验的是探针自带的执行逻辑（与生产 `executeLikeComment` 同构：`getElementById` 定位 + `#liked`/赞数 后置校验 + 找不到 `no_target`），不是生产代码本身的端到端。生产执行器的真正闭环仍以 §2 AC-E2E-1 的真实会话为准。

---

## 5. 调参 / 熔断 / 回滚

**配置（当前默认，偏保守）**：
- 开关：ECS `/opt/aidcp/cloud/.env` 的 `AIDCP_COMMENT_LIKE=true`。
- 每场硬上限 `comment_likes=3`、频率比率 `ratio=0.15`、Bernoulli `likeProbability=0.6`：**写死在代码默认值**（`role-dispatcher.ts` freshBudget / `CommentLikeAppraiser` options）。要调需改代码重部署（目前没做成 env 旋钮——YAGNI，将来要灰度可加）。
- 风控当日 `comment_like` 配额：保守 3 / 正常 6 / 激进 12（`src/risk/quotas.ts`）。

**熔断（不重新部署即可关功能）**：
```bash
# 把 .env 里 AIDCP_COMMENT_LIKE 改成 false（或删除该行）后重启
ssh -i ~/codes/isales-4.pem root@121.89.85.150 \
  "sed -i 's/^AIDCP_COMMENT_LIKE=.*/AIDCP_COMMENT_LIKE=false/' /opt/aidcp/cloud/.env && systemctl restart aidcp-cloud.service"
```
关掉后 appraiser/archivist 不注册、`comment_like.intended` 订阅惰性——功能彻底停（已有的 risk/protocol 仍在，但无害）。

**完整回滚到部署前**（代码层）：
```bash
# 备份在 ECS：/opt/aidcp/cloud.bak.20260621-211207.tar.gz + /opt/aidcp/cloud/.env.bak.20260621-211207
ssh -i ~/codes/isales-4.pem root@121.89.85.150 \
  'cd /opt/aidcp && tar xzf cloud.bak.20260621-211207.tar.gz && cp cloud/.env.bak.20260621-211207 cloud/.env && systemctl restart aidcp-cloud.service'
```
> 注：迁移（`risk_counters` 放行 `comment_like` / `valuable_comments` 表）是**加性、幂等**，回滚代码无需回滚迁移——旧代码不会用到它们，留着也无害。

---

## 6. 架构定位（调试用，按符号；行号会漂）

**链路顺序**：详情页 → `note.scroll_comments`（边缘滚评论 + `harvestCommentCandidates` 抽候选挂回执）→ 云端 `CommentLikeAppraiser`（订 `reading.scroll_comments` 拿 noteId + `action.completed` 拿候选）→ 预闸 → LLM 挑 0/1 → `comment_like.intended` → 分发器 `canInteract('comment_like')`+预算 → `comment_like` 指令 → 边缘 `executeLikeComment` → 回执 → 分发器扣预算 + appraiser `comment_like.confirmed` → `ValuableCommentArchivist` 归档。

| 组件 | 文件 · 符号 |
|---|---|
| 边缘执行器 | `aidcp-edge/src/browse/browse-session.ts` · `executeLikeComment` / `harvestCommentCandidates` / case `interaction.like_comment` |
| 决策角色 | `aidcp-cloud/src/agents/comment-like-appraiser.ts` · `CommentLikeAppraiser`（预闸 `appraise` / 解析 `parsePick`） |
| 归档角色 | `aidcp-cloud/src/agents/valuable-comment-archivist.ts` · `onConfirmed` |
| 语料库 | `aidcp-cloud/src/cache/valuable-comment-store.ts` · `ValuableCommentStore` / `topicKeysFromTitle` |
| 分发/预算/频率 | `aidcp-cloud/src/orchestrator/role-dispatcher.ts` · `comment_like.intended` 订阅 / `consumeBudget` / `sessionLikeCounts` / 角色注册（`commentLikeEnabled`） |
| 风控记账红线 | `aidcp-cloud/src/comm/handler.ts` · action.completed 记账过滤（含 `comment_like`） |
| 独立风控动作 | `aidcp-cloud/src/risk/types.ts` · `RISK_ACTIONS`（含 `comment_like`，刻意不进 `InteractionAction`）；`quotas.ts`；`pg-risk-store.ts`（幂等 DO-block 迁移） |
| 取参考 | `aidcp-cloud/src/agents/comment-composer.ts` · `getCorpusReferences` |
| 撞车护栏 | `aidcp-cloud/src/agents/comment-de-ai-flavor.ts` · `overlapsAny`（4-gram Jaccard≥0.5，rewrite-once-then-skip） |
| 协议 | 两仓 `src/comm/protocol.ts` · `interaction.like_comment` / `CommentCandidate`（byte-identical，共 56 消息） |
| 离线红线测试 | `aidcp-cloud/test/acceptance/comment-like.test.ts`（8 个 AC-CLIKE） |

---

## 7. 已知坑 / 注意

- **候选抽取的 author/content 选择器是 best-effort**（Phase-0 只钉死了 `like-wrapper` + 锚点 + 已赞信号；作者/正文用的是宽松 `[class*=...]` 猜测）。若真机上候选 `text` 抓得脏/空，appraiser 仍能判，但可调 `harvestCommentCandidates` 的选择器。verdict 以真机日志里候选的实际 `text` 为准。
- **早场不点是预期**：比率闸 `(commentLikes+1)/max(1,noteLikes) ≤ 0.15`，笔记赞少时分母小、几乎必跳过。验收别因为「刷了两篇没点」就判失败——要刷够量。
- **分钟桶上限 = 1**：`comment_like` 每分钟最多 1 次（`quotas.ts` MINUTE_BURST_CAP），真人节奏，正常。
- **并发会话纪律**：本机多 session、edge 仓有别人未提交 WIP（`chrome-launcher.ts` 等）——动 edge 时**精确 `git add` 自己的文件，绝不 `git add -A`**。
- **isales**：同机另有 isales（当前 inactive），任何 ECS 操作绝不波及。

---

## 8. 验收完成后

- 真机 E2E 全过 → 在 `openspec/changes/comment-like-on-detail/tasks.md` 把 6.3 / 6.7（`[~]`）补成 `[x]`，然后 `openspec validate comment-like-on-detail --strict` → **archive**（`/opsx:archive`）。
- 若发现选择器漂移 / 行为偏差 → 记进 `docs/deferred-verification-2026-06-21.md` 债务台账，或起一个修复 change。
