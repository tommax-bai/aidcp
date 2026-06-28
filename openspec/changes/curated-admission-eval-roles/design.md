# Design — curated-admission-eval-roles（精选准入：两段式 + 模型评估角色）

> cloud = `../aidcp-cloud`。行号截至 2026-06-28，以符号/上下文为准。

## 1. 背景与定位

`curated-inspiration-corpus`（Phase 1/2/2b 已上线）的准入现状（真机验坐实）：

- 笔记观测捕获在全局事件处理器（`cloud/src/server.ts` 的 `eventBus.on('note.detail.arrived', …)`，约 `:641-693`）：取人设兴趣 → `evaluateAdmission`（相关性子串 + 共鸣）→ 过则 `upsertObservation`。
- 真机验（账号「测评酱」66cd1d4f）发现：兴趣是描述性长短语（`primary/secondary/seed_keywords` 全是「模型横向对比（能力/价格/延迟/上下文/并发）」这种、人设明示「不用于硬匹配」），硬子串相关性恒不命中 → 25 篇观测全判 off_topic、精选库 0 行。已把 `minTopicOverlap` 缺省 1→0（`curated-gate.ts`，commit 7c7192c）临时止血——但于是变成「光看收藏量」，**无内容层相关性、无质量/丰富度关**。

**定位**：在「共鸣预筛」之后插一道**模型读全文**的相关性 + 丰富度评估，承担相关性（取代退役的硬子串闸）并补质量关；模型只跑在共鸣幸存者上以控成本；正文 / 评论各一个独立角色。

## 2. 关键设计决策

### 2.1 两段式准入（成本红线）

```
笔记详情到达 / 评论确认点赞
  → 【第一段】共鸣预筛（确定性、零 LLM）
       笔记：collect ≥ collectFloor  或  collect/like ≥ ratioMin 且 like ≥ ratioLikeFloor
       评论：comment.likeCount ≥ commentLikeFloor  或  已确认点赞
     不过 → 弃（绝不进第二段）            ← 成本红线：模型只评共鸣幸存者
  → 【第二段】模型评估角色（LLM，读全文）
       相关性(内容层) ∧ 内容丰富度 ∧ 非纯广告/标题党/蹭热点
     不过 → 弃
  → 准入 → upsertObservation / archiveComment
```

- 第一段复用 `curated-gate.ts` 的 resonance 逻辑（把 `evaluateAdmission` 拆出一个「只判共鸣、不判相关性」的纯函数 `passesResonance(input, config)`，相关性交给第二段）。
- 第二段是新角色调 LLM。判定类调用，复用既有 role-model 配置（判定类默认 qwen 系，见用量诊断备忘）。

### 2.2 「正文进精选」评估角色 `curated_note_evaluator`

新建 `cloud/src/agents/curated-note-evaluator.ts`，仿两个现成角色拼装：

- **订阅**：`note.detail.arrived`（仿 `content-curator-role.ts:47` 的 `this.eventBus.on('note.detail.arrived', …)`；该事件带全文 `content` + `likeCount` + `collectCount`）。
- **持 LLM + 人设**：仿 `comment-like-appraiser.ts`（角色持 `llm` + 注入闭包）。注入 `getSoul(accountId)` 取账号领域、`curatedStore`。
- **流程**：`onNoteDetailArrived` → ① `passesResonance`（不过即返回，零 LLM）→ ② 构造 prompt（账号身份/领域 + 笔记标题 + **全文** + 赞藏数）调 LLM → ③ 解析严格 JSON `{admit, relevanceOk, richnessOk, isPromoOrClickbait, reason}` → ④ `admit && relevanceOk && richnessOk && !isPromoOrClickbait` 则 `curatedStore.upsertObservation(...)`（admitReason 记 `llm_eval`）。
- **fire-and-forget**：评估/落库失败只 log、不抛、不阻塞浏览（仿 archivist `:64`）。LLM 降级 → 诚实不纳入（不静默纳入）。
- **取代**：删 `server.ts` 全局处理器里「笔记精选捕获」段（`:659-692`）；该处只保留展示账本 upsertMeta + 「记最近观测笔记内容」缓存（`lastObservedNoteByAccount`，仍供自有收藏补建用）。

### 2.3 「评论进精选」评估角色 `curated_comment_evaluator`（独立）

新建 `cloud/src/agents/curated-comment-evaluator.ts`：

