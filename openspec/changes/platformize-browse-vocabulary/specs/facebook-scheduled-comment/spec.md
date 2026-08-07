## MODIFIED Requirements

### Requirement: Facebook targeted comment holds a keep-open edge lease through human review

Facebook 定向评论（手动 `/comment` / `--join` 与自动排期两条触发路径同等生效）SHALL 在**一个持续持有的边端租约**内完成「站内搜索 → 打开目标帖 → 撰写 → 飞书人审 → 提交」整段，**贯穿人审等待窗口不释放边端**，直至提交或诚实终止。租约 `kind` MUST 为 `comment_prepare`，`leaseMs` MUST 覆盖搜索 + 读正文 + 人审超时 + 提交的最坏耗时。审批期间边端 MUST 停留在目标帖、MUST NOT 被同一会话并发的自治浏览闭环夺走浏览器或导航离开。

系统 MUST 给该路径下发给边端的**每一条评论命令**（`facebook.search.execute` / `facebook.note.open` / `interaction.comment`）透传该租约的 `taskId`。这是硬性要求而非可选：边端 FB 命令入口按 `canExecute(payload.taskId)` 无差别门控——持租约期内**无 taskId 的命令一律被挡**，故评论自身的命令若不带匹配 taskId 会被自己持有的租约一起挡死（自锁死锁）。透传后：本任务的评论命令（taskId 匹配）放行、并发自治浏览闭环的无标识命令（`facebook.feed.scroll` / 返回等）被挡 → 页面钉死在目标帖。

租约 `priority` MUST 反映触发来源：手动操作员命令为 `'human'`、自动排期为 `'automatic'`（与小红书 keep-open 同口径）。

诚实边界不变：租约只负责「把浏览器钉在目标帖上」，MUST NOT 借此绕过或弱化任何既有闸——未授权 / 人审超时 / 被拒照样不提交（AC-PUB）；发布前就地核对目标帖身份、不评错帖、不重复评论照旧。**拿不到租约（获取超时）或提交前被更高优先级任务抢占**时，MUST 走诚实非提交终态（不打去重标记、可重试、不误计当日上限），MUST NOT 静默假成功。

边端不需改动：taskId 门控（`canExecute`）与租约接线为既有通道，本要求为 cloud 侧接线（申请租约 + 透传 taskId）。

#### Scenario: 手动 /comment --join 持锁贯穿人审、审批期停在目标帖
- **WHEN** 运营 `/comment <目标> --join` 触发 FB 定向评论，搜索命中候选并打开目标帖，进入飞书人审等待
- **THEN** 系统 MUST 在同一持有的 `comment_prepare` 租约内保持在目标帖贯穿撰写与人审等待，MUST NOT 在人审窗口释放边端使并发自治浏览闭环把页面导回首页；人审通过后 MUST 在**同一目标帖**上提交（不再复搜/换页）

#### Scenario: FB 评论命令透传 taskId、并发浏览命令被挡
- **WHEN** 该 keep-open 租约持有期间，边端同时收到本任务的评论命令（带匹配 taskId）与自治浏览闭环命令（无 taskId）
- **THEN** 带匹配 taskId 的评论命令 MUST 被 `canExecute` 放行执行；无 taskId 的浏览命令 MUST 被挡（不导航离开目标帖）

#### Scenario: 拿不到租约或提交前被抢占 → 诚实非提交
- **WHEN** 租约获取超时（边端无响应），或提交前被更高优先级任务抢占
- **THEN** MUST 记诚实非提交终态、MUST NOT 打每帖去重标记（可重试）、MUST NOT 误计当日评论上限，MUST NOT 静默假成功

#### Scenario: 红线反例——为省事不持锁或不透传 taskId（禁止）
- **WHEN** 有实现让 FB 定向评论在人审期不持锁（撒手等审批），或持锁却不给评论命令透传 taskId
- **THEN** MUST 视为违规、不予合入：前者会被自治浏览闭环滚回首页致 `editor_not_found`；后者会被自己的租约把评论命令挡死

### Requirement: Comment target open confirms the requested canonical Facebook post identity

The Facebook comment path SHALL treat `facebook.note.open` as successful only when the hydrated detail derives the same canonical Facebook post identity as the requested target. Equivalent supported permalink forms for one post MUST compare equal. A detail for a different post, a profile/feed article, or an identity-less URL MUST NOT advance composition or create an approval request.

