# Design — platform-browse-protocol (C1b)

> cloud + 协议脊柱、🔴 热点串行单写者。FB 表值=今天 ⇒ 阶段 0 零行为。所有 `文件:行` 为 2026-07-14 HEAD 实核。

## 1. 协议 delta（4 optional 字段，0 新消息类型）

| # | 消息 | 字段 | 方向 | 语义 | 缺省 |
|---|---|---|---|---|---|
| 1 | `NoteOpenPayload`（`protocol.ts:418`） | `surface?:'feed'\|'detail'` | ↓ | detail=导航进详情（今天）；feed=就地展开不离列表 | `'detail'`⇒逐位等价 |
| 2 | `NoteOpenPayload` | `purpose?:'read'\|'navigate'` | ↓ | read=打开并上报 note.detail（今天）；navigate=只把浏览器带到该 detail、**MUST NOT 上报 note.detail**，只回 `action.completed{ok,observation,noteId}` | `'read'` |
| 3 | `ActionCompletedPayload`（`protocol.ts:1114`） | `noteId?:string` | ↑ | **MUST 从被点 article DOM 重新派生规范 postId。MUST NOT 复制命令 payload** | 缺省回落 `session.currentNoteId`（老边端零回归）|
| 4 | `ActionCompletedPayload` | `observation?:{surface?;listKey?;author?;textPreviewHead?;reactionText?;articleIndex?}` | ↑ | 独立见证包：surface=上下文回声（审计/迁移确认）；listKey=当前 feed URL 规范化；其余=归账仲裁独立证据 | 缺省⇒不比对 |

**MessageType 枚举不动** ⇒ 两份 protocol.ts 的 `Record<MessageType,true>` 穷举不变 ⇒ AC-PROTO 全绿、计数不变。edge-client 白名单**零改动**（4 条消息均已在内）。

## 2. 归账仲裁（`src/comm/handler.ts`，独立见证驱动）

`handler.ts:409-410` 的旧假设「like 总在 note.detail 之后、`currentNoteId` 即被互动」在 feed 上失效。新规则：

1. **版本偏斜闸**：hello 握手带 edge 能力位 `inline_targeting`；静态 `readSurface==='feed'` 时若回执缺 noteId ⇒ 拒记账 + 审计，**MUST NOT 回落 `currentNoteId`**。
2. **XHS / detail 路径**：回执无 noteId ⇒ 逐位回落今天的 `currentNoteId` 逻辑（零回归）。
3. **独立见证比对**：`observation{author,textPreviewHead,reactionText}` 与 `page.cards` 里选中的那张卡逐字段比对，不符 ⇒ `target_mismatch` ⇒ 拒写 `liked_notes` 血缘 + 审计 + 灰度回滚计数。**这才是 shadow 的真 gate**——只回一个 noteId 是把命令抄回来（派生规则=匹配规则时两边同错恒等）。
4. **`no_target(stale)`** ⇒ 快照过期：postId 移出会话候选 + 重扫/重选，**MUST NOT 计互动配额失败**。

风控仍按真实发生计数（数量真实、目标存疑时不猜血缘）。

## 3. 回执驱动两步评论迁移（dispatcher）

触发条件 `resolveCommentSurface(platform)!==resolveReadSurface(platform)`（C1a 声明；阶段 0 FB 相等 ⇒ 结构性不可达）。执行：

```
发 open_note{noteId, url, purpose:'navigate'}
  → 现役 comment-handler.onOpen → openPost → 落地页派生 postId==请求？+ editorReady 诚实闸
  → 等其 action.completed{ok, observation.surface:'detail', noteId 匹配}
  → 才发 comment{noteId, text} → submitComment（提交前边缘自身断言落地 postId==payload.noteId 且编辑框在该 article 子树内）
```

任一步失败 ⇒ 不发 comment + 「已批准未送达」显式回报操作员（飞书出口，人审成本已付、比 like 更值得一次有界重导航再报）。`purpose:'navigate'` 的 onOpen **MUST 跳过 `reportNoteDetail`**（否则 onOpen 无条件 `reportNoteDetail({likeCount:0})` 会拿 0 覆盖真实反应数）。

## 4. feed 自愈与审批时序

- **`feed_exhausted` 回执 ⇒ 云端立即映射为 refresh**（否则 `scroll∈noRecoverScroll` 无人触发 → idle → 240s nudge 循环）。
- **审批在途抑制 idle nudge**（平台无关机制）：session flag 由 `comment-approval-gate` 置、dispatcher 的 idle_nudge 翻译器门控。**不复用 `pauseClock`**——它不冻 idle（`session-monitor-role.ts` 的 idle 计时不看 pauseClock）。审批被拒后清 flag。
- **`observedSurface` 仅审计**：回声与静态 `resolveReadSurface` 期望不符 ⇒ warn（检测漂移），不参与任何控制流。

## 5. MODIFIED 的三处（原文保留 + 追加）

- `platform-runtime-abstraction`「协议语义保持平台无关」：追加 scenario——surface/purpose/派生 noteId/observation 是平台无关 optional 扩展，MessageType 计数不变。
- `command-pacing`「详情页返回兜底，杜绝秒退」：把「详情页返回前」推广到「离开一条内容前（详情页 `navigation.back` **或** feed 内联读完后的下一条 `page.scroll`）」，XHS 既有 2 scenario 原样保留，追加内联读 scenario。
- `command-pacing`「边缘保证 feed 翻页停留达标且不与详情页停留双算」：新增第三锚点（内联读，边缘本地 read floor，锚点 `inlineReadStartedAt`），三锚点取 max、MUST NOT 相加；XHS 既有 3 scenario 原样保留，追加内联读锚点 scenario。

## 6. 撞车规避（协议热点串行）

- **C1b 先于 `facebook-join-actuation-decouple`**（0/24 deferred，也加 clickToken 到 protocol.ts）：C1b 纯 optional 字段、不动枚举；join-decouple 起手 `fetch` + rebase 到含 C1b 的 master。
- `facebook-post-publish`/`edge-environment-platform-select` 对 `platform-runtime-abstraction` 只 ADD、不同 header ⇒ 可并行、归档顺序固定。
- `humanize-interaction-prompts` MODIFY comment-interaction/interaction-appraisal ⇒ 本 change 一条不碰。

## 7. 不做

- ❌ `note.detail.surface`/`contentTruncated`/`readDwellMs` 协议字段（控制流走静态表后 surface 回声冗余；contentTruncated 延到 C3 且与 N6 同批；readDwellMs 用边缘本地 read floor）。
- ❌ `interaction.comment.url`（迁移用 `open_note{purpose:'navigate'}` 复用现役 onOpen 的 editorReady 闸）。
- ❌ 归账「拒写血缘」建在 noteId==noteId 上（N1 正确时永不触发；仲裁建在独立见证 observation 上）。