- **订阅**：`comment_like.confirmed`（Phase 2b 起带 `likeCount`）。
- **流程**：① 共鸣预筛——`likeCount ≥ commentLikeFloor` **∪** 本事件即「已确认点赞」（确认点赞本身是机器人选过，放行进评估）→ ② LLM 评估评论的相关性（对账号领域）+ 作为「角度/口吻范例」的价值（替代笔记的「丰富度」，评论看「是否有借鉴价值」）+ 非纯广告/水评 → ③ 准入则 `curatedStore.archiveComment(accountId, {…, likeCount})`。
- **取代**：`server.ts` 评论双写（约 `:965-987`）里直接 `archiveComment` 那段挪到本角色；`valuableCommentStore.archive`（评论写作语料，喂 composer）**保持不变**，仍在原闭包同步落。

> 账号维度：角色在 `RoleDispatcher` 内、按连接账号实例化，`accountId` 由连接上下文（`ctx.accountId`）提供，与 Phase 2 一致。

### 2.4 自有收藏免评估（用户决策①）

机器人自有收藏的自动纳入（`server.ts` interaction.occurred → `markBotAction('collect', …)`，约 `:603-611`）**保持在全局处理器、绕过 LLM 评估**——机器人主动收藏 = 已策展、比共鸣预筛更强，直接进。点赞标记（`markBotAction('like')`，弱信号只标既有行）同样不经评估。

### 2.5 角色注册与开关

- `RoleName`（`event-bus/types.ts:455+`）加 `curated_note_evaluator` / `curated_comment_evaluator`。
- `RoleDispatcher`（`role-dispatcher.ts`）注册两角色，**仅 `curatedStore` 可用时注册**（仿 `concept_extractor` 仅概念池可用时注册）；注入账号绑定 `llm` + `getSoul` + `getNoteData` + `curatedStore`。评论角色仅 `AIDCP_COMMENT_LIKE=true`（评论赞链路开启）时注册。
- 文档维护：CLAUDE.md「角色数」人工计数 +2（35→37，以 `RoleName` 穷举为准）。

### 2.6 相关性硬子串闸退役

`curated-gate.ts` 的相关性子串匹配**保留代码、缺省关**（`minTopicOverlap=0`，已上线）；相关性由本 change 的模型评估承担。`evaluateAdmission` 拆为 `passesResonance`（预筛用）+ 旧整体（向后兼容/可配启用硬闸）。

## 3. Prompt 与输出契约

- **正文评估 prompt**：给「账号身份 + 兴趣领域（人设 interests，作软背景）」+「笔记标题 + 全文 + 赞X 藏Y」；问三件事：① 是否与账号创作领域相关（**依据全文，不止标题**）② 内容是否丰富扎实（具体信息/观点/可复用细节，区别于水帖/几句话配图）③ 是否纯广告/标题党/蹭热点。输出严格 JSON。
- **评论评估 prompt**：给「账号领域」+「评论正文 + 来源笔记标题 + 赞数」；问 ① 相关 ② 作为真人留言的角度/口吻范例是否有借鉴价值 ③ 是否水评/广告。输出严格 JSON。
- 解析失败 / 缺字段 → 诚实判不纳入（绝不默认纳入）。

## 4. 时序与竞态

- `note.detail.arrived` 现已有多个消费者（content_curator / concept_extractor / 全局展示账本 + 本新角色）。新角色独立消费、不依赖他人次序。
- LLM 评估异步（数秒）；期间浏览继续。落库 fire-and-forget，迟到不影响。
- 自有收藏补建仍读 `lastObservedNoteByAccount`（保留在全局处理器，故不受角色化影响）。

## 5. 风险与缓解

| 风险 | 级别 | 缓解 |
| --- | --- | --- |
| 模型评估成本 | 中 | 红线：只评共鸣预筛幸存者（collect≥50 等，feed 中少量）；判定类小模型 |
| 评估过严 → 精选又变空 | 中 | 维度可配；先放宽（相关 OR 丰富满足其一可调）；真机标定 |
| 评估过松 → 仍灌水帖 | 低 | 三维 AND + 非广告排除；真机看样本回调 prompt |
| LLM 降级/超时 | 低 | 诚实不纳入 + fire-and-forget，不阻塞浏览（参用量超时备忘，判定类已 60s） |
| 角色化回归 | 中 | 把全局处理器的捕获整段平移进角色、行为等价；保留展示账本/自有收藏/补建缓存不动；单测覆盖预筛短路 + 评估准入/拒绝 |

## 6. 拆分判断

Phase 3 与 Phase 1/2/2b 解耦：前者「采集/存储/消费/共鸣门槛」已上线，本 change 只在准入处插模型评估段、新建两角色，纯云端、零边端零协议零新表，可独立交付。两评估角色互相独立（正文/评论），但同属一次准入质量化、共用预筛与落库口，一体实现。