Edge SHALL perform this post-navigation validation inside the existing bounded detail-hydration window and discard transient mismatched details while waiting for the requested target. If the requested identity never appears, Edge SHALL return an honest terminal open failure before Cloud's open-step deadline. Cloud SHALL independently correlate returned detail evidence by canonical identity rather than raw URL equality and SHALL ignore evidence for another target.

#### Scenario: Equivalent permalink forms identify the same opened target

- **WHEN** Cloud requests a post through one supported Facebook permalink form and Edge reports the same post through another supported form
- **THEN** both sides derive the same canonical post identity
- **AND** the comment path may advance to composition and configured approval

#### Scenario: Stale article is discarded while requested detail hydrates

- **WHEN** the first detail sampled after navigation belongs to another post and the requested post appears within the bounded hydration window
- **THEN** Edge does not emit the stale detail as successful target evidence
- **AND** it returns the requested post detail once its identity is confirmed

#### Scenario: Requested target never hydrates

- **WHEN** only mismatched or identity-less detail is observable throughout the bounded hydration window
- **THEN** Edge reports an explicit open failure before Cloud's deadline
- **AND** Cloud records a non-submit outcome without composing a comment or creating an approval card

#### Scenario: Cloud rejects mismatched detail evidence

- **WHEN** Cloud receives detail evidence whose canonical Facebook post identity differs from the requested target
- **THEN** it does not accept the open step or advance the task
- **AND** it MUST NOT reinterpret timeout or mismatch as success

### Requirement: Facebook keyword configuration selects search or first-post targeting

For every Facebook group-comment run, configured search keywords SHALL be a targeting-mode selector rather than an enablement prerequisite. When the account has one or more non-empty keywords, the pipeline MUST choose one configured keyword and use the existing container-scoped search path. When the account has no keywords, the pipeline MUST NOT dispatch `facebook.search.execute`; it SHALL open the target group discussion stream and select the first hydrated top-level post that exposes both a canonical group-post permalink and a post-level comment affordance.

The two paths MUST NOT silently fall back to each other. A configured-keyword search with no result remains an honest search-path no-target outcome. An empty-keyword first-post selection with no eligible post remains an honest first-post no-target outcome. The first-post path MUST NOT skip to another post because the first eligible post is already in the account's comment dedupe ledger.

#### Scenario: Configured keyword keeps the search path
- **WHEN** a Facebook comment run has at least one configured non-empty keyword
- **THEN** Cloud dispatches the existing container-scoped search before opening the selected permalink
- **AND** it does not inspect the group feed as a first-post fallback

#### Scenario: Empty keywords open the first eligible group post without search
- **WHEN** a Facebook comment run has no configured keywords
- **THEN** Cloud dispatches no `facebook.search.execute`, and Edge selects and opens the first hydrated top-level group post with a stable permalink and post-level comment affordance

#### Scenario: Obfuscated timestamp href uses Facebook's explicit canonical story URL
- **WHEN** a hydrated top-level group post has a post-level comment affordance but its rendered timestamp `href` is only the group root plus an opaque fragment
- **AND** Facebook's React link/story data for that same rendered anchor explicitly contains a canonical group-post permalink
- **THEN** Edge MAY use that explicit canonical permalink for the candidate
- **AND** it MUST NOT infer or synthesize a post ID from the opaque fragment, text, or feed order

#### Scenario: First post already deduped does not advance to the second post
- **WHEN** empty-keyword mode selects the first eligible post and the account has already commented on that permalink
- **THEN** the run ends with an honest dedupe/no-strong-candidate outcome
- **AND** it does not substitute a later post or keyword search

### Requirement: First-post selection is a bounded read-open operation

Cloud SHALL request first-post selection through the existing `facebook.note.open` protocol message with a Facebook-only selection discriminator, the target group container, and the current task lease ID. Edge SHALL establish the canonical group discussion root before selecting the first post. Edge SHALL skip the root navigation when one fresh probe on the current CDP target proves that the page is the exact target-group root, the document and group scope are ready and unblocked, the feed is not loading, no modal obscures the surface, and the actual feed scroller is at its origin. Missing, malformed, failed, or mismatched reuse evidence SHALL fall back to one navigation to the canonical group root, except that an observed cancellation or task takeover SHALL terminate without navigation. Edge SHALL then select one eligible permalink or session-bound target, open or bind it as required, and emit the existing `note.detail` shape with the selected target as `noteId`. This operation MUST NOT emit a search activity receipt or be counted/reported as keyword search.

