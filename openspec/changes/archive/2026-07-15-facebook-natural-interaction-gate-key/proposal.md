# Facebook feed 点赞资格闸去竞态：以「已选中」为据，不硬闸同级订阅者写的「已放行」集合

## Why

真机（dev、FB 号 Tianxing Bai、簇82）暴露：FB feed 就地读**working**（多次 note_open、view 递增），但 `interaction_appraiser`（点赞判定）**恒 `skip fb_quality_not_passed`、系统性挡掉全部点赞**。`[fb-gate]` 诊断日志取证定谳：**eligibility 检查 `passed=false` 紧接着才打 `quality_passed add`——顺序反了**（两处 noteId key 实测一致，**不是形态漂移**）。

根因是 `EventBus` 同步 emit 下的**顺序竞态**：`quality.pass` 有两个**同级订阅者**——点赞闸的 `facebookQualityPassedNoteIds.add` 与 `deep_reader`。会话启动 `roles.forEach(subscribe)` 在闸的接线**之前**，`deep_reader` 先注册先跑；FB 下（不看图 / 不滚评论）`deep_reader` 在自己的 `quality.pass` 处理器里**同步**一路 emit → `reading.images_done` → `comment_reviewer` 同步 `reading.done` → `interaction_appraiser` 资格检查，**全发生在 `deep_reader` 的处理器内、早于同级的闸 add** → 检查时集合恒空 → 恒判 `fb_quality_not_passed`。

## What Changes

1. **点赞资格闸不再硬闸「已放行」集合**：`interaction_appraiser` 由 `reading.done` 触发，而 `reading.done` 只可能在 `content_curator` 的 `quality.pass` 驱动深读链走通后才发出——**能走到点赞判定本身就证明 curator 已放行**。故资格改为只闸「已选中」（`content_selected`）；「已放行」集合降级为**观测/诊断**（`passed(advisory)`），不再作为硬闸。
2. **noteId 归一到规范帖 key**（`facebookPostKey`，防御性）：`content_selected` / `reading.done` 的 noteId 可能来自不同上报形态（`page.cards` 卡 vs 详情），归一到帖数字 id 防将来形态漂移。
3. 新增 `[fb-gate]` 诊断日志（eligibility / quality_passed add / content_selected add），供真机观测顺序竞态。

## Impact

- **Affected specs**: `facebook-feed-browse`（ADDED：点赞资格闸以「已选中 + 已走到点赞判定」为充分证据、不硬闸同级订阅者写的集合）。
- **Affected code**（cloud `aidcp-cloud`，已 land `354d6a6` + `56112be`、已部署 dev）：`src/orchestrator/role-dispatcher.ts`（`facebookNaturalInteractionEligibility` + `facebookPostKey` + `[fb-gate]` 日志）。cloud-only、无协议 / 边缘改动。
- **验证**：`facebookPostKey` 6 新单测 + acceptance 50 + typecheck 净。真机：修复后 like 命令真被下发（`interaction_appraiser` 出 LLM 判定 + `action=like`），下游边缘两步提交问题另修（`facebook-feed-like-picker-commit-fix`）。
- **通用教训**（见 memory `fb-like-gate-sync-emit-race`）：EventBus 同步 emit 下，别用「同级订阅者写、下游同步读」的模式做闸；要么写方保证在任何消费者之前（注册顺序脆弱），要么让下游的**到达本身**即为充分证据（本 change 解法）。
- **诊断日志**：`[fb-gate]` 三处 `console.log` 验证稳定后可降噪（现留作观测），登记 backlog。
