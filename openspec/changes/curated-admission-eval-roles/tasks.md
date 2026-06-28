# Tasks — curated-admission-eval-roles（精选准入：两段式 + 模型评估角色）

> **依赖序**：共鸣预筛拆出（task 1）→ 正文评估角色（task 2）→ 评论评估角色（task 3）→ 注册 + server 移交（task 4）→ prompt（task 5）→ 配置（task 6）→ 验收/回归（task 7-8）→ 部署（task 9）→ 真机标定（task 10）。
> **回写格式**：完成用 HTML 注释 `[ ]`→`[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
> **前置**：依赖 `curated-inspiration-corpus`（Phase 1/2/2b，已上线：`curated_content` 表 + `upsertObservation`/`archiveComment`/`markBotAction`）。纯 cloud、零边端、零协议、零新表。

## 1. aidcp-cloud — 共鸣预筛拆出（第一段）

- [ ] 1.1 `src/publish-agent/curated-gate.ts` 拆出 `passesResonance(input, config): { ok: boolean; reason: string }`——只判共鸣（collect 地板 / 比率），**不判相关性**（相关性移交模型评估）。`evaluateAdmission` 保留（向后兼容 + 可配硬相关性闸）。验证：单测——collect 达地板/比率双过/below_resonance 三路；相关性不参与。
- [ ] 1.2 评论共鸣预筛判定：`likeCount ≥ commentLikeFloor` ∪「已确认点赞」(调用方传入 confirmed=true)。验证：单测两路放行 + 双缺被拦。

## 2. aidcp-cloud — 正文进精选评估角色

- [ ] 2.1 新增 `src/agents/curated-note-evaluator.ts`（`curated_note_evaluator`，仿 `content-curator-role.ts` 订阅 `note.detail.arrived` + 仿 `comment-like-appraiser.ts` 持 `llm`）。流程：`passesResonance` 短路（零 LLM）→ 过则 LLM 评估全文 → 解析 JSON → `admit ∧ relevanceOk ∧ richnessOk ∧ !isPromoOrClickbait` → `curatedStore.upsertObservation`（admitReason='llm_eval'）。验证：单测——预筛不过零 LLM 调用；预筛过且评估准入则 upsert；评估拒绝/解析失败则不 upsert（诚实不纳入）。
- [ ] 2.2 fire-and-forget：评估/落库失败只 log、不抛、不阻塞浏览；LLM 降级→不纳入。验证：单测桩 LLM 抛错→不 upsert、不抛。

## 3. aidcp-cloud — 评论进精选评估角色（独立）

- [ ] 3.1 新增 `src/agents/curated-comment-evaluator.ts`（`curated_comment_evaluator`，订阅 `comment_like.confirmed` 带 likeCount）。流程：评论共鸣预筛（task 1.2）→ LLM 评估（相关 + 范例价值 + 非水评/广告）→ `curatedStore.archiveComment(accountId, {…, likeCount})`。验证：单测——预筛+评估准入则 archiveComment；评估拒绝不落；账号取连接上下文。

## 4. aidcp-cloud — 角色注册 + server 移交

- [ ] 4.1 `src/event-bus/types.ts` `RoleName` 加 `curated_note_evaluator` / `curated_comment_evaluator`。验证：typecheck（穷举一致）。
- [ ] 4.2 `src/orchestrator/role-dispatcher.ts` 注册两角色：仅 `curatedStore` 可用时注册（仿 `concept_extractor`）；评论角色仅 `AIDCP_COMMENT_LIKE=true` 时注册；注入账号绑定 `llm`+`getSoul`+`getNoteData`+`curatedStore`。验证：单测——curatedStore 缺则不注册、不报错。
- [ ] 4.3 `src/server.ts` 移交：**删**全局 `note.detail.arrived` 的「笔记精选捕获」段（移进 task 2 角色），**保留** `lastObservedNoteByAccount` 缓存 + 展示账本 upsertMeta + 自有收藏 `markBotAction('collect')`（免评估）+ 点赞标记；评论双写里**删**直接 `archiveComment`（移进 task 3 角色），**保留** `valuableCommentStore.archive`。验证：grep 确认 server 不再直接 upsertObservation（笔记观测）/ archiveComment；自有收藏/点赞标记仍在。
- [ ] 4.4 CLAUDE.md 角色数人工计数 +2（35→37，以 `RoleName` 穷举为准）。

## 5. aidcp-cloud — 评估 prompt

- [ ] 5.1 正文 prompt：账号身份/领域(人设 interests 作软背景) + 标题 + **全文** + 赞藏数 → 严格 JSON `{admit, relevanceOk, richnessOk, isPromoOrClickbait, reason}`；问相关(依据全文)/丰富/非广告标题党。验证：单测样例解析。
- [ ] 5.2 评论 prompt：账号领域 + 评论正文 + 来源笔记标题 + 赞数 → 严格 JSON（相关/范例价值/非水评）。验证：单测样例。
- [ ] 5.3 解析失败/缺字段→诚实判不纳入（绝不默认纳入）。验证：单测坏输出→不纳入。

## 6. aidcp-cloud — 配置

- [ ] 6.1 共鸣预筛阈值沿用 Phase 1（collectFloor/ratioMin/ratioLikeFloor + 新 commentLikeFloor）；评估模型选择复用既有 role-model 配置（判定类）；评估总开关（缺省开，可关回「仅共鸣」）。**不写死、不记敏感值**。验证：单测缺省 + 覆盖。

## 7. 验收

- [ ] 7.1 成本红线：预筛不过的笔记**零 LLM 调用**。验证：AC 断言 LLM 桩未被调用。
- [ ] 7.2 准入正确：预筛过 + 评估(相关∧丰富∧非广告)过 → 落精选；任一不过 → 不落。验证：AC 多路。
- [ ] 7.3 自有收藏免评估直接进；诚实红线：LLM 降级/解析失败不静默纳入。验证：AC。
- [ ] 7.4 移交无回归：自有收藏/点赞标记/展示账本/评论写作语料(composer)行为不变。验证：相关单测全过。

## 8. cloud 全量回归

- [ ] 8.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
- [ ] 8.2 中控：`openspec validate curated-admission-eval-roles --strict` 通过。

## 9. 部署（ECS 安全序列；git archive committed-only 绕开并发 WIP）

- [ ] 9.1 §0 前置（私钥/子仓）→ ECS 先备份 → `git archive <sha> src | ssh tar -x` → `systemctl restart aidcp-cloud` → healthcheck（active+8787+飞书+PG+`curated_content`）→ 失败回滚。绝不碰 isales。

## 10. 真机标定

- [ ] 10.1 真账号浏览一段：核精选库样本——是否挡掉「高收藏但跑题/水帖/广告」、是否纳入「相关且扎实」；据样本回调三维严格度（过严→放宽、过松→收紧）。参 Phase 1 真机验经验（[[curated-inspiration-corpus-impl]] 的相关性 bug 即真机才暴露）。