Before accepting a first-post candidate, Edge MUST prove in that candidate probe that the candidate still comes from the exact requested canonical group root, including origin, path, empty query/hash, surface, and group scope. A context change after an in-place reuse SHALL trigger the one canonical root navigation and a fresh candidate probe using only the command's remaining fixed scroll-round budget. A context mismatch after that navigation MUST end honestly without another navigation loop. Once Edge accepts a candidate, existing permalink or session-bound target binding rules remain authoritative and Edge MUST NOT navigate back to the group root to substitute another post.

When the container is invalid, the group feed cannot be opened, the page is blocked, no eligible post hydrates within the bounded window, or the selected target cannot be opened and bound, Edge SHALL return an honest `open_note` failure and MUST NOT emit a fabricated detail.

#### Scenario: Exact ready group root is reused
- **WHEN** the current CDP target is the exact requested group root, its document and unique group scope are ready and unblocked, its feed is settled, and its actual feed scroller is at the origin
- **THEN** Edge skips the canonical group-root navigation
- **AND** Edge freshly probes and binds the first eligible post on that current target

#### Scenario: Uncertain current page falls back to canonical navigation
- **WHEN** any current-page reuse field is missing, malformed, failed, or does not prove an exact reusable target-group root
- **THEN** Edge navigates to the canonical group root exactly once before first-post selection
- **AND** the reuse uncertainty itself is not reported as a completed or failed Facebook action

#### Scenario: Cancellation does not become a navigation fallback
- **WHEN** cancellation or task takeover is observed before or after the reuse probe
- **THEN** Edge terminates the command without navigating the current page

#### Scenario: Reused page changes context before candidate acceptance
- **WHEN** the initial group root was reused but the first-post candidate probe no longer proves the exact requested canonical group root
- **THEN** Edge performs the one canonical group-root navigation and continues with only the command's remaining fixed scroll-round budget
- **AND** if the context still mismatches after navigation, Edge returns `target_context_mismatch` without accepting a candidate, commenting, or navigating again

#### Scenario: First-post read returns the selected permalink as detail identity
- **WHEN** the first eligible group post is successfully selected and opened
- **THEN** Edge emits `note.detail` whose `noteId` is that post's canonical navigable permalink and whose content belongs to the same post

#### Scenario: Cloud accepts an equivalent multi-permalink identity
- **WHEN** Edge returns `https://www.facebook.com/groups/<group>?multi_permalinks=<post>` for the selected first post
- **THEN** Cloud accepts it as a canonical group-post permalink when `<post>` derives a stable Facebook post identity
- **AND** Cloud continues to reject non-group posts, empty identities, and unknown URL shapes

#### Scenario: No eligible feed post is an honest non-submit
- **WHEN** no top-level post with a stable group-post permalink or safely bound session target and comment affordance hydrates within the bounded selection window
- **THEN** Edge returns an explicit open failure and Cloud does not compose, approve, or submit a comment

#### Scenario: First post starts below the initial viewport
- **WHEN** the canonical target group is open but its first feed cards begin below the cover/composer and outside the initial viewport
- **THEN** Edge performs a fixed bounded sequence of same-container downward scroll-and-probe rounds
- **AND** it opens the first eligible hydrated card without navigating home, searching, changing groups, or substituting a later targeting mode

#### Scenario: Native decoding preserves first-post intent
- **WHEN** Cloud sends `facebook.note.open` with `selection=first_commentable_group_post` and a canonical group container
- **THEN** every active Edge command-mapping and decoding layer preserves both fields and routes the bounded first-post operation
- **AND** the request MUST NOT degrade into a generic current-page `facebook.note.open`

#### Scenario: First-post failures remain distinguishable
- **WHEN** first-post opening ends because no candidate hydrated, the selected post has no uniquely bound comment editor, target context mismatches, or Cloud times out waiting for detail
- **THEN** the result and user-facing receipt preserve the corresponding reason
- **AND** Cloud MUST NOT report all of those outcomes as “群内未找到合适的可评论帖子”
