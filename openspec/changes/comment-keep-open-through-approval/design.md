# Design — keep-open comment through approval

## Context

按需评论走 `comment-scheduler.ts` 的 `runTask`（人工 `/comment` 与自动排期评论两触发同入口）。现结构对同一搜索词做三次独立全量搜索：
1. `withLease(comment_prepare)` → `searchAndHarvest(term)`（发现）→ 释放
2. `picker.pick`（无锁）
3. `withLease(comment_prepare)` → `searchAndHarvest(term)` 复搜找回 stable → `readNote`（读正文）→ 释放
4. `composeAndApprove`（无锁；含飞书人审，最长 90s）
5. `withLease(comment_commit)` → `searchAndHarvest(term)` 复搜找回 → `readNote` 重开 → 核对 noteId → `post` → 释放

每次 `withLease` 释放后边端空出，自治浏览闭环（RoleDispatcher）夺走浏览器并导航离开；步骤 3、5 的复搜因此必须重新跑不稳定的 AI 搜索，成功率 ≈ p³。`withManualCommitMarker` 仅对 `priority='human'` 生效（`onTakeoverStart/End` 暂停/恢复自治浏览），自动路径完全不暂停浏览。

边端租约语义（`edge-task-lease-client.ts`）：`acquire` 时边端取消挂起的 browse 命令（`cancelledBrowseCommands`），持锁期间边端专属该任务；`leaseMs` 是边端侧 TTL，超时边端自动释放。`readNote` 走 `note.open{noteId}` 在**当前页**按 noteId 打开，不重新搜索。

## Decision：单租约贯穿「搜索→选卡→读正文→人审→发布」

`runTask` 的每个搜索词迭代改为**一个持续持有的租约**内完成全部步骤：

```
for term of terms (≤ maxTerms):
  outcome = withLease({ kind: 'comment_prepare', priority, leaseMs: KEEP_OPEN_LEASE_MS }, async lease:
    edge = edgeFor(lease.taskId)
    cards = await edge.searchAndHarvest(term)          # 唯一一次真搜索
    fresh = dedup-filter(cards)
    if fresh empty: return { kind:'next-term' }         # 搜不到候选 → 换词
    picked = await picker.pick(fresh)                    # 持锁期间跑 pick（边端空持数秒）
    if picked.index == null: return { kind:'next-term' }
    selected = fresh[picked.index]
    prepared = await edge.readNote(selected)             # note.open{noteId} 当前页打开，不复搜
    if !prepared or prepared.noteId != selected.noteId: return { kind:'result', read_failed }
    composed = await composeAndApprove(prepared.note, prepared.comments)   # 飞书人审，持锁不释放
    if !composed: return { kind:'result', compose_skipped }                # 超时/被拒 → 结束
    if await dedup.hasInteracted(selected.noteId): return { kind:'result', post_failed:already }
    posted = await edge.post(selected.noteId, composed.text, contact)      # 边端发前就地核对 noteId
    if !posted: return { kind:'result', post_failed }
    await dedup.recordInteraction(selected.noteId)
    return { kind:'result', commented }
  )
  if outcome.kind == 'next-term': continue
  result = outcome.result; break                          # 选中即定：成/败都结束，不再换词
```

要点：
- **消除 prepare 复搜与 commit 复搜**：读正文用当前页 `readNote`；发布用持锁保留的当前详情页，不再搜索。
- **人审在持锁内**：`composeAndApprove` 移进 `withLease` 回调，浏览器停在详情页，自治浏览拿不到边端。
- **换词只在 fresh 空 / pick 空**：选中后无论后续成败都 `break`（不换词、不复搜、不评他篇）——对齐用户定案。
- **takeover 覆盖两路径**：持锁期间对 `priority in {human, automatic}` 都调 `onTakeoverStart/End`，暂停自治浏览（原「只覆盖 commit」在评论任务持锁期被有意反转）。

### 租约时长

`KEEP_OPEN_LEASE_MS` 取 4 分钟（240s）：覆盖 搜索(~30s)+pick(~5s)+读正文(~10s)+人审超时(90s)+发布(~15s) 最坏 ≈ 150s，留足边端 TTL 余量。人审本身仍有 90s 超时闸，不会真占满 4 分钟。

### 发布前就地核对 noteId（取舍2）—— 放边端 post 动作里

不新增 round-trip 或协议消息：`interaction.comment` payload 已带 `noteId`（现仅 log）。边端 `executeComment` 前 MUST 读当前详情页真实 `noteId`（地址栏/DOM）与 payload.noteId 核对，不符则诚实回失败（`note_page_mismatch`）、不提交。云端 `post` 据回执 ok 判成败。这是发布前最后一道新鲜度闸，取代 commit 复搜。

### 边端发现搜索判据加固（P1 + Bug C）

`search-handler.ts`：
- `waitForSearchNavigation` 从宽松 `href.includes('search')` 改为共享严格 `SEARCH_LIST_RE`（抽为导出常量，`browse-session` 同用）+ **基线 URL 变化**（executeSearch 进入前记 baseline，要求 URL 变为结果页且不同于 baseline），使残留 `search` 子串不再让首轮误判成功、跳过提交按钮兜底。
- 确认到达后**核对 URL 的 `keyword` 参数解码后等于本次搜索词**（容错 trim/大小写），不等则视为停在旧关键词页、回未到达（关 Bug C）。
- `clickSearchSubmit` 找不到按钮 rect 时补 warn。

## Risks / Trade-offs

- **审批期占用浏览器 ≤ ~90s**：自治浏览暂停。量级小（评论受日上限、风控 normal 才触发、每小时≤1），<空闲看门狗阈值（~240s），且停在详情页读笔记像真人。可接受（用户定案）。
- **边端空闲看门狗**：持锁停在详情页无命令 ~90s 若触发看门狗需处理——90s < 已知 idle 阈值，v1 观察；必要时人审期让边端做轻 dwell（复用 `ensureDetailDwell`）。真机验收核。
- **`priority='automatic'` 租约被抢占**：持锁跨审批窗口 MUST 不被自治浏览抢占。边端 acquire 即取消 browse、且 takeover 暂停云端下发，双保险。实装加断言。
- **红线**：发前就地核对不过→诚实终止不发；发现搜索未到结果页/关键词不符→诚实回失败不采卡。均不静默假成功。

## Out of scope（YAGNI）

- 不用 `note.open.url` permalink 直驱重开（keep-open 不关详情页，无需重开）。
- 不给 `page.cards` 卡片加 url 协议字段（不需要，避开协议热点）。
- 提交按钮多候选+有界重试延后（button-not-rendered 是未证子机制，待真机簇34 定）。
- 就绪轮询替换固定睡眠延后（与现有 `waitForCards` 重叠）。
